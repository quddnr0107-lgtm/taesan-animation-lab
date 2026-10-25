"""Procedural reference study; no production assets or source footage embedded."""
import bpy, math, json, os, time, resource
from pathlib import Path
from mathutils import Vector
T=time.monotonic(); out=Path('output');out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE'
s.eevee.use_gtao=True;s.eevee.gtao_distance=3;s.eevee.gtao_factor=1.12
s.eevee.use_soft_shadows=True;s.eevee.taa_render_samples=64
s.render.resolution_x=768;s.render.resolution_y=432;s.render.resolution_percentage=100
s.render.fps=24;s.frame_start=1;s.frame_end=72
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.56,.67,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.45
s.render.image_settings.file_format='PNG';s.render.film_transparent=False

def mat(n,c,rough=.65):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;return m
skin=mat('warm porcelain skin',(.93,.64,.46)); blush=mat('soft cheeks',(.93,.38,.32)); hair=mat('chestnut hair',(.085,.025,.012),.35);hairlit=mat('hair sculpt highlights',(.14,.047,.019),.42)
red=mat('raspberry cotton',(.68,.025,.055));trim=mat('warm red trim',(.9,.17,.19));teal=mat('muted teal skirt',(.12,.38,.40));cream=mat('ivory',(.95,.88,.71));ink=mat('lashes',(.033,.011,.009));iris=mat('brown irises',(.19,.07,.025),.22);black=mat('pupils',(.009,.004,.003),.12);white=mat('eye whites',(.98,.98,.94),.25);mouthmat=mat('mouth cavity',(.15,.013,.025));tongue=mat('tongue',(.91,.22,.30));pink=mat('ribbon pink',(.92,.27,.31));wood=mat('honey wood',(.58,.33,.15));wall=mat('warm cream wall',(.88,.79,.64));sage=mat('window sage',(.38,.55,.32));glass=mat('blue window',(.50,.68,.74));rug=mat('rose playmat',(.78,.39,.46));green=mat('bird green',(.28,.53,.045));lime=mat('bird yellowgreen',(.63,.76,.11));dogmat=mat('puppy ivory',(.96,.92,.82));blue=mat('toy blue',(.11,.49,.61))
def empty(n,p=(0,0,0),par=None):
 o=bpy.data.objects.new(n,None);s.collection.objects.link(o);o.location=p;o.parent=par;return o
def ell(n,p,scale,m,par=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=p);o=bpy.context.object;o.name=n;o.scale=scale;o.parent=par;o.data.materials.append(m)
 for face in o.data.polygons:face.use_smooth=True
 return o
