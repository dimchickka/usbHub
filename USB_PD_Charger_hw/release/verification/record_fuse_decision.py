"""Record the selected input fuse and explicit integration requirements."""
import csv, json, re
from pathlib import Path
hw=Path(__file__).resolve().parents[2]; rel=hw/'release'; root=hw.parent
p=rel/'verification/fuse-selection.json'; data=json.loads(p.read_text(encoding='utf-8'))
data.update(approval_status='DESIGN_SELECTED_WITH_REQUIREMENTS; prototype qualification pending',
 user_confirmed={'single_24V_PSU_all_five_inputs':True,'may_specify_PSU_requirements':True,'may_select_wires':True},
 integration_requirements={'input_voltage_V':[22.8,25.2],'PSU_continuous_current_A_min':60,
 'PSU_fault_current_A_max':85.1,'PSU_fault_shutdown_s_max':5,'PSU_fault_recovery':'latched off, deliberate restart',
 'PSU_example_not_purchase_selection':'Mean Well RSP-1500-24, 24V 63A',
 'wire':'5 equal red/black pairs, flexible copper H07V2-K 90C, 4mm2; <=0.5m per conductor; ferrules',
 'fuse_ambient_C_max':50,'forced_air_required':True,'normal_current_any_input_A_max':10.5,
 'connect_all_five_with_PSU_off':True,'missing_input':'reduce output power; no 1kW operation',
 'startup':'SC8815 outputs disabled during input charging; verify rise time >=20ms and actual inrush'},
 calculation={'output_W':1000,'assumed_min_converter_efficiency':0.90,'logic_allowance_W':10,
 'worst_input_current_A':(1000/.9+10)/22.8,'balanced_current_A':(1000/.9+10)/22.8/5,
 'engineering_utilization_factor':.75,'conservative_50C_derating_factor':.95,
 'design_fuse_continuous_current_A':15*.75*.95,'input_capacitance_nominal_uF':3127,
 'input_capacitance_engineering_allowance':1.2,'charge_energy_J_at_25_2V':.5*3127e-6*1.2*25.2**2},
 prototype_tests_completed=False)
data['copper_and_placement_changed']='Only ten fuse land sizes and five courtyards changed; tracks, vias and placement preserved.'
data['footprint_unchanged']='Library identifier retained; lands corrected to Bel recommendation 1.96 x 3.15mm, 4.91mm pitch.'
p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
bom=rel/'assembly/BOM.csv'
with bom.open(encoding='utf-8-sig',newline='') as f: reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
for row in rows:
 if row.get('MPN')=='0680H9150-05':row['SelectionStatus']='DESIGN_SELECTED_WITH_REQUIREMENTS; see FUSE_SELECTION.md; prototype tests pending'
