/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/lots.ts
 * Açıklama   : Lot mal kabulü, FEFO tahsisi, karantina ve geri çağırma tutarlılığı.
 */
import {createHash} from 'node:crypto';
import {z} from 'zod';
import {query,transaction,type Connection} from '../db';
import type {Principal} from '../../shared/contracts';
import {assertPermission,requireCondition} from './rules';
import {lockPhysicalStockTargets} from './bundles';
import type {PurchaseReceiptLotInput,PurchaseLotSources} from '../../shared/purchase-receipts';

// A date denotes the start of the unsafe day in the Turkish warehouse timezone.
const validLot="l.quarantined=false AND l.recall_reference IS NULL AND(l.expires_at IS NULL OR l.expires_at>(now() AT TIME ZONE 'Europe/Istanbul')::date)";
const activeReservation="r.status='active' AND r.expires_at>now()";
const text=z.string().trim().min(1).max(300),reason=z.string().trim().min(5).max(1000),key=z.string().min(16).max(128);
const schema=z.discriminatedUnion('action',[
 z.object({action:z.literal('enable'),variantId:text,expiryRequired:z.boolean(),reason,idempotencyKey:key}).strict(),
 z.object({action:z.literal('receipt'),variantId:text,lotNumber:text,expiresAt:z.iso.date().nullable().optional(),quantity:z.number().int().positive().max(1000000),sourceReference:reason,quarantined:z.boolean().default(false),reason,idempotencyKey:key}).strict(),
 z.object({action:z.enum(['quarantine','release']),lotId:text,reason,idempotencyKey:key}).strict(),
 z.object({action:z.literal('recall'),lotId:text,reference:reason,reason,idempotencyKey:key}).strict()
]);
const camel=(row:Record<string,unknown>)=>Object.fromEntries(Object.entries(row).map(([k,v])=>[k.replace(/_([a-z])/g,(_,c:string)=>c.toUpperCase()),v instanceof Date?v.toISOString():v]));

