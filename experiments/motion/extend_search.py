"""Append 180,000 trials to existing 20,000; checkpoint every 2,000."""
import os
from pathlib import Path
R=Path(__file__).parent
code=(R/'search.py').read_text().split('start=time.time();rng=')[0]
exec(compile(code,str(R/'search.py'),'exec'))
records=[];seen=set();passed=[]
with (R/'trials.jsonl').open() as f:
 for line in f:
  r=json.loads(line);seen.add(r['config_sha256']);records.append(r)
  if r['accepted']:passed.append(r)
assert len(seen)==len(records);assert len(records)>=20000
old_summary=json.loads((R/'search-summary.json').read_text());rng=np.random.default_rng(SEED+180000);start=time.time();summaries=[]
# Predeclared staged hypotheses based on completed first two rounds.
r3={'attack_s':(.025,.08),'release_s':(.04,.125),'noise_floor':(.003,.012),'gain_divisor':(.045,.095),'gamma':(.45,.85),'slew':(.10,.19),'silence_grace':(.05,.16),'arm_deg':(1.8,5.0),'wrist_deg':(.45,2.7),'hand_hz':(.40,1.05),'hand_phase':(-.7,.7),'nod_pixels':(2.3,5.2),'nod_hz':(.55,1.05),'nod_phase':(-.3,.3),'head_tilt_deg':(.15,.75),'nod_tilt_deg':(.15,.85),'tail_deg':(.55,2.3),'tail_hz':(.3,.8),'bird_pixels':(.45,2.0),'bird_hz':(.3,.9),'blink_seconds':(.18,.34),'blink_offset':(-.18,.18)}
# No gates relaxed; subsequent stages probe observed boundary behavior and jointly refine survivors.
with (R/'trials.jsonl').open('a') as out:
 for roundno in [3,4,5]:
  counts=collections.Counter();lp=[];t0=time.time()
  if roundno==3:ranges=r3;purpose='Target observed motion/animal jitter failures while preserving minimum expressiveness.'
  elif roundno==4:
   ranges={}
   for k,(lo,hi) in RANGES.items():
    vals=[r['config'][k] for r in passed if r['round']==3];qlo,qhi=np.quantile(vals,[.02,.98]);pad=.12*(hi-lo);ranges[k]=(float(max(lo,qlo-pad)),float(min(hi,qhi+pad)))
   purpose='Boundary challenge around third-round survivor support; half samples near parameter-range edges. Tests coupled-motion robustness rather than simply selecting low amplitudes.'
  else:
   pool=[r for r in passed if r['round']==4]
   ranges={k:tuple(float(q) for q in np.quantile([r['config'][k] for r in pool],[.03,.97])) for k in RANGES}
   purpose='Joint refinement using fourth-round stress survivors, preserving original engineering gates.'
  (R/f'round-{roundno}-hypothesis.json').write_text(json.dumps({'round':roundno,'purpose':purpose,'ranges':ranges,'gates_unchanged':True,'prior_rejections':summaries[-1]['rejection_counts'] if summaries else old_summary['rounds'][-1]['rejection_counts']},indent=2))
  for j in range(60000):
   ident=20001+(roundno-3)*60000+j
   c={}
   for k,(lo,hi) in ranges.items():
    u=float(rng.random())
    if roundno==4 and j%2==0:u=.15*u if rng.random()<.5 else .85+.15*u
    c[k]=round(lo+(hi-lo)*u,7)
   c['audio_shift_frames']=int(rng.integers(0,2))
   raw=json.dumps(c,sort_keys=True,separators=(',',':'));sha=hashlib.sha256(raw.encode()).hexdigest()
   # Exact deterministic resume: generated earlier identities must match, not be re-counted.
   if ident<=len(records):
    prior=records[ident-1];assert prior['config_sha256']==sha
    if prior['accepted']:lp.append(prior)
    counts.update(prior['rejections']);continue
   assert sha not in seen;seen.add(sha)
   m,why=evaluate(c);rec={'id':ident,'round':roundno,'seed':SEED+180000,'config_sha256':sha,'config':c,'metrics':m,'accepted':not why,'rejections':why};out.write(json.dumps(rec,separators=(',',':'))+'\n');counts.update(why)
   if not why:passed.append(rec);lp.append(rec)
   if ident%2000==0:
    out.flush();os.fsync(out.fileno());checkpoint={'completed_unique_trials':ident,'round':roundno,'accepted_total':len(passed),'last_config_sha256':sha,'seconds_this_extension':time.time()-start,'actual_video_renders':0};tmp=R/'checkpoint.tmp';tmp.write_text(json.dumps(checkpoint,indent=2));tmp.replace(R/'checkpoint.json');print(json.dumps(checkpoint),flush=True)
  summary={'round':roundno,'trials':60000,'accepted':len(lp),'rejected':60000-len(lp),'rejection_counts':dict(counts),'seconds':time.time()-t0,'hypothesis':purpose};summaries.append(summary);print('ROUND '+json.dumps(summary),flush=True)
# Choose five different engineering tradeoffs for real full-duration renders.
choices=[];used=set()
def choose(label,key):
 for r in sorted(passed,key=key):
  if r['config_sha256'] not in used:
   used.add(r['config_sha256']);rr=dict(r);rr['selection_reason']=label;choices.append(rr);return
choose('lowest latency with strongest zero-lag amplitude correspondence',lambda r:(abs(r['metrics']['audio_lag_frames']),-r['metrics']['audio_corr_zero_lag']))
choose('lowest accepted mouth-control step',lambda r:r['metrics']['mouth_max_step'])
choose('largest safe accepted hand expression',lambda r:-r['metrics']['hand_peak_deg'])
choose('maximum sampled warp margin with non-frozen movement',lambda r:-r['metrics']['sampled_linearized_min_jacobian'])
choose('balanced baseline-near motion and fast envelope correspondence',lambda r:abs(r['config']['arm_deg']+r['config']['wrist_deg']-5)*.3+abs(r['config']['nod_pixels']-3.5)*.2+abs(r['metrics']['audio_lag_frames'])*.4-r['metrics']['audio_corr_zero_lag'])
for i,r in enumerate(choices):
 m,why,controls=evaluate(r['config'],True);r['controls']=controls;(R/f'finalist-{i+1}.json').write_text(json.dumps(r,indent=2))
summary={**old_summary,'unique_complete_configs':len(seen),'parameter_simulations':len(seen),'total_accepted':len(passed),'rounds':old_summary['rounds']+summaries,'extension_seconds':time.time()-start,'finalists':[{'file':f'finalist-{i+1}.json','trial_id':r['id'],'reason':r['selection_reason']} for i,r in enumerate(choices)],'actual_frame_renders_during_search':0,'actual_video_renders_during_search':0}
assert len(seen)==200000
(R/'search-summary-200k.json').write_text(json.dumps(summary,indent=2));print('COMPLETE '+json.dumps(summary),flush=True)
