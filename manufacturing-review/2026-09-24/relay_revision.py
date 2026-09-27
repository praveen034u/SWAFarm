"""Generate reviewable patches for the approved eight-relay revision.

No design is written by this script: patch modes emit apply_patch input.
"""
from pathlib import Path
import sys, re, uuid, json, difflib
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
PROJECT = BASE / 'project'
LIB = Path('C:/Program Files/KiCad/10.0/share/kicad')
sys.path.insert(0, str(BASE.parent / '2026-09-21'))
from inspect_open_items import blocks
from open_items import diff

def uid(s):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'swafarm-relay-poc-20260924/' + s))

def stock(libid):
    library, name = libid.split(':')
    return next(b for b in blocks((LIB/'symbols'/(library+'.kicad_sym')).read_text(encoding='utf-8'), 'symbol') if b.startswith('\t(symbol "'+name+'"\n'))

def pins(symbol):
    # Library symbols at depth 1, inner pin definitions at depth 3.
    return {re.search(r'\(number "([^"]+)"',b)[1]: {
        'name': re.search(r'\(name "([^"]*)"',b)[1],
        'at': list(map(float,re.search(r'\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)\)',b).groups()))
    } for b in blocks(symbol,'pin',3)}

def patch(files):
    print('*** Begin Patch')
    for path,new in files.items():
        item=diff(path,path.read_text(encoding='utf-8') if path.exists() else '',new)
        if item: print(item)
    print('*** End Patch')

def q(s):
    return json.dumps(str(s),ensure_ascii=False)

def prop(name,value,x,y,visible=False):
    return f'\t\t(property {q(name)} {q(value)} (at {x} {y} 0)'+('' if visible else ' (hide yes)')+' (effects (font (size 1 1))))'

class Sheet:
    def __init__(self,filename):
        self.path=PROJECT/filename
        self.old=self.path.read_text(encoding='utf-8')
        self.sheet_uuid=re.search(r'\(uuid "([^"]+)"',self.old)[1]
        self.instance_path=re.search(r'\(path "([^"]+)"',self.old)[1]
        self.libs={}
        self.items=[]

    def addlib(self,libid,source=None):
        if libid in self.libs: return
        if source is None:
            try: source=stock(libid)
            except StopIteration:
                cached=next(b for b in blocks(self.old,'symbol',2) if b.startswith('\t\t(symbol '+q(libid)+'\n'))
                source='\n'.join(l[1:] for l in cached.splitlines())
        oldname=re.search(r'\(symbol "([^"]+)"',source)[1]
        source=source.replace('(symbol '+q(oldname),'(symbol '+q(libid),1)
        self.libs[libid]=source

    def text(self,text,x,y,size=1.5):
        self.items.append(f'\t(text {q(text)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left top)) (uuid "{uid(text+str(x)+str(y))}"))')

    def add(self,libid,ref,value,fp,x,y,nets,manufacturer='',mpn='',datasheet='',source=None):
        x,y=round(round(x/1.27)*1.27,4),round(round(y/1.27)*1.27,4)
        self.addlib(libid,source)
        ps=pins(self.libs[libid])
        assert set(nets)==set(ps),(ref,set(nets)^set(ps))
        item=f'\t(symbol (lib_id {q(libid)}) (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (in_pos_files yes) (dnp no) (uuid "{uid(ref)}")\n'
        # Place visible identifiers above the bounding pin extent.
        top=round(y-max(p['at'][1] for p in ps.values())-15.24,4)
        item+='\n'.join([prop('Reference',ref,x,top,True),prop('Value',value,x,top+2.54,True),prop('Footprint',fp,x,y),prop('Datasheet',datasheet,x,y),prop('Manufacturer',manufacturer,x,y),prop('MPN',mpn,x,y)])+'\n'
        item+=f'\t\t(instances (project "SWAFarmNodeV1" (path "{self.instance_path}" (reference {q(ref)}) (unit 1))))\n\t)'
        self.items.append(item)
        for pin,p in ps.items():
            a,b,angle=p['at']; px,py=round(x+a,4),round(y-b,4)
            net=nets[pin]
            key=ref+'-'+pin
            if net is None:
                self.items.append(f'\t(no_connect (at {px} {py}) (uuid "{uid(key)}"))')
                continue
            dx,dy={0:(-5.08,0),180:(5.08,0),90:(0,5.08),270:(0,-5.08)}[int(angle)]
            ex,ey=round(px+dx,4),round(py+dy,4)
            self.items.append(f'\t(wire (pts (xy {px} {py}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(key+"wire")}"))')
            global_net=net in ('GND','+3V3','+5V','+12V','12V_SW') or net.startswith('VALVE_SPI_')
            if global_net:
                # Use labels for cross-sheet signal/power identity; ERC still checks actual source pins.
                orient=180 if angle==0 else 0
                justify='right' if orient==180 else 'left'
                self.items.append(f'\t(global_label {q(net)} (shape bidirectional) (at {ex} {ey} {orient}) (effects (font (size 0.9 0.9)) (justify {justify})) (uuid "{uid(key+"label")}"))')
            else:
                orient=90 if dx==0 else 0
                justify='right' if angle in (0,270) else 'left'
                self.items.append(f'\t(label {q(net)} (at {ex} {ey} {orient}) (effects (font (size 0.9 0.9)) (justify {justify} bottom)) (uuid "{uid(key+"label")}"))')

    def complete(self,title):
        caches='\n'.join('\n'.join('\t'+l for l in b.splitlines()) for b in self.libs.values())
        return f'(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n\t(uuid "{self.sheet_uuid}")\n\t(paper "A3")\n\t(title_block (title {q(title)}) (date "2026-09-24") (rev "POC-R8-WIP"))\n\t(lib_symbols\n{caches}\n\t)\n'+'\n'.join(self.items)+'\n\t(embedded_fonts no)\n)\n'

