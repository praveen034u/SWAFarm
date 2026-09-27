"""Repair hierarchical symbol associations only; emit a reviewable apply_patch."""
from pathlib import Path
import sys,re,json,hashlib,xml.etree.ElementTree as ET
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE.parent/'2026-09-24'))
import relay_revision as r

pcb=BASE/'project/SWAFarmNodeV1.kicad_pcb'
old=pcb.read_text(encoding='utf-8')
net=ET.parse(BASE/'reports/recovered-netlist.xml').getroot()
comps={c.attrib['ref']:c for c in net.findall('components/comp') if c.find("property[@name='exclude_from_board']") is None}
changes=[];seen=set();new=old
for f in r.blocks(old,'footprint'):
    ref=re.search(r'\(property "Reference" "([^"]+)"',f)[1]
    assert ref not in seen,ref
    seen.add(ref)
    if ref not in comps:continue
    c=comps[ref];ids=c.findtext('tstamps').split()
    assert len(ids)==1,(ref,ids)
    expected=c.find('sheetpath').attrib['tstamps'].rstrip('/')+'/'+ids[0]
    m=re.search(r'\(path "([^"]*)"\)',f)
    assert m,(ref,'missing PCB path')
    assert m[1].split('/')[-1]==ids[0],(ref,m[1],ids)
    assert f.startswith('\t(footprint '+json.dumps(c.findtext('footprint'))),(ref,'footprint mismatch')
    if m[1]!=expected:
        replacement=f[:m.start(1)]+expected+f[m.end(1):]
        new=new.replace(f,replacement,1)
        changes.append({'reference':ref,'before':m[1],'after':expected})
assert set(comps)<=seen,sorted(set(comps)-seen)
# Removing path fields makes the entire PCB byte-for-byte equal: no geometry/net/zone changes.
strip=lambda s:re.sub(r'\(path "[^"]*"\)','(path "")',s)
assert strip(old)==strip(new)
paths=[re.search(r'\(path "([^"]*)"\)',f)[1] for f in r.blocks(new,'footprint') if re.search(r'\(property "Reference" "([^"]+)"',f)[1] in comps]
assert len(paths)==len(set(paths))==len(comps)
report={'status':'PASS','schematic_components':len(comps),'board_footprints':len(seen),'links_corrected':len(changes),'duplicate_references':0,'duplicate_symbol_paths':0,'non_path_board_content_unchanged':True,'changes':changes,'limitation':'Identifier-level update matching verified. Native GUI update has not been exercised by this script.'}
r.patch({pcb:new,BASE/'reports/link-recovery.json':json.dumps(report,indent=2)+'\n'})
