"""Synthesize the one-minute preschool episode with pinned Supertonic 3 on CPU.

Setup (Ubuntu / Python 3.11):
  git clone https://github.com/supertone-oss-archive/supertonic.git /tmp/supertonic
  git -C /tmp/supertonic checkout 1e9799e964ea4c0dad7cde993b65c3c813a7b373
  pip install numpy==2.2.6 onnxruntime==1.23.1 soundfile==0.13.1 huggingface_hub==0.36.0
  apt-get install ffmpeg libsndfile1
  python tools/episode_audio.py
"""
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

SOURCE_REVISION = "1e9799e964ea4c0dad7cde993b65c3c813a7b373"
MODEL_REVISION = "aafc6e32416a594460b32413efc49d7fe4ce6d46"
SAMPLE_RATE = 16000
DURATION = 60
FPS = 12
SHOTS = [
    ("함께 인사해요", "greet", "안녕! 오늘은 몸으로 인사해요.", "함께 천천히 따라 해 볼까요?"),
    ("손을 살랑살랑", "wave", "손을 살랑살랑 흔들어요.", "반가워! 친구에게 인사해요."),
    ("고개를 끄덕끄덕", "nod", "고개를 끄덕끄덕 해 볼까요?", "그래, 그래! 아주 잘했어요."),
    ("어깨를 으쓱으쓱", "shrug", "어깨를 살짝 들었다 내려요.", "으쓱으쓱! 힘을 쏙 빼 주세요."),
    ("두 팔을 활짝", "open_arms", "두 팔을 활짝 벌려 볼까요?", "햇살처럼 환하게 웃어 보세요."),
    ("다음에 또 만나요", "goodbye", "손과 고개로 인사했어요.", "오늘도 즐거웠어요. 다음에 또 만나요!"),
]


def srt_time(seconds):
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{sec:02},{ms:03}"


