"""Extend existing In2 3V3 fingers to the exactly copied template vias."""
import os,json,hashlib,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/right-complete'
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:os.environ[k]=str(rt/n)
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(main);expected=json.loads((out/'right-row-complete.json').read_text())['candidate_sha256'];assert source_sha==expected
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project)
z=next(z for z in b.Zones() if z.m_Uuid.AsString()=='0d6c0e1a-8aaa-4fe2-8b9e-0621bf230124');assert z.GetNetname()=='+3v3' and z.IsOnLayer(P.In2_Cu)
original={t.m_Uuid.AsString():t.Format() if hasattr(t,'Format') else str(t) for t in []}
otherzones={q.m_Uuid.AsString():q.Outline().Format() for q in b.Zones() if q!=z};extensions=[]
for dy in [69600000,142325800,211925800,281525800]:
 x1,y1=429617109,145131298+dy;x2,y2=430992109,147181298+dy;r=600000
 points=[(x1-r,y1-r),(x1+r,y1-r),(x2+r,y2-r),(x2+r,y2+r),(x2-r,y2+r),(x1-r,y1+r)]
 poly=P.SHAPE_POLY_SET();poly.NewOutline()
 for x,y in points:poly.Append(x,y)
 z.Outline().BooleanAdd(poly);extensions.append([[P.ToMM(x),P.ToMM(y)] for x,y in points])
assert otherzones=={q.m_Uuid.AsString():q.Outline().Format() for q in b.Zones() if q!=z}
for q in b.Zones():q.UnFill();q.SetNeedRefill(True)
b.BuildConnectivity();filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity();pending=rt/'plane-result.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b);assert sha(main)==source_sha
shutil.copyfile(pending,main);(out/'right-row-plane-reach.json').write_text(json.dumps({'source_sha256':source_sha,'applied_sha256':sha(main),'zone_uuid':z.m_Uuid.AsString(),'extensions_mm':extensions,'all_other_zone_outlines_unchanged':True},indent=2));print('Applied four local 3V3 plane extensions',sha(main),flush=True)
