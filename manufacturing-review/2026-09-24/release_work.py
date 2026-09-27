"""Manufacturing revision tools: emit reviewable patches; native KiCad for geometry."""
import sys,re,json,os,hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
import relay_revision as r
BASE,PROJECT,LIB=r.BASE,r.PROJECT,r.LIB
SNAP=BASE/'before-layout'
THERMALS={
 'U1':('Power.kicad_sch','Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask2.66x2.46mm_ThermalVias','TPS26600PWP_Thermal_D0.30_P0.70','17'),
 'U_MCU1':('MCU.kicad_sch','RF_Module:ESP32-S3-WROOM-1','ESP32-S3-WROOM-1_Thermal_D0.30_P0.70','41')}

def thermal_libs():
    changes={}
    for ref,(sheet,fpid,name,pnum) in THERMALS.items():
        nick,stock=fpid.split(':')
        text=(LIB/'footprints'/(nick+'.pretty')/(stock+'.kicad_mod')).read_text(encoding='utf-8')
        text=text.replace('(footprint '+r.q(stock),'(footprint '+r.q(name),1)
        count=0
        for p in list(r.direct_blocks(text)):
            if p.startswith('(pad '+r.q(pnum)+' thru_hole'):
                assert '(drill 0.2)' in p
                new=p.replace('(drill 0.2)','(drill 0.3)')
                new=re.sub(r'\(size [\d.]+ [\d.]+\)','(size 0.7 0.7)',new,count=1)
                text=text.replace(p,new); count+=1
        assert count==12,(ref,count)
        changes[PROJECT/'SWAFarm_Review.pretty'/(name+'.kicad_mod')]=text
        path=PROJECT/sheet; sch=path.read_text(encoding='utf-8')
        for b in r.direct_blocks(sch):
            if b.startswith('(symbol') and '(property "Reference" '+r.q(ref) in b:
                revised=b.replace('(property "Footprint" '+r.q(fpid),'(property "Footprint" '+r.q('SWAFarm_Review:'+name))
                if ref=='U_MCU1': revised=revised.replace('(lib_id '+r.q('SWAFarm_Review:'+name),'(lib_id "RF_Module:ESP32-S3-WROOM-1"')
                sch=sch.replace(b,revised)
        changes[path]=sch
    path=PROJECT/'fp-lib-table'; text=path.read_text(encoding='utf-8')
    if '(name "SWAFarm_Review")' not in text:
        text=text.rstrip()[:-1]+'\n\t(lib (name "SWAFarm_Review") (type "KiCad") (uri "${KIPRJMOD}/SWAFarm_Review.pretty") (options "") (descr "Reviewed project-local manufacturing footprints"))\n)\n'
    changes[path]=text
    r.patch(changes)

def board_thermal():
    import pcbnew
    path=PROJECT/'SWAFarmNodeV1.kicad_pcb'; old=path.read_text(encoding='utf-8')
    board=pcbnew.LoadBoard(str(path)); fps={f.GetReference():f for f in board.GetFootprints()}
    for ref,(_,_,name,_) in THERMALS.items():
        prev=fps[ref]; f=pcbnew.FootprintLoad(str(PROJECT/'SWAFarm_Review.pretty'),name)
        assert f
        f.SetFPID(pcbnew.LIB_ID('SWAFarm_Review',name)); f.SetReference(ref); f.SetValue(prev.GetValue())
        f.SetPosition(prev.GetPosition()); f.SetOrientation(prev.GetOrientation()); f.SetPath(prev.GetPath())
        f.SetSheetname(prev.GetSheetname()); f.SetSheetfile(prev.GetSheetfile())
        pm={p.GetNumber():p.GetNet() for p in prev.Pads()}
        for p in f.Pads(): p.SetNet(pm[p.GetNumber()])
        board.Remove(prev); board.Add(f)
    candidate=BASE/'reports/pcb-thermal-candidate.kicad_pcb'; pcbnew.SaveBoard(str(candidate),board)
    candidates={re.search(r'\(property "Reference" "([^"]+)"',b)[1]:b for b in r.blocks(candidate.read_text(encoding='utf-8'),'footprint')}
    new=old
    for b in r.blocks(old,'footprint'):
        ref=re.search(r'\(property "Reference" "([^"]+)"',b)[1]
        if ref not in THERMALS: continue
        replacement=candidates[ref]
        oldid=re.search(r'^\t\t\(uuid "([^"]+)"',b,re.M)[1]
        replacement=re.sub(r'^\t\t\(uuid "[^"]+"',lambda m:'\t\t(uuid "'+oldid+'"',replacement,count=1,flags=re.M)
        for p in r.direct_blocks(b):
            if p.startswith('(property "'):
                field=re.search(r'\(property "([^"]+)"',p)[1]
                existing=next((v for v in r.direct_blocks(replacement) if v.startswith('(property '+r.q(field)+' ')),None)
                if existing: replacement=replacement.replace(existing,p)
                else: replacement=replacement[:-1]+'\n\t\t'+p+'\n\t)'
        new=new.replace(b,replacement)
    r.patch({path:new}); sys.stdout.flush(); os._exit(0)

