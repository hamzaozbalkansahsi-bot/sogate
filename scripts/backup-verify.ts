/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/backup-verify.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import pg from 'pg';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {mkdir,readFile,writeFile,unlink} from 'node:fs/promises';
import path from 'node:path';
import {createCipheriv,createDecipheriv,createHash,randomBytes} from 'node:crypto';
import assert from 'node:assert/strict';
const exec=promisify(execFile);
const source=process.env.TEST_DATABASE_URL;if(!source)throw new Error('TEST_DATABASE_URL required');
const url=new URL(source);if(!url.pathname.endsWith('_test')||!['localhost','127.0.0.1'].includes(url.hostname))throw new Error('Geri yükleme testi yalnız yerel test veritabanına izin verir.');
const key=Buffer.from(process.env.BACKUP_ENCRYPTION_KEY??'','hex');if(key.length!==32)throw new Error('32byte BACKUP_ENCRYPTION_KEY required');
const binary=process.env.PG_BIN??path.resolve('.local/postgresql/pgsql/bin');
const pgExe=(name:string)=>path.join(binary,process.platform==='win32'?`${name}.exe`:name);
const pgEnv={...process.env,PGHOST:url.hostname,PGPORT:url.port,PGUSER:decodeURIComponent(url.username),PGPASSWORD:decodeURIComponent(url.password),PGDATABASE:url.pathname.slice(1)};
await mkdir('.local/backups',{recursive:true});const stamp=new Date().toISOString().replace(/[^0-9]/g,'');
const dump=path.resolve(`.local/backups/restore-${stamp}.dump`);const encrypted=dump+'.enc';
const tables=['schema_migrations','products','variants','orders','order_items','inventory_movements','payments','order_agreements','inventory_lots','inventory_lot_balances','reservation_lots','cms_regions','cms_region_revisions','content_revisions','privacy_requests','privacy_policies','privacy_controllers','bundle_components','bundle_changes','product_documents','product_eligibility','product_contact_profiles','product_compliance_events','compliance_commands','country_address_profiles','country_address_events','customer_addresses','purchase_orders','purchase_items','purchase_receipts','purchase_receipt_items','purchase_receipt_lots','lot_operations'];
async function fingerprint(client:pg.Client){const out:Record<string,unknown>={};for(const table of tables){const result=await client.query(`SELECT count(*)::int n,md5(coalesce(string_agg(row_to_json(t)::text,'' ORDER BY row_to_json(t)::text),'')) digest FROM ${table} t`);out[table]=result.rows[0];}return out;}
try {
const sourceClient=new pg.Client({connectionString:source});await sourceClient.connect();const before=await fingerprint(sourceClient);await sourceClient.end();
await exec(pgExe('pg_dump'),['-Fc','--no-owner','--no-acl','-f',dump],{env:pgEnv,windowsHide:true,maxBuffer:1024*1024});
const plain=await readFile(dump);const iv=randomBytes(12);const cipher=createCipheriv('aes-256-gcm',key,iv);const ciphertext=Buffer.concat([cipher.update(plain),cipher.final()]);
await writeFile(encrypted,Buffer.concat([Buffer.from('SGDB1'),iv,cipher.getAuthTag(),ciphertext]),{mode:0o600});await unlink(dump);
const sealed=await readFile(encrypted);const decipher=createDecipheriv('aes-256-gcm',key,sealed.subarray(5,17));decipher.setAuthTag(sealed.subarray(17,33));await writeFile(dump,Buffer.concat([decipher.update(sealed.subarray(33)),decipher.final()]),{mode:0o600});
const restoreName=`sexsogate_restore_${stamp}_test`;assert.match(restoreName,/^sexsogate_restore_[0-9]+_test$/);
const adminUrl=new URL(source);adminUrl.pathname='/postgres';const admin=new pg.Client({connectionString:adminUrl.href});await admin.connect();
try{
 await admin.query(`CREATE DATABASE ${restoreName} ENCODING 'UTF8' TEMPLATE template0`);
 await exec(pgExe('pg_restore'),['--exit-on-error','--no-owner','--no-acl','-d',restoreName,dump],{env:{...pgEnv,PGDATABASE:restoreName},windowsHide:true,maxBuffer:1024*1024});
 const restoredUrl=new URL(source);restoredUrl.pathname='/'+restoreName;const restored=new pg.Client({connectionString:restoredUrl.href});await restored.connect();const after=await fingerprint(restored);await restored.end();assert.deepEqual(after,before);
 const sample=await readFile('public/brand/share-preview.png');const mediaIv=randomBytes(12);const mediaCipher=createCipheriv('aes-256-gcm',key,mediaIv);const mediaEncrypted=Buffer.concat([mediaCipher.update(sample),mediaCipher.final()]);
 await writeFile(`.local/backups/media-${stamp}.enc`,Buffer.concat([mediaIv,mediaCipher.getAuthTag(),mediaEncrypted]),{mode:0o600});const mediaDec=createDecipheriv('aes-256-gcm',key,mediaIv);mediaDec.setAuthTag(mediaCipher.getAuthTag());const mediaRestored=Buffer.concat([mediaDec.update(mediaEncrypted),mediaDec.final()]);assert.equal(createHash('sha256').update(sample).digest('hex'),createHash('sha256').update(mediaRestored).digest('hex'));
 await writeFile('.local/backups/last-restore-report.json',JSON.stringify({at:new Date().toISOString(),database:'isolated local restore test',tables:after,media:{fixture:'public/brand/share-preview.png',bytes:sample.length,sha256:createHash('sha256').update(sample).digest('hex')},encryptedArchive:path.basename(encrypted),result:'PASS'},null,2));
 console.log(`PASS: şifreli PostgreSQL yedeği yeni izole veritabanına geri yüklendi; ${tables.length} kritik tablo sayısı/hash ve medya SHA-256 eşleşti.`);
}finally{
 // Only the database created by this invocation is removed; source DB is untouched.
 await admin.query(`DROP DATABASE IF EXISTS ${restoreName} WITH(FORCE)`);await admin.end();await unlink(dump).catch(()=>{});
}
}finally{await unlink(dump).catch(()=>{});}
