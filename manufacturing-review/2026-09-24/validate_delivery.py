"""Independent output and source checks. Reports are emitted as apply_patch input."""
import sys,os,re,json,csv,math,hashlib,collections,warnings
from pathlib import Path
import pcbnew as p
import relay_revision as r
B,P=r.BASE,r.PROJECT
sys.path.insert(0,str(B/'tool-deps'))
from gerbonara.rs274x import GerberFile
from gerbonara.excellon import ExcellonFile
from gerbonara.utils import MM
from gerbonara.graphic_objects import Flash,Line,Region
from gerbonara.ipc356 import Netlist
OUT=B/'release-candidate'

def inspect():
    b=p.LoadBoard(str(P/'SWAFarmNodeV1.kicad_pcb'));fs={f.GetReference():f for f in b.GetFootprints()}
    secondary=set()
    for ref,f in fs.items():
        if ref.startswith(('J_RS485','D_RS485','CMC_RS485','U_RS485','R_BIAS','R_TERM','TP_RS485','TP_ISO')) or ref in ('C_ISOOUT1','C_ISOBULK2','C_RSDEC1','R_ISODE1'):
            secondary.update(str(a.GetNetname()) for a in f.Pads() if a.GetNetCode()>0 and not str(a.GetNetname()).startswith('unconnected-'))
    crossings=[]
    def iso(x,y):return (107<x<199.5 and .5<y<34) or (112<x<199.5 and 34<=y<61)
    for t in b.GetTracks():
        name=str(t.GetNetname())
        if name in secondary or name.startswith('unconnected-'):continue
        a,z=t.GetStart(),t.GetEnd();length=math.hypot(z.x-a.x,z.y-a.y)/1e6
        if any(iso((a.x+(z.x-a.x)*i/max(1,math.ceil(length)))/1e6,(a.y+(z.y-a.y)*i/max(1,math.ceil(length)))/1e6) for i in range(max(1,math.ceil(length))+1)):
            crossings.append({'net':name,'from':[p.ToMM(a.x),p.ToMM(a.y)],'to':[p.ToMM(z.x),p.ToMM(z.y)],'layer':b.GetLayerName(t.GetLayer())})
    print('primary_tracks_over_secondary_plane',json.dumps(crossings))
    print('secondary_nets',sorted(secondary))
    for name in ['SWAFarmNodeV1-PTH.drl','SWAFarmNodeV1-NPTH.drl']:
        d=ExcellonFile.open(OUT/'fab'/name);print(name,len(d.objects),[str(x) for x in d.objects[:2]])
    g=GerberFile.open(OUT/'fab/SWAFarmNodeV1-F_Mask.gts');print('mask',len(g.objects),[str(x) for x in g.objects[:2]])

def expanded(text):
    ans=[]
    for token in text.split(','):
        token=token.strip();m=re.fullmatch(r'(.+?)(\d+)-(.+?)(\d+)',token)
        if m:
            assert m[1]==m[3];ans.extend(m[1]+str(i) for i in range(int(m[2]),int(m[4])+1))
        elif token:ans.append(token)
    return ans