def inspect():
    import pcbnew
    board=pcbnew.LoadBoard(str(PROJECT/'SWAFarmNodeV1.kicad_pcb'))
    root=ET.parse(BASE/'reports/netlist-input.xml').getroot()
    cs={c.attrib['ref']:c for c in root.findall('./components/comp')}
    output=[]
    for f in board.GetFootprints():
        ref=f.GetReference();c=cs.get(ref)
        ps=[]
        for p in f.Pads():
            v=p.GetPosition()-f.GetPosition()
            ps.append({'n':p.GetNumber(),'xy':[pcbnew.ToMM(v.x),pcbnew.ToMM(v.y)],'net':str(p.GetNetname())})
        output.append({'ref':ref,'value':str(f.GetValue()),'sheet':c.find('sheetpath').attrib['names'] if c is not None else '', 'at':[pcbnew.ToMM(f.GetPosition().x),pcbnew.ToMM(f.GetPosition().y)],'angle':f.GetOrientationDegrees(),'pads':ps})
    print(json.dumps(output,separators=(',',':'))); sys.stdout.flush(); os._exit(0)

def lora_inspect():
    s=r.Sheet('Sensors & LORA.kicad_sch')
    b=next(b for b in r.direct_blocks(s.old) if b.startswith('(symbol') and '(property "Reference" "U_LORA1"' in b)
    print(b[:2500])
    libid=re.search(r'\(lib_id "([^"]+)"',b)[1]
    lib=next(b for b in r.blocks(s.old,'symbol',2) if b.startswith('\t\t(symbol '+r.q(libid)))
    print(json.dumps(r.pins('\n'.join(l[1:] for l in lib.splitlines())),indent=2))
    for b in r.direct_blocks(s.old):
        if b.startswith(('(global_label','(hierarchical_label','(label')) and ('LORA' in b or 'UART' in b): print(b)
        if b.startswith(('(wire','(no_connect')) and any(v in b for v in ('57.15','59.69','85.09 54.61','85.09 52.07')): print(b)

def set_property(b,name,value):
    token='(property '+r.q(name)+' '
    p=next((p for p in r.direct_blocks(b) if p.startswith(token)),None)
    if p:
        revised=re.sub(r'^(\(property "[^"]+" )"(?:\\.|[^"\\])*"',lambda m:m[1]+r.q(value),p,count=1)
        return b.replace(p,revised)
    xy=re.search(r'\(at ([\d.-]+) ([\d.-]+)',b)
    return b[:-1]+'\n'+r.prop(name,value,*xy.groups())+'\n\t)'

def lora_schematic():
    path=PROJECT/'Sensors & LORA.kicad_sch'; old=path.read_text(encoding='utf-8'); new=old
    # Move complete independent wire/label stubs from UART1 to UART2.
    translations=[((44.45,57.15),(85.09,52.07),'LORA_UART_RX'),((44.45,59.69),(85.09,54.61),'LORA_UART_TX')]
    for start,end,net in translations:
        matches=[]
        for b in r.direct_blocks(old):
            if b.startswith('(wire'):
                points=[tuple(map(float,p)) for p in re.findall(r'\(xy ([\d.-]+) ([\d.-]+)\)',b)]
                if start in points: matches.append((b,points))
        assert len(matches)==1,(net,matches)
        wire,points=matches[0]; other=next(p for p in points if p!=start)
        assert other==(26.67,start[1]),(net,points)
        label=next(b for b in r.direct_blocks(old) if b.startswith('(global_label '+r.q(net)))
        nc=next(b for b in r.direct_blocks(old) if b.startswith('(no_connect') and tuple(map(float,re.search(r'\(at ([\d.-]+) ([\d.-]+)',b).groups()))==end)
        endstub=(end[0]+7.62,end[1])
        revised=re.sub(r'\(xy ([\d.-]+) ([\d.-]+)\)',lambda m:'(xy %g %g)'%(end if tuple(map(float,m.groups()))==start else endstub),wire)
        new=new.replace(wire,revised)
        new=new.replace(label,re.sub(r'\(at [\d.-]+ [\d.-]+ 0\)','(at %g %g 180)'%endstub,label,count=1).replace('(justify left)','(justify right)'))
        new=new.replace(nc,re.sub(r'\(at [\d.-]+ [\d.-]+\)','(at %g %g)'%start,nc,count=1))
    b=next(b for b in r.direct_blocks(new) if b.startswith('(symbol') and '(property "Reference" "U_LORA1"' in b)
    revised=b
    for name,value in {'Value':'RAK3172-T-8-SM-NI','Manufacturer':'RAKwireless','MPN':'RAK3172-T-8-SM-NI','Datasheet':'https://docs.rakwireless.com/product-categories/wisduo/rak3172-module/datasheet/'}.items(): revised=set_property(revised,name,value)
    new=new.replace(b,revised); r.patch({path:new})

