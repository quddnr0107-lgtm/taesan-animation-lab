"""Render one 10-second shot of episode 013 from the reviewed 012 Blender scene.

Open input/polished-scene.blend before executing this script. Each job renders
120 actual frames at 12 fps; assembly may duplicate frames to a 24 fps container.
Speech motion uses audio energy, not a phoneme recognizer or neural face model.
"""
import array
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import sys
import time
import wave

import bpy
from mathutils import Vector

started = time.monotonic()
shot = int(os.environ.get('SHOT_INDEX', '0'))
assert 0 <= shot <= 5, 'SHOT_INDEX must be 0..5'
FPS, COUNT, SECONDS = 12, 120, 60
out = Path('output') / ('shot_%d' % shot)
out.mkdir(parents=True, exist_ok=True)
audio_path = Path(os.environ.get('EPISODE_AUDIO', 'inputaudio/episode.wav'))
with wave.open(str(audio_path)) as reader:
    assert reader.getnchannels() == 1 and reader.getsampwidth() == 2, 'Expected mono PCM16 WAV'
    rate = reader.getframerate()
    samples = array.array('h', reader.readframes(reader.getnframes()))
if sys.byteorder != 'little':
    samples.byteswap()
assert abs(len(samples) / rate - SECONDS) < 1 / rate, 'Narration must be exactly 60 seconds'

# Compute a global curve once so shot boundaries cannot change normalization.
rms = []
for index in range(SECONDS * FPS):
    center = round(index * rate / FPS)
    radius = max(1, round(rate * .025))
    window = samples[max(0, center-radius):min(len(samples), center+radius)]
    rms.append(math.sqrt(sum(float(v)*v for v in window)/max(1, len(window))) / 32768)
active = sorted(v for v in rms if v > .003)
assert active, 'No speech energy in narration'
reference = max(.025, active[min(len(active)-1, int(len(active)*.95))])
raw_jaw = [.66 * math.sqrt(max(0., min(1., (v-.003)/reference))) for v in rms]
jaw = []
for index in range(len(raw_jaw)):
    jaw.append(sum(w*raw_jaw[max(0, min(len(raw_jaw)-1, index+offset))]
                   for offset, w in [(-1,.25), (0,.5), (1,.25)]))

s = bpy.context.scene
s.frame_set(1)
face = bpy.data.objects['continuous facial shell']
head = face.parent
root = bpy.data.objects['child_root']
body = bpy.data.objects['body']
keys = face.data.shape_keys.key_blocks
required = ['JawOpen','LipRound','Smile','BrowRaise','BlinkL','BlinkR']
assert all(name in keys for name in required)
shoulders = sorted([obj for obj in bpy.data.objects if obj.name.startswith('shoulder')],
                   key=lambda obj: obj.location.x)
assert len(shoulders) == 2, 'Expected two arm controls'
eyebrows = [obj for obj in bpy.data.objects if obj.name.startswith('fine eyebrow')]

# Preserve the lash shape-key drivers and object constraints; replace actions only.
for obj in bpy.data.objects:
    if obj.animation_data:
        obj.animation_data.action = None
if face.data.shape_keys.animation_data:
    face.data.shape_keys.animation_data.action = None
root.location = (0,0,0)
root.rotation_euler = (0,0,0)
head.rotation_euler = (0,0,0)
for obj in shoulders:
    obj.rotation_euler = (0,0,0)
shoulder_locations = [obj.location.copy() for obj in shoulders]
body_location = body.location.copy()
head_location = head.location.copy()

s.render.engine = 'BLENDER_EEVEE'
s.eevee.taa_render_samples = 4
s.render.resolution_x = 768
s.render.resolution_y = 432
s.render.resolution_percentage = 100
s.render.fps = FPS
s.render.fps_base = 1
s.frame_start, s.frame_end = 1, COUNT
s.render.image_settings.file_format = 'PNG'
s.render.image_settings.color_mode = 'RGB'
s.render.film_transparent = False
s.render.use_file_extension = True
s.render.threads_mode = 'FIXED'
s.render.threads = 4
# Keep the approved scene, with a small exposure reduction for its bright hands.
s.view_settings.exposure -= .20

cam = s.camera
focus = bpy.data.objects['camera focus']
camera_specs = [
    ((.40,-5.5,2.25),(0,0,1.70),46),
    ((-.65,-5.7,2.15),(0,0,1.68),46),
    ((.25,-4.95,2.25),(0,0,1.91),48),
    ((-.40,-6.60,2.30),(0,0,1.48),44),
    ((.25,-6.80,2.25),(0,0,1.46),44),
    ((.45,-5.40,2.22),(0,0,1.73),46),
]
camera_start, focus_location, lens = camera_specs[shot]
focus.location = focus_location
cam.location = camera_start
cam.data.lens = lens
cam.data.dof.use_dof = True
cam.data.dof.focus_object = focus
cam.data.dof.aperture_fstop = 5.6
if not any(c.type == 'TRACK_TO' for c in cam.constraints):
    constraint = cam.constraints.new('TRACK_TO')
    constraint.target = focus
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

def smoothstep(value):
    value = max(0., min(1., value))
    return value*value*(3-2*value)

def window(time_value, start, end, edge=.65):
    return smoothstep((time_value-start)/edge) * smoothstep((end-time_value)/edge)

