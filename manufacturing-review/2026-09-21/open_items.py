"""Controlled, reviewable patches for the authorized open-item corrections.

Only acts in the manufacturing-review project. Does not release the design.
"""
from pathlib import Path
import difflib
import hashlib
import json
import re
import sys
import uuid
import xml.etree.ElementTree as ET
from inspect_open_items import BASE, LIB, blocks
from section_a import read_nets

PROJECT = BASE / 'project'
SOURCE = BASE / 'before-open-items'
CMC_FP = 'Inductor_SMD:L_CommonMode_Wurth_WE-CNSW-1206'
CAP_FP = 'Capacitor_THT:CP_Radial_D10.0mm_P5.00mm'
DIODE_FP = 'Diode_SMD:D_PowerDI-5'
SOURCES = {
    'choke': ('Wurth Elektronik', '744232090', 'https://www.we-online.com/components/products/datasheet/744232090.pdf'),
    'cap': ('Panasonic', 'EEUFR1E102', 'https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1E102'),
    'clamp': ('onsemi', 'BAV99LT1G', 'https://www.onsemi.com/pdf/datasheet/bav99lt1-d.pdf'),
    'catch': ('Diodes Incorporated', 'PDS760-13', 'https://www.diodes.com/datasheet/download/PDS760.pdf'),
}

def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'swafarm-review-open-items/' + name))

def diff(path, old, new):
    if old == new:
        return ''
    if not path.exists():
        return '*** Add File: ' + path.as_posix() + '\n' + '\n'.join('+' + s for s in new.splitlines())
    lines = list(difflib.unified_diff(old.splitlines(), new.splitlines(), n=5))[2:]
    return '*** Update File: ' + path.as_posix() + '\n' + '\n'.join('@@' if l.startswith('@@') else l for l in lines)

def prop(name, value, x=0, y=0, visible=False):
    return f'\t\t(property "{name}" "{value}"\n\t\t\t(at {x} {y} 0)\n' + ('' if visible else '\t\t\t(hide yes)\n') + '\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)'

def source_fields(b, kind):
    manufacturer, mpn, url = SOURCES[kind]
    ds = next(t for t in blocks(b,'property',2) if t.startswith('\t\t(property "Datasheet"'))
    at = re.search(r'\(at ([\d.-]+) ([\d.-]+)',b)
    b = b.replace(ds, prop('Datasheet',url,*at.groups()))
    marker = '\t\t(instances'
    assert marker in b
    return b.replace(marker, '\n'.join([prop('Manufacturer',manufacturer),prop('MPN',mpn),
        prop('Qualification','Reference candidate; load and thermal validation pending' if kind == 'catch' else 'Package and pinout checked; system qualification pending')]) + '\n' + marker)

def rename_cache(b, old, new):
    b = b.replace(f'(symbol "{old}"', f'(symbol "SWAFarm_Review:{new}"',1)
    # Nested graphical unit names do not carry a library nickname.
    base = old.split(':')[-1]
    b = b.replace(f'(symbol "{base}_', f'(symbol "{new}_')
    return b

def pin_names(b, mapping):
    for p in blocks(b,'pin',4):
        n = re.search(r'\(number "([^"]+)"',p)[1]
        if n in mapping:
            changed = re.sub(r'\(name "[^"]*"',lambda m: '(name "' + mapping[n] + '"',p,count=1)
            b = b.replace(p,changed)
    return b

def wire(a,b,name):
    return f'\t(wire\n\t\t(pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]}))\n\t\t(stroke (width 0) (type default))\n\t\t(uuid "{uid(name)}")\n\t)'

def label(name,x,y,key):
    return f'\t(label "{name}"\n\t\t(at {x} {y} 0)\n\t\t(effects (font (size 1.27 1.27)) (justify left bottom))\n\t\t(uuid "{uid(key)}")\n\t)'