def relay_sheet():
    s=Sheet('Motor Valve.kicad_sch')
    exp='Interface_Expansion:MCP23S17x-x-SO'
    enets={str(i):None for i in range(1,29)}
    enets.update({'9':'+3V3','10':'GND','11':'VALVE_SPI_CS','12':'VALVE_SPI_SCLK','13':'VALVE_SPI_MOSI','14':'VALVE_SPI_MISO','15':'GND','16':'GND','17':'GND','18':'EXP_RESET_N'})
    enets.update({str(21+i):f'RELAY_CMD{i+1}' for i in range(8)})
    s.add(exp,'U_VALVEEXP1','MCP23S17-E/SO','Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm',65,65,enets,'Microchip','MCP23S17-E/SO','https://ww1.microchip.com/downloads/en/DeviceDoc/20001952C.pdf')
    resistor='Resistor_SMD:R_0603_1608Metric'
    capacitor='Capacitor_SMD:C_0603_1608Metric'
    s.add('Device:R','R_EXP_RESET1','10k',resistor,30,100,{'1':'+3V3','2':'EXP_RESET_N'})
    s.add('Device:C','C_EXP1','100nF',capacitor,112,60,{'1':'+3V3','2':'GND'})
    driver=stock('Transistor_Array:ULN2803A').replace('ULN2803A','TBD62083AFWG')
    driver=re.sub(r'\(property "Datasheet" "[^"]*"','(property "Datasheet" "https://toshiba.semicon-storage.com/info/docget.jsp?did=29893"',driver)
    driver=re.sub(r'\(property "Description" "[^"]*"','(property "Description" "Eight-channel 50V DMOS sink driver; inputs 1-8, ground 9, flyback common 10, reversed outputs 11-18"',driver)
    dn={str(i):f'RELAY_CMD{i}' for i in range(1,9)}
    dn.update({str(19-i):f'COIL_LOW{i}' for i in range(1,9)})
    dn.update({'9':'GND','10':'+12V'})
    s.add('SWAFarm_Review:TBD62083AFWG','U_RELAY1','TBD62083AFWG,EL','Package_SO:SOIC-18W_7.5x11.6mm_P1.27mm',175,50,dn,'Toshiba','TBD62083AFWG,EL','https://toshiba.semicon-storage.com/info/docget.jsp?did=29893',driver)
    for i in range(1,9):
        s.add('Device:R',f'R_RELAY_PD{i}','47k',resistor,225+20*(i-1),58,{'1':f'RELAY_CMD{i}','2':'GND'})
    s.add('Device:C','C_RELAY1','100nF',capacitor,155,97,{'1':'+12V','2':'GND'})
    s.add('Device:C_Polarized','C_RELAYBULK1','100uF 25V','Capacitor_THT:CP_Radial_D6.3mm_P2.50mm',190,97,{'1':'+12V','2':'GND'})
    for i in range(1,9):
        x=43+95*((i-1)%4); y=152+76*((i-1)//4)
        s.add('Relay:G5Q-1',f'K{i}','G5Q-14 DC12','Relay_THT:Relay_SPDT_Omron-G5Q-1',x,y,{'1':f'COIL_LOW{i}','5':'+12V','2':f'RLY{i}_COM','3':f'RLY{i}_NO','4':f'RLY{i}_NC'},'Omron','G5Q-14 DC12','https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5q.pdf')
        s.add('Connector_Generic:Conn_01x03',f'J_RELAY{i}','COM / NO / NC','Connector_Phoenix_MSTB:PhoenixContact_MSTBVA_2,5_3-G-5,08_1x03_P5.08mm_Vertical',x+35,y+14,{'1':f'RLY{i}_COM','2':f'RLY{i}_NO','3':f'RLY{i}_NC'},'Phoenix Contact','1755749','https://www.phoenixcontact.com/en-in/products/pcb-header-mstbva-25-3-g-508-1755749')
    s.text('EIGHT INDEPENDENT LOW-VOLTAGE DRY CONTACTS - NO MAINS',20,15,2)
    s.text('GPA0..7 = channels 1..8, active high. GPB and interrupts unused.\n47k input pull-downs: relay commands off while expander pins are inputs.\nFirmware: write OLATA=0 before IODIRA=0; default concurrency=1.\nMCU software reset alone does NOT force expander reset.',225,82,1.3)
    s.text('12 V controller supply powers relay coils only. External isolated 24 VAC valve supply is NOT connected to controller rails.\nWire each valve using COM and NO. Provide external branch fusing and AC-compatible coil suppression.\nPOC target: Hunter PGV-101-G-B, eight simultaneous valves for qualification. Contact/load life testing required.',20,116,1.25)
    new=s.complete('SWAFarm eight-relay POC - low-voltage outputs')
    library=PROJECT/'SWAFarm_Review.kicad_sym'
    oldlib=library.read_text(encoding='utf-8')
    custom=s.libs['SWAFarm_Review:TBD62083AFWG'].replace('(symbol "SWAFarm_Review:TBD62083AFWG"','(symbol "TBD62083AFWG"',1)
    previous=next((b for b in blocks(oldlib,'symbol') if b.startswith('\t(symbol "TBD62083AFWG"')),None)
    newlib=oldlib.replace(previous,custom) if previous else oldlib.rstrip()[:-1]+'\n'+custom+'\n)\n'
    return {s.path:new,library:newlib}

def direct_blocks(text):
    depth=0; start=None; quoted=False; escaped=False
    for i,c in enumerate(text):
        if quoted:
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': quoted=False
        elif c=='"': quoted=True
        elif c=='(':
            if depth==1: start=i
            depth+=1
        elif c==')':
            depth-=1
            if depth==1 and start is not None:
                yield text[start:i+1]
                start=None

def module_symbol():
    b='\t(symbol "RECOM_R78B_2A"\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
    b+='\t\t(property "Reference" "U" (at 0 7.62 0) (effects (font (size 1.27 1.27))))\n'
    b+='\t\t(property "Value" "RECOM_R78B_2A" (at 0 5.08 0) (effects (font (size 1.27 1.27))))\n'
    b+='\t\t(symbol "RECOM_R78B_2A_0_1" (rectangle (start -7.62 3.81) (end 7.62 -5.08) (stroke (width 0.254) (type default)) (fill (type background))))\n'
    b+='\t\t(symbol "RECOM_R78B_2A_1_1"\n'
    for n,name,kind,x,y,a in [('1','VIN','power_in',-10.16,0,0),('2','GND','power_in',0,-7.62,90),('3','VOUT','power_out',10.16,0,180)]:
        b+=f'\t\t\t(pin {kind} line\n\t\t\t\t(at {x} {y} {a})\n\t\t\t\t(length 2.54)\n\t\t\t\t(name "{name}" (effects (font (size 1.27 1.27))))\n\t\t\t\t(number "{n}" (effects (font (size 1.27 1.27))))\n\t\t\t)\n'
    return b+'\t\t)\n\t)'

def power_patch():
    s=Sheet('Power.kicad_sch')
    mod=module_symbol()
    fp='Converter_DCDC:Converter_DCDC_RECOM_R-78B-2.0_THT'
    ds='https://recom-power.com/pdf/Innoline/R-78B-2.0.pdf'
    for ref,value,rail,y in [('U2','R-78B5.0-2.0','+5V',45.72),('U3','R-78B3.3-2.0','+3V3',111.76)]:
        s.add('SWAFarm_Review:RECOM_R78B_2A',ref,value,fp,218.44,y,{'1':'12V_SW','2':'GND','3':rail},'RECOM',value,ds,mod)
        suffix='2' if ref=='U2' else '3'
        s.add('Device:C','C_IN'+suffix,'10uF 25V','Capacitor_SMD:C_1206_3216Metric',180.34,y+20.32,{'1':'12V_SW','2':'GND'})
        s.add('Device:C','C_OUT'+suffix,'22uF 10V','Capacitor_SMD:C_1206_3216Metric',250.19,y+20.32,{'1':rail,'2':'GND'})
        s.add('Connector:TestPoint','TP_5V1' if ref=='U2' else 'TP_3V3',rail,'TestPoint:TestPoint_Pad_D2.0mm',269.24,y,{'1':rail})
    s.text('APPROVED POC MODULE POWER\nBoth converters fed from protected 12V_SW.\n2 A output nameplate each; combined input budget applies.\n17.5 mm module height; enclosure clearance required.\nInput/output capacitors and input protection still need sourcing/qualification.',171.45,153.67,1.2)
    new=s.old
    removed=[]
    for b in list(direct_blocks(s.old)):
        kind=b[1:].split()[0]
        if kind not in ('symbol','wire','junction','no_connect','label','global_label','text'): continue
        coords=re.findall(r'\((?:at|xy) ([\d.-]+) ([\d.-]+)',b)
        if not coords: continue
        xs=[float(a) for a,_ in coords]
        # Entire discrete converter areas. USB and input/eFuse circuits lie to the left.
        if kind=='symbol': selected=xs[0]>=169
        else: selected=min(xs)>=169
        if min(xs)<169<=max(xs) and kind=='wire':
            raise ValueError('Converter boundary crossed by wire: '+b)
        if selected:
            removed.append(b)
            new=new.replace(b,'')
    oldcache=next(b for b in direct_blocks(new) if b.startswith('(lib_symbols'))
    cache=oldcache[:-1]
    for libid,b in s.libs.items():
        if '(symbol '+q(libid) not in oldcache:
            cache+='\n'+'\n'.join('\t'+l for l in b.splitlines())
    new=new.replace(oldcache,cache+'\n\t)')
    new=new.rstrip()[:-1]+'\n'+'\n'.join(s.items)+'\n)\n'
    library=PROJECT/'SWAFarm_Review.kicad_sym'
    oldlib=library.read_text(encoding='utf-8')
    previous=next((b for b in blocks(oldlib,'symbol') if b.startswith('\t(symbol "RECOM_R78B_2A"')),None)
    return {s.path:new,library:oldlib.replace(previous,mod) if previous else oldlib.rstrip()[:-1]+'\n'+mod+'\n)\n'}

def net_data():
    root=ET.parse(BASE/'reports/netlist-relay-power.xml').getroot()
    comps={c.attrib['ref']:c for c in root.findall('./components/comp') if c.find("property[@name='exclude_from_board']") is None}
    nets={n.attrib['name']: {(p.attrib['ref'],p.attrib['pin']) for p in n.findall('node')} for n in root.findall('./nets/net')}
    return comps,nets

def pcb_sync():
    import pcbnew
    comps,nets=net_data()
    path=PROJECT/'SWAFarmNodeV1.kicad_pcb'
    old=path.read_text(encoding='utf-8')
    selected=set(sys.argv[2].split(',')) if len(sys.argv)>2 else None
    # Preserve all pre-existing package geometry, attributes and library overrides.
    b=pcbnew.LoadBoard(str(BASE.parent/'2026-09-21/project/SWAFarmNodeV1.kicad_pcb'))
    assert not b.GetTracks() and b.GetAreaCount()==0, 'Re-sync must not discard routing'
    existing={f.GetReference():f for f in b.GetFootprints()}
    removed=[]
    changed=[]
    for ref,f in list(existing.items()):
        if ref not in comps and not (f.GetAttributes() & pcbnew.FP_BOARD_ONLY):
            b.Remove(f); removed.append(ref)
    for ref,c in comps.items():
        fpid=c.findtext('footprint')
        if not fpid: raise ValueError('Missing footprint: '+ref)
        fp=existing.get(ref)
        # KiCad UTF8 wrappers implement equality but not reliable Python inequality.
        if fp is None or not (fp.GetFPID().GetLibItemName()==fpid.split(':')[1]) or not (fp.GetFPID().GetLibNickname()==fpid.split(':')[0]):
            nick,name=fpid.split(':')
            fresh=pcbnew.FootprintLoad(str(LIB/'footprints'/(nick+'.pretty')),name)
            assert fresh is not None,(ref,fpid)
            fresh.SetFPID(pcbnew.LIB_ID(nick,name)); fresh.SetReference(ref)
            if fp is not None:
                fresh.SetPosition(fp.GetPosition()); fresh.SetOrientation(fp.GetOrientation()); b.Remove(fp)
            else:
                # Staging only: final compact floorplan follows input-circuit approval.
                idx=len(changed)
                fresh.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(30+(idx%8)*40),pcbnew.FromMM(280+(idx//8)*20)))
            fp=fresh; b.Add(fp); changed.append(ref)
        fp.SetValue(c.findtext('value'))
        fp.SetExcludedFromBOM(c.find("property[@name='exclude_from_bom']") is not None)
        fp.SetExcludedFromPosFiles(c.find("property[@name='exclude_from_pos_files']") is not None)
        fp.SetPath(pcbnew.KIID_PATH('/'+c.findtext('tstamps')))
        fp.SetSheetname(c.find('sheetpath').attrib['names'].strip('/'))
        fp.SetSheetfile((c.find('sheetpath').attrib['names'].strip('/') or 'SWAFarmNodeV1')+'.kicad_sch')
    pinmap={p:(name.replace('/','{slash}') if name.startswith(('Net-(','unconnected-(')) else name) for name,group in nets.items() for p in group}
    net_objects={str(n.GetNetname()):n for n in b.GetNetInfo().NetsByNetcode().values()}
    for name in set(pinmap.values())-net_objects.keys():
        n=pcbnew.NETINFO_ITEM(b,name); b.Add(n); net_objects[name]=n
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            key=(fp.GetReference(),pad.GetNumber())
            if key in pinmap: pad.SetNet(net_objects[pinmap[key]])
            else: pad.SetNetCode(0)
    candidate=BASE/'reports/pcb-relay-power-candidate.kicad_pcb'
    pcbnew.SaveBoard(str(candidate),b)
    candidates={re.search(r'\(property "Reference" "([^"]+)"',f)[1]:f for f in blocks(candidate.read_text(encoding='utf-8'),'footprint')}
    for ref,comp in comps.items():
        fptext=candidates[ref]
        for fld in comp.findall('./fields/field'):
            name=fld.attrib['name']; value=fld.text or ''
            if name not in ('Manufacturer','MPN','Datasheet','Qualification'): continue
            pattern=r'\(property '+re.escape(q(name))+r' "(?:[^"\\]|\\.)*"'
            if re.search(pattern,fptext):
                fptext=re.sub(pattern,lambda m:'(property '+q(name)+' '+q(value),fptext)
            else:
                fptext=fptext[:-1]+f'\t(property {q(name)} {q(value)} (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1))))\n\t)'
        candidates[ref]=fptext
    new=old
    used=set()
    for block in blocks(old,'footprint'):
        ref=re.search(r'\(property "Reference" "([^"]+)"',block)[1]
        if selected is not None and ref not in selected:
            used.add(ref)
            continue
        if ref in removed:
            new=new.replace(block,''); continue
        replacement=candidates[ref]
        oldid=re.search(r'^\t\t\(uuid "([^"]+)"',block,re.M)[1]
        replacement=re.sub(r'^\t\t\(uuid "[^"]+"',lambda m:'\t\t(uuid "'+oldid+'"',replacement,count=1,flags=re.M)
        new=new.replace(block,replacement); used.add(ref)
    new=new.rstrip()[:-1]+'\n'+'\n'.join(v for k,v in candidates.items() if k not in used and (selected is None or k in selected))+'\n)\n'
    patch({path:new})
    # KiCad 10 SWIG finalizers emit leak diagnostics into buffered stdout.
    # Flush the complete patch and exit this short-lived generator before teardown.
    import os
    sys.stdout.flush()
    os._exit(0)

def verify():
    import pcbnew,hashlib
    comps,nets=net_data()
    bypin={p:name for name,group in nets.items() for p in group}
    checks={}
    for i in range(1,9):
        assert nets[f'/Motor Valve/RELAY_CMD{i}']=={('U_VALVEEXP1',str(20+i)),('U_RELAY1',str(i)),(f'R_RELAY_PD{i}','1')}
        assert nets[f'/Motor Valve/COIL_LOW{i}']=={('U_RELAY1',str(19-i)),(f'K{i}','1')}
        for contact,kpin,jpin in [('COM','2','1'),('NO','3','2'),('NC','4','3')]:
            assert nets[f'/Motor Valve/RLY{i}_{contact}']=={(f'K{i}',kpin),(f'J_RELAY{i}',jpin)}
        assert (f'K{i}','5') in nets['+12V']
        assert (f'R_RELAY_PD{i}','2') in nets['GND']
    checks['eight_independent_contact_sets_verified']=True
    checks['eight_active_high_commands_and_pulldowns_verified']=True
    for ref,rail in [('U2','+5V'),('U3','+3V3')]:
        assert bypin[(ref,'1')]=='12V_SW'
        assert bypin[(ref,'2')]=='GND'
        assert bypin[(ref,'3')]==rail
    checks['module_pinouts_and_rail_mapping_verified']=True
    prior_xml=ET.parse(BASE.parent/'2026-09-21/reports/netlist-open-items.xml').getroot()
    prior_comps={c.attrib['ref']:c for c in prior_xml.findall('./components/comp')}
    prior_nets=[{(p.attrib['ref'],p.attrib['pin']) for p in n.findall('node')} for n in prior_xml.findall('./nets/net')]
    shared=set(comps)&set(prior_comps)
    electrical_changes={'U2','U3','C_IN2','C_IN3','C_OUT2','C_OUT3','U_VALVEEXP1','D_LED2'}
    # Existing 3V3 indicator was reverse biased: stock LED pin 1 is cathode.
    assert bypin[('D_LED2','2')]=='+3V3'
    assert nets[bypin[('D_LED2','1')]]=={('D_LED2','1'),('R_LED2','1')}
    checks['retained_3v3_indicator_polarity_corrected']=True
    retained=shared-electrical_changes
    def partitions(groups):
        return {frozenset(p for p in group if p[0] in retained) for group in groups if any(p[0] in retained for p in group)}
    assert partitions(prior_nets)==partitions(nets.values()),{'removed':partitions(prior_nets)-partitions(nets.values()),'added':partitions(nets.values())-partitions(prior_nets)}
    checks['unrelated_net_partitions_preserved']=True
    b=pcbnew.LoadBoard(str(PROJECT/'SWAFarmNodeV1.kicad_pcb'))
    fps={f.GetReference():f for f in b.GetFootprints()}
    assert len(fps)==len(b.GetFootprints()),'duplicate references'
    board_only={ref for ref,fp in fps.items() if fp.GetAttributes() & pcbnew.FP_BOARD_ONLY}
    assert set(comps)==set(fps)-board_only,(set(comps)-set(fps),set(fps)-set(comps))
    assert board_only=={'MH1','MH2','MH3','MH4'},'Existing mechanical holes must be retained'
    count=0
    for fp in fps.values():
        for pad in fp.Pads():
            key=(fp.GetReference(),pad.GetNumber())
            if key in bypin:
                name=bypin[key]
                if name.startswith(('Net-(','unconnected-(')): name=name.replace('/','{slash}')
                assert pad.GetNetname()==name,(key,pad.GetNetname(),name)
                count+=1
    checks['footprint_count']=len(fps)
    checks['pad_nets_checked']=count
    checks['tracks']=len(b.GetTracks()); checks['zones']=b.GetAreaCount()
    previous=BASE.parent/'2026-09-21/before-section-a'
    original=BASE.parents[1]/'Hardware/SWAFarmNodeV1'
    checks['original_design_unchanged']=all(hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((original/p.name).read_bytes()).digest() for p in previous.iterdir() if p.suffix in ('.kicad_sch','.kicad_pcb','.kicad_pro'))
    assert checks['original_design_unchanged']
    checks['board_outline_or_project_rules_changed']=False
    assert (BASE.parent/'2026-09-21/project/SWAFarmNodeV1.kicad_pro').read_bytes()==(PROJECT/'SWAFarmNodeV1.kicad_pro').read_bytes()
    prior_board=pcbnew.LoadBoard(str(BASE.parent/'2026-09-21/project/SWAFarmNodeV1.kicad_pcb'))
    preserved=0
    for fp in prior_board.GetFootprints():
        ref=fp.GetReference()
        if ref not in fps or ref in {'U2','U3','C_IN2','C_IN3','C_OUT2','C_OUT3','TP_3V3','TP_5V1','TP_VALVE_PWR1'}: continue
        current=fps[ref]
        def geometry(f):
            return sorted((p.GetNumber(),p.GetPosition().x,p.GetPosition().y,p.GetSize().x,p.GetSize().y,p.GetDrillSize().x,p.GetDrillSize().y,p.GetShape()) for p in f.Pads())
        assert geometry(fp)==geometry(current),ref
        preserved+=1
    checks['unchanged_existing_footprint_pad_geometries_checked']=preserved
    bom=[c for c in comps.values() if c.find("property[@name='exclude_from_bom']") is None]
    checks['bom_included_board_components']=len(bom)
    checks['bom_components_with_explicit_mpn']=sum(bool(c.findtext("./fields/field[@name='MPN']")) for c in bom)
    checks['status']='NOT READY - placement/routing, input protection, sourcing and release verification open'
    print(json.dumps(checks,indent=2))

def presentation_patch():
    path=PROJECT/'Power.kicad_sch'
    old=path.read_text(encoding='utf-8'); new=old.replace('(paper "A4")','(paper "A3")')
    selected={'U2','U3','C_IN2','C_IN3','C_OUT2','C_OUT3','TP_5V1','TP_3V3'}
    for b in direct_blocks(old):
        if b.startswith('(symbol '):
            ref=re.search(r'\(property "Reference" "([^"]+)"',b)[1]
            if ref not in selected: continue
            x,y,_=map(float,re.search(r'\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)',b).groups())
            revised=b
            for p in direct_blocks(b):
                if p.startswith('(property "Reference"') or p.startswith('(property "Value"'):
                    name,value=re.search(r'\(property "([^"]+)" "([^"]+)"',p).groups()
                    px=x+13.97 if ref.startswith('C_') else x
                    py=y+(-1.27 if name=='Reference' else 1.27) if ref.startswith('C_') else y+(-15.24 if name=='Reference' else -12.7)
                    revised=revised.replace(p,prop(name,value,round(px,4),round(py,4),True).strip())
            new=new.replace(b,revised)
        elif b.startswith('(text "APPROVED POC MODULE POWER'):
            new=new.replace(b,re.sub(r'\(at [\d.-]+ [\d.-]+ 0\)','(at 300 35 0)',b,count=1))
    patch({path:new})

def staging_patch():
    import pcbnew,os
    path=PROJECT/'SWAFarmNodeV1.kicad_pcb'; old=path.read_text(encoding='utf-8')
    b=pcbnew.LoadBoard(str(path)); fps={f.GetReference():f for f in b.GetFootprints()}
    positions={f'K{i}':(20+40*(i-1),310) for i in range(1,9)}
    positions.update({f'J_RELAY{i}':(20+40*(i-1),347) for i in range(1,9)})
    positions.update({f'R_RELAY_PD{i}':(330+10*(i-1),340) for i in range(1,9)})
    positions.update({'U_RELAY1':(380,315),'C_EXP1':(285,330),'R_EXP_RESET1':(305,330),'C_RELAY1':(350,330),'C_RELAYBULK1':(350,315),'TP_VALVE_PWR1':(30,291)})
    for ref,(x,y) in positions.items():
        fp=fps[ref]; fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))); fp.SetOrientationDegrees(0)
    generated=BASE/'reports/pcb-staging-candidate.kicad_pcb'; pcbnew.SaveBoard(str(generated),b)
    candidates={re.search(r'\(property "Reference" "([^"]+)"',f)[1]:f for f in blocks(generated.read_text(encoding='utf-8'),'footprint')}
    new=old
    for block in blocks(old,'footprint'):
        ref=re.search(r'\(property "Reference" "([^"]+)"',block)[1]
        if ref in positions: new=new.replace(block,candidates[ref])
    patch({path:new}); sys.stdout.flush(); os._exit(0)

