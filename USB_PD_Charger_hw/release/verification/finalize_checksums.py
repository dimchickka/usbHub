import json,hashlib
from pathlib import Path
hw=Path(__file__).resolve().parents[2];root=hw.parent;release=hw/'release';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();validation=json.loads((release/'verification/final-validation.json').read_text());assert sha(hw/'USB_PD_Charger.kicad_pcb')==validation['main_pcb_sha256'];assert len(list(root.rglob('*.kicad_pcb')))==1
files=[hw/name for name in ['USB_PD_Charger.kicad_pcb','USB_PD_Charger.kicad_sch','dual_port.kicad_sch','SC8815.kicad_sch','USB_PD_Charger.kicad_pro','USB_PD_Charger.kicad_dru','fp-lib-table','sym-lib-table']]
files += [p for p in (hw/'libs').rglob('*') if p.is_file()]
files += [p for folder in ['fabrication','assembly'] for p in (release/folder).rglob('*') if p.is_file()]
files += [release/'USB_PD_Charger_fabrication.zip',release/'FINAL_REVIEW.md',root/'README.md',root/'.gitignore',root/'.gitattributes']
if (release/'FUSE_SELECTION.md').exists():files.append(release/'FUSE_SELECTION.md')
files += [p for p in (root/'documents/Protection').glob('*.pdf')]
if (release/'verification/wide-3v3-comparison.png').exists():files.append(release/'verification/wide-3v3-comparison.png')
entries={p.relative_to(root).as_posix():sha(p) for p in sorted(set(files))};(release/'CHECKSUMS.sha256').write_text(''.join(h+'  '+name+'\n' for name,h in entries.items()),encoding='utf-8');(release/'verification/source-manifest.json').write_text(json.dumps({'source_pcb_sha256':validation['main_pcb_sha256'],'files':entries},indent=2));print('FROZEN',len(entries),'files. One PCB. Hash',validation['main_pcb_sha256'])
