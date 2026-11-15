/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-variant-artifact.mjs
 * Açıklama   : Yerelde üretilen özel katalog paketinin yeni modüllerinde önbellek sürümlemesini denetler.
 */
import {test} from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import path from 'node:path';
test('Yeni seçenek modülleri her yayında varlık sürümünü kullanır',()=>{
 const pkg=JSON.parse(fs.readFileSync(new URL('../.local/native-stage-package.json',import.meta.url),'utf8')),manifest=JSON.parse(fs.readFileSync(path.join(pkg.bundle,'deployment-manifest.json'),'utf8'));
 for(const file of ['app.js','shop-core.js','shopping-ui.js','sexogate-variant-ui.js']){const source=fs.readFileSync(path.join(pkg.bundle,'public',file),'utf8'),imports=[...source.matchAll(/from ['"]\.\/sexogate-variant[^'"]+['"]/g)];assert.ok(imports.length);for(const entry of imports)assert.ok(entry[0].includes('?v=sexogate-'+manifest.assetVersion),file+': missing asset revision');}
});
test('Katalog ve ayar okuması sürümlü süre sınırı modülüne bağlıdır',()=>{
 const pkg=JSON.parse(fs.readFileSync(new URL('../.local/native-stage-package.json',import.meta.url),'utf8')),manifest=JSON.parse(fs.readFileSync(path.join(pkg.bundle,'deployment-manifest.json'),'utf8')),source=fs.readFileSync(path.join(pkg.bundle,'public/app.js'),'utf8');
 assert.ok(source.includes("./sexogate-public-read.js?v=sexogate-"+manifest.assetVersion));
 for(const name of ['catalog','config'])assert.ok(source.includes("readStorefrontJson('/__SEXOGATE_MOUNT__/api/"+name+"'"));
});
