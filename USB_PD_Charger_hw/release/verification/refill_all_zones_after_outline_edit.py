"""Reload expanded outlines before refill so all cached spatial bounds are current."""
import os,json,hashlib,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/all-fill'
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:os.environ[k]=str(rt/n)
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(main);rep=json.loads((out/'remaining-zone-voids-fill.json').read_text());assert source_sha==rep['applied_sha256']
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project)
for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
b.BuildConnectivity();filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity();pending=rt/'reloaded-refill.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b);assert sha(main)==source_sha;shutil.copyfile(pending,main)
rep.update(applied_sha256=sha(main),refilled_after_reloading_outline_geometry=True);(out/'remaining-zone-voids-fill.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');print('Fresh spatial-cache refill completed',sha(main),flush=True)
