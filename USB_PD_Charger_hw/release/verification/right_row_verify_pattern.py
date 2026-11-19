"""Independent geometry comparison of local signals, SPI escapes, and power branches."""
import os,json,collections,hashlib
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/right-complete';os.environ['KICAD_CONFIG_HOME']=str(rt/'config')
import pcbnew as P
main=hw/'USB_PD_Charger.kicad_pcb';b=P.PCB_IO_KICAD_SEXPR().LoadBoard(str(main),None);fs=list(b.GetFootprints());tracks=list(b.GetTracks());refs={f.GetReference():f for f in fs};group=lambda f:f.GetPath().AsString().split('/')[1];role=lambda f:'/'.join(f.GetPath().AsString().split('/')[2:]);src={role(f):f for f in fs if group(f)==group(refs['DD29'])};source_refs={f.GetReference() for f in src.values()};netrefs=collections.defaultdict(set)
for f in fs:
 for p in f.Pads():netrefs[p.GetNetCode()].add(f.GetReference())
private={n for n,r in netrefs.items() if r and r<=source_refs};spi={'/STM8_CS','/STM_MOSI','/STM_MISO','/STM_SCK'}
def localspi(t,dy=0):return all(440000000<=v.x<=461000000 and 170000000<=v.y-dy<=195000000 for v in [t.GetStart(),t.GetEnd()])
def sig(t,dy=0,net=None):
 a=(t.GetStart().x,t.GetStart().y+dy);z=(t.GetEnd().x,t.GetEnd().y+dy);a,z=sorted([a,z]);s=[t.GetClass(),net or t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),*a,*z]
 if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y+dy])
 if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return tuple(s)
results=[]
for ref in ['DD34','DD39','DD44','DD49']:
 target=refs[ref];dy=target.GetPosition().y-refs['DD29'].GetPosition().y;dst={role(f):f for f in fs if group(f)==group(target)};mapping={}
 for r,sf in src.items():
  df=dst[r];assert sf.GetPosition().x==df.GetPosition().x and sf.GetPosition().y+dy==df.GetPosition().y
  dp={p.GetNumber():p for p in df.Pads()}
  for sp in sf.Pads():
   sn=sp.GetNetCode();dn=dp[sp.GetNumber()].GetNetCode();assert sn not in mapping or mapping[sn]==dn;mapping[sn]=dn
 expected=collections.Counter(sig(t,dy,b.FindNet(mapping[t.GetNetCode()]).GetNetname()) for t in tracks if t.GetNetCode() in private or t.GetNetname() in spi and localspi(t))
 targetprivate={mapping[n] for n in private};targetspi={mapping[b.FindNet(n).GetNetCode()] for n in spi}
 actual=collections.Counter(sig(t) for t in tracks if t.GetNetCode() in targetprivate or t.GetNetCode() in targetspi and localspi(t,dy))
 missing=list((expected-actual).elements());extra=list((actual-expected).elements());results.append({'target':ref,'expected_local_signal_and_SPI_objects':sum(expected.values()),'missing':missing,'extra':extra})
print(json.dumps(results),flush=True)
report={'source_sha256':hashlib.sha256(main.read_bytes()).hexdigest(),'results':results};(out/'right-row-pattern-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');assert all(not r['missing'] and not r['extra'] for r in results)