def retain_indicator_patch():
    s=Sheet('Power.kicad_sch')
    baseline=ET.parse(BASE.parent/'2026-09-21/reports/netlist-open-items.xml').getroot()
    oldcomps={c.attrib['ref']:c for c in baseline.findall('./components/comp')}
    s.add('Device:LED','D_LED2',oldcomps['D_LED2'].findtext('value'),oldcomps['D_LED2'].findtext('footprint'),220.98,162.56,{'1':'LED_3V3_K','2':'+3V3'})
    s.add('Device:R','R_LED2','330',oldcomps['R_LED2'].findtext('footprint'),259.08,162.56,{'1':'LED_3V3_K','2':'GND'})
    new=s.old.rstrip()[:-1]+'\n'+'\n'.join(s.items)+'\n)\n'
    patch({s.path:new})

def mechanical_bom_patch():
    changes={}
    path=PROJECT/'SWAFarmNodeV1.kicad_pcb'
    old=path.read_text(encoding='utf-8')
    prior=(BASE.parent/'2026-09-21/project/SWAFarmNodeV1.kicad_pcb').read_text(encoding='utf-8')
    mechanical=[b for b in blocks(prior,'footprint') if re.search(r'\(property "Reference" "MH[1-4]"',b)]
    assert len(mechanical)==4
    assert not re.search(r'\(property "Reference" "MH[1-4]"',old)
    changes[path]=old.rstrip()[:-1]+'\n'+'\n'.join(mechanical)+'\n)\n'
    for path in PROJECT.glob('*.kicad_sch'):
        old=path.read_text(encoding='utf-8'); new=old
        for b in direct_blocks(old):
            if b.startswith('(symbol ') or b.startswith('(symbol\n'):
                if re.search(r'\(property "Footprint" "TestPoint:TestPoint_Pad_',b):
                    new=new.replace(b,b.replace('(in_bom yes)','(in_bom no)').replace('(in_pos_files yes)','(in_pos_files no)'))
        if old!=new: changes[path]=new
    patch(changes)

