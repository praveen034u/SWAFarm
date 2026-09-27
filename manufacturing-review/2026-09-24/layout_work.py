"""Physical implementation on the manufacturing copy; all source changes via patches."""
import sys,re,json,os,difflib
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as p
import relay_revision as r
import release_work as w
B,P,L=r.BASE,r.PROJECT,r.LIB
path=P/'SWAFarmNodeV1.kicad_pcb'
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def finish(board,tag):
    candidate=B/'reports'/('pcb-'+tag+'-candidate.kicad_pcb');p.SaveBoard(str(candidate),board)
    old=path.read_text(encoding='utf-8');raw=candidate.read_text(encoding='utf-8')
    # Keep source block order, avoiding enormous diffs from native UUID sorting.
    root=ET.parse(B/'reports/netlist-release.xml').getroot(); cs={c.attrib['ref']:c for c in root.findall('./components/comp')}
    fps={re.search(r'\(property "Reference" "([^"]+)"',b)[1]:b for b in r.blocks(raw,'footprint')}
    for ref,b in list(fps.items()):
        if ref not in cs:continue
        for field in cs[ref].findall('./fields/field'):
            name,value=field.attrib['name'],field.text or ''
            token='(property '+r.q(name)+' '
            found=next((x for x in r.direct_blocks(b) if x.startswith(token)),None)
            if found:b=b.replace(found,re.sub(r'^(\(property "[^"]+" )"(?:\\.|[^"\\])*"',lambda m:m[1]+r.q(value),found,count=1))
            else:b=b[:-1]+f'\n\t\t(property {r.q(name)} {r.q(value)} (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1))))\n\t)'
        fps[ref]=b
    new=old
    for b in r.blocks(old,'footprint'):
        ref=re.search(r'\(property "Reference" "([^"]+)"',b)[1]
        fresh=fps.pop(ref,'')
        if fresh:
            oid=re.search(r'^\t\t\(uuid "([^"]+)"',b,re.M)[1]
            fresh=re.sub(r'^\t\t\(uuid "[^"]+"',lambda m:'\t\t(uuid "'+oid+'"',fresh,count=1,flags=re.M)
        new=new.replace(b,fresh)
    for kind in ('layers','setup','gr_line','gr_rect','gr_text','segment','via','zone'):
        ob=list(r.blocks(new,kind)); nb=list(r.blocks(raw,kind))
        for i,b in enumerate(ob):new=new.replace(b,nb[i] if i<len(nb) else '',1)
        if len(nb)>len(ob):new=new.rstrip()[:-1]+'\n'+'\n'.join(nb[len(ob):])+'\n)\n'
    if fps:new=new.rstrip()[:-1]+'\n'+'\n'.join(fps.values())+'\n)\n'
    # Emit separate per-footprint hunks to avoid SequenceMatcher's repeated-line ambiguity.
    def fpmap(text):return {re.search(r'\(property "Reference" "([^"]+)"',b)[1]:b for b in r.blocks(text,'footprint')}
    om,nm=fpmap(old),fpmap(new)
    print('*** Begin Patch\n*** Update File: '+path.as_posix())
    for ref in om:
        if ref not in nm:continue
        lines=list(difflib.unified_diff(om[ref].splitlines(),nm[ref].splitlines(),n=5))[2:]
        if lines:
            for line in lines:print('@@' if line.startswith('@@') else line)
    tailold=old;tailnew=new
    for ref,b in nm.items():
        if ref in om:tailnew=tailnew.replace(b,om[ref])
    for line in list(difflib.unified_diff(tailold.splitlines(),tailnew.splitlines(),n=3))[2:]:print('@@' if line.startswith('@@') else line)
    print('*** End Patch');sys.stdout.flush();os._exit(0)

