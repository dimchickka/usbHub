import os,json,hashlib,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/lower-left'
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:os.environ[k]=str(rt/n)
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rep=json.loads((out/'lower-left-finish.json').read_text());source_sha=sha(main);assert source_sha==rep['applied_sha256']
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project);ts={t.m_Uuid.AsString():t for t in b.GetTracks()};net=b.FindNet('/USB-C_VBUS').GetNetCode();held=[]
oldids=rep['usb_added_uuids'][1:]
for u in oldids:b.Remove(ts[u]);held.append(ts[u])
newids=[];newvias=[]
for x,y in [(428900000,143900000),(434300000,143200000)]:
 v=P.PCB_VIA(b);v.SetViaType(P.VIATYPE_THROUGH);v.SetLayerPair(P.F_Cu,P.B_Cu);v.SetPosition(P.VECTOR2I(x,y));v.SetWidth(600000);v.SetDrill(300000);v.SetNetCode(net);b.Add(v);newvias.append(v.m_Uuid.AsString())
routes=[(P.In2_Cu,[(410490000,142400000),(412590000,144500000),(428300000,144500000),(428900000,143900000)]),(P.B_Cu,[(428900000,143900000),(429500000,144500000),(433000000,144500000),(434300000,143200000)]),(P.In2_Cu,[(434300000,143200000),(435600000,144500000),(436185404,144500000),(439517702,147832298),(450380000,136970000)])]
for layer,points in routes:
 for a,z in zip(points,points[1:]):
  t=P.PCB_TRACK(b);t.SetLayer(layer);t.SetNetCode(net);t.SetWidth(150000);t.SetStart(P.VECTOR2I(*a));t.SetEnd(P.VECTOR2I(*z));b.Add(t);newids.append(t.m_Uuid.AsString())
for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
b.BuildConnectivity();filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity();pending=rt/'usb-bridge.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b);assert sha(main)==source_sha;shutil.copyfile(pending,main)
rep.update(applied_sha256=sha(main),usb_intermediate_removed_uuids=oldids,usb_bridge_track_uuids=newids,usb_bridge_via_uuids=newvias,usb_bridge_via_size_mm=[.6,.3],usb_bridge_purpose='Preserve In2 3V3 plane continuity while retaining exact repeated template routing');(out/'lower-left-finish.json').write_text(json.dumps(rep,indent=2));print('USB sense bridge applied',sha(main),flush=True)
