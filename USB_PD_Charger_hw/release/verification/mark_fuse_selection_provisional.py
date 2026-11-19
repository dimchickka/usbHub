"""Correct fuse approval status: PSU and fault coordination are not selected."""
import csv,json
from pathlib import Path
hw=Path(__file__).resolve().parents[2];root=hw.parent;release=hw/'release';out=release/'verification';bom=release/'assembly/BOM.csv'
with bom.open(encoding='utf-8-sig',newline='') as h:reader=csv.DictReader(h);headers=list(reader.fieldnames);rows=list(reader)
if 'SelectionStatus' not in headers:headers.append('SelectionStatus')
for row in rows:
 row.setdefault('SelectionStatus','')
 if set(x.strip() for x in row['References'].split(','))=={'F1','F2','F3','F4','F5'}:row['SelectionStatus']='PROVISIONAL: PSU, inrush and fault clearing not validated'
with bom.open('w',encoding='utf-8-sig',newline='') as h:writer=csv.DictWriter(h,fieldnames=headers);writer.writeheader();writer.writerows(rows)
path=out/'fuse-selection.json';data=json.loads(path.read_text());data['approval_status']='PROVISIONAL';data['psu_model']=None;data['user_confirmed_psu_not_selected']=True;data['fault_example']={'assumed_psu_current_limit_A':50,'assumed_equal_parallel_inputs':5,'current_per_fuse_A':10,'consequence':'Neither slow nor fast 15A fuses are guaranteed to clear this shared-bus fault.'};data['fast_candidate_for_further_comparison']={'manufacturer':'Bel Fuse','mpn':'0679L9150-05','current_A':15,'voltage_VDC':125,'response':'fast acting','datasheet':'https://www.belfuse.com/media/datasheets/products/circuit-protection/ds-cp-0679l-series.pdf','approval_status':'NOT SELECTED; check inrush, temperature and fault coordination'};path.write_text(json.dumps(data,ensure_ascii=False,indent=2))
note=release/'FUSE_SELECTION.md';text=note.read_text(encoding='utf-8');status='''> **Статус: предварительный, не утверждён для закупки/монтажа.** Пользователь подтвердил, что БП ещё не выбран. Артикул 0680H9150-05 оставлен в схеме как предварительный вариант, а в BOM добавлен SelectionStatus. Окончательно выбрать характеристику и подтвердить номинал можно после выбора БП и проверки пускового тока, нагрева и аварийных режимов.

Если БП при КЗ на общей шине ограничивает суммарный ток, например, до 50 А, при идеальном распределении через каждый из пяти вводов проходит только 10 А. Ни быстрый, ни замедленный предохранитель 15 А не обязан сработать. Общее КЗ должна отключать согласованная защита БП либо электронная защита общей шины; замена slow blow на fast acting сама по себе этого не обеспечивает.

Для сравнения существует **Bel 0679L9150-05**, 15 А / 125 В DC, быстрый, корпус 2410. Это пока не утверждённая замена. [Даташит](https://www.belfuse.com/media/datasheets/products/circuit-protection/ds-cp-0679l-series.pdf). В схему этот альтернативный артикул не вносился.

'''
if '> **Статус: предварительный' not in text:
 pos=text.index('\n')+1;text=text[:pos]+'\n'+status+text[pos:]
note.write_text(text.replace('Выбор артикула закрывает BOM, но не заменяет проверку защиты и испытания на 1 кВт.','Запись артикула в BOM остаётся предварительной до проверки защиты и испытаний.'),encoding='utf-8')
review=release/'FINAL_REVIEW.md';text=review.read_text(encoding='utf-8');lines=text.splitlines();lines=[('- F1–F5: предварительный Bel 0680H9150-05, 15 А, 125 В DC, замедленный. БП ещё не выбран, поэтому номинал и характеристика защиты не утверждены для монтажа; в BOM указан SelectionStatus. Условия и пример КЗ общей шины — в `FUSE_SELECTION.md`.') if line.startswith('- F1–F5:') else line for line in lines];review.write_text('\n'.join(lines)+'\n',encoding='utf-8')
readme=root/'README.md';text=readme.read_text(encoding='utf-8');text=text.replace('F1–F5: Bel 0680H9150-05, 15 А / 125 В DC, замедленные; условия выбора','F1–F5: предварительно Bel 0680H9150-05, 15 А / 125 В DC; до выбора БП и согласования защиты не утверждены для монтажа. Условия выбора');readme.write_text(text,encoding='utf-8')
print('F1-F5 marked PROVISIONAL in BOM and release documentation. PCB and schematic unchanged.')