def stage():
    old=path.read_text(encoding='utf-8');raw=(B/'reports/pcb-placement-candidate.kicad_pcb').read_text(encoding='utf-8')
    get=lambda t:{re.search(r'\(property "Reference" "([^"]+)"',b)[1]:b for b in r.blocks(t,'footprint')}
    om,nm=get(old),get(raw);new=old
    start=int(sys.argv[2]);refs=sorted(nm)[start:start+15]
    for ref in refs:
        if ref in om:new=new.replace(om[ref],nm[ref])
        else:new=new.rstrip()[:-1]+'\n'+nm[ref]+'\n)\n'
    if start==0:
        for kind in ('gr_line','gr_rect'):
            ob=list(r.blocks(new,kind));nb=list(r.blocks(raw,kind))
            for i,b in enumerate(ob):new=new.replace(b,nb[i] if i<len(nb) else '',1)
            if len(nb)>len(ob):new=new.rstrip()[:-1]+'\n'+'\n'.join(nb[len(ob):])+'\n)\n'
    r.patch({path:new});sys.stdout.flush();os._exit(0)

def refine():
    board=p.LoadBoard(str(path));fps={f.GetReference():f for f in board.GetFootprints()}
    moves={'D_PWR1':(91,14),'R_PWR1':(96,14),'FID4':(49,21),'FID3':(190,140),'MH3':(5,141),
      'J_RS485_IN1':(110,12),'J_RS485_LOC1':(140,12),'J_RS485_OUT1':(170,16),'MH2':(195,5),
      'C_IN1':(175,84),'C_BULK2':(47,9),'C_EXP1':(101,73),'C_ISOOUT1':(119.5,40),
      'C_DEC9':(101,42),'C_OUT2':(147,80),'R_UVLO2':(153,80),'C_DEC7':(81,70)}
    for i in range(1,7):
        for prefix in ('R_SER','JP_VBYP','R_VBOT','C_FILT','D_CLHI','R_BURDEN','JP_IGND'):
            f=fps[prefix+str(i)];f.Move(v(0,11 if i<4 else 8))
    for ref,(x,y) in moves.items():fps[ref].SetPosition(v(x,y))
    for ref,f in fps.items():
        if ref.startswith('FID'):f.SetAttributes(f.GetAttributes()|p.FP_SMD)
    finish(board,'refined')

def labels():
    board=p.LoadBoard(str(path));fps=list(board.GetFootprints());occupied=[]
    def box(b,margin=0):return (p.ToMM(b.GetX())-margin,p.ToMM(b.GetY())-margin,p.ToMM(b.GetRight())+margin,p.ToMM(b.GetBottom())+margin)
    def overlaps(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
    for f in fps:
        f.Reference().SetVisible(False)
        for pad in f.Pads():occupied.append(box(pad.GetBoundingBox(),.2))
        for s in f.GraphicalItems():
            if s.GetLayer()==p.F_SilkS:occupied.append(box(s.GetBoundingBox(),.12))
    occupied.append((41,-15,89,6.4))
    for f in sorted(fps,key=lambda f:(not f.GetReference().startswith(('J','K','U')),f.GetReference())):
        ref=f.Reference();ref.SetVisible(True);ref.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));ref.SetTextSize(v(1,1));ref.SetTextThickness(p.FromMM(.12))
        pos=f.GetPosition();x,y=p.ToMM(pos.x),p.ToMM(pos.y)
        found=False
        for d in [2,3,4,5,6,8,10,12,15]:
            for dx,dy in [(0,-d),(0,d),(-d,0),(d,0),(-d,-d),(d,-d),(-d,d),(d,d)]:
                ref.SetPosition(v(x+dx,y+dy));b=box(ref.GetBoundingBox(),.08)
                if b[0]<.6 or b[1]<.6 or b[2]>199.4 or b[3]>159.4:continue
                if any(overlaps(b,a) for a in occupied):continue
                occupied.append(b);found=True;break
            if found:break
        assert found, f.GetReference()
    finish(board,'labels')

def clearplacement():
    board=p.LoadBoard(str(path));fps={f.GetReference():f for f in board.GetFootprints()}
    for ref,x,y in [('C_OUT2',149,80),('D_RS485PROT1',119,21),('D_RS485PROT2',149,21),('MH3',5,155)]+[('J_RELAY'+str(i),9+24*(i-1),145) for i in range(1,9)]:fps[ref].SetPosition(v(x,y))
    finish(board,'clearplacement')

