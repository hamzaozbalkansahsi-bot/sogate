/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/native-postgres.mjs
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import { mkdir, access, writeFile, readFile, unlink } from 'node:fs/promises';
import { createWriteStream } from 'node:fs';
import { pipeline } from 'node:stream/promises';
import { Readable } from 'node:stream';
import { execFile, spawn } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';
import pg from 'pg';
const exec=promisify(execFile);
// EDB Windows binaries use ANSI install paths during initdb; the 8.3 path keeps
// the original UTF-8 workspace and PostgreSQL data encoding intact.
const root=process.platform==='win32'?(await exec('C:\\Windows\\System32\\cmd.exe',['/d','/c','for %I in (.) do @echo %~sI'],{windowsHide:true})).stdout.trim():process.cwd();
if(process.platform!=='win32') throw new Error('Bu yardımcı Windows içindir; diğer sistemlerde Docker Compose kullanın.');
const bin=path.join(root,'.local','postgresql','pgsql','bin');
await mkdir('.local',{recursive:true});
try { await access(path.join(bin,'pg_ctl.exe')); } catch {
  console.log('Resmî EDB PostgreSQL 18.6 kararlı Windows arşivi indiriliyor (yalnız proje içine).');
  const response=await fetch('https://get.enterprisedb.com/postgresql/postgresql-18.6-1-windows-x64-binaries.zip');
  if(!response.ok||!response.body) throw new Error('PostgreSQL arşivi indirilemedi.');
  await pipeline(Readable.fromWeb(response.body),createWriteStream('.local/postgres.zip'));
  await exec('python',['-c','import zipfile; z=zipfile.ZipFile(".local/postgres.zip"); z.extractall(".local/postgresql", members=[n for n in z.namelist() if n.startswith(("pgsql/bin/","pgsql/lib/","pgsql/share/"))])'],{windowsHide:true,maxBuffer:1024*1024});
}
const env=Object.fromEntries((await readFile('.env.local','utf8')).split(/\r?\n/).filter(l=>l&&!l.startsWith('#')).map(l=>{const i=l.indexOf('=');return[l.slice(0,i),l.slice(i+1)];}));
const url=new URL(env.DATABASE_URL); const data=path.join(root,'.local','postgres-data');
if(process.argv.includes('--stop')) { await exec(path.join(bin,'pg_ctl.exe'),['-D',data,'-m','fast','-w','stop'],{windowsHide:true}); console.log('Yerel PostgreSQL durduruldu.'); process.exit(0); }
try { await access(path.join(data,'PG_VERSION')); } catch {
  const passFile=path.join(root,'.local','pg-init-password'); await writeFile(passFile,decodeURIComponent(url.password),{mode:0o600});
  try { await exec(path.join(bin,'initdb.exe'),['-D',data,'-U','sexsogate','--pwfile',passFile,'--auth=scram-sha-256','--encoding=UTF8','--locale=C'],{windowsHide:true,maxBuffer:1024*1024}); } finally { await unlink(passFile); }
}
try { await exec(path.join(bin,'pg_ctl.exe'),['-D',data,'status'],{windowsHide:true}); }
catch { await new Promise((resolve,reject)=>{ const child=spawn(path.join(bin,'pg_ctl.exe'),['-D',data,'-l',path.join(root,'.local','postgres.log'),'-o','-h 127.0.0.1 -p 55432','-w','start'],{windowsHide:true,stdio:'ignore'}); child.on('error',reject);child.on('exit',code=>code===0?resolve():reject(new Error('PostgreSQL başlatılamadı; .local/postgres.log dosyasını inceleyin.'))); }); }
const adminUrl=new URL(url);adminUrl.pathname='/postgres';const client=new pg.Client({connectionString:adminUrl.href});await client.connect();
for (const dbName of ['sexsogate_dev','sexsogate_test']) { if(!(await client.query('select 1 from pg_database where datname=$1',[dbName])).rowCount) await client.query(`CREATE DATABASE ${dbName} ENCODING 'UTF8' TEMPLATE template0`); }
await client.end();console.log('Proje PostgreSQL hazır: 127.0.0.1:55432; development ve test ayrı.');
