"""20,000 unique hypotheses, two evidence-driven rounds. Numeric tests, NOT renders."""
import json,math,hashlib,time,collections,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
import os
R=Path(__file__).parent;SRC=Path(os.environ['MOTION_FIXTURES']); FPS=24;N=312;T=np.arange(N)/FPS
AUD=json.loads((SRC/'audio-motion.json').read_text());RMS=np.array(AUD['rms']);LINES=AUD['speech']
ACTIVE=np.array([any(l['start']<=t<=l['end'] for l in LINES) for t in T]);REST=np.array([not any(l['start']-.12<=t<=l['end']+.4 for l in LINES) for t in T])
SEED=202610260004
# Predeclared engineering gates. They are not a visual naturalness rating.
GATES={'max_mouth_step':.20,'min_active_mouth_mean':.20,'min_peak_open':.60,'max_rest_open':.035,'min_audio_envelope_correlation':.68,'max_envelope_lag_frames':2,'max_hand_velocity_deg_per_frame':1.8,'max_hand_acceleration_deg_per_frame2':.48,'min_hand_peak_degrees':2.0,'max_head_velocity_px_per_frame':1.5,'max_head_acceleration_px_per_frame2':.65,'min_nod_peak_pixels':2.0,'min_sampled_linearized_jacobian':.50,'max_blink_seconds':.38,'min_blink_seconds':.16,'min_tail_peak_deg':.45,'max_tail_velocity_deg_per_frame':.55,'max_bird_velocity_px_per_frame':.65}
(R/'gates.json').write_text(json.dumps(GATES,indent=2))
def pulse(start,end):
 u=np.clip((T-start)/(end-start),0,1);return np.where((T>=start)&(T<=end),np.sin(np.pi*u)**2,0)
E=np.sin(np.pi*np.arange(N)/(N-1))**2
WP=pulse(.4,2.9)+pulse(3.25,5.95);NP=pulse(6.5,8.6);TP=pulse(9.1,12.8);BP=pulse(.3,5.9)
# Fixed pixel mask derivatives for sampled local deformation safety; actual raster QA is separate.
w,h=1280,720;s=w/1672;y,x=np.mgrid[0:h,0:w].astype(np.float32)
def mask(points,blur):
 im=Image.new('L',(w,h));ImageDraw.Draw(im).polygon([(int(a*s),int(b*s)) for a,b in points],fill=255);return np.asarray(im.filter(ImageFilter.GaussianBlur(blur*s)),dtype=np.float32)/255
head=mask([(550,0),(736,0),(829,51),(862,145),(864,235),(807,296),(789,341),(748,375),(694,393),(602,395),(547,371),(476,367),(400,361),(359,324),(339,251),(360,162),(401,79),(474,35)],14)
arm=mask([(788,397),(810,385),(832,365),(823,338),(823,321),(835,315),(847,330),(851,293),(863,286),(871,307),(878,291),(891,291),(893,307),(907,303),(914,315),(906,333),(916,331),(924,342),(913,357),(895,379),(874,386),(859,417),(839,442),(815,455),(794,447)],10)
hand=mask([(832,370),(828,342),(824,321),(837,316),(848,330),(852,292),(865,289),(872,307),(880,292),(891,293),(893,307),(907,305),(914,316),(906,333),(916,331),(924,343),(913,357),(893,378),(868,388),(848,384)],7)
tail=mask([(881,529),(914,531),(943,555),(952,594),(960,632),(968,664),(944,672),(927,637),(920,605),(906,574),(889,558)],9)
bird=mask([(957,135),(983,155),(1013,171),(1045,166),(1093,177),(1126,211),(1179,228),(1199,248),(1169,277),(1128,288),(1102,314),(1069,330),(1025,340),(982,328),(959,296),(954,264),(940,229),(942,182)],9)
bases=[]
def basis(m,cx,cy):
 dx=(y-cy*s)*m;dy=-(x-cx*s)*m
 return np.array([np.gradient(dx,axis=1),np.gradient(dx,axis=0),np.gradient(dy,axis=1),np.gradient(dy,axis=0)])
