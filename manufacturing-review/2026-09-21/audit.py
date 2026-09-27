import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew

base = Path(__file__).resolve().parent
repo = base.parents[1]
board = pcbnew.LoadBoard(str(base / 'project/SWAFarmNodeV1.kicad_pcb'))
root = ET.parse(base / 'reports/netlist.xml').getroot()
old_bom = {}
with (repo / 'BOM/SWAFarmNodeV1_NodeCore_BOM.csv').open(encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        for ref in row['RefDes'].split(','):
            old_bom[ref.strip()] = row
rows = []
for comp in root.findall('./components/comp'):
    ref = comp.attrib['ref']
    props = {p.attrib['name']: p.attrib.get('value', '') for p in comp.findall('property')}
    prior = old_bom.get(ref, {})
    rows.append({'Reference': ref, 'Value': comp.findtext('value', ''),
                 'Footprint': comp.findtext('footprint', ''),
                 'ExcludeFromBoard': 'exclude_from_board' in props,
                 'DNP': 'dnp' in props,
                 'SchematicMPN': props.get('MPN', props.get('Manufacturer Part Number', '')),
                 'AssemblerPart': props.get('LCSC', props.get('LCSC Part #', '')),
                 'HistoricalMPN_Unverified': prior.get('MPN', ''),
                 'HistoricalNotes': prior.get('Notes', ''),
                 'HistoricalValueMatch': prior.get('Value') == comp.findtext('value', ''),
                 'HistoricalFootprintMatch': prior.get('Footprint') == comp.findtext('footprint', '')})
with (base / 'reports/sourcing-audit.csv').open('w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
fps = []
for fp in board.GetFootprints():
    fps.append({'ref': fp.GetReference(), 'value': fp.GetValue(),
                'footprint': str(fp.GetFPID().GetLibItemName()),
                'x_mm': pcbnew.ToMM(fp.GetPosition().x), 'y_mm': pcbnew.ToMM(fp.GetPosition().y),
                'rotation': fp.GetOrientationDegrees(), 'pads': len(list(fp.Pads()))})
bbox = board.GetBoardEdgesBoundingBox()
source = repo / 'Hardware/SWAFarmNodeV1'
hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (base / 'project').iterdir() if p.is_file() and p.suffix != '.kicad_prl'}
unchanged = all(hashlib.sha256((source / name).read_bytes()).hexdigest() == h for name, h in hashes.items())
report = {'kicad': pcbnew.Version(), 'dsn_export_available': hasattr(pcbnew, 'ExportSpecctraDSN'),
          'ses_import_available': hasattr(pcbnew, 'ImportSpecctraSES'),
          'copper_layers': board.GetCopperLayerCount(),
          'outline_bbox_mm': [pcbnew.ToMM(bbox.GetWidth()), pcbnew.ToMM(bbox.GetHeight())],
          'thickness_mm': pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness()),
          'tracks_and_vias': len(list(board.GetTracks())), 'zones': len(list(board.Zones())),
          'footprint_count': len(fps), 'components': len(rows),
          'no_footprint': [r['Reference'] for r in rows if not r['Footprint']],
          'no_schematic_mpn': sum(not r['SchematicMPN'] for r in rows),
          'no_assembler_part': sum(not r['AssemblerPart'] for r in rows),
          'historical_mpn_present': sum(bool(r['HistoricalMPN_Unverified']) for r in rows),
          'source_matches_copy': unchanged, 'sha256': hashes, 'footprints': fps}
(base / 'reports/audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k not in ('footprints', 'sha256')}, indent=2))
print('Critical parts:', json.dumps([r for r in rows if r['Reference'] in ['U1','U2','U3','L1','F1','F2','J1','J_OUT1','J_RS485_IN1','J_RS485_OUT1','J_RS485_LOC1']], indent=2))
