import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

base = Path(__file__).resolve().parent
root = ET.parse(base / 'reports/netlist.xml').getroot()
selected = []
for net in root.findall('./nets/net'):
    name = net.attrib['name']
    nodes = [dict(n.attrib) for n in net.findall('node')]
    if any(s in name for s in ('VALVE_SPI', 'RS485_TX', 'RS485_RX', 'RS485_DE', 'RS485_RE', 'LORA_UART', 'net_USB_D', 'SENSOR_CH')) or any(n['ref'] in ('U1','U2','U3','Q1','TP_3V3','U_ISODCDC1','D_CLHI1') for n in nodes):
        selected.append({'net': name, 'nodes': nodes})

def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack = [[]]
    for t in tokens:
        if t == '(':
            child = []
            stack[-1].append(child)
            stack.append(child)
        elif t == ')':
            stack.pop()
        else:
            stack[-1].append(t[1:-1] if t.startswith('"') else t)
    return stack[0][0]

def children(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

symbols = []
labels = []
for path in (base / 'project').glob('*.kicad_sch'):
    tree = parse(path.read_text(encoding='utf-8'))
    for sym in children(tree, 'symbol'):
        props = {p[1]: p[2] for p in children(sym, 'property')}
        ref = props.get('Reference','')
        if ref in ('#PWR01','#PWR0167','#PWR070','#PWR0133','#PWR0160','TP_3V3') or ref.startswith('#FLG'):
            symbols.append({'sheet': path.name, 'reference': ref, 'value': props.get('Value'), 'at': children(sym,'at'), 'uuid': children(sym,'uuid')})
    for kind in ('label','global_label','hierarchical_label'):
        for label in children(tree, kind):
            labels.append({'sheet': path.name, 'kind': kind, 'name':label[1], 'at':children(label,'at')})
report = {'nets': selected, 'power_symbols': symbols, 'labels': labels}
(base / 'reports/connectivity-trace.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
for net in selected:
    print(net['net'] + ': ' + ', '.join(n['ref']+'.'+n['pin']+'('+n.get('pinfunction','')+')' for n in net['nodes']))
print(json.dumps(symbols, indent=2))