def box(n,p,size,m,r=.06,par=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=n;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.parent=par;o.data.materials.append(m)
 if r:
  mod=o.modifiers.new('rounded edges','BEVEL');mod.width=r;mod.segments=3
  o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
 return o
def curve(n,points,r,m,par=None):
 d=bpy.data.curves.new(n,'CURVE');d.dimensions='3D';d.resolution_u=16;d.bevel_depth=r;d.bevel_resolution=3
 sp=d.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
 for b,p in zip(sp.bezier_points,points):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 o=bpy.data.objects.new(n,d);s.collection.objects.link(o);o.data.materials.append(m);o.parent=par;return o
# Set: floor boards, playmat, bookcase, window, toy kitchen.
box('floor',(0,0,-.10),(14,12,.20),wood)
for i in range(-10,11):
 box('floor seam',(i*.55,0,.004),(.009,10,.006),cream,0)
box('rear wall',(0,3.5,2.5),(14,.18,5),wall)
box('playmat',(0,-.6,.025),(5.4,3.0,.035),rug,.04)
for x in [-1.8,0,1.8]:
 box('mat seam',(x,-.6,.046),(.01,3,.006),pink,0)
box('window pane',(.8,3.35,2.65),(5.2,.08,3.1),glass)
for x in [-1.9,.8,3.5]:box('window frame',(x,3.22,2.65),(.12,.18,3.3),sage)
for z in [1.02,2.3,4.28]:box('window frame',(.8,3.22,z),(5.5,.18,.12),sage)
box('bookcase',(-3.25,2.8,1.85),(1.6,.65,3.7),wood)
for z in [.5,1.6,2.7]:
 box('shelf',(-3.25,2.40,z),(1.55,.8,.10),cream)
 for i in range(6):
  b=box('book',(-3.85+i*.23,2.34,z+.40),(.16,.36,.69),[sage,red,teal,cream,blue,pink][i],.015);b.rotation_euler.y=(i%3-1)*.05
# plant
box('planter',(2.9,2.75,.40),(.7,.7,.75),cream,.18)
curve('plant trunk',[(2.9,2.75,.7),(2.82,2.75,1.5),(2.94,2.75,2.5)],.055,wood)
for i in range(9):
 a=i*2.4;o=ell('leaf',(2.9+.35*math.cos(a),2.75+.22*math.sin(a),1.8+(i%3)*.23),(.45,.13,.08),green);o.rotation_euler=(.2,a*.1,a)
# child: 2.8 heads high; sculpted broad cheeks and narrowed jaw.
root=empty('child_root',(0,0,0));body=empty('body',(0,0,.83),root)
ell('tee',(0,0,.40),(.39,.24,.47),red,body)
for x in [-.21,.21]:
 ell('leg',(x,-.005,-.44),(.13,.14,.36),skin,body)
 ell('sock',(x,-.015,-.63),(.135,.145,.14),cream,body)
 ell('shoe',(x,-.08,-.74),(.17,.25,.11),trim,body)
# Pleated skirt, cream pinstripes.
verts=[];faces=[];N=64
for z,r in [(.13,.35),(-.31,.57)]:
 for i in range(N):
  a=2*math.pi*i/N;rr=r*(1+.032*math.cos(a*16));verts.append((rr*math.cos(a),rr*math.sin(a),z))
for i in range(N):faces.append((i,(i+1)%N,(i+1)%N+N,i+N))
me=bpy.data.meshes.new('pleated skirt');me.from_pydata(verts,[],faces);o=bpy.data.objects.new('pleated skirt',me);s.collection.objects.link(o);o.parent=body;o.data.materials.append(teal);o.modifiers.new('fabric thickness','SOLIDIFY').thickness=.018
for i in range(32):
 a=2*math.pi*i/32;curve('skirt pinstripe',[(.353*math.cos(a),.353*math.sin(a),.12),(.575*math.cos(a),.575*math.sin(a),-.30)],.006,cream,body)
for z,r in [(-.25,.54),(-.30,.577)]:curve('hem piping',[(r*math.cos(i*2*math.pi/64),r*math.sin(i*2*math.pi/64),z) for i in range(65)],.010,trim,body)
# Front pocket and seams.
box('shirt pocket',(0,-.244,.32),(.31,.025,.25),red,.035,body)
curve('pocket seam',[(-.14,-.263,.42),(-.14,-.27,.22),(0,-.275,.19),(.14,-.27,.22),(.14,-.263,.42)],.005,cream,body)
for x in [-.27,.27]:curve('backpack strap',[(x,-.15,.76),(x,-.26,.55),(x,-.25,.18)],.027,cream,body)
head=empty('head',(0,0,1.05),body)
face=ell('sculpted face',(0,0,0),(.59,.44,.57),skin,head)
# Modify the unit sphere's cheeks/jaw silhouette before scale.
for v in face.data.vertices:
 z=v.co.z
 if z<-.25:v.co.x*=1-.22*((-z-.25)/.75)
for x in [-.58,.58]:
 ell('ear',(x,.015,-.05),(.10,.09,.15),skin,head)
 ell('ear inset',(x,-.062,-.05),(.048,.018,.07),blush,head)
 ell('cheek',(x*.59,-.38,-.16),(.13,.025,.065),blush,head)
ell('button nose',(0,-.45,-.10),(.080,.064,.064),skin,head)
eyes=[];lids=[]
for x in [-.215,.215]:
 e=empty('eye assembly',(x,-.397,.035),head);eyes.append(e)
 ell('eyeball',(0,0,0),(.145,.065,.17),white,e)
 ell('iris',(0,-.060,-.005),(.107,.020,.126),iris,e)
 ell('pupil',(0,-.078,-.005),(.063,.014,.088),black,e)
 ell('eye catchlight',(-.033,-.093,.046),(.028,.008,.034),white,e)
 ell('eye catchlight small',(.025,-.093,-.042),(.013,.007,.016),white,e)
 curve('upper lid',[(-.14,-.035,.05),(-.09,-.067,.15),(.02,-.067,.17),(.13,-.035,.075)],.012,ink,e)
 for j in range(2):curve('lash',[(.11,-.041,.10),(.15+j*.015,-.040,.13+j*.025)],.008,ink,e)
 curve('eyebrow',[(x-.10,-.375,.28),(x,-.414,.305),(x+.09,-.38,.28)],.015,hair,head)
# Raised lip rim, separate open mouth and tongue.
ell('lip',(0,-.417,-.29),(.12,.027,.055),blush,head)
mouth=ell('mouth',(0,-.443,-.285),(.098,.018,.043),mouthmat,head)
ell('tongue',(0,-.462,-.309),(.058,.008,.017),tongue,head)
# Volumetric curls, forelock, top knot and bow.
ell('back hair',(0,.12,.10),(.69,.42,.62),hair,head)
for i in range(13):
 a=math.pi*(.06+.88*i/12);x=.62*math.cos(a);z=.21+.38*math.sin(a);y=-.05-.10*math.sin(a)
 c=ell('sculpted curl',(x,y,z),(.20,.26,.22),hair if i%2 else hairlit,head);c.rotation_euler.y=.4*math.cos(a)
for side in [-1,1]:
 for j in range(3):ell('side curl',(side*(.55+.03*(j%2)),.025,.02-j*.10),(.17,.23,.19),hair,head)
for i in range(5):
 x=-.40+i*.19;c=ell('swept fringe',(x,-.245,.365+.06*math.sin(i)),(.18,.17,.20),hairlit if i%2==0 else hair,head);c.rotation_euler.y=-.40
ell('top knot',(.20,.10,.69),(.25,.23,.24),hair,head)
for side in [-1,1]:
 o=ell('ribbon loop',(.20+side*.16,-.12,.68),(.17,.045,.085),pink,head);o.rotation_euler.y=side*.25
ell('ribbon knot',(.20,-.17,.67),(.06,.045,.06),trim,head)
# Articulated arms and individually separated fingers.
arms=[]
for side in [-1,1]:
 a=empty('shoulder',(side*.37,0,.64),body);arms.append(a)
 ell('sleeve',(side*.07,0,-.08),(.16,.19,.19),red,a)
 ell('upper arm',(side*.10,-.005,-.25),(.11,.12,.21),skin,a)
 elbow=empty('elbow',(side*.12,0,-.39),a)
 ell('forearm',(side*.015,-.005,-.12),(.10,.105,.18),skin,elbow)
 hand=empty('hand',(side*.025,-.015,-.27),elbow)
 ell('palm',(0,0,0),(.115,.06,.11),skin,hand)
 for j in range(4):
  x=(j-1.5)*.048
  curve('finger',[(x,0,-.03),(x*1.25,-.005,-.14),(x*1.40,-.015,-.20+abs(j-1.5)*.025)],.027,skin,hand)
 curve('thumb',[(side*.07,-.01,.02),(side*.15,-.025,-.02),(side*.18,-.03,-.07)],.033,skin,hand)
# Puppy and bird provide a listener reaction.
pet=empty('puppy',(1.52,-.12,0))
ell('puppy body',(0,0,.34),(.28,.23,.30),dogmat,pet)
for x in [-.15,.15]:ell('paw',(x,-.10,.09),(.11,.17,.085),dogmat,pet)
ph=empty('puppy head',(0,-.015,.64),pet)
ell('puppy face',(0,0,0),(.30,.24,.26),dogmat,ph)
for x in [-.23,.23]:ell('floppy ear',(x,.015,-.04),(.11,.13,.22),dogmat,ph)
for x in [-.10,.10]:ell('puppy eye',(x,-.223,.035),(.035,.018,.043),black,ph)
ell('puppy muzzle',(0,-.22,-.08),(.15,.075,.085),cream,ph);ell('puppy nose',(0,-.294,-.055),(.052,.025,.035),black,ph)
tail=empty('tail',(0,.20,.40),pet);ell('curled tail',(0,.06,.07),(.07,.08,.20),dogmat,tail)
bird=empty('bird',(1.55,.02,1.12))
ell('bird body',(0,0,0),(.13,.11,.20),green,bird);ell('bird head',(0,-.025,.19),(.13,.115,.13),lime,bird)
ell('beak',(0,-.139,.17),(.035,.06,.04),trim,bird)
for x in [-.075,.075]:ell('bird eye',(x,-.103,.21),(.015,.01,.022),black,bird)
for side in [-1,1]:
 ell('bird wing',(side*.115,0,-.01),(.035,.10,.12),green,bird)
 curve('bird leg',[(side*.05,0,-.15),(side*.05,-.005,-.23)],.012,trim,bird)
 curve('bird toes',[(side*.05-.025,-.04,-.23),(side*.05,0,-.23),(side*.05+.025,-.04,-.23)],.009,trim,bird)
# Toy kitchen and utensils on the left.
box('toy kitchen',(-1.70,.05,.50),(1.04,.56,.90),cream,.08)
box('toy counter',(-1.70,-.02,.98),(1.15,.69,.10),yellow if 'yellow' in globals() else cream,.06)
box('toy backsplash',(-1.70,.26,1.29),(1.05,.08,.60),red,.06)
for x in [-1.93,-1.48]:
 ell('toy burner',(x,-.06,1.045),(.18,.18,.018),ink)
 ell('pan',(x,-.06,1.075),(.15,.15,.035),blue)
curve('spatula', [(-1.90,-.02,1.20),(-1.86,.05,1.53)],.022,wood)
box('spatula head',(-1.85,.06,1.58),(.15,.04,.16),cream,.02)
# Large lights keep facial planes soft, with warm key and cool window fill.
for n,p,power,size,color in [('key',(-3,-4,6),650,5,(1,.86,.72)),('fill',(4,-1,4),400,4,(.76,.86,1)),('window',(0,3,5),500,3,(1,.92,.80))]:
 bpy.ops.object.light_add(type='AREA',location=p);o=bpy.context.object;o.name=n;o.data.energy=power;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(3.3,-7.8,3.4));cam=bpy.context.object;s.camera=cam;cam.data.lens=43
