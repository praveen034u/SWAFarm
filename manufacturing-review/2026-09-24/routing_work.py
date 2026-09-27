"""Import and verify autorouting using native KiCad, apply source edits in bounded patches."""
import sys,os,re,json,math
import pcbnew as p
import layout_work as l
import relay_revision as r
B,P,path,v=l.B,l.P,l.path,l.v
candidate=B/'reports/pcb-routed-candidate.kicad_pcb'

def prepare():
    b=p.LoadBoard(str(path))
    before={f.GetReference():(f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),tuple(sorted((a.GetNumber(),str(a.GetNetname())) for a in f.Pads()))) for f in b.GetFootprints()}
    assert p.ImportSpecctraSES(b,str(B/'routing-tools/routed.ses'))
    after={f.GetReference():(f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),tuple(sorted((a.GetNumber(),str(a.GetNetname())) for a in f.Pads()))) for f in b.GetFootprints()}
    assert before==after,'Import altered placement or pad nets'
    p.ZONE_FILLER(b).Fill(b.Zones())
    p.SaveBoard(str(candidate),b)
    print(json.dumps({'candidate':str(candidate),'tracks_and_vias':len(b.GetTracks()),'footprints':len(before),'zones':len(b.Zones())}))

def stage():
    kind=sys.argv[2];start=int(sys.argv[3]);count=int(sys.argv[4])
    old=path.read_text(encoding='utf-8');raw=candidate.read_text(encoding='utf-8')
    ob=list(r.blocks(old,kind));nb=list(r.blocks(raw,kind));new=old
    if start==0:
        for block in ob:new=new.replace(block,'',1)
    marker='\t(generator_version "10.0")'
    assert marker in new
    new=new.replace(marker,marker+'\n'+'\n'.join(nb[start:start+count]),1)
    r.patch({path:new})

def inventory():
    b=p.LoadBoard(str(path));raw=candidate.read_text(encoding='utf-8')
    print(json.dumps({kind:len(list(r.blocks(raw,kind))) for kind in ('segment','via','zone')}))

def api():
    b=p.LoadBoard(str(path));c=b.GetConnectivity();f=next(iter(b.GetFootprints()));a=next(iter(f.Pads()))
    print('connectivity', [x for x in dir(c) if 'Connect' in x or 'Net' in x or 'Build' in x])
    print('shape', [x for x in dir(a.GetEffectiveShape(p.F_Cu)) if not x.startswith('_')])
    for name in ['SHAPE_SEGMENT','SHAPE_CIRCLE']:
        cls=getattr(p,name);print(name,cls.__init__.__doc__)
    print('collide',a.GetEffectiveShape(p.F_Cu).Collide.__doc__)
    print('GetConnectedItems',c.GetConnectedItems.__doc__)

