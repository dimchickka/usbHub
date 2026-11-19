import os,sys,json,subprocess,hashlib,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
hw=Path(__file__).resolve().parents[2];root=hw.parent;rel=hw/'release';out=rel/'verification';runtime=out/'.runtime/refresh';runtime.mkdir(parents=True,exist_ok=True);env=os.environ.copy()
for key,part in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:
 p=runtime/part;p.mkdir(exist_ok=True);env[key]=str(p)
config=runtime/'config/9.0';config.mkdir(exist_ok=True)
for table in ['sym','fp']:(config/(table+'-lib-table')).write_text('('+table+'_lib_table (version 7))\n',encoding='utf-8')
cli=os.environ.get('KICAD_CLI','D:/my_programs/KiCad/bin/kicad-cli.exe');main=hw/'USB_PD_Charger.kicad_pcb';fab=rel/'fabrication';assembly=rel/'assembly'
commands=[['pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--subtract-soldermask','-o',str(fab),str(main)],['pcb','export','drill','--format','excellon','--excellon-units','mm','--excellon-separate-th','--drill-origin','absolute','--excellon-oval-format','route','-o',str(fab),str(main)],['pcb','export','ipcd356','-o',str(fab/'USB_PD_Charger.ipc'),str(main)],['pcb','export','pos','--format','csv','--units','mm','--exclude-dnp','-o',str(assembly/'positions.csv'),str(main)],['pcb','export','gerbers','--layers','F.Paste','-o',str(assembly),str(main)],['sch','export','netlist','--format','kicadxml','-o',str(out/'netlist.xml'),str(main.with_suffix('.kicad_sch'))]]
with (runtime/'export.log').open('w') as log:
 for args in commands:
  result=subprocess.run([cli]+args,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180);assert result.returncode==0,args;print('EXPORTED',' '.join(args[:3]),flush=True)
selection=json.loads((out/'fuse-selection.json').read_text());netlist=ET.parse(out/'netlist.xml').getroot();nodes={(x.get('ref'),x.get('pin')):n.get('name') for n in netlist.find('nets') for x in n.findall('node')};signature=hashlib.sha256(json.dumps(sorted((list(k),v) for k,v in nodes.items())).encode()).hexdigest();assert signature==selection['before_net_signature'],'Electrical nets changed'
for c in netlist.find('components'):
 if c.get('ref') in ['F1','F2','F3','F4','F5']:
  assert c.findtext('value')=='15A';assert c.find("fields/field[@name='MPN']").text=='0680H9150-05'
review=rel/'FINAL_REVIEW.md';t=review.read_text(encoding='utf-8');t=__import__('re').sub(r'SHA256 платы: `[0-9a-f]{64}`','SHA256 платы: `'+selection['pcb_sha256']+'`',t);lines=t.splitlines();lines=[('- F1–F5: выбран Bel 0680H9150-05, 15 А, 125 В DC, замедленный, корпус 2410. Артикул внесён в схему и BOM. Условия подключения пяти вводов и обязательные проверки нагрева/КЗ описаны в `FUSE_SELECTION.md`.') if line.startswith('- F1–F5:') else line for line in lines];review.write_text('\n'.join(lines)+'\n',encoding='utf-8')
readme=root/'README.md';t=readme.read_text(encoding='utf-8').replace('Перед монтажом уточнить номиналы F1–F5 (в BOM пока Fuse).','F1–F5: Bel 0680H9150-05, 15 А / 125 В DC, замедленные; условия выбора — в release/FUSE_SELECTION.md.');readme.write_text(t,encoding='utf-8')
# Engineering decision is maintained in FUSE_SELECTION.md, not regenerated from export.
with zipfile.ZipFile(rel/'USB_PD_Charger_fabrication.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(fab.iterdir()):
  if p.is_file():z.write(p,p.name)
print('FUSE RELEASE REFRESHED; electrical nets unchanged',flush=True)
