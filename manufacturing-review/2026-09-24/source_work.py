"""Traceable sourcing fields and verified same-pin connector packages."""
import sys,re
import relay_revision as r
import release_work as w
P=r.PROJECT
def catalog():
    changes={}
    parts={
      'J_USB1':('GCT','USB4105-GF-A','https://gct.co/files/drawings/usb4105.pdf','Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal'),
      'J_SENSOR_SIG1':('Phoenix Contact','1710726','https://www.phoenixcontact.com/it-it/prodotti/morsetto-circuito-stampato-mkds-15-6-508-1710726',None),
      'J_SENSOR_RET1':('Phoenix Contact','1710726','https://www.phoenixcontact.com/it-it/prodotti/morsetto-circuito-stampato-mkds-15-6-508-1710726',None),
      'J_PROG1':('Wurth Elektronik','61300311121','https://www.we-online.com/components/products/datasheet/61300311121.pdf',None),
      'J_LORASMA1':('Amphenol RF','132134','https://www.amphenolrf.com/en-us/part/132134/662/',None),
      'U_MCU1':('Espressif','ESP32-S3-WROOM-1-N16R8','https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf',None),
      'U_RS485_TX1':('Texas Instruments','THVD1450DR','https://www.ti.com/lit/ds/symlink/thvd1450.pdf',None),
      'C_RELAYBULK1':('Panasonic','EEUFR1E101','https://industrial.panasonic.com/sa/products/pt/aluminum-cap-lead/models/EEUFR1E101',None)}
    for ref in ('J_RS485_IN1','J_RS485_LOC1','J_RS485_OUT1'):
        parts[ref]=('Phoenix Contact','1755765','https://www.phoenixcontact.com/en-in/products/pcb-header-mstbva-25-5-g-508-1755765','Connector_Phoenix_MSTB:PhoenixContact_MSTBVA_2,5_5-G-5,08_1x05_P5.08mm_Vertical')
    for path in P.glob('*.kicad_sch'):
        old=path.read_text(encoding='utf-8');new=old
        for b in r.direct_blocks(old):
            if not b.startswith('(symbol'):continue
            ref=re.search(r'\(property "Reference" "([^"]+)"',b)[1]
            val=re.search(r'\(property "Value" "([^"]*)"',b)[1]
            fp=re.search(r'\(property "Footprint" "([^"]*)"',b)[1]
            spec=parts.get(ref)
            if ref.startswith('JP_'): spec=('Wurth Elektronik','61300211121','https://www.we-online.com/components/products/datasheet/61300211121.pdf',None)
            if ref.startswith('C_') and val.startswith('10uF') and '1206' in fp:spec=('Murata','GRM31CR71E106KA12L','https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31CR71E106KA12-01CA.pdf',None)
            if not spec:continue
            mfr,mpn,url,newfp=spec;revised=b
            for k,v in {'Manufacturer':mfr,'MPN':mpn,'Datasheet':url}.items():revised=w.set_property(revised,k,v)
            if newfp:revised=w.set_property(revised,'Footprint',newfp)
            if ref.startswith('J_RS485'):revised=w.set_property(revised,'Value','RS485 '+ref.split('_')[2]+' GND/A/B/NC/GND')
            if ref=='J_LORASMA1':revised=w.set_property(revised,'Value','SMA PCB jack 50R')
            new=new.replace(b,revised)
        if new!=old:changes[path]=new
    # SM712's two cached instances have different drawings; retain each reviewed pin mapping.
    path=P/'RS-485.kicad_sch';new=changes.get(path,path.read_text(encoding='utf-8'))
    lp=P/'SWAFarm_Review.kicad_sym';lib=lp.read_text(encoding='utf-8')
    for n in (1,2):
        name='SM712_SOT23_'+str(n);local='SWAFarm_Review:'+name
        cache=next(b for b in r.direct_blocks(new) if b.startswith('(lib_symbols'))
        b=next(b for b in r.direct_blocks(cache) if b.startswith('(symbol '+r.q(name)))
        assert all('(number '+r.q(str(i)) in b for i in (1,2,3))
        new=new.replace(b,b.replace('(symbol '+r.q(name),'(symbol '+r.q(local),1))
        new=new.replace('(lib_name '+r.q(name)+')\n\t\t(lib_id "Diode:SM712_SOT23")','(lib_id '+r.q(local)+')')
        if '(symbol '+r.q(name) not in lib:lib=lib.rstrip()[:-1]+'\n\t'+b+'\n)\n'
    changes[path]=new;changes[lp]=lib;r.patch(changes)
