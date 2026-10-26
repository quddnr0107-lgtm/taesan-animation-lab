# Reproducible bounded numerical motion study

This is **200,000 unique parameter/trajectory simulations, zero image frames, zero video renders**. The v2 audit checks those same configurations again; it adds **zero** new configurations. Engineering acceptance is not a visual-naturalness score or a phoneme-alignment measurement.

## Run

Python 3.11 and the exact tested dependency pins:

```sh
python -m pip install -r experiments/motion/requirements.txt
python experiments/motion/run.py --output output/numeric
```

The output directory must be empty. Fixed seed, sequential 10k+10k+60k+60k+60k stages, fixed original gates, existing refinement rules, and v2 validation equations are preserved. The full scripts generate the audit ledgers and finalist control JSONs. They do not render artwork or invoke external APIs. Full reproduction previously took approximately 11 minutes locally; hosted-runner performance can differ. The single standard CPU job times out at 30 minutes and retains compressed ledgers and compact evidence for seven days.

```sh
python experiments/motion/run.py --output output/smoke --smoke-count 32
```

Smoke runs explicitly report their actual count, do not claim 200k completion, and do not exercise survivor-dependent later-stage refinement. The first 32 configuration hashes, numerical metrics and v2 checks are compared against the existing full ledgers in the accompanying local test evidence.

## Fixtures and provenance

`fixtures/audio-motion.json` contains only the existing training RMS envelope and speech timing intervals. `fixtures/heldout-reference.json` contains the exact float RMS samples originally calculated by audit_v2.py from the first eight seconds of the existing dialogue WAV, zero-padded to thirteen seconds, with its speech intervals. Loading these serialized float values preserves the existing v2 calculations while excluding voice recordings and artwork from this public bundle. The held-out excerpt is another passage from the same voice, not broad speaker or language generalization. Training/held-out signals each contain 312 frames at 24fps.

Only portability changes were made to the original scientific scripts: fixture path via MOTION_FIXTURES, and precomputed held-out RMS instead of reading the private local WAV path. The wrapper runs isolated copies so imported script side effects cannot overwrite the source/reference evidence. `reference/` retains original run summaries, not results claimed to have been produced by a future Actions run.

`verify.py` independently counts ledger rows, recomputes canonical config hashes, checks uniqueness and sequential IDs, checks one-to-one v2 linkage, checks acceptance logic and summary totals, and links each selected finalist back to the actual accepted ledger record. It writes raw-ledger SHA-256 digests. V2 finalists must be accepted in v2 and contain matching v2 metrics.

## Automation bounds

The workflow responds only to **opened** same-repository pull requests touching this bundle. No synchronize/push/schedule/re-dispatch loop, no new repository, no GPU or paid runner label, no secrets, and read-only repository permissions. One job and a fixed concurrency group avoid parallel duplicate study runs. Other pre-existing repository workflows are not edited. Final visual render comparisons are a separate task and must not be counted as completed here.