def ground():
    b=p.LoadBoard(str(path));p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();c=b.GetConnectivity()
    items=list(b.GetTracks())+[a for f in b.GetFootprints() for a in f.Pads()]
    byid={a.m_Uuid.AsString():a for a in items};seen=set();added=[];failed=[]
    report=json.loads((B/'reports/drc-routed.json').read_text())
    seeds=[byid[x['uuid']] for e in report['unconnected_items'] for x in e['items'] if x['uuid'] in byid]
    def component(seed):
        found={};todo=[seed]
        while todo:
            a=todo.pop();uid=a.m_Uuid.AsString()
            if uid in found:continue
            found[uid]=a
            for z in c.GetConnectedItems(a):
                zid=z.m_Uuid.AsString()
                if zid in byid and zid not in found:todo.append(byid[zid])
        return list(found.values())
    def free(pos,anchor,net):
        circle=p.SHAPE_CIRCLE(pos,p.FromMM(.4));stub=p.SHAPE_SEGMENT(anchor,pos,p.FromMM(.25))
        for a in items:
            same=a.GetNetCode()==net
            layers=[layer for layer in (p.F_Cu,p.B_Cu) if a.IsOnLayer(layer)]
            for layer in layers:
                shape=a.GetEffectiveShape(layer)
                if not same and shape.Collide(circle,p.FromMM(.215)):return False
                if not same and layer==p.F_Cu and shape.Collide(stub,p.FromMM(.215)):return False
                # Do not drill in SMT lands, even on the same net.
                if isinstance(a,p.PAD) and a.GetAttribute()==p.PAD_ATTRIB_SMD and shape.Collide(circle,p.FromMM(.1)):return False
            if isinstance(a,p.PAD) and a.GetDrillSize().x:
                radius=max(a.GetDrillSize().x,a.GetDrillSize().y)/2
                if math.hypot(pos.x-a.GetPosition().x,pos.y-a.GetPosition().y)<radius+p.FromMM(.15+.255):return False
            if isinstance(a,p.PCB_VIA) and math.hypot(pos.x-a.GetPosition().x,pos.y-a.GetPosition().y)<p.FromMM(.55):return False
        return True
    for seed in seeds:
        if seed.m_Uuid.AsString() in seen:continue
        group=component(seed);seen.update(a.m_Uuid.AsString() for a in group)
        if any(isinstance(a,p.PCB_VIA) or isinstance(a,p.PAD) and a.GetAttribute()==p.PAD_ATTRIB_PTH for a in group):continue
        anchors=[]
        for a in group:
            if not a.IsOnLayer(p.F_Cu):continue
            anchors.append(a.GetPosition())
            if isinstance(a,p.PCB_TRACK):anchors.extend([a.GetStart(),a.GetEnd()])
        placed=False;net=seed.GetNetCode();name=str(seed.GetNetname())
        for radius in [.9,1.2,1.5,2,2.5,3,4]:
            for anchor in anchors:
                for angle in range(0,360,45):
                    pos=anchor+v(radius*math.cos(math.radians(angle)),radius*math.sin(math.radians(angle)))
                    x,y=p.ToMM(pos.x),p.ToMM(pos.y)
                    # Only connect to the correct reference-plane region.
                    if name=='GND' and not(.8<x<198 and 7<y<121 and (x<98.5 or 22.5<y<33.5 and x<105.5 or 34.5<y<61.5 and x<109.5 or y>62.5)):continue
                    if name=='ISO_GND' and not(114<x<198 and 1<y<60):continue
                    if not free(pos,anchor,net):continue
                    via=p.PCB_VIA(b);via.SetPosition(pos);via.SetWidth(p.FromMM(.8));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(seed.GetNet());b.Add(via)
                    t=p.PCB_TRACK(b);t.SetStart(anchor);t.SetEnd(pos);t.SetWidth(p.FromMM(.25));t.SetLayer(p.F_Cu);t.SetNet(seed.GetNet());b.Add(t)
                    items.extend([via,t]);added.append({'net':name,'x':x,'y':y,'island_items':len(group)});placed=True;break
                if placed:break
            if placed:break
        if not placed:failed.append({'net':name,'uuid':seed.m_Uuid.AsString(),'items':len(group)})
    p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(candidate),b)
    print(json.dumps({'added':added,'failed':failed}))

def delta():
    old=path.read_text(encoding='utf-8');raw=candidate.read_text(encoding='utf-8');new=old
    getid=lambda block:re.search(r'\(uuid "([^"]+)"',block)[1]
    for kind in ('segment','via'):
        om={getid(a):a for a in r.blocks(old,kind)};nm={getid(a):a for a in r.blocks(raw,kind)}
        for uid,a in om.items():new=new.replace(a,nm.get(uid,''),1)
        extra=[a for uid,a in nm.items() if uid not in om]
        marker='\t(generator_version "10.0")';new=new.replace(marker,marker+'\n'+'\n'.join(extra),1)
    r.patch({path:new})