for m,cx,cy in [(head,650,385),(arm,803,425),(hand,856,375),(tail,947,666)]:bases.append(basis(m,cx,cy))
for m in [head,bird]:bases.append(np.array([np.zeros_like(m),np.zeros_like(m),np.gradient(m,axis=1),np.gradient(m,axis=0)]))
bases=np.array(bases);importance=np.max(abs(bases),axis=(0,1));inds=[]
# Max derivative points in 24x16 spatial tiles include edge risks, not just arbitrary landmarks.
for yy in range(0,h,45):
 for xx in range(0,w,54):
  tile=importance[yy:yy+45,xx:xx+54]
  if tile.max()>.005:
   iy,ix=np.unravel_index(tile.argmax(),tile.shape);inds.append((yy+iy)*w+xx+ix)
J=bases.reshape(6,4,-1)[:,:,inds].astype(np.float32);del bases

def control(c):
 raw=np.clip((RMS-c['noise_floor'])/c['gain_divisor'],0,1)**c['gamma'];out=np.empty(N);v=0
 for i,r in enumerate(raw):
  near=any(l['start']-.04<=T[i]<=l['end']+c['silence_grace'] for l in LINES)
  if not near:r=0
  a=1-math.exp(-1/FPS/(c['attack_s'] if r>v else c['release_s']))
  nv=v+a*(r-v);nv=v+max(-c['slew'],min(c['slew'],nv-v))
  if not near and nv<.025:nv=0
  out[i]=nv;v=nv
 shift=c['audio_shift_frames']
 if shift>0:out=np.r_[np.zeros(shift),out[:-shift]]
 elif shift<0:out=np.r_[out[-shift:],np.zeros(-shift)]
 wave=WP*np.sin(2*np.pi*c['hand_hz']*T+c['hand_phase'])
 nod=NP*np.sin(2*np.pi*c['nod_hz']*(T-6.5)+c['nod_phase'])
 tailv=TP*np.sin(2*np.pi*c['tail_hz']*(T-9.1))
 birdv=BP*np.sin(2*np.pi*c['bird_hz']*T)
 return out,raw,wave,nod,tailv,birdv

def evaluate(c,return_controls=False):
 mouth,raw,wave,nod,tailv,birdv=control(c);reasons=[]
 corr=[]
 for lag in range(-4,5):
  aa=mouth[max(lag,0):N+min(lag,0)];bb=raw[max(-lag,0):N-min(max(lag,0),N)]
  corr.append(float(np.corrcoef(aa,bb)[0,1]) if aa.std()>.001 else 0)
 bestlag=int(np.argmax(corr))-4
 handv=(c['arm_deg']+c['wrist_deg'])*wave;headv=c['nod_pixels']*nod
 co=np.array([np.deg2rad(c['head_tilt_deg']*E*np.sin(2*np.pi*T/12)+c['nod_tilt_deg']*nod),np.deg2rad(c['arm_deg']*wave),np.deg2rad(c['wrist_deg']*wave),np.deg2rad(c['tail_deg']*tailv),headv*s,c['bird_pixels']*birdv*s],dtype=np.float32).T
 # All controls' extrema plus regular temporal samples. Full raster validation only for finalists.
 times=set(np.linspace(0,N-1,20).astype(int).tolist())
 for k in range(6):times.update(np.argsort(abs(co[:,k]))[-3:].tolist())
 js=np.einsum('tk,kdp->tdp',co[sorted(times)],J,optimize=False)
 jac=(1+js[:,0])*(1+js[:,3])-js[:,1]*js[:,2]
 m={'mouth_max_step':float(abs(np.diff(mouth)).max()),'mouth_active_mean':float(mouth[ACTIVE].mean()),'mouth_peak':float(mouth.max()),'rest_mouth_max':float(mouth[REST].max()),'audio_corr_zero_lag':corr[4],'audio_corr_best':max(corr),'audio_lag_frames':bestlag,'hand_peak_deg':float(abs(handv).max()),'hand_max_velocity':float(abs(np.diff(handv)).max()),'hand_max_acceleration':float(abs(np.diff(handv,n=2)).max()),'head_peak_px':float(abs(headv).max()),'head_max_velocity':float(abs(np.diff(headv)).max()),'head_max_acceleration':float(abs(np.diff(headv,n=2)).max()),'sampled_linearized_min_jacobian':float(jac.min()),'tail_peak_deg':float(abs(c['tail_deg']*tailv).max()),'tail_max_velocity':float(abs(np.diff(c['tail_deg']*tailv)).max()),'bird_max_velocity':float(abs(np.diff(c['bird_pixels']*birdv)).max()),'blink_seconds':c['blink_seconds'],'sampled_spatial_points':len(inds),'sampled_time_points':len(times)}
 tests=[('mouth_jitter',m['mouth_max_step']>.20+1e-9),('frozen_mouth',m['mouth_active_mean']<.20 or m['mouth_peak']<.60),('silence_residual',m['rest_mouth_max']>.035),('audio_detached',m['audio_corr_best']<.68),('mouth_latency',abs(bestlag)>2),('hand_jitter',m['hand_max_velocity']>1.8 or m['hand_max_acceleration']>.48),('frozen_hand',m['hand_peak_deg']<2),('head_jitter',m['head_max_velocity']>1.5 or m['head_max_acceleration']>.65),('frozen_nod',m['head_peak_px']<2),('warp_risk',m['sampled_linearized_min_jacobian']<.50),('blink_extreme',not .16<=c['blink_seconds']<=.38),('frozen_tail',m['tail_peak_deg']<.45),('animal_jitter',m['tail_max_velocity']>.55 or m['bird_max_velocity']>.65)]
 reasons=[k for k,v in tests if v]
 if return_controls:return m,reasons,{'mouth':mouth.tolist(),'wave':wave.tolist(),'nod':nod.tolist(),'tail':tailv.tolist(),'bird':birdv.tolist()}
 return m,reasons