def lora_board():
    import pcbnew
    path=PROJECT/'SWAFarmNodeV1.kicad_pcb'; old=path.read_text(encoding='utf-8')
    board=pcbnew.LoadBoard(str(path)); root=ET.parse(BASE/'reports/netlist-release.xml').getroot()
    nets={}
    for n in root.findall('./nets/net'):
        name=n.attrib['name']
        for p in n.findall('node'):
            if p.attrib['ref']=='U_LORA1': nets[p.attrib['pin']]=name
    for p in ('1','2','4','5'): assert p in nets
    assert nets['1']=='LORA_UART_TX' and nets['2']=='LORA_UART_RX'
    assert all(nets[p].startswith('unconnected-') for p in ('4','5'))
    f=next(f for f in board.GetFootprints() if f.GetReference()=='U_LORA1')
    for p in f.Pads():
        name=nets[p.GetNumber()]
        if name.startswith('unconnected-'): name=name.replace('/','{slash}')
        n=board.FindNet(name)
        if not n: n=pcbnew.NETINFO_ITEM(board,name); board.Add(n)
        p.SetNet(n)
    f.SetValue('RAK3172-T-8-SM-NI')
    candidate=BASE/'reports/pcb-lora-candidate.kicad_pcb'; pcbnew.SaveBoard(str(candidate),board)
    new=candidate.read_text(encoding='utf-8')
    b=next(b for b in r.blocks(new,'footprint') if '(property "Reference" "U_LORA1"' in b)
    revised=b
    for k,v in {'Manufacturer':'RAKwireless','MPN':'RAK3172-T-8-SM-NI','Datasheet':'https://docs.rakwireless.com/product-categories/wisduo/rak3172-module/datasheet/'}.items(): revised=set_property(revised,k,v)
    prev=next(b for b in r.blocks(old,'footprint') if '(property "Reference" "U_LORA1"' in b)
    new=old.replace(prev,revised)
    r.patch({path:new}); sys.stdout.flush(); os._exit(0)

