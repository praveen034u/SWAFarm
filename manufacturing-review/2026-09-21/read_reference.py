"""Read-only XLSX extraction using the bundled Python standard library."""
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as E
base = Path(__file__).resolve().parent
ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with ZipFile(base.parents[1] / 'NodeForRefrence.xlsx') as z:
    strings = [''.join(e.itertext()) for e in E.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)] if 'xl/sharedStrings.xml' in z.namelist() else []
    rels = {e.attrib['Id']: e.attrib['Target'] for e in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    for sheet in E.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet',ns):
        name = sheet.attrib['name']
        print('SHEET', name)
        if not any(word in name.lower() for word in ('power','valve','layout','mechanic','connector','bom','dnp','require','footprint','allocation')):
            continue
        target = rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
        target = target.lstrip('/') if target.startswith('/') else 'xl/' + target
        for row in E.fromstring(z.read(target)).findall('s:sheetData/s:row', ns):
            cells = {}
            for cell in row.findall('s:c', ns):
                v = cell.findtext('s:v', '', ns)
                if cell.attrib.get('t') == 's': v = strings[int(v)]
                elif cell.attrib.get('t') == 'inlineStr': v = ''.join(cell.find('s:is',ns).itertext())
                if v: cells[cell.attrib['r']] = v
            if cells and (row.attrib['r']=='1' or not any(x in ' '.join(cells.values()) for x in ('HUB_CORE','MOTOR_CONTROLLER'))):
                print(json.dumps(cells, ensure_ascii=True))
