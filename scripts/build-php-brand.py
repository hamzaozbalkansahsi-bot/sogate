#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/build-php-brand.py
# Açıklama   : Onaylı SVG simgesinden gerçek PNG/ICO uygulama ikonlarını yerelde üretir.
import json,struct,xml.etree.ElementTree as ET
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent.parent;target=root/'public/brand/app';target.mkdir(parents=True,exist_ok=True)
ET.register_namespace('','http://www.w3.org/2000/svg')
source=ET.fromstring((root/'public/brand/symbol.svg').read_text('utf8'))
assert not any(e.tag.endswith('image') for e in source.iter()),'Raster monogram is not accepted'
def vector(maskable=False):
    mark=ET.fromstring(ET.tostring(source));mark.attrib.update({'x':'111' if maskable else '90','y':'99' if maskable else '76','width':'290' if maskable else '332','height':'314' if maskable else '360'})
    for key in ['role','aria-labelledby']:mark.attrib.pop(key,None)
    frame='' if maskable else '<path d="M35 469V220C35 -30 477 -30 477 220V469" fill="none" stroke="#E7B4BD" stroke-width="1.2" opacity=".32"/>'
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" role="img" aria-label="SEXOGATE"><defs><radialGradient id="app-bg" cx=".18" cy=".05" r="1.1"><stop stop-color="#8E0F38"/><stop offset=".55" stop-color="#5A0A20"/><stop offset="1" stop-color="#260611"/></radialGradient></defs><rect width="512" height="512" fill="url(#app-bg)"/><path d="M0 450C145 280 326 576 512 287V512H0Z" fill="#8E0F38" opacity=".22"/>'''+frame+ET.tostring(mark,encoding='unicode')+'</svg>'
for name,mask in [('app-icon.svg',False),('app-maskable.svg',True)]:
    (target/name).write_text('<!-- Proje: SEXOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN | Dosya: public/brand/app/'+name+' | Açıklama: Onaylı simgeden türetilmiş düzenlenebilir uygulama ikonu. -->\n'+vector(mask),encoding='utf8')
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True);page=browser.new_page()
    try:
        for size,name,source_name in [(16,'favicon-16.png','app-icon.svg'),(32,'favicon-32.png','app-icon.svg'),(48,'app-icon-48.png','app-icon.svg'),(180,'apple-touch-icon.png','app-icon.svg'),(192,'app-icon-192.png','app-icon.svg'),(512,'app-icon-512.png','app-icon.svg'),(512,'app-maskable-512.png','app-maskable.svg')]:
            page.set_viewport_size({'width':size,'height':size});page.goto((target/source_name).as_uri());page.evaluate('(size)=>{document.documentElement.setAttribute("width",size);document.documentElement.setAttribute("height",size)}',size);page.screenshot(path=str(target/name))
    finally:browser.close()
images=[(16,(target/'favicon-16.png').read_bytes()),(32,(target/'favicon-32.png').read_bytes())];offset=6+16*len(images);entries=[]
for size,data in images:entries.append(struct.pack('<BBBBHHII',size,size,0,0,1,32,len(data),offset));offset+=len(data)
(target/'favicon.ico').write_bytes(struct.pack('<HHH',0,1,len(images))+b''.join(entries)+b''.join(data for _,data in images))
print(json.dumps({'pngSizes':[16,32,48,180,192,512],'maskable':True,'editableSvg':True,'source':'public/brand/symbol.svg'}))