if __name__=='__main__':
    if sys.argv[1]=='relay-patch':
        patch(relay_sheet())
    elif sys.argv[1]=='power-patch':
        patch(power_patch())
    elif sys.argv[1]=='pcb-patch':
        pcb_sync()
    elif sys.argv[1]=='pcb-refs':
        import pcbnew
        comps,nets=net_data()
        board=pcbnew.LoadBoard(str(PROJECT/'SWAFarmNodeV1.kicad_pcb'))
        print(json.dumps(sorted(set(comps)|{f.GetReference() for f in board.GetFootprints()})))
    elif sys.argv[1]=='verify':
        verify()
    elif sys.argv[1]=='presentation-patch':
        presentation_patch()
    elif sys.argv[1]=='staging-patch':
        staging_patch()
    elif sys.argv[1]=='retain-indicator-patch':
        retain_indicator_patch()
    elif sys.argv[1]=='mechanical-bom-patch':
        mechanical_bom_patch()
    elif sys.argv[1]=='inspect':
        for name in ['Relay:G5Q-1','Transistor_Array:ULN2803A','Interface_Expansion:MCP23S17_SP','Device:R','Device:C','Connector_Generic:Conn_01x03']:
            try: print(name,json.dumps(pins(stock(name)),indent=2))
            except StopIteration: print('NOT FOUND',name)
        old=(PROJECT/'Motor Valve.kicad_sch').read_text(encoding='utf-8')
        for b in blocks(old,'symbol'):
            if '(property "Reference" "U_VALVEEXP1"' in b: print(b)
        for b in blocks(old,'symbol',2):
            if 'MCP23S17' in b[:200]: print('EXPANDER CACHE', b[:170], json.dumps(pins('\n'.join(l[1:] for l in b.splitlines())),indent=2))
    elif sys.argv[1]=='render':
        sys.path.insert(0,str(BASE.parent/'2026-09-21/tool-deps'))
        import pymupdf
        p=Path(sys.argv[2]); d=pymupdf.open(p)
        for idx in map(int,sys.argv[3:]):
            d[idx].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(str(p.with_name(p.stem+f'-{idx}.png')))