def instance(libid, ref, value, fp, x,y,angle,path,pins):
    s = f'\t(symbol\n\t\t(lib_id "{libid}")\n\t\t(at {x} {y} {angle})\n\t\t(unit 1)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(uuid "{uid(ref)}")\n'
    s += '\n'.join([prop('Reference',ref,x+10.16,y-1.27,True),prop('Value',value,x+10.16,y+1.27,True),prop('Footprint',fp,x,y),prop('Datasheet','',x,y)]) + '\n'
    for p in pins:
        s += f'\t\t(pin "{p}" (uuid "{uid(ref+"-pin"+p)}"))\n'
    return s + f'\t\t(instances (project "SWAFarmNodeV1" (path "{path}" (reference "{ref}") (unit 1))))\n\t)'

def schematic_patch():
    result = ['*** Begin Patch']
    library_symbols = []
    for path in sorted(PROJECT.glob('*.kicad_sch')):
        old = path.read_text(encoding='utf-8')
        new = old
        if path.name == 'RS-485.kicad_sch':
            cache = next(b for b in blocks(old,'symbol',2) if b.startswith('\t\t(symbol "Device:Filter_EMI_CommonMode"'))
            corrected = rename_cache(cache,'Device:Filter_EMI_CommonMode','WE_CNSW_744232090')
            for p in blocks(corrected,'pin',4):
                num = re.search(r'\(number "([^"]+)"',p)[1]
                if num in ('3','4'):
                    other = '4' if num == '3' else '3'
                    corrected = corrected.replace(p,p.replace(f'(number "{num}"',f'(number "{other}"').replace(f'(name "{num}"',f'(name "{other}"'))
            new = new.replace(cache,corrected)
            library_symbols.append(corrected)
        if path.name == 'Sensors & LORA.kicad_sch':
            candidates = []
            for cache in blocks(old,'symbol',2):
                if '(number "3"' in cache and '(at -5.08 -5.08 90)' in cache:
                    candidates.append(cache)
            assert len(candidates) == 1, len(candidates)
            cache = candidates[0]
            cache_name = re.search(r'\(symbol "([^"]+)"',cache)[1]
            corrected = rename_cache(cache,cache_name,'BAV99LT1G_Clamp')
            corrected = pin_names(corrected,{'1':'A1','2':'K2','3':'K1/A2'})
            new = new.replace(cache,corrected)
            library_symbols.append(corrected)
        for b in blocks(old,'symbol'):
            reference = re.search(r'\(property "Reference" "([^"]+)"',b)
            if not reference:
                continue
            ref = reference[1]
            replacement = b
            if ref.startswith('CMC_RS485_'):
                replacement = source_fields(b.replace('Device:Filter_EMI_CommonMode','SWAFarm_Review:WE_CNSW_744232090').replace('Inductor_SMD:L_CommonModeChoke_Bourns_SRF1260',CMC_FP),'choke')
            elif ref.startswith('C_VALVEBULK'):
                replacement = source_fields(b.replace('Capacitor_THT:CP_Radial_D12.5mm_P5.00mm',CAP_FP),'cap')
            elif ref.startswith('D_CLHI'):
                replacement = re.sub(r'\n\t\t\(lib_name "[^"]+"\)','',b).replace('(lib_id "Device:D")','(lib_id "SWAFarm_Review:BAV99LT1G_Clamp")')
                replacement = source_fields(replacement,'clamp')
            elif ref == 'J2':
                replacement = b.replace('(in_bom yes)','(in_bom no)').replace('(in_pos_files yes)','(in_pos_files no)')
                for y in ('36.83','39.37','41.91'):
                    replacement += f'\n\t(no_connect\n\t\t(at 39.37 {y})\n\t\t(uuid "{uid("J2-nc-"+y)}")\n\t)'
            if replacement != b:
                new = new.replace(b,replacement)
        if path.name == 'Power.kicad_sch':
            stock = next(b for b in blocks((LIB/'symbols/Device.kicad_sym').read_text(encoding='utf-8'),'symbol') if b.startswith('\t(symbol "D_Schottky"\n'))
            stock = stock.replace('(symbol "D_Schottky"','(symbol "Device:D_Schottky"',1)
            cached = '\n'.join('\t' + l for l in stock.splitlines())
            new = new.replace('\t(lib_symbols\n','\t(lib_symbols\n' + cached + '\n',1)
            sheetpath = '/7f190bf9-c800-4055-b329-7f500a7a2cbd/3cb697fd-09b1-402e-bcee-3805c0c74356'
            d = instance('Device:D_Schottky','D_BUCK1','PDS760-13',DIODE_FP,251.46,83.82,270,sheetpath,['1','2'])
            additions = [source_fields(d,'catch'),label('BUCK_SW',236.22,52.07,'sw-label-original'),label('BUCK_SW',251.46,76.2,'sw-label-diode'),wire((251.46,76.2),(251.46,80.01),'catch-k'),wire((251.46,87.63),(251.46,91.44),'catch-a')]
            gnd = instance('power:GND','#PWR0200','GND','',251.46,91.44,0,sheetpath,['1'])
            gnd = gnd.replace('(in_bom yes)','(in_bom no)').replace('(on_board yes)','(on_board no)').replace('(in_pos_files yes)','(in_pos_files no)')
            gnd = gnd.replace(prop('Reference','#PWR0200',261.62,90.17,True),prop('Reference','#PWR0200',251.46,91.44))
            gnd = gnd.replace(prop('Value','GND',261.62,92.71,True),prop('Value','GND',251.46,96.52,True))
            additions.append(gnd)
            pos = new.rfind('\n)')
            new = new[:pos] + '\n' + '\n'.join(additions) + new[pos:]
        if new != old:
            result.append(diff(path,old,new))
    symtext = '(kicad_symbol_lib\n\t(version 20250114)\n\t(generator "kicad_symbol_editor")\n'
    for s in library_symbols:
        s = s.replace('SWAFarm_Review:','')
        symtext += '\n'.join(l[1:] for l in s.splitlines()) + '\n'
    symtext += ')\n'
    result.append(diff(PROJECT/'SWAFarm_Review.kicad_sym','',symtext))
    table = '(sym_lib_table\n\t(version 7)\n\t(lib (name "SWAFarm_Review") (type "KiCad") (uri "${KIPRJMOD}/SWAFarm_Review.kicad_sym") (options "") (descr "Datasheet-verified pin maps preserving review schematic geometry"))\n)\n'
    assert not (PROJECT/'sym-lib-table').exists()
    result.append(diff(PROJECT/'sym-lib-table','',table))
    print('\n'.join(result + ['*** End Patch']))

