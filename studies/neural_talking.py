"""Render the connected face with neural controls; keep the fixed geometry for comparison."""
import bpy,json,time,resource
from pathlib import Path
T=time.monotonic();s=bpy.context.scene;out=Path('output');frames=json.loads((out/'neural-controls.json').read_text())
face=bpy.data.objects['continuous facial shell'];face.data.shape_keys.animation_data_clear();keys=face.data.shape_keys.key_blocks
names=['BlinkL','BlinkR','JawOpen','Smile','BrowRaise','LipRound'];assert all(n in keys for n in names)
for row in frames:
 for n in names:
  keys[n].value=row[n];keys[n].keyframe_insert('value',frame=row['frame'])
for fc in face.data.shape_keys.animation_data.action.fcurves:
 for k in fc.keyframe_points:k.interpolation='LINEAR'
assert not any(o.animation_data for o in bpy.data.objects if o.name.startswith('eye assembly'))
s.render.fps=24;s.frame_start=1;s.frame_end=len(frames);s.render.resolution_x=576;s.render.resolution_y=576;s.eevee.taa_render_samples=4
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/'neural-speaking.blend'));s.render.filepath=str(out/'frame_');bpy.ops.render.render(animation=True)
r={'experiment':'011-neural-connected-speech','frames':len(frames),'fps':24,'width':576,'height':576,
'elapsed_seconds':round(time.monotonic()-T,2),'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
'geometry':'unchanged connected-face-2 mesh','controls_source':'neural-controls.json',
'limitations':['Experimental six-control projection, not a full 52-expression rig','Preset adult voice, not original actor','Closed-eyelid folds and simplified facial anatomy remain','Not reference-equivalent animation']}
(out/'report.json').write_text(json.dumps(r,indent=2))
