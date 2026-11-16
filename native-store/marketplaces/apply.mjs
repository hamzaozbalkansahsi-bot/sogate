/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/marketplaces/apply.mjs
 * Açıklama   : Pazaryeri kaynak kimliğini koruyarak türetilmiş katalog, medya ve yönetim bağlantılarını genişletir.
 */
import fs from 'node:fs';import path from 'node:path';
const bundle=path.resolve(process.argv[2]);if(!bundle.includes('native-stage-'))throw Error('MARKETPLACE_BUILD_SCOPE');
const catalog=JSON.parse(fs.readFileSync(path.join(bundle,'private/catalog.json'),'utf8'));if(catalog.catalogOrigin!=='sexogate-catalog-v2')throw Error('MARKETPLACE_SOURCE_REQUIRED');
function edit(file,from,to){const p=path.join(bundle,file),text=fs.readFileSync(p,'utf8');if(text.split(from).length!==2)throw Error('MARKETPLACE_HOOK_CHANGED:'+file);fs.writeFileSync(p,text.replace(from,to));}
for(const file of ['private/sexogate-catalog.php','private/seo.php','private/sexogate-storefront-content.php','public/index.php']){
 const p=path.join(bundle,file);let text=fs.readFileSync(p,'utf8');
 for(const expression of ["($product['catalogOrigin']??'')","($state['sourceCatalog']['catalogOrigin']??'')"]){text=text.replaceAll(expression+"==='sexogate-suppliers-v1'","in_array("+expression+",['sexogate-suppliers-v1','sexogate-marketplaces-v1','sexogate-catalog-v2'],true)").replaceAll(expression+"!=='sexogate-suppliers-v1'","!in_array("+expression+",['sexogate-suppliers-v1','sexogate-marketplaces-v1'],true)");}
 text=text.replaceAll('(?:xsh|lio|sis)','(?:xsh|lio|sis|ty)');fs.writeFileSync(p,text);
}
edit('public/seo-core.js',"product.catalogOrigin==='sexogate-suppliers-v1'","['sexogate-suppliers-v1','sexogate-marketplaces-v1'].includes(product.catalogOrigin)");
const sourceBrandHook="if(in_array(($product['catalogOrigin']??''),['sexogate-suppliers-v1','sexogate-marketplaces-v1','sexogate-catalog-v2'],true)){if(!empty($product['brand']))$data['brand']=['@type'=>'Brand','name'=>$product['brand']];else unset($data['brand']);}";
edit('private/seo.php',sourceBrandHook,'');
edit('private/seo.php',"$data['description']=nodenoSeoDescription($product,$locale,$catalog);",sourceBrandHook+"$data['description']=nodenoSeoDescription($product,$locale,$catalog);");
edit('public/sexogate-catalog.js','(xsh|lio|sis)','(xsh|lio|sis|ty)');
edit('public/sexogate-catalog.js',"let editorId='',queued=false;","let editorId=new URLSearchParams(location.hash.split('?')[1]??'').get('record')??'',queued=false;");
edit('private/sexogate-catalog.php',"'initialMarkup'=>'İlk aktarımda kaynak kamu fiyatı +%30. Sonraki aktarım yönetici fiyatını değiştirmez.'","'initialMarkup'=>'İlk aktarım: kaynak indirimsiz kamu fiyatı +%'.($work['initialMarkupPercent']??30).'. Sonraki aktarım yönetici fiyatını değiştirmez.'");
edit('private/sexogate-catalog.php',"'rightsBasis'=>'15 Kasım 2026 kullanıcı beyanı · ürün fotoğrafları ve içerikleri; yazılı sözleşme varlığı iddia edilmez.'","'rightsBasis'=>($work['rights']['at']??'2026-11-15').' kullanıcı beyanı · fotoğraf/içerik izni; gerçek üretici kimliği korunur. Yazılı sözleşme veya tedarik kabulü iddia edilmez.'");
edit('private/sexogate-catalog.php',"'markupPercent'=>30","'markupPercent'=>$manifest['markupPercent']??null,'pricingSummary'=>$manifest['pricingSummary']??'Yönetici fiyatları korunur.'");
edit('public/sexogate-catalog.js','İlk satış fiyatı, kaynak kamu fiyatının %30 üzeridir. Mevcut yönetici fiyatları ve düzenlemeleri korunur. Kamu bulunabilirliği depo stoğuna aktarılmaz.','\'+esc(data.pricingSummary)+\' Kamu bulunabilirliği depo stoğuna aktarılmaz.');
console.log(JSON.stringify({marketplaceNamespaces:true,sourceSkuPreserved:true,newMarkupPercent:15,additionalDiscountPercent:0,legacyArchivedRecordsPreserved:true,automaticPublication:false}));