def inspect_board():
    import pcbnew
    b = pcbnew.LoadBoard(str(PROJECT/'SWAFarmNodeV1.kicad_pcb'))
    for fp in b.GetFootprints():
        if fp.GetReference() in ('U2','L1','C_BOOT1','C_IN2','C_OUT2','C_VALVEBULK1','CMC_RS485_1'):
            print(fp.GetReference(),fp.GetPosition(),fp.GetOrientationDegrees(),fp.GetPath().AsString(),[(p.GetNumber(),p.GetNetname(),p.GetDrillSize()) for p in fp.Pads()])
    print('API', [n for n in dir(pcbnew) if 'Format' in n or 'PCB_IO_KICAD' in n])

def verify_netlist():
    before = read_nets(SOURCE/'netlist.xml')
    after = read_nets(BASE/'reports/netlist-open-items.xml')
    def translated(pin):
        ref, num = pin
        return (ref, {'3':'4','4':'3'}.get(num,num)) if ref.startswith('CMC_RS485_') else pin
    expected = {frozenset(translated(p) for p in pins) for pins in before.values()}
    actual = {frozenset(p for p in pins if p[0] != 'D_BUCK1') for pins in after.values()}
    assert expected == actual, {'missing':str(expected-actual),'extra':str(actual-expected)}
    sw = next(pins for pins in after.values() if ('U2','9') in pins)
    assert sw == frozenset([('U2','9'),('L1','1'),('C_BOOT1','2'),('D_BUCK1','1')]), sw
    assert ('D_BUCK1','2') in after['GND']
    for i in range(1,7):
        assert (f'D_CLHI{i}','1') in after['GND']
        assert (f'D_CLHI{i}','2') in after['+3V3']
        assert (f'D_CLHI{i}','3') in after[f'SENSOR_CH{i}']
    return after

