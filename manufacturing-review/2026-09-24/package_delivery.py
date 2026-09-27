"""Package verified deliverables, with content hashes and ZIP readback checks."""
from pathlib import Path
import hashlib,json,zipfile

base=Path(__file__).resolve().parent
out=base/'release-candidate'
validation=json.loads((out/'review/output-validation.json').read_text())
assert validation['status']=='PASS' and not validation['errors']
board=base/'project/SWAFarmNodeV1.kicad_pcb'
assert hashlib.sha256(board.read_bytes()).hexdigest()==validation['board_sha256']
assert 'data-selftest="PASS"' in (base/'reports/review-dom.html').read_text(encoding='utf-8')

def build(name, entries):
    assert len(entries)==len({k for k,p in entries})
    manifest={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in entries}
    target=base/name
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for key,path in entries:z.write(path,key)
        z.writestr('SHA256-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for key,digest in manifest.items():assert hashlib.sha256(z.read(key)).hexdigest()==digest,key
    print(json.dumps({'archive':str(target),'files':len(entries)+1,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'readback':'PASS'}))

entries=[(str(p.relative_to(out)).replace('\\','/'),p) for p in sorted(out.rglob('*')) if p.is_file() and not (p.parent.name=='assembly' and p.suffix=='.png')]
entries += [('project/'+str(p.relative_to(base/'project')).replace('\\','/'),p) for p in sorted((base/'project').rglob('*')) if p.is_file() and p.suffix not in ('.kicad_prl','.lck')]
entries += [('review/engineering-checkpoint.md',base/'reports/relay-power-checkpoint.md'),('review/browser-selftest.html',base/'reports/review-dom.html'),('review/layer-contact-sheet.png',base/'reports/layer-contact-sheet.png')]
build('SWAFarm-8Relay-2POC-Manufacturing-Candidate.zip',entries)
fab=[(p.name,p) for p in sorted((out/'fab').iterdir()) if p.is_file()]
build('SWAFarm-8Relay-Fab-DFM-Candidate.zip',fab)
