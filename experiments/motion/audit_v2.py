"""Re-evaluate SAME 200k unique configurations; do not count as new experiments."""
from pathlib import Path
R=Path(__file__).parent
exec(compile((R/'search.py').read_text().split('start=time.time();rng=')[0],str(R/'search.py'),'exec'))
import os
assert (R/'search-summary-200k.json').exists(),'Complete 200k ledger required'
V2_GATES={'fixed_reference_best_corr_min':.65,'fixed_reference_abs_lag_max_frames':2,'heldout_active_mouth_mean_min':.15,'heldout_rest_mouth_max':.035,'bird_actual_peak_px_min':.35,'combined_head_velocity_px_per_frame_max':1.8,'combined_head_acceleration_px_per_frame2_max':.75,'each_blink_peak_min':.95,'blink_step_max':.90}
(R/'v2-gates.json').write_text(json.dumps(V2_GATES,indent=2))
FIXED=np.clip((RMS-.006)/.07,0,1)**.65
trainR=RMS.copy();trainL=LINES.copy()
heldout=json.loads((SRC/'heldout-reference.json').read_text())
HOLD_RMS=np.array(heldout['rms']);HOLD_LINES=heldout['speech'];HOLD_FIXED=np.clip((HOLD_RMS-.006)/.07,0,1)**.65
HA=np.array([any(l['start']<=t<=l['end'] for l in HOLD_LINES) for t in T]);HR=np.array([not any(l['start']-.12<=t<=l['end']+.4 for l in HOLD_LINES) for t in T]);HEVAL=np.array([any(l['start']-.2<=t<=l['end']+.25 for l in HOLD_LINES) for t in T]);TEVAL=np.array([any(l['start']-.2<=t<=l['end']+.25 for l in trainL) for t in T])
# Fixed unmodified-reference envelopes; train/holdout excerpts contain different sentences.
(R/'heldout-reference.json').write_text(json.dumps({'source':'first eight seconds of existing minute audio, zero padded to13 seconds','speech':HOLD_LINES,'source_words':'안녕! 오늘은 몸으로 인사해요. 함께 천천히 따라 해 볼까요?','not_used_in_search':True,'rms':HOLD_RMS.tolist()},ensure_ascii=False,indent=2))
def corr(a,b):
 a=a-a.mean();b=b-b.mean();den=np.sqrt(np.dot(a,a)*np.dot(b,b));return float(np.dot(a,b)/den) if den>1e-10 else 0

def fixedcorr(m,ref,valid):
 scores=[]
 for lag in range(-4,5):
  ia=np.arange(max(lag,0),N+min(lag,0));ib=ia-lag;ok=valid[ib]
  scores.append(corr(m[ia[ok]],ref[ib[ok]]))
 lag=int(np.argmax(scores))-4;return scores[4],max(scores),lag

def blinkseries(c):
 dur=c['blink_seconds'];offset=c['blink_offset'];curves=[]
 for center in [2.8,6.18,8.72,11.96]:
  u=(T-(center+offset-dur*.5))/dur
  v=np.where((u>=0)&(u<.30),u/.30,np.where((u>=.30)&(u<=.55),1,np.where((u>.55)&(u<=1),(1-u)/.45,0)))
  curves.append(v)
 return np.max(curves,axis=0),curves