def passives():
    changes={};rvals={'5.1k':'5K1','10k':'10K','330':'330R','1k':'1K','680':'680R','120R':'120R','150R':'150R','232k':'232K','100k':'100K','124k':'124K','64.9k':'64K9','47k':'47K'}
    for path in P.glob('*.kicad_sch'):
        old=path.read_text(encoding='utf-8');new=old
        for b in r.direct_blocks(old):
            if not b.startswith('(symbol'):continue
            ref=re.search(r'\(property "Reference" "([^"]+)"',b)[1];val=re.search(r'\(property "Value" "([^"]*)"',b)[1];fp=re.search(r'\(property "Footprint" "([^"]*)"',b)[1]
            spec=None
            if ref.startswith('R_') and val in rvals:
                size='0603' if '0603' in fp else '0805';mpn='RC'+size+'FR-07'+rvals[val]+'L';spec=('YAGEO',mpn,'https://yageogroup.com/component-documentation/download/specsheet/'+mpn)
            if ref.startswith('C_'):
                if val.startswith('100nF'):
                    mpn='GRM188R72A104KA35D' if '0603' in fp else 'GRM21BR71H104KA01L';spec=('Murata',mpn,'https://www.murata.com/products/productdetail?partno='+mpn[:-1]+'%23')
                elif val.startswith('1uF'):
                    spec=('Murata','GRM21BR71C105KA01L','https://www.murata.com/en-us/products/productdetail?partno=GRM21BR71C105KA01%23')
                elif val.startswith('22uF'):
                    spec=('Murata','GRM31CR71A226KE15L','https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31CR71A226KE15-01.pdf')
            if ref.startswith('SW_'):spec=('Omron','B3U-1000P','https://components.omron.com/us-en/system/files/2023-01/datasheet_pdf/A162-E1.pdf')
            if ref.startswith('D_RS485PROT'):spec=('Littelfuse','SM712-02HTG','https://www.littelfuse.com/assetdocs/tvs-diode-array-spa-sm712-datasheet?assetguid=8313a28c-8802-4d47-a2a7-e30b5b1f67d8')
            if ref in ('D_PWR1','D_LED2','D_LINK1','D_FLT1'):
                mpn={'D_PWR1':'150080GS75000','D_LED2':'150080GS75000','D_LINK1':'150080YS75000','D_FLT1':'150080RS75000'}[ref];spec=('Wurth Elektronik',mpn,'https://www.we-online.com/components/products/datasheet/'+mpn+'.pdf')
            if spec:
                revised=b
                for k,v in zip(('Manufacturer','MPN','Datasheet'),spec):revised=w.set_property(revised,k,v)
                new=new.replace(b,revised)
        if new!=old:changes[path]=new
    r.patch(changes)

def geometry():
    changes={};name='TPS26600PWP_Thermal_D0.30_P0.70';path=P/'SWAFarm_Review.pretty'/(name+'.kicad_mod');text=path.read_text(encoding='utf-8')
    paste=[]
    for pad in list(r.direct_blocks(text)):
        if not pad.startswith('(pad ""'):continue
        if '(layers "F.Mask")' in pad:text=text.replace(pad,pad.replace('(size 2.66 2.46)','(size 3.3 3.3)'))
        if '(layers "F.Paste")' in pad:paste.append(pad)
    assert len(paste)==2
    replacement='(pad "" smd roundrect (at 0 0) (size 3.3 3.3) (layers "F.Paste") (roundrect_rratio 0.0151515))'
    text=text.replace(paste[0],replacement).replace(paste[1],'');changes[path]=text
    name='USB4105_GF_A_NPTH_Clearance_025';stock='USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal'
    text=(r.LIB/'footprints/Connector_USB.pretty'/(stock+'.kicad_mod')).read_text(encoding='utf-8').replace('(footprint '+r.q(stock),'(footprint '+r.q(name),1)
    for pad in list(r.direct_blocks(text)):
        if any(pad.startswith('(pad '+r.q(n)+' ') for n in ('A1','A12','B1','B12')):
            revised=pad.replace('(size 0.6 1.15)','(size 0.6 1.25)').replace('-3.68)','-3.78)').replace('(roundrect_rratio 0.25)','(roundrect_rratio 0.5)')
            assert revised!=pad;text=text.replace(pad,revised)
    changes[P/'SWAFarm_Review.pretty'/(name+'.kicad_mod')]=text
    path=P/'Power.kicad_sch';text=path.read_text(encoding='utf-8')
    for b in list(r.direct_blocks(text)):
        if b.startswith('(symbol') and '(property "Reference" "J_USB1"' in b:text=text.replace(b,w.set_property(b,'Footprint','SWAFarm_Review:'+name))
    changes[path]=text;r.patch(changes)
if __name__=='__main__':{'catalog':catalog,'passives':passives,'geometry':geometry}[sys.argv[1] if len(sys.argv)>1 else 'catalog']()
