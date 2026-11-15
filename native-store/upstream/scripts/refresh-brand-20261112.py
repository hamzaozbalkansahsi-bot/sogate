"""Rebuild editable NODENO artwork from the user's approved logo reference.

The original N symbol is retained. Reference wordmark contours become vector
paths; no font substitution, image generation or product-photo retouching.
"""
from pathlib import Path
import base64
import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET

import cv2
import numpy as np
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from playwright.sync_api import sync_playwright

R = Path(__file__).resolve().parents[1]
E = R / 'artifacts/brand-refresh-20261112'
O = R / 'output/brand/nodeno-home-2026-11-12'
REFERENCE = Path('C:/Users/HAMZAZ~1/AppData/Local/Temp/codex-clipboard-38299a27-7140-4815-bda4-49c86c6a2296.png')
VERSION = 'reference-20261112-v2'
INK = '#292925'
OLIVE = '#8A8249'
NS = '{http://www.w3.org/2000/svg}'


def save(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(body, str):
        body = body.encode('utf-8')
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_bytes(body)
    temporary.replace(path)


def uri(path, mime):
    return 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode()


def svg(width, height, content):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" data-brand-version="{VERSION}"><title>NODENO</title>{content}</svg>\n'


def lettering(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    paths = []
    for contour in contours:
        if cv2.contourArea(contour) < 1:
            continue
        points = cv2.approxPolyDP(contour, 0.17, True).reshape(-1, 2)
        paths.append('M' + ' L'.join(f'{x-49},{y-35}' for x, y in points) + ' Z')
    return ' '.join(paths)


def slogan_paths(text):
    font = TTFont(R/'web/assets/fonts/NODENOSans-Regular.woff')
    cmap = font.getBestCmap()
    glyphs = font.getGlyphSet()
    cursor = 0
    parts = []
    for ch in text:
        name = cmap[ord(ch)]
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        parts.append(f'<path transform="translate({cursor} 0)" d="{pen.getCommands()}"/>')
        cursor += font['hmtx'][name][0]
    return ''.join(parts), cursor


def main():
    # The later user decision on logo roles supersedes the initial combined
    # reference. Keep this legacy entry point safe for future rebuilds.
    current_brand = json.loads((R/'data/brand.json').read_bytes())
    if current_brand.get('identity',{}).get('usage',{}).get('horizontal') == 'wordmark_only':
        import runpy
        runpy.run_path(str(R/'scripts/apply-logo-roles-20261112.py'),run_name='__main__')
        return
    E.mkdir(exist_ok=True)
    O.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REFERENCE, O/'onayli-logo-referansi.png')
    files = ['assets/brand/logo-horizontal.svg', 'assets/brand/logo-horizontal-white.svg',
             'assets/brand/logo-with-slogan.svg', 'wordmark.svg', 'brand.svg', 'favicon.svg',
             'favicon.ico', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png',
             'maskable-512.png', 'assets/brand/share-cover.jpg',
             'assets/brand/social-logo.png', 'assets/brand/social-mark.png']
    for name in files:
        original = R/'web'/name
        backup = E/'before'/name
        if original.exists() and not backup.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, backup)
    old = ET.fromstring((E/'before/assets/brand/logo-horizontal.svg').read_bytes())
    symbol = old.find('.//' + NS + 'path').attrib['d']
    pixels = np.array(Image.open(REFERENCE).convert('RGB'))[70:205, 1420:2040]
    ink = (np.max(np.abs(pixels.astype(int)-[41,41,37]),axis=2)<60).astype('uint8')*255
    ink[:, :150] = 0
    word = lettering(ink)
    olive = (np.max(np.abs(pixels.astype(int)-[138,130,73]),axis=2)<38).astype('uint8')*255
    olive[:30,:]=0
    olive[58:,:]=0
    olive[:,:370]=0
    olive[:,435:]=0
    # The accent is a detached, straight bar, rather than a coloured full E.
    ys, xs = np.where(olive > 0)
    assert 375 <= xs.min() <= 382 and 420 <= xs.max() <= 430
    accent = '<path data-logo-part="e-accent" fill="'+OLIVE+'" d="M330,4 H377 V16 H330 Z"/>'

    def mark(color=INK):
        return f'<g data-logo-part="symbol" fill="{color}" transform="scale(0.08862)"><path d="{symbol}"/></g><path data-logo-part="wordmark" fill="{color}" fill-rule="evenodd" d="{word}"/>{accent}'

    tight = svg(548, 92, '<g transform="translate(8 8)">'+mark()+'</g>')
    save(O/'NODENO_Logo_Yatay.svg', tight)
    save(O/'NODENO_Logo_Yatay_Beyaz.svg', svg(548,92,'<g transform="translate(8 8)">'+mark('#FFFFFF')+'</g>'))
    for color, suffix in [(INK,''),('#FFFFFF','-white')]:
        save(R/f'web/assets/brand/logo-horizontal{suffix}.svg', svg(1600,360,'<g transform="translate(90 78) scale(2.66917)">'+mark(color)+'</g>'))
    save(R/'web/wordmark.svg', svg(1400,250,'<g transform="translate(-248 12) scale(3.05)"><path fill="'+INK+'" fill-rule="evenodd" d="'+word+'"/>'+accent+'</g>'))
    text, text_width = slogan_paths('İyi tasarım. Kolay yaşam.')
    save(R/'web/assets/brand/logo-with-slogan.svg', svg(1600,460,'<g transform="translate(90 60) scale(2.66917)">'+mark()+'</g><g fill="'+INK+'" transform="translate(90 382) scale('+str(1080/text_width)+' '+str(-1080/text_width)+')">'+text+'</g>'))
    symbol_body = f'<path fill="{INK}" transform="translate(220 231) scale(0.67)" d="{symbol}"/>'
    save(R/'web/brand.svg', svg(1024,1024,symbol_body))
    app_icon = svg(1024,1024,'<rect width="1024" height="1024" fill="#F5F2E9"/>'+symbol_body)
    save(R/'web/favicon.svg', app_icon)
    save(O/'NODENO_Sembol.svg', svg(1024,1024,symbol_body))
    save(O/'NODENO_Profil.svg', svg(1080,1080,'<rect width="1080" height="1080" fill="#F5F2E9"/><g transform="translate(108 476) scale(1.624)">'+mark()+'</g>'))
    save(O/'NODENO_Kapak.svg', svg(1640,624,'<rect width="1640" height="624" fill="#F5F2E9"/><g transform="translate(235 210) scale(2.2)">'+mark()+'</g><g fill="'+INK+'" transform="translate(385 406) scale('+str(870/text_width)+' '+str(-870/text_width)+')">'+text+'</g>'))

    executable = Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(executable),headless=True)
        def raster(source, target, width, height, transparent=True):
            page = browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
            page.set_content('<style>html,body{margin:0;background:transparent}img{display:block}</style><img width="'+str(width)+'" height="'+str(height)+'" src="'+uri(source,'image/svg+xml')+'">')
            page.wait_for_function('() => document.images[0].complete && document.images[0].naturalWidth > 0')
            page.screenshot(path=str(target),omit_background=transparent)
            page.close()
        raster(O/'NODENO_Logo_Yatay.svg',R/'web/assets/brand/social-logo.png',1096,184)
        raster(O/'NODENO_Logo_Yatay.svg',O/'NODENO_Logo_Yatay.png',2192,368)
        raster(O/'NODENO_Logo_Yatay_Beyaz.svg',O/'NODENO_Logo_Yatay_Beyaz.png',2192,368)
        raster(O/'NODENO_Profil.svg',O/'NODENO_Profil_1080.png',1080,1080,False)
        raster(O/'NODENO_Kapak.svg',O/'NODENO_Kapak_1640x624.png',1640,624,False)
        for path,size in [('apple-touch-icon.png',180),('icon-192.png',192),('icon-512.png',512),('maskable-512.png',512)]:
            raster(R/'web/favicon.svg',R/'web'/path,size,size,False)
        raster(R/'web/favicon.svg',E/'favicon-256.png',256,256,False)
        raster(R/'web/assets/brand/logo-horizontal.svg',E/'website-logo.png',800,180)
        raster(O/'NODENO_Kapak.svg',E/'share-cover.png',1200,630,False)
        browser.close()
    # ICO/JPEG are format exports of the exact rendered native artwork.
    Image.open(E/'favicon-256.png').save(R/'web/favicon.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    Image.open(E/'share-cover.png').convert('RGB').save(R/'web/assets/brand/share-cover.jpg',quality=94)
    shutil.copyfile(O/'NODENO_Profil_1080.png',R/'web/assets/brand/social-mark.png')
    brand=json.loads((R/'data/brand.json').read_bytes())
    brand['identity']={'version':VERSION,'ink':INK,'accent':OLIVE,'reference':'output/brand/nodeno-home-2026-11-12/onayli-logo-referansi.png','description':'İnce kelime logosu; E harfinin ayrık üst çizgisi zeytin tonunda. Özgün N sembolü korunur.'}
    save(R/'data/brand.json',json.dumps(brand,ensure_ascii=False,indent=2)+'\n')
    assets=json.loads((R/'data/brand-assets.json').read_bytes())
    for item in assets:
        if item['published'] not in files:
            continue
        data=(R/'web'/item['published']).read_bytes()
        item.update(sha256=hashlib.sha256(data).hexdigest().upper(),bytes=len(data),source='output/brand/nodeno-home-2026-11-12/'+Path(item['published']).name,identityVersion=VERSION)
    save(R/'data/brand-assets.json',json.dumps(assets,ensure_ascii=False,indent=2)+'\n')
    save(E/'assets.json',json.dumps({'version':VERSION,'sourceReferenceSha256':hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),'ink':INK,'accent':OLIVE,'files':files,'originalSymbolPreserved':True,'socialProfilesUploaded':False},indent=2)+'\n')
    print(json.dumps({'saved':True,'version':VERSION,'assets':len(files),'output':O.relative_to(R).as_posix()}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
