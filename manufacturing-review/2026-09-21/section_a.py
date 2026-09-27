"""Prepare minimal patches and verify the explicitly approved section-A edits."""
import collections
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
PROJECT = BASE / 'project'
PAIRS = {
    **{f'SENSOR_CH{i}': [('U_MCU1', str(pin)), (f'D_CLHI{i}', '3')]
       for i, pin in enumerate([39, 38, 4, 5, 6, 7], 1)},
    'VALVE_SPI_CS': [('U_MCU1', '18'), ('U_VALVEEXP1', '11')],
    'VALVE_SPI_MOSI': [('U_MCU1', '19'), ('U_VALVEEXP1', '13')],
    'VALVE_SPI_SCLK': [('U_MCU1', '20'), ('U_VALVEEXP1', '12')],
    'VALVE_SPI_MISO': [('U_MCU1', '21'), ('U_VALVEEXP1', '14')],
    'LORA_UART_TX': [('U_MCU1', '10'), ('U_LORA1', '5')],
    'LORA_UART_RX': [('U_MCU1', '11'), ('U_LORA1', '4')],
    'net_USB_DM': [('U_MCU1', '13'), ('J_USB1', 'A7'), ('J_USB1', 'B7')],
    'net_USB_DP': [('U_MCU1', '14'), ('J_USB1', 'A6'), ('J_USB1', 'B6')],
    'RS485_TX': [('U_MCU1', '8'), ('U_ISO1', '2')],
    'RS485_RX': [('U_MCU1', '9'), ('U_ISO1', '7')],
}

def read_nets(path):
    root = ET.parse(path).getroot()
    return {n.attrib['name']: frozenset((x.attrib['ref'], x.attrib['pin']) for x in n.findall('node'))
            for n in root.findall('./nets/net')}

def patch(path, changes):
    result = [f'*** Update File: {path.as_posix()}']
    for old, new in changes:
        result.append('@@')
        result.extend('-' + line for line in old.splitlines())
        result.extend('+' + line for line in new.splitlines())
    return '\n'.join(result)

def schematic_patch():
    output = ['*** Begin Patch']
    counts = collections.Counter()
    for path in sorted(PROJECT.glob('*.kicad_sch')):
        text = path.read_text(encoding='utf-8')
        changes = []
        for match in re.finditer(r'^\t\(label "([^"]+)"\n.*?^\t\)', text, re.M | re.S):
            name = match.group(1)
            if name not in PAIRS:
                continue
            old = match.group(0)
            new = old.replace('(label ', '(global_label ', 1)
            new = new.replace('\n', '\n\t\t(shape bidirectional)\n', 1)
            # Global-label text is centered vertically within its outline.
            new = new.replace('(justify left bottom)', '(justify left)').replace('(justify right bottom)', '(justify right)')
            changes.append((old, new))
            counts[name] += 1
        if path.name == 'Power.kicad_sch':
            old = '\t\t\t(xy 240.03 107.95) (xy 240.03 110.49)'
            assert text.count(old) == 1
            changes.append((old, old.replace('110.49', '109.22')))
            old = '\t\t\t(xy 238.76 109.22) (xy 246.38 109.22)'
            assert text.count(old) == 1
            changes.append((old, old.replace('(xy 246.38 109.22)', '(xy 240.03 109.22)')))
            marker = '\t\t(uuid "5c1f88f9-a3ca-48d2-9d0f-d922a9eb2a54")\n\t)'
            assert text.count(marker) == 1
            new = '''\t(wire
\t\t(pts (xy 240.03 109.22) (xy 246.38 109.22))
\t\t(stroke (width 0) (type default))
\t\t(uuid "fc814d54-1ac9-43b5-9fe1-b706a87c7a01")
\t)
\t(junction
\t\t(at 240.03 109.22)
\t\t(diameter 0)
\t\t(color 0 0 0 0)
\t\t(uuid "fc814d54-1ac9-43b5-9fe1-b706a87c7a02")
\t)
'''
            changes.append((marker, marker + '\n' + new.rstrip('\n')))
        if changes:
            changes.sort(key=lambda change: text.index(change[0]))
            output.append(patch(path, changes))
    assert counts == collections.Counter({name: 3 if name.startswith('net_USB') else 2 for name in PAIRS}), counts
    output.append('*** End Patch')
    print('\n'.join(output))

