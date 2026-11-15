"""Read-only current access-log discovery. No raw visitor data is persisted."""
from pathlib import Path
from datetime import datetime, timezone
from html.parser import HTMLParser
import importlib.util
import json
import re
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/indexnow-bing-guidance-20261112'
BASE = 'https://srvc77.trwww.com:2083'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self,tag,attrs):
        values = dict(attrs)
        if tag == 'a' and 'href' in values:
            href=values['href']
            if re.search(r'getsite|getaccess|download|rawaccess|access_log',href,re.I):
                self.links.append(re.sub(r'/cpsess[0-9]+/', '/[session]/',href))


def main():
    OUT.mkdir(exist_ok=True)
    spec=importlib.util.spec_from_file_location('hosting_probe',ROOT/'scripts/hosting-probe.py')
    hosting=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hosting)
    record={'checkedAt':datetime.now(timezone.utc).isoformat(),'readOnly':True,'rawVisitorDataPersisted':False}
    apps=hosting.api('Branding','get_applications')
    app_records=[]
    def find_apps(value):
        if isinstance(value,dict):
            if isinstance(value.get('url'),str)and re.search(r'rawaccess|rawlogs|raw.*access',json.dumps(value),re.I):
                app_records.append({k:value.get(k)for k in ['itemdesc','url','group']})
            for item in value.values():find_apps(item)
        elif isinstance(value,list):
            for item in value:find_apps(item)
    find_apps(apps.get('data'))
    record['rawAccessApps']=app_records
    path=next((x['url']for x in app_records if 'raw' in x['url'].lower()),'stats/rawaccess.html')
    assert re.fullmatch(r'[A-Za-z0-9_./-]+',path)
    response=requests.get(BASE+'/frontend/jupiter/'+path,auth=hosting.credentials(),timeout=40,allow_redirects=False)
    links=Links()
    if response.status_code==200:
        links.feed(response.text)
    record['rawAccessPage']={'httpStatus':response.status_code,'downloadLinks':links.links}
    listing=hosting.api('Fileman','list_files',dir='/home/nodenoho/logs',show_hidden=1)
    record['archiveInventory']={'status':listing.get('status'),'files':[{k:x.get(k)for k in ['file','type','size','mtime']}for x in listing.get('data',[])if isinstance(x,dict)and re.search(r'nodenohome.*Nov-2026\.gz$',x.get('file',''))]}
    (OUT/'current-log-discovery.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record,ensure_ascii=True))


if __name__=='__main__':main()
