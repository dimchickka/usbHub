import os,json,hashlib
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/lower-left';os.environ['KICAD_CONFIG_HOME']=str(rt/'config')
import pcbnew as P
io=P.PCB_IO_KICAD_SEXPR();a=io.LoadBoard(str(rt/'current-before.tmp'),None);b=io.LoadBoard(str(hw/'USB_PD_Charger.kicad_pcb'),None);rep=json.loads((out/'lower-left-copy.json').read_text());finish=json.loads((out/'lower-left-finish.json').read_text())
def sig(t):
 s=[t.GetClass(),t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
 if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y])
 if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return s
before={t.m_Uuid.AsString():sig(t) for t in a.GetTracks()};after={t.m_Uuid.AsString():sig(t) for t in b.GetTracks()};allowed_removed=set(rep['removed_uuids'])|set(finish['usb_removed_uuids']);allowed_added=set(rep['added_uuids'])|set(finish['usb_added_uuids'])|set(finish.get('usb_bridge_track_uuids',[]))|set(finish.get('usb_bridge_via_uuids',[]))|{x['added_uuid'] for x in rep['source_fixes']};allowed_modified={x['track_uuid'] for x in rep['source_fixes']}|{'287324b4-bec9-490b-819d-7666f27b7b39','abf5ea7a-3802-4d37-8250-1ed29fdd7737','293ac3e6-f7bf-4ce0-be2d-15c67c53eae6','ef1b19f2-aa4f-4f4b-b526-749951612edc','edce690e-53b7-47e1-94ba-d9708f971fac'}
assert set(before)-set(after)<=allowed_removed;assert set(after)-set(before)<=allowed_added;assert all(after[u]==s for u,s in before.items() if u not in allowed_removed|allowed_modified)
def fp(board):return {f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in board.GetFootprints()}
assert fp(a)==fp(b);assert {z.m_Uuid.AsString():z.Outline().Format() for z in a.Zones()}=={z.m_Uuid.AsString():z.Outline().Format() for z in b.Zones()}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();h=sha(hw/'USB_PD_Charger.kicad_pcb');m=json.loads((out/'lower-left-pattern-check.json').read_text());assert h==m['main_sha256'];assert all(not r['missing'] and not r['extra'] for r in m['pattern_results'])
proof={'main_sha256':h,'tracks_outside_template_and_listed_seam_repairs_unchanged':True,'component_placement_unchanged':True,'zone_outlines_unchanged':True,'sdram_track_geometry_unchanged':True};(out/'lower-left-preservation-check.json').write_text(json.dumps(proof,indent=2))
for name,key in [('production-data.json','source_pcb_sha256'),('fuse-selection.json','pcb_sha256'),('native-audit.json','main_sha')]:
 p=out/name;j=json.loads(p.read_text());j[key]=h
 if name=='native-audit.json':
  j.update(tracks=m['tracks'],vias=m['vias'],latest_template_source='DD24/DD27/DD28');j['sdram']['lengths_mm']=m['sdram_lengths_mm']
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
print('Preservation and pattern checks passed',h)
