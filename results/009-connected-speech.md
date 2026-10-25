# 009: Connected face speaking Korean

[Video](009-connected-korean.mp4) · [Selected frames](009-speech-frames.jpg) · [Before/after face comparison](008-before-after.jpg) · [Report](009-report.json)

CPU workflow run 40164464363 succeeded. Blender 3.0.1 EEVEE with Mesa llvmpipe software rendering, 77 frames at 24fps, 576×576. Render duration 241.43 seconds, maximum RSS 1059988 KiB. Video 3.208333 seconds, audio 3.174438 seconds. All 77 frames passed a nonblank/contrast check. Frames 1,20,28,55 were visually inspected, including the closed blink.

The connected face from experiment 008 replaces the prior separate skin pieces. Its six skin controls are driven by the existing byte-identical Korean audio fixture and 15 phonetic segments. Eye geometry is not scaled to blink. The preset adult voice is not the reference actor; prior ASR validation of this unchanged audio was not rerun.

Short 45ms cue-edge interpolation and linear keyframe interpolation replace stepped jaw/lip curves. Measured maximum per-frame JawOpen change: 0.52 before, 0.502167 after; LipRound: 1.0 before, 0.991973 after. These modest numerical changes do not establish natural lip sync; abrupt motion remains.

## Visual assessment

The broad cheek boundary is reduced and the previously exposed dark iris corner fragments are covered in the inspected closed-eye pose. Uneven closed-eyelid folds, simplified mouth anatomy, procedural hair and facial proportions remain visible. This is an intermediate rig improvement, not visual equivalence to the reference, a finished episode, or a complete prompt-to-video website.

Source: studies/connected_talking.py and studies/continuous_face.py. The Connected Rig Korean Speech CPU workflow loads the connected-face-2 artifact from run 40164256182. Full raw frames, editable Blender scene, cue values and logs have 14-day Actions artifact retention. If that input expires, rerun Connected Face CPU Study and update the workflow input artifact name and run-id.