def verify_netlist():
    before = read_nets(BASE / 'before-section-a/netlist.xml')
    after = read_nets(BASE / 'reports/netlist-section-a.xml')
    expected = set(before.values())
    checks = {}
    for name, pins in {**PAIRS, '+3V3_TP': [('TP_3V3','1'), ('U_MCU1','2')]}.items():
        groups = {group for group in expected if any(pin in group for pin in pins)}
        assert len(groups) == 2, (name, groups)
        merged = frozenset().union(*groups)
        expected -= groups
        expected.add(merged)
        actual = [(net, group) for net, group in after.items() if pins[0] in group]
        assert len(actual) == 1 and actual[0][1] == merged, (name, actual)
        checks[name] = {'net': actual[0][0], 'pins': sorted(merged)}
    assert expected == set(after.values()), 'Unexpected net partition change'
    assert set().union(*before.values()) == set().union(*after.values()), 'Pins added or lost'
    # Verify that all three direction-control endpoints remain electrically separate.
    directions = [('U_MCU1','34'), ('U_MCU1','35'), ('U_ISO1','3')]
    assert len({n for n, pins in after.items() if any(p in pins for p in directions)}) == 3
    return checks

def pcb_patch():
    verify_netlist()
    nets = read_nets(BASE / 'reports/netlist-section-a.xml')
    pins = {pin: (name.replace('/', '{slash}') if name.startswith(('Net-(', 'unconnected-(')) else name)
            for name, group in nets.items() for pin in group}
    path = PROJECT / 'SWAFarmNodeV1.kicad_pcb'
    text = path.read_text(encoding='utf-8')
    changes = []
    for match in re.finditer(r'^\t\(footprint .*?^\t\)', text, re.M | re.S):
        old = match.group(0)
        ref = re.search(r'\(property "Reference" "([^"]+)"', old).group(1)
        new = old
        for pad_match in reversed(list(re.finditer(r'^\t\t\(pad "([^"]*)".*?^\t\t\)', old, re.M | re.S))):
            key = (ref, pad_match.group(1))
            if key not in pins:
                continue
            pad = pad_match.group(0)
            desired = pins[key]
            current = re.search(r'\(net "([^"]*)"\)', pad)
            assert current, key
            updated = pad[:current.start()] + f'(net "{desired}")' + pad[current.end():]
            new = new[:pad_match.start()] + updated + new[pad_match.end():]
        if new != old:
            # Keep footprint UUID and nearby lines as unique patch context.
            import difflib
            diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(), n=5))
            changes.extend('@@' if line.startswith('@@') else line for line in diff[2:])
    print('*** Begin Patch\n*** Update File: ' + path.as_posix() + '\n' + '\n'.join(changes) + '\n*** End Patch')

def verify():
    import pcbnew
    checks = verify_netlist()
    after = read_nets(BASE / 'reports/netlist-section-a.xml')
    pins = {pin: name.replace('/', '{slash}') if name.startswith(('Net-(', 'unconnected-(')) else name
            for name, group in after.items() for pin in group}
    old = pcbnew.LoadBoard(str(BASE / 'before-section-a/SWAFarmNodeV1.kicad_pcb'))
    new = pcbnew.LoadBoard(str(PROJECT / 'SWAFarmNodeV1.kicad_pcb'))
    def geometry(board):
        return {fp.GetReference(): (str(fp.m_Uuid.AsString()), fp.GetPosition().x, fp.GetPosition().y,
                fp.GetOrientationDegrees(), str(fp.GetFPID().GetLibItemName()),
                [(p.GetNumber(), p.GetPosition().x, p.GetPosition().y, p.GetSize().x, p.GetSize().y)
                 for p in fp.Pads()]) for fp in board.GetFootprints()}
    assert geometry(old) == geometry(new), 'Footprint geometry changed'
    count = 0
    for fp in new.GetFootprints():
        for pad in fp.Pads():
            key = (fp.GetReference(), pad.GetNumber())
            if key in pins:
                assert pad.GetNetname() == pins[key], (key, pad.GetNetname(), pins[key])
                count += 1
    original = BASE.parents[1] / 'Hardware/SWAFarmNodeV1'
    untouched = all(hashlib.sha256(p.read_bytes()).digest() == hashlib.sha256((original / p.name).read_bytes()).digest()
                    for p in (BASE / 'before-section-a').iterdir() if p.suffix in ('.kicad_sch','.kicad_pcb','.kicad_pro'))
    assert untouched, 'Original sources changed'
    report = {'approved_connections_verified': checks, 'all_net_partitions_match_authorized_merges': True,
              'rs485_direction_pins_still_separate': True, 'pcb_pads_checked': count,
              'footprint_geometry_unchanged': True, 'original_sources_unchanged': untouched}
    (BASE / 'reports/section-a-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k,v in report.items() if k != 'approved_connections_verified'}, indent=2))

if __name__ == '__main__':
    {'schematic-patch': schematic_patch, 'pcb-patch': pcb_patch, 'verify': verify}[sys.argv[1]]()
