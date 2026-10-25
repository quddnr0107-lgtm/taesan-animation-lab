"""CPU animation driven by real Korean WAV and Rhubarb phonetic cues."""
import bpy, os, runpy, json, math, wave, time, resource
from pathlib import Path
T=time.monotonic();os.environ['FIT_VARIANT']='B';os.environ['FIT_BUILD_ONLY']='1'
g=runpy.run_path('studies/likeness.py');base=g['g'];s=g['s'];mouth=g['mouth'];out=Path('output');out.mkdir(exist_ok=True)
fixture=Path('studies/fixtures');cue_data=json.loads((fixture/'004-mouth-cues.json').read_text());cues=cue_data['mouthCues']
with wave.open(str(fixture/'004-voice.wav')) as w:duration=w.getnframes()/w.getframerate()
assert cues and all(c['end']>=c['start'] for c in cues)
s.render.fps=24;s.frame_start=1;s.frame_end=math.ceil(duration*24)
s.render.resolution_x=768;s.render.resolution_y=432;s.eevee.taa_render_samples=12
# Stable medium close shot. Face source is the reviewed B variant.
cam=base['cam'];cam.location=(.35,-4.75,2.28);cam.data.lens=52;base['focus'].location=(0,0,1.76)
shapes={'X':(.073,.012,.004),'A':(.075,.012,.003),'B':(.080,.012,.018),'C':(.095,.012,.055),'D':(.080,.012,.075),'E':(.055,.022,.045),'F':(.040,.027,.030),'G':(.070,.012,.013),'H':(.085,.012,.030)}
base_scales=[tuple(e.scale) for e in base['eyes']]
active=0;closed=0;keys=[]
for f in range(1,s.frame_end+1):
 t=(f-1)/24
 cue=next((c['value'] for c in cues if c['start']<=t<c['end']),'X')
 mouth.scale=shapes.get(cue,shapes['X']);mouth.keyframe_insert('scale',frame=f);keys.append({'frame':f,'time':round(t,5),'cue':cue,'scale':list(mouth.scale)})
 active+=int(cue not in ['X','A']);closed+=int(cue in ['X','A'])
 for e,sc in zip(base['eyes'],base_scales):
  blink=.12 if f in [27,28,60,61] else (.65 if f in [26,29,59,62] else 1)
  e.scale=(sc[0],sc[1],sc[2]*blink);e.keyframe_insert('scale',frame=f)
for fc in mouth.animation_data.action.fcurves:
 for k in fc.keyframe_points:k.interpolation='CONSTANT'
assert active>=5 and closed>=5
# All cues come from actual speech; no sinusoidal surrogate is used for mouth shape.
(out/'applied-mouth-cues.json').write_text(json.dumps(keys,indent=2))
s.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(out/'talking-B.blend'))
s.render.filepath=str(out/'frame_');bpy.ops.render.render(animation=True)
report={'experiment':'005-korean-talking-B','frames':s.frame_end,'fps':24,'width':768,'height':432,'voice_seconds':duration,'video_seconds':s.frame_end/24,'render_elapsed_seconds':round(time.monotonic()-T,2),'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'source_mouth_segments':len(cues),'active_mouth_frames':active,'closed_mouth_frames':closed,'voice_text':'안녕! 오늘은 무슨 놀이를 할까?','tools':['Blender EEVEE via llvmpipe CPU','Supertonic 3 ONNX CPU preset F1','Rhubarb 1.14.0 phonetic'],'limitations':['approximate phonetic mouth-shape mapping, not exact Korean phoneme alignment','adult preset voice, not the original actor','face/hair are still procedural approximations','no claim of broadcast-equivalent quality']}
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