export async function trackedAvailable(variantId:string,warehouseId:string,connection?:Connection):Promise<number|null>{
 const [variant]=await query('SELECT lot_tracking FROM variants WHERE id=$1',[variantId],connection);if(!variant?.lot_tracking)return null;
 const [balance]=await query('SELECT on_hand,safety_stock FROM inventory_balance WHERE variant_id=$1 AND warehouse_id=$2',[variantId,warehouseId],connection);if(!balance)return 0;
 const [stock]=await query(`SELECT coalesce(sum(greatest(0,b.on_hand-coalesce(a.qty,0))),0)::int n FROM inventory_lot_balances b JOIN inventory_lots l ON l.id=b.lot_id LEFT JOIN(SELECT rl.lot_id,r.warehouse_id,sum(rl.quantity)::int qty FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id WHERE ${activeReservation} GROUP BY rl.lot_id,r.warehouse_id)a ON a.lot_id=l.id AND a.warehouse_id=b.warehouse_id WHERE l.variant_id=$1 AND b.warehouse_id=$2 AND ${validLot}`,[variantId,warehouseId],connection);
 const [reserved]=await query(`SELECT coalesce(sum(r.quantity),0)::int n FROM reservations r WHERE r.variant_id=$1 AND r.warehouse_id=$2 AND ${activeReservation}`,[variantId,warehouseId],connection);
 return Math.max(0,Math.min(Number(stock.n),balance.on_hand-reserved.n)-balance.safety_stock);
}
export async function assertUntrackedStock(variantIds:string[],connection:Connection){
 const tracked=await query('SELECT id FROM variants WHERE id=ANY($1::text[]) AND lot_tracking=true',[variantIds],connection);
 requireCondition(!tracked.length,'LOT_ACTION_REQUIRED','Lot takipli stok için Lot ve son kullanma ekranını kullanın. Lotu bilinmeyen iade satışa açılamaz.',409);
}
export async function reserveLots(reservationId:string,variantId:string,quantity:number,warehouseId:string,connection:Connection){
 const [variant]=await query('SELECT lot_tracking FROM variants WHERE id=$1',[variantId],connection);if(!variant?.lot_tracking)return;
 const lots=await query(`SELECT l.id,b.on_hand FROM inventory_lot_balances b JOIN inventory_lots l ON l.id=b.lot_id WHERE l.variant_id=$1 AND b.warehouse_id=$2 AND ${validLot} ORDER BY l.expires_at ASC NULLS LAST,l.id FOR UPDATE OF b,l`,[variantId,warehouseId],connection);
 let remaining=quantity;
 for(const lot of lots){
  const [held]=await query(`SELECT coalesce(sum(rl.quantity),0)::int n FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id WHERE rl.lot_id=$1 AND r.warehouse_id=$2 AND ${activeReservation}`,[lot.id,warehouseId],connection);
  const take=Math.min(remaining,Math.max(0,lot.on_hand-held.n));
  if(take>0){await query('INSERT INTO reservation_lots(reservation_id,lot_id,quantity) VALUES($1,$2,$3)',[reservationId,lot.id,take],connection);remaining-=take;}
  if(!remaining)break;
 }
 requireCondition(!remaining,'LOT_STOCK_UNAVAILABLE','Uygun son kullanma tarihli lot stoğu kalmadı.',409);
}
export async function paymentLotsAvailable(orderId:string,connection:Connection):Promise<boolean>{
 const reservations=await query('SELECT r.id,r.variant_id,r.warehouse_id,r.quantity,v.lot_tracking FROM reservations r JOIN variants v ON v.id=r.variant_id WHERE r.order_id=$1 ORDER BY r.variant_id,r.warehouse_id',[orderId],connection);
 for(const reservation of reservations){
  if(!reservation.lot_tracking)continue;
  const lots=await query(`SELECT rl.quantity,b.on_hand,l.variant_id,b.warehouse_id,(${validLot}) valid FROM reservation_lots rl JOIN inventory_lots l ON l.id=rl.lot_id JOIN inventory_lot_balances b ON b.lot_id=l.id AND b.warehouse_id=$2 WHERE rl.reservation_id=$1 ORDER BY l.id FOR UPDATE OF b,l`,[reservation.id,reservation.warehouse_id],connection);
  if(lots.reduce((n,l)=>n+l.quantity,0)!==reservation.quantity||lots.some(l=>!l.valid||l.variant_id!==reservation.variant_id||l.on_hand<l.quantity))return false;
 }
 return true;
}
export async function consumeReservationLots(reservation:{id:string;order_id:string;variant_id:string;warehouse_id:string},connection:Connection):Promise<boolean>{
 const [variant]=await query('SELECT lot_tracking FROM variants WHERE id=$1',[reservation.variant_id],connection);if(!variant?.lot_tracking)return false;
 const lots=await query('SELECT lot_id,quantity FROM reservation_lots WHERE reservation_id=$1 ORDER BY lot_id',[reservation.id],connection);
 requireCondition(lots.length,'LOT_ALLOCATION_REQUIRED','Sipariş lot tahsisi doğrulanamadı.',409);
 for(const lot of lots){
  const updated=await query('UPDATE inventory_lot_balances SET on_hand=on_hand-$3 WHERE lot_id=$1 AND warehouse_id=$2 AND on_hand>=$3 RETURNING lot_id',[lot.lot_id,reservation.warehouse_id,lot.quantity],connection);
  requireCondition(updated.length,'LOT_STOCK_CONFLICT','Lot stoğu doğrulanamadı.',409);
  await query("INSERT INTO inventory_movements(variant_id,warehouse_id,lot_id,type,quantity,reason,reference) VALUES($1,$2,$3,'sale',$4,'Doğrulanmış ödeme lot tüketimi',$5)",[reservation.variant_id,reservation.warehouse_id,lot.lot_id,-lot.quantity,`payment:${reservation.order_id}:${reservation.variant_id}:${lot.lot_id}`],connection);
 }
 return true;
}
export async function assertOrderLotsShippable(orderId:string,connection:Connection){
 const invalid=await query(`SELECT l.id FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id JOIN inventory_lots l ON l.id=rl.lot_id WHERE r.order_id=$1 AND r.status='consumed' AND NOT(${validLot}) FOR SHARE OF l`,[orderId],connection);
 requireCondition(!invalid.length,'LOT_SHIPMENT_BLOCKED','Sipariş lotu geri çağrılmış, karantinada veya son kullanma tarihi geçmiş. Sevkiyat kapalıdır.',409);
}
export async function lockReceiptKey(idempotencyKey:string,connection:Connection){
 await query('SELECT pg_advisory_xact_lock(hashtextextended($1,0))',['inventory-receipt:'+idempotencyKey],connection);
}
/** Caller transaction owns both PO counters and this single physical-stock writer. */
export async function receiveLotStock(data:PurchaseReceiptLotInput&{variantId:string;reason:string},context:{connection:Connection;actorId:string;reference:string;movementType:'lot_receipt'|'purchase_lot_receipt'}){
 const {connection}=context,variantId=data.variantId;await lockPhysicalStockTargets([variantId],connection);
 const [balance]=await query("SELECT variant_id FROM inventory_balance WHERE variant_id=$1 AND warehouse_id='main' FOR UPDATE",[variantId],connection);requireCondition(balance,'INVENTORY_NOT_FOUND','Ana depo stok kaydı bulunamadı.',404);
 const [variant]=await query('SELECT lot_tracking,expiry_required FROM variants WHERE id=$1',[variantId],connection);
   requireCondition(variant.lot_tracking,'LOT_TRACKING_REQUIRED','Önce boş stok için lot takibini açın.',409);
   requireCondition(!variant.expiry_required||data.expiresAt,'LOT_EXPIRY_REQUIRED','Bu stok kodunda son kullanma tarihi zorunludur.',409);
   const [date]=await query("SELECT $1::date IS NULL OR $1::date>(now() AT TIME ZONE 'Europe/Istanbul')::date valid",[data.expiresAt??null],connection);
   requireCondition(date.valid||data.quarantined,'LOT_EXPIRED','Tarihi geçmiş lot yalnız açık karantina kabulüyle alınabilir.',409);
   let [lot]=await query("SELECT *,to_char(expires_at,'YYYY-MM-DD') expiry_date FROM inventory_lots WHERE variant_id=$1 AND lot_number=$2 FOR UPDATE",[variantId,data.lotNumber],connection);
   if(lot){requireCondition(lot.expiry_date===(data.expiresAt??null),'LOT_METADATA_CONFLICT','Aynı üretici lotunun son kullanma tarihi değiştirilemez.',409);requireCondition(!lot.recall_reference,'LOT_RECALLED','Geri çağrılan lot için yeni mal kabulü kapalıdır.',409);requireCondition(lot.quarantined===data.quarantined,'LOT_QUARANTINE_MISMATCH','Mal kabulü mevcut lotun karantina durumuyla eşleşmelidir.',409);}
   else [lot]=await query('INSERT INTO inventory_lots(variant_id,lot_number,expires_at,source_reference,quarantined) VALUES($1,$2,$3,$4,$5) RETURNING *',[variantId,data.lotNumber,data.expiresAt??null,data.sourceReference,data.quarantined],connection);
   if(!lot.source_reference)await query('UPDATE inventory_lots SET source_reference=$2 WHERE id=$1',[lot.id,data.sourceReference],connection);
   const lotId=String(lot.id);const good=data.quarantined?0:data.quantity,bad=data.quarantined?data.quantity:0;
   await query("INSERT INTO inventory_lot_balances(lot_id,warehouse_id,on_hand,quarantine) VALUES($1,'main',$2,$3) ON CONFLICT(lot_id,warehouse_id) DO UPDATE SET on_hand=inventory_lot_balances.on_hand+excluded.on_hand,quarantine=inventory_lot_balances.quarantine+excluded.quarantine",[lotId,good,bad],connection);
   await query("UPDATE inventory_balance SET on_hand=on_hand+$2,quarantine=quarantine+$3 WHERE variant_id=$1 AND warehouse_id='main'",[variantId,good,bad],connection);
   const [movement]=await query("INSERT INTO inventory_movements(variant_id,warehouse_id,lot_id,type,quantity,quarantine_quantity,reason,reference,actor_id) VALUES($1,'main',$2,$3,$4,$5,$6,$7,$8) RETURNING id,created_at",[variantId,lotId,context.movementType,good,bad,data.reason,context.reference,context.actorId],connection);
   return {lotId,movementId:String(movement.id),quantity:data.quantity,quarantineQuantity:bad,sourceReference:data.sourceReference,receivedAt:movement.created_at.toISOString()};
}
export async function manageLot(input:unknown,principal:Principal){
 assertPermission(principal,'lots','write');const parsed=schema.safeParse(input);requireCondition(parsed.success,'INVALID_LOT','Lot alanlarını ve belge referansını kontrol edin.');const data=parsed.data;
 const hash=createHash('sha256').update(JSON.stringify({data,actor:principal.id})).digest('hex');
 return transaction(async connection=>{
  if(data.action==='receipt')await lockReceiptKey(data.idempotencyKey,connection);else await query('SELECT pg_advisory_xact_lock(hashtextextended($1,0))',['lot-operation:'+data.idempotencyKey],connection);
  const [existing]=await query('SELECT request_hash,result FROM lot_operations WHERE idempotency_key=$1',[data.idempotencyKey],connection);
  if(existing){requireCondition(existing.request_hash===hash,'IDEMPOTENCY_CONFLICT','Aynı işlem anahtarı farklı içerikle kullanılamaz.',409);return {...existing.result,duplicate:true};}
  if(data.action==='receipt')requireCondition(!(await query('SELECT 1 FROM purchase_receipts WHERE idempotency_key=$1',[data.idempotencyKey],connection)).length,'IDEMPOTENCY_CONFLICT','Bu kabul anahtarı başka bir stok kabulünde kullanılmış.',409);
  let receiptResult:Awaited<ReturnType<typeof receiveLotStock>>|undefined;
  let variantId:string,lotId:string|null=null;
  if('variantId'in data)variantId=data.variantId;else{const [lot]=await query('SELECT variant_id FROM inventory_lots WHERE id=$1',[data.lotId],connection);requireCondition(lot,'LOT_NOT_FOUND','Lot bulunamadı.',404);variantId=lot.variant_id;lotId=data.lotId;}
  if(data.action==='enable'){await query("SELECT pg_advisory_xact_lock_shared(hashtext('bundle-definition'))",[],connection);requireCondition(!(await query('SELECT 1 FROM bundle_components WHERE bundle_variant_id=$1',[variantId],connection)).length,'BUNDLE_LOT_TRACKING_DISABLED','Setin kendisi yerine fiziksel bileşenlerin lotunu izleyin.',409);}
  await lockPhysicalStockTargets([variantId],connection);
  const [balance]=await query("SELECT * FROM inventory_balance WHERE variant_id=$1 AND warehouse_id='main' FOR UPDATE",[variantId],connection);requireCondition(balance,'INVENTORY_NOT_FOUND','Ana depo stok kaydı bulunamadı.',404);
  const [variant]=await query(`SELECT lot_tracking,expiry_required FROM variants WHERE id=$1${data.action==='enable'?' FOR UPDATE':''}`,[variantId],connection);
  if(data.action==='enable'){
   if(!variant.lot_tracking||variant.expiry_required!==data.expiryRequired){
    const [held]=await query("SELECT count(*)::int n FROM reservations WHERE variant_id=$1 AND status='active' AND expires_at>now()",[variantId],connection);
    const balances=await query('SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=$1 ORDER BY warehouse_id FOR UPDATE',[variantId],connection);
    requireCondition(balances.every(b=>b.on_hand===0&&b.quarantine===0)&&held.n===0,'LOT_ATTRIBUTION_REQUIRED','Lot takibi yalnız tüm depo stoğu ve rezervasyonu sıfırken açılabilir. Mevcut stoğa lot uydurulamaz.',409);
    const [bundle]=await query('SELECT 1 FROM bundle_components WHERE bundle_variant_id=$1 LIMIT 1',[variantId],connection);requireCondition(!bundle,'BUNDLE_LOT_TRACKING_DISABLED','Setin kendisi yerine fiziksel bileşenlerin lotunu izleyin.',409);
    await query('UPDATE variants SET lot_tracking=true,expiry_required=$2 WHERE id=$1',[variantId,data.expiryRequired],connection);
   }
  }else if(data.action==='receipt'){
   const received=await receiveLotStock({...data,expiresAt:data.expiresAt??null},{connection,actorId:principal.id,reference:`lot:${data.idempotencyKey}`,movementType:'lot_receipt'});lotId=received.lotId;receiptResult=received;
  }else{
   const [lot]=await query('SELECT * FROM inventory_lots WHERE id=$1 FOR UPDATE',[lotId],connection);
   const [lotBalance]=await query("SELECT * FROM inventory_lot_balances WHERE lot_id=$1 AND warehouse_id='main' FOR UPDATE",[lotId],connection);requireCondition(lotBalance,'LOT_BALANCE_REQUIRED','Lot stok detayı bulunamadı.',409);
   if(data.action==='release'){
    const [date]=await query("SELECT $1::date IS NULL OR $1::date>(now() AT TIME ZONE 'Europe/Istanbul')::date valid",[lot.expires_at],connection);
    requireCondition(!lot.recall_reference&&date.valid,'LOT_RELEASE_BLOCKED','Geri çağrılan veya tarihi geçen lot satışa açılamaz.',409);
   }
   const release=data.action==='release',quantity=release?lotBalance.quarantine:lotBalance.on_hand,delta=release?quantity:-quantity;
   await query('UPDATE inventory_lots SET quarantined=$2,recall_reference=CASE WHEN $3::text IS NULL THEN recall_reference ELSE $3 END WHERE id=$1',[lotId,!release,data.action==='recall'?data.reference:null],connection);
   await query("UPDATE inventory_lot_balances SET on_hand=on_hand+$2,quarantine=quarantine-$2 WHERE lot_id=$1 AND warehouse_id='main'",[lotId,delta],connection);
   await query("UPDATE inventory_balance SET on_hand=on_hand+$2,quarantine=quarantine-$2 WHERE variant_id=$1 AND warehouse_id='main'",[variantId,delta],connection);
   await query("INSERT INTO inventory_movements(variant_id,warehouse_id,lot_id,type,quantity,quarantine_quantity,reason,reference,actor_id) VALUES($1,'main',$2,$3,$4,$5,$6,$7,$8)",[variantId,lotId,'lot_'+data.action,delta,-delta,data.reason,`lot:${data.idempotencyKey}`,principal.id],connection);
  }
  const result={variantId,lotId,action:data.action,...(receiptResult??{})};
  await query('INSERT INTO lot_operations(idempotency_key,request_hash,action,lot_id,actor_id,result) VALUES($1,$2,$3,$4,$5,$6)',[data.idempotencyKey,hash,data.action,lotId,principal.id,JSON.stringify(result)],connection);
  await query("INSERT INTO audit_log(actor_id,action,resource,resource_id,details) VALUES($1,$2,'lots',$3,$4)",[principal.id,data.action,lotId??variantId,JSON.stringify({reason:data.reason,...('reference'in data?{reference:data.reference}:{}),...('sourceReference'in data?{sourceReference:data.sourceReference,quantity:data.quantity}:{})})],connection);
  return result;
 });
}
export async function listLots(principal:Principal,filter:Record<string,string>={}){
 assertPermission(principal,'lots','read');const page=Math.max(1,Math.min(100000,Number(filter.page)||1)),search=`%${(filter.q??'').slice(0,100).replace(/[\\%_]/g,'\\$&')}%`;
 const conditions="(sg_search_normalize(v.sku||' '||p.name||' '||l.lot_number) LIKE sg_search_normalize($1))AND($2::text IS NULL OR v.id=$2)";
 const rows=await query(`SELECT l.id,l.variant_id,v.sku,p.name,l.lot_number,to_char(l.expires_at,'YYYY-MM-DD') expires_at,l.quarantined,l.recall_reference,l.source_reference,b.warehouse_id,b.on_hand,b.quarantine,coalesce(a.qty,0)::int reserved,CASE WHEN ${validLot} THEN greatest(0,b.on_hand-coalesce(a.qty,0))::int ELSE 0 END available FROM inventory_lots l JOIN inventory_lot_balances b ON b.lot_id=l.id JOIN variants v ON v.id=l.variant_id JOIN products p ON p.id=v.product_id LEFT JOIN(SELECT rl.lot_id,r.warehouse_id,sum(rl.quantity)::int qty FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id WHERE ${activeReservation} GROUP BY rl.lot_id,r.warehouse_id)a ON a.lot_id=l.id AND a.warehouse_id=b.warehouse_id WHERE ${conditions} ORDER BY l.expires_at ASC NULLS LAST,l.id LIMIT 25 OFFSET $3`,[search,filter.variantId??null,(page-1)*25]);
 const [count]=await query(`SELECT count(*)::int n FROM inventory_lots l JOIN variants v ON v.id=l.variant_id JOIN products p ON p.id=v.product_id WHERE ${conditions}`,[search,filter.variantId??null]);
 return {rows:rows.map(camel),total:count.n,page};
}
export async function lotSources(principal:Principal,lotId:string,filter:{q?:string;page?:number}={}):Promise<PurchaseLotSources>{
 assertPermission(principal,'lots','read');assertPermission(principal,'purchases','read');
 const parsed=z.object({lotId:z.string().min(1).max(300).refine(value=>!/[\u0000-\u001f\u007f]/u.test(value)),q:z.string().max(100).default(''),page:z.number().int().min(1).max(100000).default(1)}).safeParse({lotId,...filter});
 requireCondition(parsed.success,'INVALID_FILTER','Kaynak arama ve sayfa alanlarını kontrol edin.');const {q,page}=parsed.data;
 const search=`%${q.replace(/[\\%_]/g,'\\$&')}%`;
 const [data]=await query(`WITH sources AS(
  SELECT r.movement_id id,'purchase'::text kind,p.purchase_id,p.id receipt_id,s.name supplier_name,r.lot_id,r.variant_id,r.quantity,r.quarantine_quantity,r.source_reference,p.source_reference receipt_source_reference,p.created_at received_at
  FROM purchase_receipt_lots r JOIN purchase_receipts p ON p.id=r.receipt_id JOIN purchase_orders o ON o.id=p.purchase_id JOIN suppliers s ON s.id=o.supplier_id WHERE r.lot_id=$1
  UNION ALL
  SELECT m.id,'direct'::text,NULL::text,NULL::text,NULL::text,m.lot_id,m.variant_id,m.quantity+m.quarantine_quantity,m.quarantine_quantity,nullif(l.result->>'sourceReference',''),NULL::text,m.created_at
  FROM inventory_movements m JOIN lot_operations l ON l.lot_id=m.lot_id AND l.action='receipt' AND m.reference='lot:'||l.idempotency_key WHERE m.lot_id=$1 AND m.type='lot_receipt'
 ),filtered AS(SELECT * FROM sources WHERE sg_search_normalize(concat_ws(' ',purchase_id,receipt_id,supplier_name,source_reference,receipt_source_reference)) LIKE sg_search_normalize($2))
 SELECT(SELECT count(*)::int FROM filtered) total,coalesce((SELECT jsonb_agg(row ORDER BY row.received_at DESC,row.id) FROM(SELECT * FROM filtered ORDER BY received_at DESC,id LIMIT 25 OFFSET $3)row),'[]'::jsonb) rows`,[lotId,search,(page-1)*25]);
 return {rows:data.rows.map((row:Record<string,unknown>)=>({id:String(row.id),kind:row.kind as 'purchase'|'direct',purchaseId:row.purchase_id===null?null:String(row.purchase_id),receiptId:row.receipt_id===null?null:String(row.receipt_id),supplierName:row.supplier_name===null?null:String(row.supplier_name),lotId:String(row.lot_id),variantId:String(row.variant_id),quantity:Number(row.quantity),quarantineQuantity:Number(row.quarantine_quantity),sourceReference:row.source_reference===null?null:String(row.source_reference),receiptSourceReference:row.receipt_source_reference===null?null:String(row.receipt_source_reference),receivedAt:String(row.received_at)})),total:Number(data.total),page,pageSize:25};
}
export async function recallOrders(lotId:string,principal:Principal,page=1){
 assertPermission(principal,'lots','read');requireCondition(lotId.length>0&&lotId.length<=300,'INVALID_LOT','Lot seçin.');
 page=Math.max(1,Math.min(100000,Number(page)||1));
 const rows=await query('SELECT o.id,o.number,o.status,o.payment_status,r.status reservation_status,r.warehouse_id,rl.quantity,l.lot_number,l.recall_reference FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id JOIN orders o ON o.id=r.order_id JOIN inventory_lots l ON l.id=rl.lot_id WHERE l.id=$1 ORDER BY o.created_at DESC LIMIT 25 OFFSET $2',[lotId,(page-1)*25]);
 const [count]=await query('SELECT count(*)::int n FROM reservation_lots WHERE lot_id=$1',[lotId]);
 return {rows:rows.map(camel),total:count.n,page};
}
export async function unknownLotReturns(principal:Principal,filter:Record<string,string>={}){
 assertPermission(principal,'lots','read');const page=Math.max(1,Math.min(100000,Number(filter.page)||1)),search=`%${(filter.q??'').slice(0,100).replace(/[\\%_]/g,'\\$&')}%`;
 const from="FROM return_stock_lines l JOIN returns r ON r.id=l.return_id JOIN orders o ON o.id=r.order_id JOIN variants v ON v.id=l.variant_id JOIN products p ON p.id=v.product_id WHERE v.lot_tracking=true AND r.restocked=false AND sg_search_normalize(v.sku||' '||p.name||' '||o.number) LIKE sg_search_normalize($1)";
 const rows=await query(`SELECT r.id,r.status,r.created_at,o.number,l.variant_id,v.sku,p.name,l.quantity,l.warehouse_id ${from} ORDER BY r.created_at DESC,l.variant_id LIMIT 25 OFFSET $2`,[search,(page-1)*25]);
 const [count]=await query(`SELECT count(*)::int n ${from}`,[search]);
 return {rows:rows.map(camel),total:count.n,page};
}
