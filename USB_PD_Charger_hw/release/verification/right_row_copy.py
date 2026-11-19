"""Copy the user's top-right pair routing by pad identity; no autorouter."""
import os,json,hashlib,collections,sys
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/right-row';rt.mkdir(parents=True,exist_ok=True)
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:p=rt/n;p.mkdir(exist_ok=True);os.environ[k]=str(p)
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';inspect=json.loads((out/'right-row-inspection.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(main)==inspect['source_sha256'],'Source changed; inspect again'
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')))
b=P.LoadBoard(str(main));b.SetProject(project)
# Repair two open ends in the saved template before replicating it.
lookup={t.m_Uuid.AsString():t for t in b.GetTracks()};source_fixes=[]
t=lookup['6d73ff98-36b3-4af9-a080-8d2f4c6848ea'];t.SetEnd(P.VECTOR2I(422450532,150129468))
q=P.PCB_TRACK(b);q.SetLayer(t.GetLayer());q.SetNetCode(t.GetNetCode());q.SetWidth(t.GetWidth());q.SetStart(t.GetEnd());q.SetEnd(P.VECTOR2I(422450532,149585533));b.Add(q)
source_fixes.append('SCL2: extend front track to existing via with 45-degree corner')
t=lookup['d45bdbed-0320-494c-b301-0a8f8cd3c2ed'];t.SetStart(P.VECTOR2I(418219341,150320000))
q=P.PCB_TRACK(b);q.SetLayer(t.GetLayer());q.SetNetCode(t.GetNetCode());q.SetWidth(t.GetWidth());q.SetStart(t.GetStart());q.SetEnd(P.VECTOR2I(418239670,150340329));b.Add(q)
source_fixes.append('COMP: extend back track to existing via')
for u in ['82abbfec-699a-42be-b7c1-de97d9a32361','cea26013-0abd-4bc8-9837-86e532760f39']:lookup[u].SetWidth(150000)
source_fixes.append('ACIN: 0.15mm escape on two short segments for required pad clearance')
tracks=list(b.GetTracks());fs=list(b.GetFootprints());refs={f.GetReference():f for f in fs};source=refs['DD29'];group=lambda f:f.GetPath().AsString().split('/')[1];role=lambda f:'/'.join(f.GetPath().AsString().split('/')[2:]);src={role(f):f for f in fs if group(f)==group(source)}
netpads=collections.defaultdict(set)
for f in fs:
 for p in f.Pads():netpads[p.GetNetCode()].add(f.GetReference())
source_refs={f.GetReference() for f in src.values()};private={n for n,rr in netpads.items() if rr and rr<=source_refs};globals_names={'GND','+3v3','+24v'}
assert all(b.FindNet(n).GetNetname() not in globals_names for n in private)
def sig(t):
 s=[t.GetClass(),t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
 if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y])
 if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return s
def key_s(s,dy=0,net=None):
 s=list(s);s[1]=s[1] if net is None else net
 s[5]+=dy;s[7]+=dy
 if s[0]=='PCB_ARC':s[9]+=dy
 # End-point order is irrelevant. Round only for matching old translated geometry (<0.1 um).
 a=(round(s[4]/100),round(s[5]/100));z=(round(s[6]/100),round(s[7]/100));a,z=sorted([a,z]);tail=s[8:]
 if s[0]=='PCB_ARC':tail=[round(s[8]/100),round(s[9]/100)]
 return tuple(s[:4])+a+z+tuple(tail)
def key(t):return key_s(sig(t))
def duplicate(t,dy,net):
 q=t.Duplicate();q.SetNetCode(net);q.Move(P.VECTOR2I(0,dy));return q
original={t.m_Uuid.AsString():sig(t) for t in tracks};placements={f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in fs};zones={z.m_Uuid.AsString():z.Outline().Format() for z in b.Zones()}
removed=[];held=[];added=[];plans=[]
current_by_uuid={t.m_Uuid.AsString():t for t in tracks}
old_delta=dict(inspect['deleted']);new_delta=dict(inspect['added'])
for u,m in inspect['modified'].items():old_delta[u]=m['before'];new_delta[u]=m['after']
def in_source_power(s):
 power=s[1] in {'+3v3','+24v'} and all(390e6<=s[i]<=480e6 for i in [4,6]) and all(139e6<=s[i]<=205e6 for i in [5,7])
 spi=s[1] in {'/STM8_CS','/STM_MOSI','/STM_MISO','/STM_SCK'} and all(440e6<=s[i]<=480e6 for i in [4,6]) and all(170e6<=s[i]<=190e6 for i in [5,7])
 return power or spi
