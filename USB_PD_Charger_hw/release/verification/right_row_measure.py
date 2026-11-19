import os,json,hashlib,collections
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/right-row';os.environ['KICAD_CONFIG_HOME']=str(rt/'config')
import pcbnew as P
main=hw/'USB_PD_Charger.kicad_pcb';b=P.PCB_IO_KICAD_SEXPR().LoadBoard(str(main),None)
lengths=collections.defaultdict(float);widths=collections.defaultdict(set);vias=0;rows=[];pads=[]
for t in b.GetTracks():
 if isinstance(t,P.PCB_VIA):vias+=1
 if t.GetNetname().startswith('/SDRAM_'):
  lengths[t.GetNetname()]+=1.465 if isinstance(t,P.PCB_VIA) else P.ToMM(t.GetLength())
  if not isinstance(t,P.PCB_VIA):widths[t.GetNetname()].add(P.ToMM(t.GetWidth()))
 if 400<P.ToMM(t.GetStart().x)<470 and 140<P.ToMM(t.GetStart().y)<270:
  rows.append({'kind':t.GetClass(),'start':[P.ToMM(t.GetStart().x),P.ToMM(t.GetStart().y)],'end':[P.ToMM(t.GetEnd().x),P.ToMM(t.GetEnd().y)],'layer':t.GetLayerName(),'width':P.ToMM(t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth()),'net':t.GetNetname()})
for f in b.GetFootprints():
 if 400<P.ToMM(f.GetPosition().x)<470 and 140<P.ToMM(f.GetPosition().y)<270:
  for p in f.Pads():pads.append({'ref':f.GetReference(),'num':p.GetNumber(),'pos':[P.ToMM(p.GetPosition().x),P.ToMM(p.GetPosition().y)],'size':[P.ToMM(p.GetSize().x),P.ToMM(p.GetSize().y)],'angle':p.GetOrientationDegrees()})
j={'source_sha256':hashlib.sha256(main.read_bytes()).hexdigest(),'tracks':rows,'pads':pads,'sdram_lengths_mm':dict(lengths),'sdram_min_mm':min(lengths.values()),'sdram_max_mm':max(lengths.values()),'sdram_spread_mm':max(lengths.values())-min(lengths.values()),'sdram_widths':{n:sorted(v) for n,v in widths.items()},'via_count':vias,'track_objects':len(list(b.GetTracks())),'footprints':len(list(b.GetFootprints()))}
(rt/'geometry.json').write_text(json.dumps(j));print({k:v for k,v in j.items() if k not in ['tracks','pads','sdram_lengths_mm','sdram_widths']})
