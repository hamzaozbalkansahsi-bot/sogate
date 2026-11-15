"""Symbol-only avatars; wordmark-only horizontal spaces, per user instruction."""
from pathlib import Path
import base64,copy,hashlib,json,shutil,xml.etree.ElementTree as ET
from PIL import Image
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'output/brand/nodeno-home-2026-11-12';S=R/'output/social-media/current';E=R/'artifacts/social-refresh-20261112';NS='{http://www.w3.org/2000/svg}';VERSION='roles-20261112-v3'

def svg(w,h,body):return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" data-brand-version="{VERSION}"><title>NODENO</title>{body}</svg>'
def save(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(s.encode()if isinstance(s,str)else s);t.replace(p)
def uri(p):return 'data:image/svg+xml;base64,'+base64.b64encode(p.read_bytes()).decode()

def main():
 E.mkdir(exist_ok=True)
 master=O/'NODENO_Tam_Logo_Referans.svg'
 if not master.exists():shutil.copyfile(O/'NODENO_Logo_Yatay.svg',master)
 tree=ET.fromstring(master.read_bytes());word=next(n for n in tree.iter()if n.attrib.get('data-logo-part')=='wordmark');accent=next(n for n in tree.iter()if n.attrib.get('data-logo-part')=='e-accent')
 def paths(color):return '<path data-logo-part="wordmark" fill="'+color+'" fill-rule="evenodd" d="'+word.attrib['d']+'"/><path data-logo-part="e-accent" fill="#8A8249" d="'+accent.attrib['d']+'"/>'
 for color,suffix in [('#292925',''),('#FFFFFF','_Beyaz')]:save(O/f'NODENO_Logo_Yatay{suffix}.svg',svg(448,92,'<g transform="translate(-99 8)">'+paths(color)+'</g>'))
 for color,suffix in [('#292925',''),('#FFFFFF','-white')]:save(R/f'web/assets/brand/logo-horizontal{suffix}.svg',svg(1600,360,'<g transform="translate(-268 45) scale(3.349)">'+paths(color)+'</g>'))
 save(R/'web/wordmark.svg',svg(1400,250,'<g transform="translate(-248 12) scale(3.05)">'+paths('#292925')+'</g>'))
 # Retain the existing vector slogan, replacing only the full logo group.
 slogan=ET.fromstring((R/'web/assets/brand/logo-with-slogan.svg').read_bytes());groups=list(slogan);slogan_group=ET.tostring(groups[-1],encoding='unicode').replace('ns0:','').replace(':ns0','')
 save(R/'web/assets/brand/logo-with-slogan.svg',svg(1600,460,'<g transform="translate(-268 20) scale(3.349)">'+paths('#292925')+'</g>'+slogan_group))
 for name in ['brand.svg','favicon.svg']:
  body=(R/'web'/name).read_text(encoding='utf-8').replace('reference-20261112-v2',VERSION)
  save(R/'web'/name,body)
 profile=(R/'web/favicon.svg').read_text(encoding='utf-8');save(O/'NODENO_Profil.svg',profile)
 def cover(w,h,logo_width):
  return svg(w,h,f'<rect width="{w}" height="{h}" fill="#F5F2E9"/><image x="{(w-logo_width)/2}" y="{(h-logo_width*92/448)/2}" width="{logo_width}" height="{logo_width*92/448}" href="'+uri(O/'NODENO_Logo_Yatay.svg')+'"/>')
 specs=[('NODENO_Kapak_1640x624',1640,624,1120),('NODENO_LinkedIn_Kapak',1128,191,610),('NODENO_YouTube_Kapak',2560,1440,1250)]
 for name,w,h,lw in specs:save(O/(name+'.svg'),cover(w,h,lw))
 save(O/'NODENO_Kapak.svg',(O/'NODENO_Kapak_1640x624.svg').read_bytes())
 save(E/'share-cover.svg',cover(1200,630,850))
 with sync_playwright()as p:
  b=p.chromium.launch(executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'),headless=True)
  def raster(src,dest,w,h,transparent=True):
   page=b.new_page(viewport={'width':w,'height':h});page.set_content('<style>body{margin:0;background:transparent}img{display:block}</style><img width="'+str(w)+'" height="'+str(h)+'" src="'+uri(src)+'">');page.wait_for_function('()=>document.images[0].complete&&document.images[0].naturalWidth>0');page.screenshot(path=str(dest),omit_background=transparent);page.close()
  raster(O/'NODENO_Profil.svg',O/'NODENO_Profil_1080.png',1080,1080,False)
  for suffix in ['','_Beyaz']:raster(O/f'NODENO_Logo_Yatay{suffix}.svg',O/f'NODENO_Logo_Yatay{suffix}.png',1792,368)
  raster(O/'NODENO_Logo_Yatay.svg',R/'web/assets/brand/social-logo.png',1096,225)
  raster(O/'NODENO_Logo_Yatay_Beyaz.svg',R/'web/assets/brand/social-logo-white.png',1096,225)
  shutil.copyfile(R/'web/assets/brand/social-logo-white.png',O/'NODENO_Sosyal_Yazi_Beyaz.png')
  for name,w,h,lw in specs:raster(O/(name+'.svg'),O/(name+'.png'),w,h,False)
  raster(E/'share-cover.svg',E/'share-cover.png',1200,630,False)
  for name,w,h,lw in specs:
   # Replace old HTML previews as well; they contained embedded combined marks.
   if name in ['NODENO_LinkedIn_Kapak','NODENO_YouTube_Kapak']:
    save(O/(name+'.html'),'<meta charset="utf-8"><style>body{margin:0;background:#F5F2E9}</style><img width="'+str(w)+'" height="'+str(h)+'" src="'+uri(O/(name+'.svg'))+'">')
  raster(R/'web/assets/brand/logo-horizontal.svg',E/'wordmark-website.png',800,180)
  b.close()
 Image.open(E/'share-cover.png').convert('RGB').save(R/'web/assets/brand/share-cover.jpg',quality=94)
 shutil.copyfile(O/'NODENO_Profil_1080.png',R/'web/assets/brand/social-mark.png')
 for p in O.iterdir():
  if p.is_file()and p.name.startswith('NODENO_')and p.suffix in ['.png','.svg']and p.name!='NODENO_Tam_Logo_Referans.svg':shutil.copyfile(p,S/p.name)
 combined_current=S/'NODENO_Tam_Logo_Referans.svg'
 if combined_current.exists():
  archive=E/'historical-combined-reference.svg'
  if not archive.exists():shutil.copyfile(combined_current,archive)
  # Only this exact reference file moves out of the active delivery folder.
  assert combined_current.resolve().parent==S.resolve()
  combined_current.replace(E/'combined-reference-not-for-active-use.svg')
 brand=json.loads((R/'data/brand.json').read_bytes());brand['identity'].update(version=VERSION,usage={'profile':'symbol_only','favicon':'symbol_only','banner':'wordmark_only','horizontal':'wordmark_only','productSignature':'wordmark_only'});save(R/'data/brand.json',json.dumps(brand,ensure_ascii=False,indent=2)+'\n');save(S/'identity.json',json.dumps(brand,ensure_ascii=False,indent=2)+'\n');save(O/'identity.json',json.dumps(brand,ensure_ascii=False,indent=2)+'\n')
 manifest=json.loads((R/'data/brand-assets.json').read_bytes())
 changed=['assets/brand/logo-horizontal.svg','assets/brand/logo-horizontal-white.svg','assets/brand/logo-with-slogan.svg','wordmark.svg','brand.svg','favicon.svg','assets/brand/social-logo.png','assets/brand/social-logo-white.png','assets/brand/social-mark.png','assets/brand/share-cover.jpg']
 for n in changed:
  data=(R/'web'/n).read_bytes();dest=O/'web'/n;save(dest,data)
  matches=[row for row in manifest if row['published']==n]
  if not matches:
   matches=[{'published':n}];manifest.extend(matches)
  for row in matches:row.update(sha256=hashlib.sha256(data).hexdigest().upper(),bytes=len(data),source=dest.relative_to(R).as_posix(),identityVersion=VERSION)
 save(R/'data/brand-assets.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');save(O/'brand-assets.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 save(E/'logo-role-assets.json',json.dumps({'version':VERSION,'changedWebAssets':changed,'avatar':'symbol_only','cover':'wordmark_only'},indent=2)+'\n')
 print(json.dumps({'ready':True,'avatar':'symbol_only','cover':'wordmark_only','webAssets':len(changed)}))

if __name__=='__main__':main()
