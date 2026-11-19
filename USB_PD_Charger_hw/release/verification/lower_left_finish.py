import os,json,hashlib,collections,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/lower-left'
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:os.environ[k]=str(rt/n)
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(main);rep=json.loads((out/'lower-left-copy.json').read_text());assert source_sha==rep['candidate_sha256']
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project)
def key(t):
 a,z=sorted([(t.GetStart().x,t.GetStart().y),(t.GetEnd().x,t.GetEnd().y)]);v=[t.GetClass(),t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),*a,*z]
 if isinstance(t,P.PCB_ARC):v.extend([t.GetMid().x,t.GetMid().y])
 if isinstance(t,P.PCB_VIA):v.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return tuple(v)
groups=collections.defaultdict(list)
for t in b.GetTracks():groups[key(t)].append(t)
inserted=set(rep['added_uuids']);held=[];deduplicated=[]
for items in groups.values():
 if len(items)<2:continue
 originals=[t for t in items if t.m_Uuid.AsString() not in inserted];new=[t for t in items if t.m_Uuid.AsString() in inserted]
 for t in (new if originals else new[1:]):b.Remove(t);held.append(t);deduplicated.append(t.m_Uuid.AsString())
lookup={t.m_Uuid.AsString():t for t in b.GetTracks()};net=b.FindNet('/USB-C_VBUS').GetNetCode();front=P.F_Cu;back=P.B_Cu;inner=P.In2_Cu
removed_usb=['28bfcaea-de8e-4d68-a8bf-c1a42d10dc47','c558d0c6-20c7-4b75-8026-b323094de435','7a0b0cfd-3a60-4e04-9492-c21c8f529b6b','3cdeef9a-14f7-459f-b89d-2d47df09ec88','4d0af400-0b14-4826-a9cd-dd853973bdc1','c5942206-7510-4af2-b32b-a6898dfb834f','306bcc0f-1aac-4217-98bb-cfb538cb2658']
for u in removed_usb:b.Remove(lookup[u]);held.append(lookup[u])
lookup['287324b4-bec9-490b-819d-7666f27b7b39'].SetPosition(P.VECTOR2I(410490000,142400000))
lookup['abf5ea7a-3802-4d37-8250-1ed29fdd7737'].SetEnd(P.VECTOR2I(409500000,142400000))
lookup['293ac3e6-f7bf-4ce0-be2d-15c67c53eae6'].SetStart(P.VECTOR2I(450380000,136970000))
extra=[]
def addtrack(layer,a,z):
 t=P.PCB_TRACK(b);t.SetNetCode(net);t.SetLayer(layer);t.SetWidth(150000);t.SetStart(P.VECTOR2I(*a));t.SetEnd(P.VECTOR2I(*z));b.Add(t);extra.append(t.m_Uuid.AsString())
addtrack(back,(409500000,142400000),(410490000,142400000))
points=[(410490000,142400000),(411390000,143300000),(434985404,143300000),(439517702,147832298),(450380000,136970000)]
for a,z in zip(points,points[1:]):addtrack(inner,a,z)
# Existing open GND connection at the display connector, present before this transfer.
g=lookup['ef1b19f2-aa4f-4f4b-b526-749951612edc'];assert g.GetNetname()=='GND';g.SetStart(P.VECTOR2I(478320200,109460000))
for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
b.BuildConnectivity();filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity();pending=rt/'finished.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b);assert sha(main)==source_sha;shutil.copyfile(pending,main)
rep['added_uuids']=[u for u in rep['added_uuids'] if u not in deduplicated];rep['applied_sha256']=sha(main);rep['duplicates_avoided']=len(deduplicated);(out/'lower-left-copy.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'lower-left-finish.json').write_text(json.dumps({'source_sha256':source_sha,'applied_sha256':sha(main),'deduplicated_added_objects':deduplicated,'usb_vbus_sense_route_repositioned_to_clear_template':True,'usb_removed_uuids':removed_usb,'usb_added_uuids':extra,'XL2_GND_open_end_restored':True},indent=2));print('Finished template seam corrections',sha(main),flush=True)
