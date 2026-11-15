"""Export role-specific native vectors without combining symbol and wordmark."""
import asyncio, base64, shutil
from pathlib import Path
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1]
async def main():
 source=R/'output/brand/nodeno-home-2026-11-12'
 word=source/'NODENO_Logo_Yatay.svg';white=source/'NODENO_Logo_Yatay_Beyaz.svg';profile=source/'NODENO_Profil.svg'
 assert b'data-logo-part="wordmark"'in word.read_bytes()and b'data-logo-part="symbol"'not in word.read_bytes()
 assert b'data-logo-part="wordmark"'not in profile.read_bytes()and b'e-accent'not in profile.read_bytes()
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'),headless=True)
  for vector,name,w,h in [(word,'social-logo.png',1096,225),(white,'social-logo-white.png',1096,225),(profile,'social-mark.png',1080,1080)]:
   encoded=base64.b64encode(vector.read_bytes()).decode();page=await browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
   await page.set_content('<html><body style="margin:0;background:transparent"><img width="'+str(w)+'" height="'+str(h)+'" src="data:image/svg+xml;base64,'+encoded+'"></body></html>')
   await page.locator('img').evaluate('(image)=>image.decode()')
   await page.screenshot(path=str(R/'web/assets/brand'/name),omit_background=True)
   await page.close()
  await browser.close()
 print('NODENO wordmark and symbol exported into their separate roles.')
if __name__=='__main__':asyncio.run(main())
