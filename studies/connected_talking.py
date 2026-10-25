"""Drive the reviewed facial skin rig with the existing real Korean speech fixture."""
import bpy,json,math,wave,time,resource
from pathlib import Path
T=time.monotonic();s=bpy.context.scene;out=Path('output');out.mkdir(exist_ok=True)
face=bpy.data.objects['continuous facial shell'];face.data.shape_keys.animation_data_clear()
keys=face.data.shape_keys.key_blocks
assert all(n in keys for n in ['BlinkL','BlinkR','JawOpen','Smile','BrowRaise'])
# LipRound is authored on the same connected facial mesh.
assert 'LipRound' in keys
fixture=Path('studies/fixtures')
cues=json.loads((fixture/'004-mouth-cues.json').read_text())['mouthCues']
with wave.open(str(fixture/'004-voice.wav')) as w:duration=w.getnframes()/w.getframerate()
s.render.fps=24;s.frame_start=1;s.frame_end=math.ceil(duration*24);s.eevee.taa_render_samples=4
s.render.resolution_x=576;s.render.resolution_y=576
jaw={'X':0,'A':0,'B':.18,'C':.7,'D':1,'E':.5,'F':.35,'G':.14,'H':.4}
rounding={'E':.75,'F':1};applied=[]
for f in range(1,s.frame_end+1):
 t=(f-1)/24;cue=next((c['value'] for c in cues if c['start']<=t<c['end']),'X')
 blink=max(0,1-abs(f-28)/2) if f<45 else max(0,1-abs(f-61)/2)
 vals={'BlinkL':blink,'BlinkR':blink,'JawOpen':jaw.get(cue,0),'Smile':.12 if cue not in ['X','A'] else 0,'BrowRaise':.10 if .5<t<1 else 0,'LipRound':rounding.get(cue,0)}
 for name,v in vals.items():keys[name].value=v;keys[name].keyframe_insert('value',frame=f)
 applied.append({'frame':f,'time':t,'cue':cue,**vals})
# Smooth cue transitions inside each non-silent segment. X silence stays exactly shut.
for frame in applied:
 if frame['cue'] in ['X','A']:continue
 t=frame['time'];segment=next(c for c in cues if c['start']<=t<c['end'])
 idx=cues.index(segment);fade=.045
 for control,table in [('JawOpen',jaw),('LipRound',rounding)]:
  target=table.get(frame['cue'],0);value=target
  if t-segment['start']<fade:
   prev=table.get(cues[idx-1]['value'],0) if idx else 0
   alpha=max(0,min(1,(t-segment['start'])/fade));alpha=alpha*alpha*(3-2*alpha)
   value=prev+(target-prev)*alpha
  if segment['end']-t<fade:
   nxt=table.get(cues[idx+1]['value'],0) if idx+1<len(cues) else 0
   alpha=max(0,min(1,(segment['end']-t)/fade));alpha=alpha*alpha*(3-2*alpha)
   value=nxt+(value-nxt)*alpha
  frame[control]=value;keys[control].value=value;keys[control].keyframe_insert('value',frame=frame['frame'])
for fc in face.data.shape_keys.animation_data.action.fcurves:
 if 'JawOpen' in fc.data_path or 'LipRound' in fc.data_path:
  for k in fc.keyframe_points:k.interpolation='LINEAR'
assert any(x['JawOpen']>.5 for x in applied) and any(x['LipRound']>.5 for x in applied)
assert all(x['JawOpen']==0 for x in applied if x['cue']=='X')
assert not any(o.animation_data for o in bpy.data.objects if o.name.startswith('eye assembly'))
(out/'applied-cues.json').write_text(json.dumps(applied,indent=2))
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/'skin-rig-speaking.blend'))
s.render.filepath=str(out/'frame_');bpy.ops.render.render(animation=True)
r={'experiment':'009-connected-rig-speech','frames':s.frame_end,'fps':24,'width':576,'height':576,'voice_seconds':duration,'video_seconds':s.frame_end/24,'elapsed_seconds':round(time.monotonic()-T,2),'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'mouth_segments':len(cues),'controls':['BlinkL','BlinkR','JawOpen','Smile','BrowRaise','LipRound'],'checks':['skin jaw and lips follow real voice cues','silent X cues have closed jaw','eyeball assemblies are not animated or scaled for blink'],'limitations':['approximate phonetic mapping','preset adult voice, not the original actor','procedural facial proportions and lip anatomy require more work','not original-character or broadcast-quality equivalence']}
(out/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
