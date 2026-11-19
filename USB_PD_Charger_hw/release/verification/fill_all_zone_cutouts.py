"""Remove every explicit cutout in existing copper zones; keep board routing and zone perimeters."""
import os,json,hashlib,shutil,collections
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/all-fill';rt.mkdir(parents=True,exist_ok=True)
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:p=rt/n;p.mkdir(exist_ok=True);os.environ[k]=str(p)
config=rt/'config/9.0';config.mkdir(exist_ok=True)
for n in ['fp','sym']:(config/(n+'-lib-table')).write_text('('+n+'_lib_table (version 7))\n')
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(main);(rt/'before.tmp').write_bytes(main.read_bytes())
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project)
def ts(t):
 s=[t.GetClass(),t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
 if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y])
 if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return s
def perimeter(z):
 o=z.Outline();return [[(o.COutline(i).CPoint(k).x,o.COutline(i).CPoint(k).y) for k in range(o.COutline(i).PointCount())] for i in range(o.OutlineCount())]
tracks={t.m_Uuid.AsString():ts(t) for t in b.GetTracks()};placements={f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in b.GetFootprints()};original_outlines={z.m_Uuid.AsString():z.Outline().Format() for z in b.Zones()};perimeters={z.m_Uuid.AsString():perimeter(z) for z in b.Zones()};filled_before={z.m_Uuid.AsString():{b.GetLayerName(layer):z.GetFilledPolysList(layer).Area()/1e12 for layer in z.GetLayerSet().CuStack()} for z in b.Zones() if not z.GetIsRuleArea()}
changes=[]
for z in b.Zones():
 if z.GetIsRuleArea():continue
 o=z.Outline();count=sum(o.HoleCount(i) for i in range(o.OutlineCount()))
 if not count:continue
 assert z.GetNetname()=='GND' and z.IsOnLayer(P.B_Cu),'Inspect any unexpected power-zone cutout separately'
 holes=[]
 for i in range(o.OutlineCount()):
  for j in range(o.HoleCount(i)):
   h=o.Hole(i,j);holes.append({'area_mm2':abs(h.Area())/1e12,'points_mm':[[P.ToMM(h.CPoint(k).x),P.ToMM(h.CPoint(k).y)] for k in range(h.PointCount())]})
 outer=perimeters[z.m_Uuid.AsString()];o.RemoveAllContours()
 for points in outer:
  idx=o.NewOutline()
  for x,y in points:o.Append(x,y,idx)
 assert o.OutlineCount()==len(outer) and all(o.HoleCount(i)==0 for i in range(o.OutlineCount()))
 changes.append({'uuid':z.m_Uuid.AsString(),'net':z.GetNetname(),'layers':[b.GetLayerName(layer) for layer in z.GetLayerSet().CuStack()],'name':z.GetZoneName(),'removed_holes':holes})
assert sum(len(c['removed_holes']) for c in changes)==38
assert perimeters=={z.m_Uuid.AsString():perimeter(z) for z in b.Zones()}
changed_ids={c['uuid'] for c in changes};assert all(z.Outline().Format()==original_outlines[z.m_Uuid.AsString()] for z in b.Zones() if z.m_Uuid.AsString() not in changed_ids)
for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
b.BuildConnectivity();filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity()
assert tracks=={t.m_Uuid.AsString():ts(t) for t in b.GetTracks()};assert placements=={f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in b.GetFootprints()}
pending=rt/'filled.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b);assert sha(main)==source_sha;shutil.copyfile(pending,main)
filled_after={z.m_Uuid.AsString():{b.GetLayerName(layer):z.GetFilledPolysList(layer).Area()/1e12 for layer in z.GetLayerSet().CuStack()} for z in b.Zones() if not z.GetIsRuleArea()}
report={'source_sha256':source_sha,'applied_sha256':sha(main),'changed_zones':changes,'removed_cutouts':38,'cutout_area_mm2':sum(h['area_mm2'] for c in changes for h in c['removed_holes']),'all_zone_outer_perimeters_unchanged':True,'tracks_vias_and_component_placement_unchanged':True,'all_In1_and_In2_zone_outlines_unchanged':True,'filled_area_before_mm2':filled_before,'filled_area_after_mm2':filled_after}
(out/'all-zone-cutouts-fill.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('Filled 38 cutouts in',len(changes),'existing B.Cu GND zones',report['applied_sha256'],flush=True)
