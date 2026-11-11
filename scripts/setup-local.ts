/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/setup-local.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import { randomBytes } from 'node:crypto';
import { mkdir, writeFile, access, readFile, appendFile } from 'node:fs/promises';
await mkdir('.local', {recursive:true});
try { await access('.env.local'); console.log('.env.local korunuyor; mevcut yerel ayarlar değiştirilmedi.'); }
catch {
  const dbPassword=randomBytes(24).toString('hex');
  const adminPassword=randomBytes(24).toString('base64url');
  await writeFile('.env.local', [
    'APP_ENV=development','APP_URL=http://127.0.0.1:3000',
    `DATABASE_URL=postgresql://sexsogate:${dbPassword}@127.0.0.1:55432/sexsogate_dev`,
    `TEST_DATABASE_URL=postgresql://sexsogate:${dbPassword}@127.0.0.1:55432/sexsogate_test`,
    'BETTER_AUTH_URL=http://127.0.0.1:3000',`BETTER_AUTH_SECRET=${randomBytes(48).toString('hex')}`,
    'PAYMENT_PROVIDER=test',`PAYMENT_WEBHOOK_SECRET=${randomBytes(48).toString('hex')}`,
    'LIVE_SALES_ENABLED=false','STRIPE_BUSINESS_APPROVED=false','STRIPE_SECRET_KEY=','STRIPE_WEBHOOK_SECRET=',
    'NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=','STORAGE_PROVIDER=local','STORAGE_LOCAL_PATH=.local/media',
    `BACKUP_ENCRYPTION_KEY=${randomBytes(32).toString('hex')}`,
    'ADMIN_SETUP_EMAIL=admin@sexsogate.local',`ADMIN_SETUP_PASSWORD=${adminPassword}`,
  ].join('\n')+'\n',{mode:0o600});
  await writeFile('.local/admin-access.txt',`Yalnız yerel geliştirme erişimi\nE-posta: admin@sexsogate.local\nParola: ${adminPassword}\nİlk girişten sonra iki adımlı doğrulamayı Hesabım > Güvenlik alanında etkinleştirin.\n`,{mode:0o600});
  console.log('Yerel sırlar üretildi. Değerler Git dışında .env.local içinde; yerel yönetici bilgisi .local/admin-access.txt.');
}
const existingText=await readFile('.env.local','utf8');
const current=Object.fromEntries(existingText.split(/\r?\n/).filter(line=>line&&!line.startsWith('#')).map(line=>{const index=line.indexOf('=');return[line.slice(0,index),line.slice(index+1)];}));
const additions:string[]=[];
if(!('LOCAL_DB_PASSWORD' in current)&&current.DATABASE_URL)additions.push(`LOCAL_DB_PASSWORD=${decodeURIComponent(new URL(current.DATABASE_URL).password)}`);
if(!('TRUSTED_PROXY_ENABLED' in current))additions.push('TRUSTED_PROXY_ENABLED=false');
if(!('TRUSTED_CLIENT_IP_HEADER' in current))additions.push('TRUSTED_CLIENT_IP_HEADER=');
if(additions.length)await appendFile('.env.local',additions.join('\n')+'\n',{mode:0o600});
