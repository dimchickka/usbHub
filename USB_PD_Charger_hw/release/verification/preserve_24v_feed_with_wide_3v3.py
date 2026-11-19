"""Keep broad 3V3 logic regions while retaining the existing left/bottom 24V input route."""
import os,json,hashlib,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/wide-3v3'
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:os.environ[k]=str(rt/n)
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rep=json.loads((out/'wide-3v3-plane.json').read_text());source_sha=sha(main);assert source_sha==rep['applied_sha256']
old=P.PCB_IO_KICAD_SEXPR().LoadBoard(str(rt/'before.tmp'),None);source=next(z for z in old.Zones() if z.m_Uuid.AsString()==rep['zone_uuid'])
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project);z=next(z for z in b.Zones() if z.m_Uuid.AsString()==rep['zone_uuid']);o=z.Outline();o.RemoveAllContours();o.Append(source.Outline())
regions=[[(280000000,139000000),(318000000,139000000),(318000000,491500000),(280000000,491500000)],[(425000000,139000000),(484300000,139000000),(484300000,498108000),(425000000,498108000)]]
for points in regions:
 patch=P.SHAPE_POLY_SET();patch.NewOutline()
 for x,y in points:patch.Append(x,y)
 o.BooleanAdd(patch)
missing=P.SHAPE_POLY_SET(source.Outline());missing.BooleanSubtract(o);assert missing.Area()<100
z.CacheBoundingBox();z.UnFill();z.SetNeedRefill(True);pending=rt/'wide-feeder-geometry.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b);assert sha(main)==source_sha;shutil.copyfile(pending,main)
rep.update(applied_sha256=sha(main),side_regions_mm=[[[P.ToMM(x),P.ToMM(y)] for x,y in p] for p in regions],left_24V_feed_reserved_x_mm=[258.7,280],bottom_24V_return_reserved_y_mm=[491.5,498.108],new_3V3_outline_area_mm2=o.Area()/1e12,needs_fresh_refill=True);(out/'wide-3v3-plane.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');print('Broad 3V3 retained with 24V perimeter feeder',sha(main),flush=True)
