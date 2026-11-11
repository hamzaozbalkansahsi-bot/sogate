/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/refunds.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import {query,transaction} from '../db';
import {requireCondition} from './rules';

/** Only call after the official provider API or verified event establishes this status. */
export async function finalizeProviderRefund(refundId:string,providerReference:string,status:'succeeded'|'pending'|'failed'):Promise<{duplicate:boolean,status:string}> {
 requireCondition(typeof providerReference==='string'&&providerReference.length>=3&&providerReference.length<=200,'REFUND_REFERENCE_REQUIRED','Sağlayıcı iade referansı gerekir.');
 requireCondition(['succeeded','pending','failed'].includes(status),'INVALID_REFUND_STATUS','İade yanıtı geçersiz.');
 return transaction(async c=>{
  const [refund]=await query('SELECT r.*,rt.order_id FROM refunds r JOIN returns rt ON rt.id=r.return_id WHERE r.id=$1 FOR UPDATE OF r',[refundId],c);
  requireCondition(refund,'REFUND_NOT_FOUND','İade kaydı bulunamadı.',404);
  const [payment]=await query('SELECT * FROM payments WHERE id=$1 FOR UPDATE',[refund.payment_id],c);
  requireCondition(payment?.provider==='stripe','REFUND_PROVIDER_MISMATCH','İade sağlayıcısı eşleşmiyor.',409);
  requireCondition(!refund.provider_reference||refund.provider_reference===providerReference,'REFUND_REFERENCE_MISMATCH','İade oturumu kaydı eşleşmiyor.',409);
  if(refund.status==='succeeded')return {duplicate:true,status:'succeeded'};
  if(status==='pending') {
   requireCondition(refund.status==='pending','INVALID_REFUND_STATE','Sonuçlanmış iade bekleyen duruma alınamaz.',409);
   await query('UPDATE refunds SET provider_reference=$2 WHERE id=$1',[refund.id,providerReference],c);return {duplicate:false,status};
  }
  if(status==='failed') {
   if(refund.status==='failed')return {duplicate:true,status};
   await query("UPDATE refunds SET status='failed',provider_reference=$2 WHERE id=$1",[refund.id,providerReference],c);
   await query("UPDATE returns SET status='refund_failed',updated_at=now() WHERE id=$1",[refund.return_id],c);
   await query("INSERT INTO order_history(order_id,type,to_status,details) VALUES($1,'refund','failed',$2)",[refund.order_id,JSON.stringify({refundId:refund.id})],c);return {duplicate:false,status};
  }
  const amount=Number(refund.amount_minor),current=Number(payment.refunded_minor),total=Number(payment.amount_minor);
  requireCondition(Number.isSafeInteger(amount)&&amount>0&&Number.isSafeInteger(current+amount)&&current+amount<=total,'REFUND_AMOUNT','İade toplamı tahsilatı aşamaz.',409);
  const paymentStatus=current+amount===total?'refunded':'partially_refunded';
  await query("UPDATE refunds SET status='succeeded',provider_reference=$2 WHERE id=$1",[refund.id,providerReference],c);
  await query('UPDATE payments SET refunded_minor=refunded_minor+$2,status=$3,updated_at=now() WHERE id=$1',[payment.id,amount,paymentStatus],c);
  await query('UPDATE orders SET payment_status=$2,updated_at=now() WHERE id=$1',[refund.order_id,paymentStatus],c);
  await query("UPDATE returns SET status='refunded',updated_at=now() WHERE id=$1",[refund.return_id],c);
  await query("INSERT INTO order_history(order_id,type,to_status,details) VALUES($1,'refund','succeeded',$2)",[refund.order_id,JSON.stringify({refundId:refund.id,amountMinor:amount})],c);
  return {duplicate:false,status:'succeeded'};
 });
}
