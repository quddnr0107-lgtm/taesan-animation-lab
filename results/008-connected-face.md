# 008: Connected facial topology

[Before/after comparison](008-before-after.jpg) · [Measured report](008-report.json)

Rebuilt the head as a single connected mesh with apertures, integrating 1,152 eyelid vertices into the head surface. Removed separate front/back skin pieces and overlapping periorbital patches. Recessed the eye assemblies and reduced their depth; narrowed the resting mouth aperture. Six skin shape keys: BlinkL/R, JawOpen, Smile, BrowRaise and LipRound.

CPU run 40164045206 passed connectivity and file checks but failed visual review: black iris fragments remained visible at closed-eye corners. Run 40164256182 corrects full-envelope eyelid clearance. Five 576-square stills were rendered: neutral, half-blink, blink, smile and three-quarter. Render duration 111.85 seconds, max RSS 1053576 KiB; these are still-render measurements, not comparable to the prior animation timing.

Visual review: the horizontal cheek seam and detached cap-like eyelids are reduced; closed eye corners cover the prior exposed dark iris fragments. Uneven folds/bumpiness remain around closed lids. Facial anatomy, hair, mouth and materials are still procedural and differ substantially from the reference. Connected geometry is not proof of production quality or character identity.

Source: studies/continuous_face.py. Workflow: Connected Face CPU Study. Full editable scene, raw stills and logs are in the connected-face-2 Actions artifact (14-day retention). Source, selected comparison and report are preserved in this repository.
