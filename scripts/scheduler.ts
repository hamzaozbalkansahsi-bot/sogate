/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/scheduler.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import {pool} from '../src/server/db';
let stopped=false;process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
while(!stopped){
 const interval=Math.floor(Date.now()/60000);
 for(const type of ['reservation.expire',...(process.env.PAYMENT_PROVIDER==='stripe'?['payment.reconcile','refund.reconcile']:[])]){
  await pool.query('INSERT INTO jobs(type,payload,dedupe_key) VALUES($1,\'{}\',$2) ON CONFLICT DO NOTHING',[type,`schedule:${type}:${interval}`]);
 }
 await pool.query('DELETE FROM request_limits WHERE expires_at<now()');
 if(process.argv.includes('--once'))break;
 await new Promise(resolve=>setTimeout(resolve,30000));
}
await pool.end();
