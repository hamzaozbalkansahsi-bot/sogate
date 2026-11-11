/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/operations.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import {z} from 'zod';
import {createHash} from 'node:crypto';
import type {Principal} from '../../shared/contracts';
import {query,transaction,type Connection} from '../db';
import {DomainError,requireCondition} from './rules';
import {receiveLotStock,lockReceiptKey} from './lots';
import {purchaseReceiptSchema,canonicalPurchaseReceipt,type PurchaseReceiptResult} from '../../shared/purchase-receipts';
import {bundleEditorData,bundleCandidates,manageBundle,lockPhysicalStockTargets} from './bundles';

const text=z.string().trim().min(1).max(300);
const money=z.number().int().nonnegative().max(9e12);
const currency=z.enum(['TRY','EUR','USD','GBP']);
const slug=z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/).max(100);
const parse=<T>(schema:z.ZodType<T>,input:unknown):T=>{const out=schema.safeParse(input);requireCondition(out.success,'INVALID_INPUT','Alanları ve biçimlerini kontrol edin.');return out.data;};
const camel=(row:Record<string,unknown>)=>Object.fromEntries(Object.entries(row).map(([k,v])=>[k.replace(/_([a-z])/g,(_,c:string)=>c.toUpperCase()),v instanceof Date?v.toISOString():v]));
async function audit(principal:Principal,action:string,resource:string,id:string,details:Record<string,unknown>={},connection?:Connection){await query('INSERT INTO audit_log(actor_id,action,resource,resource_id,details) VALUES($1,$2,$3,$4,$5)',[principal.id,action,resource,id,JSON.stringify(details)],connection);}
export const operationsResources=new Set(['variants','purchases','campaigns','categories','brands','invoices']);
export async function assertShippingPermissions(variantIds:string[],country:string,carrier:string|undefined,connection?:Connection) {
 const restricted=await query("SELECT id FROM variants WHERE id=ANY($1::text[]) AND((battery_type IS NOT NULL AND battery_type<>'')OR liquid=true)",[variantIds],connection);
 for(const variant of restricted){const rows=await query('SELECT 1 FROM shipping_approvals WHERE variant_id=$1 AND country=$2 AND accepted=true AND(valid_until IS NULL OR valid_until>now())AND($3::text IS NULL OR carrier=lower($3)) LIMIT 1',[variant.id,country,carrier??null],connection);requireCondition(rows.length,'CARRIER_ACCEPTANCE_REQUIRED','Pil veya sıvı içeren ürünün taşıyıcı kabulü doğrulanmalıdır.',409);}
}
export async function listOperations(resource:string,principal:Principal,filter:Record<string,string>={}) {
 if(resource==='variants'&&filter.view==='bundle')return bundleEditorData(filter.id??'',principal);
 if(resource==='variants'&&filter.view==='bundleCandidates')return bundleCandidates(principal,filter);
 const page=Math.max(1,Math.min(100000,Number(filter.page)||1)),limit=25,offset=(page-1)*limit,search=`%${(filter.q??'').slice(0,100).replace(/[\\%_]/g,'\\$&')}%`;
 const finance=['admin','finance'].includes(principal.role);
 let rows:Record<string,unknown>[],total:number;
 if(resource==='variants') {
  const values:unknown[]=[search,filter.productId??null,limit,offset];
  rows=await query(`SELECT v.id,v.product_id,p.name product_name,v.sku,v.name,v.name_en,v.tax_class,v.lot_tracking,v.expiry_required,v.bundle_version,v.price_minor${finance?',v.cost_minor':''},v.currency,v.color,v.size,v.weight_grams,v.battery_type,v.liquid,v.hygiene_sealed,v.active,
   coalesce((SELECT jsonb_agg(jsonb_build_object('currency',vp.currency,'amountMinor',vp.amount_minor)) FROM variant_prices vp WHERE vp.variant_id=v.id),'[]'::jsonb) prices
   FROM variants v JOIN products p ON p.id=v.product_id WHERE(sg_search_normalize(v.sku) LIKE sg_search_normalize($1) OR sg_search_normalize(p.name) LIKE sg_search_normalize($1))AND($2::text IS NULL OR v.product_id=$2) ORDER BY p.name,v.sku LIMIT $3 OFFSET $4`,values);
  total=Number((await query('SELECT count(*) n FROM variants v JOIN products p ON p.id=v.product_id WHERE(sg_search_normalize(v.sku) LIKE sg_search_normalize($1) OR sg_search_normalize(p.name) LIKE sg_search_normalize($1))AND($2::text IS NULL OR v.product_id=$2)',[search,filter.productId??null]))[0].n);
 }else if(resource==='purchases') {
  rows=await query(`SELECT po.id,po.supplier_id,s.name supplier_name,po.status,po.currency,po.created_at,
   coalesce((SELECT jsonb_agg(jsonb_build_object('variantId',pi.variant_id,'sku',v.sku,'lotTracking',v.lot_tracking,'expiryRequired',v.expiry_required,'quantity',pi.quantity,'received',pi.received,'remaining',pi.quantity-pi.received${finance?",'unitCostMinor',pi.unit_cost_minor":''})) FROM purchase_items pi JOIN variants v ON v.id=pi.variant_id WHERE pi.purchase_id=po.id),'[]'::jsonb) items
   FROM purchase_orders po JOIN suppliers s ON s.id=po.supplier_id WHERE sg_search_normalize(s.name) LIKE sg_search_normalize($1) ORDER BY po.created_at DESC LIMIT $2 OFFSET $3`,[search,limit,offset]);
  total=Number((await query('SELECT count(*) n FROM purchase_orders po JOIN suppliers s ON s.id=po.supplier_id WHERE sg_search_normalize(s.name) LIKE sg_search_normalize($1)',[search]))[0].n);
 }else {
  const specs:Record<string,{table:string,fields:string,search:string,order:string}>={
   campaigns:{table:'coupons',fields:'id,code,discount_bps,minimum_minor,max_uses,used_count,minimum_contribution_minor,expires_at,active',search:'code',order:'code'},
   categories:{table:'categories',fields:'slug,name,name_en,active',search:'name',order:'name'},
   brands:{table:'brands',fields:'slug,name,name_en,active',search:'name',order:'name'},
   invoices:{table:'invoice_references',fields:'id,order_id,provider,external_reference,document_kind,actor_id,note,created_at',search:'external_reference',order:'created_at DESC'}
  };const spec=specs[resource];requireCondition(spec,'UNKNOWN_RESOURCE','Bölüm bulunamadı.',404);
  rows=await query(`SELECT ${spec.fields} FROM ${spec.table} WHERE sg_search_normalize(${spec.search}) LIKE sg_search_normalize($1) ORDER BY ${spec.order} LIMIT $2 OFFSET $3`,[search,limit,offset]);
  total=Number((await query(`SELECT count(*) n FROM ${spec.table} WHERE sg_search_normalize(${spec.search}) LIKE sg_search_normalize($1)`,[search]))[0].n);
 }
 return {rows:rows.map(camel),total,page};
}
const variantFields=z.object({taxClass:z.string().trim().min(1).max(100).optional(),sku:z.string().trim().min(1).max(100),name:text,nameEn:text,priceMinor:money,costMinor:money.optional(),color:z.string().max(100).nullable().optional(),size:z.string().max(100).nullable().optional(),weightGrams:z.number().int().nonnegative().max(10000000).optional(),batteryType:z.string().trim().max(100).nullable().optional(),liquid:z.boolean().optional(),hygieneSealed:z.boolean().optional()});
async function variantAction(input:unknown,principal:Principal) {
 const record=input as Record<string,unknown>;
 if(record.action==='shippingApproval') {
  requireCondition(principal.role==='admin','FORBIDDEN','Taşıma uygunluğu onayı için yönetici yetkisi gerekir.',403);
  const d=parse(z.object({action:z.literal('shippingApproval'),id:text,carrier:text,country:z.string().regex(/^[A-Z]{2}$/),accepted:z.boolean(),reference:z.string().trim().min(10).max(1000),validUntil:z.iso.datetime().optional()}).strict(),input);
  await query('INSERT INTO shipping_approvals(variant_id,carrier,country,accepted,reviewed_by,reference,valid_until) VALUES($1,lower($2),$3,$4,$5,$6,$7) ON CONFLICT(variant_id,carrier,country) DO UPDATE SET accepted=excluded.accepted,reviewed_by=excluded.reviewed_by,reference=excluded.reference,valid_until=excluded.valid_until,created_at=now()',[d.id,d.carrier,d.country,d.accepted,principal.id,d.reference,d.validUntil??null]);await audit(principal,'shippingApproval','variants',d.id,{carrier:d.carrier,country:d.country,accepted:d.accepted,reference:d.reference});return {id:d.id};
 }
 if(record.action==='bundle'||record.action==='bundlePreview')return manageBundle(input,principal);
 if(record.action==='prices') {
  const d=parse(z.object({action:z.literal('prices'),id:text,prices:z.array(z.object({currency,amountMinor:money}).strict()).min(1).max(4),reason:z.string().min(5).max(500)}).strict(),input);
  requireCondition(new Set(d.prices.map(p=>p.currency)).size===d.prices.length,'DUPLICATE_CURRENCY','Aynı para birimi bir kez girilebilir.');
  return transaction(async c=>{
   const [v]=await query('SELECT id,currency FROM variants WHERE id=$1 FOR UPDATE',[d.id],c);requireCondition(v,'VARIANT_NOT_FOUND','Varyant bulunamadı.',404);
   for(const price of d.prices){await query('INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES($1,$2,$3) ON CONFLICT(variant_id,currency) DO UPDATE SET amount_minor=excluded.amount_minor,valid_from=now(),valid_until=null',[d.id,price.currency,price.amountMinor],c);if(price.currency===v.currency)await query('UPDATE variants SET price_minor=$2 WHERE id=$1',[d.id,price.amountMinor],c);}
   await audit(principal,'prices','variants',d.id,{prices:d.prices,reason:d.reason},c);return {id:d.id};
  });
 }
 requireCondition(['admin','catalog'].includes(principal.role),'FORBIDDEN','Varyant düzenleme için katalog yetkisi gerekir.',403);
 if(record.action==='archive') {const d=parse(z.object({action:z.literal('archive'),id:text}).strict(),input);await query('UPDATE variants SET active=false WHERE id=$1',[d.id]);await audit(principal,'archive','variants',d.id);return {id:d.id,active:false};}
 try {
  if(record.action==='create') {
   const d=parse(variantFields.extend({action:z.literal('create'),productId:text}).strict(),input);
   return await transaction(async c=>{
    const [product]=await query('SELECT id,status FROM products WHERE id=$1 FOR UPDATE',[d.productId],c);requireCondition(product,'PRODUCT_NOT_FOUND','Ürün bulunamadı.',404);
    const [v]=await query('INSERT INTO variants(product_id,sku,name,name_en,price_minor,cost_minor,color,size,weight_grams,battery_type,liquid,hygiene_sealed,tax_class) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13) RETURNING id',[d.productId,d.sku,d.name,d.nameEn,d.priceMinor,d.costMinor??0,d.color??null,d.size??null,d.weightGrams??0,d.batteryType??null,d.liquid??false,d.hygieneSealed??false,d.taxClass??'*'],c);
    await query("INSERT INTO inventory_balance(variant_id,warehouse_id) VALUES($1,'main')",[v.id],c);await query("INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES($1,'TRY',$2)",[v.id,d.priceMinor],c);
    if(product.status==='published'){await query("UPDATE products SET status='review',updated_at=now() WHERE id=$1",[product.id],c);await query('UPDATE product_eligibility SET approved=false WHERE variant_id IN(SELECT id FROM variants WHERE product_id=$1)',[product.id],c);}
    await audit(principal,'create','variants',v.id,{productId:d.productId,sku:d.sku,reviewRequired:product.status==='published'},c);return {id:v.id};
   });
  }
  const d=parse(variantFields.partial().extend({action:z.literal('update'),id:text}).strict(),input);
  return await transaction(async c=>{
   const [link]=await query('SELECT product_id FROM variants WHERE id=$1',[d.id],c);requireCondition(link,'VARIANT_NOT_FOUND','Varyant bulunamadı.',404);
   await query('SELECT id FROM products WHERE id=$1 FOR UPDATE',[link.product_id],c);
   const [v]=await query('SELECT * FROM variants WHERE id=$1 FOR UPDATE',[d.id],c);requireCondition(v,'VARIANT_NOT_FOUND','Varyant bulunamadı.',404);
   const map:Record<string,string>={taxClass:'tax_class',sku:'sku',name:'name',nameEn:'name_en',priceMinor:'price_minor',costMinor:'cost_minor',color:'color',size:'size',weightGrams:'weight_grams',batteryType:'battery_type',liquid:'liquid',hygieneSealed:'hygiene_sealed'};
   const entries=Object.entries(d).filter(([key])=>key in map);requireCondition(entries.length,'NO_CHANGES','Değiştirilecek alan bulunamadı.');
   const technicalChanged=entries.some(([key,value])=>!['priceMinor','costMinor'].includes(key)&&v[map[key]]!==value);
   await query(`UPDATE variants SET ${entries.map(([key],i)=>`${map[key]}=$${i+2}`).join(',')} WHERE id=$1`,[d.id,...entries.map(([,value])=>value)],c);
   if(d.priceMinor!==undefined)await query('INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES($1,$2,$3) ON CONFLICT(variant_id,currency) DO UPDATE SET amount_minor=excluded.amount_minor,valid_from=now()',[d.id,v.currency,d.priceMinor],c);
   if(technicalChanged){await query("UPDATE products SET status='review',updated_at=now() WHERE id=$1 AND status='published'",[v.product_id],c);await query('UPDATE product_eligibility SET approved=false WHERE variant_id=$1',[d.id],c);await query('UPDATE shipping_approvals SET accepted=false WHERE variant_id=$1',[d.id],c);await query('UPDATE product_documents SET reviewed=false WHERE variant_id=$1',[d.id],c);}
   await audit(principal,'update','variants',d.id,{fields:entries.map(([key])=>key),reviewRequired:technicalChanged},c);return {id:d.id};
  });
 }catch(error){if((error as {code?:string}).code==='23505')throw new DomainError('DUPLICATE_SKU','SKU veya barkod başka bir varyantta kullanılıyor.',409);throw error;}
}
async function purchaseAction(input:unknown,principal:Principal) {
 const record=input as Record<string,unknown>;
 if(record.action==='create') {
  requireCondition(['admin','catalog'].includes(principal.role),'FORBIDDEN','Satın alma oluşturmak için katalog yetkisi gerekir.',403);
  const d=parse(z.object({action:z.literal('create'),supplierId:text,currency,items:z.array(z.object({variantId:text,quantity:z.number().int().positive().max(1000000),unitCostMinor:money}).strict()).min(1).max(100)}).strict(),input);
  requireCondition(new Set(d.items.map(i=>i.variantId)).size===d.items.length,'DUPLICATE_VARIANT','Aynı varyant bir satırda bulunmalıdır.');
  return transaction(async c=>{
   const [supplier]=await query('SELECT id FROM suppliers WHERE id=$1 AND archived=false',[d.supplierId],c);requireCondition(supplier,'SUPPLIER_NOT_FOUND','Tedarikçi bulunamadı.',404);
   const [purchase]=await query("INSERT INTO purchase_orders(supplier_id,status,currency) VALUES($1,'ordered',$2) RETURNING id",[d.supplierId,d.currency],c);
   for(const item of d.items)await query('INSERT INTO purchase_items(purchase_id,variant_id,quantity,unit_cost_minor) VALUES($1,$2,$3,$4)',[purchase.id,item.variantId,item.quantity,item.unitCostMinor],c);
   await audit(principal,'create','purchases',purchase.id,{items:d.items},c);return {id:purchase.id,status:'ordered'};
  });
 }
 requireCondition(['admin','warehouse'].includes(principal.role),'FORBIDDEN','Mal kabulü için depo yetkisi gerekir.',403);
 const legacySchema=z.object({action:z.literal('receive'),id:text,idempotencyKey:z.string().min(16).max(128),items:z.array(z.object({variantId:text,quantity:z.number().int().positive().max(1000000)}).strict()).min(1).max(100),reason:z.string().min(5).max(500)}).strict();
 const current=purchaseReceiptSchema.safeParse(input),legacy=legacySchema.safeParse(input);requireCondition(current.success||legacy.success,'INVALID_INPUT','Mal kabulü kaynak, lot ve adet alanlarını kontrol edin.');
 const envelope=current.success?current.data:legacy.data!;
 const v2Hash=current.success?createHash('sha256').update(JSON.stringify({version:2,actor:principal.id,data:canonicalPurchaseReceipt(current.data)})).digest('hex'):null;
 const v1Hash=legacy.success?createHash('sha256').update(JSON.stringify(legacy.data)).digest('hex'):null;
 return transaction(async c=>{
  await lockReceiptKey(envelope.idempotencyKey,c);
  requireCondition(!(await query('SELECT 1 FROM lot_operations WHERE idempotency_key=$1',[envelope.idempotencyKey],c)).length,'IDEMPOTENCY_CONFLICT','Bu kabul anahtarı başka bir stok işleminde kullanılmış.',409);
  const [purchase]=await query('SELECT * FROM purchase_orders WHERE id=$1 FOR UPDATE',[envelope.id],c);requireCondition(purchase,'PURCHASE_NOT_FOUND','Satın alma bulunamadı.',404);
  const [existing]=await query('SELECT id,request_hash,request_version,actor_id FROM purchase_receipts WHERE idempotency_key=$1',[envelope.idempotencyKey],c);
  if(existing){requireCondition(existing.actor_id===principal.id&&existing.request_hash===(existing.request_version===1?v1Hash:v2Hash),'IDEMPOTENCY_CONFLICT','Aynı kabul anahtarı başka içerik veya kişiyle kullanılamaz.',409);return {id:String(existing.id),duplicate:true} satisfies PurchaseReceiptResult;}
  requireCondition(current.success,'RECEIPT_SOURCE_REQUIRED','Yeni mal kabulünde gerçek teslimat belgesi referansını girin.',409);const d=canonicalPurchaseReceipt(current.data);
  requireCondition(['ordered','partially_received'].includes(purchase.status),'PURCHASE_NOT_RECEIVABLE','Satın alma mal kabulüne uygun değil.',409);
  const lines=await query('SELECT * FROM purchase_items WHERE purchase_id=$1 ORDER BY variant_id FOR UPDATE',[d.id],c);
  for(const item of d.items){const line=lines.find(l=>l.variant_id===item.variantId);requireCondition(line&&line.received+item.quantity<=line.quantity,'OVER_RECEIPT','Mal kabulü kalan sipariş adedini aşamaz.',409);}
  await lockPhysicalStockTargets(d.items.map(i=>i.variantId),c);
  const variants=await query('SELECT id,lot_tracking,expiry_required FROM variants WHERE id=ANY($1::text[]) ORDER BY id',[d.items.map(i=>i.variantId)],c);
  for(const item of d.items){const variant=variants.find(row=>row.id===item.variantId)!;requireCondition(variant.lot_tracking?!!item.lots?.length:!item.lots,'LOT_ACTION_REQUIRED',variant.lot_tracking?'Lot takipli kabulde üretici lotlarını girin.':'Takipsiz stok koduna lot satırı eklenemez.',409);}
  await query("SELECT variant_id FROM inventory_balance WHERE variant_id=ANY($1::text[]) AND warehouse_id='main' ORDER BY variant_id FOR UPDATE",[d.items.map(i=>i.variantId)],c);
  const [receipt]=await query('INSERT INTO purchase_receipts(purchase_id,idempotency_key,request_hash,actor_id,reason,source_reference,request_version) VALUES($1,$2,$3,$4,$5,$6,2) RETURNING id',[d.id,d.idempotencyKey,v2Hash,principal.id,d.reason,d.sourceReference],c);
  for(const item of d.items){
   await query('INSERT INTO purchase_receipt_items(receipt_id,variant_id,quantity) VALUES($1,$2,$3)',[receipt.id,item.variantId,item.quantity],c);
   if(item.lots){for(const lot of item.lots){
    const received=await receiveLotStock({...lot,variantId:item.variantId,reason:d.reason},{connection:c,actorId:principal.id,reference:`purchase:${receipt.id}:${item.variantId}:${createHash('sha256').update(lot.lotNumber).digest('hex')}`,movementType:'purchase_lot_receipt'});
    await query('INSERT INTO purchase_receipt_lots(receipt_id,variant_id,lot_id,movement_id,quantity,quarantine_quantity,source_reference)VALUES($1,$2,$3,$4,$5,$6,$7)',[receipt.id,item.variantId,received.lotId,received.movementId,lot.quantity,received.quarantineQuantity,lot.sourceReference],c);
   }}else{
    await query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand) VALUES($1,'main',$2) ON CONFLICT(variant_id,warehouse_id) DO UPDATE SET on_hand=inventory_balance.on_hand+excluded.on_hand",[item.variantId,item.quantity],c);
    await query("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,reason,reference,actor_id) VALUES($1,'main','purchase_receipt',$2,$3,$4,$5)",[item.variantId,item.quantity,d.reason,`purchase:${receipt.id}:${item.variantId}`,principal.id],c);
   }
   await query('UPDATE purchase_items SET received=received+$3 WHERE purchase_id=$1 AND variant_id=$2',[d.id,item.variantId,item.quantity],c);
  }
  const complete=lines.every(line=>line.received+(d.items.find(i=>i.variantId===line.variant_id)?.quantity??0)===line.quantity);const status=complete?'received':'partially_received';await query('UPDATE purchase_orders SET status=$2 WHERE id=$1',[d.id,status],c);await audit(principal,'receive','purchases',d.id,{receiptId:receipt.id,sourceReference:d.sourceReference,items:d.items},c);return {id:String(receipt.id),status} satisfies PurchaseReceiptResult;
 });
}
export async function performOperation(resource:string,input:unknown,principal:Principal):Promise<unknown> {
 if(resource==='variants')return variantAction(input,principal);
 if(resource==='purchases')return purchaseAction(input,principal);
 if(resource==='categories'||resource==='brands') {
  const r=input as Record<string,unknown>,table=resource==='categories'?'categories':'brands';
  if(r.action==='archive'){const d=parse(z.object({action:z.literal('archive'),slug}).strict(),input);await query(`UPDATE ${table} SET active=false WHERE slug=$1`,[d.slug]);await audit(principal,'archive',resource,d.slug);return {slug:d.slug,active:false};}
  const d=parse(z.object({action:z.enum(['create','update']),slug,name:text,nameEn:text}).strict(),input);
  if(d.action==='create')await query(`INSERT INTO ${table}(slug,name,name_en) VALUES($1,$2,$3)`,[d.slug,d.name,d.nameEn]);else {const rows=await query(`UPDATE ${table} SET name=$2,name_en=$3 WHERE slug=$1 RETURNING slug`,[d.slug,d.name,d.nameEn]);requireCondition(rows.length,'TAXONOMY_NOT_FOUND','Kayıt bulunamadı.',404);}
  await audit(principal,d.action,resource,d.slug);return {slug:d.slug};
 }
 if(resource==='campaigns') {
  const r=input as Record<string,unknown>;
  if(r.action==='archive'){const d=parse(z.object({action:z.literal('archive'),id:text}).strict(),input);await query('UPDATE coupons SET active=false WHERE id=$1',[d.id]);await audit(principal,'archive','campaigns',d.id);return {id:d.id};}
  const d=parse(z.object({action:z.enum(['create','update']),id:text.optional(),code:z.string().trim().regex(/^[A-Za-z0-9_-]{2,60}$/),discountBps:z.number().int().min(1).max(10000),minimumMinor:money,maxUses:z.number().int().positive().max(1000000),minimumContributionMinor:money,expiresAt:z.iso.datetime(),active:z.boolean()}).strict(),input);
  requireCondition(new Date(d.expiresAt).getTime()>Date.now(),'CAMPAIGN_EXPIRED','Bitiş zamanı gelecekte olmalıdır.');
  return transaction(async c=>{
   let id=d.id;
   if(d.action==='create'){const [row]=await query('INSERT INTO coupons(code,discount_bps,minimum_minor,max_uses,minimum_contribution_minor,expires_at,active) VALUES(upper($1),$2,$3,$4,$5,$6,$7) RETURNING id',[d.code,d.discountBps,d.minimumMinor,d.maxUses,d.minimumContributionMinor,d.expiresAt,d.active],c);id=row.id;}
   else{requireCondition(id,'CAMPAIGN_ID_REQUIRED','Kampanya seçin.');const [row]=await query('SELECT used_count FROM coupons WHERE id=$1 FOR UPDATE',[id],c);requireCondition(row&&d.maxUses>=row.used_count,'CAMPAIGN_LIMIT','Kullanım sınırı mevcut kullanımdan düşük olamaz.',409);await query('UPDATE coupons SET code=upper($2),discount_bps=$3,minimum_minor=$4,max_uses=$5,minimum_contribution_minor=$6,expires_at=$7,active=$8 WHERE id=$1',[id,d.code,d.discountBps,d.minimumMinor,d.maxUses,d.minimumContributionMinor,d.expiresAt,d.active],c);}
   await audit(principal,d.action,'campaigns',id!,{code:d.code,discountBps:d.discountBps,maxUses:d.maxUses},c);return {id};
  });
 }
 if(resource==='invoices') {
  const d=parse(z.object({action:z.literal('register').default('register'),orderId:text,provider:text,reference:z.string().trim().min(3).max(200),documentKind:z.enum(['e_invoice','e_archive','credit_note']),note:z.string().trim().min(10).max(1000)}).strict(),input);
  return transaction(async c=>{
   const [order]=await query('SELECT id,payment_status FROM orders WHERE id=$1 FOR UPDATE',[d.orderId],c);requireCondition(order&&['succeeded','partially_refunded','refunded'].includes(order.payment_status),'INVOICE_ORDER_REQUIRED','Belge referansı doğrulanmış siparişe bağlanmalıdır.',409);
   const seller=await query("SELECT key,value FROM settings WHERE key=ANY($1::text[])",[['seller.name','seller.taxNumber','seller.address','seller.supportEmail','seller.phone']],c);requireCondition(seller.length===5&&seller.every(s=>typeof s.value==='string'&&s.value.trim()),'SELLER_NOT_CONFIGURED','Mali belge referansı için satıcı bilgileri doğrulanmalıdır.',409);
   const existing=await query('SELECT id,order_id FROM invoice_references WHERE provider=$1 AND external_reference=$2',[d.provider,d.reference],c);if(existing.length){requireCondition(existing[0].order_id===d.orderId,'INVOICE_REFERENCE_CONFLICT','Belge referansı başka siparişe bağlı.',409);return {id:existing[0].id,duplicate:true};}
   const [row]=await query('INSERT INTO invoice_references(order_id,provider,external_reference,document_kind,actor_id,note) VALUES($1,$2,$3,$4,$5,$6) RETURNING id',[d.orderId,d.provider,d.reference,d.documentKind,principal.id,d.note],c);await audit(principal,'register_external_reference','invoices',row.id,{orderId:d.orderId,provider:d.provider,documentKind:d.documentKind},c);return {id:row.id,status:'external_reference',fiscalDocumentGenerated:false};
  });
 }
 throw new DomainError('UNKNOWN_OPERATION','Operasyon bulunamadı.',404);
}
