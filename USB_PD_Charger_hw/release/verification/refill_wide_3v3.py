"""Reload expanded zone geometry; discard only unconnected 24V copper islands."""
import os,json,hashlib,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/wide-3v3'
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:os.environ[k]=str(rt/n)
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rep=json.loads((out/'wide-3v3-plane.json').read_text());source_sha=sha(main);assert source_sha==rep['applied_sha256']
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project);removed_islands=[]
for z in b.Zones():
 if z.GetNetname()=='+24v' and z.IsOnLayer(P.In2_Cu):z.SetIslandRemovalMode(P.ISLAND_REMOVAL_MODE_ALWAYS);removed_islands.append(z.m_Uuid.AsString())
 z.UnFill();z.SetNeedRefill(True)
b.BuildConnectivity();filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity();pending=rt/'reloaded-wide.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b);assert sha(main)==source_sha;shutil.copyfile(pending,main)
rep.update(applied_sha256=sha(main),refilled_after_reloading_expanded_geometry=True,remove_unconnected_24V_islands_in_zones=removed_islands);(out/'wide-3v3-plane.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');print('Reloaded broad plane and removed unconnected 24V copper remnants',sha(main),flush=True)
