"""Fill the explicit 3V3 In2 cutout beside C35/C38; preserve all routed copper."""
import os,json,hashlib,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/fill-gap';rt.mkdir(parents=True,exist_ok=True)
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:p=rt/n;p.mkdir(exist_ok=True);os.environ[k]=str(p)
config=rt/'config/9.0';config.mkdir(exist_ok=True)
for n in ['fp','sym']:(config/(n+'-lib-table')).write_text('('+n+'_lib_table (version 7))\n')
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(main);(rt/'before.tmp').write_bytes(main.read_bytes())
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project)
def track_signature(t):
 s=[t.GetClass(),t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
 if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y])
 if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return s
tracks={t.m_Uuid.AsString():track_signature(t) for t in b.GetTracks()};placements={f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in b.GetFootprints()}
target=next(z for z in b.Zones() if z.m_Uuid.AsString()=='0d6c0e1a-8aaa-4fe2-8b9e-0621bf230124');assert target.GetNetname()=='+3v3' and target.IsOnLayer(P.In2_Cu)
otherzones={z.m_Uuid.AsString():z.Outline().Format() for z in b.Zones() if z.m_Uuid.AsString()!=target.m_Uuid.AsString()};o=target.Outline();assert o.OutlineCount()==1 and o.HoleCount(0)==1;hole=o.Hole(0,0);points=[(hole.CPoint(i).x,hole.CPoint(i).y) for i in range(hole.PointCount())]
assert min(x for x,y in points)==287500000 and max(x for x,y in points)==292000000 and min(y for x,y in points)==101500000 and max(y for x,y in points)==134500000
patch=P.SHAPE_POLY_SET();patch.NewOutline()
for x,y in points:patch.Append(x,y)
o.BooleanAdd(patch);assert o.OutlineCount()==1 and o.HoleCount(0)==0
assert otherzones=={z.m_Uuid.AsString():z.Outline().Format() for z in b.Zones() if z.m_Uuid.AsString()!=target.m_Uuid.AsString()}
for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
b.BuildConnectivity();filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity()
assert tracks=={t.m_Uuid.AsString():track_signature(t) for t in b.GetTracks()};assert placements=={f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in b.GetFootprints()}
pending=rt/'filled.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b);assert sha(main)==source_sha;shutil.copyfile(pending,main)
report={'source_sha256':source_sha,'applied_sha256':sha(main),'changed_zone_uuid':target.m_Uuid.AsString(),'removed_cutout_points_mm':[[P.ToMM(x),P.ToMM(y)] for x,y in points],'tracks_vias_and_placements_preserved':True,'all_other_zone_outlines_preserved':True}
(out/'in2-gap-fill.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('Filled In2 3V3 cutout next to C35/C38',report['applied_sha256'],flush=True)