def rules():
    pro=P/'SWAFarmNodeV1.kicad_pro';data=json.loads(pro.read_text(encoding='utf-8'))
    ds=data['board']['design_settings'];ds['rules']['min_track_width']=.15;ds['rules']['min_via_annular_width']=.15
    ns=data['net_settings'];base=ns['classes'][0];base.update(track_width=.25,via_diameter=.8,via_drill=.3,clearance=.2)
    definitions=[('Power',.8,.2,['+5V','+3V3','+12V','12V_SW','VIN_12V','/Power/DC_IN_RAW_P','ISO_5V']),('Contacts',1,.5,['/Motor Valve/RLY*']),('Coils',.5,.2,['/Motor Valve/COIL_LOW*']),('USB',.15,.15,['net_USB_D*']),('RF',.15,.2,['/Sensors & LORA/LORA_RF'])]
    ns['classes']=[base];ns['netclass_patterns']=[]
    for priority,(name,width,clear,patterns) in enumerate(definitions):
        c=base.copy();c.update(name=name,track_width=width,clearance=clear,priority=priority)
        if name=='USB':c.update(diff_pair_width=.15,diff_pair_gap=.15)
        ns['classes'].append(c)
        for pattern in patterns:ns['netclass_patterns'].append({'netclass':name,'pattern':pattern})
    r.patch({pro:json.dumps(data,indent=2)+'\n'})

def exportdsn():
    board=p.LoadBoard(str(path));out=B/'routing-tools/placed.dsn'
    assert p.ExportSpecctraDSN(board,str(out));print(out);sys.stdout.flush();os._exit(0)

def pinreport():
    board=p.LoadBoard(str(path))
    for f in board.GetFootprints():
        if f.GetReference() not in ('J_USB1','U_MCU1','U1'):continue
        for a in f.Pads():
            if f.GetReference()=='U_MCU1' and a.GetNumber() not in ('13','14'):continue
            print(f.GetReference(),a.GetNumber(),str(a.GetNetname()),p.ToMM(a.GetPosition().x),p.ToMM(a.GetPosition().y))
    print('apis',[x for x in dir(p) if 'ZONE_' in x or 'POLY' in x][:50]);sys.stdout.flush();os._exit(0)

def usb_planes():
    board=p.LoadBoard(str(path));fs={f.GetReference():f for f in board.GetFootprints()}
    fs['FID3'].SetPosition(v(190,156))
    def route(net,points,width=.15,layer=p.F_Cu):
        for a,b in zip(points,points[1:]):
            t=p.PCB_TRACK(board);t.SetStart(v(*a));t.SetEnd(v(*b));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(board.FindNet(net));board.Add(t)
    def via(net,x,y):
        t=p.PCB_VIA(board);t.SetPosition(v(x,y));t.SetWidth(p.FromMM(.65));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(board.FindNet(net));board.Add(t)
    # Reversible USB pin join, one short layer transition for the crossing pin pair.
    route('net_USB_DP',[(33.25,6.68),(33.25,8.7),(34.25,8.7),(34.25,6.68)])
    route('net_USB_DM',[(33.75,6.68),(33.75,7.8)])
    route('net_USB_DM',[(34.75,6.68),(34.75,7.8),(35.25,8.3),(35.25,12),(45,21.75),(54.02,21.75),(55.25,22.98),(56.25,22.98)])
    via('net_USB_DM',33.75,7.8);via('net_USB_DM',34.75,7.8)
    route('net_USB_DM',[(33.75,7.8),(34.75,7.8)],layer=p.B_Cu)
    route('net_USB_DP',[(34.25,8.7),(34.95,9.4),(34.95,12.124),(45,22.174),(53,22.174),(55.076,24.25),(56.25,24.25)])
    # Dedicated references on both internal layers; no controller plane beneath contacts.
    primary=[(.5,.5),(99,.5),(99,22),(106,22),(106,34),(110,34),(110,62),(199.5,62),(199.5,122),(.5,122)]
    isolated=[(107,.5),(199.5,.5),(199.5,61),(112,61),(112,34),(107,34)]
    for layer in (p.In1_Cu,p.In2_Cu):
        for name,points in [('GND',primary),('ISO_GND',isolated)]:
            z=p.ZONE(board);z.SetLayer(layer);z.SetNet(board.FindNet(name));z.SetLocalClearance(p.FromMM(.25));z.SetMinThickness(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL)
            outline=z.Outline();outline.NewOutline()
            for x,y in points:outline.Append(p.FromMM(x),p.FromMM(y))
            board.Add(z)
    p.ZONE_FILLER(board).Fill(board.Zones());finish(board,'usb-planes')

