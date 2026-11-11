/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/setup-ci.mjs
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import {randomBytes} from 'node:crypto';
import {writeFile,appendFile} from 'node:fs/promises';
import pg from 'pg';
if(process.env.APP_ENV!=='test'||!process.env.CI)throw new Error('Yalnız izole CI test ortamı.');
const values={BETTER_AUTH_SECRET:randomBytes(48).toString('hex'),PAYMENT_WEBHOOK_SECRET:randomBytes(48).toString('hex'),BACKUP_ENCRYPTION_KEY:randomBytes(32).toString('hex')};
const lines=Object.entries(values).map(([k,v])=>`${k}=${v}`).join('\n')+'\n';
await writeFile('.env.local',lines,{mode:0o600});if(process.env.GITHUB_ENV)await appendFile(process.env.GITHUB_ENV,lines);
const url=new URL(process.env.DATABASE_URL);url.pathname='/postgres';const client=new pg.Client({connectionString:url.href});await client.connect();if(!(await client.query("SELECT 1 FROM pg_database WHERE datname='sexsogate_test'")).rowCount)await client.query('CREATE DATABASE sexsogate_test');await client.end();
