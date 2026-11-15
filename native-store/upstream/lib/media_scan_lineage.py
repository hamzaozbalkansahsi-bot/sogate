"""An unchanged combined report must still bind its exact immutable parent scan."""
import hashlib,json,re
def validate_combined_report(report,parent_index,parent_pass,read_bytes):
 lineage=report.get('scanLineage',{});ref=parent_index.get(report.get('fileSha256'))
 if not ref or lineage.get('passVersion')!=parent_pass or lineage.get('path')!=ref['path']or lineage.get('sha256')!=ref['reportSha256']or not re.fullmatch(r'artifacts/media-object-removal-20261102/web-supplemental/reports/[a-f0-9]{64}\.json',ref['path']):raise ValueError('combined scan lineage binding differs')
 body=read_bytes(ref['path'])
 if hashlib.sha256(body).hexdigest()!=ref['reportSha256']:raise ValueError('combined scan lineage parent bytes changed')
 parent=json.loads(body)
 if parent.get('fileSha256')!=report['fileSha256']or parent.get('passVersion')!=parent_pass:raise ValueError('combined scan lineage parent identity differs')
 frames=lambda v:[{k:f[k]for k in ['frame','background','rgbSha256']}for f in v['frames']]
 if frames(parent)!=frames(report):raise ValueError('combined scan lineage decoded frames differ')
 hit=lambda h:json.dumps({k:v for k,v in h.items()if k!='id'},sort_keys=True,separators=(',',':'))
 if not {hit(h)for h in parent['hits']}.issubset({hit(h)for h in report['hits']}):raise ValueError('combined scan lineage dropped a parent detection')
 return True
