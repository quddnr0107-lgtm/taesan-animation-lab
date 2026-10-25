"""Controlled CPU likeness variants. No source-frame projection or image overlay."""
import os, runpy, math, json, time, resource
from pathlib import Path
import bpy
from mathutils import Vector
T=time.monotonic();os.environ['STUDY_BUILD_ONLY']='1'
g=runpy.run_path('studies/preschool.py');s=g['s'];s.frame_set(1)
out=Path('output');out.mkdir(exist_ok=True)
name=os.environ.get('FIT_VARIANT','B')
configs={'A':{'face':(.64,.46,.57),'eyes':.90,'eye_x':.225,'jaw':.13,'hair_width':.73},'B':{'face':(.67,.47,.59),'eyes':.84,'eye_x':.235,'jaw':.10,'hair_width':.77},'C':{'face':(.65,.45,.60),'eyes':.93,'eye_x':.230,'jaw':.16,'hair_width':.75}}
cfg=configs[name];head=g['head'];face=g['face'];ell=g['ell'];curve=g['curve'];mat=g['mat']
def remove(prefixes):
 for o in list(bpy.data.objects):
  if any(o.name.startswith(p) for p in prefixes):bpy.data.objects.remove(o,do_unlink=True)
def material_color(m,c,rough=.7,spec=.25):
 m.diffuse_color=(*c,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Specular'].default_value=spec
# Wider cheek silhouette, gentler chin. Rebuild from the undeformed unit sphere.
face.scale=cfg['face']
for v in face.data.vertices:
 z=v.co.z
 if z<-.25:
  old=1-.22*((-z-.25)/.75)
  v.co.x/=old
  v.co.x*=1-cfg['jaw']*((-z-.25)/.75)
 v.co.x*=1+.035*math.exp(-((z+.23)/.30)**2)
remove(['cheek','lip','tongue','eyebrow'])
# Blush is now a smooth color field on the face mesh, not floating pink discs.
col=face.data.vertex_colors.new(name='SkinColor')
base=(.94,.70,.53);tint=(.94,.48,.42)
for p in face.data.polygons:
 for li in p.loop_indices:
  v=face.data.vertices[face.data.loops[li].vertex_index].co
  w=.42*math.exp(-((abs(v.x)-.58)/.24)**2-((v.z+.22)/.22)**2)*max(0,-v.y)**5
  col.data[li].color=tuple(base[i]*(1-w)+tint[i]*w for i in range(3))+(1,)
fm=g['skin'].copy();fm.name='smooth skin and cheek field';face.data.materials.clear();face.data.materials.append(fm)
vc=fm.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name=col.name;fm.node_tree.links.new(vc.outputs['Color'],fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
fm.node_tree.nodes['Principled BSDF'].inputs['Specular'].default_value=.22
# Flatten eye depth and reduce white exposure. Keep the same coordinate frame for all variants.
for i,e in enumerate(g['eyes']):
 e.animation_data_clear();e.scale=(cfg['eyes'],.53,cfg['eyes']*.94);e.location=(cfg['eye_x']*(-1 if i==0 else 1),-.414,-.005)
 for o in e.children:
  if o.name.startswith('iris'):o.scale.x*=1.08;o.scale.z*=1.04
  if o.name.startswith('eyeball'):o.scale.z*=.92
for x in [-cfg['eye_x'],cfg['eye_x']]:curve('fine eyebrow',[(x-.085,-.397,.254),(x,-.433,.279),(x+.085,-.395,.254)],.008,g['hair'],head)
nose=bpy.data.objects.get('button nose');nose.scale=(.059,.042,.049);nose.location=(0,-.481,-.128)
mouth=g['mouth'];mouth.animation_data_clear();mouth.location=(0,-.446,-.291);mouth.scale=(.080,.012,.029)
curve('subtle upper lip',[(-.084,-.446,-.280),(0,-.458,-.272),(.084,-.446,-.280)],.006,g['blush'],head)
# Replace repeated bead curls with continuous, tapered lofted hair locks.
remove(['back hair','sculpted curl','side curl','swept fringe','top knot'])
hair=g['hair'];material_color(hair,(.038,.010,.005),.57,.22)
hairline=mat('fine hair flow',(.054,.016,.008),.65)
ell('hair silhouette',(0,.15,.13),(cfg['hair_width'],.46,.63),hair,head)
def bez(p,t):return (1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]
def lock(n,points,width,depth):
 ps=[Vector(p) for p in points];vs=[];fs=[];N=25;R=12;centers=[]
 for j in range(N):
  t=j/(N-1);p=bez(ps,t);centers.append(p)
  d=bez(ps,min(1,t+.002))-bez(ps,max(0,t-.002));d.y=0;d.normalize();side=Vector((-d.z,0,d.x))
  taper=.15+.85*math.sin(math.pi*t)**.45
  for k in range(R):
   a=2*math.pi*k/R;v=p+side*(math.cos(a)*width*taper)+Vector((0,math.sin(a)*depth*taper,0));vs.append(tuple(v))
 for j in range(N-1):
  for k in range(R):
   a=j*R+k;b=j*R+(k+1)%R;fs.append((a,b,b+R,a+R))
 mesh=bpy.data.meshes.new(n);mesh.from_pydata(vs,[],fs);mesh.update();o=bpy.data.objects.new(n,mesh);s.collection.objects.link(o);o.parent=head;o.data.materials.append(hair)
 for f in mesh.polygons:f.use_smooth=True
 for offset in [-.055,0,.055]:
  curve('hair flow groove',[(p.x+offset,p.y-depth*.96,p.z) for p in centers[2:-2:2]],.0017,hairline,head)
for j in range(4):
 z=j*.045
 lock('swept bang', [(-.57,.015,.36+z),(-.40,-.30,.68+z),(.18,-.34,.66-z),(.48,-.33,.24-z)],.15,.075)
for side in [-1,1]:
 for j in range(3):
  dx=j*.035
  lock('side wave',[(side*.24,.02,.59),(side*(.74+dx),-.13,.60),(side*(.83+dx),-.15,.00),(side*.53,-.10,-.23+j*.045)],.14,.12)
ell('soft top knot',(.19,.10,.73),(.25,.23,.22),hair,head)
# Tone down plastic reflections and add a subtle cloth normal field.
for m in [g['red'],g['teal']]:
 p=m.node_tree.nodes['Principled BSDF'];p.inputs['Roughness'].default_value=.86;p.inputs['Specular'].default_value=.16
 no=m.node_tree.nodes.new('ShaderNodeTexNoise');no.inputs['Scale'].default_value=170
 bu=m.node_tree.nodes.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.10;bu.inputs['Distance'].default_value=.008
 m.node_tree.links.new(no.outputs['Fac'],bu.inputs['Height']);m.node_tree.links.new(bu.outputs['Normal'],p.inputs['Normal'])
for m in [g['skin'],g['blush']]:m.node_tree.nodes['Principled BSDF'].inputs['Specular'].default_value=.2
s.world.node_tree.nodes['Background'].inputs[1].default_value=.28
for o in bpy.data.objects:
 if o.type=='LIGHT':o.data.energy*=.75
 if o.name.startswith('floor seam'):
  o.hide_render=True
material_color(g['glass'],(.30,.40,.43),.85,.1)
s.view_settings.exposure=-.2
# Remove camera motion and compare every variant with the same frontal portrait camera.
cam=g['cam'];cam.animation_data_clear();cam.location=(.26,-4.50,2.23);cam.data.lens=58
g['focus'].location=(0,0,1.90)
s.render.resolution_x=640;s.render.resolution_y=640;s.eevee.taa_render_samples=24
if os.environ.get('FIT_BUILD_ONLY')!='1':
 bpy.context.view_layer.update();s.render.filepath=str(out/f'variant-{name}.png')
 bpy.ops.wm.save_as_mainfile(filepath=str(out/f'variant-{name}.blend'))
 bpy.ops.render.render(write_still=True)
 img=bpy.data.images.load(str((out/f'variant-{name}.png').resolve()));px=list(img.pixels);vals=[v for i,v in enumerate(px) if i%4<3]
 check={'mean':sum(vals)/len(vals),'range':max(vals)-min(vals)};assert check['mean']>.02 and check['range']>.1
 report={'experiment':'004-likeness-variants','variant':name,'parameters':cfg,'width':640,'height':640,'frames_rendered':1,'elapsed_seconds':round(time.monotonic()-T,2),'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'pixel_check':check,'improvements_under_test':['cheek width and chin','flatter eye depth and iris proportion','blended blush','continuous swept hair locks','matte cloth and reduced reflections'],'limitations':['manual procedural likeness study','no numeric identity score claimed','not identical to original','portrait still only; no voice or lip sync']}
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 