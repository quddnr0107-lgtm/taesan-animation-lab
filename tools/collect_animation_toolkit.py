"""Download upstream source snapshots and an audio-to-expression model; never run upstream code."""
import concurrent.futures,hashlib,json,os,pathlib,tarfile,time,urllib.request,urllib.parse,zipfile,io
OUT=pathlib.Path('toolkit');OUT.mkdir(exist_ok=True)
MAX_FILE=512*1024*1024
def request(url):
 headers={'User-Agent':'TaesanAnimationLab-source-collector'}
 if urllib.parse.urlparse(url).hostname=='api.github.com' and os.getenv('GH_TOKEN'):
  headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
 return urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=90)
def api(url):
 with request(url) as r:return json.load(r)
def download(url,path):
 path.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();n=0
 try:
  with request(url) as r,path.open('wb') as f:
   while True:
    b=r.read(1024*1024)
    if not b:break
    n+=len(b)
    if n>MAX_FILE:raise ValueError('File exceeds 512 MiB collection limit')
    h.update(b);f.write(b)
 except Exception:
  path.unlink(missing_ok=True);raise
 return {'path':str(path),'bytes':n,'sha256':h.hexdigest(),'url':url}
def archive_inventory(path):
 with tarfile.open(path,'r:gz') as tf:
  names=[x.name for x in tf.getmembers() if x.isfile()]
 return {'members':len(names),'license_files':[n for n in names if pathlib.PurePosixPath(n).name.lower().startswith(('license','copying','notice'))][:150],
         'readme_files':[n for n in names if pathlib.PurePosixPath(n).name.lower().startswith('readme')][:50],
         'dependency_note':'Source snapshot only: submodules, LFS payloads, pretrained weights and runtime dependencies are not implied.'}
SOURCES=[
 {'id':'studio-pose-tools','kind':'gitea','repo':'studio/blender-studio-tools','purpose':'Pose Shape Keys, rigging tools and workflow source'},
 {'id':'cloudrig','kind':'gitea','repo':'Mets/CloudRig','purpose':'Generated body and facial control rigs'},
 {'id':'corrective-smooth','kind':'github-files','repo':'blender/blender','paths':['source/blender/modifiers/intern/MOD_correctivesmooth.cc','COPYING','README.md'],'purpose':'Built-in modifier implementation, not a standalone plugin'},
 {'id':'rokoko','kind':'github','repo':'Rokoko/rokoko-studio-live-blender','purpose':'Animation retargeting'},
 {'id':'mediapipe','kind':'github','repo':'google-ai-edge/mediapipe','purpose':'Face and pose capture source'},
 {'id':'lam-a2e','kind':'github','repo':'aigc3d/LAM_Audio2Expression','purpose':'Audio-driven facial expressions; upstream CUDA route'},
 {'id':'wav2arkit-cpu','kind':'huggingface','repo':'myned-ai/wav2arkit_cpu','purpose':'Third-party ONNX CPU audio-to-52-blendshape candidate'},
 {'id':'audio2face-sdk','kind':'github','repo':'NVIDIA/Audio2Face-3D-SDK','purpose':'GPU audio-driven facial animation SDK'},
 {'id':'unirig','kind':'github','repo':'VAST-AI-Research/UniRig','purpose':'GPU skeleton and skin-weight prediction'},
 {'id':'trellis2','kind':'github','repo':'microsoft/TRELLIS.2','purpose':'GPU image-to-3D generation'},
 {'id':'wan22','kind':'github','repo':'Wan-Video/Wan2.2','purpose':'GPU character animation and video generation'},
 {'id':'comfyui','kind':'github','repo':'Comfy-Org/ComfyUI','purpose':'Graph-based generation workflow engine'},
 {'id':'polyhaven-api','kind':'github','repo':'Poly-Haven/Public-API','purpose':'Official asset API integration source; not all hosted assets'},
]
def collect(item):
 r=dict(item);folder=OUT/item['id'];folder.mkdir(exist_ok=True);r['files']=[]
 try:
  repo=item['repo'];kind=item['kind']
  if kind.startswith('github'):
   meta=api('https://api.github.com/repos/'+repo);sha=api('https://api.github.com/repos/'+repo+'/commits/'+meta['default_branch'])['sha']
   r.update(revision=sha,license=(meta.get('license') or {}).get('spdx_id','NOASSERTION'))
   (folder/'upstream-metadata.json').write_text(json.dumps(meta,indent=2))
   if kind=='github':
    info=download('https://codeload.github.com/'+repo+'/tar.gz/'+sha,folder/'source.tar.gz');r['files'].append(info);r.update(archive_inventory(folder/'source.tar.gz'))
   else:
    for p in item['paths']:r['files'].append(download('https://raw.githubusercontent.com/'+repo+'/'+sha+'/'+p,folder/p))
    r['note']='Selected built-in source files, not a full Blender distribution.'
  elif kind=='gitea':
   root='https://projects.blender.org/api/v1/repos/'+repo
   meta=api(root);commits=api(root+'/commits?limit=1');sha=commits[0]['sha'];r['revision']=sha
   (folder/'upstream-metadata.json').write_text(json.dumps(meta,indent=2))
   info=download(root+'/archive/'+sha+'.tar.gz',folder/'source.tar.gz');r['files'].append(info);r.update(archive_inventory(folder/'source.tar.gz'))
  else:
   meta=api('https://huggingface.co/api/models/'+repo+'?blobs=true');sha=meta['sha'];r['revision']=sha
   (folder/'upstream-metadata.json').write_text(json.dumps(meta,indent=2))
   for x in meta.get('siblings',[]):
    p=x['rfilename'];pp=pathlib.PurePosixPath(p)
    if pp.is_absolute() or '..' in pp.parts:raise ValueError('Unsafe upstream filename')
    r['files'].append(download('https://huggingface.co/'+repo+'/resolve/'+sha+'/'+urllib.parse.quote(p,safe='/'),folder/p))
   r['license']=(meta.get('cardData') or {}).get('license','NOASSERTION')
  r['status']='downloaded';r['runtime_status']='not-installed-or-executed'
 except Exception as e:r['status']='failed';r['error']=type(e).__name__+': '+str(e)
 (folder/'collection.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
 print(item['id'],r['status'],sum(f['bytes'] for f in r['files']),flush=True)
 return r
if __name__=='__main__':
 start=time.monotonic()
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(collect,SOURCES))
 summary={'scope':'13 upstream source/model bundles from the capability map; not the entire internet, all model weights, or all asset libraries',
 'downloaded':sum(r['status']=='downloaded' for r in results),'failed':sum(r['status']=='failed' for r in results),'elapsed_seconds':round(time.monotonic()-start,2),'sources':results}
 (OUT/'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
 lines=['# Animation toolkit collection','',summary['scope'],'','Download success does not establish installability, license compatibility or visual quality.','', '| Bundle | Status | Revision | Bytes |','|---|---|---|---:|']
 for r in results:lines.append('| '+r['id']+' | '+r['status']+' | '+r.get('revision','')+' | '+str(sum(f['bytes'] for f in r['files']))+' |')
 (OUT/'README.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({k:v for k,v in summary.items() if k!='sources'}),flush=True)
