# 006: Deformable facial mesh CPU experiment

Source: studies/face_rig.py. CPU workflow run: 40162378739. Automated geometry and video checks passed; visual quality is still provisional.

Replaced a solid face sphere and separate mouth overlay with a facial shell containing eye and mouth apertures. Added BlinkL, BlinkR, JawOpen, Smile and BrowRaise shape keys; eyelash deformation follows the skin blink controls. Eyeballs are not scaled to simulate blinking.

Result: 23,461 vertices, 21,150 faces, 36 frames at 24fps, 576 square. Render time 146.13 seconds, maximum RSS 914392 KiB. These measurements are for this particular preview only.

## Visual review

Earlier iterations had folding eyelids and exposed iris rims. Run 40162012650 passed automated checks but was rejected visually. Run 40162378739 reduces the exposed iris issue; closed eyelids remain protruding and seams are visible around the eyes, cheek boundary and mouth. The hairstyle, face proportions, materials and performance do not match the reference production. This is experimental procedural topology, not finished production retopology.

[Pose comparison](006-poses.jpg). The Actions artifact also contains the editable Blender scene, raw frames, software-renderer details and silent deformation MP4; artifact retention is 14 days. Source and this comparison/report remain in the repository.

No claim of original-character equivalence, broadcast quality, or a finished prompt-to-episode website.