def validate(c):
 global RMS,LINES
 RMS=trainR;LINES=trainL
 mouth,raw,wave,nod,tailv,birdv=control(c);tr0,trbest,trlag=fixedcorr(mouth,FIXED,TEVAL)
 RMS=HOLD_RMS;LINES=HOLD_LINES
 hm,*_=control(c);h0,hbest,hlag=fixedcorr(hm,HOLD_FIXED,HEVAL)
 RMS=trainR;LINES=trainL
 bs,individual=blinkseries(c)
 angle=np.deg2rad(c['head_tilt_deg']*E*np.sin(2*np.pi*T/12)+c['nod_tilt_deg']*nod)
 # Exact rigid head rotation plus positive inverse-map translation, matching NEW renderer.
 motions=[]
 for px,py in [(650,40),(700,300),(810,300)]:
  qx=(px-650)*s;qy=(py-385)*s
  dx=(np.cos(angle)-1)*qx+np.sin(angle)*qy
  dy=-np.sin(angle)*qx+(np.cos(angle)-1)*qy+c['nod_pixels']*nod*s
  motions.append(np.stack([dx,dy],axis=1))
 hv=max(float(np.linalg.norm(np.diff(a,axis=0),axis=1).max()) for a in motions);ha=max(float(np.linalg.norm(np.diff(a,n=2,axis=0),axis=1).max()) for a in motions)
 m={'train_fixed_corr_zero':tr0,'train_fixed_corr_best':trbest,'train_fixed_lag':trlag,'heldout_fixed_corr_zero':h0,'heldout_fixed_corr_best':hbest,'heldout_fixed_lag':hlag,'heldout_active_mean':float(hm[HA].mean()),'heldout_rest_max':float(hm[HR].max()),'bird_peak_pixels':float(abs(c['bird_pixels']*birdv*s).max()),'combined_head_velocity':hv,'combined_head_acceleration':ha,'blink_peak_each':[float(a.max()) for a in individual],'blink_closed_frames_each':[int((a>=.95).sum()) for a in individual],'blink_max_step':float(abs(np.diff(bs)).max()),'blink_duration_seconds':c['blink_seconds'],'blink_offset_seconds':c['blink_offset']}
 reasons=[]
 if min(trbest,hbest)<.65:reasons.append('fixed_reference_correlation')
 if max(abs(trlag),abs(hlag))>2:reasons.append('fixed_reference_latency')
 if m['heldout_active_mean']<.15:reasons.append('heldout_frozen_mouth')
 if m['heldout_rest_max']>.035:reasons.append('heldout_silence_residual')
 if m['bird_peak_pixels']<.35:reasons.append('frozen_bird')
 if hv>1.8 or ha>.75:reasons.append('combined_head_jitter')
 if min(m['blink_peak_each'])<.95 or min(m['blink_closed_frames_each'])<1:reasons.append('blink_never_closes')
 if m['blink_max_step']>.9:reasons.append('blink_jitter')
 return m,reasons,{'mouth':mouth.tolist(),'wave':wave.tolist(),'nod':nod.tolist(),'tail':tailv.tolist(),'bird':birdv.tolist(),'blink':bs.tolist()}
start=time.time();counts=collections.Counter();survivors=[];n=0;byround=collections.Counter()
with (R/'validation-v2.jsonl').open('w') as out,(R/'trials.jsonl').open() as source:
 for line in source:
  r=json.loads(line);m,why,ct=validate(r['config']);ok=r['accepted'] and not why;n+=1;counts.update(why)
  out.write(json.dumps({'id':r['id'],'config_sha256':r['config_sha256'],'v1_accepted':r['accepted'],'v2_new_checks_passed':not why,'final_accepted':ok,'v2_rejections':why,'metrics':m},separators=(',',':'))+'\n')
  if ok:r['v2_metrics']=m;survivors.append(r);byround[r['round']]+=1
  if n%5000==0:
   out.flush();cp={'same_configurations_revalidated':n,'v2_survivors':len(survivors),'seconds':time.time()-start};(R/'v2-checkpoint.json').write_text(json.dumps(cp,indent=2));print(json.dumps(cp),flush=True)
assert n==200000
choices=[];used=set()
def choose(label,key):
 for r in sorted(survivors,key=key):
  if r['config_sha256'] not in used:
   used.add(r['config_sha256']);rr=dict(r);rr['selection_reason']=label;choices.append(rr);return
choose('fixed-reference low latency + heldout envelope correspondence',lambda r:(max(abs(r['v2_metrics']['train_fixed_lag']),abs(r['v2_metrics']['heldout_fixed_lag'])),-min(r['v2_metrics']['train_fixed_corr_zero'],r['v2_metrics']['heldout_fixed_corr_zero'])))
choose('smoothest accepted mouth',lambda r:r['metrics']['mouth_max_step'])
choose('expressive accepted hand',lambda r:-r['metrics']['hand_peak_deg'])
choose('largest sampled warp margin',lambda r:-r['metrics']['sampled_linearized_min_jacobian'])
choose('balanced motion and fixed-reference response',lambda r:abs(r['config']['arm_deg']+r['config']['wrist_deg']-5)*.3+abs(r['config']['nod_pixels']-3.5)*.2+max(abs(r['v2_metrics']['train_fixed_lag']),abs(r['v2_metrics']['heldout_fixed_lag']))*.4-min(r['v2_metrics']['train_fixed_corr_zero'],r['v2_metrics']['heldout_fixed_corr_zero']))
for i,r in enumerate(choices):
 m,why,controls=validate(r['config']);r['controls']=controls;(R/f'finalist-v2-{i+1}.json').write_text(json.dumps(r,indent=2))
summary={'same_unique_configs_revalidated':n,'new_unique_configs_added':0,'v2_survivors':len(survivors),'survivors_by_round':dict(byround),'additional_rejection_counts':dict(counts),'seconds':time.time()-start,'gates':V2_GATES,'finalists':[{'file':f'finalist-v2-{i+1}.json','trial_id':r['id'],'reason':r['selection_reason']} for i,r in enumerate(choices)],'limits':['Heldout audio is one different eight-second passage from same voice, not broad generalization.','Final visual selection still required; numerical acceptance is not naturalness.','Full-raster exact warp Jacobian checked only during actual finalist renders.']}
(R/'validation-v2-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
