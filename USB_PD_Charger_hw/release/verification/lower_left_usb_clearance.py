import os,json,hashlib,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/lower-left'
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:os.environ[k]=str(rt/n)
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rep=json.loads((out/'lower-left-finish.json').read_text());source_sha=sha(main);assert source_sha==rep['applied_sha256']
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project);ts={t.m_Uuid.AsString():t for t in b.GetTracks()};ids=rep['usb_bridge_track_uuids'];assert len(ids)==10
ts[rep['usb_bridge_via_uuids'][1]].SetPosition(P.VECTOR2I(436700000,144000000))
edits={4:((429500000,144500000),(436200000,144500000)),5:((436200000,144500000),(436700000,144000000)),6:((436700000,144000000),(436700000,145014596)),7:((436700000,145014596),(439517702,147832298)),8:((439517702,147832298),(450380000,136970000))}
for i,(a,z) in edits.items():ts[ids[i]].SetStart(P.VECTOR2I(*a));ts[ids[i]].SetEnd(P.VECTOR2I(*z))
removed=ts[ids[9]];b.Remove(removed)
for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
b.BuildConnectivity();filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity();pending=rt/'usb-clearance.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b);assert sha(main)==source_sha;shutil.copyfile(pending,main)
rep.update(applied_sha256=sha(main),usb_bridge_track_uuids=ids[:9],usb_bridge_exit_via_mm=[436.7,144.0]);(out/'lower-left-finish.json').write_text(json.dumps(rep,indent=2));print('USB bridge exit cleared',sha(main),flush=True)
