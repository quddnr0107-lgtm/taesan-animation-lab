"""008: connected facial topology, recessed eyes, and integrated eyelid rings."""
import bpy,os,math,json,runpy,time,resource
from pathlib import Path
from collections import Counter,defaultdict
T=time.monotonic();os.environ['FIT_VARIANT']='B';os.environ['FIT_BUILD_ONLY']='1'
g=runpy.run_path('studies/likeness.py');base=g['g'];s=g['s'];head=g['head'];out=Path('output');out.mkdir(exist_ok=True)
for o in list(bpy.data.objects):
 if o==g['face'] or any(o.name.startswith(p) for p in ['mouth','subtle upper lip','upper lid','lash']):bpy.data.objects.remove(o,do_unlink=True)
w,d,h=.66,.47,.59;U,V=192,128;vs=[];fs=[];eyes=[(-.235,-.005),(.235,-.005)];outer=(.148,.153);inner=(.121,.125)
def taper(z):return 1-.16*max(0,min(1,(-z-.15)/.44))**.75
def surface_y(x,z):
 xx=x/taper(z);return -d*math.sqrt(max(.001,1-(xx/w)**2-(z/h)**2))
for j in range(1,V):
 phi=math.pi*j/V;z=h*math.cos(phi)
 for i in range(U):
  a=2*math.pi*i/U;vs.append((w*math.sin(phi)*math.cos(a)*taper(z),d*math.sin(phi)*math.sin(a),z))
top=len(vs);vs.append((0,0,h));bottom=len(vs);vs.append((0,0,-h))
for i in range(U):fs.append((top,i,(i+1)%U))
for j in range(V-2):
 for i in range(U):
  a=j*U+i;b=j*U+(i+1)%U;fs.append((a,a+U,b+U,b))
for i in range(U):fs.append(((V-2)*U+i,bottom,(V-2)*U+(i+1)%U))
def in_hole(x,y,z):
 if y>=0:return False
 return any(((x-ex)/outer[0])**2+((z-ez)/outer[1])**2<1 for ex,ez in eyes) or (x/.090)**2+((z+.29)/.020)**2<1
fs=[f for f in fs if not in_hole(*[sum(vs[k][a] for k in f)/len(f) for a in range(3)])]
edges=Counter(tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in fs for i in range(len(f)))
boundary=set(k for e,n in edges.items() if n==1 for k in e)
# A single connected head surface, including annular eyelids. No overlapping skin patches.
roles={};rings={};eye_meshes=[]
for e in base['eyes']:
 e.animation_data_clear();e.location.y=-.404;e.scale.y=.30
 for o in e.children:
  if o.name.startswith('iris'):o.scale.x=.136;o.scale.z=.150
  elif o.name.startswith('pupil'):o.scale.x=.080;o.scale.z=.103
  if o.type=='MESH':eye_meshes.append((e,o))
def eye_front(x,z):
 front=0
 for e,o in eye_meshes:
  cx=e.location.x+o.location.x*e.scale.x;cz=e.location.z+o.location.z*e.scale.z
  xx=(x-cx)/(o.scale.x*e.scale.x);zz=(z-cz)/(o.scale.z*e.scale.z);q=xx*xx+zz*zz
  if q<1:front=min(front,e.location.y+o.location.y*e.scale.y-o.scale.y*e.scale.y*math.sqrt(1-q))
 return front
for side,(ex,ez) in zip(['L','R'],eyes):
 ids=[k for k in boundary if vs[k][1]<0 and abs(vs[k][0]-ex)<.19 and abs(vs[k][2]-ez)<.19]
 ids.sort(key=lambda k:math.atan2((vs[k][2]-ez)/outer[1],(vs[k][0]-ex)/outer[0]))
 assert len(ids)>30
 angles=[math.atan2((vs[k][2]-ez)/outer[1],(vs[k][0]-ex)/outer[0]) for k in ids]
 for k,a in zip(ids,angles):
  x=ex+outer[0]*math.cos(a);z=ez+outer[1]*math.sin(a);vs[k]=(x,surface_y(x,z),z)
 prev=ids
 for j in range(1,9):
  t=j/8;current=[]
  for a in angles:
   x=ex+((1-t)*outer[0]+t*inner[0])*math.cos(a);z=ez+((1-t)*outer[1]+t*inner[1])*math.sin(a)
   y=surface_y(x,z)-.002*math.sin(t*math.pi/2)
   closed_z=ez+(1-t)*outer[1]*math.sin(a)
   # Minimal eye clearance: avoid forcing the entire closed lid into a round cap.
   target_y=min(surface_y(x,closed_z)-.002,eye_front(x,closed_z)-.004)
   closed_y=(1-t)*surface_y(x,closed_z)+t*target_y
   k=len(vs);vs.append((x,y,z));roles[k]=(side,(x,closed_y,closed_z));current.append(k)
  for i in range(len(ids)):fs.append((prev[i],prev[(i+1)%len(ids)],current[(i+1)%len(ids)],current[i]))
  prev=current
 rings[side]=prev
# Smooth the mouth aperture boundary and add a short skin rim inside the same mesh.
ids=[k for k in boundary if vs[k][1]<0 and abs(vs[k][0])<.13 and abs(vs[k][2]+.29)<.05]
ids.sort(key=lambda k:math.atan2((vs[k][2]+.29)/.020,vs[k][0]/.090));assert len(ids)>10
for k in ids:
 a=math.atan2((vs[k][2]+.29)/.020,vs[k][0]/.090);x=.090*math.cos(a);z=-.29+.020*math.sin(a);vs[k]=(x,surface_y(x,z),z)
