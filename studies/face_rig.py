"""New deformable facial shell with real eye/mouth apertures and coupled blend shapes.
This is a geometry/rig experiment, not a claim of original-character identity.
"""
import bpy, os, math, json, runpy, time, resource
from pathlib import Path
T=time.monotonic();os.environ['FIT_VARIANT']='B';os.environ['FIT_BUILD_ONLY']='1'
g=runpy.run_path('studies/likeness.py');base=g['g'];s=g['s'];head=g['head'];out=Path('output');out.mkdir(exist_ok=True)
# Discard the previous solid head and floating mouth overlay.
old=g['face'];skin=g['fm'];bpy.data.objects.remove(old,do_unlink=True)
for o in list(bpy.data.objects):
 if any(o.name.startswith(p) for p in ['mouth','subtle upper lip','upper lid','lash']):bpy.data.objects.remove(o,do_unlink=True)
# Back of skull: front hemisphere removed so eye/mouth holes are genuine openings.
import bmesh
back=base['ell']('back skull',(0,0,0),(.66,.47,.59),base['skin'],head)
bm=bmesh.new();bm.from_mesh(back.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.y<0],context='VERTS');bm.to_mesh(back.data);bm.free()
w,d,h=.66,.47,.59;N=176;M=160;vs=[];lookup={};faces=[]
eyes=[(-.235,-.005),(.235,-.005)];rx,rz=.121,.125
for j in range(M+1):
 z=-h+2*h*j/M
 for i in range(N+1):
  x=-w+2*w*i/N;q=(x/w)**2+(z/h)**2
  if q>=.995:continue
  y=-d*math.sqrt(1-q)
  # Cheek volume and a shallow nasal bridge are part of the same mesh.
  y-=.012*math.exp(-((abs(x)-.34)/.17)**2-((z+.16)/.16)**2)
  y-=.020*math.exp(-(x/.095)**2-((z+.10)/.19)**2)
  lookup[i,j]=len(vs);vs.append((x,y,z))
for j in range(M):
 for i in range(N):
  ids=[lookup.get(k) for k in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]]
  if None in ids:continue
  x=sum(vs[k][0] for k in ids)/4;z=sum(vs[k][2] for k in ids)/4
  eyehole=any(((x-ex)/rx)**2+((z-ez)/rz)**2<1 for ex,ez in eyes)
  mouthhole=(x/.082)**2+((z+.29)/.014)**2<1
  if not eyehole and not mouthhole:faces.append(tuple(ids))
me=bpy.data.meshes.new('facial aperture topology');me.from_pydata(vs,[],faces);me.update()
face=bpy.data.objects.new('deformable facial shell',me);s.collection.objects.link(face);face.parent=head;face.data.materials.append(skin)
for p in me.polygons:p.use_smooth=True
sub=face.modifiers.new('subdivision facial surface','SUBSURF');sub.levels=1;sub.render_levels=1
col=me.vertex_colors.new(name='SkinColor')
for p in me.polygons:
 for li in p.loop_indices:
  v=me.vertices[me.loops[li].vertex_index].co
  a=.28*math.exp(-((abs(v.x)-.34)/.13)**2-((v.z+.16)/.10)**2)
  a*=max(0,-v.y)/d
  c=(.94,.70,.53);r=(.94,.46,.42);col.data[li].color=tuple(c[k]*(1-a)+r[k]*a for k in range(3))+(1,)
# Surface displacements: lids, lips, jaw and cheek vertices share the facial shell.
def displacement(p,kind):
 x,y,z=p;dz=0;dx=0;dy=0
 if kind.startswith('Blink'):
  ex=-.235 if kind.endswith('L') else .235;ez=-.005
  r=math.sqrt(((x-ex)/rx)**2+((z-ez)/rz)**2)
  q=math.exp(-((r-1)/.58)**2)*math.exp(-((x-ex)/.23)**6)
  dz=-(z-ez)*.985*q;dy=-.008*q
 elif kind=='JawOpen':
  q=max(0,1-(x/.16)**2)*math.exp(-abs(z+.29)/.095)
  dz=(.042 if z>=-.29 else -.048)*q
  dz-=.010*math.exp(-(x/.4)**2-((z+.39)/.17)**2)
 elif kind=='Smile':
  q=math.exp(-((abs(x)-.085)/.073)**2-((z+.29)/.09)**2)
  dz=.035*q;dx=(1 if x>0 else -1)*.014*q
  dz+=.012*math.exp(-((abs(x)-.30)/.16)**2-((z+.13)/.15)**2)
 elif kind=='BrowRaise':dz=.028*math.exp(-((abs(x)-.235)/.20)**2-((z-.25)/.13)**2)
 return (x+dx,y+dy,z+dz)
