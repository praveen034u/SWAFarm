"""Read-only forward-link/net audit; does not invoke the native GUI updater."""
from pathlib import Path
import sys,os,json,re,hashlib,xml.etree.ElementTree as ET
import pcbnew as p
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE.parent/'2026-09-24'))
import relay_revision as r

def main():
    board=BASE/'project/SWAFarmNodeV1.kicad_pcb'
    b=p.LoadBoard(str(board));fs=list(b.GetFootprints())
    net=ET.parse(BASE/'reports/recovered-netlist.xml').getroot()
    comps=[c for c in net.findall('components/comp') if c.find("property[@name='exclude_from_board']") is None]
    errors=[];matched=[];pin_checks=0
    expected_nets={(n.attrib['ref'],n.attrib['pin']):a.attrib['name'] for a in net.findall('nets/net') for n in a.findall('node')}
    for c in comps:
        ref=c.attrib['ref'];uid=c.find('sheetpath').attrib['tstamps'].rstrip('/')+'/'+c.findtext('tstamps')
        matches=[f for f in fs if f.GetPath().AsString()==uid]
        if len(matches)!=1:errors.append([ref,'path_match_count',len(matches)]);continue
        f=matches[0];matched.append(ref)
        if f.GetReference()!=ref:errors.append([ref,'reference',f.GetReference()])
        if f.GetValue()!=c.findtext('value'):errors.append([ref,'value',f.GetValue(),c.findtext('value')])
        if f.GetFPID().GetLibItemName()!=c.findtext('footprint').split(':')[-1]:errors.append([ref,'footprint'])
        for a in f.Pads():
            key=(ref,a.GetNumber())
            if key not in expected_nets:continue
            pin_checks+=1
            if a.GetNetname()!=expected_nets[key]:errors.append([ref,a.GetNumber(),'net',str(a.GetNetname()),expected_nets[key]])
    before=(BASE/'verified-snapshot/project/SWAFarmNodeV1.kicad_pcb').read_text()
    strip=lambda s:re.sub(r'\(path "[^"]*"\)','(path "")',s)
    assert strip(before)==strip(board.read_text()),'non-link PCB changes'
    original=BASE.parent/'2026-09-24/project'
    snapshot=BASE/'before-recovery'
    preserved=all((original/x.relative_to(snapshot)).read_bytes()==x.read_bytes() for x in snapshot.rglob('*') if x.is_file())
    schematic_unchanged=all(x.read_bytes()==(BASE/'verified-snapshot/project'/x.name).read_bytes() for x in (BASE/'project').glob('*.kicad_sch'))
    assert preserved and schematic_unchanged
    report={'status':'PASS' if not errors else 'FAIL','errors':errors,'footprints':len(fs),'schematic_components_to_match':len(comps),'matched_by_full_hierarchical_id':len(matched),'expected_new_footprints':len(comps)-len(matched),'pad_net_comparisons':pin_checks,'board_only_references':sorted(f.GetReference() for f in fs if f.GetReference() not in matched),'geometry_routing_zones_nets_unchanged':True,'schematics_identical_to_verified_archive':schematic_unchanged,'user_current_files_preserved_and_backed_up':preserved,'board_sha256':hashlib.sha256(board.read_bytes()).hexdigest(),'method':'Native KiCad netlist export and native pcbnew loading; exact full identifier match, ref/value/footprint and pad-net comparisons. No GUI update executed; this is not a claim of a native GUI round-trip.'}
    r.patch({BASE/'reports/forward-link-audit.json':json.dumps(report,indent=2)+'\n'})
    if errors:sys.stdout.flush();os._exit(1)
if __name__=='__main__':
    main();sys.stdout.flush();os._exit(0)
