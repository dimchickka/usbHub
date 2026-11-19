import os,json,hashlib,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/lower-left'
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:os.environ[k]=str(rt/n)
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(main);rep=json.loads((out/'lower-left-finish.json').read_text());assert source_sha==rep['applied_sha256']
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project);ts={t.m_Uuid.AsString():t for t in b.GetTracks()}
points=[(410490000,142400000),(412590000,144500000),(436185404,144500000),(439517702,147832298),(450380000,136970000)]
ids=rep['usb_added_uuids'][1:];assert len(ids)==4
for u,a,z in zip(ids,points,points[1:]):ts[u].SetStart(P.VECTOR2I(*a));ts[u].SetEnd(P.VECTOR2I(*z))
ts['ef1b19f2-aa4f-4f4b-b526-749951612edc'].SetStart(P.VECTOR2I(478320200,108960000))
t=ts['edce690e-53b7-47e1-94ba-d9708f971fac'];assert t.GetNetname()=='GND';t.SetStart(P.VECTOR2I(478320200,108460000));t.SetEnd(P.VECTOR2I(478320200,109460000))
for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
b.BuildConnectivity();filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity();pending=rt/'last.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b);assert sha(main)==source_sha;shutil.copyfile(pending,main)
rep['applied_sha256']=sha(main);rep['usb_in2_corridor_y_mm']=144.5;rep['XL2_GND_bridge_between_pads_5_6_7']=True;(out/'lower-left-finish.json').write_text(json.dumps(rep,indent=2));print('Applied final seam adjustment',sha(main),flush=True)