def usb_fix():
    board=p.LoadBoard(str(path));fs={f.GetReference():f for f in board.GetFootprints()};fs['FID4'].SetPosition(v(46,15))
    for t in board.GetTracks():
        if str(t.GetNetname()) not in ('net_USB_DM','net_USB_DP'):continue
        if isinstance(t,p.PCB_VIA):
            if abs(p.ToMM(t.GetPosition().x)-34.75)<.001:t.SetPosition(v(35.25,7.8))
        else:
            a,b=t.GetStart(),t.GetEnd()
            for which,c in [('start',a),('end',b)]:
                xy=(round(p.ToMM(c.x),3),round(p.ToMM(c.y),3))
                change={(34.75,7.8):(35.25,7.8),(33.25,8.7):(32.9,8.7),(34.25,8.7):(34.4,8.7)}.get(xy)
                if change:(t.SetStart if which=='start' else t.SetEnd)(v(*change))
    # The USB joins are corrected further by DRC before final signoff.
    finish(board,'usb-fix')

def critical():
    board=p.LoadBoard(str(path));assert not board.GetTracks();fs={f.GetReference():f for f in board.GetFootprints()}
    def pad(ref,num):return next(z for z in fs[ref].Pads() if z.GetNumber()==num)
    def point(z):return (p.ToMM(z.GetPosition().x),p.ToMM(z.GetPosition().y))
    def route(net,points,width,layer=p.F_Cu):
        for a,b in zip(points,points[1:]):
            t=p.PCB_TRACK(board);t.SetStart(v(*a));t.SetEnd(v(*b));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(net);board.Add(t)
    # Short 50-ohm target RF path. Width tied to published PCBPower stack, confirmation required.
    a=pad('U_LORA1','12');b=pad('J_LORASMA1','1');route(a.GetNet(),[point(a),point(b)],.15)
    # Independent dry contact routes remain entirely in the field contact region.
    for i in range(1,9):
        k,j='K'+str(i),'J_RELAY'+str(i);x=10+24*(i-1)
        for kn,jn,bends in [('2','1',[(x-3,131.16),(x-3,143)]),('3','2',[(x+4.08,139.86)]),('4','3',[(x+10.16,135.78),(x+10.16,143.9)])]:
            a=pad(k,kn);b=pad(j,jn);route(a.GetNet(),[point(a)]+bends+[point(b)],1)
    finish(board,'critical')

