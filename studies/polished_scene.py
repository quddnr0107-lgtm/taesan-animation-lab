"""012: rebuild lid closure, relight the existing CPU scene, then review stills.

Run after opening input/continuous-face.blend. STILL_ONLY defaults to 1.
Set STILL_ONLY=0 for the reviewed 77-frame animation. No image projection.
"""
import bpy, json, math, os, time, resource
from pathlib import Path
from mathutils import Vector

started = time.monotonic()
out = Path('output'); out.mkdir(exist_ok=True)
s = bpy.context.scene
face = bpy.data.objects['continuous facial shell']
head = face.parent
keys = face.data.shape_keys.key_blocks
face.data.shape_keys.animation_data_clear()

def surface_y(x, z):
    taper = 1 - .16 * max(0, min(1, (-z-.15)/.44))**.75
    return -.47 * math.sqrt(max(.001, 1-(x/taper/.66)**2-(z/.59)**2))

def smoothstep(x):
    x=max(0., min(1., x)); return x*x*(3-2*x)

# The old closed lid followed a minimum over separate eyeball surfaces.
# A smooth annular offset removes the resulting ridges in the depth field.
lid_count = 0
for side, ex in [('L', -.235), ('R', .235)]:
    key = keys['Blink'+side]
    for i, b in enumerate(keys['Basis'].data):
        if (key.data[i].co-b.co).length < 1e-8:
            continue
        x,y,z=b.co; lo,hi=0.,1.
        for _ in range(24):
            t=(lo+hi)/2; rx=.148-.027*t; rz=.153-.028*t
            q=((x-ex)/rx)**2+((z+.005)/rz)**2
            if q>1: hi=t
            else: lo=t
        t=(lo+hi)/2
        angle=math.atan2((z+.005)/(.153-.028*t),(x-ex)/(.148-.027*t))
        closed_z=-.005+(1-t)*.153*math.sin(angle)
        key.data[i].co=(x,surface_y(x,closed_z)-.064*smoothstep(t),closed_z)
        lid_count += 1
    lashes=bpy.data.objects.get('skin driven lashes '+side)
    if lashes and lashes.data.shape_keys:
        basis= lashes.data.shape_keys.key_blocks['Basis']
        target=lashes.data.shape_keys.key_blocks['Blink'+side]
        for i,b in enumerate(basis.data):
            x=b.co.x; z=-.005+(i%2)*.005
            target.data[i].co=(x,surface_y(x,-.005)-.068,z)

# Widen the tiny mouth aperture while keeping the rest of the face continuous.
for key in keys:
    for point in key.data:
        x,y,z=point.co
        if y<0:
            weight=math.exp(-(x/.22)**4-((z+.29)/.095)**2)
            nx=x*(1+.35*weight)
            point.co.x=nx
            point.co.y=y+surface_y(nx,z)-surface_y(x,z)

def material(name, color, roughness=.6, specular=.3):
    m=bpy.data.materials.get(name)
    if not m: return
    p=m.node_tree.nodes.get('Principled BSDF')
    m.diffuse_color=(*color,1)
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=roughness
    p.inputs['Specular'].default_value=specular

material('chestnut hair',(.075,.025,.012),.43,.3)
material('fine hair flow',(.085,.032,.015),.52,.25)
material('raspberry cotton',(.62,.023,.055),.86,.17)
material('muted teal skirt',(.11,.37,.35),.86,.17)
material('ribbon pink',(.82,.19,.26),.56,.25)
material('brown irises',(.13,.055,.017),.24,.45)
material('eye whites',(.96,.94,.86),.28,.35)
material('warm cream wall',(.72,.64,.49),.88,.1)
material('window sage',(.33,.48,.29),.75,.15)
material('blue window',(.42,.65,.80),.75,.12)
for m in bpy.data.materials:
    if 'skin' in m.name or m.name=='warm porcelain skin':
        if not m.use_nodes: continue
        p=m.node_tree.nodes.get('Principled BSDF')
        if not p: continue
        p.inputs['Roughness'].default_value=.55
        p.inputs['Specular'].default_value=.27
        p.inputs['Subsurface'].default_value=.06
        p.inputs['Subsurface Radius'].default_value=(1,.42,.23)