RANGES={'attack_s':(.015,.18),'release_s':(.025,.32),'noise_floor':(.002,.019),'gain_divisor':(.04,.12),'gamma':(.42,1.0),'slew':(.07,.42),'silence_grace':(.03,.40),'arm_deg':(.5,9),'wrist_deg':(.2,6),'hand_hz':(.3,1.8),'hand_phase':(-.7,.7),'nod_pixels':(.5,10),'nod_hz':(.5,1.8),'nod_phase':(-.3,.3),'head_tilt_deg':(.1,1.1),'nod_tilt_deg':(.1,1.2),'tail_deg':(.1,4),'tail_hz':(.25,1.7),'bird_pixels':(.2,3.5),'bird_hz':(.25,1.5),'blink_seconds':(.10,.55),'blink_offset':(-.2,.2)}
BASE={'attack_s':.055,'release_s':.09,'noise_floor':.006,'gain_divisor':.07,'gamma':.65,'slew':.14,'silence_grace':.14,'audio_shift_frames':0,'arm_deg':3.5,'wrist_deg':2.5,'hand_hz':.95,'hand_phase':0,'nod_pixels':4.5,'nod_hz':1.1,'nod_phase':0,'head_tilt_deg':.45,'nod_tilt_deg':.6,'tail_deg':.7,'tail_hz':.65,'bird_pixels':.8,'bird_hz':.7,'blink_seconds':.27,'blink_offset':0}
(R/'baseline.json').write_text(json.dumps({'config':BASE,'metrics':evaluate(BASE)[0],'rejections':evaluate(BASE)[1]},indent=2))
start=time.time();rng=np.random.default_rng(SEED);seen=set();passed=[];summaries=[]
with (R/'trials.jsonl').open('w') as f:
 for roundno in [1,2]:
  counts=collections.Counter();localpass=[];t0=time.time()
  if roundno==2:
   # Hypothesis update from observed passing distributions; no silent gate changes.
   if not passed:raise RuntimeError('No first-round survivors. Analyze logged reasons before second round.')
   newranges={}
   for k,(lo,hi) in RANGES.items():
    vals=[r['config'][k] for r in passed];qlo,qhi=np.quantile(vals,[.05,.95]);pad=.08*(hi-lo)
    newranges[k]=(float(max(lo,qlo-pad)),float(min(hi,qhi+pad)))
   # Direct failure-specific constraints established by rejection evidence.
   newranges['attack_s']=(max(.02,newranges['attack_s'][0]),min(.085,newranges['attack_s'][1]))
   newranges['release_s']=(max(.04,newranges['release_s'][0]),min(.14,newranges['release_s'][1]))
   newranges['slew']=(max(.10,newranges['slew'][0]),min(.20,newranges['slew'][1]))
   newranges['silence_grace']=(.05,.16);newranges['blink_seconds']=(.18,.34)
   ranges=newranges
   (R/'round-2-hypothesis.json').write_text(json.dumps({'reason':'Refine first-round failure modes without changing gates; quantile bounds from survivors plus explicit latency/silence/blink limits.','first_round_rejections':dict(summaries[0]['rejection_counts']),'ranges':ranges,'audio_shift_frames':[0,1]},indent=2))
  else:ranges=RANGES
  for j in range(10000):
   c={k:round(float(rng.uniform(lo,hi)),7) for k,(lo,hi) in ranges.items()};c['audio_shift_frames']=int(rng.integers(-3,5)) if roundno==1 else int(rng.integers(0,2))
   raw=json.dumps(c,sort_keys=True,separators=(',',':'));sha=hashlib.sha256(raw.encode()).hexdigest();assert sha not in seen;seen.add(sha)
   m,why=evaluate(c);rec={'id':(roundno-1)*10000+j+1,'round':roundno,'seed':SEED,'config_sha256':sha,'config':c,'metrics':m,'accepted':not why,'rejections':why};f.write(json.dumps(rec,separators=(',',':'))+'\n')
   counts.update(why)
   if not why:passed.append(rec);localpass.append(rec)
  f.flush();summary={'round':roundno,'trials':10000,'accepted':len(localpass),'rejected':10000-len(localpass),'rejection_counts':dict(counts),'seconds':time.time()-t0};summaries.append(summary);print(json.dumps(summary),flush=True)
