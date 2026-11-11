/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/checkout-pricing.ts
 * Açıklama   : Teklif ve siparişin aynı fiyat, indirim ve vergi hesabını kullanmasını sağlar.
 */
import {z} from 'zod';
import {query,type Connection} from '../db';
import type {CheckoutQuoteInput} from '../../shared/contracts';
import {requireCondition,calculateTotals} from './rules';
import {resolveShippingTaxRule,applyShippingTax,resolveProductTaxRule,calculateMixedProductTax,type ProductTaxRule} from '../shipping-tax';
import {assertShippingPermissions} from './operations';
import {quoteFingerprint,type QuoteBinding} from './quote-token';
export const quoteInputSchema=z.object({country:z.string().regex(/^[A-Z]{2}$/),currency:z.enum(['TRY','EUR','USD','GBP']),locale:z.enum(['tr','en']),couponCode:z.string().trim().min(1).max(60).optional()}).strict();
export function parseQuoteInput(input:unknown):CheckoutQuoteInput{const result=quoteInputSchema.safeParse(input);requireCondition(result.success,'INVALID_CHECKOUT','Teslimat ülkesi, para birimi ve kupon alanlarını kontrol edin.');return result.data;}
export async function evaluateCheckoutPricing(cartId:string,input:CheckoutQuoteInput,connection:Connection,locked=false){
  if(locked){
   // Para kararı boyunca katalog ve set kimliği sabit kalır; stok yazımıyla aynı sıra.
   await query("SELECT pg_advisory_xact_lock_shared(hashtext('bundle-definition'))",[],connection);
   const links=await query(`SELECT v.id,v.product_id FROM variants v WHERE v.id IN(SELECT variant_id FROM cart_items WHERE cart_id=$1 UNION SELECT bc.component_variant_id FROM bundle_components bc JOIN cart_items ci ON ci.variant_id=bc.bundle_variant_id WHERE ci.cart_id=$1) ORDER BY v.id`,[cartId],connection);
   await query('SELECT id FROM products WHERE id=ANY($1::text[]) ORDER BY id FOR SHARE',[[...new Set(links.map(row=>row.product_id))].sort()],connection);
   await query('SELECT id FROM variants WHERE id=ANY($1::text[]) ORDER BY id FOR SHARE',[links.map(row=>row.id)],connection);
  }
  const countries=await query(`SELECT * FROM country_rules WHERE code=$1${locked?' FOR SHARE':''}`,[input.country],connection);const country=countries[0];
  requireCondition(country&&country.enabled&&country.product_approved&&country.age_approved&&country.payment_approved&&country.shipping_approved&&country.tax_approved&&country.legal_approved,"COUNTRY_NOT_APPROVED","Bu teslimat ülkesi için satış henüz açık değil.",409);
  requireCondition(country.shipping_minor!==null&&country.currency===input.currency,"SHIPPING_NOT_CONFIGURED","Teslimat ücreti veya tahsilat para birimi yapılandırılmadı.",409);
  requireCondition(!country.fixture||["development","test"].includes(process.env.APP_ENV??""),"FIXTURE_NOT_ALLOWED","Test ülke kurallarıyla gerçek satış yapılamaz.",503);
  const items=await query(`SELECT ci.quantity,v.*,
   CASE WHEN $2='en' THEN v.name_en ELSE v.name END variant_display_name,
   CASE WHEN $2='en' THEN p.name_en ELSE p.name END product_name,
   CASE WHEN $2='en' THEN p.description_en ELSE p.description END description,
   CASE WHEN $2='en' THEN coalesce(p.translations->'en'->>'warnings','') ELSE p.warnings END warnings,
   CASE WHEN $2='en' THEN coalesce(p.translations->'en'->>'care','') ELSE p.care END care,
   p.image,p.material,p.manufacturer,p.fixture,p.status product_status
   FROM cart_items ci JOIN variants v ON v.id=ci.variant_id JOIN products p ON p.id=v.product_id WHERE ci.cart_id=$1 ORDER BY v.id${locked?' FOR SHARE OF ci,p,v':''}`,[cartId,input.locale],connection);
  requireCondition(items.length>0,"EMPTY_CART","Sepetinize ürün ekleyin.");
  // Lock all physical components in one stable product/SKU order before checking approvals.
  // A component may be sold only as part of a set; standalone publication is not required.
  const allComponents=await query(`SELECT bc.bundle_variant_id,bc.component_variant_id,bc.quantity,v.cost_minor,v.active,p.fixture FROM products p JOIN variants v ON v.product_id=p.id JOIN bundle_components bc ON bc.component_variant_id=v.id WHERE bc.bundle_variant_id=ANY($1::text[]) ORDER BY p.id,v.id,bc.bundle_variant_id ${locked?' FOR SHARE OF p,v,bc':''}`,[items.map(item=>item.id)],connection);
  const nested=allComponents.length?await query('SELECT 1 FROM bundle_components WHERE bundle_variant_id=ANY($1::text[]) LIMIT 1',[allComponents.map(c=>c.component_variant_id)],connection):[];
  requireCondition(!nested.length,'NESTED_BUNDLE_DISABLED','İç içe setler bu sipariş akışında desteklenmiyor.',409);
  const stock=new Map<string,number>();
  const taxRules=new Map<string,ProductTaxRule>();
  for(const item of items) {
   requireCondition(item.active&&item.product_status==="published","PRODUCT_UNAVAILABLE","Sepetteki bir ürün artık satışa açık değil.",409);
   requireCondition(!item.fixture||["development","test"].includes(process.env.APP_ENV??""),"FIXTURE_NOT_ALLOWED","Örnek ürünlerle gerçek satış yapılamaz.",503);
   const components=allComponents.filter(component=>component.bundle_variant_id===item.id);
   for(const component of components){
    requireCondition(component.active,'BUNDLE_COMPONENT_UNAVAILABLE','Setin fiziksel bileşeni satış işlemine kapalıdır.',409);
    requireCondition(!component.fixture||['development','test'].includes(process.env.APP_ENV??''),'FIXTURE_NOT_ALLOWED','Örnek set bileşeni gerçek satışta kullanılamaz.',503);
   }
   const prices=await query(`SELECT variant_id,currency,amount_minor,valid_from,valid_until FROM variant_prices WHERE variant_id=$1 AND currency=$2 AND valid_from<=now() AND(valid_until IS NULL OR valid_until>now())${locked?' FOR SHARE':''}`,[item.id,input.currency],connection);
   requireCondition(prices.length,"PRICE_NOT_CONFIGURED","Seçilen para birimi için fiyat listesi bulunamadı.",409);
   item.price_minor=Number(prices[0].amount_minor);item.price_source=prices[0];
   if(!taxRules.has(item.tax_class))taxRules.set(item.tax_class,await resolveProductTaxRule(input.country,item.tax_class,connection,locked));
   item.tax_rule=taxRules.get(item.tax_class)!;
   item.bundle_components=components.map(c=>({variantId:c.component_variant_id,quantity:c.quantity}));
   if(components.length)item.cost_minor=components.reduce((sum,c)=>sum+Number(c.cost_minor)*c.quantity,0);
   await assertShippingPermissions(components.length?components.map(c=>c.component_variant_id):[item.id],input.country,undefined,connection);
   for(const part of components.length?components:[{component_variant_id:item.id,quantity:1}])stock.set(part.component_variant_id,(stock.get(part.component_variant_id)??0)+part.quantity*item.quantity);
  }
  const agreements=await query("SELECT * FROM legal_documents WHERE kind=ANY($1::text[]) AND locale=$2 AND status='effective' AND effective_at<=now()",[["privacy","terms"],input.locale],connection);
  requireCondition(new Set(agreements.map(a=>a.kind)).size===2,"LEGAL_DOCUMENTS_REQUIRED","Geçerli sözleşme ve aydınlatma metinleri hazırlanmadı.",409);
  requireCondition(agreements.every(a=>!a.fixture||["development","test"].includes(process.env.APP_ENV??"")),"FIXTURE_NOT_ALLOWED","Test sözleşmesiyle gerçek satış yapılamaz.",503);
  const taxInputs=items.map(item=>({grossMinor:item.price_minor*item.quantity,rateBps:Number(item.tax_rule.rateBps)}));
  let productTaxes=calculateMixedProductTax(taxInputs,0);
  const subtotalMinor=productTaxes.subtotalMinor;
  const costMinor=items.reduce((sum,item)=>sum+Number(item.cost_minor)*item.quantity,0);
  let discountMinor=0,coupon:Record<string,unknown>|undefined;
  if(input.couponCode) {
   const rows=await query(`SELECT * FROM coupons WHERE upper(code)=upper($1)${locked?' FOR UPDATE':''}`,[input.couponCode],connection);coupon=rows[0];
   requireCondition(coupon&&coupon.active&&new Date(String(coupon.expires_at)).getTime()>Date.now(),"COUPON_INVALID","Kupon geçerli değil.",409);
   requireCondition(subtotalMinor>=Number(coupon.minimum_minor),"COUPON_MINIMUM","Sepet tutarı kuponun alt sınırını karşılamıyor.",409);
   const [usage]=await query("SELECT count(*)::int n FROM coupon_usage u JOIN orders o ON o.id=u.order_id WHERE u.coupon_id=$1 AND(u.status='consumed' OR(u.status='reserved' AND o.status='awaiting_payment' AND o.expires_at>now()))",[coupon.id],connection);
   requireCondition(usage.n<Number(coupon.max_uses),"COUPON_LIMIT","Kupon kullanım sınırına ulaştı.",409);
   discountMinor=Number((BigInt(subtotalMinor)*BigInt(Number(coupon.discount_bps))+5000n)/10000n);
   productTaxes=calculateMixedProductTax(taxInputs,discountMinor);
   requireCondition(productTaxes.grossAfterDiscountMinor-productTaxes.goodsTaxMinor-costMinor>=Number(coupon.minimum_contribution_minor),"COUPON_MARGIN","Kupon bu sepet için uygulanamıyor.",409);
  }
  const shippingTaxRule=await resolveShippingTaxRule(input.country,country.fixture,connection,locked);
  const totals=applyShippingTax({...calculateTotals(subtotalMinor,Number(country.shipping_minor),discountMinor,0),taxMinor:productTaxes.goodsTaxMinor},shippingTaxRule);
  const [profile]=await query(`SELECT id,version FROM country_address_profiles WHERE country=$1 AND status='approved' AND approved_by IS NOT NULL AND($2 OR fixture=false)${locked?' FOR SHARE':''}`,[input.country,['development','test'].includes(process.env.APP_ENV??'')],connection);
  requireCondition(profile,'ADDRESS_PROFILE_REQUIRED','Bu ülke için teslimat adresi kuralları henüz hazır değil.',409);
  return {country,items,allComponents,stock,taxRules,agreements,productTaxes,subtotalMinor,costMinor,discountMinor,coupon,shippingTaxRule,totals,profile};
}
export type CheckoutPricing=Awaited<ReturnType<typeof evaluateCheckoutPricing>>;
export function pricingQuoteBinding(cartId:string,cartTokenHash:string,input:CheckoutQuoteInput,pricing:CheckoutPricing):QuoteBinding{
 const selection={country:input.country,currency:input.currency,locale:input.locale,couponCode:input.couponCode?.toUpperCase()??null};
 const evaluation={selection,profile:pricing.profile,deliveryTerm:pricing.country.delivery_term,shippingMinor:pricing.country.shipping_minor,
  items:pricing.items.map(item=>({id:item.id,name:item.product_name,variantName:item.variant_display_name,description:item.description,warnings:item.warnings,care:item.care,material:item.material,manufacturer:item.manufacturer,image:item.image,quantity:item.quantity,price:item.price_source,costMinor:item.cost_minor,taxClass:item.tax_class,taxRule:item.tax_rule,bundle:item.bundle_components})),
  coupon:pricing.coupon?Object.fromEntries(['id','code','active','expires_at','minimum_minor','max_uses','discount_bps','minimum_contribution_minor'].map(key=>[key,pricing.coupon![key]])):null,shippingTaxRule:pricing.shippingTaxRule,totals:pricing.totals,
  agreements:pricing.agreements.map(row=>({id:row.id,kind:row.kind,version:row.version,bodyHash:row.body_hash})).sort((a,b)=>a.kind.localeCompare(b.kind))};
 return {cartId,cartTokenHash,selectionHash:quoteFingerprint(selection),evaluationHash:quoteFingerprint(evaluation)};
}
