"""Read current hosting logs, retaining only anonymized ownership-file events."""
from pathlib import Path
import gzip, importlib.util, io, json, re
from datetime import datetime, timezone
import requests

R=Path(__file__).resolve().parents[1]
O=R/'artifacts/indexnow-live-diagnosis-20261112'
O.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('hosting',R/'scripts/hosting-probe.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
key=json.loads((R/'data/seo-indexnow.json').read_bytes())
result={'checkedAt':datetime.now(timezone.utc).isoformat(),'sources':[]}
for suffix,prefix in [('', '/getaccesslog/accesslog_'),('-ssl_log','/getsslaccesslog/sslaccesslog_')]:
    url='https://srvc77.trwww.com:2083'+prefix+'nodenohome.com.tr_11_12_2026.gz'
    response=requests.get(url,auth=h.credentials(),timeout=(20,45))
    record={'source':'current'+suffix,'httpStatus':response.status_code,'bytes':len(response.content),'ownershipEvents':[]}
    body=response.content
    if body.startswith(b'\x1f\x8b'):
        body=gzip.decompress(body)
    if response.status_code==200 and not body.lstrip().startswith(b'<'):
        lines=body.decode('utf-8','replace').splitlines()
        record['lineCount']=len(lines)
        record['lastLogTimestamp']=next((re.search(r'\[([^]]+)\]',x).group(1) for x in reversed(lines) if re.search(r'\[([^]]+)\]',x)),None)
        for line in lines:
            if key['key']+'.txt' in line or (re.search(r'/[a-f0-9]{32}\.txt',line)):
                match=re.search(r'\[([^]]+)\] "([^"]+)" (\d+) (\S+).*?"([^"]*)" "([^"]*)"',line)
                if match:
                    record['ownershipEvents'].append(dict(zip(['time','request','status','responseBytes','referer','userAgent'],match.groups())))
    result['sources'].append(record)
(O/'current-accesslog.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=True))
