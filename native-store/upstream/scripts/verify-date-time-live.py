"""Read-only live delivery and browser check; never authenticates or creates customer records."""
from pathlib import Path
import json,hashlib,urllib.request
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];E=R/'artifacts/date-time-20261112'
def main():
 def fetch(path):
  with urllib.request.urlopen(urllib.request.Request('https://nodenohome.com'+path,headers={'Cache-Control':'no-cache','Accept-Encoding':'identity'}),timeout=60)as response:return response.status,response.read(20000001)
 proof=json.loads((E/'release.json').read_bytes());health=json.loads(fetch('/api/health')[1]);assert health['releaseHash']==proof['releaseHash']and health['mediaReady']and health['products']==proof['publicProducts'];checks=[]
 for name in proof['changedFiles']:
  if not name.startswith('public/'):continue
  status,body=fetch('/'+name[7:]);expected=(R/proof['release']/name).read_bytes();assert status==200 and body==expected,name;checks.append({'file':name,'sha256':hashlib.sha256(expected).hexdigest()})
 with sync_playwright()as p:
  browser=p.chromium.launch(executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'),headless=True);page=browser.new_page(timezone_id='America/Los_Angeles',viewport={'width':390,'height':950});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('https://nodenohome.com/yonetim',wait_until='networkidle')
  result=page.evaluate("""async()=>{const m=await import('/date-time.js?v=20261112-r1');const rows=[];for(const country of ['TR','US','GB','DE']){localStorage.setItem('nodeno.market-country.v1',JSON.stringify(country));window.dispatchEvent(new Event('storage'));rows.push({country,date:m.formatDate('2026-11-12'),datetime:m.formatDateTime('2026-11-12T21:05:00Z'),zone:m.dateTimeSettings().timeZone});}return rows;}""")
  assert [r['date']for r in result]==['12/11/2026','11/12/2026','12/11/2026','12.11.2026'];assert result[0]['datetime']=='13/11/2026 00:05';assert not errors,errors;page.screenshot(path=str(E/'live-admin-390.png'));browser.close()
 report={'passed':True,'live':True,'releaseHash':proof['releaseHash'],'publicFilesVerified':checks,'browserCountryExamples':result,'ordersCreated':0,'chargesCreated':0,'customerDataModified':False};(E/'browser-live.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'live':True,'releaseHash':proof['releaseHash'],'files':len(checks),'countryExamples':len(result)}))
if __name__=='__main__':main()
