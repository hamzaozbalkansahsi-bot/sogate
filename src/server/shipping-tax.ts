/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/shipping-tax.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import {z} from 'zod';
import {query,transaction,type Connection} from './db';
import {HttpError} from './security';
import type {Principal} from '../shared/contracts';
import {allocateMinor,calculateTotals} from './commerce/rules';
export interface ShippingTaxRule {id:string|null;rateBps:number;source:string;}
export interface ProductTaxRule {id:string;productClass:string;rateBps:number;source:string|null;validFrom:string;validUntil:string|null;fixture:boolean;}
export async function resolveProductTaxRule(country:string,productClass:string,connection?:Connection,locked=false):Promise<ProductTaxRule>{
 if(!/^[A-Z]{2}$/.test(country)||typeof productClass!=='string'||productClass!==productClass.trim()||productClass.length<1||productClass.length>100)throw new HttpError(400,'Ürün vergi sınıfı geçersiz.','PRODUCT_TAX_CLASS_INVALID');
 const rows=await query(`SELECT t.*,s.value reference FROM tax_rules t LEFT JOIN settings s ON s.key='tax.source.'||t.id WHERE t.country=$1 AND t.product_class=$2 AND t.valid_from<=now() AND(t.valid_until IS NULL OR t.valid_until>now())${locked?' FOR SHARE OF t':''}`,[country,productClass],connection);
 if(!rows.length)throw new HttpError(409,'Bu SKU sınıfı için yürürlükte ürün vergi kuralı gerekir.','PRODUCT_TAX_NOT_CONFIGURED');
 if(rows.length!==1)throw new HttpError(409,'Bu SKU sınıfı için birden fazla vergi kuralı eşleşiyor.','PRODUCT_TAX_AMBIGUOUS');
 const row=rows[0],local=['development','test'].includes(process.env.APP_ENV??'');
 if(row.fixture&&!local)throw new HttpError(503,'Örnek vergi kuralı gerçek satışta kullanılamaz.','FIXTURE_NOT_ALLOWED');
 if(!local&&(typeof row.reference!=='string'||!row.reference.trim()))throw new HttpError(409,'Ürün vergi kuralının onay kaynağı tamamlanmadı.','PRODUCT_TAX_SOURCE_REQUIRED');
 return {id:row.id,productClass:row.product_class,rateBps:Number(row.rate_bps),source:typeof row.reference==='string'?row.reference:null,validFrom:row.valid_from.toISOString(),validUntil:row.valid_until?.toISOString()??null,fixture:row.fixture};
}
export interface ProductTaxInput {grossMinor:number;rateBps:number;}
export interface ProductTaxLine extends ProductTaxInput {discountMinor:number;taxMinor:number;netMinor:number;}
export function calculateMixedProductTax(lines:ProductTaxInput[],discountMinor:number){
 if(!Array.isArray(lines)||!lines.length)throw new HttpError(400,'Ürün vergi hesabı için satır gerekir.','INVALID_PRODUCT_TAX');
 for(const line of lines)calculateTotals(line.grossMinor,0,0,line.rateBps);
 const subtotal=lines.reduce((sum,line)=>sum+BigInt(line.grossMinor),0n);
 if(subtotal>9000000000000n)throw new HttpError(400,'Ürün vergi hesabı tutarı sınırı aşıyor.','INVALID_PRODUCT_TAX');
 const subtotalMinor=Number(subtotal);calculateTotals(subtotalMinor,0,discountMinor,0);
 const discounts=subtotalMinor===0?lines.map(()=>0):allocateMinor(discountMinor,lines.map(line=>line.grossMinor));
 const allocated:ProductTaxLine[]=lines.map((line,i)=>{
  const taxMinor=calculateTotals(line.grossMinor,0,discounts[i],line.rateBps).taxMinor;
  return {...line,discountMinor:discounts[i],taxMinor,netMinor:line.grossMinor-discounts[i]-taxMinor};
 });
 return {subtotalMinor,discountMinor,grossAfterDiscountMinor:subtotalMinor-discountMinor,goodsTaxMinor:allocated.reduce((sum,line)=>sum+line.taxMinor,0),lines:allocated};
}
export async function resolveShippingTaxRule(country:string,fixture:boolean,connection?:Connection,locked=false):Promise<ShippingTaxRule>{
 const rows=await query(`SELECT id,rate_bps,reference FROM shipping_tax_rules WHERE country=$1 AND approved=true AND valid_from<=now() AND(valid_until IS NULL OR valid_until>now())${locked?' FOR SHARE':''}`,[country],connection);
 if(rows.length===1)return {id:rows[0].id,rateBps:rows[0].rate_bps,source:rows[0].reference};
 if(rows.length===0&&fixture&&['development','test'].includes(process.env.APP_ENV??''))return {id:null,rateBps:0,source:'Yalnız izole yerel kargo vergisi senaryosu'};
 throw new HttpError(409,'Bu ülke için onaylı ve yürürlükte kargo vergi kuralı gerekir.','SHIPPING_TAX_NOT_CONFIGURED');
}
interface Totals {subtotalMinor:number;discountMinor:number;shippingMinor:number;taxMinor:number;totalMinor:number;}
export function applyShippingTax(totals:Totals,rule:ShippingTaxRule){
 if(!Number.isInteger(rule.rateBps)||rule.rateBps<0||rule.rateBps>10000||!Number.isSafeInteger(totals.shippingMinor)||totals.shippingMinor<0)throw new HttpError(400,'Kargo vergi hesabı geçersiz.');
 const divisor=BigInt(10000+rule.rateBps);const shippingTaxMinor=Number((BigInt(totals.shippingMinor)*BigInt(rule.rateBps)+divisor/2n)/divisor);
 return {...totals,goodsTaxMinor:totals.taxMinor,shippingTaxMinor,taxMinor:totals.taxMinor+shippingTaxMinor};
}
function permitted(principal:Principal){if(!principal.mfa||!['admin','finance'].includes(principal.role))throw new HttpError(403,'Vergi kuralları için finans yetkisi ve oturum doğrulaması gerekir.');}
const schema=z.object({kind:z.enum(['product','shipping']),country:z.string().regex(/^[A-Z]{2}$/),rateBps:z.number().int().min(0).max(10000),effectiveFrom:z.iso.datetime(),effectiveUntil:z.iso.datetime().optional(),productClass:z.string().trim().min(1).max(100).default('*'),reference:z.string().trim().min(10).max(1000)}).strict();
export async function manageTax(input:unknown,principal:Principal){
 permitted(principal);const data=schema.parse(input);if(data.effectiveUntil&&data.effectiveUntil<=data.effectiveFrom)throw new HttpError(400,'Bitiş tarihi başlangıçtan sonra olmalıdır.');
 return transaction(async connection=>{
  await query('SELECT pg_advisory_xact_lock(hashtextextended($1,0))',[`tax:${data.kind}:${data.country}:${data.productClass}`],connection);
  const table=data.kind==='shipping'?'shipping_tax_rules':'tax_rules';
  const values:unknown[]=[data.country,data.effectiveFrom,data.effectiveUntil??null];
  const extra=data.kind==='product'?(values.push(data.productClass),' AND product_class=$4'):'';
  const overlap=await query(`SELECT id FROM ${table} WHERE country=$1 AND tstzrange(valid_from,coalesce(valid_until,'infinity'::timestamptz),'[)') && tstzrange($2::timestamptz,coalesce($3::timestamptz,'infinity'::timestamptz),'[)')${extra}` ,values,connection);
  if(overlap.length)throw new HttpError(409,'Aynı ülke ve sınıf için çakışan yürürlükte kural var. Mevcut kuralın tarihlerini inceleyin.');
  const [row]=data.kind==='shipping'?await query('INSERT INTO shipping_tax_rules(country,rate_bps,valid_from,valid_until,reference,approved) VALUES($1,$2,$3,$4,$5,true) RETURNING id',[data.country,data.rateBps,data.effectiveFrom,data.effectiveUntil??null,data.reference],connection):await query('INSERT INTO tax_rules(country,product_class,rate_bps,valid_from,valid_until,fixture) VALUES($1,$2,$3,$4,$5,false) RETURNING id',[data.country,data.productClass,data.rateBps,data.effectiveFrom,data.effectiveUntil??null],connection);
  if(data.kind==='product')await query('INSERT INTO settings(key,value) VALUES($1,$2)',[`tax.source.${row.id}`,JSON.stringify(data.reference)],connection);
  await query('INSERT INTO audit_log(actor_id,action,resource,resource_id,details) VALUES($1,\'create\',\'taxes\',$2,$3)',[principal.id,row.id,JSON.stringify({country:data.country,kind:data.kind,reference:data.reference,rateBps:data.rateBps})],connection);return {id:row.id};
 });
}
export async function listTaxes(principal:Principal){permitted(principal);const rows=await query("SELECT id,'product' kind,country,product_class,rate_bps,valid_from,valid_until FROM tax_rules ORDER BY country,valid_from DESC LIMIT 100");const shipping=await query("SELECT id,'shipping' kind,country,'*' product_class,rate_bps,valid_from,valid_until,reference FROM shipping_tax_rules ORDER BY country,valid_from DESC LIMIT 100");return {rows:[...rows,...shipping].map(row=>({id:row.id,kind:row.kind,country:row.country,productClass:row.product_class,rateBps:row.rate_bps,validFrom:row.valid_from.toISOString(),validUntil:row.valid_until?.toISOString()??null,reference:row.reference??null})),total:rows.length+shipping.length};}
