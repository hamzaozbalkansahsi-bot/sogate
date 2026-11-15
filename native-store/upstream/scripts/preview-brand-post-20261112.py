"""Render an authentic three-frame NODENO carousel with native HTML/SVG."""
from pathlib import Path
import base64
import hashlib
import json
from playwright.sync_api import sync_playwright

R=Path(__file__).resolve().parents[1]
O=R/'output/social-media/2026-11-12-yeni-kimlik'
B=R/'artifacts/cpanel-release-social-copy-20261112-r2/private'

def uri(path,mime):
    return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()

def main():
    O.mkdir(parents=True,exist_ok=True)
    a=json.loads((B/'media-approved.json').read_bytes())
    cat=json.loads((B/'catalog.json').read_bytes())
    product=next(p for p in cat['products']if p['id']=='5015')
    assert '120x195x45' in product['name']['tr']
    photos={}
    provenance=[]
    for i in [1,2,5]:
        row=a['images'][a['references']['5015:'+str(i)]]
        p=R/'artifacts/social-engine-20261112/preview/media'/(row['outputSha']+'.jpg')
        assert row['state']in ['approved_unmodified','approved_cleaned']and hashlib.sha256(p.read_bytes()).hexdigest()==row['outputSha']
        photos[i]=uri(p,'image/jpeg')
        provenance.append({'index':i,'state':row['state'],'sha256':row['outputSha']})
    logo=uri(R/'output/brand/nodeno-home-2026-11-12/NODENO_Logo_Yatay.svg','image/svg+xml')
    font=uri(R/'web/assets/fonts/NODENOSans-Regular.woff','font/woff')
    bold=uri(R/'web/assets/fonts/NODENOSans-Bold.woff','font/woff')
    css='''@font-face{font-family:NODENO;src:url(FONT)}@font-face{font-family:NODENO;src:url(BOLD);font-weight:700}*{box-sizing:border-box}html,body{margin:0;width:1080px;height:1350px;overflow:hidden}body{font-family:NODENO,sans-serif;color:#292925}.frame{position:relative;width:1080px;height:1350px;background:#fff;overflow:hidden}.photo{position:absolute;width:100%;height:100%;object-fit:cover;object-position:center}.logo{position:absolute;width:238px;height:40px;right:44px;top:42px}.technical .photo{width:940px;height:940px;left:70px;top:165px;object-fit:contain}.technical .logo{top:52px}.technical h1{position:absolute;left:62px;top:48px;margin:0;font-size:34px;font-weight:400;line-height:1.3}.technical h1 small{display:block;font-size:20px;margin-top:7px;color:#69695f}.dimensions{position:absolute;inset:0;width:1080px;height:1350px}.specs{position:absolute;left:62px;right:62px;bottom:58px;display:grid;grid-template-columns:repeat(3,1fr);gap:32px;border-top:1px solid #d9d7ce;padding-top:28px}.specs span{font-size:23px;color:#6c6a60;display:block;margin-bottom:10px}.specs strong{font-size:37px;font-weight:400}.technical svg text{fill:#56584c;font-family:NODENO,sans-serif;font-size:23px}.technical svg line{stroke:#8A8249;stroke-width:1.5}'''.replace('FONT',font).replace('BOLD',bold)
    dims='''<svg class="dimensions" viewBox="0 0 1080 1350" aria-label="Genişlik 120, yükseklik 195 ve derinlik 45 santimetre"><line x1="333" y1="182" x2="741" y2="182"/><line x1="333" y1="173" x2="333" y2="196"/><line x1="741" y1="173" x2="741" y2="196"/><rect x="465" y="161" width="146" height="40" fill="white"/><text x="538" y="187" text-anchor="middle">120 cm</text><line x1="278" y1="197" x2="278" y2="1008"/><line x1="267" y1="197" x2="290" y2="197"/><line x1="267" y1="1008" x2="290" y2="1008"/><rect x="256" y="527" width="44" height="138" fill="white"/><text transform="translate(285 597) rotate(-90)" text-anchor="middle">195 cm</text></svg>'''
    bodies=[
        '<main class="frame"><img class="photo" src="'+photos[1]+'"><img class="logo" src="'+logo+'" alt="NODENO"></main>',
        '<main class="frame"><img class="photo" src="'+photos[2]+'"><img class="logo" src="'+logo+'" alt="NODENO"></main>',
        '<main class="frame technical"><h1>Lungo<small>Çok amaçlı kahve köşesi</small></h1><img class="photo" src="'+photos[5]+'"><img class="logo" src="'+logo+'" alt="NODENO">'+dims+'<div class="specs"><div><span>Genişlik</span><strong>120 cm</strong></div><div><span>Yükseklik</span><strong>195 cm</strong></div><div><span>Derinlik</span><strong>45 cm</strong></div></div></main>'
    ]
    names=['01-genel-gorunum','02-depolama-detayi','03-olculer']
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'),headless=True)
        page=b.new_page(viewport={'width':1080,'height':1350},device_scale_factor=1)
        for name,body in zip(names,bodies):
            html='<!doctype html><html lang="tr"><meta charset="utf-8"><title>NODENO Lungo</title><style>'+css+'</style>'+body+'</html>'
            (O/(name+'.html')).write_text(html,encoding='utf-8')
            page.goto((O/(name+'.html')).as_uri());page.evaluate('document.fonts.ready');page.wait_for_function('() => Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)')
            page.screenshot(path=str(O/(name+'.png')))
        board='<style>html,body{margin:0;background:#f5f2e9}.board{display:flex;gap:16px;padding:20px}img{width:384px;height:480px;display:block}</style><div class="board">'+''.join('<img src="'+uri(O/(name+'.png'),'image/png')+'">'for name in names)+'</div>'
        page.set_viewport_size({'width':1224,'height':520});page.set_content(board);page.wait_for_function('() => Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)');page.screenshot(path=str(O/'NODENO_Lungo_Kaydirmali_Gonderi.png'));b.close()
    caption='''Kahve makinesi, fincanlar ve her gün kullandığınız mutfak gereçleri için aynı yerde toplanan bir düzen. Lungo’nun açık rafları günlük kullanıma alan bırakırken, kapaklı bölmeleri göz önünde tutmak istemediğiniz eşyaları saklar.

Florida meşe görünümü ve beyaz yüzeyleriyle Lungo, 120 cm genişliğinde bir kahve köşesi sunar. İç bölmelerini ve ölçülerini görmek için görselleri kaydırabilirsiniz.

İyi tasarım. Kolay yaşam.
nodenohome.com
'''
    (O/'gonderi-aciklamasi.txt').write_text(caption,encoding='utf-8')
    (O/'preview.json').write_text(json.dumps({'previewOnly':True,'published':False,'productId':'5015','brandVersion':'reference-20261112-v2','size':[1080,1350],'frames':names,'sources':provenance,'dimensionsSource':'approved catalogue product name, 120x195x45 cm','technicalImageDimensionConflict':'Source technical line drawing at index 9 says 196 cm; not used. Primary catalogue and approved reference say 195 cm.'},indent=2)+'\n')
    print(json.dumps({'previewReady':True,'frames':len(names)}))

if __name__=='__main__':main()