def pcb_patch():
    import pcbnew
    selected=sys.argv[2] if len(sys.argv)>2 else 'all'
    nets = verify_netlist()
    root = ET.parse(BASE/'reports/netlist-open-items.xml').getroot()
    comps = {c.attrib['ref']: c for c in root.findall('./components/comp')}
    path = PROJECT/'SWAFarmNodeV1.kicad_pcb'
    old = path.read_text(encoding='utf-8')
    b = pcbnew.LoadBoard(str(path))
    assert len(b.GetTracks()) == 0 and b.GetAreaCount() == 0
    old_fps = {f.GetReference(): f for f in b.GetFootprints()}
    replace = {**{f'CMC_RS485_{i}':CMC_FP for i in range(1,3)}, **{f'C_VALVEBULK{i}':CAP_FP for i in range(1,7)},'D_BUCK1':DIODE_FP}
    for ref, identifier in replace.items():
        if selected not in ('all',ref):
            continue
        nick, name = identifier.split(':')
        fp = pcbnew.FootprintLoad(str(LIB/'footprints'/(nick+'.pretty')),name)
        assert fp is not None, identifier
        fp.SetFPID(pcbnew.LIB_ID(nick,name))
        fp.SetReference(ref)
        fp.SetValue(comps[ref].findtext('value'))
        if ref in old_fps:
            original = old_fps[ref]
            fp.SetPosition(original.GetPosition())
            fp.SetOrientation(original.GetOrientation())
            fp.SetPath(original.GetPath())
            fp.SetSheetname(original.GetSheetname())
            fp.SetSheetfile(original.GetSheetfile())
            b.Remove(original)
        else:
            origin = old_fps['U2'].GetPosition()
            fp.SetPosition(pcbnew.VECTOR2I(origin.x+pcbnew.FromMM(8),origin.y+pcbnew.FromMM(9)))
            fp.SetPath(pcbnew.KIID_PATH('/'+uid('D_BUCK1')))
            fp.SetSheetname('Power')
            fp.SetSheetfile('Power.kicad_sch')
        fp.Reference().SetVisible(old_fps[ref].Reference().IsVisible() if ref in old_fps else True)
        b.Add(fp)
    pins = {p: name.replace('/','{slash}') if name.startswith(('Net-(', 'unconnected-(')) else name for name,group in nets.items() for p in group}
    net_by_name = {str(n.GetNetname()):n for n in b.GetNetInfo().NetsByNetcode().values()}
    for name in set(pins.values())-net_by_name.keys():
        n=pcbnew.NETINFO_ITEM(b,name)
        b.Add(n)
        net_by_name[name]=n
    for fp in b.GetFootprints():
        ref=fp.GetReference()
        for pad in fp.Pads():
            key=(ref,pad.GetNumber())
            if key in pins:
                pad.SetNet(net_by_name[pins[key]])
    generated = BASE/'reports/pcb-open-items-candidate.kicad_pcb'
    pcbnew.SaveBoard(str(generated),b)
    candidates = {re.search(r'\(property "Reference" "([^"]+)"',f)[1]:f for f in blocks(generated.read_text(encoding='utf-8'),'footprint')}
    new=old
    for fp in blocks(old,'footprint'):
        ref=re.search(r'\(property "Reference" "([^"]+)"',fp)[1]
        if ref in replace and selected != 'nets':
            if selected not in ('all',ref):
                continue
            replacement=candidates[ref]
            original_uuid=re.search(r'^\t\t\(uuid "([^"]+)"\)',fp,re.M)[1]
            replacement=re.sub(r'^\t\t\(uuid "[^"]+"\)',lambda m:'\t\t(uuid "'+original_uuid+'")',replacement,count=1,flags=re.M)
            new=new.replace(fp,replacement)
        else:
            if selected not in ('all','nets'):
                continue
            updated=fp
            for pad in blocks(fp,'pad',2):
                num=re.search(r'\(pad "([^"]*)"',pad)[1]
                key=(ref,num)
                if key in pins:
                    updated=updated.replace(pad,re.sub(r'\(net "[^"]*"\)',lambda m:'(net "'+pins[key]+'")',pad))
            new=new.replace(fp,updated)
    if selected in ('all','D_BUCK1'):
        assert 'D_BUCK1' not in old_fps
        pos=new.rfind('\n)')
        new=new[:pos]+'\n'+candidates['D_BUCK1']+new[pos:]
    print('*** Begin Patch\n'+diff(path,old,new)+'\n*** End Patch')

