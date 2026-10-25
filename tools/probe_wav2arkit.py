"""Inspect and run downloaded ONNX on CPU using an existing Korean voice and matched silence."""
import hashlib,json,pathlib,time,wave,resource
import numpy as np
import onnxruntime as ort
p=pathlib.Path('toolkit/wav2arkit-cpu');result={'status':'failed','provider':'CPUExecutionProvider'}
try:
 models=list(p.glob('**/*.onnx'));assert len(models)==1, str([str(m) for m in models])
 model=models[0];options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
 start=time.monotonic();session=ort.InferenceSession(str(model),sess_options=options,providers=['CPUExecutionProvider'])
 result['load_seconds']=round(time.monotonic()-start,4)
 result['inputs']=[{'name':x.name,'shape':x.shape,'type':x.type} for x in session.get_inputs()]
 result['outputs']=[{'name':x.name,'shape':x.shape,'type':x.type} for x in session.get_outputs()]
 assert len(session.get_inputs())==1
 with wave.open('studies/fixtures/004-voice.wav') as w:
  assert w.getframerate()==16000 and w.getnchannels()==1 and w.getsampwidth()==2
  audio=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32)/32768
 name=session.get_inputs()[0].name
 for label,a in [('korean',audio),('silence',np.zeros_like(audio))]:
  start=time.monotonic();outputs=session.run(None,{name:a.reshape(1,-1)});seconds=time.monotonic()-start
  values=outputs[0];assert np.isfinite(values).all();assert values.shape[-1]==52 and values.size>52
  np.save(p/(label+'-coefficients.npy'),values)
  (p/(label+'-coefficients.json')).write_text(json.dumps(values.tolist()))
  result[label]={'shape':list(values.shape),'seconds':round(seconds,4),'min':float(values.min()),'max':float(values.max()),'mean':float(values.mean()),'time_variation':float(np.std(values,axis=-2).mean())}
 result['korean_silence_mae']=float(np.abs(np.load(p/'korean-coefficients.npy')-np.load(p/'silence-coefficients.npy')).mean())
 assert result['korean_silence_mae']>1e-6,'Output insensitive to speech versus silence'
 result['status']='cpu-inference-passed';result['limitations']=['No rendered avatar quality claim','No Korean phoneme accuracy score','52 outputs require a corresponding authored facial rig','Model card speed/size claims are not assumed true']
except Exception as e:result['error']=type(e).__name__+': '+str(e)
result['max_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
(p/'cpu-probe.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
