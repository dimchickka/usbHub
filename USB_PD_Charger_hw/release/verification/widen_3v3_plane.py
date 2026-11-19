"""Expand the existing 3V3 In2 plane into two broad side regions; retain central 24V."""
import os,json,hashlib,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/wide-3v3';rt.mkdir(parents=True,exist_ok=True)
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:p=rt/n;p.mkdir(exist_ok=True);os.environ[k]=str(p)
config=rt/'config/9.0';config.mkdir(exist_ok=True)
for n in ['fp','sym']:(config/(n+'-lib-table')).write_text('('+n+'_lib_table (version 7))\n')
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(main);(rt/'before.tmp').write_bytes(main.read_bytes())
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project)
def sig(t):
 s=[t.GetClass(),t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
 if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y])
 if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return s
tracks={t.m_Uuid.AsString():sig(t) for t in b.GetTracks()};placements={f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in b.GetFootprints()};z=next(z for z in b.Zones() if z.m_Uuid.AsString()=='0d6c0e1a-8aaa-4fe2-8b9e-0621bf230124');assert z.GetNetname()=='+3v3' and z.IsOnLayer(P.In2_Cu)
old=P.SHAPE_POLY_SET(z.Outline());otherzones={q.m_Uuid.AsString():q.Outline().Format() for q in b.Zones() if q.m_Uuid.AsString()!=z.m_Uuid.AsString()}
power24=[p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname()=='+24v']+[t for t in b.GetTracks() if isinstance(t,P.PCB_VIA) and t.GetNetname()=='+24v']
assert all(319000000<=p.GetPosition().x<=424000000 for p in power24 if p.GetPosition().y>139000000),'Preserve every 24V load and feeder in central band'
regions=[[(258700000,139000000),(318000000,139000000),(318000000,498108000),(258700000,498108000)],[(425000000,139000000),(484300000,139000000),(484300000,498108000),(425000000,498108000)]]
for points in regions:
 patch=P.SHAPE_POLY_SET();patch.NewOutline()
 for x,y in points:patch.Append(x,y)
 z.Outline().BooleanAdd(patch)
missing=P.SHAPE_POLY_SET(old);missing.BooleanSubtract(z.Outline());assert missing.Area()<100
assert otherzones=={q.m_Uuid.AsString():q.Outline().Format() for q in b.Zones() if q.m_Uuid.AsString()!=z.m_Uuid.AsString()}
for q in b.Zones():q.CacheBoundingBox();q.UnFill();q.SetNeedRefill(True)
b.BuildConnectivity();filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity();assert tracks=={t.m_Uuid.AsString():sig(t) for t in b.GetTracks()};assert placements=={f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in b.GetFootprints()}
pending=rt/'wide.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b);assert sha(main)==source_sha;shutil.copyfile(pending,main)
report={'source_sha256':source_sha,'applied_sha256':sha(main),'zone_uuid':z.m_Uuid.AsString(),'same_existing_zone':True,'side_regions_mm':[[[P.ToMM(x),P.ToMM(y)] for x,y in p] for p in regions],'central_24V_band_x_mm':[318,425],'all_24V_load_pads_and_vias_remain_in_central_band':True,'existing_3V3_plane_area_fully_preserved':True,'all_other_zone_outlines_unchanged':True,'tracks_vias_placements_unchanged':True,'original_3V3_outline_area_mm2':old.Area()/1e12,'new_3V3_outline_area_mm2':z.Outline().Area()/1e12}
(out/'wide-3v3-plane.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('Expanded existing 3V3 plane to broad side regions',sha(main),flush=True)
