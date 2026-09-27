"""Approved input-protection change. Design edits are emitted as apply_patch patches."""
import sys, re, json, os, hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
import relay_revision as r

BASE, PROJECT, LIB = r.BASE, r.PROJECT, r.LIB
SNAP = BASE / 'before-input-protection'
INPUT_REFS = {'J1','J_OUT1','Q1','R_gate1','U1','F1','F2','D1','C_IN1','C_OUT1','R_UVLO1','R_UVLO2','R_OVP1','R_OVP2','R_SHDN1','R_ILIM1','R_IMON1','R_FLT1','C_DVDT1','TP_FLT1','TP_IMON1','TP_12V_SW1','TP_GND1','TP_VALVE_PWR1'}

def schematic():
    s = r.Sheet('Power.kicad_sch')
    s.old=(SNAP/'project/Power.kicad_sch').read_text(encoding='utf-8')
    # Rebuild only the input area; retain USB, modules, indicator and excluded J2.
    # J2 and its three NC markers are relocated without changing their properties.
    preserved=[]
    for b in r.direct_blocks(s.old):
        kind=b[1:].split()[0]
        if kind not in ('symbol','wire','junction','no_connect','label','global_label','text'): continue
        coords=re.findall(r'\((?:at|xy) ([\d.-]+) ([\d.-]+)',b)
        if not coords: continue
        x,y=map(float,coords[0])
        ref=re.search(r'\(property "Reference" "([^"]+)"',b)
        is_j2=ref and ref[1]=='J2'
        is_j2_nc=kind=='no_connect' and x==39.37 and y in (36.83,39.37,41.91)
        if is_j2 or is_j2_nc:
            b=re.sub(r'\(at ([\d.-]+) ([\d.-]+)',lambda m:f'(at {float(m[1])+320.04:.4f} {float(m[2])+180.34:.4f}',b)
            preserved.append(b); continue
        # USB's VBUS testpoint is at y=149.86. The remaining USB circuitry is below it.
        if x>=169 or (x>=112 and y>=148): preserved.append(b)
        elif y>=150: raise AssertionError(('unexpected input boundary',b[:200]))
    libinput='Power_Management:TPS26600PWP'
    cached=next(b for b in r.blocks(s.old,'symbol',2) if b.startswith('\t\t(symbol "'+libinput+'"'))
    source='\n'.join(l[1:] for l in cached.splitlines())
    oldxml=ET.parse(SNAP/'netlist.xml').getroot()
    comps={c.attrib['ref']:c for c in oldxml.findall('./components/comp')}
    fp=lambda ref:comps[ref].findtext('footprint')
    conn='Connector_Phoenix_MSTB:PhoenixContact_MSTBVA_2,5_2-G-5,08_1x02_P5.08mm_Vertical'
    cds='https://www.phoenixcontact.com/en-in/products/pcb-header-mstbva-25-2-g-508-1755736'
    s.add('Connector_Generic:Conn_01x02','J1','12V IN: + / GND',conn,32,30,{'1':'DC_IN_RAW_P','2':'GND'},'Phoenix Contact','1755736',cds)
    s.add('Connector_Generic:Conn_01x02','J_OUT1','AUX OUT: + / GND',conn,145,30,{'1':'12V_SW','2':'GND'},'Phoenix Contact','1755736',cds)
    ef={'1':'VIN_12V','2':'VIN_12V','3':'EF_UVLO','4':None,'5':'EF_OVP','6':'EF_RTN','7':'EF_SHDN','8':'EF_RTN','9':'GND','10':'EF_IMON','11':'EF_ILIM','12':'EF_DVDT','13':None,'14':'EF_FLT_N','15':'12V_SW','16':'12V_SW','17':'EF_RTN'}
    s.add(libinput,'U1','TPS26600PWP',fp('U1'),85,65,ef,'Texas Instruments','TPS26600PWP','https://www.ti.com/lit/ds/symlink/tps2660.pdf',source)
    # Remove duplicate wires/labels for stacked package pins, preserving electrical identity.
    unique=[]; seen=set()
    for b in s.items:
        k=re.sub(r'\(uuid "[^"]+"\)','',b)
        if k in seen: continue
        seen.add(k); unique.append(b)
    s.items=unique
    fds='https://www.littelfuse.com/assetdocs/fuse-451-and-453-datasheet?assetguid=533cd5cc-956c-4243-867f-6ab5a62f6ba1'
    s.add('Device:Fuse','F1','2A fast / 125V','Fuse:Fuse_Littelfuse-NANO2-451_453',25,115,{'1':'DC_IN_RAW_P','2':'VIN_12V'},'Littelfuse','0451002.MRL',fds)
    s.add('Device:Fuse','F2','1A fast / 125V','Fuse:Fuse_Littelfuse-NANO2-451_453',145,115,{'1':'12V_SW','2':'+12V'},'Littelfuse','0451001.MRL',fds)
    s.add('Device:D_TVS_Filled','D1','SMBJ18CA',fp('D1'),55,115,{'1':'VIN_12V','2':'GND'},'Littelfuse','SMBJ18CA','https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet?assetguid=ba555e99-a12d-4f72-a0b6-86b06c67171e')
    s.add('Device:C','C_IN1','10uF 63V X7R','Capacitor_SMD:C_1210_3225Metric',85,115,{'1':'VIN_12V','2':'GND'},'Murata','GRM32ER71J106KA12L','https://www.murata.com/-/media/webrenewal/tool/library/common-pdf/dynamic-model/component-list-d-mlcc-2504.ashx?cvid=20250523010405000000&la=en')
    s.add('Device:C','C_OUT1','10uF 25V',fp('C_OUT1'),115,115,{'1':'12V_SW','2':'GND'})
    values=[('R_UVLO1','64.9k','VIN_12V','EF_UVLO'),('R_UVLO2','10k','EF_UVLO','EF_RTN'),('R_OVP1','124k','VIN_12V','EF_OVP'),('R_OVP2','10k','EF_OVP','EF_RTN'),('R_SHDN1','100k','VIN_12V','EF_SHDN'),('R_ILIM1','8.06k 1%','EF_ILIM','EF_RTN'),('R_IMON1','10k','EF_IMON','EF_RTN'),('R_FLT1','10k','12V_SW','EF_FLT_N')]
    for i,(ref,value,a,b) in enumerate(values):
        ilim=ref=='R_ILIM1'
        s.add('Device:R',ref,value,'Resistor_SMD:R_0603_1608Metric' if ilim else fp(ref),25+35*i,235,{'1':a,'2':b},'YAGEO' if ilim else '', 'RC0603FR-078K06L' if ilim else '', 'https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-078K06L' if ilim else '')
    s.add('Device:C','C_DVDT1','100nF 50V X7R',fp('C_DVDT1'),305,235,{'1':'EF_DVDT','2':'EF_RTN'})
    for ref,net,x,y in [('TP_GND1','GND',30,75),('TP_12V_SW1','12V_SW',115,30),('TP_VALVE_PWR1','+12V',145,75),('TP_FLT1','EF_FLT_N',315,95),('TP_IMON1','EF_IMON',355,95)]:
        s.add('Connector:TestPoint',ref,net,'TestPoint:TestPoint_Pad_D2.0mm',x,y,{'1':net})
    for i,(net,x,y) in enumerate([('VIN_12V',25,160),('GND',55,160),('+12V',85,160)]):
        s.add('power:PWR_FLAG',f'#FLG_INPUT{i+1}','PWR_FLAG','',x,y,{'1':net})
    s.text('12 VDC INPUT PROTECTION\nLOW-VOLTAGE POC - NOT RELEASED',300,15,1.5)
    s.text('SETTINGS / FLOATING RETURN: EF_RTN MUST NOT CONNECT TO GND',15,198,1.5)
    s.text('Nominal board limit 1.49 A (8.06k); normal operating target <=1.2 A total.\nAdapter: regulated 12 V / 3 A, isolated and current-limited.\nAuxiliary output shares the protected budget; no daisy-chain guarantee.\nFuses are secondary protection; fault clearing and hot-start tests required.',15,263,1.1)
    s.text('RTN island and exposed pad are separate from system GND.\nUVLO ~8.91 V; OVP ~15.95 V, nominal. Divider tolerance applies.\nMODE to RTN: current limit / auto-retry.\n100 nF dVdT: ~9.6 ms at 12 V (nominal).\nTP_IMON / TP_FLT reference EF_RTN; not MCU logic signals.',295,155,1.1)
    new=s.old
    for b in list(r.direct_blocks(new)):
        if b[1:].split()[0] in ('symbol','wire','junction','no_connect','label','global_label','text'):
            new=new.replace(b,'')
    oldcache=next(b for b in r.direct_blocks(new) if b.startswith('(lib_symbols'))
    cache=oldcache[:-1]
    for libid,b in s.libs.items():
        if '(symbol '+r.q(libid) not in oldcache: cache+='\n'+'\n'.join('\t'+l for l in b.splitlines())
    new=new.replace(oldcache,cache+'\n\t)')
    items=[]
    for b in s.items:
        if b.startswith('\t(symbol') and '(property "Reference" "F1"' in b:
            for p in list(r.direct_blocks(b)):
                if p.startswith('(property "Reference"') or p.startswith('(property "Value"'):
                    name,value=re.search(r'\(property "([^"]+)" "([^"]+)"',p).groups()
                    b=b.replace(p,r.prop(name,value,25.4,133 if name=='Reference' else 136,True).strip())
        if b.startswith('\t(label') and re.search(r'\(at [\d.-]+ [\d.-]+ 90\)',b):
            # Rotated local labels must extend away from the component body.
            b=b.replace('(justify right bottom)','(justify TMP bottom)').replace('(justify left bottom)','(justify right bottom)').replace('(justify TMP bottom)','(justify left bottom)')
        # VIN retains its global identity; RTN deliberately remains local.
        b=re.sub(r'\(label "VIN_12V" \(at ([\d.-]+) ([\d.-]+) [\d.-]+\)',r'(global_label "VIN_12V" (shape bidirectional) (at \1 \2 0)',b)
        if b.startswith('\t(symbol') and ('"TestPoint"' in b or '(lib_id "Connector:TestPoint")' in b or '(lib_id "power:PWR_FLAG")' in b):
            b=b.replace('(in_bom yes)','(in_bom no)').replace('(in_pos_files yes)','(in_pos_files no)')
        items.append(b)
    # Existing module note now reflects the implemented protection.
    preserved=[b.replace('Input/output capacitors and input protection still need sourcing/qualification.','Input/output capacitors still need sourcing/qualification.') for b in preserved]
    preserved=[b.replace('(justify right bottom)','(justify left bottom)') if b.startswith('(label "LED_3V3_K"') and ' 90)' in b else b for b in preserved]
    new=new.rstrip()[:-1]+'\n'+'\n'.join(preserved+items)+'\n)\n'
    r.patch({s.path:new})

