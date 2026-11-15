"""Refresh the local IPv4/IPv6 country index. No visitor IPs leave the host.

Data: DB-IP Country Lite, CC BY 4.0. Attribution is displayed in the store footer.
Usage: python scripts/update-country-db.py --month YYYY-MM
"""
import argparse,csv,gzip,hashlib,io,ipaddress,json,tempfile,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--month',required=True);args=parser.parse_args()
 import re
 if not re.fullmatch(r'20\d{2}-(0[1-9]|1[0-2])',args.month):raise SystemExit('Invalid month')
 url=f'https://download.db-ip.com/free/dbip-country-lite-{args.month}.csv.gz'
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 NODENO/1.0'}),timeout=60) as response:raw=response.read(12_000_001)
 if len(raw)>12_000_000 or not raw.startswith(b'\x1f\x8b'):raise SystemExit('Invalid database response')
 buffers={4:io.BytesIO(),6:io.BytesIO()};counts={4:0,6:0};previous={4:-1,6:-1}
 for row in csv.reader(io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(raw)),encoding='utf-8')):
  start,end,code=row;first=ipaddress.ip_address(start);last=ipaddress.ip_address(end);v=first.version
  if last.version!=v or int(first)<=previous[v] or int(last)<int(first) or not re.fullmatch('[A-Z]{2}',code):raise SystemExit('Invalid/overlapping country range')
  buffers[v].write(first.packed+last.packed+code.encode('ascii'));previous[v]=int(last);counts[v]+=1
 if counts[4]<100_000 or counts[6]<100_000:raise SystemExit('Incomplete country database')
 target=ROOT/'data/geo';target.mkdir(parents=True,exist_ok=True);files={}
 for v,buffer in buffers.items():
  name=f'geo-v{v}.bin';data=buffer.getvalue();files[name]={'sha256':hashlib.sha256(data).hexdigest(),'records':counts[v],'bytes':len(data)}
  stage=target/(name+'.tmp');stage.write_bytes(data);stage.replace(target/name)
 manifest={'schema':1,'provider':'DB-IP Country Lite','month':args.month,'source':url,'sourceSha256':hashlib.sha256(raw).hexdigest(),'license':'CC-BY-4.0','licenseUrl':'https://creativecommons.org/licenses/by/4.0/','attributionUrl':'https://db-ip.com','files':files}
 (target/'geo-license.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8');print(json.dumps({'month':args.month,'records':counts,'bytes':sum(f['bytes'] for f in files.values())}))
if __name__=='__main__':main()
