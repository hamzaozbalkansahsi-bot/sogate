/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/providers/retry-policy.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import {HttpError} from '../security';
export function assertRefundCreationWindow(createdAt:string|Date,now=Date.now()){
 const created=new Date(createdAt).getTime();
 if(!Number.isFinite(created)||created>now||now-created>=23*60*60*1000)throw new HttpError(409,'Önceki iade sonucu sağlayıcıdan mutabık kılınmadan eski işlem yeniden gönderilemez.','REFUND_RECONCILIATION_REQUIRED');
}
export function choosePaymentAction(state:{orderStatus:string;paymentStatus:string;expiresAt:string|Date;providerReference:string|null},now=Date.now()):'order'|'resume'|'create'{
 if(state.paymentStatus!=='pending'||state.orderStatus!=='awaiting_payment'||new Date(state.expiresAt).getTime()<=now)return 'order';
 return state.providerReference?'resume':'create';
}