def main():
    import numpy as np
    import soundfile as sf
    from huggingface_hub import snapshot_download

    started = time.monotonic()
    out = Path(os.environ.get("AUDIO_OUTPUT", "output"))
    out.mkdir(parents=True, exist_ok=True)
    lines_dir = out / "speech-lines"
    lines_dir.mkdir(exist_ok=True)
    source = Path(os.environ.get("SUPERTONIC_SOURCE", "/tmp/supertonic"))
    actual_revision = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if actual_revision != SOURCE_REVISION:
        raise RuntimeError(f"Unexpected Supertonic source revision: {actual_revision}")
    assets = source / "assets"
    snapshot_download(
        "supertone-oss-archive/supertonic-3", revision=MODEL_REVISION,
        local_dir=str(assets),
        allow_patterns=["onnx/*", "voice_styles/F1.json", "LICENSE*", "README.md"])
    sys.path.insert(0, str(source / "py"))
    from helper import load_text_to_speech, load_voice_style
    np.random.seed(1301)
    tts = load_text_to_speech(str(assets / "onnx"), use_gpu=False)
    style = load_voice_style([str(assets / "voice_styles/F1.json")], verbose=False)
    audio = np.zeros(SAMPLE_RATE * DURATION, dtype=np.float32)
    speech = []
    shots = []
    for shot, (title, action, first, second) in enumerate(SHOTS):
        shots.append({"index": shot, "start": shot * 10, "end": shot * 10 + 10,
                      "title": title, "action": action})
        for j, text in enumerate([first, second]):
            line_start = shot * 10 + [.5, 5.0][j]
            line_id = shot * 2 + j + 1
            synthesis_start = time.monotonic()
            wav, duration = tts(text, "ko", style, 8, 1.12)
            w = np.asarray(wav[0, :int(tts.sample_rate * duration[0].item())], dtype=np.float32)
            assert w.size and np.isfinite(w).all()
            raw = lines_dir / f"{line_id:02}-raw.wav"
            converted = lines_dir / f"{line_id:02}.wav"
            sf.write(raw, w, tts.sample_rate, subtype="PCM_16")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw),
                            "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le",
                            str(converted)], check=True)
            w, sr = sf.read(converted, dtype="float32")
            assert sr == SAMPLE_RATE and w.ndim == 1
            original_seconds = len(w) / SAMPLE_RATE
            # Remove only quiet padding, retaining 80ms at each edge.
            active = np.flatnonzero(np.abs(w) > max(.0007, float(np.max(np.abs(w))) * .005))
            assert active.size, f"No speech detected in line {line_id}"
            a = max(0, int(active[0]) - int(.08 * SAMPLE_RATE))
            b = min(len(w), int(active[-1]) + int(.08 * SAMPLE_RATE) + 1)
            w = w[a:b]
            trimmed_seconds = len(w) / SAMPLE_RATE
            stretch = max(1.0, trimmed_seconds / 4.15)
            if stretch > 1.15:
                raise RuntimeError(f"Line {line_id} too long ({trimmed_seconds:.2f}s): {text}")
            sf.write(converted, w, SAMPLE_RATE, subtype="PCM_16")
            if stretch > 1.0:
                fitted = lines_dir / f"{line_id:02}-fit.wav"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(converted),
                                "-af", f"atempo={stretch:.8f}", "-ar", str(SAMPLE_RATE),
                                "-ac", "1", "-c:a", "pcm_s16le", str(fitted)], check=True)
                w, sr = sf.read(fitted, dtype="float32")
                if len(w) > round(4.2 * SAMPLE_RATE):
                    raise RuntimeError("Time-stretch failed to fit the slot")
            peak = float(np.max(np.abs(w)))
            if peak > .92:
                w = w * (.92 / peak)
            begin = round(line_start * SAMPLE_RATE)
            end = begin + len(w)
            assert end <= round((shot * 10 + (4.8 if j == 0 else 9.5)) * SAMPLE_RATE)
            audio[begin:end] = w
            sf.write(converted, w, SAMPLE_RATE, subtype="PCM_16")
            speech.append({
                "id": line_id, "shot": shot, "start": line_start, "end": end / SAMPLE_RATE,
                "text": text, "wav": f"speech-lines/{line_id:02}.wav",
                "original_seconds": original_seconds, "trimmed_seconds": trimmed_seconds,
                "atempo": stretch, "seconds": len(w) / SAMPLE_RATE,
                "rms": float(np.sqrt(np.mean(w * w))),
                "synthesis_seconds": round(time.monotonic() - synthesis_start, 4),
            })
            print(json.dumps(speech[-1], ensure_ascii=False), flush=True)
    sf.write(out / "episode.wav", audio, SAMPLE_RATE, subtype="PCM_16")
    # Mouth motion is an energy envelope, not phoneme inference.
    rms = []
    for f in range(DURATION * FPS):
        center = round(f / FPS * SAMPLE_RATE)
        window = audio[max(0, center - 480):min(len(audio), center + 480)]
        rms.append(float(np.sqrt(np.mean(window * window))) if len(window) else 0.0)
    envelope = np.clip(np.asarray(rms) * 6.8, 0, .66)
    smooth = np.convolve(np.pad(envelope, (1, 1)), [.25, .5, .25], mode="valid")
    frames = [{"frame": f + 1, "time": f / FPS, "shot": f // (10 * FPS), "rms": rms[f],
               "JawOpen": float(smooth[f]), "LipRound": 0.0, "Smile": .08}
              for f in range(DURATION * FPS)]
    timeline = {"title": "몸으로 인사해요", "duration": DURATION, "fps": FPS,
                "sample_rate": SAMPLE_RATE, "shots": shots, "speech": speech, "frames": frames,
                "lip_method": "60ms RMS envelope and centered three-frame smoothing; not phoneme lip sync"}
    (out / "episode-timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2))
    subtitles = "\n\n".join(f"{i}\n{srt_time(line['start'])} --> {srt_time(line['end'])}\n{line['text']}"
                                for i, line in enumerate(speech, 1)) + "\n"
    (out / "episode.srt").write_text(subtitles)
    report = {"title": timeline["title"], "duration_seconds": len(audio) / SAMPLE_RATE,
              "sample_rate": SAMPLE_RATE, "samples": len(audio), "tts": "Supertonic 3 F1 CPU",
              "source_revision": SOURCE_REVISION, "model_revision": MODEL_REVISION,
              "line_count": len(speech), "spoken_seconds": sum(x["seconds"] for x in speech),
              "lines": speech, "audio_sha256": hashlib.sha256((out / "episode.wav").read_bytes()).hexdigest(),
              "elapsed_seconds": round(time.monotonic() - started, 3),
              "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "limitations": ["Preset adult F1 voice, not the reference actor",
                              "Gaps are participation pauses, not missing speech",
                              "Energy-driven mouth motion does not verify Korean phoneme accuracy",
                              "Listening review is still needed"]}
    assert len(audio) == SAMPLE_RATE * 60 and len(speech) == 12 and len(frames) == 720
    assert all(x["rms"] > .001 for x in speech)
    assert all(a["end"] <= b["start"] for a, b in zip(speech, speech[1:]))
    (out / "audio-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({"status": "audio-created", "duration": 60, "lines": 12,
                      "spoken_seconds": report["spoken_seconds"]}), flush=True)


if __name__ == "__main__":
    main()

