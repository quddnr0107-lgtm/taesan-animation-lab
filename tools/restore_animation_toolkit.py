"""Restore the exact collected revisions, verifying every file against the saved SHA-256 lock."""
import argparse,hashlib,json,pathlib
from collect_animation_toolkit import download
parser=argparse.ArgumentParser();parser.add_argument('--lock',default='results/010-toolkit-manifest.json');args=parser.parse_args()
manifest=json.loads(pathlib.Path(args.lock).read_text())
for source in manifest['sources']:
 for f in source['files']:
  path=pathlib.Path(f['path'])
  if path.is_absolute() or '..' in path.parts or path.parts[0]!='toolkit':raise ValueError('Unsafe lock path')
  if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256']:continue
  info=download(f['url'],path)
  if info['sha256']!=f['sha256']:
   path.unlink();raise ValueError('SHA-256 mismatch: '+str(path))
 print(source['id'],'restored',flush=True)
