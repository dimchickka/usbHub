"""Compare and synchronize EVERY pad-connected track/via in repeated right cells."""
import os,json,hashlib,collections,sys,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';rt=out/'.runtime/right-complete';rt.mkdir(parents=True,exist_ok=True)
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:p=rt/n;p.mkdir(exist_ok=True);os.environ[k]=str(p)
p=rt/'config/9.0';p.mkdir(exist_ok=True)
for n in ['sym','fp']:(p/(n+'-lib-table')).write_text('('+n+'_lib_table (version 7))\n')
import pcbnew as P
import wx;wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(main)
if '--verify-only' not in sys.argv:(rt/'before.tmp').write_bytes(main.read_bytes())
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));b=P.LoadBoard(str(main));b.SetProject(project);b.BuildConnectivity();conn=b.GetConnectivity();fs=list(b.GetFootprints());tracks=list(b.GetTracks());refs={f.GetReference():f for f in fs};group=lambda f:f.GetPath().AsString().split('/')[1];role=lambda f:'/'.join(f.GetPath().AsString().split('/')[2:]);source=refs['DD29'];src={role(f):f for f in fs if group(f)==group(source)}
padrefs={p.m_Uuid.AsString():f.GetReference() for f in fs for p in f.Pads()}
def cluster(pad):
 seen={};queue=[pad]
 while queue:
  obj=queue.pop();u=obj.m_Uuid.AsString()
  if u in seen:continue
  seen[u]=obj
  queue.extend(t for t in conn.GetConnectedTracks(obj) if t.GetNetCode()==pad.GetNetCode())
  queue.extend(p for p in conn.GetConnectedPads(obj) if p.GetNetCode()==pad.GetNetCode())
 return seen
def sig(t):
 s=[t.GetClass(),t.GetNetname(),t.GetLayer(),t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
 if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y])
 if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
 return s
def key(t,dy=0,net=None):
 s=sig(t);s[1]=net or s[1];a=(s[4],s[5]+dy);z=(s[6],s[7]+dy);a,z=sorted([a,z]);tail=s[8:]
 if isinstance(t,P.PCB_ARC):tail=[s[8],s[9]+dy]
 return tuple(s[:4])+a+z+tuple(tail)
def branches(cell):
 objects={};external=[];cellrefs={f.GetReference() for f in cell.values()}
 for f in cell.values():
  for p in f.Pads():
   if p.GetNetname() not in {'GND','+3v3','+24v'}:continue
   cc=cluster(p);pp={padrefs[o.m_Uuid.AsString()] for o in cc.values() if o.GetClass()=='PAD'}
   if not pp<=cellrefs:
    external.append({'pad':f.GetReference()+'.'+p.GetNumber(),'net':p.GetNetname(),'external_refs':sorted(pp-cellrefs)});continue
   for u,o in cc.items():
    if o.GetClass() in {'PCB_TRACK','PCB_ARC','PCB_VIA'}:objects[u]=o
 return objects,external
srcobjects,external=branches(src);print('SOURCE GLOBAL BRANCH OBJECTS',len(srcobjects),'EXTERNAL',len(external),flush=True)
original={t.m_Uuid.AsString():sig(t) for t in tracks};removed=[];added=[];held=[];plans=[];details=[]
for ref in ['DD34','DD39','DD44','DD49']:
 target=refs[ref];dy=target.GetPosition().y-source.GetPosition().y;dst={role(f):f for f in fs if group(f)==group(target)}
 assert set(src)==set(dst)
 for r,f in src.items():assert dst[r].GetPosition().x==f.GetPosition().x and dst[r].GetPosition().y==f.GetPosition().y+dy and dst[r].GetOrientationDegrees()==f.GetOrientationDegrees()
 targetobjects,ex=branches(dst);assert not external and not ex,('External power branch; do not blindly copy',external,ex)
 wanted=collections.defaultdict(list)
 for t in srcobjects.values():wanted[key(t,dy)].append(t)
 rr=[];aa=[]
 for t in targetobjects.values():
  k=key(t)
  if wanted[k]:wanted[k].pop()
  else:rr.append(t)
 for items in wanted.values():aa.extend(items)
 plans.append({'target':ref,'dy_mm':P.ToMM(dy),'remove':len(rr),'add':len(aa),'old_objects':len(targetobjects),'expected_objects':len(srcobjects)})
 details.append({'target':ref,'removed':[sig(t) for t in rr],'added':[sig(t) for t in aa]})
 for t in rr:b.Remove(t);removed.append(t.m_Uuid.AsString());held.append(t)
 for t in aa:
  q=t.Duplicate();q.Move(P.VECTOR2I(0,dy));b.Add(q);added.append(q.m_Uuid.AsString())
 # Exact geometric equality: every source global branch object is represented once.
 expected=collections.Counter(key(t,dy) for t in srcobjects.values());actual=collections.Counter(key(t) for t in targetobjects.values() if t not in rr)
 actual.update(key(t,dy) for t in aa);assert expected==actual
print(json.dumps(plans),flush=True)
now={t.m_Uuid.AsString():sig(t) for t in b.GetTracks()};assert all(now[u]==s for u,s in original.items() if u not in removed)
report={'source_sha256':source_sha,'plans':plans,'details':details,'source_global_objects':len(srcobjects),'all_other_track_objects_unchanged':True,'removed_uuids':removed,'added_uuids':added}
report_path=out/('right-row-power-check.json' if '--verify-only' in sys.argv else 'right-row-complete.json')
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
if '--verify-only' in sys.argv:assert not removed and not added,'Power branches still differ'
if '--prepare' in sys.argv:
 for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
 b.BuildConnectivity();print('REFILL',flush=True);filler=P.ZONE_FILLER(b);filler.Fill(b.Zones());b.BuildConnectivity();candidate=rt/'candidate.tmp';P.PCB_IO_KICAD_SEXPR().SaveBoard(str(candidate),b);report['candidate_sha256']=sha(candidate);(out/'right-row-complete.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('READY',report['candidate_sha256'],flush=True)
