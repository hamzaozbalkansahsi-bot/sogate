/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/verify-build-artifact.ts
 * Açıklama   : Standalone çıktının sırları, test kayıtlarını ve geliştirme verisini paketlemediğini denetler.
 */
import {readdir,readFile} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve('.next/standalone');
const forbidden=new Set(['.local','.git','test-results','playwright-report','docs','tests']);
const entries=await readdir(root);
for(const entry of entries)assert(!forbidden.has(entry)&&!entry.startsWith('.env'),`Derleme çıktısı özel geliştirme verisi içeriyor: ${entry}`);
await readFile(path.join(root,'server.js'));
const manifest=JSON.parse(await readFile('.next/server/app/api/admin/social/route.js.nft.json','utf8')) as {files:string[]};
for(const asset of ['SexsogateBody-Regular.ttf','SexsogateDisplay-Regular.ttf','Montserrat-OFL.txt','PlayfairDisplay-OFL.txt','logo-horizontal.svg','symbol.svg'])assert(manifest.files.some(file=>file.endsWith('/'+asset)),`Sosyal şablon çalışma varlığı eksik: ${asset}`);
console.log('Build artifact: private development data excluded; required social fonts, licences and logos traced. PASS.');
