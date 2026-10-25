"""Assemble six independently rendered CPU shots into one measured minute."""
import hashlib,json,subprocess,wave
from pathlib import Path
from PIL import Image,ImageDraw,ImageStat

out=Path('output'); out.mkdir(exist_ok=True)
shots=[Path('shots')/f'shot_{i}' for i in range(6)]
for p in shots:
    assert (p/'shot.mp4').exists(),str(p)
listing=out/'concat.txt'
listing.write_text(''.join("file '"+str((p/'shot.mp4').resolve())+"'\n" for p in shots))
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(out/'joined.mp4')],check=True)
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
caption="subtitles=output/episode.srt:force_style='Fontname=Noto Sans CJK KR,Fontsize=22,Outline=2,Shadow=1,MarginV=20'"
title="drawtext=fontfile="+font+":text='몸으로 인사해요':x=20:y=16:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.25:boxborderw=6"
subprocess.run(['ffmpeg','-v','error','-y','-i',str(out/'joined.mp4'),'-i',str(out/'episode.wav'),'-vf',title+','+caption,'-map','0:v:0','-map','1:a:0','-c:v','libx264','-crf','22','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-t','60','-movflags','+faststart',str(out/'episode-minute.mp4')],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out/'episode-minute.mp4')]))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'])==(768,432)
assert int(v['nb_frames'])==1440 and v['r_frame_rate']=='24/1'
assert abs(float(v['duration'])-60)<.01 and abs(float(a['duration'])-60)<.08
with wave.open(str(out/'episode.wav')) as w: assert w.getnframes()/w.getframerate()==60
canvas=Image.new('RGB',(1152,480),'#ece5db');d=ImageDraw.Draw(canvas)
hashes=[]
for i,p in enumerate(shots):
    im=Image.open(p/'frame_0060.png').convert('RGB')
    st=ImageStat.Stat(im.convert('L'));assert st.mean[0]>10 and st.stddev[0]>10
    x=i%3*384;y=i//3*240
    canvas.paste(im.resize((384,216)),(x,y+24));d.text((x+12,y+6),f'Shot {i+1} / {i*10+5:02d}s',fill='#222222')
    hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
assert len(set(hashes))==6,'Shots must not be identical'
canvas.save(out/'contact-sheet.jpg',quality=90)
report={'duration_seconds':float(v['duration']),'audio_seconds':float(a['duration']),'width':768,'height':432,'output_fps':24,'output_frames':1440,'render_fps':12,'unique_rendered_frames':720,'shots':6,'speech_lines':12,'method':'Six new CPU 3D shots; each 12fps frame is held twice for 24fps delivery','video_sha256':hashlib.sha256((out/'episode-minute.mp4').read_bytes()).hexdigest(),'limitations':['RMS approximate mouth motion, not phoneme lip sync','Existing procedural character and adult preset voice','No quality equivalence to the generated target image or Gemini','No 24fps motion interpolation; frames are held twice']}
(out/'video-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
