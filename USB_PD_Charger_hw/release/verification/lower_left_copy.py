"""Transfer the latest lower-left template changes; rotate right cells by 180 degrees."""
import os,json,hashlib,collections,sys
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/lower-left';rt.mkdir(parents=True,exist_ok=True)
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:p=rt/n;p.mkdir(exist_ok=True);os.environ[k]=str(p)
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();inspection=json.loads((out/'lower-left-inspection.json').read_text());source_sha=sha(main);assert source_sha==inspection['source_sha256']
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project)
source_fixes=[];held=[]
for u in ['95426efc-1765-4c0d-ac43-cf567ff33828','ffdbee2a-b5a6-4bbd-99f2-0f3d43e89007']:
 t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==u);start=t.GetStart();vs=[v for v in b.GetTracks() if isinstance(v,P.PCB_VIA) and v.GetNetCode()==t.GetNetCode()];v=min(vs,key=lambda v:(v.GetPosition().x-start.x)**2+(v.GetPosition().y-start.y)**2).GetPosition();assert abs(v.x-start.x)<800000 and abs(v.y-start.y)<800000
 x=v.x+(abs(v.y-start.y) if v.x<start.x else -abs(v.y-start.y));junction=P.VECTOR2I(x,start.y);t.SetStart(junction);q=P.PCB_TRACK(b);q.SetNetCode(t.GetNetCode());q.SetLayer(t.GetLayer());q.SetWidth(t.GetWidth());q.SetStart(junction);q.SetEnd(v);b.Add(q);source_fixes.append({'net':t.GetNetname(),'track_uuid':u,'added_uuid':q.m_Uuid.AsString()})
fs=list(b.GetFootprints());refs={f.GetReference():f for f in fs};tracks=list(b.GetTracks());source=refs['DD24'];group=lambda f:f.GetPath().AsString().split('/')[1];role=lambda f:'/'.join(f.GetPath().AsString().split('/')[2:]);src={role(f):f for f in fs if group(f)==group(source)};srcrefs={f.GetReference() for f in src.values()};netrefs=collections.defaultdict(set);padrefs={}
for f in fs:
 for p in f.Pads():netrefs[p.GetNetCode()].add(f.GetReference());padrefs[p.m_Uuid.AsString()]=f.GetReference()
private={n for n,r in netrefs.items() if r and r<=srcrefs};allchanged=list(inspection['deleted'].values())+list(inspection['added'].values())+[m[x] for m in inspection['modified'].values() for x in ['before','after']]
affected={b.FindNet(s[1]).GetNetCode() for s in allchanged if b.FindNet(s[1]) and b.FindNet(s[1]).GetNetCode() in private}
affected=private # Copy coordinated local signal groups together.
spi_names={'/STM3_CS','/STM_SCK','/STM_MISO','/STM_MOSI'}
def inspi(s):return all(280000000<=s[i]<=300000000 for i in [4,6]) and all(448000000<=s[i]<=468000000 for i in [5,7])
def sig(t):
 s=[t.GetClass(),t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
 if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y])
 if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return s
def canonical(s):
 a=(s[4],s[5]);z=(s[6],s[7]);a,z=sorted([a,z]);return tuple(s[:4])+a+z+tuple(s[8:])
original={t.m_Uuid.AsString():sig(t) for t in tracks};placements={f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in fs};zoneoutlines={z.m_Uuid.AsString():z.Outline().Format() for z in b.Zones()}
b.BuildConnectivity();conn=b.GetConnectivity()
def cluster(pad):
 seen={};queue=[pad]
 while queue:
  obj=queue.pop();u=obj.m_Uuid.AsString()
  if u in seen:continue
  seen[u]=obj;queue.extend(t for t in conn.GetConnectedTracks(obj) if t.GetNetCode()==pad.GetNetCode());queue.extend(p for p in conn.GetConnectedPads(obj) if p.GetNetCode()==pad.GetNetCode())
 return seen
global_seeds={u for u,s in inspection['added'].items() if s[1] in {'GND','+3v3','+24v'} and all(260e6<=s[i]<=356e6 for i in [4,6]) and all(426e6<=s[i]<=496e6 for i in [5,7])}
global_seeds|={u for u,m in inspection['modified'].items() if m['after'][1] in {'GND','+3v3','+24v'} and all(260e6<=m['after'][i]<=356e6 for i in [4,6]) and all(426e6<=m['after'][i]<=496e6 for i in [5,7])}
power_objects={};power_pads=[];seen_clusters=set()
for f in src.values():
 for p in f.Pads():
  if p.GetNetname() not in {'GND','+3v3','+24v'}:continue
  cc=cluster(p);ids=frozenset(cc)
  if ids in seen_clusters:continue
  seen_clusters.add(ids);pp=[o for o in cc.values() if o.GetClass()=='PAD'];assert {padrefs[o.m_Uuid.AsString()] for o in pp}<=srcrefs
  power_objects.update({u:o for u,o in cc.items() if o.GetClass() in {'PCB_TRACK','PCB_ARC','PCB_VIA'}})
  power_pads.extend((role(refs[padrefs[o.m_Uuid.AsString()]]),o.GetNumber()) for o in pp)
