"""Verify unchanged live media without publishing concurrent catalogue work."""
from pathlib import Path
import copy,hashlib,importlib.util,json,os,subprocess
R=Path(__file__).resolve().parents[1];E=R/'artifacts/brand-refresh-20261112'

def verify(d,base,candidate,proof):
    # This gate is exclusively for an asset-only delta from the audited live
    # release. Every catalogue, approval and photo byte must still equal base.
    previous=json.loads((R/'artifacts/social-copy-20261112/media.json').read_bytes())
    assert previous['passed']is True and previous['releaseHash']==base['manifest']['releaseHash']
    names=[n for n in base['all_bytes']if n.startswith(('private/catalog','private/media','private/supplier-','private/door-catalog','private/cabinet-fronts','public/assets/suppliers/','public/assets/doors/','public/assets/fronts/'))]
    assert all(candidate['all_bytes'][n]==base['all_bytes'][n]for n in names)
    cleanup_path=R/'artifacts/media-cleanup.json';cleanup=json.loads(cleanup_path.read_bytes());audit=json.loads((R/'artifacts/measurement-orders/full-media-audit.json').read_bytes())
    assert cleanup['publicationReady']is True and not cleanup.get('testOnly')
    assert audit['passed']is True and audit['sourceReportSha256']==d.sha256(cleanup_path.read_bytes())and audit['mediaVersion']==candidate['manifest']['mediaVersion']
    assert all(d.sha256(candidate['all_bytes'][n])==digest for n,digest in audit['files'].items())
    for i,row in enumerate(cleanup['images'].values(),1):
        for field,digest,folder in [('sourcePath','sourceSha','media-originals'),('path','outputSha','media-cleaned')]:
            path=R/row[field];assert not path.is_symlink()and path.resolve().is_relative_to((R/'artifacts'/folder).resolve())and d.sha256(path.read_bytes())==row[digest]
        if i%1000==0:print(json.dumps({'stage':'media_hash_progress','verified':i,'total':len(cleanup['images'])}),flush=True)
    projection=json.loads((R/'data/supplier-storefront.json').read_bytes())
    assert projection['publicationReady']is True and not projection.get('testOnly')
    old_products=[p for p in json.loads(base['all_bytes']['private/catalog.json'])['products']if p.get('productType')=='supplier-item']
    current={p['id']:p for p in projection['products']}
    for old in old_products:
        row=copy.deepcopy(current[old['id']])
        for key in ['finishState','paintSurface']:
            if key not in old:row.pop(key,None)
        assert row==old,'Existing live supplier product changed; separate catalogue review required'
    # Reconstruct the exact previously approved projection as a private
    # validation input. Added products and unpublished finish metadata are
    # excluded, while the original validator and visual checks remain intact.
    reviewed=copy.deepcopy(projection);reviewed['products']=old_products
    for filename,key in [('supplier-media-approved.json','mediaSha256'),('supplier-details.json','detailIndexSha256'),('supplier-details.bin','detailBlobSha256')]:reviewed[key]=d.sha256(base['all_bytes']['private/'+filename])
    shadow=E/'approved-live-inputs';(shadow/'data').mkdir(parents=True,exist_ok=True)
    for row in reviewed['review']['files']:
        source=R/row['path'];assert d.sha256(source.read_bytes())==row['sha256'];target=shadow/row['path'];target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():os.link(source,target)
    (shadow/'data/supplier-storefront.json').write_text(json.dumps(reviewed,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    d.validate_supplier_publication(shadow,candidate)
    spec=importlib.util.spec_from_file_location('brand_owner_gate',R/'lib/owner_media_gate.py');owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner);owner.verify_owner_catalogues(R,candidate)
    subprocess.run(['node',str(R/'scripts/verify-current-media.mjs'),str(R),str(R/proof['release'])],check=True)
    record={'passed':True,'releaseHash':proof['releaseHash'],'auditedBaseReleaseHash':base['manifest']['releaseHash'],'allOriginalAndOutputHashesVerified':True,'catalogueAndApprovalBytesEqualLiveBase':True,'supplierVisualValidatorUnchanged':True,'liveSupplierProducts':len(old_products),'unpublishedNewProductsExcluded':len(current)-len(old_products),'unpublishedAdditionalFieldsExcluded':['finishState','paintSurface'],'sourceProjectionUnmodified':True}
    (E/'media.json').write_text(json.dumps(record,indent=2)+'\n')
