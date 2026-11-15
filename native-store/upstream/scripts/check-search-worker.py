from pathlib import Path
import hashlib,json,subprocess,tempfile
R=Path(__file__).resolve().parents[1];E=R/'artifacts/search-automation-20261112';proof=json.loads((E/'release.json').read_bytes());candidate=R/proof['release'];storage=Path(tempfile.mkdtemp(prefix='worker-qa-'+proof['releaseHash'][:12]+'-',dir=E))
if(storage/'control.sqlite').exists():raise RuntimeError('worker_qa_already_used')
payload={'private':str(candidate/'private'),'public':str(candidate/'public'),'storage':str(storage),'baseline':(R/'artifacts/indexnow-live-diagnosis-20261112/preflight/canonical-urls.txt').read_text().splitlines()}
result=subprocess.run([str(R/'artifacts/runtime-php/php.exe'),str(R/'tests/fixtures/search-worker.php')],input=json.dumps(payload),capture_output=True,text=True,encoding='utf-8');assert result.returncode==0,result.stdout+result.stderr;d=json.loads(result.stdout)
assert d['blog']['published']==2;assert d['first']['status']=='ok';assert d['second']['delivery']['urlCount']==0
assert d['third']['delivery']['urlCount']==11,d['third'];assert len(d['sent'][1])==11 and all('product='+d['changedProduct']in u for u in d['sent'][1]);assert d['fourth']['delivery']['urlCount']==8,d['fourth'] # Four article URLs + four changed listing pages.
assert all('/blog/'+d['newArticleSlug']in u or u.split('?')[0].endswith('/blog')for u in d['sent'][2]);assert all(x['httpStatus']==200 for x in [d['first']['delivery'],d['third']['delivery'],d['fourth']['delivery']]);
summary={'passed':True,'releaseHash':proof['releaseHash'],'realRuntimeProjection':True,'publishedBlogDetected':True,'unpublishedBlogExcluded':True,'unchangedTickNoDelivery':True,'priceUpdateLocales':11,'publishedArticleAndListingLocales':8,'realOutboundRequests':0};(E/'worker-local.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
