import os,json,zipfile,hashlib,collections
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/right-row';rt.mkdir(parents=True,exist_ok=True)
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:
 p=rt/n;p.mkdir(exist_ok=True);os.environ[k]=str(p)
config=rt/'config/9.0';config.mkdir(exist_ok=True)
for n in ['sym','fp']:(config/(n+'-lib-table')).write_text('('+n+'_lib_table (version 7))\n')
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';data=main.read_bytes();(rt/'current-before.tmp').write_bytes(data)
with zipfile.ZipFile('D:/study/7sem/courseWork/USB_PD_Charger_work_archive_20261118/fuse-qualified-before.zip') as z:
 names=[n for n in z.namelist() if n.endswith('.kicad_pcb')];assert len(names)==1;(rt/'previous.tmp').write_bytes(z.read(names[0]))
io=P.PCB_IO_KICAD_SEXPR();a=io.LoadBoard(str(rt/'previous.tmp'),None);b=io.LoadBoard(str(main),None)
def sig(t):
 s=[t.GetClass(),t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
 if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y])
 if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return s
aa={t.m_Uuid.AsString():sig(t) for t in a.GetTracks()};bb={t.m_Uuid.AsString():sig(t) for t in b.GetTracks()}
deleted={u:s for u,s in aa.items() if u not in bb};added={u:s for u,s in bb.items() if u not in aa};modified={u:{'before':aa[u],'after':bb[u]} for u in aa.keys()&bb.keys() if aa[u]!=bb[u]}
info={'source_sha256':hashlib.sha256(data).hexdigest(),'deleted':deleted,'added':added,'modified':modified,'footprints':[]}
for f in b.GetFootprints():
 info['footprints'].append({'ref':f.GetReference(),'value':f.GetValue(),'x':P.ToMM(f.GetPosition().x),'y':P.ToMM(f.GetPosition().y),'angle':f.GetOrientationDegrees(),'path':f.GetPath().AsString(),'pads':[{ 'num':p.GetNumber(),'net':p.GetNetname(),'x':P.ToMM(p.GetPosition().x),'y':P.ToMM(p.GetPosition().y)} for p in f.Pads()]})
(out/'right-row-inspection.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print('TRACK CHANGES',len(deleted),len(added),len(modified),flush=True)
changes=list(deleted.values())+list(added.values())+[s['after'] for s in modified.values()]
print('CHANGED NETS',collections.Counter(s[1] for s in changes),flush=True)
print('CHANGED BBOX',[(min(s[i] for s in changes)/1e6,max(s[i] for s in changes)/1e6) for i in [4,5,6,7]],flush=True)
print('CONTROLLERS',[(f['ref'],f['value'],f['x'],f['y'],f['angle'],f['path']) for f in info['footprints'] if f['value'].startswith(('SC8815','STM32'))],flush=True)
