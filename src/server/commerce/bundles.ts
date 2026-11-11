/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/bundles.ts
 * Açıklama   : Sürümlü set tanımı, değişim önizlemesi ve stok/onay sınırlarını yönetir.
 */
import {z} from 'zod';
import {query,transaction,type Connection} from '../db';
import type {Principal} from '../../shared/contracts';
import {bundleDifferences,type BundleComponent,type BundleEditorData,type BundlePreview,type BundleBlocker,type BundleQuantity} from '../../shared/bundle-management';
import {assertPermission,requireCondition} from './rules';
import {variantAvailability} from './catalog';
const id=z.string().trim().min(1).max(300),quantity=z.number().int().min(1).max(99),version=z.number().int().min(0).max(2147483646).default(0);
const fields={id,expectedVersion:version,components:z.array(z.object({variantId:id,quantity}).strict()).min(1).max(20)};
const schema=z.discriminatedUnion('action',[
 z.object({action:z.literal('bundle'),...fields,reason:z.string().trim().min(5).max(500)}).strict(),
 z.object({action:z.literal('bundlePreview'),...fields}).strict()
]);
const local=()=>['development','test'].includes(process.env.APP_ENV??'');
function readPermission(principal:Principal){assertPermission(principal,'variants','read');requireCondition(['admin','catalog','warehouse','finance'].includes(principal.role),'FORBIDDEN','Set tanımını incelemek için yetkiniz yok.',403);}
function writePermission(principal:Principal){assertPermission(principal,'variants','write');requireCondition(['admin','catalog'].includes(principal.role),'FORBIDDEN','Set tanımını yalnız katalog yetkilisi düzenleyebilir.',403);}
interface Parent{id:string;product_id:string;sku:string;active:boolean;lot_tracking:boolean;bundle_version:number;product_name:string;product_status:string;fixture:boolean;}
async function lockProductVariants(variantIds:string[],connection:Connection){
 const ids=[...new Set(variantIds)].sort(),links=await query('SELECT id,product_id FROM variants WHERE id=ANY($1::text[]) ORDER BY id',[ids],connection);
 requireCondition(links.length===ids.length,'VARIANT_NOT_FOUND','Fiziksel stok kodu bulunamadı.',404);
 await query('SELECT id FROM products WHERE id=ANY($1::text[]) ORDER BY id FOR UPDATE',[[...new Set(links.map(row=>row.product_id))].sort()],connection);
 await query('SELECT id FROM variants WHERE id=ANY($1::text[]) ORDER BY id FOR UPDATE',[ids],connection);
}
/** Tanım dönüşümü ile fiziksel stok yazımı aynı global → ürün → SKU kilit sırasını izler. */
export async function lockPhysicalStockTargets(variantIds:string[],connection:Connection){
 await query("SELECT pg_advisory_xact_lock_shared(hashtext('bundle-definition'))",[],connection);
 await lockProductVariants(variantIds,connection);
 const logical=await query('SELECT 1 FROM bundle_components WHERE bundle_variant_id=ANY($1::text[]) LIMIT 1',[variantIds],connection);
 requireCondition(!logical.length,'BUNDLE_PHYSICAL_STOCK_DISABLED','Set üst koduna fiziksel stok yazılamaz. Mal kabulü ve iade fiziksel bileşen kodlarına bağlanmalıdır.',409);
}
async function parentRecord(variantId:string,connection:Connection):Promise<Parent>{
 const [parent]=await query<Parent>(`SELECT v.id,v.product_id,v.sku,v.active,v.lot_tracking,v.bundle_version,p.name product_name,p.status product_status,p.fixture FROM variants v JOIN products p ON p.id=v.product_id WHERE v.id=$1`,[variantId],connection);
 requireCondition(parent,'VARIANT_NOT_FOUND','Stok kodu bulunamadı.',404);return parent;
}
async function components(variantId:string,connection:Connection):Promise<BundleComponent[]>{
 const rows=await query('SELECT v.id,v.sku,v.name,v.active,v.lot_tracking,p.name product_name,b.quantity FROM bundle_components b JOIN variants v ON v.id=b.component_variant_id JOIN products p ON p.id=v.product_id WHERE b.bundle_variant_id=$1 ORDER BY v.id',[variantId],connection);
 const result:BundleComponent[]=[];for(const row of rows)result.push({variantId:row.id,sku:row.sku,name:row.name,productName:row.product_name,active:row.active,lotTracking:row.lot_tracking,quantity:row.quantity,available:await variantAvailability(row.id,connection)});return result;
}
const capacity=(items:BundleComponent[])=>items.length?Math.min(...items.map(item=>Math.floor(item.available/item.quantity))):0;
async function blockers(parent:Parent,connection:Connection,lock=false):Promise<BundleBlocker[]>{
 const result:BundleBlocker[]=[];
 if(!parent.active)result.push({code:'BUNDLE_PARENT_INACTIVE',message:'Arşivdeki stok kodunun set tanımı değiştirilemez.'});
 if(parent.fixture&&!local())result.push({code:'FIXTURE_NOT_ALLOWED',message:'Örnek set gerçek satış ortamında düzenlenemez.'});
 if(parent.lot_tracking)result.push({code:'BUNDLE_LOT_TRACKING_DISABLED',message:'Lot takipli fiziksel stok kodunu set üst kaydına dönüştüremezsiniz.'});
 const balances=await query(`SELECT on_hand,quarantine FROM inventory_balance WHERE variant_id=$1 ORDER BY warehouse_id${lock?' FOR UPDATE':''}`,[parent.id],connection);
 if(balances.some(row=>row.on_hand>0||row.quarantine>0))result.push({code:'BUNDLE_PARENT_STOCK',message:'Set üst kodunda fiziksel veya karantina stoğu var. Gerçek stok kaydı çözümlenmeden tanım değiştirilemez.'});
 const reserved=await query("SELECT 1 FROM reservations WHERE variant_id=$1 AND status='active' AND expires_at>now() UNION ALL SELECT 1 FROM order_items i JOIN orders o ON o.id=i.order_id WHERE i.variant_id=$1 AND o.status='awaiting_payment' AND o.expires_at>now() LIMIT 1",[parent.id],connection);
 if(reserved.length)result.push({code:'BUNDLE_RESERVED',message:'Etkin ödeme rezervasyonu varken set tanımı değiştirilemez.'});
 const used=await query('SELECT 1 FROM bundle_components WHERE component_variant_id=$1 LIMIT 1',[parent.id],connection);
 if(used.length)result.push({code:'NESTED_BUNDLE_DISABLED',message:'Başka setin fiziksel bileşeni olan stok kodu set üst kaydına dönüştürülemez.'});
 const physicalHistory=await query(`SELECT 1 FROM order_items i WHERE
  (i.variant_id=$1 AND CASE WHEN jsonb_typeof(i.snapshot->'bundleComponents')='array' THEN jsonb_array_length(i.snapshot->'bundleComponents')=0 ELSE true END)
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(CASE WHEN jsonb_typeof(i.snapshot->'bundleComponents')='array' THEN i.snapshot->'bundleComponents' ELSE '[]'::jsonb END) component WHERE component->>'variantId'=$1)
  UNION ALL SELECT 1 FROM return_stock_lines WHERE variant_id=$1 LIMIT 1`,[parent.id],connection);
 if(physicalHistory.length)result.push({code:'BUNDLE_PHYSICAL_HISTORY',message:'Bu stok kodu geçmiş sipariş veya iadede fiziksel ürün olarak kullanılmış. Set için yeni bir üst stok kodu oluşturun.'});
 return result;
}
export async function bundleEditorData(variantId:string,principal:Principal):Promise<BundleEditorData>{
 readPermission(principal);requireCondition(typeof variantId==='string'&&variantId.length>0&&variantId.length<=300,'INVALID_BUNDLE','Bir stok kodu seçin.');
 return transaction(async connection=>{
  await query("SELECT pg_advisory_xact_lock_shared(hashtext('bundle-definition'))",[],connection);
  const parent=await parentRecord(variantId,connection),items=await components(variantId,connection);
  const rows=await query('SELECT version,previous_components,components,reason,created_at FROM bundle_changes WHERE variant_id=$1 ORDER BY version DESC LIMIT 10',[variantId],connection);
  return {id:parent.id,sku:parent.sku,productName:parent.product_name,version:parent.bundle_version,productStatus:parent.product_status,components:items,capacity:capacity(items),canWrite:['admin','catalog'].includes(principal.role),blockers:await blockers(parent,connection),history:rows.map(row=>({version:row.version,before:row.previous_components,after:row.components,reason:row.reason,createdAt:row.created_at.toISOString()}))};
 });
}
export async function bundleCandidates(principal:Principal,filter:Record<string,string>={}){
 readPermission(principal);const page=Math.max(1,Math.min(100000,Math.floor(Number(filter.page)||1))),search=`%${(filter.q??'').slice(0,100).replace(/[\\%_]/g,'\\$&')}%`;
 const where="v.active=true AND($2::text IS NULL OR v.id<>$2)AND($3=true OR p.fixture=false) AND NOT EXISTS(SELECT 1 FROM bundle_components b WHERE b.bundle_variant_id=v.id) AND(sg_search_normalize(v.sku) LIKE sg_search_normalize($1) OR sg_search_normalize(p.name) LIKE sg_search_normalize($1))";
 const rows=await query(`SELECT v.id,v.sku,v.name,v.active,v.lot_tracking,p.name product_name FROM variants v JOIN products p ON p.id=v.product_id WHERE ${where} ORDER BY p.name COLLATE "tr-x-icu",v.sku,v.id LIMIT 25 OFFSET $4`,[search,filter.exclude??null,local(),(page-1)*25]);
 const [count]=await query(`SELECT count(*)::int n FROM variants v JOIN products p ON p.id=v.product_id WHERE ${where}`,[search,filter.exclude??null,local()]);
 const result=[];for(const row of rows)result.push({id:row.id,variantId:row.id,sku:row.sku,name:row.name,productName:row.product_name,active:row.active,lotTracking:row.lot_tracking,available:await variantAvailability(row.id),quantity:1});return {rows:result,total:count.n,page};
}
export async function manageBundle(input:unknown,principal:Principal):Promise<BundlePreview|{id:string;version:number;status:string}>{
 writePermission(principal);const parsed=schema.safeParse(input);requireCondition(parsed.success,'INVALID_BUNDLE','Set bileşenlerini, adetleri ve gerekçeyi kontrol edin.');const data=parsed.data;
 requireCondition(new Set(data.components.map(item=>item.variantId)).size===data.components.length&&data.components.every(item=>item.variantId!==data.id),'INVALID_BUNDLE','Set kendisini içeremez; aynı fiziksel stok kodu bir kez seçilmelidir.');
 return transaction(async connection=>{
  // Set edits are rare: serialize definitions across parents to prevent concurrent
  // A→B/B→A compositions. Customer stock decisions still use their normal locks.
  await query("SELECT pg_advisory_xact_lock(hashtext('bundle-definition'))",[],connection);
  const previous=await query('SELECT component_variant_id FROM bundle_components WHERE bundle_variant_id=$1',[data.id],connection);
  const involved=[...new Set([data.id,...data.components.map(item=>item.variantId),...previous.map(row=>String(row.component_variant_id))])].sort();
  await lockProductVariants(involved,connection);
  const parent=await parentRecord(data.id,connection);requireCondition(parent.bundle_version===data.expectedVersion,'BUNDLE_VERSION_CONFLICT','Bu set başka bir işlemde değişti. Güncel tanımı yeniden yükleyin.',409);
  const blocked=await blockers(parent,connection,true);if(blocked.length)requireCondition(false,blocked[0].code,blocked[0].message,409);
  const nested=await query('SELECT 1 FROM bundle_components WHERE bundle_variant_id=ANY($1::text[]) LIMIT 1',[data.components.map(item=>item.variantId)],connection);requireCondition(!nested.length,'NESTED_BUNDLE_DISABLED','Setin içine başka bir set eklenemez.',409);
  const rows=await query('SELECT v.id,v.sku,v.name,v.active,v.lot_tracking,p.fixture,p.name product_name FROM variants v JOIN products p ON p.id=v.product_id WHERE v.id=ANY($1::text[]) ORDER BY v.id',[data.components.map(item=>item.variantId)],connection);
  const desired:BundleComponent[]=[];for(const row of rows){requireCondition(row.active,'BUNDLE_COMPONENT_UNAVAILABLE','Arşivdeki bileşen sete eklenemez.',409);requireCondition(!row.fixture||local(),'FIXTURE_NOT_ALLOWED','Örnek bileşen gerçek satış ortamında kullanılamaz.',503);desired.push({variantId:row.id,quantity:data.components.find(item=>item.variantId===row.id)!.quantity,sku:row.sku,name:row.name,productName:row.product_name,active:row.active,lotTracking:row.lot_tracking,available:await variantAvailability(row.id,connection)});}
  const current=await components(data.id,connection),details=new Map([...current,...desired].map(item=>[item.variantId,item]));
  const differences=bundleDifferences(current,desired).map(change=>({...change,sku:details.get(change.variantId)!.sku,name:details.get(change.variantId)!.name,productName:details.get(change.variantId)!.productName}));
  if(data.action==='bundlePreview')return {id:data.id,expectedVersion:data.expectedVersion,components:desired,changes:differences,capacityBefore:capacity(current),capacityAfter:capacity(desired),hasChanges:differences.length>0};
  requireCondition(differences.length>0,'NO_BUNDLE_CHANGES','Set tanımında değişiklik bulunmuyor.',409);
  await query('DELETE FROM bundle_components WHERE bundle_variant_id=$1',[data.id],connection);
  for(const item of desired)await query('INSERT INTO bundle_components(bundle_variant_id,component_variant_id,quantity) VALUES($1,$2,$3)',[data.id,item.variantId,item.quantity],connection);
  const next=parent.bundle_version+1;
  await query('UPDATE variants SET bundle_version=$2 WHERE id=$1',[data.id,next],connection);
  await query("UPDATE products SET status='review',updated_at=now() WHERE id=$1",[parent.product_id],connection);
  await query('UPDATE product_eligibility SET approved=false WHERE variant_id=$1',[data.id],connection);
  await query('UPDATE shipping_approvals SET accepted=false WHERE variant_id=$1',[data.id],connection);
  await query('UPDATE product_documents SET reviewed=false WHERE variant_id=$1',[data.id],connection);
  const snapshot=(items:BundleComponent[]):(BundleQuantity&{sku:string;name:string;productName:string})[]=>items.map(({variantId,quantity,sku,name,productName})=>({variantId,quantity,sku,name,productName}));
  await query('INSERT INTO bundle_changes(variant_id,version,previous_components,components,reason,actor_id) VALUES($1,$2,$3,$4,$5,$6)',[data.id,next,JSON.stringify(snapshot(current)),JSON.stringify(snapshot(desired)),data.reason,principal.id],connection);
  await query("INSERT INTO audit_log(actor_id,action,resource,resource_id,details) VALUES($1,'bundle','variants',$2,$3)",[principal.id,data.id,JSON.stringify({version:next,reason:data.reason,before:snapshot(current),after:snapshot(desired),reviewRequired:true})],connection);
  return {id:data.id,version:next,status:'review'};
 });
}
