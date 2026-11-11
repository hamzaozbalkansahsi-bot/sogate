/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/worker.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import {createDecipheriv,createHash} from 'node:crypto';
import nodemailer from 'nodemailer';
import {pool} from '../src/server/db';
import {processJobsOnce,settleVerifiedPayment,expireReservations,finalizeProviderRefund} from '../src/server/commerce';
import {stripeProvider} from '../src/server/providers/stripe';
import type {VerifiedPayment} from '../src/server/providers/contracts';
import {assertRefundCreationWindow} from '../src/server/providers/retry-policy';
const mailer=()=>{if(!process.env.SMTP_HOST||!process.env.SMTP_FROM)throw new Error('SMTP_NOT_CONFIGURED');return nodemailer.createTransport({host:process.env.SMTP_HOST,port:Number(process.env.SMTP_PORT??587),secure:process.env.SMTP_PORT==='465',auth:process.env.SMTP_USER?{user:process.env.SMTP_USER,pass:process.env.SMTP_PASSWORD}:undefined});};
async function processStripeRefund(refundId:string,reconcile=false){
 const row=(await pool.query('SELECT r.id,r.status,r.created_at,r.amount_minor,r.provider_reference refund_reference,p.provider_reference payment_reference,p.provider,p.currency FROM refunds r JOIN payments p ON p.id=r.payment_id WHERE r.id=$1',[refundId])).rows[0];
 if(!row||row.provider!=='stripe')throw new Error('REFUND_NOT_FOUND');if(row.status==='succeeded'||row.status==='failed')return;
 const provider=stripeProvider();
 if(row.refund_reference){const result=await provider.queryRefund(row.refund_reference);if(result.amountMinor!==Number(row.amount_minor)||result.currency!==row.currency)throw new Error('REFUND_AMOUNT_MISMATCH');await finalizeProviderRefund(row.id,result.reference,result.status);return;}
 if(!row.payment_reference)throw new Error('PAYMENT_REFERENCE_REQUIRED');
 const prior=await provider.findRefund(row.payment_reference,`refund:${row.id}`);
 if(prior){if(prior.amountMinor!==Number(row.amount_minor)||prior.currency!==row.currency)throw new Error('REFUND_AMOUNT_MISMATCH');await finalizeProviderRefund(row.id,prior.reference,prior.status);return;}
 if(reconcile)return;
 assertRefundCreationWindow(row.created_at);
 const result=await provider.refund(row.payment_reference,Number(row.amount_minor),`refund:${row.id}`);
 const status=result.status==='succeeded'?'succeeded':['failed','canceled'].includes(result.status)?'failed':'pending';await finalizeProviderRefund(row.id,result.reference,status);
}
const handlers:Record<string,(payload:Record<string,unknown>)=>Promise<void>>={
 'email.privacy':async payload=>{
  const secret=process.env.BETTER_AUTH_SECRET;if(!secret||secret.length<32)throw new Error('NOTICE_SECRET_REQUIRED');
  const decipher=createDecipheriv('aes-256-gcm',createHash('sha256').update(secret).digest(),Buffer.from(String(payload.iv),'hex'));decipher.setAuthTag(Buffer.from(String(payload.tag),'hex'));
  const data=JSON.parse(Buffer.concat([decipher.update(Buffer.from(String(payload.data),'hex')),decipher.final()]).toString('utf8'));
  const en=data.locale==='en',link=data.url?`\n${data.url}`:'';
  await mailer().sendMail({from:process.env.SMTP_FROM,to:data.email,subject:en?'Your request status':'Başvurunuzun durumu',text:en?`Your request ${data.reference} has been recorded or updated. View its status using your private link. Detailed responses are shared only through a verified secure channel.${link}`:`${data.reference} numaralı başvurunuz kaydedildi veya güncellendi. Durumunu size özel bağlantınızdan izleyebilirsiniz. Ayrıntılı yanıtlar yalnız kimliği doğrulanmış güvenli kanaldan paylaşılır.${link}`});
 },
 'email.auth':async payload=>{
  const decipher=createDecipheriv('aes-256-gcm',createHash('sha256').update(process.env.BETTER_AUTH_SECRET!).digest(),Buffer.from(String(payload.iv),'hex'));decipher.setAuthTag(Buffer.from(String(payload.tag),'hex'));
  const data=JSON.parse(Buffer.concat([decipher.update(Buffer.from(String(payload.data),'hex')),decipher.final()]).toString('utf8'));
  await mailer().sendMail({from:process.env.SMTP_FROM,to:data.email,subject:data.kind==='password-reset'?'Hesap erişim bağlantınız':'E-posta adresinizi doğrulayın',text:`İşleminizi tamamlamak için güvenli bağlantıyı kullanın:\n${data.url}\nBu işlemi siz başlatmadıysanız bağlantıyı kullanmayın.`});
 },
 'payment.stripe':async payload=>{const row=(await pool.query('SELECT normalized,payload_hash FROM provider_events WHERE id=$1 AND provider=\'stripe\'',[payload.eventId])).rows[0];if(!row)throw new Error('EVENT_NOT_FOUND');await settleVerifiedPayment(row.normalized as VerifiedPayment,'stripe',row.payload_hash);await pool.query('UPDATE provider_events SET status=\'completed\' WHERE id=$1',[payload.eventId]);},
 'payment.stripe-review':async()=>{throw new Error('PROVIDER_EVENT_REQUIRES_REVIEW');},
 'refund.stripe':async payload=>processStripeRefund(String(payload.refundId??'')),
 'refund.reconcile':async()=>{const rows=await pool.query('SELECT r.id FROM refunds r JOIN payments p ON p.id=r.payment_id WHERE p.provider=\'stripe\' AND r.status=\'pending\' ORDER BY r.created_at LIMIT 100');for(const row of rows.rows)await processStripeRefund(row.id,true);},
 'payment.reconcile':async()=>{
  const provider=stripeProvider();const rows=await pool.query('SELECT order_id,provider_reference FROM payments WHERE provider=\'stripe\' AND status=\'pending\' AND provider_reference IS NOT NULL LIMIT 100');
  for(const row of rows.rows){const result=await provider.query(row.provider_reference);if(result.status!=='pending')await settleVerifiedPayment({eventId:`reconcile:${row.provider_reference}:${result.status}`,orderId:row.order_id,status:result.status,amountMinor:result.amountMinor,currency:result.currency,timestamp:Math.floor(Date.now()/1000),providerReference:row.provider_reference},'stripe');}
 },
 'order.confirmation':async payload=>{const id=String(payload.orderId??'');const result=await pool.query('SELECT email,number,locale FROM orders WHERE id=$1 AND payment_status=\'succeeded\'',[id]);const order=result.rows[0];if(!order)throw new Error('ORDER_NOT_PAID');await mailer().sendMail({from:process.env.SMTP_FROM,to:order.email,subject:order.locale==='en'?'Your order has been received':'Siparişiniz alındı',text:order.locale==='en'?`Your order ${order.number} has been received. View details securely in your account or the private link provided at checkout.`:`${order.number} numaralı siparişiniz alındı. Ayrıntılara hesabınızdan veya sipariş sırasında verilen size özel bağlantıdan erişebilirsiniz.`});},
};
let stopped=false;process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
console.log('SEXSOGATE kalıcı iş işleyicisi başladı.');
while(!stopped){try{await expireReservations();await processJobsOnce(handlers);}catch{console.error('İş döngüsü tamamlanamadı; sır veya müşteri verisi kaydedilmedi.');}if(process.argv.includes('--once'))break;await new Promise(resolve=>setTimeout(resolve,2000));}
await pool.end();
