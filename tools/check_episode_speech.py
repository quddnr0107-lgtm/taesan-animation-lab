"""Independent full-episode ASR; expected text is never sent to Whisper.

pip install faster-whisper==1.2.0 huggingface_hub==0.36.0
Input defaults: inputaudio/episode.wav and inputaudio/episode-timeline.json.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import time
import wave


def normalize(text):
    return re.sub(r"[^가-힣a-zA-Z0-9]", "", text).lower()


def edit_distance(reference, hypothesis):
    previous = list(range(len(hypothesis) + 1))
    for i, a in enumerate(reference, 1):
        row = [i]
        for j, b in enumerate(hypothesis, 1):
            row.append(min(row[-1] + 1, previous[j] + 1, previous[j - 1] + (a != b)))
        previous = row
    return previous[-1]


def main():
    from faster_whisper import WhisperModel

    started = time.monotonic()
    out = Path(os.environ.get("ASR_OUTPUT", "output"))
    out.mkdir(parents=True, exist_ok=True)
    audio = Path(os.environ.get("EPISODE_AUDIO", "inputaudio/episode.wav"))
    timeline_path = Path(os.environ.get("EPISODE_TIMELINE", "inputaudio/episode-timeline.json"))
    report = {"status": "failed", "engine": "faster-whisper 1.2.0 small CPU int8",
              "prompt": None, "language": "ko", "beam_size": 5,
              "condition_on_previous_text": False, "vad_filter": True}
    try:
        with wave.open(str(audio)) as wav:
            seconds = wav.getnframes() / wav.getframerate()
        assert abs(seconds - 60) < .001, f"Expected a 60-second WAV, got {seconds}"
        model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
        # Deliberately no initial_prompt, prefix, hotwords or expected dialogue.
        segments, info = model.transcribe(
            str(audio), language="ko", beam_size=5,
            condition_on_previous_text=False, vad_filter=True)
        decoded = [{"start": float(s.start), "end": float(s.end),
                    "text": s.text.strip(), "avg_logprob": float(s.avg_logprob)}
                   for s in segments]
        transcript = " ".join(s["text"] for s in decoded).strip()
        assert transcript, "Empty independent transcript"
        # Only load expected words after inference; they are comparison data.
        expected_lines = json.loads(timeline_path.read_text())["speech"]
        assert len(expected_lines) == 12, "Expected 12 narration lines"
        reference = " ".join(line["text"] for line in expected_lines)
        ref, hyp = normalize(reference), normalize(transcript)
        assert ref and hyp, "Empty normalized reference or transcript"
        distance = edit_distance(ref, hyp)
        cer = distance / len(ref)
        report.update({
            "status": "review-required" if cer > .15 else "transcription-check-passed",
            "flag_for_review": cer > .15,
            "reference": reference, "transcript": transcript,
            "normalized_character_error_rate": cer,
            "normalized_reference_characters": len(ref),
            "normalized_hypothesis_characters": len(hyp),
            "edit_distance": distance, "review_threshold": .15,
            "expected_lines": [{"id": line["id"], "shot": line["shot"],
                                "start": line["start"], "end": line["end"], "text": line["text"]}
                               for line in expected_lines],
            "decoded_segments": decoded,
            "duration_seconds": seconds,
            "audio_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
            "timeline_sha256": hashlib.sha256(timeline_path.read_bytes()).hexdigest(),
            "limitations": [
                "ASR errors are possible; CER is a screening signal, not a listening verdict",
                "Passing does not establish natural acting, voice identity or phoneme lip sync",
                "Expected lines and decoded segments are shown separately; no forced alignment claimed",
                "CER above threshold is flagged for human review and does not fail the render pipeline",
            ],
        })
    except Exception as error:
        report["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        report["max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (out / "asr-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

