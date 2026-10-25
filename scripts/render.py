import bpy, math, os, json, time, resource, platform
from mathutils import Vector
from pathlib import Path
start=time.monotonic()
out=Path('output'); out.mkdir(exist_ok=True)
prompt=os.environ.get('LAB_PROMPT','태산이가 손을 흔들며 인사한다')[:1000]
intent='surprise' if any(x in prompt for x in ['놀','깜짝']) else 'look' if any(x in prompt for x in ['고개','둘러']) else 'wave'
matched=intent!='wave' or any(x in prompt for x in ['인사','손','흔들'])
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
s=bpy.context.scene
s.render.engine='CYCLES'; s.cycles.device='CPU'; s.cycles.samples=2
s.cycles.use_denoising=False
s.render.use_compositing=False
s.render.use_sequencer=False
s.render.resolution_x=320; s.render.resolution_y=180; s.render.resolution_percentage=100
s.render.fps=16; s.frame_start=1; s.frame_end=96
s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.5,.6,.8,1)
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8
def mat(name,color):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1); return m
skin=mat('warm peach',(.92,.58,.36)); blue=mat('teal outfit',(.035,.46,.51)); dark=mat('espresso',(.055,.028,.025)); white=mat('cream',(.96,.94,.85)); yellow=mat('sunshine',(.95,.65,.12)); floor=mat('coral',(.61,.28,.22))
def sphere(name,pos,scale,material,parent=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=pos)
 o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 if parent:o.parent=parent
 return o
def pivot(name,pos,parent=None):
 o=bpy.data.objects.new(name,None); s.collection.objects.link(o); o.location=pos
 if parent:o.parent=parent
 return o
root=pivot('Taesan', (0,0,0))
sphere('shirt',(0,0,1.14),(.39,.24,.46),blue,root)
for x in [-.2,.2]:
 sphere('trousers',(x,0,.57),(.18,.20,.34),yellow,root)
 sphere('shoes',(x,-.10,.25),(.21,.30,.13),white,root)
head=pivot('head',(0,0,1.93),root)
sphere('face',(0,0,0),(.53,.40,.55),skin,head)
sphere('hair cap',(0,.03,.30),(.54,.39,.31),dark,head)
for x in [-.54,.54]:sphere('ear',(x,0,-.02),(.10,.12,.14),skin,head)
eyes=[]
for x in [-.18,.18]:
 sphere('eye white',(x,-.366,.04),(.12,.045,.15),white,head)
 eyes.append(sphere('pupil',(x,-.408,.03),(.060,.025,.085),dark,head))
 sphere('spark',(x-.015,-.433,.061),(.017,.008,.024),white,head)
sphere('nose',(0,-.416,-.10),(.065,.065,.07),skin,head)
mouth=sphere('mouth',(0,-.385,-.23),(.12,.022,.037),dark,head)
arm=pivot('wave shoulder',(.40,0,1.48),root)
sphere('sleeve',(.12,0,-.15),(.17,.19,.24),blue,arm)
sphere('hand',(.20,-.01,-.43),(.13,.12,.18),skin,arm)
sphere('left sleeve',(-.46,0,1.29),(.16,.18,.25),blue,root)
sphere('left hand',(-.51,-.01,.97),(.12,.12,.17),skin,root)
# A fixed, reusable room and props.
bpy.ops.mesh.primitive_plane_add(size=200); bpy.context.object.data.materials.append(floor)
for x,y,z in [(-1.6,.7,.45),(1.4,.8,.28)]:sphere('play cushion',(x,y,z),(.55,.45,z),yellow)
for i in range(3):sphere('toy ball',(1.15+i*.22,-.25,.14),(.14,.14,.14),[blue,white,yellow][i])
for loc,power,size in [((2,-4,6),650,5),((-4,-1,3),300,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.data.energy=power; l.data.shape='DISK'; l.data.size=size
 l.rotation_euler=(Vector((0,0,1.2))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(3,-7,3.0)); cam=bpy.context.object; s.camera=cam
cam.data.lens=48
target=pivot('camera target',(0,0,1.35))
track=cam.constraints.new('TRACK_TO'); track.target=target; track.track_axis='TRACK_NEGATIVE_Z'; track.up_axis='UP_Y'
for f in range(1,97):
 t=(f-1)/16
 root.location.z=.018*math.sin(t*3)
 root.keyframe_insert('location',frame=f)
 head.rotation_euler.y=.07*math.sin(t*2)
 head.rotation_euler.z=(.3*math.sin(t*1.8) if intent=='look' else .045*math.sin(t*2))
 head.keyframe_insert('rotation_euler',frame=f)
 arm.rotation_euler.y=(-2.3+.28*math.sin(t*8)) if intent=='wave' else (-1.2 if intent=='surprise' else -.12)
 arm.keyframe_insert('rotation_euler',frame=f)
 mouth.scale.z=.11 if intent=='surprise' and t>2 else .037
 mouth.keyframe_insert('scale',frame=f)
 for e in eyes:
  e.scale.z=.009 if f in [29,30,70,71] else .085
  e.keyframe_insert('scale',frame=f)
 cam.location=(2.7,-7,2.9) if f<33 else ((.6,-5,2.5) if f<65 else (-2.7,-6.4,2.8))
 cam.rotation_euler=(Vector((0,0,1.35))-cam.location).to_track_quat('-Z','Y').to_euler()
 cam.keyframe_insert('location',frame=f); cam.keyframe_insert('rotation_euler',frame=f)
# Three hard cuts; motion curves remain smooth.
for fc in cam.animation_data.action.fcurves:
 for k in fc.keyframe_points:k.interpolation='CONSTANT'
s.render.image_settings.file_format='PNG'; s.render.filepath=str(out/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'))
s.frame_set(1)
bpy.context.view_layer.update()
(out/'debug.json').write_text(json.dumps({'camera_position':list(cam.matrix_world.translation),'camera_forward':list(cam.matrix_world.to_quaternion() @ Vector((0,0,-1))),'face':list(bpy.data.objects['face'].matrix_world.translation),'lights':[{ 'name':o.name,'energy':o.data.energy,'position':list(o.matrix_world.translation)} for o in s.objects if o.type=='LIGHT']},indent=2))
bpy.ops.render.render(write_still=False)
s.render.filepath=str(out/'preflight.png'); bpy.data.images['Render Result'].save_render(s.render.filepath,scene=s)
im=bpy.data.images.load(str((out/'preflight.png').resolve()))
pix=list(im.pixels); rgb=[v for i,v in enumerate(pix) if i%4!=3]
mean=sum(rgb)/len(rgb); spread=max(rgb)-min(rgb)
(out/'visual-check.json').write_text(json.dumps({'mean_linear':mean,'range_linear':spread}))
assert mean>.01 and spread>.1, 'Black or blank preflight frame: abort before full render'
s.render.filepath=str(out/'frame_')
bpy.ops.render.render(animation=True)
report={'prompt':prompt,'intent':intent,'recognized_keyword':matched,'fallback':'default wave' if not matched else None,'engine':'Blender Cycles CPU','frames':96,'fps':16,'width':320,'height':180,'elapsed_seconds':round(time.monotonic()-start,2),'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'cpu_count':os.cpu_count(),'platform':platform.platform(),'blender':bpy.app.version_string,'limitations':['procedural prototype character','keyword routing only, not general prompt understanding','no speech or lip sync','not broadcast quality']}
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