def data(path):
    root=ET.parse(path).getroot()
    comps={c.attrib['ref']:c for c in root.findall('./components/comp') if c.find("property[@name='exclude_from_board']") is None}
    nets={n.attrib['name']:{(p.attrib['ref'],p.attrib['pin']) for p in n.findall('node')} for n in root.findall('./nets/net')}
    return comps,nets

def pcb():
    import pcbnew
    comps,nets=data(BASE/'reports/netlist-input.xml')
    path=PROJECT/'SWAFarmNodeV1.kicad_pcb'
    old=path.read_text(encoding='utf-8')
    board=pcbnew.LoadBoard(str(path))
    assert not board.GetTracks() and board.GetAreaCount()==0
    oldfp={f.GetReference():f for f in board.GetFootprints()}
    changed=set()
    for ref,f in oldfp.items():
        if ref in ('Q1','R_gate1'): board.Remove(f); changed.add(ref)
    for ref in INPUT_REFS & comps.keys():
        c=comps[ref]; fp=oldfp[ref]; nick,name=c.findtext('footprint').split(':')
        if not(fp.GetFPID().GetLibItemName()==name and fp.GetFPID().GetLibNickname()==nick):
            fresh=pcbnew.FootprintLoad(str(LIB/'footprints'/(nick+'.pretty')),name)
            assert fresh is not None
            fresh.SetFPID(pcbnew.LIB_ID(nick,name)); fresh.SetReference(ref)
            fresh.SetPosition(fp.GetPosition()); fresh.SetOrientation(fp.GetOrientation())
            board.Remove(fp); board.Add(fresh); fp=fresh
        fp.SetValue(c.findtext('value')); fp.SetPath(pcbnew.KIID_PATH('/'+c.findtext('tstamps')))
        fp.SetExcludedFromBOM(c.find("property[@name='exclude_from_bom']") is not None)
        fp.SetExcludedFromPosFiles(c.find("property[@name='exclude_from_pos_files']") is not None)
        fp.SetSheetname('Power'); fp.SetSheetfile('Power.kicad_sch')
        if ref=='J_OUT1':
            origin=fp.GetPosition()
            fp.Reference().SetPosition(pcbnew.VECTOR2I(origin.x,origin.y+pcbnew.FromMM(7)))
        changed.add(ref)
    pinmap={p:(name.replace('/','{slash}') if name.startswith(('Net-(','unconnected-(')) else name) for name,group in nets.items() for p in group}
    netobjs={str(n.GetNetname()):n for n in board.GetNetInfo().NetsByNetcode().values()}
    for name in set(pinmap.values())-netobjs.keys():
        n=pcbnew.NETINFO_ITEM(board,name); board.Add(n); netobjs[name]=n
    for f in board.GetFootprints():
        for p in f.Pads():
            key=(f.GetReference(),p.GetNumber()); name=pinmap.get(key,'')
            if str(p.GetNetname())!=name:
                changed.add(f.GetReference())
                p.SetNet(netobjs[name]) if name else p.SetNetCode(0)
    candidate=BASE/'reports/pcb-input-candidate.kicad_pcb'
    pcbnew.SaveBoard(str(candidate),board)
    candidates={re.search(r'\(property "Reference" "([^"]+)"',b)[1]:b for b in r.blocks(candidate.read_text(encoding='utf-8'),'footprint')}
    new=old
    for b in r.blocks(old,'footprint'):
        ref=re.search(r'\(property "Reference" "([^"]+)"',b)[1]
        if ref not in changed: continue
        if ref in ('Q1','R_gate1'): new=new.replace(b,''); continue
        replacement=candidates[ref]
        oldid=re.search(r'^\t\t\(uuid "([^"]+)"',b,re.M)[1]
        replacement=re.sub(r'^\t\t\(uuid "[^"]+"',lambda m:'\t\t(uuid "'+oldid+'"',replacement,count=1,flags=re.M)
        for fld in comps[ref].findall('./fields/field'):
            name,value=fld.attrib['name'],fld.text or ''
            if name not in ('Manufacturer','MPN','Datasheet'): continue
            pattern=r'\(property '+re.escape(r.q(name))+r' "(?:[^"\\]|\\.)*"'
            if re.search(pattern,replacement): replacement=re.sub(pattern,lambda m:'(property '+r.q(name)+' '+r.q(value),replacement)
            else: replacement=replacement[:-1]+f'\t(property {r.q(name)} {r.q(value)} (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1))))\n\t)'
        new=new.replace(b,replacement)
    r.patch({path:new}); sys.stdout.flush(); os._exit(0)

