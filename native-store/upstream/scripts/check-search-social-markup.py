from pathlib import Path
import argparse,json,os,socket,subprocess
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];E=R/'artifacts/search-automation-20261112'
def main():
 p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');a=p.parse_args();proof=json.loads((E/'release.json').read_bytes());server=None;log=None
 if a.live:base='https://nodenohome.com'
 else:
  q=E/('qa-'+proof['releaseHash'][:12]);public=q/'public';assert public.exists()
  with socket.socket()as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
  log=(q/'social-markup-php.log').open('w');server=subprocess.Popen([str(R/'artifacts/runtime-php/php.exe'),'-S','127.0.0.1:'+str(port),'-t',str(public),str(R/'hosting/dev-router.php')],env={**os.environ,'NODENO_TEST_PUBLIC':str(public),'NODENO_TEST_HTTPS':'loopback-tls-only'},stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);base='http://127.0.0.1:'+str(port)
 try:
  expected=[x['url']for x in json.loads((R/'data/brand.json').read_bytes())['socials']]
  with sync_playwright()as p:
   browser=p.chromium.launch(executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'),headless=True);page=browser.new_page(viewport={'width':390,'height':900});response=page.goto(base+'/?lang=tr',wait_until='networkidle');assert response.status==200
   page.wait_for_function("() => [...document.querySelectorAll('script[type=\"application/ld+json\"]')].flatMap(s=>JSON.parse(s.textContent)).some(x=>x['@type']==='Organization'&&x.sameAs?.length===7)")
   found=page.evaluate("() => [...document.querySelectorAll('script[type=\"application/ld+json\"]')].flatMap(s=>JSON.parse(s.textContent)).find(x=>x['@type']==='Organization').sameAs");assert found==expected
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(E/('social-markup-'+('live'if a.live else'local')+'.png')),full_page=False);browser.close()
  report={'passed':True,'live':a.live,'releaseHash':proof['releaseHash'],'afterBrowserRendering':True,'socialProfileCount':7,'sameAs':found};(E/('social-markup-live.json'if a.live else'social-markup-local.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
 finally:
  if server:server.terminate();server.wait(timeout=10)
  if log:log.close()
if __name__=='__main__':main()
