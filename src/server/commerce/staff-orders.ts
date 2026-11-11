/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/staff-orders.ts
 * Açıklama   : Rol sınırlı sipariş ayrıntısı ve işlemsel toplama/paketleme komutları.
 */
import {createHash} from 'node:crypto';
import {z} from 'zod';
import {query,transaction} from '../db';
import type {Currency,Principal} from '../../shared/contracts';
import {assertPermission,requireCondition} from './rules';
import {audit,shipmentAction} from './admin';

export interface StaffOrderItem {variantId:string;name:string;sku:string;barcode:string|null;quantity:number;shippedQuantity:number;remainingQuantity:number;assignedQuantity:number;unitMinor?:number;costMinor?:number;}
export interface StaffTask {id:string;status:string;shipmentId:string|null;createdAt:string;items:{variantId:string;quantity:number;pickedQuantity:number;packedQuantity:number}[];}
export interface StaffOrderDetail {
 id:string;number:string;status:string;paymentStatus:string;fulfillmentStatus:string;createdAt:string;
 items:StaffOrderItem[];tasks:StaffTask[];
 shipments:{id:string;carrier:string;trackingNumber:string;status:string;items:{variantId:string;quantity:number}[]}[];
 address?:{fullName:string;phone:string;line1:string;city:string;postalCode:string;region?:string;district?:string;country:string};
 contact?:{email:string};
 totals?:{currency:Currency;subtotalMinor:number;discountMinor:number;shippingMinor:number;taxMinor:number;totalMinor:number};
 payment?:{provider:string;status:string;amountMinor:number;refundedMinor:number;currency:Currency;reference:string|null};
 history?:{type:string;status:string|null;createdAt:string}[];
 canFulfill:boolean;
}
const paid=(row:{status:string;payment_status:string})=>['confirmed','partially_shipped'].includes(row.status)&&['succeeded','partially_refunded'].includes(row.payment_status);
export async function staffOrderDetail(orderId:string,principal:Principal):Promise<StaffOrderDetail>{
 assertPermission(principal,'orders','read');
 const financial=['admin','finance'].includes(principal.role),shipping=['admin','warehouse','support'].includes(principal.role);
 const [o]=await query(`SELECT id,number,status,payment_status,fulfillment_status,created_at${shipping?',address':''}${principal.role==='admin'||principal.role==='support'?',email':''}${financial?',currency,subtotal_minor,discount_minor,shipping_minor,tax_minor,total_minor':''} FROM orders WHERE id=$1`,[orderId]);
 requireCondition(o&&(principal.role!=='warehouse'||['succeeded','partially_refunded'].includes(o.payment_status)),'ORDER_NOT_FOUND','Sipariş bulunamadı veya bu işlem için uygun değil.',404);
 const lines=await query(`SELECT i.variant_id,i.name,i.sku,v.barcode,i.quantity${principal.role!=='warehouse'?',i.unit_minor':''}${financial?',i.cost_minor':''},
 coalesce((SELECT sum(si.quantity) FROM shipment_items si JOIN shipments s ON s.id=si.shipment_id WHERE s.order_id=i.order_id AND si.variant_id=i.variant_id),0)::int shipped,
 coalesce((SELECT sum(fi.quantity) FROM fulfillment_task_items fi JOIN fulfillment_tasks ft ON ft.id=fi.task_id WHERE ft.order_id=i.order_id AND fi.variant_id=i.variant_id AND ft.status IN('picking','packing','packed')),0)::int assigned
 FROM order_items i JOIN variants v ON v.id=i.variant_id WHERE i.order_id=$1 ORDER BY i.id`,[orderId]);
 const tasks=await query("SELECT t.id,t.status,t.shipment_id,t.created_at,coalesce(jsonb_agg(jsonb_build_object('variantId',i.variant_id,'quantity',i.quantity,'pickedQuantity',i.picked_quantity,'packedQuantity',i.packed_quantity) ORDER BY i.variant_id),'[]'::jsonb) items FROM fulfillment_tasks t JOIN fulfillment_task_items i ON i.task_id=t.id WHERE t.order_id=$1 GROUP BY t.id ORDER BY t.created_at DESC",[orderId]);
 const shipments=await query("SELECT s.id,s.carrier,s.tracking_number,s.status,jsonb_agg(jsonb_build_object('variantId',i.variant_id,'quantity',i.quantity) ORDER BY i.variant_id) items FROM shipments s JOIN shipment_items i ON i.shipment_id=s.id WHERE s.order_id=$1 GROUP BY s.id ORDER BY s.created_at",[orderId]);
 const result:StaffOrderDetail={id:o.id,number:o.number,status:o.status,paymentStatus:o.payment_status,fulfillmentStatus:o.fulfillment_status,createdAt:o.created_at.toISOString(),
  items:lines.map(i=>({variantId:i.variant_id,name:i.name,sku:i.sku,barcode:i.barcode,quantity:i.quantity,shippedQuantity:i.shipped,remainingQuantity:Math.max(0,i.quantity-i.shipped),assignedQuantity:i.assigned,...(principal.role!=='warehouse'?{unitMinor:Number(i.unit_minor)}:{}),...(financial?{costMinor:Number(i.cost_minor)}:{})})),
  tasks:tasks.map(t=>({id:t.id,status:t.status,shipmentId:t.shipment_id,createdAt:t.created_at.toISOString(),items:t.items})),
  shipments:shipments.map(s=>({id:s.id,carrier:s.carrier,trackingNumber:s.tracking_number,status:s.status,items:s.items})),canFulfill:['admin','warehouse'].includes(principal.role)&&paid({status:o.status,payment_status:o.payment_status})};
 if(shipping&&['succeeded','partially_refunded'].includes(o.payment_status)){const a=o.address;result.address={fullName:String(a.fullName??''),phone:String(a.phone??''),line1:String(a.line1??''),city:String(a.city??''),postalCode:String(a.postalCode??''),region:String(a.region??''),district:String(a.district??''),country:String(a.country??'')};}
 if(principal.role==='admin'||principal.role==='support')result.contact={email:o.email};
 if(financial){result.totals={currency:o.currency,subtotalMinor:Number(o.subtotal_minor),discountMinor:Number(o.discount_minor),shippingMinor:Number(o.shipping_minor),taxMinor:Number(o.tax_minor),totalMinor:Number(o.total_minor)};const [p]=await query('SELECT provider,status,amount_minor,refunded_minor,currency,provider_reference FROM payments WHERE order_id=$1',[orderId]);if(p)result.payment={provider:p.provider,status:p.status,amountMinor:Number(p.amount_minor),refundedMinor:Number(p.refunded_minor),currency:p.currency,reference:p.provider_reference};}
 if(principal.role!=='warehouse'){const history=await query('SELECT type,to_status,created_at FROM order_history WHERE order_id=$1 ORDER BY created_at DESC LIMIT 50',[orderId]);result.history=history.map(h=>({type:h.type,status:h.to_status,createdAt:h.created_at.toISOString()}));}
 return result;
}