# Leave the identity and editable 3D construction intact; tame the helmet width.
for obj in bpy.data.objects:
    if obj.name.startswith(('side wave','hair silhouette')):
        obj.scale.x *= .94
    if obj.name.startswith('hair flow groove'):
        obj.hide_render=True
    if obj.name.startswith('backpack strap') and obj.type=='CURVE':
        obj.data.bevel_depth=.019
    if obj.name.startswith('eye assembly'):
        obj.animation_data_clear()
    if obj.name.startswith('iris') and obj.type=='MESH':
        obj.scale.x*=.92; obj.scale.z*=.92
    if obj.name.startswith('pupil') and obj.type=='MESH':
        obj.scale.x*=.94; obj.scale.z*=.94

def ellipsoid(name, location, scale, material_name):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20)
    obj=bpy.context.object; obj.name=name; obj.parent=head
    obj.location=location; obj.scale=scale
    obj.data.materials.append(bpy.data.materials[material_name])
    for poly in obj.data.polygons: poly.use_smooth=True
    return obj

ellipsoid('polished upper teeth',(0,-.373,-.273),(.078,.012,.012),'ivory')
ellipsoid('polished tongue',(0,-.366,-.321),(.060,.012,.015),'tongue')
cavity=bpy.data.objects.get('inner mouth cavity')
if cavity: cavity.scale.x=.18

# Face-scale ambient occlusion, soft warm key and brighter window separation.
s.render.engine='BLENDER_EEVEE'
s.eevee.use_gtao=True; s.eevee.gtao_distance=.18; s.eevee.gtao_factor=.65
s.eevee.use_soft_shadows=True
s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs[0].default_value=(.30,.38,.49,1)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.40
for obj in list(bpy.data.objects):
    if obj.type=='LIGHT': bpy.data.objects.remove(obj,do_unlink=True)
for name,loc,energy,size,color in [
    ('soft warm key',(-3,-4,5),850,4.5,(1,.83,.65)),
    ('broad neutral fill',(3,-3,3.2),450,5,(.83,.90,1)),
    ('window rim',(-1,2.5,4.4),1000,3,(1,.89,.69))]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    light=bpy.context.object; light.name=name
    light.data.energy=energy; light.data.size=size; light.data.color=color
    light.rotation_euler=(Vector((0,0,1.8))-light.location).to_track_quat('-Z','Y').to_euler()
s.view_settings.view_transform='Filmic'
s.view_settings.look='Medium High Contrast'; s.view_settings.exposure=.55
s.view_settings.gamma=1
s.render.resolution_x=int(os.environ.get('WIDTH','960'))
s.render.resolution_y=int(os.environ.get('HEIGHT','540'))
s.render.resolution_percentage=100; s.render.fps=24
s.render.image_settings.file_format='PNG'; s.render.film_transparent=False
cam=s.camera; cam.animation_data_clear(); cam.location=(.45,-4.80,2.30)
cam.data.lens=50
focus=bpy.data.objects.get('camera focus'); focus.location=(.07,0,1.86)
cam.data.dof.use_dof=True; cam.data.dof.focus_object=focus; cam.data.dof.aperture_fstop=3.5

# Filter AFTER the RMS gate. The previous experiment filtered before the gate,
# which restored a one-frame step when speech resumed. Offline look-ahead is explicit.
control_path=Path(os.environ.get('CONTROL_PATH','results/011-neural-controls.json'))
source=json.loads(control_path.read_text())
kernel=[1/9,2/9,3/9,2/9,1/9]
tracks={}
for name in ['JawOpen','LipRound','Smile']:
    tracks[name]=[sum(kernel[j]*source[max(0,min(len(source)-1,i+j-2))][name]
                      for j in range(5)) for i in range(len(source))]
