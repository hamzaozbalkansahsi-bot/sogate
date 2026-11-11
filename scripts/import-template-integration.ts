/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/import-template-integration.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import assert from 'node:assert/strict';
import { randomBytes } from 'node:crypto';
import pg from 'pg';
import { migrate } from './migrate';
import {mkdir,writeFile,unlink,rmdir} from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const base = process.env.TEST_DATABASE_URL;
if (!base) throw new Error('TEST_DATABASE_URL gereklidir.');
const parsed = new URL(base);
if (!['127.0.0.1','localhost','[::1]'].includes(parsed.hostname) || !parsed.pathname.endsWith('_test')) throw new Error('Yalnız yerel ve izole test veritabanı kullanılabilir.');
const dbName = `sexsogate_${randomBytes(5).toString('hex')}_import_test`;
const control = new pg.Client({connectionString:base});
await control.connect();
await control.query(`CREATE DATABASE "${dbName}"`);
parsed.pathname = '/'+dbName;
process.env.APP_ENV='test'; process.env.DATABASE_URL=parsed.toString();
const {pool,query} = await import('../src/server/db');
const {previewImport,commitImport,escapeImportCsvCell} = await import('../src/server/imports');
const actor = {id:'catalog-import-test',role:'catalog' as const,mfa:true};
const header='sku,name,nameEn,category,priceMinor,material,image';
const data=(sku:string)=>Buffer.from(header+'\n'+sku+',Ölçü ve Özellikler,Measurements and details,aksesuarlar,10001,Tekstil,/media/atelier-01.svg');
let passed=0;
async function check(name:string,work:()=>Promise<void>){await work();console.log(`PASS ${++passed}: ${name}`);}
try {
  await migrate(process.env.DATABASE_URL);
  await query("INSERT INTO categories(slug,name,name_en) VALUES('aksesuarlar','Aksesuarlar','Accessories')");
  await check('Missing own depot is a preview error and never creates a warehouse automatically',async()=>{const p=await previewImport(data('NO-DEPOT'),'text/csv','depot.csv',{},actor);assert.equal(p.valid,false);assert(p.errors.some(e=>e.field==='depo'));assert.equal((await query('SELECT count(*)::int n FROM warehouses'))[0].n,0);});
  await query("INSERT INTO warehouses(id,name) VALUES('main','Yalnız izole test deposu')");
  await check('Preview is a dry run; commit creates draft product and zero warehouse stock',async()=>{
    const preview=await previewImport(data('IMPORT-1'),'text/csv','list.csv',{},actor);
    assert.equal(preview.valid,true);assert.equal((await query('SELECT count(*)::int AS n FROM products'))[0].n,0);
    const result=await commitImport(preview.previewId,actor);assert.equal(result.created,1);
    assert.equal((await query('SELECT status FROM products'))[0].status,'draft');
    assert.equal((await query("SELECT vp.amount_minor FROM variant_prices vp JOIN variants v ON v.id=vp.variant_id WHERE v.sku='IMPORT-1' AND vp.currency='TRY'"))[0]?.amount_minor,10001);
    assert.equal((await query('SELECT count(*)::int AS n FROM inventory_movements'))[0].n,0);
    assert.equal((await query('SELECT count(*)::int AS n FROM product_eligibility'))[0].n,0);
    const [balance]=await query("SELECT b.on_hand,b.quarantine,b.safety_stock FROM inventory_balance b JOIN variants v ON v.id=b.variant_id WHERE v.sku='IMPORT-1' AND b.warehouse_id='main'");assert.deepEqual(balance,{on_hand:0,quarantine:0,safety_stock:0});
  });
  await check('Repeated commit is idempotent and produces one audit and batch',async()=>{
    const preview=await previewImport(data('IMPORT-2'),'text/csv','list.csv',{},actor);
    const results=await Promise.all([commitImport(preview.previewId,actor),commitImport(preview.previewId,actor)]);
    assert.equal(results.filter(result=>result.alreadyCommitted).length,1);
    assert.equal((await query('SELECT count(*)::int AS n FROM import_batches WHERE id=$1',[preview.previewId]))[0].n,1);
    assert.equal((await query("SELECT count(*)::int AS n FROM audit_log WHERE action='catalog.import' AND resource_id=$1",[preview.previewId]))[0].n,1);
  });
  await check('Preview owner binding and MFA/role checks prevent cross actor commit',async()=>{
    const preview=await previewImport(data('IMPORT-3'),'text/csv','list.csv',{},actor);
    await assert.rejects(()=>commitImport(preview.previewId,{...actor,id:'another-catalog-user'}));
    await assert.rejects(()=>commitImport(preview.previewId,{...actor,mfa:false}));
    await assert.rejects(()=>previewImport(data('IMPORT-4'),'text/csv','list.csv',{}, {...actor,role:'warehouse'}));
  });
  await check('Existing DB SKU appears as row error and invalid previews cannot commit',async()=>{
    const preview=await previewImport(data('IMPORT-1'),'text/csv','list.csv',{},actor);
    assert.equal(preview.valid,false);assert(preview.errors.some(error=>error.row===2 && error.field==='sku'));
    await assert.rejects(()=>commitImport(preview.previewId,actor));
  });
  await check('Concurrent previews recheck SKU at commit and only one transaction writes',async()=>{
    const one=await previewImport(data('IMPORT-RACE'),'text/csv','list.csv',{},actor);
    const two=await previewImport(data('IMPORT-RACE'),'text/csv','list.csv',{},actor);
    const results=await Promise.allSettled([commitImport(one.previewId,actor),commitImport(two.previewId,actor)]);
    assert.equal(results.filter(result=>result.status==='fulfilled').length,1);
    assert.equal((await query("SELECT count(*)::int AS n FROM variants WHERE sku='IMPORT-RACE'"))[0].n,1);
  });
  await check('Unknown categories, missing local image and changed checksum block writes',async()=>{
    const bad=await previewImport(Buffer.from(data('IMPORT-5').toString().replace(',aksesuarlar,',',bilinmeyen,')),'text/csv','list.csv',{},actor);assert.equal(bad.valid,false);
    const image=await previewImport(Buffer.from(data('IMPORT-6').toString().replace('atelier-01.svg','does-not-exist.png')),'text/csv','list.csv',{},actor);assert.equal(image.valid,false);
    const preview=await previewImport(data('IMPORT-7'),'text/csv','list.csv',{},actor);
    await query("UPDATE import_preview SET rows=jsonb_set(rows,'{0,name}','\"Changed\"') WHERE id=$1",[preview.previewId]);
    await assert.rejects(()=>commitImport(preview.previewId,actor));
    assert.equal((await query("SELECT count(*)::int AS n FROM variants WHERE sku='IMPORT-7'"))[0].n,0);
  });
  await check('Expired previews and catalog changes cannot be committed',async()=>{
    const preview=await previewImport(data('IMPORT-8'),'text/csv','list.csv',{},actor);
    await query("UPDATE import_preview SET created_at=now()-interval '2 hours' WHERE id=$1",[preview.previewId]);
    await assert.rejects(()=>commitImport(preview.previewId,actor));
  });
  await check('Row-error integrity cannot be bypassed by clearing a stored unsupported-stock error',async()=>{
    const content=Buffer.from(header+',stock\nROW-ERROR,Ölçü,Measurements,aksesuarlar,10001,Tekstil,/media/atelier-01.svg,12');const p=await previewImport(content,'text/csv','stock.csv',{},actor);assert.equal(p.valid,false);await query("UPDATE import_preview SET errors='[]'::jsonb WHERE id=$1",[p.previewId]);await assert.rejects(()=>commitImport(p.previewId,actor));assert.equal((await query("SELECT count(*)::int n FROM variants WHERE sku='ROW-ERROR'"))[0].n,0);
  });
  const extended=(names:string[],rows:string[][])=>Buffer.from(names.join(',')+'\n'+rows.map(row=>row.map(escapeImportCsvCell).join(',')).join('\n'));
  const groupedFields=header.split(',').concat(['productKey','variantName','variantNameEn','size','color','weightGrams','packageDimensions','barcode','brand','manufacturer','origin','costMinor','priceEurMinor','priceUsdMinor','priceGbpMinor','description','descriptionEn','care','careEn','warnings','warningsEn','warranty','hygieneSealed','supplierId','taxClass','ingredients','measurements']);
  await query("INSERT INTO brands(slug,name,name_en) VALUES('gercek-kayit','Ölçü Markası','Measurements Brand')");
  const [supplier]=await query("INSERT INTO suppliers(name) VALUES('Mevcut Tedarikçi') RETURNING id");
  const groupedRow=(sku:string,size:string,barcode:string)=>[sku,'Şişli Ölçü Seti','Sisli measurement set','aksesuarlar','10001','Tekstil','/media/atelier-01.svg','GRUP-İÇ',`Bordo ${size}`,`Burgundy ${size}`,size,'Bordo','120',JSON.stringify({lengthCm:20,widthCm:15,heightCm:3}),barcode,'gercek-kayit','Dosyada beyan edilen üretici','TR','3000','2500','2600','2300','Türkçe açıklama','English description','Etiketi izleyin','Follow label','Yetişkin kullanımı','Adults only','Belgeye göre garanti koşulları','true',supplier.id,'textile','Dosyada beyan edilen içerik','Göğüs: 90 cm'];
  await check('Grouped rows create one draft product and distinct fully populated variants and four prices',async()=>{
    const preview=await previewImport(extended(groupedFields,[groupedRow('GROUP-M','M','00869000000001'),groupedRow('GROUP-L','L','00869000000002')]),'text/csv','grup.csv',{},actor);assert.equal(preview.valid,true);assert.equal(preview.productCount,1);assert.equal(preview.variantCount,2);
    const result=await commitImport(preview.previewId,actor);assert.equal(result.created,1);assert.equal(result.variants,2);
    const records=await query("SELECT v.*,p.name,p.description,p.manufacturer,p.origin,p.supplier_id,p.translations,p.attributes,p.status,p.fixture FROM variants v JOIN products p ON p.id=v.product_id WHERE v.sku IN('GROUP-M','GROUP-L') ORDER BY sku");assert.equal(new Set(records.map(row=>row.product_id)).size,1);assert.equal(records[0].barcode,'00869000000002');assert.equal(records[0].cost_minor,3000);assert.equal(records[0].size,'L');assert.equal(records[0].package_dimensions.lengthCm,20);assert.equal(records[0].name,'Şişli Ölçü Seti');assert.equal(records[0].translations.en.care,'Follow label');assert.equal(records[0].attributes.warranty,'Belgeye göre garanti koşulları');assert.equal(records[0].supplier_id,supplier.id);assert.equal(records[0].status,'draft');assert.equal(records[0].fixture,true);assert.equal((await query('SELECT count(*)::int n FROM variant_prices WHERE variant_id=ANY($1::text[])',[records.map(row=>row.id)]))[0].n,8);assert.equal((await query('SELECT count(*)::int n FROM inventory_movements'))[0].n,0);assert.equal((await query('SELECT count(*)::int n FROM product_eligibility'))[0].n,0);
    assert.equal((await commitImport(preview.previewId,actor)).created,1);
  });
  await check('Conflicting group metadata, existing barcodes and unknown references cannot commit or create entities',async()=>{
    const a=groupedRow('BAD-M','M','00869000000001'),b=groupedRow('BAD-L','L','00869000000003');b[1]='Farklı ürün';a[groupedFields.indexOf('brand')]='olmayan-marka';a[groupedFields.indexOf('supplierId')]='olmayan-tedarikci';const p=await previewImport(extended(groupedFields,[a,b]),'text/csv','bad.csv',{},actor);assert.equal(p.valid,false);for(const field of ['productKey','barcode','brand','supplierId'])assert(p.errors.some(e=>e.field===field),field);await assert.rejects(()=>commitImport(p.previewId,actor));assert.equal((await query("SELECT count(*)::int n FROM brands WHERE slug='olmayan-marka'"))[0].n,0);
  });
  await check('Preview version and environment are immutable; production cannot promote fixture media',async()=>{
    const p=await previewImport(data('VERSION-1'),'text/csv','version.csv',{},actor);await query('UPDATE import_preview SET format_version=99 WHERE id=$1',[p.previewId]);await assert.rejects(()=>commitImport(p.previewId,actor));const moved=await previewImport(data('ENV-1'),'text/csv','environment.csv',{},actor);process.env.APP_ENV='production';try{await assert.rejects(()=>commitImport(moved.previewId,actor));const prod=await previewImport(data('PROD-ILLUSTRATION'),'text/csv','production.csv',{},actor);assert.equal(prod.valid,false);assert(prod.errors.some(e=>e.field==='image'));}finally{process.env.APP_ENV='test';}
  });
  await check('Existing SKU-scoped documents stay unapproved references for the imported variant',async()=>{
    const [sourceVariant]=await query("SELECT id FROM variants WHERE sku='IMPORT-1'");const [doc]=await query("INSERT INTO product_documents(variant_id,country,kind,reference,valid_from,reviewed) VALUES($1,'TR','test-reference','Yalnız izole mevcut belge kaydı','2026-01-01',true) RETURNING id",[sourceVariant.id]);
    const p=await previewImport(extended(header.split(',').concat(['documentRefs']),[['DOC-1','Belge Referansı','Document Reference','aksesuarlar','10001','Tekstil','/media/atelier-01.svg',doc.id]]),'text/csv','docs.csv',{},actor);assert.equal(p.valid,true);await commitImport(p.previewId,actor);const [link]=await query("SELECT l.status FROM catalog_import_document_links l JOIN variants v ON v.id=l.variant_id WHERE v.sku='DOC-1'");assert.equal(link.status,'review_required');assert.equal((await query('SELECT count(*)::int n FROM product_documents'))[0].n,1);assert.equal((await query('SELECT count(*)::int n FROM product_eligibility'))[0].n,0);
    const bad=await previewImport(extended(header.split(',').concat(['documentRefs']),[['DOC-2','Belge Referansı','Document Reference','aksesuarlar','10001','Tekstil','/media/atelier-01.svg','missing-document']]),'text/csv','bad-doc.csv',{},actor);assert.equal(bad.valid,false);assert(bad.errors.some(e=>e.field==='documentRefs'));
  });
  await check('Private uploaded media needs an existing rights record and real confined local file',async()=>{
    const previous=process.env.STORAGE_LOCAL_PATH,provider=process.env.STORAGE_PROVIDER,folder=path.resolve('.local',`import-media-${randomBytes(7).toString('hex')}`),objectId='12345678-1234-1234-1234-123456789abc',key=`products/${objectId}.webp`,target=path.join(folder,key);process.env.STORAGE_LOCAL_PATH=folder;process.env.STORAGE_PROVIDER='local';
    try{await mkdir(path.dirname(target),{recursive:true});const image=await sharp('public/brand/share-preview.png').resize(16,16).webp().toBuffer();await writeFile(target,image,{mode:0o600});await query("INSERT INTO media_assets(object_key,mime_type,size_bytes,sha256,rights_reference,actor_id) VALUES($1,'image/webp',$2,'isolated-test-hash','Projenin özgün marka varlığı; izole sınama',$3)",[key,image.length,actor.id]);const mediaData=Buffer.from(data('PRIVATE-MEDIA').toString().replace('/media/atelier-01.svg',`/uploads/${objectId}.webp`));const p=await previewImport(mediaData,'text/csv','media.csv',{},actor);assert.equal(p.valid,true);await commitImport(p.previewId,actor);assert.equal((await query("SELECT image FROM products p JOIN variants v ON v.product_id=p.id WHERE v.sku='PRIVATE-MEDIA'"))[0].image,`/uploads/${objectId}.webp`);await writeFile(target,Buffer.alloc(8*1024*1024+1));const oversized=await previewImport(Buffer.from(mediaData.toString().replace('PRIVATE-MEDIA','OVERSIZE-MEDIA')),'text/csv','media.csv',{},actor);assert.equal(oversized.valid,false);assert(oversized.errors.some(e=>e.field==='image'));await writeFile(target,image);await query('UPDATE media_assets SET rights_reference=NULL WHERE object_key=$1',[key]);const denied=await previewImport(Buffer.from(mediaData.toString().replace('PRIVATE-MEDIA','NO-RIGHTS')),'text/csv','media.csv',{},actor);assert.equal(denied.valid,false);assert(denied.errors.some(e=>e.field==='image'));}finally{if(previous===undefined)delete process.env.STORAGE_LOCAL_PATH;else process.env.STORAGE_LOCAL_PATH=previous;if(provider===undefined)delete process.env.STORAGE_PROVIDER;else process.env.STORAGE_PROVIDER=provider;await unlink(target).catch(()=>{});await rmdir(path.dirname(target)).catch(()=>{});await rmdir(folder).catch(()=>{});}
  });
  console.log(`Import integration: ${passed} checks passed.`);
} finally {
  await pool.end();
  await control.query(`DROP DATABASE "${dbName}"`);
  await control.end();
}