blink_times = [2.65,6.90,12.40,17.50,22.60,27.70,32.80,37.20,42.90,47.40,52.60,57.70]
actions = ['greet','wave','nod','shrug','open_arms','goodbye']
applied = []
animated = [root, body, head, cam, *shoulders, *eyebrows]
for local_index in range(COUNT):
    frame = local_index + 1
    local_time = local_index / FPS
    global_index = shot*COUNT + local_index
    global_time = global_index / FPS
    engagement = window(local_time, .25, 9.85)
    demonstration = window(local_time, 1.0, 9.70)
    blink = max(max(0., 1-abs(global_time-b)/.13) for b in blink_times)
    opening = jaw[global_index]
    values = {
        'JawOpen': opening,
        'LipRound': .12*opening,
        'Smile': .065 + .045*engagement,
        'BrowRaise': .05 + .07*engagement*(.5+.5*math.sin(global_time*.9)),
        'BlinkL': blink, 'BlinkR': blink,
    }
    for name, value in values.items():
        assert math.isfinite(value) and 0 <= value <= 1
        keys[name].value = value
        keys[name].keyframe_insert('value', frame=frame)

    root.location = (.015*math.sin(global_time*.7),0,.007*math.sin(global_time*2.3))
    root.rotation_euler = (0,.012*math.sin(global_time*1.2),.010*math.sin(global_time*.8))
    body.location = body_location
    head.location = head_location
    head.rotation_euler = (.012*math.sin(global_time*1.7),.018*math.sin(global_time*1.1),
                           .024*math.sin(global_time*.8))
    for index, obj in enumerate(shoulders):
        obj.location = shoulder_locations[index]
        obj.rotation_euler = (0, .15 if index == 0 else -.15, 0)

    if shot in (0,1,5):
        speed = 4.2 if shot == 1 else 3.8
        lift = engagement
        shoulders[1].rotation_euler.y = (-1.50+.20*math.sin(local_time*speed))*lift
        shoulders[1].rotation_euler.x = .09*math.sin(local_time*speed+.4)*lift
        if shot == 1:
            shoulders[0].rotation_euler.y = (1.10+.18*math.sin(local_time*speed+1.4))*lift
        if shot == 5:
            head.rotation_euler.x += .09*window(local_time,7.2,9.8)*math.sin((local_time-7.2)*2.4)
    elif shot == 2:
        head.rotation_euler.x += .17*demonstration*math.sin((local_time-1)*3.5)
        shoulders[1].rotation_euler.y = -.45*engagement
    elif shot == 3:
        shrug = demonstration*(.5+.5*math.sin((local_time-1)*3.3))
        for index, obj in enumerate(shoulders):
            obj.location.z += .065*shrug
            obj.rotation_euler.y = (1 if index == 0 else -1)*(.22+.30*shrug)
        body.location.z += .012*shrug
        head.rotation_euler.y += .035*math.sin(local_time*2)*demonstration
    elif shot == 4:
        opening_arms = smoothstep((local_time-.6)/1.4)*(1-.30*smoothstep((local_time-8.1)/1.6))
        shoulders[0].rotation_euler.y = 1.35*opening_arms
        shoulders[1].rotation_euler.y = -1.35*opening_arms
        root.rotation_euler.y += .055*math.sin(local_time*1.5)*demonstration

    for obj in eyebrows:
        obj.location.z = .045*values['BrowRaise']
    # A slow camera drift is small enough to keep both hands inside the composition.
    cam.location = (camera_start[0]+.06*math.sin(local_time*.18),
                    camera_start[1]+.10*smoothstep(local_time/10), camera_start[2])
    for obj in animated:
        obj.keyframe_insert('location', frame=frame)
        obj.keyframe_insert('rotation_euler', frame=frame)
    applied.append({'frame':frame,'global_frame':global_index+1,'time':global_time,
                    'rms':rms[global_index],**values})

for obj in animated:
    if obj.animation_data and obj.animation_data.action:
        for curve in obj.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = 'LINEAR'
for curve in face.data.shape_keys.animation_data.action.fcurves:
    for point in curve.keyframe_points:
        point.interpolation = 'LINEAR'
assert len(applied) == 120
assert not any(obj.animation_data and obj.animation_data.action
               for obj in bpy.data.objects if obj.name.startswith('eye assembly'))
(out/'controls.json').write_text(json.dumps(applied,indent=2))
s.frame_set(1)
s.render.filepath = str(out/'frame_')
bpy.ops.render.render(animation=True)
files = list(out.glob('frame_*.png'))
assert len(files) == COUNT, 'Expected exactly 120 new rendered frames'
report = {
    'experiment':'013-one-minute-episode','shot':shot,'action':actions[shot],
    'global_start_seconds':shot*10,'global_end_seconds':(shot+1)*10,
    'rendered_frames':len(files),'fps':FPS,'width':768,'height':432,
    'duration_seconds':COUNT/FPS,'samples':s.eevee.taa_render_samples,
    'elapsed_seconds':round(time.monotonic()-started,2),
    'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'voice_sha256':hashlib.sha256(audio_path.read_bytes()).hexdigest(),
    'color_transform':s.view_settings.view_transform,
    'max_jaw':max(row['JawOpen'] for row in applied),
    'limitations':['Audio-energy mouth motion, not phoneme-accurate lip sync',
                   '12 unique animation frames per second; 24fps export duplicates frames',
                   'Existing procedural character and thick eyelid geometry retained',
                   'No Gemini or reference-quality equivalence claim'],
}
(out/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