face.shape_key_add(name='Basis');keys={}
for kind in ['BlinkL','BlinkR','JawOpen','Smile','BrowRaise']:
 k=face.shape_key_add(name=kind);keys[kind]=k
 for i,v in enumerate(vs):k.data[i].co=displacement(v,kind)
# Pupil geometry remains unchanged during the blink. Skin closes over the eyeballs.
for e in base['eyes']:e.animation_data_clear()
base['ell']('inner mouth cavity',(0,-.31,-.29),(.14,.045,.13),base['mouthmat'],head)
# Thin eyelashes deform with the same blink displacement as the surrounding skin.
for side,(ex,ez) in zip(['L','R'],eyes):
 vv=[];ff=[]
 for i in range(41):
  a=math.pi*i/40;x=ex+rx*math.cos(a);z=ez+rz*math.sin(a)
  y=-d*math.sqrt(max(.01,1-(x/w)**2-(z/h)**2))-.007
  vv.extend([(x,y,z),(x,y-.003,z+.008)])
 for i in range(40):ff.append((i*2,i*2+2,i*2+3,i*2+1))
 mm=bpy.data.meshes.new('lid lash surface');mm.from_pydata(vv,[],ff);o=bpy.data.objects.new('deforming upper lashes '+side,mm);s.collection.objects.link(o);o.parent=head;o.data.materials.append(base['ink']);o.shape_key_add(name='Basis');k=o.shape_key_add(name='Blink'+side)
 for i,v in enumerate(vv):k.data[i].co=displacement(v,'Blink'+side)
 drv=k.driver_add('value').driver;var=drv.variables.new();var.name='blink';var.type='SINGLE_PROP';var.targets[0].id_type='KEY';var.targets[0].id=face.data.shape_keys;var.targets[0].data_path='key_blocks["Blink'+side+'"].value';drv.expression='blink'
# Correct outward normals on the new lofted hair strips.
for o in bpy.data.objects:
 if o.type=='MESH' and (o.name.startswith('swept bang') or o.name.startswith('side wave')):
  b=bmesh.new();b.from_mesh(o.data);bmesh.ops.recalc_face_normals(b,faces=list(b.faces));b.to_mesh(o.data);b.free()
cam=base['cam'];cam.animation_data_clear();cam.data.lens=57;base['focus'].location=(0,0,1.87)
s.render.resolution_x=576;s.render.resolution_y=576;s.eevee.taa_render_samples=16
s.frame_set(1)
def pose(blink=0,jaw=0,smile=0,brow=0):
 for n,v in [('BlinkL',blink),('BlinkR',blink),('JawOpen',jaw),('Smile',smile),('BrowRaise',brow)]:keys[n].value=v
 bpy.context.view_layer.update()
views=[('neutral',(0,-4.35,2.20),(0,0,0,0)),('blink',(0,-4.35,2.20),(1,0,0,0)),('smile',(0,-4.35,2.20),(0,.55,1,.5)),('three-quarter',(2.35,-3.65,2.20),(0,.25,.3,0))]
for name,loc,p in views:
 cam.location=loc;pose(*p);s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
# Quantify actual mesh movement rather than merely logging control values.
basis=face.data.shape_keys.key_blocks['Basis'];motion={}
for name,k in keys.items():
 ds=[(k.data[i].co-basis.data[i].co).length for i in range(len(vs))]
 motion[name]={'moved_vertices':sum(v>1e-5 for v in ds),'max_displacement':max(ds)}
assert all(x['moved_vertices']>50 for x in motion.values())
pose();cam.location=(0,-4.35,2.20)
# Short deformation test: open, smile, blink, return. No speech synchronization claim.
s.render.fps=24;s.frame_start=1;s.frame_end=36
for f in range(1,37):
 t=(f-1)/35;jaw=.8*math.sin(math.pi*t)**2;smile=.8*math.sin(math.pi*t)**2
 blink=max(0,1-abs(t-.70)/.08)
 for n,v in [('BlinkL',blink),('BlinkR',blink),('JawOpen',jaw),('Smile',smile),('BrowRaise',smile*.5)]:keys[n].value=v;keys[n].keyframe_insert('value',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'deformable-face.blend'))
s.eevee.taa_render_samples=6;s.render.filepath=str(out/'frame_');bpy.ops.render.render(animation=True)
report={'experiment':'006-deformable-face','vertices':len(vs),'faces':len(faces),'shape_keys':motion,'renderer':s.render.engine,'stills':[x[0] for x in views],'animation_frames':36,'fps':24,'width':576,'height':576,'elapsed_seconds':round(time.monotonic()-T,2),'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'checks':['true eye and mouth surface apertures','eye geometry not scaled for blink','skin and lash deformation share blink control','jaw and smile change facial shell vertices'],'limitations':['new experimental topology; boundary artifacts possible','not a production retopology or original rig','not identical to the reference','silent deformation test, no speech claim']}
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
