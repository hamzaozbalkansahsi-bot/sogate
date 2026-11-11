/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/rules.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import { createHmac, timingSafeEqual } from "node:crypto";
import { z } from "zod";
import type { Principal } from "../../shared/contracts";
import {HttpError} from '../security';

export class DomainError extends HttpError {
 constructor(code:string, message:string, status=400) {super(status,message,code);this.name="DomainError";}
}
export function requireCondition(condition:unknown,code:string,message:string,status=400):asserts condition {
 if(!condition) throw new DomainError(code,message,status);
}
const safeAmount=(value:number)=>requireCondition(Number.isSafeInteger(value)&&value>=0&&value<=9_000_000_000_000,"INVALID_MONEY","Para tutarı geçersiz.");
export function calculateTotals(subtotalMinor:number,shippingMinor:number,discountMinor:number,taxBps:number) {
 [subtotalMinor,shippingMinor,discountMinor].forEach(safeAmount);
 requireCondition(discountMinor<=subtotalMinor && Number.isInteger(taxBps)&&taxBps>=0&&taxBps<=10000,"INVALID_MONEY","İndirim veya vergi kuralı geçersiz.");
 const goods=subtotalMinor-discountMinor;
 const divisor=BigInt(10000+taxBps);
 const taxMinor=Number((BigInt(goods)*BigInt(taxBps)+divisor/2n)/divisor);
 const totalMinor=goods+shippingMinor;safeAmount(totalMinor);
 return {subtotalMinor,discountMinor,shippingMinor,taxMinor,totalMinor};
}
export function allocateMinor(total:number,weights:number[]) {
 safeAmount(total);weights.forEach(safeAmount);
 const sum=weights.reduce((a,b)=>a+BigInt(b),0n);
 requireCondition(sum>0n,"INVALID_ALLOCATION","Dağıtım ağırlığı geçersiz.");
 const shares=weights.map(w=>Number(BigInt(total)*BigInt(w)/sum));
 let remainder=total-shares.reduce((a,b)=>a+b,0);
 const ranked=weights.map((w,i)=>({i,r:BigInt(total)*BigInt(w)%sum})).sort((a,b)=>a.r===b.r?a.i-b.i:a.r>b.r?-1:1);
 for(const {i} of ranked) if(remainder-->0) shares[i]++;
 return shares;
}
export function availableStock(onHand:number,reserved:number,safetyStock:number) {return Math.max(0,onHand-reserved-safetyStock);}
const permissions:Record<string,{read:string[],write:string[]}>= {
 products:{read:["catalog","warehouse","support","finance","marketing"],write:["catalog"]},
 inventory:{read:["catalog","warehouse","finance"],write:["warehouse"]},
 lots:{read:["catalog","warehouse","support","finance"],write:["warehouse"]},
 orders:{read:["warehouse","support","finance"],write:["support"]},
 shipments:{read:["warehouse","support","finance"],write:["warehouse"]},
 returns:{read:["warehouse","support","finance"],write:["warehouse","support","finance"]},
 content:{read:["catalog","marketing"],write:["marketing"]},
 settings:{read:[],write:[]},countries:{read:["catalog"],write:[]},
 reports:{read:["finance"],write:[]},jobs:{read:[],write:[]},audit:{read:[],write:[]},
 suppliers:{read:["catalog","warehouse","finance"],write:["catalog"]},customers:{read:["support"],write:[]},
 legal:{read:["support"],write:[]},purchases:{read:["catalog","warehouse","finance"],write:["catalog","warehouse"]},
 variants:{read:["catalog","warehouse","support","finance","marketing"],write:["catalog","finance"]},
 campaigns:{read:["catalog","finance","marketing"],write:["marketing","finance"]},
 categories:{read:["catalog","warehouse","marketing"],write:["catalog"]},
 brands:{read:["catalog","warehouse","marketing"],write:["catalog"]},
 invoices:{read:["finance","support"],write:["finance"]}
};
export function assertPermission(principal:Principal,resource:string,operation:"read"|"write") {
 const allowed=permissions[resource];
 requireCondition(principal?.id && principal.mfa,"MFA_REQUIRED","Bu işlem için iki adımlı doğrulama gerekir.",403);
 requireCondition(allowed && (principal.role==="admin" || allowed[operation].includes(principal.role)),"FORBIDDEN","Bu işlem için yetkiniz yok.",403);
}
export function assertTestEnvironment(environment=process.env.APP_ENV) {
 requireCondition(environment==="development"||environment==="test","TEST_PROVIDER_DISABLED","Test ödeme bu ortamda kullanılamaz.",503);
}
const paymentSchema=z.object({id:z.string().min(1).max(200),orderId:z.string().min(1).max(100),amountMinor:z.number().int().nonnegative().max(9_000_000_000_000),currency:z.enum(["TRY","EUR","USD","GBP"]),status:z.enum(["succeeded","failed"]),timestamp:z.number().int().positive()}).strict();
export type PaymentEvent=z.infer<typeof paymentSchema>;
export function signPayment(raw:string,secret:string) {return createHmac("sha256",secret).update(raw).digest("hex");}
export function validatePaymentEnvelope(raw:string,signature:string,secret:string,now=Math.floor(Date.now()/1000)):PaymentEvent {
 requireCondition(secret?.length>=32,"PAYMENT_NOT_CONFIGURED","Ödeme doğrulaması yapılandırılmadı.",503);
 requireCondition(raw.length<=16384 && /^[a-f0-9]{64}$/i.test(signature),"INVALID_SIGNATURE","Ödeme bildirimi doğrulanamadı.",401);
 const expected=Buffer.from(signPayment(raw,secret),"hex"),actual=Buffer.from(signature,"hex");
 requireCondition(expected.length===actual.length&&timingSafeEqual(expected,actual),"INVALID_SIGNATURE","Ödeme bildirimi doğrulanamadı.",401);
 let event:PaymentEvent;
 try {event=paymentSchema.parse(JSON.parse(raw));}catch {throw new DomainError("INVALID_PAYMENT_EVENT","Ödeme bildirimi geçersiz.");}
 requireCondition(Math.abs(now-event.timestamp)<=300,"STALE_EVENT","Ödeme bildiriminin süresi geçersiz.",401);
 return event;
}
