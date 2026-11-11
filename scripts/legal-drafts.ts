/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/legal-drafts.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import pg from 'pg';
export interface LegalDraft {kind:string;locale:'tr';title:string;body:string;}
const kinds:Record<string,string>={
  'privacy-notice':'privacy','privacy-policy':'privacy_policy','cookie-policy':'cookies','terms-of-use':'usage',
  'membership-terms':'membership','pre-contract-information':'pre_information','distance-selling-contract':'terms',
  'shipping-policy':'shipping','returns-policy':'returns','marketing-consent':'consent','data-subject-request':'data_request',
  'explicit-consent':'explicit_consent','defective-product-policy':'defective',
};
export async function readLegalDrafts():Promise<LegalDraft[]> {
  const text=await readFile(new URL('../docs/legal-drafts.md',import.meta.url),'utf8');
  const sections=[...text.matchAll(/^## ([^\n]+?) \/ `([a-z-]+)`\r?\n([\s\S]*?)(?=^## |$(?![\s\S]))/gm)];
  const drafts:LegalDraft[]=[];
  for(const [,title,key,section]of sections) {
    const kind=kinds[key];if(!kind)throw new Error('Hukuk belgesi tür eşlemesi tanınmıyor.');
    const match=/\*\*İçerik taslağı:\*\*\s*([\s\S]*?)(?=\r?\n\r?\n\*\*Yayın için:\*\*)/.exec(section);
    const body=match?.[1].trim();
    if(!body||body.length<20||body.length>100000||!body.includes('{{'))throw new Error('Taslak gövdesi veya eksik alan bildirimi bulunamadı.');
    drafts.push({kind,locale:'tr',title:title.trim(),body});
  }
  if(drafts.length!==Object.keys(kinds).length||new Set(drafts.map(draft=>draft.kind)).size!==drafts.length)throw new Error('Hukuk taslağı sayısı veya türleri uyuşmuyor.');
  return drafts;
}
export async function seedLegalDrafts(databaseUrl=process.env.DATABASE_URL):Promise<{created:number;skipped:number}> {
  if(!['development','test'].includes(process.env.APP_ENV??'')||!databaseUrl)throw new Error('Taslak yükleme yalnız yapılandırılmış yerel geliştirme/test ortamında yapılabilir.');
  const url=new URL(databaseUrl);
  if(!['127.0.0.1','localhost','[::1]'].includes(url.hostname))throw new Error('Taslak yükleme yalnız yerel veritabanında yapılabilir.');
  const drafts=await readLegalDrafts(),client=new pg.Client({connectionString:databaseUrl});
  await client.connect();let created=0,skipped=0;
  try {
    await client.query('BEGIN');await client.query('SELECT pg_advisory_xact_lock(8401102027)');
    for(const draft of drafts) {
      const hash=createHash('sha256').update(draft.body).digest('hex');
      const existing=await client.query('SELECT id FROM legal_documents WHERE kind=$1 AND locale=$2 AND body_hash=$3 AND fixture=false LIMIT 1',[draft.kind,draft.locale,hash]);
      if(existing.rows.length){skipped++;continue;}
      const version=await client.query<{version:number}>('SELECT coalesce(max(version),0)+1 AS version FROM legal_documents WHERE kind=$1 AND locale=$2',[draft.kind,draft.locale]);
      const result=await client.query<{id:string}>('INSERT INTO legal_documents(kind,locale,title,body,version,status,body_hash,fixture) VALUES($1,$2,$3,$4,$5,\'draft\',$6,false) RETURNING id',[draft.kind,draft.locale,draft.title,draft.body,version.rows[0].version,hash]);
      await client.query('INSERT INTO audit_log(actor_id,action,resource,resource_id,details) VALUES(\'system:legal-draft-loader\',\'draft.template\',\'legal\',$1,$2)',[result.rows[0].id,JSON.stringify({source:'docs/legal-drafts.md',kind:draft.kind,hash})]);
      created++;
    }
    await client.query('COMMIT');return {created,skipped};
  }catch(error){await client.query('ROLLBACK');throw error;}finally{await client.end();}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href) {
  seedLegalDrafts().then(result=>console.log(`Hukuk taslakları: ${result.created} eklendi, ${result.skipped} mevcut kayıt korundu. Onay/yayın yapılmadı.`)).catch(()=>{console.error('Hukuk taslakları yüklenemedi; ortam, migration ve kaynak belgesini kontrol edin.');process.exitCode=1;});
}