def usb_fid():
    import faulthandler
    faulthandler.enable()
    b=p.LoadBoard(str(path));netinfo=b.GetNetInfo();netmap=netinfo.NetsByNetcode();nets={str(n.GetNetname()):n for n in netmap.values()}
    removed=[]
    for a in list(b.GetTracks()):
        if str(a.GetNetname()) in ('net_USB_DP','net_USB_DM'):b.RemoveNative(a);removed.append(a)
    print('Removed USB geometry; footprints',len(b.GetFootprints()),flush=True)
    def track(name,pts,layer=p.F_Cu,width=.13):
        for a,z in zip(pts,pts[1:]):
            t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(nets[name]);b.Add(t)
    dp=[(34.25,6.68),(34.25,7.5),(34.4,7.65),(34.4,8.7),(35,9.3),(35,12.103553),(44.896447,22),(53,22),(55.25,24.25),(56.25,24.25)]
    dm=[(34.75,6.68),(34.75,7.6),(35.25,8.1),(35.25,12),(45,21.75),(54.02,21.75),(55.25,22.98),(56.25,22.98)]
    track('net_USB_DP',dp);track('net_USB_DP',[(33.25,6.68),(33.25,7.55),(32.9,7.9),(32.9,8.7),(34.4,8.7)])
    track('net_USB_DM',dm);track('net_USB_DM',[(33.75,6.68),(33.75,7.8)])
    track('net_USB_DM',[(33.75,7.8),(34.95,7.8),(35.25,8.1)],p.B_Cu)
    for xy in [(33.75,7.8),(35.25,8.1)]:
        via=p.PCB_VIA(b);via.SetPosition(v(*xy));via.SetWidth(p.FromMM(.65));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(nets['net_USB_DM']);b.Add(via)
    print('Added USB geometry; footprints',len(b.GetFootprints()),flush=True)
    # Move only bare-copper local fiducials, preserving component placement.
    fps=list(b.GetFootprints());pads=[a for f in fps for a in f.Pads()];tracks=list(b.GetTracks())
    for f in b.GetFootprints():
        if f.GetReference() not in ('FID4','FID5'):continue
        origin=f.GetPosition();ox,oy=origin.x,origin.y;found=False
        for dist in [1,2,3,4,5,6]:
            for deg in range(0,360,45):
                offset=v(dist*math.cos(math.radians(deg)),dist*math.sin(math.radians(deg)))
                pos=p.VECTOR2I(ox+offset.x,oy+offset.y)
                shape=p.SHAPE_CIRCLE(pos,p.FromMM(1.15))
                if any(a.GetParentFootprint().GetReference()!=f.GetReference() and a.IsOnLayer(p.F_Cu) and a.GetEffectiveShape(p.F_Cu).Collide(shape,0) for a in pads):continue
                if any(a.IsOnLayer(p.F_Cu) and a.GetEffectiveShape(p.F_Cu).Collide(shape,0) for a in tracks):continue
                f.SetPosition(pos);found=True;print(f.GetReference(),p.ToMM(pos.x),p.ToMM(pos.y),file=sys.stderr);break
            if found:break
        assert found,f.GetReference()
    print('USB main surface lengths mm',*[sum(math.dist(a,z) for a,z in zip(pts,pts[1:])) for pts in (dp,dm)],file=sys.stderr)
    p.SaveBoard(str(candidate),b)

def footprint_delta():
    old=path.read_text(encoding='utf-8');raw=candidate.read_text(encoding='utf-8');new=old
    get=lambda t:{re.search(r'\(property "Reference" "([^"]+)"',a)[1]:a for a in r.blocks(t,'footprint')}
    om,nm=get(old),get(raw)
    for ref in ('FID4','FID5'):new=new.replace(om[ref],nm[ref])
    r.patch({path:new})

def controls():
    pro=P/'SWAFarmNodeV1.kicad_pro';d=json.loads(pro.read_text());rules=d['board']['design_settings']['rules']
    rules['min_track_width']=.125;rules['min_text_height']=1.0
    for c in d['net_settings']['classes']:
        if c['name']=='USB':c.update(track_width=.13,clearance=.12,diff_pair_width=.13,diff_pair_gap=.12)
    r.patch({pro:json.dumps(d,indent=2)+'\n'})

