"""Recheck the canonical KiCad project and fabrication source hash (Python 3)."""
import concurrent.futures,hashlib,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
hw=Path(__file__).resolve().parents[2];root=hw.parent;out=hw/'release/verification';runtime=out/'.runtime';runtime.mkdir(exist_ok=True)
for part in ['config','cache','tmp','roaming','local']:(runtime/part).mkdir(exist_ok=True)
env=os.environ.copy();env.update(KICAD_CONFIG_HOME=str(runtime/'config'),KICAD_CACHE_HOME=str(runtime/'cache'),TEMP=str(runtime/'tmp'),TMP=str(runtime/'tmp'),APPDATA=str(runtime/'roaming'),LOCALAPPDATA=str(runtime/'local'))
cli=os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or 'D:/my_programs/KiCad/bin/kicad-cli.exe';main=hw/'USB_PD_Charger.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();prod=json.loads((out/'production-data.json').read_text());assert sha(main)==prod['source_pcb_sha256'],'PCB changed: regenerate manufacturing outputs'
boards=[p for p in root.rglob('*.kicad_pcb') if '.git' not in p.relative_to(root).parts];assert boards==[main],boards
deps=json.loads((out/'dependencies.json').read_text())
for model in deps['models']:assert Path(model.replace('${KIPRJMOD}',hw.as_posix())).exists(),model
with zipfile.ZipFile(hw/'release/USB_PD_Charger_fabrication.zip') as z:assert z.testzip() is None
commands=[('drc',['pcb','drc','--all-track-errors','--schematic-parity','--severity-all','--format','json','-o',str(out/'drc.json'),str(main)]),('erc',['sch','erc','--severity-all','--format','json','-o',str(out/'erc.json'),str(main.with_suffix('.kicad_sch'))])]
def run(item):
 name,args=item
 jobenv=env.copy()
 for key,part in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:
  directory=runtime/name/part;directory.mkdir(parents=True,exist_ok=True);jobenv[key]=str(directory)
 config=runtime/name/'config/9.0';config.mkdir(parents=True,exist_ok=True)
 # Preinitialize empty global tables to avoid KiCad's first-run library
 # wizard; every library actually used must resolve from the project.
 (config/'sym-lib-table').write_text('(sym_lib_table (version 7))\n',encoding='utf-8')
 (config/'fp-lib-table').write_text('(fp_lib_table (version 7))\n',encoding='utf-8')
 with (runtime/(name+'.log')).open('w') as log:code=subprocess.run([cli]+args,env=jobenv,stdout=log,stderr=subprocess.STDOUT,timeout=240).returncode
 assert code==0,(name,code);return name
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for name in pool.map(run,commands):print('Finished',name,flush=True)
d=json.loads((out/'drc.json').read_text());e=json.loads((out/'erc.json').read_text());ev=[v for sheet in e['sheets'] for v in sheet['violations']];assert not d['violations'] and not d['schematic_parity'] and not d['unconnected_items'] and not ev,(d['violations'],d['schematic_parity'],ev)
assert sha(main)==prod['source_pcb_sha256'];large=[str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts and p.stat().st_size>=100_000_000]
report={'pcb_files_in_workspace':1,'main_pcb_sha256':sha(main),'drc_violations':0,'erc_violations':0,'schematic_parity':0,'unconnected':0,'missing_3d_models':0,'files_at_least_100MB':large,'fabrication_zip_integrity':'passed'};(out/'final-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
# This verifier owns only the temporary directory below its own output path.
assert runtime.resolve().parent==out.resolve() and runtime.name=='.runtime';shutil.rmtree(runtime)