me=bpy.data.meshes.new('continuous facial topology');me.from_pydata(vs,[],fs);me.update()
import bmesh
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
face=bpy.data.objects.new('continuous facial shell',me);s.collection.objects.link(face);face.parent=head;face.data.materials.append(g['fm'])
for p in me.polygons:p.use_smooth=True
sub=face.modifiers.new('smooth connected skin','SUBSURF');sub.levels=1;sub.render_levels=1
col=me.vertex_colors.new(name='SkinColor')
for p in me.polygons:
 for li in p.loop_indices:
  v=me.vertices[me.loops[li].vertex_index].co;a=.20*math.exp(-((abs(v.x)-.34)/.13)**2-((v.z+.16)/.10)**2)*max(0,-v.y)/d
  c=(.94,.70,.53);r=(.94,.46,.42);col.data[li].color=tuple(c[k]*(1-a)+r[k]*a for k in range(3))+(1,)
face.shape_key_add(name='Basis');keys={}
for kind in ['BlinkL','BlinkR','JawOpen','Smile','BrowRaise','LipRound']:
 key=face.shape_key_add(name=kind);keys[kind]=key
 for i,(x,y,z) in enumerate(vs):
  dx=dy=dz=0
  if kind.startswith('Blink'):
   if i in roles and roles[i][0]==kind[-1]:key.data[i].co=roles[i][1]
   continue
  if y>=0:continue
  if kind=='JawOpen':
   q=math.exp(-(x/.14)**4-((z+.29)/.13)**2);dz=.045*math.tanh((z+.29)/.012)*q-.010*math.exp(-(x/.4)**2-((z+.39)/.17)**2)
  elif kind=='Smile':
   q=math.exp(-((abs(x)-.085)/.073)**2-((z+.29)/.09)**2);dz=.027*q;dx=(1 if x>0 else -1)*.012*q
  elif kind=='BrowRaise':dz=.022*math.exp(-((abs(x)-.235)/.20)**2-((z-.25)/.13)**2)
  elif kind=='LipRound':
   q=math.exp(-(x/.14)**2-((z+.29)/.10)**2);dx=-.35*x*q;dy=-.012*q
  key.data[i].co=(x+dx,y+dy,z+dz)
base['ell']('inner mouth cavity',(0,-.31,-.29),(.14,.045,.13),base['mouthmat'],head)
base['iris'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.075,.025,.010,1)
# Eye rim lashes follow the connected skin margin through a direct key driver.
for side,ids in rings.items():
 upper=[k for k in ids if vs[k][2]>=eyes[0][1]];upper.sort(key=lambda k:vs[k][0]);vv=[];ff=[]
 for k in upper:
  x,y,z=vs[k];vv.extend([(x,y-.003,z),(x,y-.004,z+.005)])
 for i in range(len(upper)-1):ff.append((2*i,2*i+2,2*i+3,2*i+1))
 mm=bpy.data.meshes.new('connected margin lashes');mm.from_pydata(vv,[],ff);o=bpy.data.objects.new('skin driven lashes '+side,mm);s.collection.objects.link(o);o.parent=head;o.data.materials.append(base['ink']);o.shape_key_add(name='Basis');k=o.shape_key_add(name='Blink'+side)
 for j,idx in enumerate(upper):
  x,y,z=roles[idx][1];k.data[2*j].co=(x,y-.003,z);k.data[2*j+1].co=(x,y-.004,z+.005)
 drv=k.driver_add('value').driver;v=drv.variables.new();v.name='blink';v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=face.data.shape_keys;v.targets[0].data_path='key_blocks["Blink'+side+'"].value';drv.expression='blink'
# Check connectedness of used geometry; all eyelid vertices must share the head component.
adj=defaultdict(set)
for f in fs:
 for a,b in zip(f,f[1:]+f[:1]):adj[a].add(b);adj[b].add(a)
seen=set();stack=[next(iter(adj))]
while stack:
 k=stack.pop()
 if k in seen:continue
 seen.add(k);stack.extend(adj[k]-seen)
assert len(seen)==len(adj),'Disconnected facial surface'
assert all(k in seen for k in roles)
cam=base['cam'];cam.animation_data_clear();cam.data.lens=57;base['focus'].location=(0,0,1.87);s.render.resolution_x=576;s.render.resolution_y=576;s.eevee.taa_render_samples=16;s.frame_set(1)
views=[('neutral',(0,-4.35,2.20),(0,0,0)),('half-blink',(0,-4.35,2.20),(.5,0,0)),('blink',(0,-4.35,2.20),(1,0,0)),('smile',(0,-4.35,2.20),(0,.55,1)),('three-quarter',(2.35,-3.65,2.20),(0,.25,.3))]
for name,loc,(blink,jaw,smile) in views:
 for k in keys.values():k.value=0
 keys['BlinkL'].value=keys['BlinkR'].value=blink;keys['JawOpen'].value=jaw;keys['Smile'].value=smile;cam.location=loc;bpy.context.view_layer.update();s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
for k in keys.values():k.value=0
cam.location=(0,-4.35,2.20);bpy.ops.wm.save_as_mainfile(filepath=str(out/'continuous-face.blend'))
report={'experiment':'008-connected-face','vertices':len(vs),'faces':len(fs),'connected_components':1,'integrated_lid_vertices':len(roles),'shape_keys':list(keys),'stills':[v[0] for v in views],'elapsed_seconds':round(time.monotonic()-T,2),'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limitations':['experimental procedural anatomy','visual review required; connectivity does not imply likeness','not original-character or broadcast-quality equivalence']}
(out/'report.json').write_text(json.dumps(report,indent=2))
