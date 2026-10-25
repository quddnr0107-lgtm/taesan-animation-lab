"""Evaluate official public CPU TTS and phonetic mouth-cue tools; no voice cloning."""
import json, os, sys, time, subprocess, urllib.request, zipfile, hashlib, shutil
from pathlib import Path
T=time.monotonic();out=Path('output');out.mkdir(exist_ok=True)
from huggingface_hub import snapshot_download
rev='aafc6e32416a594460b32413efc49d7fe4ce6d46'
snapshot_download('supertone-oss-archive/supertonic-3',revision=rev,local_dir='/tmp/supertonic/assets',allow_patterns=['onnx/*','voice_styles/F1.json','voice_styles/F4.json','LICENSE*','README.md'])
text='안녕! 오늘은 무슨 놀이를 할까?'
for voice in ['F1','F4']:
 dest=out/voice;dest.mkdir(exist_ok=True)
 subprocess.run([sys.executable,'example_onnx.py','--n-test','1','--voice-style',f'../assets/voice_styles/{voice}.json','--text',text,'--lang','ko','--speed','1.12','--total-step','8','--save-dir',str(dest.resolve())],cwd='/tmp/supertonic/py',check=True)
# The upstream CLI returns sanitized filenames; resolve the actual generated WAV.
wavs=sorted((out/'F1').glob('*.wav'));assert len(wavs)==1,'Expected one generated Korean voice sample'
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(wavs[0]),'-ac','1','-ar','16000','-c:a','pcm_s16le',str(out/'voice.wav')],check=True)
req=urllib.request.Request('https://api.github.com/repos/DanielSWolf/rhubarb-lip-sync/releases/tags/v1.14.0',headers={'User-Agent':'taesan-animation-cpu-lab'})
release=json.load(urllib.request.urlopen(req));assets=[a for a in release['assets'] if 'Linux' in a['name'] and a['name'].endswith('.zip')];assert len(assets)==1
url=assets[0]['browser_download_url'];assert url.startswith('https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/')
p=out/'rhubarb.zip';urllib.request.urlretrieve(url,p)
with zipfile.ZipFile(p) as z:
 for n in z.namelist():assert '..' not in Path(n).parts and not n.startswith('/')
 z.extractall('/tmp/rhubarb')
bins=[x for x in Path('/tmp/rhubarb').rglob('rhubarb') if x.is_file()];assert len(bins)==1
bins[0].chmod(0o755)
subprocess.run([str(bins[0]),'-r','phonetic','-f','json','-o',str(out/'mouth-cues.json'),str(out/'voice.wav')],check=True)
cues=json.loads((out/'mouth-cues.json').read_text())['mouthCues'];assert cues and any(c['value']!='X' for c in cues)
assert all(c['end']>=c['start']>=0 for c in cues)
import soundfile as sf
import numpy as np
a,sr=sf.read(out/'voice.wav');rms=float(np.sqrt(np.mean(a*a)));assert sr==16000 and len(a)>sr and rms>.001
report={'text':text,'tts':'Supertonic 3 ONNX CPU','model_revision':rev,'voices':['F1','F4'],'selected_for_cues':'F1','sample_rate':sr,'duration_seconds':len(a)/sr,'rms':rms,'mouth_cue_count':len(cues),'mouth_cue_values':sorted(set(c['value'] for c in cues)),'rhubarb_version':'1.14.0','recognizer':'phonetic','elapsed_seconds':round(time.monotonic()-T,2),'limitations':['preset voices, not original actor voice','no voice cloning','mouth cues are provisional phonetic estimates','Korean pronunciation and acting require listening review','not yet attached to the rendered character']}
(out/'speech-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
manifest={'supertonic_source':subprocess.check_output(['git','-C','/tmp/supertonic','rev-parse','HEAD'],text=True).strip(),'model_revision':rev,'rhubarb_asset':url,'rhubarb_archive_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(out/'third-party-manifest.json').write_text(json.dumps(manifest,indent=2));p.unlink()