old_power=[s for s in old_delta.values() if in_source_power(s)];new_power=[(u,s) for u,s in new_delta.items() if in_source_power(s)]
# Cancel geometrically unchanged objects recreated by the editor.
for s in old_power[:]:
 match=next(((u,v) for u,v in new_power if key_s(v)==key_s(s)),None)
 if match:old_power.remove(s);new_power.remove(match)
def remove(t):
 u=t.m_Uuid.AsString();assert u not in removed;b.Remove(t);removed.append(u);held.append(t)
def add(q):b.Add(q);added.append(q.m_Uuid.AsString())
for targetref in ['DD34','DD39','DD44','DD49']:
 target=refs[targetref];dy=target.GetPosition().y-source.GetPosition().y;dst={role(f):f for f in fs if group(f)==group(target)};mapping={}
 assert set(src)==set(dst)
 for r,sf in src.items():
  df=dst[r];assert df.GetPosition().x==sf.GetPosition().x and df.GetPosition().y==sf.GetPosition().y+dy and df.GetOrientationDegrees()==sf.GetOrientationDegrees()
  dp=collections.defaultdict(list)
  for p in df.Pads():dp[p.GetNumber()].append(p)
  for sp in sf.Pads():
   pp=dp[sp.GetNumber()];codes={p.GetNetCode() for p in pp};assert len(codes)==1;dn=next(iter(codes));sn=sp.GetNetCode()
   assert sn not in mapping or mapping[sn]==dn;mapping[sn]=dn
 for n in private:assert netpads[mapping[n]]<={f.GetReference() for f in dst.values()}
 wanted=collections.defaultdict(list)
 for t in tracks:
  if t.GetNetCode() in private:
   q=duplicate(t,dy,mapping[t.GetNetCode()]);wanted[key(q)].append(q)
 targetcodes={mapping[n] for n in private};removed_start=len(removed);added_start=len(added)
 for t in tracks:
  if t.GetNetCode() not in targetcodes:continue
  k=key(t)
  if wanted[k]:wanted[k].pop()
  else:remove(t)
 for items in wanted.values():
  for q in items:add(q)
 # Apply only the user's local power fanout edits, leaving plane stitching untouched.
 bykey=collections.defaultdict(list)
 for t in tracks:
  if t.GetNetCode() not in private:bykey[key(t)].append(t)
 missing=[];power_remove=[]
 for s in old_power:
  targetnet=b.FindNet(mapping[b.FindNet(s[1]).GetNetCode()]).GetNetname()
  matches=bykey[key_s(s,dy,targetnet)]
  if matches:power_remove.append(matches.pop())
  else:missing.append(s)
 assert not missing,('Power edit does not match target',targetref,missing)
 for t in power_remove:remove(t)
 for u,s in new_power:
  t=current_by_uuid[u];add(duplicate(t,dy,mapping[t.GetNetCode()]))
 # This GND feeder has a different old via location in the top cell.
 # Copy its complete pad-to-via branch to clear the newly aligned SDA2 escape.
 def ground_branch(t,offset):
  s=sig(t);return s[1]=='GND' and all(423200000<=s[i]<=424300000 for i in [4,6]) and all(145200000<=s[i]-offset<=147200000 for i in [5,7])
 gsrc=[t for t in tracks if ground_branch(t,0)];gdst=[t for t in tracks if ground_branch(t,dy)]
 assert len(gsrc)==3 and len(gdst)==2,(targetref,len(gsrc),len(gdst))
 for t in gdst:remove(t)
 for t in gsrc:add(duplicate(t,dy,t.GetNetCode()))
 plans.append({'target':targetref,'dy_mm':P.ToMM(dy),'removed':len(removed)-removed_start,'added':len(added)-added_start,'power_removed':len(power_remove),'power_added':len(new_power)})
assert placements=={f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in b.GetFootprints()}
assert zones=={z.m_Uuid.AsString():z.Outline().Format() for z in b.Zones()}
now={t.m_Uuid.AsString():sig(t) for t in b.GetTracks()};assert all(now[u]==s for u,s in original.items() if u not in removed)
assert set(now)-set(original)==set(added)
report={'source_sha256':inspect['source_sha256'],'source_pair':['DD29','DD32','DD33'],'source_fixes':source_fixes,'plans':plans,'removed_uuids':removed,'added_uuids':added,'placement_unchanged':True,'zone_outlines_unchanged':True,'all_other_track_objects_unchanged':True,'no_autorouter':True}
(out/'right-row-copy.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(plans),flush=True)
if '--prepare' in sys.argv:
 for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
 b.BuildConnectivity();print('REFILL',flush=True);filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity()
 pending=rt/'candidate.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(pending),b)
 report['candidate_sha256']=sha(pending);(out/'right-row-copy.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('CANDIDATE READY',report['candidate_sha256'],flush=True)
