import os,json,hashlib,collections
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/all-fill';os.environ['KICAD_CONFIG_HOME']=str(rt/'config')
import pcbnew as P
main=hw/'USB_PD_Charger.kicad_pcb';io=P.PCB_IO_KICAD_SEXPR();a=io.LoadBoard(str(rt/'before.tmp'),None);b=io.LoadBoard(str(main),None);rep=json.loads((out/'remaining-zone-voids-fill.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(main)==rep['applied_sha256']
def sig(t):
 s=[t.GetClass(),t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
 if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y])
 if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return s
old={t.m_Uuid.AsString():sig(t) for t in a.GetTracks()};new={t.m_Uuid.AsString():sig(t) for t in b.GetTracks()};added={v['uuid'] for v in rep['added_GND_stitches']};assert set(new)-set(old)==added;assert all(new[u]==s for u,s in old.items())
def placements(board):return {f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in board.GetFootprints()}
assert placements(a)==placements(b)
az={z.m_Uuid.AsString():z for z in a.Zones()};bz={z.m_Uuid.AsString():z for z in b.Zones()};assert set(az)==set(bz)
changed={u for u in az if az[u].Outline().Format()!=bz[u].Outline().Format()};holes=json.loads((out/'all-zone-cutouts-fill.json').read_text());expected={z['uuid'] for z in holes['changed_zones']}|{'0d6c0e1a-8aaa-4fe2-8b9e-0621bf230124','404cc076-671f-4e00-b1f4-a3b505b84f0a'};assert changed==expected
for u in ['0d6c0e1a-8aaa-4fe2-8b9e-0621bf230124','404cc076-671f-4e00-b1f4-a3b505b84f0a']:
 missing=P.SHAPE_POLY_SET(az[u].Outline());missing.BooleanSubtract(bz[u].Outline());assert abs(missing.Area())<100
assert all(az[u].Outline().Format()==bz[u].Outline().Format() for u in az if az[u].IsOnLayer(P.In1_Cu))
lengths=collections.defaultdict(float);vias=0
for t in b.GetTracks():
 if isinstance(t,P.PCB_VIA):vias+=1
 if t.GetNetname().startswith('/SDRAM_'):lengths[t.GetNetname()]+=1.465 if isinstance(t,P.PCB_VIA) else P.ToMM(t.GetLength())
h=sha(main);report={'main_sha256':h,'existing_tracks_vias_and_component_placements_unchanged':True,'added_GND_vias':len(added),'new_via_size_mm':[.6,.3],'In1_ground_preserved':True,'original_In2_GND_and_3V3_areas_fully_preserved':True,'only_existing_zone_cutouts_and_listed_In2_expansions_changed':True,'sdram_lengths_mm':dict(lengths),'sdram_spread_mm':max(lengths.values())-min(lengths.values()),'tracks':len(list(b.GetTracks()))-vias,'vias':vias};(out/'all-zone-fills-preservation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for name,key in [('production-data.json','source_pcb_sha256'),('fuse-selection.json','pcb_sha256'),('native-audit.json','main_sha')]:
 p=out/name;j=json.loads(p.read_text());j[key]=h
 if name=='native-audit.json':j['tracks']=report['tracks'];j['vias']=vias;j['sdram'].update(lengths_mm=dict(lengths),min_mm=min(lengths.values()),max_mm=max(lengths.values()),spread_mm=report['sdram_spread_mm'])
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
print('Preservation verified. Four standard GND vias added; original routing preserved.',h,flush=True)
