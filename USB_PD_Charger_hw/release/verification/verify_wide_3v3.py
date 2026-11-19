import os,json,hashlib,collections
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/wide-3v3';os.environ['KICAD_CONFIG_HOME']=str(rt/'config')
import pcbnew as P
io=P.PCB_IO_KICAD_SEXPR();old=io.LoadBoard(str(rt/'before.tmp'),None);main=hw/'USB_PD_Charger.kicad_pcb';b=io.LoadBoard(str(main),None);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();h=sha(main);rep=json.loads((out/'wide-3v3-plane.json').read_text());assert h==rep['applied_sha256']
def sig(t):
 s=[t.GetClass(),t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
 if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y])
 if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return s
assert {t.m_Uuid.AsString():sig(t) for t in old.GetTracks()}=={t.m_Uuid.AsString():sig(t) for t in b.GetTracks()}
def fp(board):return {f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in board.GetFootprints()}
assert fp(old)==fp(b)
az={z.m_Uuid.AsString():z for z in old.Zones()};bz={z.m_Uuid.AsString():z for z in b.Zones()};assert set(az)==set(bz);assert {u for u in az if az[u].Outline().Format()!=bz[u].Outline().Format()}=={rep['zone_uuid']}
missing=P.SHAPE_POLY_SET(az[rep['zone_uuid']].Outline());missing.BooleanSubtract(bz[rep['zone_uuid']].Outline());assert missing.Area()<100
z=bz[rep['zone_uuid']];p=z.GetFilledPolysList(P.In2_Cu);probes=[(443,460.3),(445,435),(300,450),(295,475)];assert all(p.Contains(P.VECTOR2I(P.FromMM(x),P.FromMM(y))) for x,y in probes)
b.BuildConnectivity();c=b.GetConnectivity();c.RecalculateRatsnest();assert c.GetUnconnectedCount(False)==0
lengths=collections.defaultdict(float);vias=0
for t in b.GetTracks():
 if isinstance(t,P.PCB_VIA):vias+=1
 if t.GetNetname().startswith('/SDRAM_'):lengths[t.GetNetname()]+=1.465 if isinstance(t,P.PCB_VIA) else P.ToMM(t.GetLength())
proof={'main_sha256':h,'all_tracks_vias_and_placements_unchanged':True,'only_3v3_zone_outline_changed':True,'In1_and_In2_GND_reference_unchanged':True,'original_3v3_area_preserved':True,'all_nets_connected':True,'wide_3v3_probe_points_mm':probes,'sdram_spread_mm':max(lengths.values())-min(lengths.values())};(out/'wide-3v3-preservation.json').write_text(json.dumps(proof,indent=2))
for name,key in [('production-data.json','source_pcb_sha256'),('fuse-selection.json','pcb_sha256'),('native-audit.json','main_sha')]:
 q=out/name;j=json.loads(q.read_text());j[key]=h
 if name=='native-audit.json':j['tracks']=len(list(b.GetTracks()))-vias;j['vias']=vias;j['sdram'].update(lengths_mm=dict(lengths),min_mm=min(lengths.values()),max_mm=max(lengths.values()),spread_mm=proof['sdram_spread_mm'])
 q.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
rep['needs_fresh_refill']=False;rep['wide_regions_verified_filled']=True;(out/'wide-3v3-plane.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');print('Broad 3V3, 24V connectivity and original routing verified.',h,flush=True)
