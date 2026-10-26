"""Isolated full reproduction, or explicitly non-equivalent bounded smoke test."""
import argparse,os,subprocess,sys,json,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--smoke-count',type=int);a=p.parse_args()
root=Path(__file__).resolve().parent;out=Path(a.output).resolve()
if out.exists() and any(out.iterdir()):raise SystemExit('Output must be empty: no overwriting/resume ambiguity')
out.mkdir(parents=True,exist_ok=True)
for name in ['search.py','extend_search.py','audit_v2.py']:shutil.copy2(root/name,out/name)
os.environ['MOTION_FIXTURES']=str(root/'fixtures')
if a.smoke_count is None:
 for name in ['search.py','extend_search.py','audit_v2.py']:
  subprocess.run([sys.executable,str(out/name)],check=True)
 subprocess.run([sys.executable,str(root/'verify.py'),'--input',str(out),'--expected-count','200000'],check=True)
else:
 n=a.smoke_count
 if not 1<=n<=1000:raise SystemExit('Smoke count must be 1..1000')
 ns={'__file__':str(out/'search.py')}
 exec(compile((out/'search.py').read_text().split('start=time.time();rng=')[0],str(out/'search.py'),'exec'),ns)
 np=ns['np'];rng=np.random.default_rng(ns['SEED']);records=[]
 for i in range(n):
  c={k:round(float(rng.uniform(lo,hi)),7) for k,(lo,hi) in ns['RANGES'].items()};c['audio_shift_frames']=int(rng.integers(-3,5))
  sha=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest();m,why=ns['evaluate'](c)
  records.append({'id':i+1,'config':c,'config_sha256':sha,'metrics':m,'accepted':not why,'rejections':why})
 (out/'trials.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
 # Audit module's existence guard only; explicitly labelled smoke, never 200k metadata.
 (out/'search-summary-200k.json').write_text(json.dumps({'mode':'smoke','parameter_simulations':n}))
 ns={'__file__':str(out/'audit_v2.py')}
 exec(compile((out/'audit_v2.py').read_text().split('start=time.time();counts=')[0],str(out/'audit_v2.py'),'exec'),ns)
 with (out/'validation-v2.jsonl').open('w') as f:
  for r in records:
   m,why,_=ns['validate'](r['config'])
   f.write(json.dumps({'id':r['id'],'config_sha256':r['config_sha256'],'v1_accepted':r['accepted'],'v2_new_checks_passed':not why,'final_accepted':r['accepted'] and not why,'v2_rejections':why,'metrics':m})+'\n')
 (out/'search-summary-200k.json').unlink()
 subprocess.run([sys.executable,str(root/'verify.py'),'--input',str(out),'--expected-count',str(n),'--smoke'],check=True)
