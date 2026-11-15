"""Export clean native vector lettering. Never trace a screenshot's pixels."""
from pathlib import Path
import base64,hashlib,json,shutil,xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

R=Path(__file__).resolve().parents[1]
O=R/'output/brand/nodeno-home-2026-11-13'
S=R/'output/social-media/current'
VERSION='smooth-vector-20261113-v4'

def save(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(b.encode('utf-8')if isinstance(b,str)else b);t.replace(p)

def uri(p,mime='image/svg+xml'):
    return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()

def svg(w,h,body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" data-brand-version="{VERSION}"><title>NODENO</title>{body}</svg>'

N='M3 0H14L69 74V3Q69 0 72 0H81Q84 0 84 3V97Q84 100 81 100H70L15 26V97Q15 100 12 100H3Q0 100 0 97V3Q0 0 3 0Z'
OVAL='M48.5 0C75.286 0 97 22.386 97 50S75.286 100 48.5 100 0 77.614 0 50 21.714 0 48.5 0ZM48.5 14C29.446 14 14 30.118 14 50S29.446 86 48.5 86 83 69.882 83 50 67.554 14 48.5 14Z'
D='M3 0H34C66 0 86 19 86 50S66 100 34 100H3Q0 100 0 97V3Q0 0 3 0ZM15 14V86H34C57 86 71 73 71 50S57 14 34 14Z'
E='M2 40H72V54H15V86H72V100H2Q0 100 0 98V42Q0 40 2 40Z'

def letters(color):
    body=''.join(f'<path fill="{color}" fill-rule="evenodd" transform="translate({x} 0)" d="{p}"/>'for x,p in [(0,N),(101,OVAL),(213,D),(314,E),(400,N),(501,OVAL)])
    return body+'<path data-logo-part="e-accent" fill="#8A8249" d="M314 0H386V13H314Z"/>'

def main():
    O.mkdir(parents=True,exist_ok=True)
    for color,suffix in [('#292925',''),('#FFFFFF','_Beyaz')]:
        save(O/f'NODENO_Logo_Yatay{suffix}.svg',svg(620,124,'<g transform="translate(11 12)">'+letters(color)+'</g>'))
    for color,suffix in [('#292925',''),('#FFFFFF','-white')]:
        save(R/f'web/assets/brand/logo-horizontal{suffix}.svg',svg(1600,360,'<g transform="translate(45 54) scale(2.52)">'+letters(color)+'</g>'))
    save(R/'web/wordmark.svg',svg(1400,250,'<g transform="translate(43 15) scale(2.2)">'+letters('#292925')+'</g>'))
    old=ET.fromstring((R/'web/assets/brand/logo-with-slogan.svg').read_bytes())
    slogan=ET.tostring(list(old)[-1],encoding='unicode').replace('ns0:','').replace(':ns0','')
    save(R/'web/assets/brand/logo-with-slogan.svg',svg(1600,460,'<g transform="translate(45 24) scale(2.52)">'+letters('#292925')+'</g>'+slogan))
    # Keep the already approved original symbol for small circular profiles.
    save(O/'NODENO_Profil.svg',(R/'web/favicon.svg').read_bytes())
    font=uri(R/'web/assets/fonts/NODENOSans-Regular.woff','font/woff')
    def cover(w,h,x,y,lw,fs=26,details=True):
        scale=lw/598
        copy=f'<text x="{x+lw/2}" y="{y+100*scale+fs*1.8}" text-anchor="middle" font-size="{fs}">İyi tasarım. Kolay yaşam.</text>'
        if details:copy+=f'<text x="{x+lw/2}" y="{y+100*scale+fs*3.4}" text-anchor="middle" font-size="{fs*.8}">Mobilya, kapı, dolap kapağı ve yardımcı ürünler</text><text x="{x+lw/2}" y="{y+100*scale+fs*4.9}" text-anchor="middle" font-size="{fs*.8}">nodenohome.com</text>'
        return svg(w,h,f'<defs><style>@font-face{{font-family:NODENO;src:url({font})}}text{{font-family:NODENO,sans-serif;fill:#292925}}</style></defs><rect width="{w}" height="{h}" fill="#F5F2E9"/><g transform="translate({x} {y}) scale({scale})">'+letters('#292925')+'</g>'+copy)
    specs=[('NODENO_X_Kapak',1500,500,330,85,930,27,True),('NODENO_Kapak_1640x624',1640,624,390,120,960,30,True),('NODENO_LinkedIn_Kapak',1128,191,350,32,560,20,False),('NODENO_YouTube_Kapak',2560,1440,780,570,1000,30,True),('NODENO_Pinterest_Kapak',1600,900,320,260,960,32,True)]
    for name,w,h,x,y,lw,fs,details in specs:save(O/(name+'.svg'),cover(w,h,x,y,lw,fs,details))
    save(O/'NODENO_Share_Cover.svg',cover(1200,630,180,150,840,26,True))
    with sync_playwright()as p:
        b=p.chromium.launch(executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'),headless=True)
        def raster(src,dest,w,h):
            page=b.new_page(viewport={'width':w,'height':h});page.set_content('<style>body{margin:0;background:transparent}img{display:block}</style><img width="'+str(w)+'" height="'+str(h)+'" src="'+uri(src)+'">');page.evaluate('document.fonts.ready');page.wait_for_function('()=>document.images[0].complete&&document.images[0].naturalWidth>0');page.screenshot(path=str(dest),omit_background=True);page.close()
        raster(O/'NODENO_Profil.svg',O/'NODENO_Profil_1080.png',1080,1080)
        for suffix in ['','_Beyaz']:raster(O/f'NODENO_Logo_Yatay{suffix}.svg',O/f'NODENO_Logo_Yatay{suffix}.png',2480,496)
        for name,w,h,*_ in specs:raster(O/(name+'.svg'),O/(name+'.png'),w,h)
        raster(O/'NODENO_Logo_Yatay.svg',R/'web/assets/brand/social-logo.png',1240,248)
        raster(O/'NODENO_Logo_Yatay_Beyaz.svg',R/'web/assets/brand/social-logo-white.png',1240,248)
        page=b.new_page(viewport={'width':1200,'height':630});page.set_content('<style>body{margin:0}</style><img width="1200" height="630" src="'+uri(O/'NODENO_Share_Cover.svg')+'">');page.wait_for_function('()=>document.images[0].complete&&document.images[0].naturalWidth>0');page.screenshot(path=str(R/'web/assets/brand/share-cover.jpg'),type='jpeg',quality=95);page.close()
        b.close()
    save(O/'NODENO_Kapak.svg',(O/'NODENO_Kapak_1640x624.svg').read_bytes())
    save(O/'NODENO_Sosyal_Yazi_Beyaz.png',(O/'NODENO_Logo_Yatay_Beyaz.png').read_bytes())
    save(O/'NODENO_Sembol.svg',(R/'web/brand.svg').read_bytes())
    for p in O.iterdir():
        if p.is_file()and p.name!='manifest.json':shutil.copyfile(p,S/p.name)
    # The historical dated package is retained; active consumer uses these aliases.
    for suffix in ['','_Beyaz']:shutil.copyfile(O/f'NODENO_Logo_Yatay{suffix}.svg',R/f'output/brand/nodeno-home-2026-11-12/NODENO_Logo_Yatay{suffix}.svg')
    brand=json.loads((R/'data/brand.json').read_bytes());brand['identity']['version']=VERSION
    save(R/'data/brand.json',json.dumps(brand,ensure_ascii=False,indent=2)+'\n');save(S/'identity.json',json.dumps(brand,ensure_ascii=False,indent=2)+'\n')
    manifest=json.loads((R/'data/brand-assets.json').read_bytes())
    for n in ['assets/brand/logo-horizontal.svg','assets/brand/logo-horizontal-white.svg','assets/brand/logo-with-slogan.svg','wordmark.svg','assets/brand/social-logo.png','assets/brand/social-logo-white.png','assets/brand/share-cover.jpg']:
        data=(R/'web'/n).read_bytes();save(O/'web'/n,data)
        for row in manifest:
            if row['published']==n:row.update(sha256=hashlib.sha256(data).hexdigest().upper(),bytes=len(data),source=(O/'web'/n).relative_to(R).as_posix(),identityVersion=VERSION)
    save(R/'data/brand-assets.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    save(O/'manifest.json',json.dumps({'version':VERSION,'nativeVector':True,'pixelTracing':False,'avatar':'symbol_only','cover':'wordmark_only','files':{p.relative_to(O).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in O.rglob('*')if p.is_file()and p.name!='manifest.json'}},indent=2)+'\n')
    shutil.copyfile(O/'manifest.json',S/'manifest.json')
    print(json.dumps({'ready':True,'version':VERSION,'folder':str(O)}))

if __name__=='__main__':main()
