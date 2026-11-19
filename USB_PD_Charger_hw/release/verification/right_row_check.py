import os,sys,subprocess,json
from pathlib import Path
hw=Path(__file__).resolve().parents[2];out=hw/'release/verification';stage=sys.argv[1];rt=out/'.runtime'/('right-row-'+stage);rt.mkdir(parents=True,exist_ok=True);env=os.environ.copy()
for k,n in [('KICAD_CONFIG_HOME','config'),('KICAD_CACHE_HOME','cache'),('TEMP','tmp'),('TMP','tmp'),('APPDATA','roaming'),('LOCALAPPDATA','local')]:p=rt/n;p.mkdir(exist_ok=True);env[k]=str(p)
p=rt/'config/9.0';p.mkdir(exist_ok=True)
for n in ['fp','sym']:(p/(n+'-lib-table')).write_text('('+n+'_lib_table (version 7))\n')
report=out/('right-row-'+stage+'.drc.json')
with (rt/'cli.log').open('w') as log:r=subprocess.run(['D:/my_programs/KiCad/bin/kicad-cli.exe','pcb','drc','--all-track-errors','--schematic-parity','--severity-all','--format','json','-o',str(report),str(hw/'USB_PD_Charger.kicad_pcb')],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240)
assert r.returncode==0
j=json.loads(report.read_text());print(stage,{k:len(j[k]) for k in ['violations','unconnected_items','schematic_parity']},flush=True)
