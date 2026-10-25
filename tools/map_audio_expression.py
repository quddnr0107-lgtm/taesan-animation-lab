"""Map the pinned CPU model outputs to the six authored controls, not a full ARKit rig."""
import json,math,wave,hashlib
from pathlib import Path
import numpy as np
p=Path('toolkit/wav2arkit-cpu');out=Path('output');out.mkdir(exist_ok=True)
voice=Path('studies/fixtures/004-voice.wav')
raw=np.asarray(json.loads((p/'korean-coefficients.json').read_text()),dtype=float)[0]
silence=np.asarray(json.loads((p/'silence-coefficients.json').read_text()),dtype=float)[0]
assert raw.shape[1]==52 and np.isfinite(raw).all()
floor=np.quantile(silence,.99,axis=0)+.003
corrected=np.maximum(0,raw-floor)
# Symmetric 5-frame smoothing is offline look-ahead, about 67ms each side at 30fps.
kernel=np.array([1,2,3,2,1],float)/9
smooth=np.stack([np.convolve(np.pad(corrected[:,i],(2,2),mode='edge'),kernel,mode='valid') for i in range(52)],axis=1)
with wave.open(str(voice)) as w:
 assert w.getframerate()==16000 and w.getsampwidth()==2 and w.getnchannels()==1
 audio=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
duration=len(audio)/16000;n=math.ceil(duration*24);frames=[]
for f in range(n):
 t=f/24
 v=np.array([np.interp(t,np.arange(len(smooth))/30,smooth[:,i]) for i in range(52)])
 center=int(t*16000);window=audio[max(0,center-320):min(len(audio),center+320)]
 rms=float(np.sqrt(np.mean(window*window))) if len(window) else 0
 gate=float(np.clip((rms-.003)/.012,0,1))
 # Timed blinking remains secondary animation; the voice model is not credited with generating it.
 blink=max(0,1-abs((f+1)-28)/2) if f<45 else max(0,1-abs((f+1)-61)/2)
 controls={'JawOpen':float(np.clip(v[24]*2.5,0,.9))*gate,
 'LipRound':float(np.clip(max(v[31],v[37])*3,0,.7))*gate,
 'Smile':float(np.clip((v[43]+v[44])*.75,0,.25))*gate,
 'BrowRaise':float(np.clip(max(v[2],v[3],v[4])*1.2,0,.15)),
 'BlinkL':blink,'BlinkR':blink}
 assert all(math.isfinite(x) and 0<=x<=1 for x in controls.values())
 if gate==0:assert controls['JawOpen']==controls['LipRound']==controls['Smile']==0
 frames.append({'frame':f+1,'time':t,'rms':rms,'speech_gate':gate,**controls})
assert any(x['JawOpen']>.05 for x in frames),'Neural jaw has no useful motion'
stats={k:{'min':min(x[k] for x in frames),'max':max(x[k] for x in frames),
'max_frame_delta':max(abs(b[k]-a[k]) for a,b in zip(frames,frames[1:]))} for k in controls}
report={'method':'CPU neural audio expressions with silent baseline subtraction, offline smoothing and audio energy gate',
'voice_sha256':hashlib.sha256(voice.read_bytes()).hexdigest(),'source_frames':len(raw),'source_fps':30,'source_channels':52,
'target_frames':n,'target_fps':24,'target_controls':6,
'neural_controls':['JawOpen','LipRound','Smile','BrowRaise'],'procedural_controls':['BlinkL','BlinkR'],
'mapping':{'JawOpen':['jawOpen'],'LipRound':['mouthFunnel','mouthPucker'],'Smile':['mouthSmileLeft','mouthSmileRight'],'BrowRaise':['browInnerUp','browOuterUpLeft','browOuterUpRight']},
'silent_frames':sum(x['speech_gate']==0 for x in frames),'stats':stats,
'limitations':['Six authored controls cannot reproduce all 52 ARKit expressions','Timed blinks are not model-generated','Offline centered filter uses future frames','No Korean phoneme accuracy or visual quality claim from coefficient checks']}
(out/'neural-controls.json').write_text(json.dumps(frames,indent=2));(out/'mapping-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