const id=z.string().trim().min(1).max(100),requestKey=z.string().min(16).max(128),quantity=z.number().int().positive().max(999);
const command=z.discriminatedUnion('action',[
 z.object({action:z.literal('create'),items:z.array(z.object({variantId:id,quantity}).strict()).min(1).max(100),requestKey}).strict(),
 z.object({action:z.enum(['pick','pack']),taskId:id,code:z.string().trim().min(1).max(100),quantity,requestKey}).strict(),
 z.object({action:z.literal('ship'),taskId:id,carrier:z.string().trim().min(2).max(100),trackingNumber:z.string().trim().min(3).max(100),requestKey}).strict(),
 z.object({action:z.literal('cancel'),taskId:id,requestKey}).strict(),
]);
export async function staffFulfillmentAction(orderId:string,input:unknown,principal:Principal):Promise<{id:string;status:string;duplicate?:boolean;shipmentId?:string|null}>{
 assertPermission(principal,'shipments','write');
 const parsed=command.safeParse(input);requireCondition(parsed.success,'INVALID_INPUT','Toplama ve paketleme alanlarını kontrol edin.');const d=parsed.data;
 if(d.action==='create'){d.items.sort((a,b)=>a.variantId.localeCompare(b.variantId));requireCondition(new Set(d.items.map(i=>i.variantId)).size===d.items.length,'DUPLICATE_ITEM','Aynı ürün bir kez seçilebilir.');}
 const hash=createHash('sha256').update(JSON.stringify({actor:principal.id,...d})).digest('hex');
 return transaction(async c=>{
  const [o]=await query('SELECT id,status,payment_status FROM orders WHERE id=$1 FOR UPDATE',[orderId],c);requireCondition(o,'ORDER_NOT_FOUND','Sipariş bulunamadı.',404);
  const [previous]=await query('SELECT request_hash,task_id FROM fulfillment_commands WHERE order_id=$1 AND request_key=$2',[orderId,d.requestKey],c);
  if(previous){requireCondition(previous.request_hash===hash,'IDEMPOTENCY_CONFLICT','İşlem anahtarı farklı bir komut için kullanılmış.',409);const [t]=await query('SELECT status,shipment_id FROM fulfillment_tasks WHERE id=$1',[previous.task_id],c);return {id:previous.task_id,status:t.status,shipmentId:t.shipment_id,duplicate:true};}
  requireCondition(d.action==='cancel'||paid({status:o.status,payment_status:o.payment_status}),'ORDER_NOT_SHIPPABLE','Yalnız ödemesi doğrulanmış ve sevke uygun sipariş işlenebilir.',409);
  let taskId:string,status:string,shipmentId:string|null=null;
  if(d.action==='create'){
   for(const item of d.items){const [line]=await query("SELECT i.quantity,coalesce((SELECT sum(si.quantity) FROM shipment_items si JOIN shipments s ON s.id=si.shipment_id WHERE s.order_id=i.order_id AND si.variant_id=i.variant_id),0)::int shipped,coalesce((SELECT sum(fi.quantity) FROM fulfillment_task_items fi JOIN fulfillment_tasks t ON t.id=fi.task_id WHERE t.order_id=i.order_id AND fi.variant_id=i.variant_id AND t.status IN('picking','packing','packed')),0)::int assigned FROM order_items i WHERE i.order_id=$1 AND i.variant_id=$2",[orderId,item.variantId],c);requireCondition(line&&item.quantity<=line.quantity-line.shipped-line.assigned,'FULFILLMENT_QUANTITY','Adet, başka pakete ayrılmamış sipariş miktarını aşamaz.',409);}
   const [t]=await query('INSERT INTO fulfillment_tasks(order_id,created_by) VALUES($1,$2) RETURNING id',[orderId,principal.id],c);taskId=t.id;status='picking';
   for(const item of d.items)await query('INSERT INTO fulfillment_task_items(task_id,variant_id,quantity) VALUES($1,$2,$3)',[taskId,item.variantId,item.quantity],c);
  }else{
   const [t]=await query('SELECT id,status,shipment_id FROM fulfillment_tasks WHERE id=$1 AND order_id=$2 FOR UPDATE',[d.taskId,orderId],c);requireCondition(t,'TASK_NOT_FOUND','Paket hazırlığı bulunamadı.',404);taskId=t.id;status=t.status;
   if(d.action==='cancel'){requireCondition(!['shipped','cancelled'].includes(t.status),'TASK_CANNOT_CANCEL','Sevk edilmiş veya iptal edilmiş paket değiştirilemez.',409);status='cancelled';await query("UPDATE fulfillment_tasks SET status='cancelled',updated_at=now() WHERE id=$1",[taskId],c);}
   else if(d.action==='ship'){
    requireCondition(t.status==='packed','PACKAGE_NOT_PACKED','Bütün ürünleri doğrulayarak paketlemeyi tamamlayın.',409);
    const items=await query('SELECT variant_id,quantity FROM fulfillment_task_items WHERE task_id=$1 ORDER BY variant_id',[taskId],c);
    const result=await shipmentAction({orderId,carrier:d.carrier,trackingNumber:d.trackingNumber,items:items.map(i=>({variantId:i.variant_id,quantity:i.quantity})),idempotencyKey:`fulfillment:${taskId}`,fulfillmentTaskId:taskId},principal,c);shipmentId=result.id;status='shipped';
   }else{
    requireCondition(t.status===(d.action==='pick'?'picking':'packing'),'INVALID_TASK_STATE',d.action==='pick'?'Paket toplama adımında değil.':'Önce bütün ürünlerin toplamasını doğrulayın.',409);
    const matches=await query('SELECT fi.variant_id,fi.quantity,fi.picked_quantity,fi.packed_quantity FROM fulfillment_task_items fi JOIN order_items oi ON oi.order_id=$1 AND oi.variant_id=fi.variant_id JOIN variants v ON v.id=fi.variant_id WHERE fi.task_id=$2 AND(oi.sku=$3 OR(v.barcode IS NOT NULL AND v.barcode=$3))',[orderId,taskId,d.code],c);
    requireCondition(matches.length===1,'SCAN_MISMATCH','Okutulan barkod veya stok kodu bu pakette tek bir ürünle eşleşmeli.',409);const line=matches[0];
    const column=d.action==='pick'?'picked_quantity':'packed_quantity',maximum=d.action==='pick'?line.quantity:line.picked_quantity;
    requireCondition(line[column]+d.quantity<=maximum,'SCAN_QUANTITY','Doğrulanan adet paket miktarını aşamaz.',409);
    await query(`UPDATE fulfillment_task_items SET ${column}=${column}+$3 WHERE task_id=$1 AND variant_id=$2`,[taskId,line.variant_id,d.quantity],c);
    const [remaining]=await query(`SELECT count(*)::int n FROM fulfillment_task_items WHERE task_id=$1 AND ${column}<quantity`,[taskId],c);
    if(remaining.n===0){status=d.action==='pick'?'packing':'packed';await query('UPDATE fulfillment_tasks SET status=$2,updated_at=now() WHERE id=$1',[taskId,status],c);}
   }
  }
  await query('INSERT INTO fulfillment_commands(order_id,request_key,request_hash,task_id,action,actor_id) VALUES($1,$2,$3,$4,$5,$6)',[orderId,d.requestKey,hash,taskId,d.action,principal.id],c);
  await audit(principal,d.action,'fulfillment',taskId,{orderId,status,...('quantity'in d?{quantity:d.quantity}:{})},c);
  return {id:taskId,status,shipmentId};
 });
}