def usb_returns():
    b=p.LoadBoard(str(path));items=list(b.GetTracks())+[a for f in b.GetFootprints() for a in f.Pads()]
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA) or str(t.GetNetname())!='net_USB_DP':continue
        for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
            z=getter()
            if abs(p.ToMM(z.x)-32.9)<.00001:setter(v(32.94,p.ToMM(z.y)))
    added=[]
    for cx,cy in [(33.75,7.8),(35.25,8.1)]:
        count=0
        for radius in [1,1.3,1.6,1.9,2.2,2.5,3,3.5,4]:
            for degree in range(0,360,30):
                pos=v(cx+radius*math.cos(math.radians(degree)),cy+radius*math.sin(math.radians(degree)))
                circle=p.SHAPE_CIRCLE(pos,p.FromMM(.4));bad=False
                for a in items:
                    if str(a.GetNetname())=='GND' and isinstance(a,p.PCB_TRACK) and not isinstance(a,p.PCB_VIA):continue
                    for layer in (p.F_Cu,p.B_Cu):
                        if a.IsOnLayer(layer) and a.GetEffectiveShape(layer).Collide(circle,p.FromMM(.21)):
                            bad=True;break
                    if bad:break
                if bad:continue
                via=p.PCB_VIA(b);via.SetPosition(pos);via.SetWidth(p.FromMM(.8));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(b.FindNet('GND'));b.Add(via);items.append(via);count+=1;added.append((p.ToMM(pos.x),p.ToMM(pos.y)))
                if count==2:break
            if count==2:break
        assert count==2,(cx,cy)
    p.SaveBoard(str(candidate),b);print('USB ground return vias',added)

def artwork():
    b=p.LoadBoard(str(path))
    def label(text,x,y,size=1,layer=p.B_SilkS):
        a=p.PCB_TEXT(b);a.SetText(text);a.SetPosition(v(x,y));a.SetTextSize(v(size,size));a.SetTextThickness(p.FromMM(.15));a.SetLayer(layer);a.SetMirrored(layer==p.B_SilkS);b.Add(a)
    label('SWAFarm 8-RELAY POC R1',145,65.5,1.3,p.F_SilkS)
    label('12VDC CONTROL | 24VAC VALVES | NO MAINS',132,154,1.1)
    for i in range(1,9):
        for dx,text in [(0,'COM'),(5.08,'NO'),(10.16,'NC')]:label(text,9+24*(i-1)+dx,150.5)
    for x in [110,140,170]:
        for dx,text in [(0,'GND'),(5.08,'A'),(10.16,'B'),(15.24,'NC'),(20.32,'GND')]:label(text,x+dx,18.5 if x<170 else 22.5)
    for y in [77,98]:label('+12V',184,y);label('GND',184,y+5.08)
    for i in range(6):label('SIG'+str(i+1),15,70+5.08*i);label('RET'+str(i+1),15,30+5.08*i)
    label('POC ONLY - NOT SAFETY RATED',100,158,1.0)
    for z in b.Zones():
        z.SetPadConnection(p.ZONE_CONNECTION_THT_THERMAL);z.SetThermalReliefGap(p.FromMM(.3));z.SetThermalReliefSpokeWidth(p.FromMM(.3))
    p.SaveBoard(str(candidate),b)
    old=path.read_text(encoding='utf-8');raw=candidate.read_text(encoding='utf-8');new=old
    extra=list(r.blocks(raw,'gr_text'));assert not list(r.blocks(old,'gr_text'))
    marker='\t(generator_version "10.0")';new=new.replace(marker,marker+'\n'+'\n'.join(extra),1)
    for oz,nz in zip(r.blocks(old,'zone'),r.blocks(raw,'zone')):
        patched=oz
        for kind in ('connect_pads','fill'):
            get=lambda z:next(a for a in r.direct_blocks(z) if a.startswith('('+kind+' ' ) or a.startswith('('+kind+'\n'))
            patched=patched.replace(get(oz),get(nz))
        new=new.replace(oz,patched)
    r.patch({path:new})