def validate():
    b=p.LoadBoard(str(P/'SWAFarmNodeV1.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};checks={};errors=[]
    def check(name,value,detail=None):
        checks[name]={'pass':bool(value),'detail':detail}
        if not value:errors.append(name)
    bom=list(csv.DictReader((OUT/'assembly/BOM.csv').open(encoding='utf-8-sig')));pos=list(csv.DictReader((OUT/'assembly/CPL-KiCad.csv').open(encoding='utf-8-sig')))
    br=[ref for row in bom for ref in expanded(row['References'])];pr=[row['Ref'] for row in pos];fitted={ref for ref,f in fps.items() if not f.IsExcludedFromBOM()}
    check('bom_cpl_board_reference_match',set(br)==set(pr)==fitted and len(br)==len(set(br)) and len(pr)==len(set(pr)),{'bom':len(br),'cpl':len(pr),'board_fitted':len(fitted),'bom_only':sorted(set(br)-set(pr)),'cpl_only':sorted(set(pr)-set(br))})
    check('bom_quantities',all(len(expanded(row['References']))==int(row['QtyPerBoard']) for row in bom),sum(int(row['QtyPerBoard']) for row in bom))
    check('manufacturer_mpns_complete',all(row['MPN'] and row['Manufacturer'] for row in bom),{'groups':len(bom),'missing':[row['References'] for row in bom if not row['MPN'] or not row['Manufacturer']]})
    check('no_fitted_dnp',not any(row['DNP'].lower() in ('yes','true','1') for row in bom))
    placement=[];wrong=[]
    sources={ref:row for row in bom for ref in expanded(row['References'])}
    for row in pos:
        ref=row['Ref'];f=fps[ref];z=f.GetPosition();x,y=p.ToMM(z.x),p.ToMM(z.y);a=f.GetOrientationDegrees()
        if abs(float(row['PosX'])-x)>1e-5 or abs(float(row['PosY'])+y)>1e-5 or abs((float(row['Rot'])-a+180)%360-180)>1e-5 or row['Side']!='top':wrong.append(ref)
        pin=next((q for q in f.Pads() if q.GetNumber()=='1'),None)
        placement.append({'ref':ref,'value':row['Val'],'mpn':sources[ref]['MPN'],'x':x,'y':y,'rotation':float(row['Rot']),'pin1':None if pin is None else [p.ToMM(pin.GetPosition().x),p.ToMM(pin.GetPosition().y)]})
    check('cpl_positions_rotations_side',not wrong,{'mismatches':wrong,'convention':'KiCad absolute mm, X right / Y up (negative on this board), rotations unchanged; assembler-library offsets not available'})
    check('all_pad_centers_inside_outline',all(0<=p.ToMM(a.GetPosition().x)<=200 and 0<=p.ToMM(a.GetPosition().y)<=160 for f in fps.values() for a in f.Pads()))
    originals={}
    for old in (B.parent/'2026-09-21/before-section-a').glob('*.kicad_*'):
        original=r.ROOT/'Hardware/SWAFarmNodeV1'/old.name if hasattr(r,'ROOT') else Path('C:/Project/SWAFarm/Hardware/SWAFarmNodeV1')/old.name
        originals[old.name]=hashlib.sha256(old.read_bytes()).hexdigest()==hashlib.sha256(original.read_bytes()).hexdigest()
    check('original_project_unchanged',bool(originals) and all(originals.values()),originals)
    expected=[]
    for f in fps.values():
        for a in f.Pads():
            d=a.GetDrillSize()
            if not d.x:continue
            q=a.GetPosition();expected.append((round(p.ToMM(q.x),3),round(-p.ToMM(q.y),3),round(p.ToMM(min(d.x,d.y)),3),round(p.ToMM(max(d.x,d.y)),3),a.GetAttribute()!=p.PAD_ATTRIB_NPTH))
    for a in b.GetTracks():
        if isinstance(a,p.PCB_VIA):
            q=a.GetPosition();d=p.ToMM(a.GetDrillValue());expected.append((round(p.ToMM(q.x),3),round(-p.ToMM(q.y),3),round(d,3),round(d,3),True))
    actual=[];parser_warnings=[]
    for typ in ('PTH','NPTH'):
        with warnings.catch_warnings(record=True) as warns:
            d=ExcellonFile.open(OUT/'fab'/f'SWAFarmNodeV1-{typ}.drl')
        parser_warnings.extend(str(w.message) for w in warns)
        for a in d.objects:
            diameter=a.aperture.diameter
            if isinstance(a,Flash):x,y,length=a.x,a.y,diameter
            elif isinstance(a,Line):x,y,length=(a.x1+a.x2)/2,(a.y1+a.y2)/2,diameter+math.hypot(a.x2-a.x1,a.y2-a.y1)
            else:raise ValueError(type(a))
            actual.append((round(x,3),round(y,3),round(diameter,3),round(length,3),typ=='PTH'))
    expected=set(expected);actual=set(actual)
    missing=[e for e in expected if not any(e[4]==a[4] and max(abs(e[i]-a[i]) for i in range(4))<=.002 for a in actual)]
    extra=[a for a in actual if not any(e[4]==a[4] and max(abs(e[i]-a[i]) for i in range(4))<=.002 for e in expected)]
    check('drill_positions_sizes_and_plating_match_board',not missing and not extra,{'expected':len(expected),'exported':len(actual),'missing':missing,'extra':extra,'parser_warnings':parser_warnings})
    gerbers={f.name:GerberFile.open(f) for f in (OUT/'fab').iterdir() if f.suffix in ('.gtl','.gbl','.g1','.g2','.gts','.gbs','.gtp','.gbp','.gto','.gbo','.gm1')}
    edge=gerbers['SWAFarmNodeV1-Edge_Cuts.gm1'];edges=[a for a in edge.objects if isinstance(a,Line)];nodes=collections.Counter((round(x,4),round(y,4)) for a in edges for x,y in [(a.x1,a.y1),(a.x2,a.y2)])
    check('closed_200x160_outline',len(edges)==4 and set(nodes)=={(0,0),(200,0),(200,-160),(0,-160)} and all(v==2 for v in nodes.values()),{'edge_centerline_vertices':list(nodes),'note':'Gerber job extents include 0.05 mm edge stroke; finished profile follows centerline.'})
    job=json.loads((OUT/'fab/SWAFarmNodeV1-job.gbrjob').read_text());copper=[a['FileFunction'] for a in job['FilesAttributes'] if a['FileFunction'].startswith('Copper')]
    check('four_copper_layers_in_order',copper==['Copper,L1,Top','Copper,L2,Inr','Copper,L3,Inr','Copper,L4,Bot'],copper)
    check('all_requested_gerbers_parse',len(gerbers)==11,{n:len(g.objects) for n,g in gerbers.items()})
    openings={}
    def inside(points,x,y):
        state=False
        for (ax,ay),(bx,by) in zip(points,points[1:]+points[:1]):
            if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:state=not state
        return state
    for layer,suffix in [(p.F_Mask,'F_Mask.gts'),(p.B_Mask,'B_Mask.gbs'),(p.F_Paste,'F_Paste.gtp'),(p.B_Paste,'B_Paste.gbp')]:
        g=gerbers['SWAFarmNodeV1-'+suffix];flashes=[a for a in g.objects if isinstance(a,Flash)];regions=[a for a in g.objects if isinstance(a,Region) and a.polarity_dark];unmatched=[];count=0
        for ref,f in fps.items():
            for a in f.Pads():
                if not a.IsOnLayer(layer) or a.GetAttribute()==p.PAD_ATTRIB_NPTH:continue
                count+=1;q=a.GetPosition();x,y=p.ToMM(q.x),-p.ToMM(q.y)
                if not any(math.hypot(z.x-x,z.y-y)<.002 for z in flashes) and not any(inside(z.outline,x,y) for z in regions):unmatched.append(ref+'.'+a.GetNumber())
        openings[suffix]={'pad_apertures_checked':count,'unmatched':unmatched,'export_objects':len(g.objects)}
    check('mask_paste_pad_centers_match',all(not a['unmatched'] for a in openings.values()),openings)
    ipc=Netlist.open(OUT/'fab/SWAFarmNodeV1.ipc');normalization=json.loads((OUT/'review/ipc356-normalization.json').read_text())
    check('ipc356_parses_and_mask_fields_valid',len(ipc.test_records)==normalization['records_matched_to_board'] and not normalization['net_name_collisions'] and all(a.solder_mask is not None for a in ipc.test_records),{'records':len(ipc.test_records),'mask_codes_corrected':normalization['native_mask_values_corrected'],'note':'All records matched to source coordinates/nets; documented KiCad 10.0.5 mask-field compatibility correction. Full names in ipc356-normalization.json.'})
    drc=json.loads((B/'reports/drc-final.json').read_text());check('native_drc_clean',not(drc['violations'] or drc['unconnected_items'] or drc['schematic_parity']),{'ignored_check_categories':drc.get('ignored_checks',[]),'date':drc['date']})
    tracks=list(b.GetTracks());result={'status':'PASS' if not errors else 'FAIL','errors':errors,'checks':checks,'footprints':len(fps),'tracks':sum(not isinstance(a,p.PCB_VIA) for a in tracks),'vias':sum(isinstance(a,p.PCB_VIA) for a in tracks),'zones':len(b.Zones()),'thermal_holes':sum(a.GetDrillSize().x==p.FromMM(.3) for ref in ('U1','U_MCU1') for a in fps[ref].Pads()),'board_sha256':hashlib.sha256((P/'SWAFarmNodeV1.kicad_pcb').read_bytes()).hexdigest(),'limits':['No physical electrical, EMC, RF, environmental or valve-load tests have been performed.','No assembler library rotation offsets, stock allocation, stencil process or final impedance acceptance has been received.','3D render omits parts without installed models; not enclosure collision certification.']}
    changes={OUT/'review/output-validation.json':json.dumps(result,indent=2)+'\n',OUT/'review/placement.json':json.dumps(placement,indent=2)+'\n'}
    template=(B/'review_template.html').read_text(encoding='utf-8');changes[OUT/'review/index.html']=template.replace('__PLACEMENT_DATA__',json.dumps(placement).replace('</','<\\/'))
    r.patch(changes)

def render():
    dest=OUT/'review/independent';dest.mkdir(exist_ok=True)
    colors={'.gtl':'#ae3b16','.gbl':'#244ea3','.g1':'#7356a5','.g2':'#458056','.gm1':'#111111'}
    for f in (OUT/'fab').iterdir():
        if f.suffix in ('.gtl','.gbl','.g1','.g2','.gts','.gbs','.gtp','.gbp','.gto','.gbo','.gm1'):
            g=GerberFile.open(f)
        elif f.suffix=='.drl':g=ExcellonFile.open(f)
        else:continue
        # Renderer output is a generated derivative, never a design source.
        (dest/(f.stem+'.svg')).write_text(str(g.to_svg(force_bounds=((0,-160),(200,0)),fg=colors.get(f.suffix,'#222222'),bg='none')),encoding='utf-8')
        print(f.name,len(g.objects))

def normalize_ipc():
    b=p.LoadBoard(str(P/'SWAFarmNodeV1.kicad_pcb'));raw=(OUT/'review/IPC356-native-unprocessed.ipc').read_text();records=Netlist.from_string(raw,filename='native.ipc').test_records
    pads=[(f,a) for f in b.GetFootprints() for a in f.Pads()];vias=[a for a in b.GetTracks() if isinstance(a,p.PCB_VIA)];lines=raw.splitlines();output=[];index=0;netmap=collections.defaultdict(set);changes=[]
    for line in lines:
        if not line.startswith(('317','327','367')):output.append(line);continue
        rec=records[index];index+=1;x,y=rec.unit.convert_to(MM,rec.x),rec.unit.convert_to(MM,rec.y)
        if rec.is_via:
            matches=[a for a in vias if math.hypot(p.ToMM(a.GetPosition().x)-x,-p.ToMM(a.GetPosition().y)-y)<.002]
            assert len(matches)==1,(x,y,len(matches));a=matches[0]
            mask=int(a.IsTented(p.F_Mask))+2*int(a.IsTented(p.B_Mask))
        else:
            matches=[a for f,a in pads if f.GetReference()[:6].upper()==rec.ref_des.upper() and a.GetNumber()[:4]==(getattr(rec,'pin','') or '') and math.hypot(p.ToMM(a.GetPosition().x)-x,-p.ToMM(a.GetPosition().y)-y)<.002]
            assert matches,(rec.ref_des,getattr(rec,'pin',''),x,y)
            assert len({str(a.GetNetname()) for a in matches})==1
            a=matches[0];mask=(0 if a.IsOnLayer(p.F_Mask) else 1)+(0 if a.IsOnLayer(p.B_Mask) else 2)
        netmap[line[3:17].strip()].add(str(a.GetNetname()))
        assert line[71]=='S',line
        clean=line[:71]+' S'+str(mask)
        output.append(clean)
        if line[72:]!=str(mask):changes.append({'record':index,'old_mask_field':line[71:],'new_mask_field':'S'+str(mask),'x_mm':x,'y_mm':y})
    assert index==len(records)
    collisions={k:sorted(v) for k,v in netmap.items() if len(v)>1 and k!='N/C'};assert not collisions,collisions
    normalized='\n'.join(output)+'\n';parsed=Netlist.from_string(normalized,filename='normalized.ipc')
    assert len(parsed.test_records)==len(records) and all(a.solder_mask is not None for a in parsed.test_records)
    report={'records_matched_to_board':index,'native_mask_values_corrected':len(changes),'fixed_field_alignment':'Inserted reserved column 72 before S at column 73 for every test record.','changes':changes,'exported_net_name_to_full_board_net':{k:sorted(v) for k,v in netmap.items()},'net_name_collisions':collisions,'source':'https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0/pcbnew/exporters/export_d356.cpp','scope':'Export compatibility correction only. No PCB or schematic nets, positions, pad sizes, layer access or drill fields changed.'}
    r.patch({OUT/'fab/SWAFarmNodeV1.ipc':normalized,OUT/'review/ipc356-normalization.json':json.dumps(report,indent=2)+'\n'})

if __name__=='__main__':
    try:{'inspect':inspect,'validate':validate,'render':render,'normalize-ipc':normalize_ipc}[sys.argv[1] if len(sys.argv)>1 else 'inspect']()
    except Exception:
        import traceback;traceback.print_exc();sys.stderr.flush();os._exit(1)
    sys.stdout.flush();os._exit(0)
