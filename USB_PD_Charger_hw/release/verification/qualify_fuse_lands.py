"""Apply Bel 0680H recommended lands to F1-F5; preserve all tracks and placement."""
import os,json,re,hashlib,shutil
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';runtime=out/'.runtime/pads';runtime.mkdir(parents=True,exist_ok=True)
for key,name in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:p=runtime/name;p.mkdir(exist_ok=True);os.environ[key]=str(p)
config=runtime/'config/9.0';config.mkdir(exist_ok=True)
for name in ['sym','fp']:(config/(name+'-lib-table')).write_text('('+name+'_lib_table (version 7))\n')
import pcbnew as P
import wx; wx.DisableAsserts()
main=hw/'USB_PD_Charger.kicad_pcb';lib=hw/'libs/USB_PD_20Ports.pretty/FUSC6125X279N.kicad_mod';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(main);assert source_sha==json.loads((out/'production-data.json').read_text())['source_pcb_sha256']
def spans(text,tag,indent):
 for m in re.finditer(r'^'+'\t'*indent+r'\('+tag+r'(?=\s)',text,re.M):
  start=m.end()-len(tag)-1;depth=0;quoted=False;escaped=False
  for i in range(start,len(text)):
   c=text[i]
   if quoted:
    if escaped:escaped=False
    elif c=='\\':escaped=True
    elif c=='"':quoted=False
   elif c=='"':quoted=True
   elif c=='(':depth+=1
   elif c==')':
    depth-=1
    if depth==0:yield start,i+1;break
def patch(block,indent):
 edits=[];pads=0
 for a,z in spans(block,'pad',indent):
  s=block[a:z];assert '(size 2.15 2.8)' in s;s=s.replace('(size 2.15 2.8)','(size 1.96 3.15)');edits.append((a,z,s));pads+=1
 assert pads==2
 for a,z in spans(block,'fp_line',indent):
  s=block[a:z]
  if '(layer "F.CrtYd")' in s:edits.append((a,z,s.replace(' -1.65)',' -1.85)').replace(' 1.65)',' 1.85)')))
 for a,z,s in sorted(edits,reverse=True):block=block[:a]+s+block[z:]
 return block
text=main.read_text(encoding='utf-8-sig');edits=[]
for a,z in spans(text,'footprint',1):
 block=text[a:z];m=re.search(r'\(property "Reference" "(F[1-5])"',block)
 if m:edits.append((a,z,patch(block,2)))
assert len(edits)==5
for a,z,s in sorted(edits,reverse=True):text=text[:a]+s+text[z:]
temp=runtime/'fuse-land-input.tmp';temp.write_text(text,encoding='utf-8',newline='');newlib=patch(lib.read_text(encoding='utf-8-sig'),1)
manager=P.GetSettingsManager();manager.LoadProject(str(main.with_suffix('.kicad_pro')));project=manager.GetProject(str(main.with_suffix('.kicad_pro')));io=P.PCB_IO_KICAD_SEXPR();old=P.LoadBoard(str(main));b=P.LoadBoard(str(main));old.SetProject(project);b.SetProject(project)
for f in b.GetFootprints():
 if f.GetReference() in ['F1','F2','F3','F4','F5']:
  for p in f.Pads():p.SetSize(P.VECTOR2I(1960000,3150000))
  for g in f.GraphicalItems():
   if g.GetLayer()==P.F_CrtYd:
    for get,setter in [(g.GetStart,g.SetStart),(g.GetEnd,g.SetEnd)]:
     v=get();dy=v.y-f.GetPosition().y
     if abs(dy)==1650000:setter(P.VECTOR2I(v.x,f.GetPosition().y+(1850000 if dy>0 else -1850000)))

def ts(board):
 rows={}
 for t in board.GetTracks():
  s=[t.GetClass(),t.GetNetname(),t.GetLayer(),(t.GetWidth(P.F_Cu) if isinstance(t,P.PCB_VIA) else t.GetWidth()),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
  if isinstance(t,P.PCB_ARC):s.extend([t.GetMid().x,t.GetMid().y])
  if isinstance(t,P.PCB_VIA):s.extend([t.GetDrillValue(),t.TopLayer(),t.BottomLayer()])
  rows[t.m_Uuid.AsString()]=s
 return rows
print("TRACK CHECK",flush=True); assert ts(old)==ts(b); print("TRACKS OK",flush=True)
def placements(board):return {f.GetReference():[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayer()] for f in board.GetFootprints()}
assert placements(old)==placements(b)
def pads(board):return {p.m_Uuid.AsString():[f.GetReference(),p.GetNumber(),p.GetPosition().x,p.GetPosition().y,p.GetNetname(),p.GetSize().x,p.GetSize().y,p.GetDrillSize().x,p.GetDrillSize().y] for f in board.GetFootprints() for p in f.Pads()}
print("PLACEMENT OK",flush=True); aa=pads(old);bb=pads(b);changed=[]
for u,entry in aa.items():
 target=bb[u]
 if entry!=target:
  assert entry[:5]==target[:5] and entry[7:]==target[7:] and entry[0] in ['F1','F2','F3','F4','F5'] and target[5:7]==[1960000,3150000];changed.append([entry[0],entry[1]])
assert len(changed)==10; print("PADS OK",flush=True)
assert {z.m_Uuid.AsString():z.Outline().Format() for z in old.Zones()}=={z.m_Uuid.AsString():z.Outline().Format() for z in b.Zones()}
print("ZONES OK",flush=True)
for z in b.Zones():z.UnFill();z.SetNeedRefill(True)
b.BuildConnectivity(); print("CONNECTIVITY OK",flush=True); filler=P.ZONE_FILLER(b); print("FILL START",flush=True); filler.Fill(b.Zones()); print("FILL OK",flush=True); b.BuildConnectivity();pending=runtime/'fuse-land-result.tmp';io.SaveBoard(str(pending),b);assert sha(main)==source_sha
shutil.copyfile(pending,main);lib.write_text(newlib,encoding='utf-8',newline='')
prod=json.loads((out/'production-data.json').read_text());prod['source_pcb_sha256']=sha(main);(out/'production-data.json').write_text(json.dumps(prod,ensure_ascii=False,indent=2));sel=json.loads((out/'fuse-selection.json').read_text());sel.update(pcb_sha256=sha(main),recommended_lands_applied={'pad_size_mm':[1.96,3.15],'pad_centres_x_mm':[-2.455,2.455],'courtyard_y_mm':[-1.85,1.85],'changed_pads':changed,'tracks_and_placement_unchanged':True});(out/'fuse-selection.json').write_text(json.dumps(sel,ensure_ascii=False,indent=2));audit=json.loads((out/'native-audit.json').read_text());audit['main_sha']=sha(main);audit['fuse_lands_changed_per_manufacturer']=True;(out/'native-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2));print('APPLIED 10 recommended fuse lands; all tracks, vias and component placement preserved',flush=True)