with bom.open('w',encoding='utf-8-sig',newline='') as f: writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
note='''# F1–F5: выбор входных предохранителей

Выбран **Bel Fuse 0680H9150-05**, 15 А, 125 В DC, замедленный (Slow Blow), корпус 2410. Требуется 5 шт. Это конкретный проектный выбор для перечисленных ниже условий; испытания прототипа ещё не проведены.

- [Чип и Дип, код 8018734594](https://www.chipdip.ru/product/0680h9150-05-surface-mount-fuses-2410-smd-aec-q200-bel-fuse-8018734594).
- [Даташит Bel](https://www.belfuse.com/media/datasheets/products/circuit-protection/ds-CP-0680H-series.pdf).
- Проверка предложения 18.11.2026: 240 ₽/шт., поставка 10–11 недель. Срок и цену подтвердить при заказе.

## Схема питания и расчёт

Пользователь подтвердил: один БП питает все пять вводов; требования к БП и проводам можно задать проектом. По схеме выходы F1–F5 соединены в общую +24v. Это пять параллельных вводов, а не пять изолированных групп портов.

Максимальная выходная мощность: 20 × 50 = 1000 Вт. Для расчёта приняты КПД преобразователей не ниже 90%, дополнительные 10 Вт на логику и минимальное входное напряжение 22,8 В. Эти величины — требования/расчётные допущения, а не измерения.

Iвх = (1000 / 0,90 + 10) / 22,8 = **49,17 А**; при равном распределении **9,83 А на ввод**. При номинальных 24 В — 46,71 А всего и 9,34 А на ввод.

Для выбора использован консервативный коэффициент температуры 0,95 при 50°C и проектный коэффициент использования 0,75: 15 × 0,95 × 0,75 = **10,69 А**. Рабочее требование — **не более 10,5 А через любой ввод**. Коэффициент 0,75 принят проектом, это не дословное обязательное правило Bel. Номинал 10 А оставляет недостаточный запас для расчётного режима. Равенство токов схема не гарантирует: его проверяют измерением.

## Обязательные условия подключения

1. Один стабилизированный БП 24 В, диапазон на плате 22,8–25,2 В, непрерывный выходной ток не менее 60 А с учётом его температурного снижения мощности. Ток ограничения не выше 85,1 А; при устойчивом КЗ/перегрузке — отключение не позднее 5 с с фиксацией выключенного состояния до намеренного перезапуска. Бесконечный режим стабилизации тока не подходит. Порог и задержка должны быть подтверждены документацией выбранного БП и испытанием.
2. Пример БП с подходящим заявленным поведением — **Mean Well RSP-1500-24**, 24 В / 63 А / 1512 Вт. По даташиту перегрузка 105–135%, ограничение тока с отключением через 5 с и восстановлением после повторного включения. Это пример для согласования защиты, а не оформленная покупка. [Первичный источник](https://www.meanwell.com/Upload/PDF/RSP-1500/RSP-1500-SPEC.PDF).
3. Пять отдельных одинаковых пар от распределения БП к XL4–XL8: гибкая медь **H07V2-K 90°C, 4 мм²**, красный плюс и чёрный минус; каждый провод до 0,5 м, длины пар одинаковы. Обжимные втулочные наконечники под 4 мм². Токовую допустимость конкретного провода проверить для фактической укладки/жгута; это не универсальная таблица допустимых токов. Соединения не делать последовательным шлейфом через клеммы платы.
4. Установленные клеммы **Phoenix Contact 1933613** рассчитаны на 32 А и допускают гибкий провод с наконечником 4 мм². Зачистка 8 мм, затяжка 0,5–0,6 Н·м. [Данные производителя](https://www.phoenixcontact.com/en-us/products/printed-circuit-board-terminal-mkds-5-2-635-bk-z1l-1933613?type=pdf).
5. Принудительный обдув; температура воздуха непосредственно у F1–F5 не выше 50°C. Окончательная конструкция корпуса пока не задана — это требование к её проектированию.
6. Подключать все пять пар при выключенном БП. Работа на 1 кВт с отсутствующим/перегруженным вводом запрещена; требуется снижение общей мощности. Защита/контроль потери ввода в текущей прошивке не подтверждены.

## Пуск и короткое замыкание

Номинальная ёмкость на +24v по netlist — 3127 мкФ. Для оценки принят запас +20%: 3752 мкФ, запасённая энергия при 25,2 В около 1,19 Дж. При линейном нарастании за 20 мс зарядный ток около 4,73 А суммарно, без подключённой выходной нагрузки. Поэтому требуются отключённые SC8815 на время заряда и проверка фактического нарастания/импульса. 100 мс rise time у указанного Mean Well — типовое значение, а не гарантированный минимум. Подключение уже заряженного БП к плате под напряжением этим расчётом не покрывается.

Предохранитель 15 А не отключается мгновенно при превышении 15 А. Bel нормирует при 200% номинала отключение до 120 с; при 100% — выдержку не менее 4 ч. У 0680H заявлена отключающая способность 500 А при 125 В DC и 5000 А при 72 В DC. Импульсный ток от выходных ёмкостей конкретного БП нужно отдельно проверить по I²t/отключающей способности; ограничение установившегося тока БП не ограничивает автоматически этот импульс.

При КЗ общей шины ток БП делится между вводами и может оставаться ниже номинала каждого F1–F5. Поэтому **КЗ общей шины должен отключать БП**; нельзя рассчитывать на сгорание одного из пяти предохранителей. Даже быстрый 15 А предохранитель эту проблему не решает. Замедленная версия выбрана для резервной защиты входной проводки с запасом на импульсы. F1–F5 не заменяют защиту отдельного преобразователя/порта. Допустимость 5-секундного тока для места неисправности не доказана одним выбором предохранителя: нужна оценка энергии аварии и испытания.

## Изменения проекта и оставшаяся проверка

Артикул, номинал и ссылки внесены в схему/BOM. Посадочные площадки F1–F5 исправлены по рекомендации Bel: **1,96 × 3,15 мм**, расстояние центров 4,91 мм; courtyard расширен по Y. Позиции компонентов, дорожки, переходы и контуры полигонов сохранены; заливки пересчитаны. Производственные файлы перевыгружены.

На прототипе проверить: максимальный ток всех пяти вводов, нагрев предохранителей/клемм/меди в установившемся режиме, фактический КПД, пусковой импульс, потерю одного ввода, ограничение и отключение реального БП при КЗ. Высокотоковые испытания Bel проводятся на 3 oz меди шириной 10 мм; наша плата имеет 35 мкм меди и полигоны, поэтому тепловые условия не эквивалентны. Чистый DRC не подтверждает работу на 1 кВт и не заменяет эти испытания.
'''
(rel/'FUSE_SELECTION.md').write_text(note,encoding='utf-8')
p=rel/'FINAL_REVIEW.md'; t=p.read_text(encoding='utf-8');t=re.sub(r'^- F1–F5:.*$', '- F1–F5: выбран Bel 0680H9150-05, 15 А / 125 В DC, замедленный. Все пять вводов обязательны; требования к БП, проводам, охлаждению и испытаниям — в `FUSE_SELECTION.md`. Посадочные площадки исправлены по даташиту; трассировка и размещение сохранены.',t,flags=re.M);p.write_text(t,encoding='utf-8')
p=root/'README.md';t=p.read_text(encoding='utf-8');t=re.sub(r'F1–F5:.*?Условия выбора — в USB_PD_Charger_hw/release/FUSE_SELECTION.md\.', 'F1–F5: выбран Bel 0680H9150-05, 15 А / 125 В DC. Обязательные требования к пяти вводам, БП и испытаниям — в USB_PD_Charger_hw/release/FUSE_SELECTION.md.',t);p.write_text(t,encoding='utf-8')
print('Recorded concrete fuse selection, integration requirements and pending prototype qualification.')
