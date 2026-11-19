"""Record the selected input fuses without changing copper or symbol placement."""
import re,json,hashlib,os,csv,shutil,xml.etree.ElementTree as ET
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';root=hw.parent;main=hw/'USB_PD_Charger.kicad_pcb';sch=hw/'USB_PD_Charger.kicad_sch';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();manifest=json.loads((out/'source-manifest.json').read_text())['files']
for p in [main,sch]:assert sha(p)==manifest[p.relative_to(root).as_posix()],('Source changed',p)
MPN='0680H9150-05';DATASHEET='https://www.belfuse.com/media/datasheets/products/circuit-protection/ds-CP-0680H-series.pdf';URL='https://www.chipdip.ru/product/0680h9150-05-surface-mount-fuses-2410-smd-aec-q200-bel-fuse-8018734594'
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
def prop(block,key):
 m=re.search(r'\(property '+re.escape(json.dumps(key))+r' ("(?:[^"\\]|\\.)*")',block);return json.loads(m[1]) if m else None
changes={};texts={}
for p,tag in [(main,'footprint'),(sch,'symbol')]:
 text=p.read_text(encoding='utf-8-sig');edits=[];refs=[]
 for a,z in spans(text,tag,1):
  block=text[a:z];ref=prop(block,'Reference')
  if ref not in ['F1','F2','F3','F4','F5']:continue
  assert prop(block,'Value')=='Fuse',(ref,prop(block,'Value'));oldblock=block
  block,n=re.subn(r'(\(property "Value" )"Fuse"',r'\1"15A"',block,count=1);assert n==1
  block,n=re.subn(r'(\(property "Datasheet" )"(?:[^"\\]|\\.)*"',lambda m:m[1]+json.dumps(DATASHEET),block,count=1);assert n==1
  if tag=='symbol':
   at=re.search(r'\(at ([^ )]+) ([^ )]+)',block);x,y=at.groups();fields={'Manufacturer':'Bel Fuse','MPN':MPN,'VoltageRating':'125VDC','Characteristic':'Time Delay / Slow Blow','Supplier':'CHIPDIP','SupplierPartNumber':'8018734594','SupplierURL':URL};extra=''
   for name,value in fields.items():extra+='\n\t\t(property '+json.dumps(name)+' '+json.dumps(value)+' (at '+x+' '+y+' 0) (effects (font (size 1.27 1.27)) (hide yes)))'
   pos=block.find('\n\t\t(pin ');assert pos>0;block=block[:pos]+extra+'\n'+block[pos:]
  else:assert [oldblock[a:z] for a,z in spans(oldblock,'pad',2)]==[block[a:z] for a,z in spans(block,'pad',2)]
  edits.append((a,z,block));refs.append(ref)
 assert sorted(refs)==['F1','F2','F3','F4','F5'];outside=text
 for a,z,block in sorted(edits,reverse=True):text=text[:a]+block+text[z:]
 texts[p]=text;changes[p.name]=refs
before_nodes={(x.get('ref'),x.get('pin')):n.get('name') for n in ET.parse(out/'netlist.xml').getroot().find('nets') for x in n.findall('node')}
for p,text in texts.items():
 pending=p.with_name(p.name+'.fuse-pending');pending.write_text(text,encoding='utf-8',newline='')
 try:os.replace(pending,p)
 except PermissionError:
  assert sha(p)==manifest[p.relative_to(root).as_posix()],'Source changed while publishing'
  shutil.copyfile(pending,p);pending.unlink()
prod=json.loads((out/'production-data.json').read_text());prod['source_pcb_sha256']=sha(main);prod['generic_bom_entries']=[];prod['selected_fuses']={'references':['F1','F2','F3','F4','F5'],'manufacturer':'Bel Fuse','mpn':MPN,'current_A':15,'voltage_VDC':125,'characteristic':'slow blow','case':'2410','supplier_url':URL};(out/'production-data.json').write_text(json.dumps(prod,ensure_ascii=False,indent=2))
audit=json.loads((out/'native-audit.json').read_text());audit.update(main_sha=sha(main),schematic_sha=sha(sch));(out/'native-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
with (hw/'release/assembly/BOM.csv').open(encoding='utf-8-sig',newline='') as h:rows=list(csv.DictReader(h))
headers=list(rows[0])+['Manufacturer','MPN','VoltageRating','Characteristic','SupplierURL']
for row in rows:
 for key in headers:row.setdefault(key,'')
 if row['Value']=='Fuse':
  assert set(s.strip() for s in row['References'].split(','))=={'F1','F2','F3','F4','F5'};row.update(Value='15A',Manufacturer='Bel Fuse',MPN=MPN,VoltageRating='125VDC',Characteristic='Time Delay / Slow Blow',SupplierURL=URL)
with (hw/'release/assembly/BOM.csv').open('w',encoding='utf-8-sig',newline='') as h:writer=csv.DictWriter(h,fieldnames=headers);writer.writeheader();writer.writerows(rows)
report={'selected':prod['selected_fuses'],'price_RUB_each_checked_2026_11_18':240,'supplier_lead_time_weeks':[10,11],'input_topology':'Five fused input connectors XL4-XL8 feed the same +24v bus; these are not five isolated groups of USB ports.','rated_output_W':1000,'assumed_efficiency_range':[.90,.95],'total_input_current_A_range':[1000/(24*.95),1000/(24*.90)],'balanced_current_per_input_A_range':[1000/(24*.95*5),1000/(24*.90*5)],'copper_and_placement_changed':False,'before_net_signature':hashlib.sha256(json.dumps(sorted((list(k),v) for k,v in before_nodes.items())).encode()).hexdigest(),'pcb_sha256':sha(main),'schematic_sha256':sha(sch),'footprint_unchanged':'USB_PD_20Ports:FUSC6125X279N','qualification_required':['Measure current sharing through all five input leads at full load; equal current is not guaranteed by the schematic.','Confirm temperature derating and actual fuse/PCB heating. Bel high-current qualification uses 3 oz copper, 10mm traces; this PCB has 35um copper and planes.','Coordinate clearing with actual PSU short-circuit response; five parallel fuses do not constitute a guaranteed 75A main fuse.'],'datasheet':DATASHEET};(out/'fuse-selection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('RECORDED',MPN,'15A on F1-F5; copper and pads unchanged')