focus=empty('camera focus',(0,0,1.35));c=cam.constraints.new('TRACK_TO');c.target=focus;c.track_axis='TRACK_NEGATIVE_Z';c.up_axis='UP_Y'
# Anticipation, greeting, listener response and settling. No audio/lip-sync claim.
for f in range(1,73):
 t=(f-1)/24;u=t/3
 root.location.z=.015*math.sin(t*3.0);root.rotation_euler.z=.025*math.sin(t*2.1)
 root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
 head.rotation_euler=(.04*math.sin(t*2),.04*math.sin(t*2.2),-.09*math.sin(t*1.8));head.keyframe_insert('rotation_euler',frame=f)
 # Right hand lifts gradually, waves, then settles.
 lift=min(1,max(0,(t-.25)/.6));lift=lift*lift*(3-2*lift)
 arms[1].rotation_euler.y=(-1.65+.22*math.sin(t*8))*lift
 arms[0].rotation_euler.y=.22+.10*math.sin(t*2)
 for a in arms:a.keyframe_insert('rotation_euler',frame=f)
 for e in eyes:
  e.scale.z=.10 if f in [27,28,60,61] else 1;e.keyframe_insert('scale',frame=f)
 mouth.scale.z=.043+.018*math.sin(t*5);mouth.keyframe_insert('scale',frame=f)
 ph.rotation_euler.z=.16*math.sin(t*2.1);ph.keyframe_insert('rotation_euler',frame=f)
 tail.rotation_euler.y=.35*math.sin(t*9);tail.keyframe_insert('rotation_euler',frame=f)
 bird.rotation_euler.z=.12*math.sin(t*3);bird.keyframe_insert('rotation_euler',frame=f)
 cam.location=(3.3-.5*u,-7.8+.5*u,3.4-.2*u);cam.keyframe_insert('location',frame=f)
