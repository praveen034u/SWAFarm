"""Minimal patches and connectivity validation for approved RS-485 direction change."""
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys
import section_a as a

BASE = Path(__file__).resolve().parent
PROJECT = BASE / 'project'

def patch_schematic():
    output = ['*** Begin Patch']
    for filename in ('MCU.kicad_sch', 'RS-485.kicad_sch'):
        path = PROJECT / filename
        text = path.read_text(encoding='utf-8')
        changes = []
        for name in ('RS485_DE', 'RS485_RE'):
            matches = list(re.finditer(r'^\t\(label "' + name + r'"\n.*?^\t\)', text, re.M | re.S))
            assert len(matches) == 1, (filename, name)
            old = matches[0].group(0)
            if name == 'RS485_RE':
                new = ''
            else:
                new = old.replace('(label ', '(global_label ', 1)
                new = new.replace('\n', '\n\t\t(shape bidirectional)\n', 1)
                new = new.replace('(justify left bottom)', '(justify left)').replace('(justify right bottom)', '(justify right)')
            changes.append((old, new))
        if filename == 'MCU.kicad_sch':
            wires = [m.group(0) for m in re.finditer(r'^\t\(wire\n.*?^\t\)', text, re.M | re.S)
                     if '(xy 132.08 97.79) (xy 148.59 97.79)' in m.group(0)]
            assert len(wires) == 1
            nc = '''\t(no_connect
\t\t(at 132.08 97.79)
\t\t(uuid "ddbed41a-40a1-4289-8891-d17b4e8235cc")
\t)'''
            changes.append((wires[0], nc))
        changes.sort(key=lambda c: text.index(c[0]))
        output.append(a.patch(path, changes))
    print('\n'.join(output + ['*** End Patch']))

def verify_nets():
    before = a.read_nets(BASE / 'before-section-b/netlist.xml')
    after = a.read_nets(BASE / 'reports/netlist-section-b.xml')
    expected = set(before.values())
    group1 = before['/MCU/RS485_DE']
    group2 = before['/RS-485/RS485_DE']
    assert group1 == frozenset([('U_MCU1','34')])
    assert group2 == frozenset([('U_ISO1','3')])
    expected -= {group1, group2}
    expected.add(group1 | group2)
    assert set(after.values()) == expected, 'Unexpected connectivity change'
    assert after['RS485_DE'] == group1 | group2
    reserved = [(name, pins) for name, pins in after.items() if ('U_MCU1','35') in pins]
    assert len(reserved) == 1 and reserved[0][1] == frozenset([('U_MCU1','35')])
    assert reserved[0][0].startswith('unconnected-'), reserved
    assert not any('RS485_RE' in name for name in after)
    mcu = (PROJECT / 'MCU.kicad_sch').read_text(encoding='utf-8')
    assert re.search(r'\(no_connect\s+\(at 132.08 97.79\)', mcu)
    # Confirm the isolated side retains its combined direction pins.
    iso = next(pins for pins in after.values() if ('U_ISO1','14') in pins)
    assert {('U_ISO1','14'), ('U_RS485_TX1','2'), ('U_RS485_TX1','3')}.issubset(iso)
    return before, after, reserved[0][0]

def patch_pcb():
    before, after, reserved = verify_nets()
    mapping = {'/MCU/RS485_DE': 'RS485_DE', '/RS-485/RS485_DE': 'RS485_DE', '/MCU/RS485_RE': reserved}
    path = PROJECT / 'SWAFarmNodeV1.kicad_pcb'
    old = path.read_text(encoding='utf-8')
    new = old
    for initial, final in mapping.items():
        source = f'(net "{initial}")'
        assert new.count(source) == 1, initial
        new = new.replace(source, f'(net "{final}")')
    changes = list(difflib.unified_diff(old.splitlines(), new.splitlines(), n=5))[2:]
    print('*** Begin Patch\n*** Update File: ' + path.as_posix())
    print('\n'.join('@@' if line.startswith('@@') else line for line in changes))
    print('*** End Patch')

def verify():
    import pcbnew
    before, after, reserved = verify_nets()
    old = (BASE / 'before-section-b/SWAFarmNodeV1.kicad_pcb').read_text(encoding='utf-8')
    new = (PROJECT / 'SWAFarmNodeV1.kicad_pcb').read_text(encoding='utf-8')
    expected = old
    for initial, final in {'/MCU/RS485_DE': 'RS485_DE', '/RS-485/RS485_DE': 'RS485_DE', '/MCU/RS485_RE': reserved}.items():
        expected = expected.replace(f'(net "{initial}")', f'(net "{final}")')
    assert expected == new, 'Unexpected PCB edits beyond three pad nets'
    pins = {pin: name.replace('/', '{slash}') if name.startswith(('Net-(', 'unconnected-(')) else name
            for name, group in after.items() for pin in group}
    board = pcbnew.LoadBoard(str(PROJECT / 'SWAFarmNodeV1.kicad_pcb'))
    count = 0
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            key = (fp.GetReference(), pad.GetNumber())
            if key in pins:
                assert pad.GetNetname() == pins[key], (key, pad.GetNetname(), pins[key])
                count += 1
    original = BASE.parents[1] / 'Hardware/SWAFarmNodeV1'
    unchanged = all(hashlib.sha256(p.read_bytes()).digest() == hashlib.sha256((original / p.name).read_bytes()).digest()
                    for p in (BASE / 'before-section-a').iterdir() if p.suffix in ('.kicad_sch','.kicad_pcb','.kicad_pro'))
    assert unchanged
    report = {'io41_to_isolator_inb_verified': True, 'io42_no_connect_verified': True,
              'only_authorized_net_merge': True, 'section_a_connectivity_preserved': True,
              'isolated_side_combined_direction_preserved': True, 'pcb_pads_checked': count,
              'pcb_changes_only_three_pad_net_assignments': True, 'original_sources_unchanged': unchanged}
    (BASE / 'reports/section-b-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    {'schematic-patch': patch_schematic, 'pcb-patch': patch_pcb, 'verify': verify}[sys.argv[1]]()
