# 007: Korean speech on deformable facial skin

[Video](007-skin-rig-korean.mp4) · [Frame comparison](007-speech-frames.jpg) · [Report](007-report.json)

GitHub Actions run 40162700475 succeeded on Ubuntu 22.04 using Blender 3.0.1 EEVEE and Mesa llvmpipe CPU software rendering. Source: studies/rig_talking.py; workflow: .github/workflows/skin-rig-speech.yml. Input mesh is the experiment 006 artifact from run 40162378739.

The byte-identical existing Korean speech fixture says “안녕! 오늘은 무슨 놀이를 할까?” and uses a preset adult F1 voice, not the reference actor. Existing 15 Rhubarb phonetic cue segments drive JawOpen and the new LipRound skin shape key. BlinkL/R deform the eyelids, while eyeballs are not scaled. The audio's earlier independent transcription check was not rerun; this experiment tests the new rig with the same audio.

77 frames, 24fps, 576×576. Video duration 3.208333 seconds, audio 3.174438 seconds; difference 0.033895 seconds. Blender render duration 225.51 seconds; maximum RSS 892568 KiB. All 77 raw frames passed a basic nonblank/contrast check. Four selected frames including a closed-eye frame were visually inspected.

## Visual result

Speech and skin deformation are connected, but the eyelids protrude, seams remain around facial patches, and mouth deformation is crude and abrupt. Hair, facial proportions, materials, voice and acting differ substantially from the reference. Automated completion and geometry tests do not establish visual equivalence. This is not a finished episode or prompt-driven production website.

MP4, selected frames, report and source are preserved here. Full raw frames, editable Blender scene, applied cue values and renderer logs are in the Actions artifact with 14-day retention. Reproduction requires the experiment 006 artifact; if expired, rerun Deformable Face CPU Study and update the speech workflow input run/name.
