"""Find wide unfilled regions inside existing zone perimeters, excluding real copper."""
import os,json,hashlib
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/all-fill';os.environ['KICAD_CONFIG_HOME']=str(rt/'config')
import pcbnew as P
b=P.PCB_IO_KICAD_SEXPR().LoadBoard(str(hw/'USB_PD_Charger.kicad_pcb'),None);rows=[]
for layer in [P.F_Cu,P.In1_Cu,P.In2_Cu,P.B_Cu]:
 domain=P.SHAPE_POLY_SET();copper=P.SHAPE_POLY_SET()
 for z in b.Zones():
  if z.IsOnLayer(layer) and not z.GetIsRuleArea():domain.BooleanAdd(z.Outline());copper.Append(z.GetFilledPolysList(layer))
 for t in b.GetTracks():
  if t.IsOnLayer(layer):t.TransformShapeToPolygon(copper,layer,0,10000,P.ERROR_INSIDE)
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.IsOnLayer(layer):p.TransformShapeToPolygon(copper,layer,0,10000,P.ERROR_INSIDE)
 copper.Simplify();empty=P.SHAPE_POLY_SET(domain);empty.BooleanSubtract(copper);empty.Deflate(650000,P.CORNER_STRATEGY_ROUND_ALL_CORNERS,10000)
 gaps=[]
 for i in range(empty.OutlineCount()):
  poly=empty.COutline(i);area=abs(poly.Area())/1e12
  if area<.5:continue
  xs=[P.ToMM(poly.CPoint(k).x) for k in range(poly.PointCount())];ys=[P.ToMM(poly.CPoint(k).y) for k in range(poly.PointCount())];gaps.append({'eroded_area_mm2':area,'bbox_mm':[min(xs),min(ys),max(xs),max(ys)],'points_mm':[[P.ToMM(poly.CPoint(k).x),P.ToMM(poly.CPoint(k).y)] for k in range(poly.PointCount())]})
 rows.append({'layer':b.GetLayerName(layer),'wide_voids':gaps});print(b.GetLayerName(layer),'wide voids',len(gaps),'areas',[round(g['eroded_area_mm2'],2) for g in gaps],flush=True)
(out/'zone-void-audit.json').write_text(json.dumps({'source_sha256':hashlib.sha256((hw/'USB_PD_Charger.kicad_pcb').read_bytes()).hexdigest(),'minimum_free_radius_mm':.65,'layers':rows},ensure_ascii=False,indent=2),encoding='utf-8')