print('AFFECTED PRIVATE NETS',sorted(b.FindNet(n).GetNetname() for n in affected),'POWER OBJECTS',len(power_objects),flush=True)
removed=[];added=[];plans=[]
for targetref in ['DD4','DD9','DD14','DD19','DD29','DD34','DD39','DD44','DD49']:
 target=refs[targetref];dst={role(f):f for f in fs if group(f)==group(target)};assert set(src)==set(dst);rot=target.GetOrientationDegrees()!=source.GetOrientationDegrees();sgn=-1 if rot else 1;sx,sy=source.GetPosition().x,source.GetPosition().y;tx,ty=target.GetPosition().x,target.GetPosition().y
 def transxy(x,y):return tx+sgn*(x-sx),ty+sgn*(y-sy)
 def trans(v):return P.VECTOR2I(*transxy(v.x,v.y))
 def inverse(s):
  s=list(s)
  for i in [4,6]:s[i]=sx+sgn*(s[i]-tx);s[i+1]=sy+sgn*(s[i+1]-ty)
  return s
 mapping={}
 for r,f in src.items():
  df=dst[r];assert trans(f.GetPosition())==df.GetPosition();assert abs(((df.GetOrientationDegrees()-f.GetOrientationDegrees())%360)-(180 if rot else 0))<1e-8
  dp={p.GetNumber():p for p in df.Pads()}
  for sp in f.Pads():
   sn=sp.GetNetCode();dn=dp[sp.GetNumber()].GetNetCode();assert sn not in mapping or mapping[sn]==dn;mapping[sn]=dn
 def duplicate(t):
  q=t.Duplicate();q.SetNetCode(mapping[t.GetNetCode()])
  if isinstance(q,P.PCB_VIA):q.SetPosition(trans(t.GetPosition()))
  else:
   q.SetStart(trans(t.GetStart()));q.SetEnd(trans(t.GetEnd()))
   if isinstance(q,P.PCB_ARC):q.SetMid(trans(t.GetMid()))
  return q
 targetpower={}
 for r,num in power_pads:
  p=next(p for p in dst[r].Pads() if p.GetNumber()==num);cc=cluster(p);assert {padrefs[o.m_Uuid.AsString()] for o in cc.values() if o.GetClass()=='PAD'}<={f.GetReference() for f in dst.values()}
  targetpower.update({u:o for u,o in cc.items() if o.GetClass() in {'PCB_TRACK','PCB_ARC','PCB_VIA'}})
 st=[t for t in tracks if t.GetNetCode() in affected or t.GetNetname() in spi_names and inspi(sig(t))];st.extend(power_objects.values());st={t.m_Uuid.AsString():t for t in st}.values()
 targetaffected={mapping[n] for n in affected};targetspi={mapping[b.FindNet(n).GetNetCode()] for n in spi_names}
 dt=[t for t in tracks if t.GetNetCode() in targetaffected or t.GetNetCode() in targetspi and inspi(inverse(sig(t)))];dt.extend(targetpower.values());dt={t.m_Uuid.AsString():t for t in dt}.values()
 expected=collections.defaultdict(list)
 for t in st:
  q=duplicate(t);expected[canonical(sig(q))].append(q)
 rr=[];aa=[]
 for t in dt:
  k=canonical(sig(t))
  if expected[k]:expected[k].pop()
  else:rr.append(t)
 for items in expected.values():aa.extend(items)
 for t in rr:b.Remove(t);removed.append(t.m_Uuid.AsString());held.append(t)
 for q in aa:b.Add(q);added.append(q.m_Uuid.AsString())
 plans.append({'target':targetref,'rotated_180':rot,'removed':len(rr),'added':len(aa),'expected_objects':len(list(st))})
print(json.dumps(plans),flush=True)
assert placements=={f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in b.GetFootprints()};assert zoneoutlines=={z.m_Uuid.AsString():z.Outline().Format() for z in b.Zones()}
now={t.m_Uuid.AsString():sig(t) for t in b.GetTracks()};assert all(now[u]==s for u,s in original.items() if u not in removed)
report={'source_sha256':source_sha,'template':['DD24','DD27','DD28'],'source_fixes':source_fixes,'affected_private_nets':sorted(b.FindNet(n).GetNetname() for n in affected),'power_source_uuids':sorted(power_objects),'source_power_pads':power_pads,'plans':plans,'removed_uuids':removed,'added_uuids':added,'all_other_tracks_preserved':True,'placement_preserved':True,'zone_outlines_preserved':True}
(out/'lower-left-copy.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
if '--prepare' in sys.argv:
 for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
 b.BuildConnectivity();print('REFILL',flush=True);filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity();candidate=rt/'candidate.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(candidate),b);report['candidate_sha256']=sha(candidate);(out/'lower-left-copy.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('READY',report['candidate_sha256'],flush=True)