# Diverse engineering tradeoffs, not one fabricated naturalness score.
choices=[];used=set()
def choose(label,key):
 for r in sorted(passed,key=key):
  if r['config_sha256'] not in used:
   used.add(r['config_sha256']);r=dict(r);r['selection_reason']=label;choices.append(r);break
choose('lowest mouth latency, then envelope correspondence',lambda r:(abs(r['metrics']['audio_lag_frames']),-r['metrics']['audio_corr_zero_lag']))
choose('smoothest accepted mouth transitions',lambda r:r['metrics']['mouth_max_step'])
choose('largest accepted safe hand greeting',lambda r:-r['metrics']['hand_peak_deg'])
choose('highest sampled deformation margin',lambda r:-r['metrics']['sampled_linearized_min_jacobian'])
choose('balanced baseline-near motion with strong envelope correspondence',lambda r:abs(r['config']['arm_deg']+r['config']['wrist_deg']-5)+abs(r['config']['nod_pixels']-4)*.3+abs(r['metrics']['audio_lag_frames'])*.5-r['metrics']['audio_corr_zero_lag'])
for i,r in enumerate(choices):
 m,why,controls=evaluate(r['config'],True);r['controls']=controls;(R/f'finalist-{i+1}.json').write_text(json.dumps(r,indent=2))
summary={'seed':SEED,'unique_complete_configs':len(seen),'parameter_simulations':20000,'actual_frame_renders_during_search':0,'actual_video_renders_during_search':0,'total_accepted':len(passed),'rounds':summaries,'seconds':time.time()-start,'gates':GATES,'finalists':[{'file':f'finalist-{i+1}.json','trial_id':r['id'],'reason':r['selection_reason']} for i,r in enumerate(choices)],'limits':['Parameter/trajectory tests are not full image renders.','Jacobian is a linearized spatial/time sample, not a whole-frame proof.','Audio correlation is amplitude correspondence, not phoneme alignment or naturalness.','All gates fixed before both rounds.']}
(R/'search-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