def electrical():
    changes={}; path=PROJECT/'SWAFarm_Review.kicad_sym'; lib=path.read_text(encoding='utf-8')
    for filename in ('RS-485.kicad_sch','Power.kicad_sch'):
        s=r.Sheet(filename); new=s.old
        aliases={'Converter_DCDC_Isolated:MEE1S0505SC':'TMR_1_0511','Interface_UART:THVD1450DR':'THVD1450DR','Diode:SM712_SOT23':'SM712_02HTG','Isolator:ISO7761DW':'ISO7761FDW','Connector:USB_C_Receptacle_16P':'USB_C_Receptacle_16P_Reviewed'}
        cache=next(b for b in r.direct_blocks(new) if b.startswith('(lib_symbols'))
        for oldid,name in aliases.items():
            cached=next((b for b in r.direct_blocks(cache) if b.startswith('(symbol '+r.q(oldid))),None)
            if cached is None: continue
            local='SWAFarm_Review:'+name
            revised=cached.replace(r.q(oldid),r.q(local),1)
            basename=oldid.split(':')[1]
            revised=re.sub(r'\(symbol "'+re.escape(basename)+r'(_\d+_\d+)"',lambda m:'(symbol '+r.q(name+m[1]),revised)
            if name=='TMR_1_0511':
                revised=revised.replace('(number "3"','(number "6"')
                revised=revised.replace('(property "Value" "MEE1S0505SC"','(property "Value" "TMR 1-0511"')
            # Reviewed flat local symbols retain the verified electrical pin geometry.
            new=new.replace(cached,revised).replace('(lib_id '+r.q(oldid),'(lib_id '+r.q(local))
            entry=revised.replace(r.q(local),r.q(name),1)
            previous=next((b for b in r.direct_blocks(lib) if b.startswith('(symbol '+r.q(name))),None)
            lib=lib.replace(previous,entry) if previous else lib.rstrip()[:-1]+'\n\t'+entry+'\n)\n'
        if filename=='RS-485.kicad_sch':
            for b in list(r.direct_blocks(new)):
                if not b.startswith('(symbol'): continue
                ref=re.search(r'\(property "Reference" "([^"]+)"',b)[1]; revised=b
                if ref=='U_ISODCDC1':
                    for k,v in {'Value':'TMR 1-0511','Manufacturer':'TRACO Power','MPN':'TMR 1-0511','Datasheet':'https://www.tracopower.com/tmr1-datasheet','Footprint':'Converter_DCDC:Converter_DCDC_TRACO_TMR-1-xxxx_Single_THT'}.items(): revised=set_property(revised,k,v)
                    revised=revised.replace('(pin "3"','(pin "6"')
                if ref=='U_ISO1':
                    for k,v in {'Value':'ISO7761FDWR','Manufacturer':'Texas Instruments','MPN':'ISO7761FDWR','Datasheet':'https://www.ti.com/lit/ds/symlink/iso7761.pdf'}.items(): revised=set_property(revised,k,v)
                new=new.replace(b,revised)
            for ref,val,fp,x,y,nets in [
                ('C_ISOBULK1','10uF 25V','Capacitor_SMD:C_1206_3216Metric',250,35,{'1':'+5V','2':'GND'}),
                ('C_ISOBULK2','10uF 25V','Capacitor_SMD:C_1206_3216Metric',285,35,{'1':'ISO_5V','2':'ISO_GND'}),
                ('C_RSDEC1','100nF','Capacitor_SMD:C_0603_1608Metric',320,35,{'1':'ISO_5V','2':'ISO_GND'}),
                ('C_ISODEC1','100nF','Capacitor_SMD:C_0603_1608Metric',355,35,{'1':'+3V3','2':'GND'}),
                ('R_RSDE1','47k','Resistor_SMD:R_0603_1608Metric',250,90,{'1':'RS485_DE','2':'GND'}),
                ('R_ISODE1','47k','Resistor_SMD:R_0603_1608Metric',285,90,{'1':'net_ISO_DIR','2':'ISO_GND'})]:
                s.add('Device:C' if ref.startswith('C') else 'Device:R',ref,val,fp,x,y,nets)
            for i,b in enumerate(s.items):
                for net in ('ISO_5V','ISO_GND','RS485_DE'):
                    if b.startswith('(label') or b.startswith('\t(label'):
                        if b.lstrip().startswith('(label '+r.q(net)):
                            b=b.replace('(label','(global_label',1).replace('(effects','(shape bidirectional) (effects',1).replace(' bottom)',' )')
                s.items[i]=b
            currentcache=next(b for b in r.direct_blocks(new) if b.startswith('(lib_symbols'))
            addition=''
            for lid,b in s.libs.items():
                if '(symbol '+r.q(lid) not in currentcache: addition+='\n'+'\n'.join('\t'+line for line in b.splitlines())
            new=new.replace(currentcache,currentcache[:-1]+addition+'\n\t)')
            new=new.rstrip()[:-1]+'\n'+'\n'.join(s.items)+'\n)\n'
            new=new.replace('(paper "A4")','(paper "A3")')
        changes[s.path]=new
    changes[path]=lib; r.patch(changes)

def repair_aliases():
    changes={}
    for name in ('SWAFarm_Review.kicad_sym','RS-485.kicad_sch','Power.kicad_sch'):
        p=PROJECT/name; old=p.read_text(encoding='utf-8'); new=old.replace('"MEE1S0505SC_0_0"','"TMR_1_0511_0_0"').replace('"USB_C_Receptacle_16P_0_0"','"USB_C_Receptacle_16P_Reviewed_0_0"')
        changes[p]=new
    r.patch(changes)

if __name__=='__main__':
    {'thermal-libs':thermal_libs,'board-thermal':board_thermal,'inspect':inspect,'lora-inspect':lora_inspect,'lora-schematic':lora_schematic,'lora-board':lora_board,'electrical':electrical,'repair-aliases':repair_aliases}[sys.argv[1]]()
