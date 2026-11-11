/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/privacy-rate.ts
 * Açıklama   : Kimlik veya IP kaydetmeden gizlilik başvurularının ağ kotasını uygular.
 */
import {createHmac} from 'node:crypto';
import {checkoutNetworkPolicy} from './abuse';
import {query} from './db';
import {HttpError} from './security';
export async function privacyQuota(request:Request){
 let policy:ReturnType<typeof checkoutNetworkPolicy>;
 try{policy=checkoutNetworkPolicy(request);}catch{throw new HttpError(503,'Başvuru güvenlik sınırı henüz yapılandırılmadı.');}
 const key='privacy-network:'+createHmac('sha256',process.env.BETTER_AUTH_SECRET!).update(policy.key).digest('hex');
 const [row]=await query("INSERT INTO request_limits(key,count,window_start,expires_at) VALUES($1,1,now(),now()+interval '2 minutes') ON CONFLICT(key) DO UPDATE SET count=CASE WHEN request_limits.window_start<=now()-interval '1 minute' THEN 1 ELSE request_limits.count+1 END,window_start=CASE WHEN request_limits.window_start<=now()-interval '1 minute' THEN now() ELSE request_limits.window_start END,expires_at=now()+interval '2 minutes' RETURNING count",[key]);
 const limit=['development','test'].includes(process.env.APP_ENV??'')?50:5;
 if(Number(row.count)>limit)throw new HttpError(429,'Çok fazla başvuru isteği alındı. Bir dakika sonra tekrar deneyin.');
}