def isolate_power():
    import heapq
    b=p.LoadBoard(str(path));target=next(t for t in b.GetTracks() if str(t.GetNetname())=='+5V' and not isinstance(t,p.PCB_VIA) and abs(p.ToMM(t.GetLength())-55.91799)<.05)
    start,end=target.GetStart(),target.GetEnd();net=target.GetNet();b.RemoveNative(target)
    # Keep the primary 5V feed entirely over its own reference domain.
    obstacles=[a for a in list(b.GetTracks())+[a for f in b.GetFootprints() for a in f.Pads()] if a.IsOnLayer(p.B_Cu) and a.GetNetCode()!=net.GetNetCode()]
    clearance=p.FromMM(.625);shapes=[]
    for a in obstacles:
        shape=a.GetEffectiveShape(p.B_Cu);box=shape.BBox();shapes.append((shape,(box.GetX()-clearance,box.GetY()-clearance,box.GetRight()+clearance,box.GetBottom()+clearance)))
    def freept(pt):
        x,y=p.ToMM(pt.x),p.ToMM(pt.y)
        if not(96<x<145 and 26<y<72):return False
        if not(x<98.4 or y>22.6 and x<105.4 or y>34.6 and x<109.4 or y>62.6):return False
        return not any(box[0]<=pt.x<=box[2] and box[1]<=pt.y<=box[3] and s.Collide(pt,clearance) for s,box in shapes)
    step=.25;S=(round(p.ToMM(start.x)/step),round(p.ToMM(start.y)/step));T=(round(p.ToMM(end.x)/step),round(p.ToMM(end.y)/step));valid={}
    def clear(q):
        if q not in valid:valid[q]=freept(v(q[0]*step,q[1]*step))
        return valid[q]
    assert clear(S) and clear(T)
    todo=[(0,S)];cost={S:0};prev={};dirs=[(1,0),(0,1),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    while todo:
        _,u=heapq.heappop(todo)
        if u==T:break
        for dx,dy in dirs:
            z=(u[0]+dx,u[1]+dy)
            if not clear(z):continue
            if dx and dy and (not clear((u[0]+dx,u[1])) or not clear((u[0],u[1]+dy))):continue
            w=cost[u]+math.hypot(dx,dy)
            if w<cost.get(z,1e30):cost[z]=w;prev[z]=u;heapq.heappush(todo,(w+math.dist(z,T),z))
    assert T in cost,'No legal primary-domain route'
    pts=[T]
    while pts[-1]!=S:pts.append(prev[pts[-1]])
    pts.reverse();corners=[pts[0]]
    for a,z,c in zip(pts,pts[1:],pts[2:]):
        if (z[0]-a[0],z[1]-a[1])!=(c[0]-z[0],c[1]-z[1]):corners.append(z)
    corners.append(pts[-1]);positions=[start]+[v(x*step,y*step) for x,y in corners]+[end]
    def visible(a,z):
        n=max(1,math.ceil(math.hypot(z.x-a.x,z.y-a.y)/100000))
        return all(freept(p.VECTOR2I(round(a.x+(z.x-a.x)*i/n),round(a.y+(z.y-a.y)*i/n))) for i in range(n+1))
    simple=[positions[0]];i=0
    while i<len(positions)-1:
        j=len(positions)-1
        while j>i+1 and not visible(positions[i],positions[j]):j-=1
        simple.append(positions[j]);i=j
    positions=simple
    for a,z in zip(positions,positions[1:]):
        if a==z:continue
        t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(z);t.SetWidth(p.FromMM(.8));t.SetLayer(p.B_Cu);t.SetNet(net);b.Add(t)
    p.SaveBoard(str(candidate),b);print(json.dumps({'primary_5V_corners':[(p.ToMM(a.x),p.ToMM(a.y)) for a in positions]}))

if __name__=='__main__':
    try:
        {'prepare':prepare,'stage':stage,'inventory':inventory,'api':api,'ground':ground,'delta':delta,'usb-fid':usb_fid,'footprint-delta':footprint_delta,'controls':controls,'usb-returns':usb_returns,'artwork':artwork,'isolate-power':isolate_power}[sys.argv[1]]()
    except Exception:
        import traceback
        traceback.print_exc();sys.stderr.flush();sys.stdout.flush();os._exit(1)
    sys.stdout.flush();os._exit(0)
