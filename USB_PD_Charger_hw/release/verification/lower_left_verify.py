import os,json,collections,hashlib
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/lower-left';os.environ['KICAD_CONFIG_HOME']=str(rt/'config')
import pcbnew as P
main=hw/'USB_PD_Charger.kicad_pcb';b=P.PCB_IO_KICAD_SEXPR().LoadBoard(str(main),None);b.BuildConnectivity();conn=b.GetConnectivity();rep=json.loads((out/'lower-left-copy.json').read_text());fs=list(b.GetFootprints());tracks=list(b.GetTracks());refs={f.GetReference():f for f in fs};group=lambda f:f.GetPath().AsString().split('/')[1];role=lambda f:'/'.join(f.GetPath().AsString().split('/')[2:]);src={role(f):f for f in fs if group(f)==group(refs['DD24'])};source=refs['DD24'];affected={b.FindNet(n).GetNetCode() for n in rep['affected_private_nets']};spi_names={'/STM3_CS','/STM_MOSI','/STM_MISO','/STM_SCK'}
def sig(t):
 s=[t.GetClass(),t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
 if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y])
 if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return s
def key(s):
 a,z=sorted([(s[4],s[5]),(s[6],s[7])]);return tuple(s[:4])+a+z+tuple(s[8:])
def box(s):return all(280e6<=s[i]<=300e6 for i in [4,6]) and all(448e6<=s[i]<=468e6 for i in [5,7])
def cluster(p):
 seen={};queue=[p]
 while queue:
  obj=queue.pop();u=obj.m_Uuid.AsString()
  if u in seen:continue
  seen[u]=obj;queue.extend(t for t in conn.GetConnectedTracks(obj) if t.GetNetCode()==p.GetNetCode());queue.extend(q for q in conn.GetConnectedPads(obj) if q.GetNetCode()==p.GetNetCode())
 return {u:t for u,t in seen.items() if t.GetClass() in {'PCB_TRACK','PCB_VIA','PCB_ARC'}}
source_items={t.m_Uuid.AsString():t for t in tracks if t.GetNetCode() in affected or t.GetNetname() in spi_names and box(sig(t)) or t.m_Uuid.AsString() in rep['power_source_uuids']}
results=[]
for plan in rep['plans']:
 target=refs[plan['target']];dst={role(f):f for f in fs if group(f)==group(target)};sgn=-1 if plan['rotated_180'] else 1;sx,sy=source.GetPosition().x,source.GetPosition().y;tx,ty=target.GetPosition().x,target.GetPosition().y;mapping={}
 for r,sf in src.items():
  df=dst[r];assert df.GetPosition().x==tx+sgn*(sf.GetPosition().x-sx) and df.GetPosition().y==ty+sgn*(sf.GetPosition().y-sy)
  dp={p.GetNumber():p for p in df.Pads()}
  for sp in sf.Pads():mapping[sp.GetNetCode()]=dp[sp.GetNumber()].GetNetCode()
 def transform(s,inverse=False):
  s=list(s)
  if not inverse:s[1]=b.FindNet(mapping[b.FindNet(s[1]).GetNetCode()]).GetNetname()
  for i in [4,6]+([8] if s[0]=='PCB_ARC' else []):
   s[i]=(sx+sgn*(s[i]-tx)) if inverse else (tx+sgn*(s[i]-sx));s[i+1]=(sy+sgn*(s[i+1]-ty)) if inverse else (ty+sgn*(s[i+1]-sy))
  return s
 power={}
 for r,num in rep['source_power_pads']:power.update(cluster(next(p for p in dst[r].Pads() if p.GetNumber()==num)))
 power_keys={key(transform(sig(t))) for t in source_items.values() if t.GetNetname() in {'GND','+3v3','+24v'}}
 dcodes={mapping[n] for n in affected};spicodes={mapping[b.FindNet(n).GetNetCode()] for n in spi_names};actual_items={t.m_Uuid.AsString():t for t in tracks if t.GetNetCode() in dcodes or t.GetNetCode() in spicodes and box(transform(sig(t),True)) or t.m_Uuid.AsString() in power or key(sig(t)) in power_keys}
 expected=collections.Counter(key(transform(sig(t))) for t in source_items.values());actual=collections.Counter(key(sig(t)) for t in actual_items.values());missing=list((expected-actual).elements());extra=list((actual-expected).elements());results.append({'target':plan['target'],'expected':sum(expected.values()),'missing':missing,'extra':extra})
lengths=collections.defaultdict(float);vias=0
for t in tracks:
 if isinstance(t,P.PCB_VIA):vias+=1
 if t.GetNetname().startswith('/SDRAM_'):lengths[t.GetNetname()]+=1.465 if isinstance(t,P.PCB_VIA) else P.ToMM(t.GetLength())
report={'main_sha256':hashlib.sha256(main.read_bytes()).hexdigest(),'pattern_results':results,'sdram_lengths_mm':dict(lengths),'sdram_min_mm':min(lengths.values()),'sdram_max_mm':max(lengths.values()),'sdram_spread_mm':max(lengths.values())-min(lengths.values()),'vias':vias,'tracks':len(tracks)-vias,'footprints':len(fs)};(out/'lower-left-pattern-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print([{k:(len(v) if k in ['missing','extra'] else v) for k,v in r.items()} for r in results],flush=True);print('SDRAM spread',report['sdram_spread_mm'],flush=True);assert all(not r['missing'] and not r['extra'] for r in results)
