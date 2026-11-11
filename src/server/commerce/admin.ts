/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/admin.ts
 * Açıklama   : Yetkili yönetim işlemleri ve denetlenebilir operasyon akışları.
 */
import { z } from "zod";
import { createHash } from "node:crypto";
import type { Principal } from "../../shared/contracts";
import { query, transaction, type Connection } from "../db";
import { getOrder } from "./orders";
import { assertPermission, assertTestEnvironment, DomainError, requireCondition } from "./rules";
import {operationsResources,listOperations,performOperation,assertShippingPermissions} from './operations';
import {operationReports} from './reports';
import {receiveReturnStock,getLockedReturnStockLines} from './return-stock';
import {listLots,manageLot,assertUntrackedStock,assertOrderLotsShippable,trackedAvailable} from './lots';
import {lockPhysicalStockTargets} from './bundles';

const camel=(row:Record<string,unknown>)=>Object.fromEntries(Object.entries(row).map(([k,v])=>[k.replace(/_([a-z])/g,(_,c:string)=>c.toUpperCase()),v instanceof Date?v.toISOString():v]));
export async function audit(principal:Principal,action:string,resource:string,id:string|undefined,details:Record<string,unknown>={},connection?:Connection) {
 await query("INSERT INTO audit_log(actor_id,action,resource,resource_id,details) VALUES($1,$2,$3,$4,$5)",[principal.id,action,resource,id??null,JSON.stringify(details)],connection);
}
function parse<T>(schema:z.ZodType<T>,value:unknown):T {const result=schema.safeParse(value);requireCondition(result.success,"INVALID_INPUT","Alanları ve biçimlerini kontrol edin.");return result.data;}
const string=z.string().trim().min(1).max(500);
export async function adminList(resource:string,principal:Principal,filter:Record<string,string>={}) {
 assertPermission(principal,resource,"read");
 if(resource==='lots')return listLots(principal,filter);
 if(operationsResources.has(resource))return listOperations(resource,principal,filter);
 if(resource==='reports')return operationReports();
 if(resource==='legal'&&principal.role!=='admin') {const rows=await query("SELECT id,kind,locale,title,version,status,body_hash,effective_at FROM legal_documents WHERE status='effective' ORDER BY effective_at DESC LIMIT 25");return {rows:rows.map(camel),total:rows.length,page:1};}
 const page=Math.max(1,Math.min(100000,Number(filter.page)||1)),limit=25,offset=(page-1)*limit;
 const search=`%${(filter.q??"").slice(0,100).replace(/[\\%_]/g,"\\$&")}%`;
 const finance=["admin","finance"].includes(principal.role);
 let rows:Record<string,unknown>[]=[],total=0;
 if(resource==="products") {
  rows=await query(`SELECT p.id,p.name,p.name_en,p.slug,p.category,p.status,p.image,p.material,p.brand,p.manufacturer,p.description,p.description_en,p.warnings,p.care,p.translations->'en'->>'warnings' warnings_en,p.translations->'en'->>'care' care_en,v.id variant_id,v.sku,v.name variant_name,v.name_en variant_name_en,v.tax_class,v.price_minor${finance?",v.cost_minor":""},coalesce(b.on_hand,0)::int on_hand,coalesce(b.quarantine,0)::int quarantine
   FROM products p LEFT JOIN variants v ON v.product_id=p.id LEFT JOIN inventory_balance b ON b.variant_id=v.id AND b.warehouse_id='main' WHERE(sg_search_normalize(p.name) LIKE sg_search_normalize($1) OR sg_search_normalize(v.sku) LIKE sg_search_normalize($1))AND($4::text IS NULL OR p.id=$4) ORDER BY p.created_at DESC,v.id LIMIT $2 OFFSET $3`,[search,limit,offset,filter.productId??filter.id??null]);
  total=Number((await query("SELECT count(*) n FROM products p LEFT JOIN variants v ON v.product_id=p.id WHERE(sg_search_normalize(p.name) LIKE sg_search_normalize($1) OR sg_search_normalize(v.sku) LIKE sg_search_normalize($1))AND($2::text IS NULL OR p.id=$2)",[search,filter.productId??filter.id??null]))[0].n);
 } else if(resource==="inventory") {
  rows=await query(`SELECT v.id,v.id variant_id,v.sku,v.lot_tracking,v.expiry_required,p.name,b.on_hand,b.quarantine,b.safety_stock,b.minimum_stock,coalesce(r.qty,0)::int reserved,greatest(0,b.on_hand-b.safety_stock-coalesce(r.qty,0))::int available
   FROM inventory_balance b JOIN variants v ON v.id=b.variant_id JOIN products p ON p.id=v.product_id LEFT JOIN(SELECT variant_id,sum(quantity) qty FROM reservations WHERE status='active' AND expires_at>now() GROUP BY variant_id)r ON r.variant_id=v.id
   WHERE sg_search_normalize(p.name) LIKE sg_search_normalize($1) OR sg_search_normalize(v.sku) LIKE sg_search_normalize($1) ORDER BY v.sku LIMIT $2 OFFSET $3`,[search,limit,offset]);
  total=Number((await query("SELECT count(*) n FROM inventory_balance b JOIN variants v ON v.id=b.variant_id JOIN products p ON p.id=v.product_id WHERE sg_search_normalize(p.name) LIKE sg_search_normalize($1) OR sg_search_normalize(v.sku) LIKE sg_search_normalize($1)",[search]))[0].n);
 } else if(resource==="orders") {
  const fields=principal.role==="warehouse"?"id,number,status,payment_status,fulfillment_status,created_at":"id,number,status,payment_status,fulfillment_status,total_minor,currency,created_at";
  rows=await query(`SELECT ${fields} FROM orders WHERE sg_search_normalize(number) LIKE sg_search_normalize($1) ORDER BY created_at DESC LIMIT $2 OFFSET $3`,[search,limit,offset]);
  total=Number((await query("SELECT count(*) n FROM orders WHERE sg_search_normalize(number) LIKE sg_search_normalize($1)",[search]))[0].n);
 } else {
  const resources:Record<string,{table:string,fields:string,search:string,order:string}>= {
   shipments:{table:"shipments",fields:"id,order_id,carrier,tracking_number,status,created_at",search:"tracking_number",order:"created_at DESC"},
   returns:{table:"returns",fields:"id,order_id,variant_id,quantity,reason,seal_intact,status,decision_reason,qc_reason,restocked,refund_minor,created_at",search:"reason",order:"created_at DESC"},
   content:{table:"content_pages",fields:"id,slug,locale,title,status,version,updated_at",search:"title",order:"updated_at DESC"},
   settings:{table:"settings",fields:"key,value,updated_at",search:"key",order:"key"},
   countries:{table:"country_rules",fields:"code,name,enabled,product_approved,age_approved,payment_approved,shipping_approved,tax_approved,legal_approved,shipping_minor,currency,fixture",search:"name",order:"name"},
   jobs:{table:"jobs",fields:"id,type,status,attempts,max_attempts,available_at,lease_until,last_error,created_at",search:"type",order:"created_at DESC"},
   audit:{table:"audit_log",fields:"id,actor_id,action,resource,resource_id,details,created_at",search:"resource",order:"created_at DESC"},
   suppliers:{table:"suppliers",fields:"id,name,lead_days,archived",search:"name",order:"name"},
   customers:{table:"orders",fields:"id,user_id,number,email,created_at",search:"email",order:"created_at DESC"},
   legal:{table:"legal_documents",fields:"id,kind,locale,title,body,version,status,body_hash,approved_at,effective_at,fixture",search:"title",order:"created_at DESC"},
   purchases:{table:"purchase_orders",fields:"id,supplier_id,status,currency,created_at",search:"status",order:"created_at DESC"}
  };
  const spec=resources[resource];requireCondition(spec,"UNKNOWN_RESOURCE","Bu bölüm bulunamadı.",404);
  rows=await query(`SELECT ${spec.fields} FROM ${spec.table} WHERE sg_search_normalize(${spec.search}) LIKE sg_search_normalize($1) ORDER BY ${spec.order} LIMIT $2 OFFSET $3`,[search,limit,offset]);
  total=Number((await query(`SELECT count(*) n FROM ${spec.table} WHERE sg_search_normalize(${spec.search}) LIKE sg_search_normalize($1)`,[search]))[0].n);
 }
 if(resource==='inventory')for(const row of rows){const tracked=await trackedAvailable(String(row.variant_id),'main');if(tracked!==null)row.available=tracked;}
 return {rows:rows.map(camel),total,page};
}
const productSchema=z.object({action:z.literal("create").optional(),name:string,nameEn:string,slug:z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/).max(120),category:string,brand:z.string().max(100).default(""),description:z.string().max(10000).default(""),descriptionEn:z.string().max(10000).default(""),sku:z.string().min(1).max(100),taxClass:z.string().trim().min(1).max(100).default('*'),variantName:string,variantNameEn:z.string().max(500).default(''),priceMinor:z.number().int().min(1).max(9e12),costMinor:z.number().int().min(0).max(9e12).default(0),material:z.string().max(200).default(""),image:z.string().regex(/^\/(?:media|uploads)\/[a-zA-Z0-9/_.-]+$/).max(500),warnings:z.string().max(5000).default(""),care:z.string().max(5000).default(""),warningsEn:z.string().max(5000).default(''),careEn:z.string().max(5000).default(''),manufacturer:z.string().max(300).optional()}).strict();
async function productAction(input:unknown,principal:Principal) {
 const record=input as Record<string,unknown>;
 if(!record.action||record.action==="create") {
  const data=parse(productSchema,input);
  return transaction(async connection=>{
   await query("INSERT INTO categories(slug,name,name_en) VALUES($1,$1,$1) ON CONFLICT DO NOTHING",[data.category],connection);
   const [p]=await query("INSERT INTO products(slug,name,name_en,description,description_en,category,brand,image,material,warnings,care,manufacturer,translations) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13) RETURNING id",[data.slug,data.name,data.nameEn,data.description,data.descriptionEn,data.category,data.brand,data.image,data.material,data.warnings,data.care,data.manufacturer??null,JSON.stringify({en:{warnings:data.warningsEn,care:data.careEn}})],connection);
   const [v]=await query("INSERT INTO variants(product_id,sku,name,name_en,price_minor,cost_minor,tax_class) VALUES($1,$2,$3,$4,$5,$6,$7) RETURNING id",[p.id,data.sku,data.variantName,data.variantNameEn,data.priceMinor,data.costMinor,data.taxClass],connection);
   await query("INSERT INTO inventory_balance(variant_id,warehouse_id) VALUES($1,'main')",[v.id],connection);
   await query("INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES($1,'TRY',$2)",[v.id,data.priceMinor],connection);
   await audit(principal,"create","products",p.id,{sku:data.sku},connection);
   return {id:p.id,variantId:v.id,status:"draft"};
  });
 }
 if(record.action==="archive") {
  const data=parse(z.object({action:z.literal("archive"),id:string}).strict(),input);
  await query("UPDATE products SET status='archived',updated_at=now() WHERE id=$1",[data.id]);await audit(principal,"archive","products",data.id);return {id:data.id,status:"archived"};
 }
 if(record.action==="publish") {
  const data=parse(z.object({action:z.literal("publish"),id:string,country:z.string().length(2).default("TR"),reviewNote:z.string().min(5).max(1000)}).strict(),input);
  return transaction(async connection=>{
   const [product]=await query("SELECT * FROM products WHERE id=$1 FOR UPDATE",[data.id],connection);
   requireCondition(product,"PRODUCT_NOT_FOUND","Ürün bulunamadı.",404);
   requireCondition(product.description&&product.description_en&&product.warnings&&product.care,"CONTENT_REQUIRED","Açıklama, İngilizce içerik, bakım ve uyarıları tamamlayın.",409);
   const variants=await query("SELECT * FROM variants WHERE product_id=$1 AND active=true",[data.id],connection);
   requireCondition(variants.length,'VARIANT_REQUIRED','Yayın için etkin varyant gerekir.',409);
   if(!product.fixture)requireCondition(product.translations?.en?.warnings&&product.translations?.en?.care&&variants.every(v=>v.name_en),'TRANSLATION_REQUIRED','İngilizce uyarı, bakım ve varyant adlarını tamamlayın.',409);
   if(!["development","test"].includes(process.env.APP_ENV??""))requireCondition(product.manufacturer&&!product.fixture,"PRODUCT_REVIEW_REQUIRED","Üretici ve gerçek ürün kanıtları doğrulanmalıdır.",409);
   const {assertPublicationEligibility}=await import('../compliance');
   await assertPublicationEligibility(variants.map(v=>v.id),data.country,connection);
   await query("UPDATE products SET status='published',updated_at=now() WHERE id=$1",[data.id],connection);
   await audit(principal,"publish","products",data.id,{country:data.country,note:data.reviewNote},connection);
   return {id:data.id,status:"published"};
  });
 }
 if(record.action==="update") {
  const data=parse(z.object({action:z.literal('update'),id:string,name:string.optional(),nameEn:string.optional(),slug:productSchema.shape.slug.optional(),category:string.optional(),brand:z.string().max(100).optional(),material:z.string().max(200).optional(),image:productSchema.shape.image.optional(),manufacturer:z.string().max(300).nullable().optional(),description:z.string().max(10000).optional(),descriptionEn:z.string().max(10000).optional(),warnings:z.string().max(5000).optional(),care:z.string().max(5000).optional(),warningsEn:z.string().max(5000).optional(),careEn:z.string().max(5000).optional(),status:z.enum(['draft','review','closed']).optional()}).strict(),input);
  return transaction(async c=>{
   const [existing]=await query('SELECT * FROM products WHERE id=$1 FOR UPDATE',[data.id],c);requireCondition(existing,'PRODUCT_NOT_FOUND','Ürün bulunamadı.',404);
   const map:Record<string,string>={name:'name',nameEn:'name_en',slug:'slug',category:'category',brand:'brand',material:'material',image:'image',manufacturer:'manufacturer',description:'description',descriptionEn:'description_en',warnings:'warnings',care:'care',status:'status'};
   const entries=Object.entries(data).filter(([key])=>key in map);
   const safetyChanged=entries.some(([key,value])=>key!=='status'&&existing[map[key]]!==value)
    ||data.warningsEn!==undefined&&data.warningsEn!==(existing.translations?.en?.warnings??'')
    ||data.careEn!==undefined&&data.careEn!==(existing.translations?.en?.care??'');
   const needsReview=existing.status==='published'&&safetyChanged;
   const nextStatus=data.status??(needsReview?'review':existing.status);
   if(needsReview&&data.status===undefined)entries.push(['status','review']);
   const translation={...existing.translations,en:{...existing.translations?.en,...(data.warningsEn!==undefined?{warnings:data.warningsEn}:{}),...(data.careEn!==undefined?{care:data.careEn}:{})}};
   const values:unknown[]=[data.id,...entries.map(([,value])=>value),JSON.stringify(translation)];
   await query(`UPDATE products SET ${entries.map(([key],i)=>`${map[key]}=$${i+2}`).concat([`translations=$${values.length}`,'updated_at=now()']).join(',')} WHERE id=$1`,values,c);
   if(needsReview)await query('UPDATE product_eligibility SET approved=false WHERE variant_id IN(SELECT id FROM variants WHERE product_id=$1)',[data.id],c);
   if(safetyChanged)await query('UPDATE product_contact_profiles SET reviewed=false,version=version+1,updated_at=now() WHERE product_id=$1',[data.id],c);
   await audit(principal,'update','products',data.id,{fields:Object.keys(data).filter(k=>!['id','action'].includes(k)),reviewRequired:needsReview},c);return {id:data.id,status:nextStatus};
  });
 }
 throw new DomainError("UNKNOWN_ACTION","Ürün işlemi bulunamadı.");
}
async function inventoryAction(input:unknown,principal:Principal,connection?:Connection,releasingReturnId?:string) {
 const data=parse(z.object({action:z.enum(["receipt","adjustment","quarantine","release"]).default("receipt"),variantId:string,quantity:z.number().int().min(-1000000).max(1000000),reason:z.string().trim().min(3).max(500)}).strict(),input);
 const work=async(c:Connection)=>{
  if(data.action!=="adjustment")requireCondition(data.quantity>0,"INVALID_QUANTITY","Adet sıfırdan büyük olmalıdır.");
  await lockPhysicalStockTargets([data.variantId],c);
  const [balance]=await query("SELECT * FROM inventory_balance WHERE variant_id=$1 AND warehouse_id='main' FOR UPDATE",[data.variantId],c);
  requireCondition(balance,"INVENTORY_NOT_FOUND","Depo kaydı bulunamadı.",404);
  await assertUntrackedStock([data.variantId],c);
  const reserved=Number((await query("SELECT coalesce(sum(quantity),0)::int qty FROM reservations WHERE variant_id=$1 AND warehouse_id='main' AND status='active' AND expires_at>now()",[data.variantId],c))[0].qty);
  const delta=data.action==="quarantine"?-data.quantity:data.quantity;
  const quarantineDelta=data.action==="quarantine"?data.quantity:data.action==="release"?-data.quantity:0;
  if(delta<0)requireCondition(balance.on_hand+delta>=reserved+balance.safety_stock,"RESERVED_STOCK","İşlem ayrılmış veya güvenlik stoğunu azaltamaz.",409);
  requireCondition(balance.quarantine+quarantineDelta>=0,"INSUFFICIENT_QUARANTINE","Karantina stoğu yeterli değil.",409);
  if(data.action==="release") {
   const [held]=await query("SELECT coalesce(sum(l.quantity),0)::int qty FROM return_stock_lines l JOIN returns r ON r.id=l.return_id WHERE l.variant_id=$1 AND l.warehouse_id='main' AND r.status IN('received','inspected','refund_pending','refunded','refund_failed') AND r.restocked=false AND($2::text IS NULL OR r.id<>$2)",[data.variantId,releasingReturnId??null],c);
   requireCondition(balance.quarantine-data.quantity>=held.qty,"RETURN_QC_REQUIRED","İade karantinası yalnız başvurunun kalite kontrol adımından satışa dönebilir.",409);
  }
  await query("UPDATE inventory_balance SET on_hand=on_hand+$2,quarantine=quarantine+$3 WHERE variant_id=$1 AND warehouse_id='main'",[data.variantId,delta,quarantineDelta],c);
  await query("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,quarantine_quantity,reason,actor_id) VALUES($1,'main',$2,$3,$4,$5,$6)",[data.variantId,data.action,delta,quarantineDelta,data.reason,principal.id],c);
  await audit(principal,data.action,"inventory",data.variantId,{quantity:data.quantity,reason:data.reason},c);return {variantId:data.variantId,action:data.action,quantity:data.quantity};
 };
 return connection?work(connection):transaction(work);
}
export async function shipmentAction(input:unknown,principal:Principal,connection?:Connection) {
 assertPermission(principal,'shipments','write');
 const data=parse(z.object({orderId:string,carrier:z.string().trim().min(2).max(100),trackingNumber:z.string().trim().min(3).max(100),items:z.array(z.object({variantId:string,quantity:z.number().int().positive().max(999)}).strict()).min(1).optional(),idempotencyKey:z.string().min(16).max(128).optional(),fulfillmentTaskId:string.optional()}).strict(),input);
 requireCondition(!/^(test|fake|demo|ornek|örnek|sahte)$/i.test(data.trackingNumber),"TRACKING_REQUIRED","Taşıyıcının gerçek takip numarasını girin.");
 const work=async(connection:Connection)=>{
  const [order]=await query("SELECT * FROM orders WHERE id=$1 FOR UPDATE",[data.orderId],connection);
  const key=data.idempotencyKey??createHash("sha256").update(`${data.orderId}:${data.carrier}:${data.trackingNumber}`).digest("hex");
  const requestHash=createHash("sha256").update(JSON.stringify({orderId:data.orderId,carrier:data.carrier,trackingNumber:data.trackingNumber,items:data.items??null})).digest("hex");
  const existing=await query("SELECT id,request_hash FROM shipments WHERE idempotency_key=$1",[key],connection);
  if(existing.length){requireCondition(existing[0].request_hash===requestHash,"IDEMPOTENCY_CONFLICT","Aynı sevkiyat anahtarı farklı içerikle kullanılamaz.",409);return {id:existing[0].id,duplicate:true};}
  requireCondition(order&&["confirmed","partially_shipped"].includes(order.status)&&["succeeded","partially_refunded"].includes(order.payment_status),"ORDER_NOT_SHIPPABLE","Sipariş sevke uygun değil.",409);
  await assertOrderLotsShippable(order.id,connection);
  const lines=await query("SELECT i.variant_id,i.quantity,i.snapshot,coalesce(s.qty,0)::int shipped FROM order_items i LEFT JOIN(SELECT si.variant_id,sum(si.quantity) qty FROM shipment_items si JOIN shipments sh ON sh.id=si.shipment_id WHERE sh.order_id=$1 GROUP BY si.variant_id)s ON s.variant_id=i.variant_id WHERE i.order_id=$1",[order.id],connection);
  const items=data.items??lines.filter(l=>l.quantity>l.shipped).map(l=>({variantId:l.variant_id,quantity:l.quantity-l.shipped}));
  requireCondition(items.length&&new Set(items.map(i=>i.variantId)).size===items.length,"INVALID_SHIPMENT","Paket ürünlerini kontrol edin.");
  if(data.fulfillmentTaskId){
   const [task]=await query('SELECT id,status FROM fulfillment_tasks WHERE id=$1 AND order_id=$2 FOR UPDATE',[data.fulfillmentTaskId,order.id],connection);
   requireCondition(task?.status==='packed','PACKAGE_NOT_PACKED','Paketleme doğrulaması tamamlanmalıdır.',409);
   const prepared=await query('SELECT variant_id,quantity,packed_quantity FROM fulfillment_task_items WHERE task_id=$1',[task.id],connection);
   requireCondition(prepared.length===items.length&&prepared.every(p=>p.packed_quantity===p.quantity&&items.some(i=>i.variantId===p.variant_id&&i.quantity===p.quantity)),'PACKAGE_CONTENT_MISMATCH','Sevkiyat doğrulanmış paketle eşleşmelidir.',409);
  }
  for(const item of items){const [assigned]=await query("SELECT coalesce(sum(i.quantity),0)::int n FROM fulfillment_task_items i JOIN fulfillment_tasks t ON t.id=i.task_id WHERE t.order_id=$1 AND i.variant_id=$2 AND t.status IN('picking','packing','packed') AND($3::text IS NULL OR t.id<>$3)",[order.id,item.variantId,data.fulfillmentTaskId??null],connection);const line=lines.find(l=>l.variant_id===item.variantId);requireCondition(line&&line.shipped+item.quantity+assigned.n<=line.quantity,'FULFILLMENT_ASSIGNED','Bu adet başka bir paket hazırlığına ayrılmış. Sipariş ayrıntısından devam edin.',409);}
  for(const item of items){const line=lines.find(l=>l.variant_id===item.variantId);requireCondition(line&&line.shipped+item.quantity<=line.quantity,"SHIPMENT_QUANTITY","Paket adedi kalan sipariş adedini aşamaz.",409);const components=line.snapshot?.bundleComponents;await assertShippingPermissions(components?.length?components.map((c:{variantId:string})=>c.variantId):[item.variantId],order.address.country,data.carrier,connection);}
  const [shipment]=await query("INSERT INTO shipments(order_id,carrier,tracking_number,idempotency_key,request_hash) VALUES($1,$2,$3,$4,$5) RETURNING id",[order.id,data.carrier,data.trackingNumber,key,requestHash],connection);
  for(const item of items)await query("INSERT INTO shipment_items(shipment_id,variant_id,quantity) VALUES($1,$2,$3)",[shipment.id,item.variantId,item.quantity],connection);
  const complete=lines.every(line=>line.shipped+(items.find(i=>i.variantId===line.variant_id)?.quantity??0)===line.quantity);
  const next=complete?"shipped":"partially_shipped";
  await query("UPDATE orders SET status=$2,fulfillment_status=$2,updated_at=now() WHERE id=$1",[order.id,next],connection);
  await query("INSERT INTO order_history(order_id,type,from_status,to_status,actor_id) VALUES($1,'shipment',$2,$3,$4)",[order.id,order.status,next,principal.id],connection);
  if(data.fulfillmentTaskId)await query("UPDATE fulfillment_tasks SET status='shipped',shipment_id=$2,updated_at=now() WHERE id=$1",[data.fulfillmentTaskId,shipment.id],connection);
  await audit(principal,"ship","shipments",shipment.id,{orderId:order.id},connection);return {id:shipment.id,status:next};
 };
 return connection?work(connection):transaction(work);
}
export async function requestReturn(orderId:string,trackingToken:string|null,input:unknown,userId?:string) {
 const order=await getOrder(orderId,trackingToken,userId);requireCondition(order,"ORDER_NOT_FOUND","Sipariş bulunamadı.",404);
 requireCondition(["succeeded","partially_refunded"].includes(order.paymentStatus),"RETURN_NOT_ALLOWED","Bu sipariş için iade başvurusu alınamıyor.",409);
 return returnAction({...input as Record<string,unknown>,action:"request",orderId},{id:userId??"guest",role:"support",mfa:true},true);
}
async function returnAction(input:unknown,principal:Principal,customerRequest=false) {
 const record=input as Record<string,unknown>;
 if(record.action==="request") {
  const data=parse(z.object({action:z.literal("request"),orderId:string,variantId:string,quantity:z.number().int().positive().max(999),reason:z.string().trim().min(5).max(2000),sealIntact:z.boolean()}).strict(),input);
  return transaction(async connection=>{
   const [order]=await query("SELECT * FROM orders WHERE id=$1 FOR UPDATE",[data.orderId],connection);
   requireCondition(order&&["succeeded","partially_refunded"].includes(order.payment_status),"RETURN_NOT_ALLOWED","Sipariş iadeye uygun değil.",409);
   const [line]=await query("SELECT * FROM order_items WHERE order_id=$1 AND variant_id=$2",[data.orderId,data.variantId],connection);
   const [existing]=await query("SELECT coalesce(sum(quantity),0)::int qty FROM returns WHERE order_id=$1 AND variant_id=$2 AND status<>'rejected'",[data.orderId,data.variantId],connection);
   requireCondition(line&&existing.qty+data.quantity<=line.quantity,"RETURN_QUANTITY","İade adedi sipariş adedini aşamaz.",409);
   const [result]=await query("INSERT INTO returns(order_id,variant_id,quantity,reason,seal_intact) VALUES($1,$2,$3,$4,$5) RETURNING id",[data.orderId,data.variantId,data.quantity,data.reason,data.sealIntact],connection);
   await audit(principal,customerRequest?"customer_request":"request","returns",result.id,{orderId:data.orderId},connection);return {id:result.id,status:"requested"};
  });
 }
 const data=parse(z.object({action:z.enum(["review","receive","inspect","refund"]),id:string,approved:z.boolean().optional(),restock:z.boolean().optional(),reason:z.string().max(2000).optional()}).strict(),input);
 return transaction(async connection=>{
  const [r]=await query("SELECT * FROM returns WHERE id=$1 FOR UPDATE",[data.id],connection);requireCondition(r,"RETURN_NOT_FOUND","İade başvurusu bulunamadı.",404);
  if(data.action==="review") {
   requireCondition(["admin","support"].includes(principal.role),"FORBIDDEN","İade incelemesi için yetkiniz yok.",403);
   requireCondition(r.status==="requested"||r.status==="reviewing","INVALID_RETURN_STATE","İade zaten incelendi.",409);
   requireCondition(typeof data.approved==="boolean"&&(data.reason?.trim().length??0)>=5,"DECISION_REQUIRED","Kararı ve gerekçesini girin.");
   const status=data.approved?"approved":"rejected";
   await query("UPDATE returns SET status=$2,decision_reason=$3,updated_at=now() WHERE id=$1",[r.id,status,data.reason],connection);await audit(principal,status,"returns",r.id,{},connection);return {id:r.id,status};
  }
  if(data.action==="receive") {
   requireCondition(["admin","warehouse"].includes(principal.role),"FORBIDDEN","İade kabulü için yetkiniz yok.",403);
   requireCondition(r.status==="approved","INVALID_RETURN_STATE","Yalnız onaylı iade teslim alınabilir.",409);
   await receiveReturnStock({id:r.id,order_id:r.order_id,variant_id:r.variant_id,quantity:r.quantity},principal.id,connection);
   await query("UPDATE returns SET status='received',updated_at=now() WHERE id=$1",[r.id],connection);await audit(principal,"receive","returns",r.id,{},connection);return {id:r.id,status:"received"};
  }
  if(data.action==="inspect") {
   requireCondition(["admin","warehouse"].includes(principal.role),"FORBIDDEN","Kalite kontrol için yetkiniz yok.",403);
   requireCondition(r.status==="received","INVALID_RETURN_STATE","İade teslim alınmadan kontrol edilemez.",409);
   requireCondition(typeof data.restock==="boolean"&&(data.reason?.trim().length??0)>=5,"QC_REQUIRED","Kalite kontrol kararını ve gerekçesini girin.");
   if(data.restock) {
    requireCondition(r.seal_intact,"HYGIENE_SEAL_OPEN","Mührü açılmış ürün otomatik olarak satışa dönemez.",409);
    const lines=await getLockedReturnStockLines(r.id,connection);
    for(const line of lines)await inventoryAction({action:"release",variantId:line.variantId,quantity:line.quantity,reason:data.reason},principal,connection,r.id);
   }
   await query("UPDATE returns SET status='inspected',qc_reason=$2,restocked=$3,updated_at=now() WHERE id=$1",[r.id,data.reason,data.restock],connection);await audit(principal,"inspect","returns",r.id,{restocked:data.restock},connection);return {id:r.id,status:"inspected"};
  }
  requireCondition(["admin","finance"].includes(principal.role),"FORBIDDEN","Para iadesi için yetkiniz yok.",403);
  if(r.status==='refund_pending'){const [existing]=await query("SELECT id,amount_minor FROM refunds WHERE return_id=$1 AND status='pending'",[r.id],connection);requireCondition(existing,'REFUND_NOT_FOUND','Bekleyen iade kaydı bulunamadı.',409);return {id:r.id,refundId:existing.id,status:'refund_pending',amountMinor:Number(existing.amount_minor),duplicate:true};}
  requireCondition(r.status==="inspected","INVALID_RETURN_STATE","Kalite kontrolü tamamlanmadan para iadesi yapılamaz.",409);
  const [payment]=await query("SELECT * FROM payments WHERE order_id=$1 FOR UPDATE",[r.order_id],connection);
  requireCondition(payment&&["succeeded","partially_refunded"].includes(payment.status),"PAYMENT_NOT_REFUNDABLE","Ödeme iadeye uygun değil.",409);
  const [line]=await query("SELECT * FROM order_items WHERE order_id=$1 AND variant_id=$2",[r.order_id,r.variant_id],connection);
  const [refunded]=await query("SELECT coalesce(sum(rf.amount_minor),0) amount,coalesce(sum(rf.tax_minor),0) tax,coalesce(sum(rf.discount_minor),0) discount,coalesce(sum(rt.quantity),0)::int qty FROM refunds rf JOIN returns rt ON rt.id=rf.return_id WHERE rt.order_id=$1 AND rt.variant_id=$2 AND rf.status IN('succeeded','pending')",[r.order_id,r.variant_id],connection);
  const lineTotal=Number(line.unit_minor)*line.quantity-Number(line.discount_minor);
  const amount=refunded.qty+r.quantity===line.quantity?lineTotal-Number(refunded.amount):Math.floor(lineTotal*r.quantity/line.quantity);
  const finalLine=refunded.qty+r.quantity===line.quantity;
  const taxMinor=finalLine?Number(line.tax_minor)-Number(refunded.tax):Number(BigInt(line.tax_minor)*BigInt(r.quantity)/BigInt(line.quantity));
  const discountMinor=finalLine?Number(line.discount_minor)-Number(refunded.discount):Number(BigInt(line.discount_minor)*BigInt(r.quantity)/BigInt(line.quantity));
  const [pending]=await query("SELECT coalesce(sum(amount_minor),0) amount FROM refunds WHERE payment_id=$1 AND status='pending'",[payment.id],connection);
  requireCondition(amount>0&&Number(payment.refunded_minor)+Number(pending.amount)+amount<=Number(payment.amount_minor),"REFUND_AMOUNT","İade tutarı tahsilatı aşamaz.",409);
  if(payment.provider==='stripe') {
   requireCondition(payment.provider_reference,'PAYMENT_REFERENCE_REQUIRED','Sağlayıcının tahsilat referansı doğrulanamadı.',409);
   const [refund]=await query("INSERT INTO refunds(return_id,payment_id,amount_minor,status,tax_minor,discount_minor,restocked_cost_minor) VALUES($1,$2,$3,'pending',$4,$5,$6) RETURNING id",[r.id,payment.id,amount,taxMinor,discountMinor,r.restocked?Number(line.cost_minor)*r.quantity:0],connection);
   await query("UPDATE returns SET status='refund_pending',refund_minor=$2,updated_at=now() WHERE id=$1",[r.id,amount],connection);
   await query("INSERT INTO jobs(type,payload,dedupe_key) VALUES('refund.stripe',$1,$2) ON CONFLICT(dedupe_key) DO NOTHING",[JSON.stringify({refundId:refund.id,orderId:r.order_id}),`refund:${refund.id}`],connection);
   await audit(principal,'refund_requested','returns',r.id,{amountMinor:amount,refundId:refund.id},connection);return {id:r.id,refundId:refund.id,status:'refund_pending',amountMinor:amount};
  }
  // Unsupported providers remain blocked; an adapter capability is never assumed.
  if(payment.provider!=="test")throw new DomainError("REFUND_PROVIDER_REQUIRED","Gerçek sağlayıcı iadesi için finans entegrasyonu gerekir.",503);
  assertTestEnvironment();
  const [refund]=await query("INSERT INTO refunds(return_id,payment_id,amount_minor,status,provider_reference,tax_minor,discount_minor,restocked_cost_minor) VALUES($1,$2,$3,'succeeded',$4,$5,$6,$7) RETURNING id",[r.id,payment.id,amount,`local-refund:${r.id}`,taxMinor,discountMinor,r.restocked?Number(line.cost_minor)*r.quantity:0],connection);
  const full=Number(payment.refunded_minor)+amount===Number(payment.amount_minor),status=full?"refunded":"partially_refunded";
  await query("UPDATE payments SET refunded_minor=refunded_minor+$2,status=$3,updated_at=now() WHERE id=$1",[payment.id,amount,status],connection);
  await query("UPDATE orders SET payment_status=$2,updated_at=now() WHERE id=$1",[r.order_id,status],connection);
  await query("UPDATE returns SET status='refunded',refund_minor=$2,updated_at=now() WHERE id=$1",[r.id,amount],connection);
  await audit(principal,"refund","returns",r.id,{amountMinor:amount,refundId:refund.id},connection);return {id:r.id,status:"refunded",amountMinor:amount};
 });
}
export async function adminAction(resource:string,input:unknown,principal:Principal):Promise<unknown> {
 assertPermission(principal,resource,"write");
 if(resource==='lots')return manageLot(input,principal);
 if(operationsResources.has(resource))return performOperation(resource,input,principal);
 if(resource==="products")return productAction(input,principal);
 if(resource==="inventory")return inventoryAction(input,principal);
 if(resource==="shipments")return shipmentAction(input,principal);
 if(resource==="returns")return returnAction(input,principal);
 if(resource==="content") {
  const data=parse(z.object({slug:z.string().regex(/^[a-z0-9-]+$/).max(100),locale:z.enum(["tr","en","de","ru","ar"]),title:string,body:z.string().min(1).max(50000),status:z.enum(["draft","published"])}).strict(),input);
  requireCondition(data.status!=="published"||["tr","en"].includes(data.locale),"TRANSLATION_NOT_READY","Bu dil yayın için hazır değil.",409);
  return transaction(async connection=>{
   const [row]=await query("INSERT INTO content_pages(slug,locale,title,body,status) VALUES($1,$2,$3,$4,$5) ON CONFLICT(slug,locale) DO UPDATE SET title=excluded.title,body=excluded.body,status=excluded.status,version=content_pages.version+1,updated_at=now() RETURNING id,version",[data.slug,data.locale,data.title,data.body,data.status],connection);
   await query("INSERT INTO content_revisions(page_id,version,title,body,actor_id) VALUES($1,$2,$3,$4,$5)",[row.id,row.version,data.title,data.body,principal.id],connection);await audit(principal,"save","content",row.id,{version:row.version},connection);return row;
  });
 }
 if(resource==="settings") {
  const data=parse(z.object({key:string,value:z.union([z.string().max(2000),z.boolean()]),note:z.string().max(1000).optional()}).strict(),input);
  requireCondition(["seller.name","seller.taxNumber","seller.address","seller.supportEmail","seller.phone","seller.bankAccount","launch.backupVerified","launch.securityReviewed","launch.legalApproved","launch.catalogVerified","launch.providerApproved"].includes(data.key),"SETTING_NOT_ALLOWED","Bu ayar değiştirilemez.");
  if(data.key.startsWith("launch."))requireCondition(typeof data.value==="boolean"&&(!data.value||(data.note?.trim().length??0)>=10),"EVIDENCE_REQUIRED","Onay için kanıt referansı açıklaması gerekir.");
  else requireCondition(typeof data.value==="string","INVALID_SETTING","Satıcı alanı metin olmalıdır.");
  await query("INSERT INTO settings(key,value) VALUES($1,$2) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=now()",[data.key,JSON.stringify(data.value)]);await audit(principal,"update","settings",data.key,{note:data.note??"",approved:data.value===true});return {key:data.key};
 }
 if(resource==="countries") {
  const data=parse(z.object({code:z.string().regex(/^[A-Z]{2}$/),enabled:z.boolean(),productApproved:z.boolean(),ageApproved:z.boolean(),paymentApproved:z.boolean(),shippingApproved:z.boolean(),taxApproved:z.boolean(),legalApproved:z.boolean(),shippingMinor:z.number().int().nonnegative(),currency:z.enum(["TRY","EUR","USD","GBP"]),note:z.string().min(10).max(1000)}).strict(),input);
  requireCondition(!data.enabled||[data.productApproved,data.ageApproved,data.paymentApproved,data.shippingApproved,data.taxApproved,data.legalApproved].every(Boolean),"COUNTRY_GATES_REQUIRED","Tüm ülke uygunluk onayları tamamlanmalıdır.",409);
  await query("UPDATE country_rules SET enabled=$2,product_approved=$3,age_approved=$4,payment_approved=$5,shipping_approved=$6,tax_approved=$7,legal_approved=$8,shipping_minor=$9,currency=$10 WHERE code=$1",[data.code,data.enabled,data.productApproved,data.ageApproved,data.paymentApproved,data.shippingApproved,data.taxApproved,data.legalApproved,data.shippingMinor,data.currency]);await audit(principal,"update","countries",data.code,{note:data.note});return {code:data.code};
 }
 if(resource==="suppliers") {
  const data=parse(z.object({name:string,leadDays:z.number().int().min(0).max(1000).default(0),contactEmail:z.email().optional()}).strict(),input);
  const [row]=await query("INSERT INTO suppliers(name,lead_days,contact_email) VALUES($1,$2,$3) RETURNING id",[data.name,data.leadDays,data.contactEmail??null]);await audit(principal,"create","suppliers",row.id);return row;
 }
 if(resource==="jobs") {
  const data=parse(z.object({action:z.literal("retry"),id:string}).strict(),input);
  const rows=await query("UPDATE jobs SET status='pending',attempts=0,available_at=now(),lease_until=null,last_error=null WHERE id=$1 AND status='failed' RETURNING id",[data.id]);requireCondition(rows.length,"JOB_NOT_RETRYABLE","İş yeniden çalıştırmaya uygun değil.",409);await audit(principal,"retry","jobs",data.id);return {id:data.id};
 }
 if(resource==="legal")return legalAction(input,principal);
 if(resource==="orders") {
  const data=parse(z.object({action:z.literal("cancel"),id:string,reason:z.string().min(5).max(500)}).strict(),input);
  return transaction(async connection=>{
   const [order]=await query("SELECT * FROM orders WHERE id=$1 FOR UPDATE",[data.id],connection);requireCondition(order&&order.status==="awaiting_payment","CANCEL_NOT_ALLOWED","Yalnız ödenmemiş sipariş iptal edilebilir; ödenen sipariş için iade sürecini kullanın.",409);
   await query("UPDATE reservations SET status='released' WHERE order_id=$1 AND status='active'",[data.id],connection);
   await query("UPDATE orders SET status='cancelled',updated_at=now() WHERE id=$1",[data.id],connection);await audit(principal,"cancel","orders",data.id,{reason:data.reason},connection);return {id:data.id,status:"cancelled"};
  });
 }
 throw new DomainError("ACTION_NOT_SUPPORTED","Bu bölüm için işlem henüz desteklenmiyor.",501);
}
async function legalAction(input:unknown,principal:Principal) {
 const record=input as Record<string,unknown>;
 if(!record.action||record.action==="create") {
  const data=parse(z.object({action:z.literal("create").optional(),kind:z.enum(["privacy","privacy_policy","cookies","usage","membership","pre_information","terms","shipping","returns","consent","data_request","explicit_consent","defective"]),locale:z.enum(["tr","en"]),title:string,body:z.string().min(20).max(100000),version:z.number().int().positive()}).strict(),input);
  const hash=createHash("sha256").update(data.body).digest("hex");
  const [row]=await query("INSERT INTO legal_documents(kind,locale,title,body,version,body_hash) VALUES($1,$2,$3,$4,$5,$6) RETURNING id",[data.kind,data.locale,data.title,data.body,data.version,hash]);await audit(principal,"draft","legal",row.id,{hash});return {id:row.id,status:"draft"};
 }
 const data=parse(z.object({action:z.enum(["approve","activate","archive"]),id:string,note:z.string().min(10).max(2000)}).strict(),input);
 return transaction(async connection=>{
  const [doc]=await query("SELECT * FROM legal_documents WHERE id=$1 FOR UPDATE",[data.id],connection);requireCondition(doc,"LEGAL_NOT_FOUND","Hukuk metni bulunamadı.",404);
  const next=data.action==="approve"?"approved":data.action==="activate"?"effective":"archived";
  requireCondition(data.action==="archive"||data.action==="approve"&&doc.status==="draft"||data.action==="activate"&&doc.status==="approved","INVALID_LEGAL_TRANSITION","Hukuk metninin durum geçişi uygun değil.",409);
  if(data.action!=='archive') {
   requireCondition(!/{{|}}/.test(doc.body),'LEGAL_PLACEHOLDER','Doldurulmamış hukuk metni onaylanamaz.',409);
   requireCondition(createHash('sha256').update(doc.body).digest('hex')===doc.body_hash,'LEGAL_HASH_MISMATCH','Hukuk metni içeriği sürüm kaydıyla eşleşmiyor.',409);
  }
  if(data.action==='activate') {
   requireCondition(!doc.fixture||['development','test'].includes(process.env.APP_ENV??''),'FIXTURE_NOT_ALLOWED','Örnek hukuk metni canlıya açılamaz.',503);
   if(!doc.fixture){const seller=await query('SELECT key,value FROM settings WHERE key=ANY($1::text[])',[['seller.name','seller.taxNumber','seller.address','seller.supportEmail','seller.phone']],connection);requireCondition(seller.length===5&&seller.every(s=>typeof s.value==='string'&&s.value.trim()&&!/{{|}}/.test(s.value)),'SELLER_NOT_CONFIGURED','Hukuk metni yürürlüğe girmeden gerçek satıcı bilgilerini tamamlayın.',409);}
   if(!doc.fixture&&['privacy','privacy_policy','data_request'].includes(doc.kind)){
    const controller=await query("SELECT id FROM privacy_controllers WHERE status='approved' AND fixture=false",[],connection);
    requireCondition(controller.length===1,'CONTROLLER_NOT_CONFIGURED','Bu hukuk metni yürürlüğe girmeden veri sorumlusu kimliğini belgeyle doğrulayın.',409);
   }
  }
  if(data.action==="activate")await query("UPDATE legal_documents SET status='archived' WHERE kind=$1 AND locale=$2 AND status='effective'",[doc.kind,doc.locale],connection);
  await query("UPDATE legal_documents SET status=$2,approved_by=CASE WHEN $2='approved' THEN $3 ELSE approved_by END,approved_at=CASE WHEN $2='approved' THEN now() ELSE approved_at END,effective_at=CASE WHEN $2='effective' THEN now() ELSE effective_at END WHERE id=$1",[doc.id,next,principal.id],connection);
  await query("INSERT INTO legal_approval_log(document_id,actor_id,from_status,to_status,note) VALUES($1,$2,$3,$4,$5)",[doc.id,principal.id,doc.status,next,data.note],connection);await audit(principal,next,"legal",doc.id,{note:data.note},connection);return {id:doc.id,status:next};
 });
}
