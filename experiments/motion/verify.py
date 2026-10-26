"""Count independent ledger rows, verify canonical hashes and exact v2 linkage."""
import argparse,json,hashlib,itertools
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--expected-count',required=True,type=int);p.add_argument('--smoke',action='store_true');a=p.parse_args();root=Path(a.input)
selected={}
if not a.smoke:
 for name in ['search-summary-200k.json','validation-v2-summary.json']:
  for entry in json.loads((root/name).read_text())['finalists']:
   selected.setdefault(entry['trial_id'],[]).append((entry['file'],json.loads((root/entry['file']).read_text())))
seen=set();count=accepted=v2accepted=0;ledgerhash=hashlib.sha256();v2hash=hashlib.sha256()
with (root/'trials.jsonl').open() as f,(root/'validation-v2.jsonl').open() as g:
 for raw,vr in itertools.zip_longest(f,g):
  assert raw is not None and vr is not None,'Ledger lengths differ'
  r=json.loads(raw);v=json.loads(vr);count+=1
  digest=hashlib.sha256(json.dumps(r['config'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
  assert digest==r['config_sha256'] and digest not in seen
  seen.add(digest);assert r['id']==count==v['id'] and v['config_sha256']==digest
  assert r['accepted']==(not r['rejections'])==v['v1_accepted']
  assert v['v2_new_checks_passed']==(not v['v2_rejections'])
  assert v['final_accepted']==(r['accepted'] and v['v2_new_checks_passed'])
  for filename,finalist in selected.get(count,[]):
   assert finalist['config']==r['config'] and finalist['config_sha256']==digest and r['accepted']
   if filename.startswith('finalist-v2-'):
    assert v['final_accepted'] and finalist['v2_metrics']==v['metrics']
  accepted+=r['accepted'];v2accepted+=v['final_accepted'];ledgerhash.update(raw.encode());v2hash.update(vr.encode())
assert count==a.expected_count
if not a.smoke:
 assert count==200000
 s=json.loads((root/'search-summary-200k.json').read_text());v=json.loads((root/'validation-v2-summary.json').read_text())
 assert s['unique_complete_configs']==s['parameter_simulations']==count
 assert s['total_accepted']==accepted and s['actual_frame_renders_during_search']==s['actual_video_renders_during_search']==0
 assert v['same_unique_configs_revalidated']==count and v['new_unique_configs_added']==0 and v['v2_survivors']==v2accepted
 for kind,summary in [('finalist',s),('finalist-v2',v)]:
  assert len(summary['finalists'])==5
  for entry in summary['finalists']:
   r=json.loads((root/entry['file']).read_text());assert r['id']==entry['trial_id'];assert r['config_sha256'] in seen
   assert r['config_sha256']==hashlib.sha256(json.dumps(r['config'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
report={'mode':'smoke' if a.smoke else 'full-reproduction','unique_parameter_simulations':count,'same_configs_revalidated_v2':count,'new_configs_in_v2':0,'v1_accepted':accepted,'v2_accepted':v2accepted,'raster_frames_rendered':0,'videos_rendered':0,'trials_file_sha256':ledgerhash.hexdigest(),'v2_file_sha256':v2hash.hexdigest()}
(root/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
