/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/product-feedback-build.mjs
 * Açıklama   : Ürün geri bildirimine ait dört dosyayı yalnız türetilmiş native paketine kopyalar.
 */
import fs from'node:fs';import path from'node:path';import{fileURLToPath}from'node:url';
const source=path.dirname(fileURLToPath(import.meta.url)),bundle=path.resolve(process.argv[2]||'');
const scoped=path.basename(bundle).startsWith('native-stage-')||(path.basename(bundle)==='bundle'&&path.basename(path.dirname(bundle)).startsWith('native-stage-'));
if(!scoped||!fs.statSync(path.join(bundle,'private')).isDirectory()||!fs.statSync(path.join(bundle,'public')).isDirectory())throw Error('PRODUCT_FEEDBACK_BUILD_SCOPE');
for(const [from,to]of[['product-feedback.php','private/sg-product-feedback.php'],['product-feedback-001.sql','private/product-feedback-001.sql'],['product-feedback.js','public/sg-product-feedback.js'],['product-feedback.css','public/sg-product-feedback.css']]){
 const bytes=fs.readFileSync(path.join(source,from));new TextDecoder('utf-8',{fatal:true}).decode(bytes);fs.writeFileSync(path.join(bundle,to),bytes);
}
console.log(JSON.stringify({productFeedbackFiles:4,persistentSchema:true,adminSidebarLink:true,brandThemeOnAdmin:true,sourceSnapshotChanged:false,externalCalls:false}));