def verify():
    import pcbnew
    nets=verify_netlist()
    pins={p:name.replace('/','{slash}') if name.startswith(('Net-(', 'unconnected-(')) else name for name,group in nets.items() for p in group}
    b=pcbnew.LoadBoard(str(PROJECT/'SWAFarmNodeV1.kicad_pcb'))
    footprints={f.GetReference():f for f in b.GetFootprints()}
    assert len(footprints)==len(b.GetFootprints())==185
    count=0
    for fp in footprints.values():
        for pad in fp.Pads():
            key=(fp.GetReference(),pad.GetNumber())
            if key in pins:
                assert pad.GetNetname()==pins[key],key
                count+=1
    original=BASE.parents[1]/'Hardware/SWAFarmNodeV1'
    unchanged=all(hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((original/p.name).read_bytes()).digest() for p in (BASE/'before-section-a').iterdir() if p.suffix in ('.kicad_sch','.kicad_pcb','.kicad_pro'))
    assert unchanged
    prior=pcbnew.LoadBoard(str(SOURCE/'SWAFarmNodeV1.kicad_pcb'))
    for fp in prior.GetFootprints():
        current=footprints[fp.GetReference()]
        assert current.GetPosition()==fp.GetPosition()
        assert current.GetOrientationDegrees()==fp.GetOrientationDegrees(),fp.GetReference()
        assert current.m_Uuid.AsString()==fp.m_Uuid.AsString()
    assert (SOURCE/'SWAFarmNodeV1.kicad_pro').read_bytes()==(PROJECT/'SWAFarmNodeV1.kicad_pro').read_bytes(), 'Rules changed'
    root=ET.parse(BASE/'reports/netlist-open-items.xml').getroot()
    sourcing=[]
    for c in root.findall('./components/comp'):
        fields={f.attrib['name']:f.text or '' for f in c.findall('./fields/field')}
        sourcing.append({'reference':c.attrib['ref'],'value':c.findtext('value'),'footprint':c.findtext('footprint'),
            'MPN':fields.get('MPN',''),'Manufacturer':fields.get('Manufacturer',''),'Qualification':fields.get('Qualification',''),
            'properties':{p.attrib['name']:p.attrib.get('value','') for p in c.findall('property')}})
    (BASE/'reports/sourcing-open-items.json').write_text(json.dumps(sourcing,indent=2),encoding='utf-8')
    populated=[c for c in sourcing if 'exclude_from_bom' not in c['properties']]
    report={'original_sources_unchanged':unchanged,'existing_footprint_positions_orientations_uuids_preserved':True,'project_rules_unchanged':True,'footprints':len(footprints),'pcb_pads_checked':count,'catch_diode_polarity_verified':True,'choke_3_4_pin_swap_verified':True,'all_other_net_partitions_preserved':True,'six_clamp_pinouts_preserved':True,'tracks':len(b.GetTracks()),'zones':b.GetAreaCount(),'netlist_components':len(sourcing),'bom_included_components':len(populated),'components_with_explicit_mpn':sum(bool(c['MPN']) for c in populated),'release_status':'BLOCKED - not manufacturing ready'}
    (BASE/'reports/open-items-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

def metadata_patch():
    root=ET.parse(BASE/'reports/netlist-open-items.xml').getroot()
    comps={c.attrib['ref']:c for c in root.findall('./components/comp')}
    path=PROJECT/'SWAFarmNodeV1.kicad_pcb'
    old=path.read_text(encoding='utf-8')
    new=old
    for fp in blocks(old,'footprint'):
        ref=re.search(r'\(property "Reference" "([^"]+)"',fp)[1]
        if ref not in comps or comps[ref].find("./fields/field[@name='MPN']") is None:
            continue
        c=comps[ref]
        fields={f.attrib['name']:f.text or '' for f in c.findall('./fields/field')}
        fields.update({'Datasheet':c.findtext('datasheet') or '', 'Description':c.findtext('description') or ''})
        changed=fp
        for name in ('Manufacturer','MPN','Qualification','Datasheet','Description'):
            value=fields.get(name,'')
            existing=next((p for p in blocks(changed,'property',2) if p.startswith(f'\t\t(property "{name}" ')),None)
            p=f'\t\t(property "{name}" "{value}"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(hide yes)\n\t\t\t(uuid "{uid(ref+"-field-"+name)}")\n\t\t\t(effects (font (size 1 1) (thickness 0.15)))\n\t\t)'
            if existing:
                changed=changed.replace(existing,p)
            else:
                pos=changed.rfind('\n\t)')
                changed=changed[:pos]+'\n'+p+changed[pos:]
        if ref.startswith('C_VALVEBULK'):
            # Stock 10 mm footprint's generic 3D body is 16 mm high, whereas the
            # sourced capacitor is 20 mm. Omit that misleading generic model.
            for model in blocks(changed,'model',2):
                changed=changed.replace(model,'')
        new=new.replace(fp,changed)
    print('*** Begin Patch\n'+diff(path,old,new)+'\n*** End Patch')

def reference_visibility_patch():
    path=PROJECT/'SWAFarmNodeV1.kicad_pcb'
    old=path.read_text(encoding='utf-8')
    new=old
    prior={re.search(r'\(property "Reference" "([^"]+)"',f)[1]:f for f in blocks((SOURCE/path.name).read_text(encoding='utf-8'),'footprint')}
    for fp in blocks(old,'footprint'):
        ref=re.search(r'\(property "Reference" "([^"]+)"',fp)[1]
        if ref not in ('D_BUCK1',) and not ref.startswith(('C_VALVEBULK','CMC_RS485_')):
            continue
        p=next(p for p in blocks(fp,'property',2) if p.startswith('\t\t(property "Reference" '))
        was_hidden=False
        if ref in prior:
            prev=next(p for p in blocks(prior[ref],'property',2) if p.startswith('\t\t(property "Reference" '))
            was_hidden='(hide yes)' in prev
        changed=p if was_hidden else p.replace('\n\t\t\t(hide yes)','')
        new=new.replace(fp,fp.replace(p,changed))
    print('*** Begin Patch\n'+diff(path,old,new)+'\n*** End Patch')

if __name__ == '__main__':
    {'schematic-patch':schematic_patch,'inspect-board':inspect_board,'pcb-patch':pcb_patch,'metadata-patch':metadata_patch,'reference-visibility-patch':reference_visibility_patch,'verify':verify}[sys.argv[1]]()