jaw_peak=max(tracks['JawOpen'])
gain=min(3.,.65/jaw_peak) if jaw_peak else 1.
root=bpy.data.objects.get('child_root'); root.animation_data_clear(); head.animation_data_clear()
shoulders=sorted([o for o in bpy.data.objects if o.name.startswith('shoulder')],key=lambda o:o.location.x)
for obj in shoulders: obj.animation_data_clear()
applied=[]
for i,row in enumerate(source):
    f=i+1; t=i/24
    values={'JawOpen':min(.75,tracks['JawOpen'][i]*gain),
            'LipRound':tracks['LipRound'][i],
            'Smile':min(.28,tracks['Smile'][i]*1.5+.055),
            'BrowRaise':.20*math.exp(-((t-1.6)/.7)**2),
            'BlinkL':row['BlinkL'],'BlinkR':row['BlinkR']}
    for name,value in values.items():
        keys[name].value=value; keys[name].keyframe_insert('value',frame=f)
    # Slightly raised brow curves accompany authored secondary expression.
    for obj in bpy.data.objects:
        if obj.name.startswith('fine eyebrow'):
            obj.location.z=.045*values['BrowRaise']; obj.keyframe_insert('location',frame=f)
    root.location.z=.006*math.sin(t*2.4); root.rotation_euler.z=.012*math.sin(t*1.8)
    root.keyframe_insert('location',frame=f); root.keyframe_insert('rotation_euler',frame=f)
    head.rotation_euler=(.02*math.sin(t*2),-.045*math.sin(t*1.6),-.035*math.sin(t*1.8))
    head.keyframe_insert('rotation_euler',frame=f)
    lift=smoothstep((t-.15)/.7)*(1-.35*smoothstep((t-2.65)/.55))
    if len(shoulders)==2:
        shoulders[1].rotation_euler.y=(-1.65+.13*math.sin(t*7))*lift
        shoulders[0].rotation_euler.y=.18+.035*math.sin(t*2)
        for obj in shoulders: obj.keyframe_insert('rotation_euler',frame=f)
    applied.append({'frame':f,'time':t,**values})
for obj in [root,head,*shoulders]:
    if obj.animation_data and obj.animation_data.action:
        for curve in obj.animation_data.action.fcurves:
            for keyframe in curve.keyframe_points: keyframe.interpolation='LINEAR'
for curve in face.data.shape_keys.animation_data.action.fcurves:
    for keyframe in curve.keyframe_points: keyframe.interpolation='LINEAR'
s.frame_start=1; s.frame_end=len(source)
(out/'polished-controls.json').write_text(json.dumps(applied,indent=2))

still_only=os.environ.get('STILL_ONLY','1')!='0'
s.eevee.taa_render_samples=int(os.environ.get('STILL_SAMPLES','32'))
s.frame_set(54); bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str((out/'polished-scene.blend').resolve()))
s.render.filepath=str(out/'hero.png'); bpy.ops.render.render(write_still=True)
s.frame_set(61); s.render.filepath=str(out/'blink.png'); bpy.ops.render.render(write_still=True)
stills_seconds=round(time.monotonic()-started,2)
if not still_only:
    s.eevee.taa_render_samples=int(os.environ.get('ANIMATION_SAMPLES','8'))
    s.render.filepath=str(out/'frame_'); bpy.ops.render.render(animation=True)
stats={name:{'max':max(r[name] for r in applied),
             'max_frame_delta':max(abs(a[name]-b[name]) for a,b in zip(applied,applied[1:]))}
       for name in ['JawOpen','LipRound','Smile','BrowRaise']}
report={'experiment':'012-polished-cpu-scene','mode':'stills' if still_only else 'animation',
        'width':s.render.resolution_x,'height':s.render.resolution_y,'fps':24,
        'rendered_frames':2 if still_only else len(source)+2,'animation_frames':0 if still_only else len(source),
        'stills_seconds':stills_seconds,'elapsed_seconds':round(time.monotonic()-started,2),
        'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'rebuilt_lid_vertices':lid_count,'jaw_gain':gain,'controls':stats,
        'changes':['smooth analytic lid depth','wider mouth aperture and interior details',
                   'face-scale AO and new soft lights','Filmic color management','material and framing adjustments',
                   'post-gate offline smoothing','authored brow and smile secondary expression'],
        'limitations':['No Gemini or target-image quality equivalence established',
                       'Still review required before full render','Five-frame filter uses future frames',
                       'Brow and smile secondary animation is authored, not inferred',
                       'Procedural character and preset voice remain; not a completed episode']}
(out/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