def sync():
    board=p.LoadBoard(str(path));root=ET.parse(B/'reports/netlist-release.xml').getroot()
    cs={c.attrib['ref']:c for c in root.findall('./components/comp') if c.find("property[@name='exclude_from_board']") is None}
    nm={(node.attrib['ref'],node.attrib['pin']):(n.attrib['name'].replace('/','{slash}') if n.attrib['name'].startswith(('Net-(','unconnected-(')) else n.attrib['name']) for n in root.findall('./nets/net') for node in n.findall('node')}
    ns={str(n.GetNetname()):n for n in board.GetNetInfo().NetsByNetcode().values()}
    for name in set(nm.values())-ns.keys():ns[name]=p.NETINFO_ITEM(board,name);board.Add(ns[name])
    fs={f.GetReference():f for f in board.GetFootprints()}
    for ref,c in cs.items():
        nick,name=c.findtext('footprint').split(':');f=fs.get(ref)
        if f is None or not (f.GetFPID().GetLibNickname()==nick and f.GetFPID().GetLibItemName()==name):
            fresh=p.FootprintLoad(str(P/'SWAFarm_Review.pretty' if nick=='SWAFarm_Review' else L/'footprints'/(nick+'.pretty')),name);assert fresh,ref
            fresh.SetFPID(p.LIB_ID(nick,name));fresh.SetReference(ref)
            if f:fresh.SetPosition(f.GetPosition());fresh.SetOrientation(f.GetOrientation());board.Remove(f)
            else:fresh.SetPosition(v(250+len(fs)%10*10,180+len(fs)//10*10))
            board.Add(fresh);f=fresh
        f.SetValue(c.findtext('value'));f.SetPath(p.KIID_PATH('/'+c.findtext('tstamps')))
        f.SetExcludedFromBOM(c.find("property[@name='exclude_from_bom']") is not None)
        f.SetExcludedFromPosFiles(c.find("property[@name='exclude_from_pos_files']") is not None)
        f.SetSheetname(c.find('sheetpath').attrib['names'].strip('/'))
        for pad in f.Pads():
            name=nm.get((ref,pad.GetNumber()),'');pad.SetNet(ns[name]) if name else pad.SetNetCode(0)
    finish(board,'sync')

def place():
    board=p.LoadBoard(str(path));assert not board.GetTracks()
    coords={
      'MH1':(5,5,0),'MH2':(195,5,0),'MH3':(5,155,0),'MH4':(195,155,0),
      'U_MCU1':(65,13,0),'J_USB1':(34,3,180),'R_CC1_1':(29,11,90),'R_CC2_1':(38,11,90),'TP_USB5V1':(23,11,0),
      'C_BULK2':(49,9,180),'C_EN1':(52,14,0),'R_ENPU1':(48,18,90),
      'SW_RESET1':(43,25,0),'SW_BOOT1':(49,30,0),'R_BOOT1':(55,30,0),'SW_SETUP1':(72,32,0),'R_SETUP1':(72,28,0),
      'J_PROG1':(83,20,0),'D_PWR1':(85,5,0),'D_LINK1':(92,5,0),'D_FAULT1':(99,5,0),
      'R_PWR1':(85,9,0),'R_LINK1':(92,9,0),'R_FAULT1':(99,9,0),
      'U_LORA1':(88,51.75,0),'J_LORASMA1':(72,57,0),'R_LORABOOT1':(100,51,0),'R_LORARST1':(100,47,0),
      'TP_LORABOOT1':(104,55,0),'TP_LORARST1':(104,59,0),
      'U_ISO1':(111,45,0),'U_ISODCDC1':(101,28,0),'U_RS485_TX1':(130,43,0),
      'C_ISOIN1':(101,24,0),'C_ISOBULK1':(97,31,90),'C_ISOBULK2':(120,30,90),
      'C_ISOOUT1':(118,40,180),'C_ISODEC1':(103,40,0),'C_RSDEC1':(137,40,180),
      'R_RSDE1':(103,45,90),'R_ISODE1':(122,44,90),'R_BIASA1':(140,44,0),'R_BIASB1':(140,48,0),'R_TERM1':(139,52,90),
      'TP_RS485DI1':(125,54,0),'TP_RS485RO1':(129,54,0),
      'J_RS485_IN1':(112,10,0),'J_RS485_LOC1':(142,10,0),'J_RS485_OUT1':(170,10,0),
      'D_RS485PROT1':(119,18,90),'CMC_RS485_1':(124,22,270),'D_RS485PROT2':(149,18,90),'CMC_RS485_2':(154,22,270),
      'J_SENSOR_RET1':(7,30,270),'J_SENSOR_SIG1':(7,70,270),
      'U_VALVEEXP1':(103,82,270),'U_RELAY1':(103,103,270),'R_EXP_RESET1':(97,91,0),'C_EXP1':(101,75,90),
      'C_RELAY1':(97,110,0),'C_RELAYBULK1':(119,105,0),
      'J1':(190,77,270),'J_OUT1':(190,98,270),'F1':(181,78,0),'D1':(171,78,90),'C_IN1':(171,83,0),
      'U1':(162,81,0),'C_OUT1':(162,74,0),'R_UVLO1':(153,75,90),'R_UVLO2':(151,80,90),'R_OVP1':(153,85,90),'R_OVP2':(156,88,0),
      'R_SHDN1':(154,92,0),'R_ILIM1':(169,89,90),'R_IMON1':(166,91,90),'C_DVDT1':(168,94,90),'R_FLT1':(171,73,0),
      'U2':(138,79,0),'U3':(138,96,0),'C_IN2':(132,80,90),'C_OUT2':(149,80,90),'C_IN3':(132,97,90),'C_OUT3':(149,97,90),
      'F2':(167,104,0),'TP_VALVE_PWR1':(158,108,0),'TP_12V_SW1':(178,92,0),'TP_3V3':(145,109,0),'TP_5V1':(143,89,0),
      'TP_FLT1':(176,70,0),'TP_IMON1':(162,96,0),'TP_GND1':(182,105,0),'D_LED2':(154,105,0),'R_LED2':(154,101,90)}
    for i in range(1,9):
        coords['K'+str(i)]=(10+24*(i-1),118,270);coords['J_RELAY'+str(i)]=(9+24*(i-1),149,0)
        coords['R_RELAY_PD'+str(i)]=(91+3*(i-1),95,90)
    for i in range(1,7):
        # Two rows of three analog channels, separated from relay coil currents.
        x=25+19*((i-1)%3);y=59+28*((i-1)//3)
        for prefix,dx,dy,a in [('R_SER',0,0,0),('JP_VBYP',0,5,90),('R_VBOT',8,0,90),('C_FILT',12,0,90),('D_CLHI',13,8,0),('R_BURDEN',7,6,90),('JP_IGND',6,13,90)]:coords[prefix+str(i)]=(x+dx,y+dy,a)
    for i,point in enumerate([(52,9,180),(78,13,0),(78,27,0),(59,32,0),(40,44,0),(59,45,0),(79,74,0),(86,84,0),(98,43,180),(99,39,180)],1):coords['C_DEC'+str(i)]=point
    coords.update({'R_LEDFLT1':(99,9,0),'D_FLT1':(99,5,0),'TP_ISO5V1':(145,30,0),'TP_ISOGND1':(151,30,0),'TP_USBVBUS1':(23,11,0)})
    fps={f.GetReference():f for f in board.GetFootprints()}
    missing=set(fps)-set(coords);assert not missing,missing
    for ref,f in fps.items():
        x,y,a=coords[ref];f.SetOrientationDegrees(a);f.SetPosition(v(x,y))
        f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));f.Reference().SetTextSize(v(.8,.8));f.Reference().SetTextThickness(p.FromMM(.12))
        f.Value().SetVisible(False)
    for d in list(board.GetDrawings()):
        if d.GetLayer()==p.Edge_Cuts:board.Remove(d)
    for a,b in [((0,0),(200,0)),((200,0),(200,160)),((200,160),(0,160)),((0,160),(0,0))]:
        line=p.PCB_SHAPE();line.SetShape(p.SHAPE_T_SEGMENT);line.SetStart(v(*a));line.SetEnd(v(*b));line.SetLayer(p.Edge_Cuts);line.SetWidth(p.FromMM(.05));board.Add(line)
    for i,(x,y) in enumerate([(10,10),(190,65),(190,154),(50,5),(79,33)],1):
        f=p.FootprintLoad(str(L/'footprints/Fiducial.pretty'),'Fiducial_1mm_Mask2mm');f.SetFPID(p.LIB_ID('Fiducial','Fiducial_1mm_Mask2mm'));f.SetReference('FID'+str(i));f.SetPosition(v(x,y));f.SetAttributes(p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES|p.FP_BOARD_ONLY);board.Add(f)
    finish(board,'placement')

if __name__=='__main__':{'sync':sync,'place':place,'stage':stage,'refine':refine,'labels':labels,'clearplacement':clearplacement,'rules':rules,'critical':critical,'exportdsn':exportdsn,'pinreport':pinreport,'usb-planes':usb_planes,'usb-fix':usb_fix}[sys.argv[1]]()