def verify():
    import pcbnew
    comps,nets=data(BASE/'reports/netlist-input.xml')
    prior,pnets=data(SNAP/'netlist.xml')
    bypin={p:name for name,g in nets.items() for p in g}
    checks={}
    assert not {'Q1','R_gate1'} & comps.keys()
    expect={
        '/Power/DC_IN_RAW_P':{('J1','1'),('F1','1')},
        'VIN_12V':{('F1','2'),('U1','1'),('U1','2'),('D1','1'),('C_IN1','1'),('R_UVLO1','1'),('R_OVP1','1'),('R_SHDN1','1')},
        '/Power/EF_RTN':{('U1','6'),('U1','8'),('U1','17'),('R_UVLO2','2'),('R_OVP2','2'),('R_ILIM1','2'),('R_IMON1','2'),('C_DVDT1','2')},
        '/Power/EF_UVLO':{('U1','3'),('R_UVLO1','2'),('R_UVLO2','1')},
        '/Power/EF_OVP':{('U1','5'),('R_OVP1','2'),('R_OVP2','1')},
        '/Power/EF_ILIM':{('U1','11'),('R_ILIM1','1')},
        '/Power/EF_DVDT':{('U1','12'),('C_DVDT1','1')},
        '/Power/EF_SHDN':{('U1','7'),('R_SHDN1','2')},
        '/Power/EF_IMON':{('U1','10'),('R_IMON1','1'),('TP_IMON1','1')},
        '/Power/EF_FLT_N':{('U1','14'),('R_FLT1','2'),('TP_FLT1','1')},
        '12V_SW':{('U1','15'),('U1','16'),('F2','1'),('J_OUT1','1'),('C_OUT1','1'),('U2','1'),('U3','1'),('C_IN2','1'),('C_IN3','1'),('R_FLT1','1'),('TP_12V_SW1','1')},
        '+12V':{('F2','2'),('TP_VALVE_PWR1','1'),('U_RELAY1','10'),('C_RELAY1','1'),('C_RELAYBULK1','1')}|{(f'K{i}','5') for i in range(1,9)}
    }
    for name,group in expect.items(): assert nets[name]==group,(name,nets[name]^group)
    for p in [('J1','2'),('J_OUT1','2'),('U1','9'),('C_IN1','2'),('C_OUT1','2'),('D1','2'),('TP_GND1','1')]: assert bypin[p]=='GND',p
    for i in range(1,9):
        for name in [f'/Motor Valve/RLY{i}_{c}' for c in ('COM','NO','NC')]+[f'/Motor Valve/RELAY_CMD{i}',f'/Motor Valve/COIL_LOW{i}']:
            assert nets[name]==pnets[name],name
    checks['input_topology_exact_pin_sets_verified']=True
    checks['eight_relay_contacts_commands_and_coil_sinks_unchanged']=True
    checks['rtn_isolated_from_system_ground']=True
    # Exclude only authorized input changes; check every unrelated electrical partition.
    retained=(comps.keys() & prior.keys())-INPUT_REFS
    partitions=lambda groups:{frozenset(p for p in g if p[0] in retained) for g in groups if any(p[0] in retained for p in g)}
    assert partitions(nets.values())==partitions(pnets.values())
    checks['unrelated_net_partitions_unchanged']=True
    board=pcbnew.LoadBoard(str(PROJECT/'SWAFarmNodeV1.kicad_pcb'))
    baseline=pcbnew.LoadBoard(str(SNAP/'project/SWAFarmNodeV1.kicad_pcb'))
    fps={f.GetReference():f for f in board.GetFootprints()}
    assert len(fps)==len(list(board.GetFootprints())), 'duplicate references'
    assert set(fps)==set(comps)|{'MH1','MH2','MH3','MH4'}
    count=0
    for ref,f in fps.items():
        for p in f.Pads():
            key=(ref,p.GetNumber())
            expected=bypin.get(key,'')
            if expected.startswith(('Net-(','unconnected-(')): expected=expected.replace('/','{slash}')
            assert str(p.GetNetname())==expected,(key,str(p.GetNetname()),expected)
            if key in bypin: count+=1
        if ref in comps:
            c=comps[ref]
            nick,name=c.findtext('footprint').split(':')
            assert f.GetFPID().GetLibNickname()==nick and f.GetFPID().GetLibItemName()==name
            assert str(f.GetValue())==c.findtext('value')
    checks['pcb_pad_net_assignments_checked']=count
    checks['footprints_including_four_mechanical']=len(fps)
    checks['no_missing_extra_or_duplicate_footprints']=True
    # Unchanged footprint blocks guarantee all geometry/attributes/position are retained.
    txt=(PROJECT/'SWAFarmNodeV1.kicad_pcb').read_text(encoding='utf-8')
    before=(SNAP/'project/SWAFarmNodeV1.kicad_pcb').read_text(encoding='utf-8')
    fblocks=lambda t:{re.search(r'\(property "Reference" "([^"]+)"',b)[1]:b for b in r.blocks(t,'footprint')}
    newblocks,oldblocks=fblocks(txt),fblocks(before)
    for ref in set(fps)-INPUT_REFS: assert newblocks[ref]==oldblocks[ref],ref
    checks['unrelated_footprint_blocks_byte_preserved']=len(set(fps)-INPUT_REFS)
    for ref in ('J1','J_OUT1'):
        pads=list(fps[ref].Pads()); assert len(pads)==2
        assert all(p.GetDrillSize().x==pcbnew.FromMM(1.4) for p in pads)
        p1,p2=sorted(pads,key=lambda p:p.GetNumber())
        delta=p1.GetPosition()-p2.GetPosition()
        assert abs((delta.x**2+delta.y**2)**0.5-pcbnew.FromMM(5.08))<2
    for ref in ('F1','F2'):
        for p in fps[ref].Pads(): assert p.GetSize()==pcbnew.VECTOR2I(pcbnew.FromMM(1.96),pcbnew.FromMM(3.15))
    checks['terminal_pitch_drill_and_fuse_lands_checked']=True
    for p in (SNAP/'project').glob('*.kicad_sch'):
        if p.name!='Power.kicad_sch': assert p.read_bytes()==(PROJECT/p.name).read_bytes(),p.name
    pro='SWAFarmNodeV1.kicad_pro'
    assert (PROJECT/pro).read_bytes()==(SNAP/'project'/pro).read_bytes()
    checks['unrelated_sheets_and_project_rules_unchanged']=True
    original=BASE.parents[1]/'Hardware/SWAFarmNodeV1'
    originals=BASE.parent/'2026-09-21/before-section-a'
    hashes={}
    for p in originals.iterdir():
        if p.suffix not in ('.kicad_sch','.kicad_pcb','.kicad_pro'): continue
        h=hashlib.sha256((original/p.name).read_bytes()).hexdigest()
        assert h==hashlib.sha256(p.read_bytes()).hexdigest(),p.name
        hashes[p.name]=h
    checks['original_source_sha256_verified']=hashes
    checks['tracks']=len(list(board.GetTracks())); checks['copper_zones']=board.GetAreaCount()
    bom=[c for c in comps.values() if c.find("property[@name='exclude_from_bom']") is None]
    checks['bom_components']=len(bom)
    checks['bom_with_mpn']=sum(bool(c.findtext("./fields/field[@name='MPN']")) for c in bom)
    checks['nominal_current_limit_A']=round(12000/8060,4)
    checks['nominal_uvlo_V']=round(1.19*(1+64900/10000),4)
    checks['nominal_ovp_V']=round(1.19*(1+124000/10000),4)
    checks['nominal_ramp_ms_at_12V']=8000*12*100e-9*1000
    checks['status']='NOT READY: placement, routing, thermal holes, sourcing, load tests and release validation remain'
    print(json.dumps(checks,indent=2)); sys.stdout.flush(); os._exit(0)
def inspect():
    s = r.Sheet('Power.kicad_sch')
    for b in r.direct_blocks(s.old):
        if b.startswith('(symbol'):
            print(re.search(r'\(property "Reference" "([^"]+)',b)[1],re.search(r'\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)\)',b).groups(),re.search(r'\(lib_id "([^"]+)',b)[1])
    for b in r.blocks(s.old,'symbol',2):
        if 'TPS2660' in b[:70]:
            src='\n'.join(l[1:] for l in b.splitlines())
            print(b[:100],r.pins(src))

if __name__ == '__main__':
    if sys.argv[1] == 'inspect': inspect()
    elif sys.argv[1] == 'schematic': schematic()
    elif sys.argv[1] == 'pcb': pcb()
    elif sys.argv[1] == 'verify': verify()
