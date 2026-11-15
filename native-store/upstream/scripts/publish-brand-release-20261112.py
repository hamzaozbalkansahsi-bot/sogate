"""Publish the reviewed NODENO identity; preserve commerce and private storage."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,importlib.util,json,secrets,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/brand-refresh-20261112'

def module(name,path):
    s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def require(value,code):
    if not value:raise RuntimeError(code)

def emit(stage,**safe):print(json.dumps({'stage':stage,**safe}),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    d=module('brand_publish_backend','scripts/deploy-cpanel.py');proof=json.loads((E/'release.json').read_bytes());base=d.load_release(R/proof['base']);new=d.load_release(R/proof['release'])
    require(proof['baseReleaseHash']=='4ae93a114d896dfe6e9297a355eac9c907123d87e2a7e62b92c4235692ed9bf0','base_not_reviewed')
    require(base['manifest']['releaseHash']==proof['baseReleaseHash']and new['manifest']['releaseHash']==proof['releaseHash'],'release_changed')
    scope={'public/'+n for n in json.loads((E/'assets.json').read_bytes())['files']}|{'private/index.html','private/legal.php','private/social-media.php','private/social-campaigns.php','private/social-admin.php','public/app.js','public/admin.js','public/admin.html','public/welcome-poster.js','public/site.webmanifest'}
    delta={n for n,b in new['all_bytes'].items()if b!=base['all_bytes'].get(n)}
    require(scope==set(proof['changedFiles'])and delta==scope|{'private/release.json'},'non_brand_release_changed')
    for name in ['browser-local.json','code-review.json']:
        record=json.loads((E/name).read_bytes());require(record.get('passed')is True and record.get('releaseHash')==proof['releaseHash'],'acceptance_missing_'+name)
    media=module('brand_media_gate','scripts/verify-brand-media-20261112.py');media.verify(d,base,new,proof)
    emit('media_and_scope_verified',releaseHash=proof['releaseHash'])
    b=d.CpanelBackend(allow_writes=args.apply);require(b.public_health()['releaseHash']==proof['baseReleaseHash'],'live_base_changed');plan=d.make_plan(new,b)
    public={n[7:]:new['all_bytes'][n]for n in scope if n.startswith('public/')};b.public_paths=frozenset(public)
    originals={n:base['all_bytes']['public/'+n]for n in public}
    for n,body in originals.items():require(b.public_read(n)==body,'live_brand_base_changed')
    if not args.apply:emit('read_only_plan_verified',publicFiles=len(public));return
    checked=set()
    def upload(directory,name,body):
        pieces=name.split('/');folder=directory+('/'+'/'.join(pieces[:-1])if len(pieces)>1 else'')
        if folder not in checked:d.ensure_directory(b,folder,private=directory!=d.PUBLIC,permissions='0700'if directory!=d.PUBLIC else'0755');checked.add(folder)
        b.upload(folder,{pieces[-1]:body})
    with d.deployment_lease(b):
        require(b.public_health()['releaseHash']==proof['baseReleaseHash'],'base_changed_before_lease')
        old=d.text_content(b,d.HOME,'nodeno-runtime.php');old_private=d.HOME+'/nodeno-releases/'+proof['baseReleaseHash']+'/private';private=plan['privateRoot'];require(old.count(old_private.encode())==1,'runtime_pointer_unexpected')
        pointer=old.replace(old_private.encode(),private.encode());require(pointer.replace(private.encode(),old_private.encode())==old,'storage_configuration_changed')
        backup=d.HOME+'/nodeno-backups/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-brand-'+secrets.token_hex(4);d.ensure_directory(b,backup,private=True,permissions='0700');b.upload(backup,{'nodeno-runtime.php':old})
        require(d.text_content(b,backup,'nodeno-runtime.php')==old,'pointer_backup_failed')
        for n,body in originals.items():upload(backup+'/public',n,body)
        d.ensure_directory(b,private,private=True,permissions='0700');d.ensure_directory(b,private+'/cache',private=True,permissions='0700')
        files={n[8:]:body for n,body in new['all_bytes'].items()if n.startswith('private/')}
        for i,(n,body)in enumerate(sorted(files.items()),1):b.upload(private,{n:body});emit('private_staging',current=i,total=len(files),file=n)
        listing=d.listing(b,private);require(all(listing.get(n,{}).get('type')=='file'and int(listing[n]['size'])==len(body)for n,body in files.items()),'private_staging_size_mismatch')
        for n in ['release.json','index.html','social-media.php','social-campaigns.php','social-admin.php']:require(d.text_content(b,private,n)==files[n],'private_source_readback_failed')
        require(d.text_content(b,d.HOME,'nodeno-runtime.php')==old,'pointer_changed_during_staging')
        def switch(body):
            d.require_deployment_lease(b);ct,payload=d.multipart({'dir':d.HOME,'overwrite':'1'},{'nodeno-runtime.php':body});d.successful_upload(b.post('/execute/Fileman/upload_files',payload,ct));require(d.text_content(b,d.HOME,'nodeno-runtime.php')==body,'runtime_pointer_readback_failed')
        try:
            for n in sorted(public):upload(d.PUBLIC,n,public[n]);require(b.public_read(n)==public[n],'public_brand_readback_failed')
            switch(pointer)
            h=b.public_health();require(h['releaseHash']==proof['releaseHash']and h['products']==3602 and h['mediaReady']is True and h['checkoutEnabled']is True,'live_health_mismatch')
        except BaseException:
            switch(old)
            for n,body in originals.items():upload(d.PUBLIC,n,body)
            require(b.public_health()['releaseHash']==proof['baseReleaseHash'],'rollback_failed');raise
    record={'passed':True,'live':True,'releaseHash':proof['releaseHash'],'baseReleaseHash':proof['baseReleaseHash'],'publicFilesChanged':sorted(public),'backupRoot':backup,'cataloguePricesAndCustomerStoragePreserved':True,'ordersCreated':0,'chargesCreated':0,'socialProfilesUploaded':False}
    (E/'deployment.json').write_text(json.dumps(record,indent=2)+'\n');emit('deployment_verified',**record)

if __name__=='__main__':main()
