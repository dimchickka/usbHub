"""Fill surrounded In2 pockets with the surrounding net and anchor surface GND islands."""
import os,json,hashlib,math,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/all-fill'
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:os.environ[k]=str(rt/n)
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(main);audit=json.loads((out/'zone-void-audit.json').read_text());assert source_sha==audit['source_sha256']
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project)
z3=next(z for z in b.Zones() if z.m_Uuid.AsString()=='0d6c0e1a-8aaa-4fe2-8b9e-0621bf230124');zg=next(z for z in b.Zones() if z.m_Uuid.AsString()=='404cc076-671f-4e00-b1f4-a3b505b84f0a')
patches=[]
for layer in audit['layers']:
 if layer['layer']!='In2.Cu':continue
 for gap in layer['wide_voids']:
  x1,y1,x2,y2=gap['bbox_mm'];target=zg if y1<150 else z3;pad=.9;points=[(x1-pad,y1-pad),(x2+pad,y1-pad),(x2+pad,y2+pad),(x1-pad,y2+pad)]
  poly=P.SHAPE_POLY_SET();poly.NewOutline()
  for x,y in points:poly.Append(P.FromMM(x),P.FromMM(y))
  target.Outline().BooleanAdd(poly);patches.append({'net':target.GetNetname(),'points_mm':points})
assert sum(p['net']=='+3v3' for p in patches)==23 and sum(p['net']=='GND' for p in patches)==1
# Find safe locations for standard GND stitching vias; planes are cleared during refill.
blocked=P.SHAPE_POLY_SET()
for t in b.GetTracks():
 clearance=250000 if t.GetNetname()=='GND' else 550000
 t.TransformShapeToPolygon(blocked,P.F_Cu if isinstance(t,P.PCB_VIA) else t.GetLayer(),clearance,10000,P.ERROR_OUTSIDE)
for f in b.GetFootprints():
 for p in f.Pads():
  layers=list(p.GetLayerSet().CuStack())
  if layers:p.TransformShapeToPolygon(blocked,layers[0],550000,10000,P.ERROR_OUTSIDE)
  if p.GetDrillSize().x or p.GetDrillSize().y:
   # A conservative circle also excludes non-plated and slotted mechanical holes.
   pos=p.GetPosition();radius=math.hypot(p.GetDrillSize().x/2,p.GetDrillSize().y/2)+550000;idx=blocked.NewOutline()
   for i in range(24):
    a=2*math.pi*i/24;r=radius/math.cos(math.pi/24);blocked.Append(round(pos.x+r*math.cos(a)),round(pos.y+r*math.sin(a)),idx)
blocked.Simplify();vias=[];skipped=[]
for layer in audit['layers']:
 if layer['layer'] not in ['F.Cu','B.Cu']:continue
 for gap in layer['wide_voids']:
  poly=P.SHAPE_POLY_SET();poly.NewOutline()
  for x,y in gap['points_mm']:poly.Append(P.FromMM(x),P.FromMM(y))
  x1,y1,x2,y2=gap['bbox_mm'];cx,cy=(x1+x2)/2,(y1+y2)/2;candidates=[]
  for ix in range(math.ceil(x1*4),math.floor(x2*4)+1):
   for iy in range(math.ceil(y1*4),math.floor(y2*4)+1):
    x,y=ix/4,iy/4;v=P.VECTOR2I(P.FromMM(x),P.FromMM(y))
    if poly.Contains(v) and not blocked.Contains(v):candidates.append(((x-cx)**2+(y-cy)**2,x,y))
  if not candidates:skipped.append({'layer':layer['layer'],'bbox_mm':gap['bbox_mm']});continue
  _,x,y=min(candidates);v=P.PCB_VIA(b);v.SetViaType(P.VIATYPE_THROUGH);v.SetLayerPair(P.F_Cu,P.B_Cu);v.SetPosition(P.VECTOR2I(P.FromMM(x),P.FromMM(y)));v.SetWidth(600000);v.SetDrill(300000);v.SetNetCode(b.FindNet('GND').GetNetCode());b.Add(v);vias.append({'uuid':v.m_Uuid.AsString(),'x_mm':x,'y_mm':y,'anchors_layer':layer['layer'],'size_mm':[.6,.3]})
print('PATCHES',len(patches),'GND STITCHES',vias,'SKIPPED',skipped,flush=True)
assert not skipped,'Inspect any surface pocket that cannot accept a safe GND stitch'
for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
b.BuildConnectivity();filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity();pending=rt/'remaining-filled.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b);assert sha(main)==source_sha;shutil.copyfile(pending,main)
report={'source_sha256':source_sha,'applied_sha256':sha(main),'In2_extensions':patches,'added_GND_stitches':vias,'skipped_surface_pockets':skipped};(out/'remaining-zone-voids-fill.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('Filled remaining wide zone voids',report['applied_sha256'],flush=True)