s.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'study.blend'))
# Check a frame before spending time on the animation.
s.render.filepath=str(out/'hero.png');bpy.ops.render.render(write_still=True)
im=bpy.data.images.load(str((out/'hero.png').resolve()));px=list(im.pixels);rgb=[v for i,v in enumerate(px) if i%4<3]
check={'mean':sum(rgb)/len(rgb),'range':max(rgb)-min(rgb)};(out/'visual-check.json').write_text(json.dumps(check))
assert check['mean']>.03 and check['range']>.15,'Blank hero frame'
still_elapsed=round(time.monotonic()-T,2)
if os.environ.get('STUDY_STILL_ONLY')!='1':
 s.eevee.taa_render_samples=8
 s.render.filepath=str(out/'frame_');bpy.ops.render.render(animation=True)
report={'experiment':'003-reference-study','renderer':s.render.engine,'device':'CPU software OpenGL; see glxinfo.txt','width':768,'height':432,'frames':72 if os.environ.get('STUDY_STILL_ONLY')!='1' else 1,'fps':24,'duration':3 if os.environ.get('STUDY_STILL_ONLY')!='1' else 0,'mode':'animation' if os.environ.get('STUDY_STILL_ONLY')!='1' else 'still','still_elapsed_seconds':still_elapsed,'render_elapsed_seconds':round(time.monotonic()-T,2),'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'hero_samples':64,'animation_samples':8,'reference':'KBS public episode thumbnail; viewing only, not embedded','changes':['sculpted cheek/jaw silhouette','layered eyes and lashes','volumetric curls and bow','pleated striped skirt and pocket seams','articulated arm and separated fingers','furnished room and puppy/bird listener','anticipation and settling'],'limitations':['procedural visual approximation, not identical production character','no speech or phoneme lip sync','single 3-second shot, not an episode','no claim of broadcast-equivalent quality']}
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
