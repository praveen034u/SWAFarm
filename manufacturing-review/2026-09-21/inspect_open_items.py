"""Read-only schematic/library inspection and datasheet rendering helpers."""
from pathlib import Path
import re
import sys

BASE = Path(__file__).resolve().parent
LIB = Path('C:/Program Files/KiCad/10.0/share/kicad')

def blocks(text, kind, depth=1):
    indent = '\t' * depth
    return [m.group() for m in re.finditer(r'^' + indent + r'\(' + kind + r'(?:\s|\n).*?^' + indent + r'\)', text, re.M | re.S)]

if __name__ == '__main__':
    if sys.argv[1] == 'render':
        sys.path.insert(0, str(BASE / 'tool-deps'))
        import pymupdf
        for name, pages in [('744232090',[0]), ('PDS760',[0,3])]:
            doc = pymupdf.open(BASE / 'datasheets' / (name + '.pdf'))
            for page in pages:
                doc[page].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(str(BASE / 'datasheets' / f'{name}-{page}.png'))
    elif sys.argv[1] == 'schematic-render':
        sys.path.insert(0, str(BASE / 'tool-deps'))
        import pymupdf
        path = BASE / 'reports' / sys.argv[2]
        doc = pymupdf.open(path)
        for page in [1,3,4,5]:
            doc[page].get_pixmap(matrix=pymupdf.Matrix(1.7,1.7)).save(str(path.with_name(path.stem + f'-{page}.png')))
    elif sys.argv[1] == 'symbols':
        refs = {'J2','U2','L1','C_BOOT1','CMC_RS485_1','D_CLHI1','C_VALVEBULK1'}
        for path in (BASE / 'project').glob('*.kicad_sch'):
            s = path.read_text(encoding='utf-8')
            for b in blocks(s,'symbol'):
                ref = re.search(r'\(property "Reference" "([^"]+)"', b)
                if ref and ref[1] in refs:
                    print(path.name, b)
    elif sys.argv[1] == 'library':
        name = sys.argv[2]
        for library in ('Device','Diode','power'):
            for b in blocks((LIB / 'symbols' / (library + '.kicad_sym')).read_text(encoding='utf-8'),'symbol'):
                if b.startswith(f'\t(symbol "{name}"\n'):
                    print(b)
    elif sys.argv[1] == 'cache':
        for b in blocks((BASE / 'project' / sys.argv[2]).read_text(encoding='utf-8'),'symbol',2):
            if b.startswith('\t\t(symbol "' + sys.argv[3] + '"\n'):
                print(b)
