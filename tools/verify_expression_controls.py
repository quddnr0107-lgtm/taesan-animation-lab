"""Independently review experiment 011 controls against the experiment 009 cue recipe.

Example from the repository root:
  python tools/verify_expression_controls.py \
    --baseline-cues studies/fixtures/004-mouth-cues.json \
    --neural-controls results/011-neural-controls.json \
    --output control-review.json

The baseline is reconstructed from studies/connected_talking.py, including its
45 ms cue-edge smoothing. This checks control values, not perceptual lip sync.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def read_json(path):
    return json.loads(path.read_text())


def reconstruct_baseline(cues, count, fps=24):
    jaw = {"X": 0, "A": 0, "B": .18, "C": .7, "D": 1,
           "E": .5, "F": .35, "G": .14, "H": .4}
    rounding = {"E": .75, "F": 1}
    rows = []
    for frame in range(1, count + 1):
        time = (frame - 1) / fps
        cue = next((c["value"] for c in cues
                    if c["start"] <= time < c["end"]), "X")
        rows.append({"frame": frame, "time": time, "cue": cue,
                     "JawOpen": jaw.get(cue, 0),
                     "LipRound": rounding.get(cue, 0)})
    for row in rows:
        if row["cue"] in ("X", "A"):
            continue
        time = row["time"]
        segment = next(c for c in cues if c["start"] <= time < c["end"])
        index = cues.index(segment)
        fade = .045
        for control, table in (("JawOpen", jaw), ("LipRound", rounding)):
            value = table.get(row["cue"], 0)
            if time - segment["start"] < fade:
                previous = table.get(cues[index - 1]["value"], 0) if index else 0
                alpha = max(0, min(1, (time - segment["start"]) / fade))
                alpha = alpha * alpha * (3 - 2 * alpha)
                value = previous + (value - previous) * alpha
            if segment["end"] - time < fade:
                following = (table.get(cues[index + 1]["value"], 0)
                             if index + 1 < len(cues) else 0)
                alpha = max(0, min(1, (segment["end"] - time) / fade))
                alpha = alpha * alpha * (3 - 2 * alpha)
                value = following + (value - following) * alpha
            row[control] = value
    return rows


def describe(rows, key, cap=None):
    values = [row[key] for row in rows]
    pairs = list(zip(rows, rows[1:]))
    first, second = max(pairs, key=lambda pair: abs(pair[1][key] - pair[0][key]))
    delta = abs(second[key] - first[key])
    extent = max(values) - min(values)
    transition = {
        "from_frame": first["frame"], "to_frame": second["frame"],
        "from_value": first[key], "to_value": second[key],
    }
    if "speech_gate" in first:
        transition.update({
            "from_gate": first["speech_gate"], "to_gate": second["speech_gate"],
            "from_rms": first["rms"], "to_rms": second["rms"],
        })
    result = {
        "min": min(values), "max": max(values), "range": extent,
        "nonzero_frames": sum(value != 0 for value in values),
        "max_frame_delta": delta,
        "range_normalized_max_frame_delta": delta / extent if extent else None,
        "largest_transition": transition,
    }
    if cap is not None:
        saturated = sum(value >= cap - 1e-9 for value in values)
        result.update({"configured_cap": cap, "cap_frames": saturated,
                       "cap_fraction": saturated / len(rows)})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-cues", type=Path, required=True)
    parser.add_argument("--neural-controls", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    neural = read_json(args.neural_controls)
    assert len(neural) >= 2, "Need at least two control frames"
    keys = ("JawOpen", "LipRound", "Smile", "BrowRaise", "BlinkL", "BlinkR")
    for index, row in enumerate(neural):
        assert row["frame"] == index + 1, "Control frames must be consecutive"
        assert abs(row["time"] - index / 24) < 1e-9, "Expected 24fps controls"
        for key in (*keys, "speech_gate"):
            assert math.isfinite(row[key]) and 0 <= row[key] <= 1, key
        assert math.isfinite(row["rms"]) and row["rms"] >= 0
    silent = [row for row in neural if row["speech_gate"] == 0]
    assert silent, "Fixture must contain gate-closed frames"
    closed_keys = ("JawOpen", "LipRound", "Smile")
    assert all(row[key] == 0 for row in silent for key in closed_keys), (
        "Gate-closed frames contain mouth motion")
    cues = read_json(args.baseline_cues)["mouthCues"]
    baseline = reconstruct_baseline(cues, len(neural))
    caps = {"JawOpen": .9, "LipRound": .7, "Smile": .25, "BrowRaise": .15}
    neural_stats = {key: describe(neural, key, caps.get(key)) for key in keys}
    comparisons = {}
    for key in ("JawOpen", "LipRound"):
        before = describe(baseline, key)
        after = neural_stats[key]
        comparisons[key] = {
            "baseline": before, "neural": after,
            "absolute_delta_decreased": after["max_frame_delta"] < before["max_frame_delta"],
            "range_normalized_delta_decreased": (
                after["range_normalized_max_frame_delta"] is not None and
                after["range_normalized_max_frame_delta"] <
                before["range_normalized_max_frame_delta"]),
        }
    report = {
        "status": "control-review-passed",
        "scope": "Numerical control review only; not visual or Korean phoneme accuracy",
        "baseline_method": "Reconstruct experiment 009 cue tables and 45ms edge smoothing",
        "inputs": {
            "baseline_cues_sha256": hashlib.sha256(args.baseline_cues.read_bytes()).hexdigest(),
            "neural_controls_sha256": hashlib.sha256(args.neural_controls.read_bytes()).hexdigest(),
        },
        "frames": len(neural), "fps": 24,
        "gate_closed_frames": len(silent),
        "gate_closed_frame_numbers": [row["frame"] for row in silent],
        "gate_closed_mouth_controls_all_zero": True,
        "gate_closed_max": {key: max(row[key] for row in silent) for key in closed_keys},
        "brow_raise_all_zero": all(row["BrowRaise"] == 0 for row in neural),
        "neural_stats": neural_stats, "comparison": comparisons,
        "limitations": [
            "Gate-closed means the configured RMS threshold, not verified perceptual silence",
            "Lower absolute deltas may result from smaller motion amplitude",
            "Range-normalized deltas do not establish perceptual smoothness",
            "Reconstructed baseline uses the current published experiment 009 recipe",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "frames": len(neural),
                      "gate_closed_frames": len(silent),
                      "brow_raise_all_zero": report["brow_raise_all_zero"],
                      "output": str(args.output)}))


if __name__ == "__main__":
    main()

