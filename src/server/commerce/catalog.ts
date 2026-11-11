/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/catalog.ts
 * Açıklama   : Sunucu katalog araması, varyant ve kalıcı sepet erişimi.
 */
import { pool,query,transaction,type Connection } from "../db";
import {catalogQueryKeys,type Cart,type CatalogFilter,type CatalogResult,type Currency,type Product,type Locale} from "../../shared/contracts";
import { createHash } from "node:crypto";
import {z} from 'zod';
import { requireCondition } from "./rules";
import {trackedAvailable} from './lots';
import {publicProductTechnical,publicVariantTechnical} from '../compliance';

export const tokenHash=(token:string)=>createHash("sha256").update(token).digest("hex");
export const normalizeSearch=(value:string)=>value.toLocaleLowerCase("tr-TR").normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/ı/g,"i");
const localFixturesAllowed=()=>['development','test'].includes(process.env.APP_ENV??'');
const searchSql="lower(translate(p.name || ' ' || p.name_en || ' ' || p.description || ' ' || p.material,'ıİğĞüÜşŞöÖçÇ','iigguussoocc'))";
export async function variantAvailability(variantId:string,connection?:Connection):Promise<number> {
 const components=await query("SELECT component_variant_id,quantity FROM bundle_components WHERE bundle_variant_id=$1",[variantId],connection);
 const ids=components.length?components.map(x=>x.component_variant_id):[variantId];
 const balances=await query(`SELECT b.variant_id,COALESCE(sum(greatest(0,b.on_hand-b.safety_stock-COALESCE(r.qty,0))),0)::int AS available
  FROM inventory_balance b LEFT JOIN(SELECT variant_id,warehouse_id,sum(quantity)::int qty FROM reservations WHERE status='active' AND expires_at>now() GROUP BY variant_id,warehouse_id)r USING(variant_id,warehouse_id)
  WHERE b.variant_id=ANY($1::text[]) AND b.warehouse_id='main' GROUP BY b.variant_id`,[ids],connection);
 const map=new Map(balances.map(row=>[row.variant_id,Number(row.available)]));
 for(const id of ids){const tracked=await trackedAvailable(id,'main',connection);if(tracked!==null)map.set(id,tracked);}
 return components.length?Math.min(...components.map(c=>Math.floor((map.get(c.component_variant_id)??0)/c.quantity))):map.get(variantId)??0;
}
type RawVariant={id:string;sku:string;name:string;nameEn:string;priceMinor:number;currency:Currency;displayPriceMinor:number|null;color?:string|null;size?:string|null;available?:number}&Parameters<typeof publicVariantTechnical>[0];
type RawProduct={id:string;slug:string;name:string;name_en:string;description:string;description_en:string;category:string;brand:string;image:string;material:string;status:string;warnings:string;care:string;manufacturer:string|null;fixture:boolean;origin?:string|null;attributes?:unknown;contact_profile?:unknown;translations?:{en?:{warnings?:string;care?:string;warranty?:string}};seo?:Partial<Record<Locale,{alt?:string}>>;localized_slugs:Partial<Record<Locale,string>>|null;variants:RawVariant[]};
const supportedCurrencies:Currency[]=["TRY","EUR","USD","GBP"];
function validCurrency(currency:Currency){requireCondition(supportedCurrencies.includes(currency),"INVALID_CURRENCY","Bu para birimi desteklenmiyor.");return currency;}
async function mapProduct(row:RawProduct,locale:Locale,currency:Currency):Promise<Product>{
 const variants=[];
 for(const variant of row.variants)variants.push({id:variant.id,sku:variant.sku,name:variant.name,nameEn:variant.nameEn,priceMinor:Number(variant.priceMinor),currency:variant.currency,displayPriceMinor:variant.displayPriceMinor===null?null:Number(variant.displayPriceMinor),displayCurrency:currency,available:variant.available??await variantAvailability(variant.id),color:variant.color??undefined,size:variant.size??undefined,...publicVariantTechnical(variant)});
 return {id:row.id,slug:row.slug,localizedSlugs:{tr:row.localized_slugs?.tr??row.slug,en:row.localized_slugs?.en??row.slug},name:row.name,nameEn:row.name_en,description:row.description,descriptionEn:row.description_en,category:row.category,brand:row.brand,image:row.image,imageAlt:row.seo?.[locale]?.alt?.trim()||(locale==="en"?row.name_en:row.name),material:row.material,status:row.status,variants,warnings:row.warnings,care:row.care,warningsEn:row.translations?.en?.warnings??"",careEn:row.translations?.en?.care??"",manufacturer:row.manufacturer,fixture:row.fixture,...publicProductTechnical(row)};
}
const productColumns=`p.*,(SELECT jsonb_build_object('reviewed',cp.reviewed,'manufacturerAddress',cp.manufacturer_address,'manufacturerEmail',cp.manufacturer_email,'responsibleName',cp.responsible_name,'responsibleAddress',cp.responsible_address,'responsibleEmail',cp.responsible_email,'responsibleCountry',cp.responsible_country) FROM product_contact_profiles cp WHERE cp.product_id=p.id AND cp.reviewed=true AND cp.reviewed_by IS NOT NULL) contact_profile,(SELECT jsonb_object_agg(pr.locale,pr.slug) FROM product_routes pr WHERE pr.product_id=p.id) localized_slugs,
 jsonb_agg(jsonb_build_object('id',v.id,'sku',v.sku,'name',v.name,'nameEn',v.name_en,'priceMinor',v.price_minor,'currency',v.currency,'displayPriceMinor',vp.amount_minor,'color',v.color,'size',v.size,'barcode',v.barcode,'weightGrams',v.weight_grams,'packageDimensions',v.package_dimensions,'batteryType',v.battery_type,'batteryCapacityMah',v.battery_capacity_mah,'measurements',v.measurements,'ingredients',v.ingredients,'hygieneSealed',v.hygiene_sealed,'liquid',v.liquid) ORDER BY v.created_at,v.id) variants`;
const currentPriceJoin="LEFT JOIN variant_prices vp ON vp.variant_id=v.id AND vp.currency=$1 AND vp.amount_minor>0 AND vp.valid_from<=now() AND(vp.valid_until IS NULL OR vp.valid_until>now())";
const filterText=(max:number)=>z.string().trim().min(1).max(max).refine(value=>[...value].every(character=>character.charCodeAt(0)>=32&&character.charCodeAt(0)!==127));
const catalogFilterSchema=z.object({
 q:filterText(120).optional(),category:filterText(100).optional(),material:filterText(200).optional(),brand:filterText(200).optional(),size:filterText(100).optional(),color:filterText(100).optional(),power:filterText(200).optional(),
 min:z.number().int().min(0).max(9e12).optional(),max:z.number().int().min(0).max(9e12).optional(),available:z.boolean().optional(),
 features:z.array(z.enum(['liquid','hygiene-sealed'])).min(1).max(2).refine(values=>new Set(values).size===values.length).optional(),
 sort:z.enum(['newest','price_asc','price_desc','price-asc','price-desc','name']).default('newest').transform(value=>value.replace('-','_')),
 page:z.number().int().min(1).max(100000).default(1),locale:z.enum(['tr','en']).default('tr'),currency:z.enum(['TRY','EUR','USD','GBP']).default('TRY')
}).strict().refine(value=>value.min===undefined||value.max===undefined||value.min<=value.max);
/** Filtre nesnesi doğrudan sunucu çağrılarında da aynı doğrulamadan geçer. */
export function validateCatalogFilter(input:unknown):CatalogFilter & {page:number;locale:Locale;currency:Currency;sort:string}{
 const result=catalogFilterSchema.safeParse(input);requireCondition(result.success,'INVALID_CATALOG_FILTER','Filtre seçeneklerini ve fiyat aralığını kontrol edin.');return result.data;
}
export function parseCatalogQuery(params:URLSearchParams,defaults:Pick<CatalogFilter,'locale'|'currency'>={},detail=false){
 const input:Record<string,unknown>={...defaults};const allowed:readonly string[]=detail?['locale','currency']:catalogQueryKeys;
 for(const key of new Set(params.keys())){
  requireCondition(allowed.includes(key),'INVALID_CATALOG_FILTER','Desteklenmeyen filtre alanı.');const values=params.getAll(key);
  if(key==='features'){input.features=values;continue;}
  requireCondition(values.length===1,'INVALID_CATALOG_FILTER','Bir filtre alanı birden fazla kez gönderilemez.');const value=values[0];
  if(['min','max','page'].includes(key)){requireCondition(/^\d+$/.test(value),'INVALID_CATALOG_FILTER','Sayfa ve fiyat değerleri geçersiz.');input[key]=Number(value);}
  else if(key==='available'){requireCondition(value==='0'||value==='1','INVALID_CATALOG_FILTER','Stok filtresi geçersiz.');input.available=value==='1';}
  else input[key]=value;
 }
 return validateCatalogFilter(input);
}
// Yalnız okuma: ödeme/rezervasyon kilitlerini değiştirmez. lots.trackedAvailable ve
// variantAvailability ile aynı güvenlik payı, aktif rezervasyon, lot ve set semantiği.
const catalogAvailability=`held AS(SELECT variant_id,warehouse_id,sum(quantity)::int qty FROM reservations WHERE status='active' AND expires_at>now() GROUP BY variant_id,warehouse_id),
 ordinary_stock AS(SELECT b.variant_id,sum(greatest(0,b.on_hand-b.safety_stock-coalesce(h.qty,0)))::int available FROM inventory_balance b LEFT JOIN held h USING(variant_id,warehouse_id) WHERE b.warehouse_id='main' GROUP BY b.variant_id),
 lot_held AS(SELECT rl.lot_id,r.warehouse_id,sum(rl.quantity)::int qty FROM reservation_lots rl JOIN reservations r ON r.id=rl.reservation_id WHERE r.status='active' AND r.expires_at>now() GROUP BY rl.lot_id,r.warehouse_id),
 lot_stock AS(SELECT l.variant_id,sum(greatest(0,b.on_hand-coalesce(h.qty,0)))::int available FROM inventory_lot_balances b JOIN inventory_lots l ON l.id=b.lot_id LEFT JOIN lot_held h ON h.lot_id=l.id AND h.warehouse_id=b.warehouse_id WHERE b.warehouse_id='main' AND l.quarantined=false AND l.recall_reference IS NULL AND(l.expires_at IS NULL OR l.expires_at>(now() AT TIME ZONE 'Europe/Istanbul')::date) GROUP BY l.variant_id),
 component_stock AS(SELECT v.id,CASE WHEN v.lot_tracking THEN greatest(0,least(coalesce(l.available,0),coalesce(b.on_hand,0)-coalesce(h.qty,0))-coalesce(b.safety_stock,0)) ELSE coalesce(o.available,0) END::int available FROM variants v LEFT JOIN ordinary_stock o ON o.variant_id=v.id LEFT JOIN lot_stock l ON l.variant_id=v.id LEFT JOIN inventory_balance b ON b.variant_id=v.id AND b.warehouse_id='main' LEFT JOIN held h ON h.variant_id=v.id AND h.warehouse_id='main'),
 catalog_stock AS(SELECT s.id,CASE WHEN count(bc.component_variant_id)>0 THEN min(floor(coalesce(c.available,0)::numeric/bc.quantity))::int ELSE s.available END available FROM component_stock s LEFT JOIN bundle_components bc ON bc.bundle_variant_id=s.id LEFT JOIN component_stock c ON c.id=bc.component_variant_id GROUP BY s.id,s.available)`;
export async function searchCatalog(input:CatalogFilter={}):Promise<CatalogResult>{
 const filter=validateCatalogFilter(input),{currency,locale,page}=filter,values:unknown[]=[currency];
 const base=["p.status='published'","v.active=true","c.active=true"];
 const selected:string[]=[];const add=(target:string[],expression:string,value:unknown)=>{values.push(value);target.push(expression.replace('?',`$${values.length}`));};
 if(!localFixturesAllowed())base.push('p.fixture=false');
 if(locale==='en')base.push('length(trim(p.name_en))>0 AND length(trim(p.description_en))>0');
 if(filter.q)add(base,`${searchSql} ILIKE ? ESCAPE '\\'`,`%${normalizeSearch(filter.q).replace(/[\\%_]/g,'\\$&')}%`);
 if(filter.available)base.push('a.available>0');
 for(const [key,operator]of[['min','>='],['max','<=']]as const)if(filter[key]!==undefined)add(base,`vp.amount_minor${operator}?`,filter[key]);
 for(const key of ['category','material','brand','size','color']as const)if(filter[key])add(selected,`${key}=?`,filter[key]);
 if(filter.power)add(selected,'battery_type=?',filter.power);
 if(filter.features?.includes('liquid'))selected.push('liquid=true');if(filter.features?.includes('hygiene-sealed'))selected.push('hygiene_sealed=true');
 const order=filter.sort==='price_asc'?'m.price ASC NULLS LAST,p.id':filter.sort==='price_desc'?'m.price DESC NULLS LAST,p.id':filter.sort==='name'?(locale==='en'?'p.name_en COLLATE "en-x-icu" ASC,p.id':'p.name COLLATE "tr-x-icu" ASC,p.id'):'p.created_at DESC,p.id';
 values.push(24,(page-1)*24);const limit=`$${values.length-1}`,offset=`$${values.length}`;
 const facet=(column:string)=>`coalesce((SELECT jsonb_agg(jsonb_build_object('value',f.value,'count',f.n) ORDER BY f.value COLLATE "${locale==='tr'?'tr':'en'}-x-icu") FROM(SELECT ${column} value,count(DISTINCT product_id)::int n FROM catalog_scope WHERE length(trim(coalesce(${column},'')))>0 GROUP BY ${column})f),'[]'::jsonb)`;
 const columns=productColumns.replace("'id',v.id,","'available',matched.available,'id',v.id,");
 const [result]=await query<{products:RawProduct[];total:number;facets:CatalogResult['facets']}>(`WITH ${catalogAvailability},
 catalog_scope AS(SELECT p.id product_id,p.category,c.name category_name,c.name_en category_name_en,p.brand,p.material,v.id variant_id,v.size,v.color,v.battery_type,v.liquid,v.hygiene_sealed,vp.amount_minor,a.available FROM products p JOIN categories c ON c.slug=p.category JOIN variants v ON v.product_id=p.id ${currentPriceJoin} JOIN catalog_stock a ON a.id=v.id WHERE ${base.join(' AND ')}),
 matched AS(SELECT * FROM catalog_scope WHERE ${selected.length?selected.join(' AND '):'true'}),
 matched_products AS(SELECT product_id,min(amount_minor) price FROM matched GROUP BY product_id),
 selected_products AS(SELECT p.id,row_number()OVER(ORDER BY ${order}) position FROM matched_products m JOIN products p ON p.id=m.product_id ORDER BY ${order} LIMIT ${limit} OFFSET ${offset}),
 result_products AS(SELECT s.position,${columns} FROM selected_products s JOIN products p ON p.id=s.id JOIN matched ON matched.product_id=p.id JOIN variants v ON v.id=matched.variant_id ${currentPriceJoin} GROUP BY p.id,s.position)
 SELECT coalesce((SELECT jsonb_agg(to_jsonb(r)-'position' ORDER BY position) FROM result_products r),'[]'::jsonb) products,
 (SELECT count(*)::int FROM matched_products) total,
 jsonb_build_object('categories',coalesce((SELECT jsonb_agg(jsonb_build_object('value',f.category,'label',f.label,'count',f.n) ORDER BY f.label COLLATE "${locale==='tr'?'tr':'en'}-x-icu") FROM(SELECT category,${locale==='en'?'category_name_en':'category_name'} label,count(DISTINCT product_id)::int n FROM catalog_scope GROUP BY category,${locale==='en'?'category_name_en':'category_name'})f),'[]'::jsonb),
 'brands',${facet('brand')},'materials',${facet('material')},'sizes',${facet('size')},'colors',${facet('color')},'power',${facet('battery_type')},
 'features',coalesce((SELECT jsonb_agg(jsonb_build_object('value',f.value,'count',f.n) ORDER BY f.value) FROM(SELECT 'liquid' value,count(DISTINCT product_id)::int n FROM catalog_scope WHERE liquid=true HAVING count(*)>0 UNION ALL SELECT 'hygiene-sealed',count(DISTINCT product_id)::int FROM catalog_scope WHERE hygiene_sealed=true HAVING count(*)>0)f),'[]'::jsonb)) facets`,values);
 return {products:await Promise.all(result.products.map(row=>mapProduct(row,locale,currency))),facets:result.facets,total:result.total,page,pageSize:24};
}
export async function listProducts(filter:CatalogFilter={}):Promise<Product[]> {return (await searchCatalog(filter)).products;}
export async function getProduct(slug:string,locale:Locale="tr",currency:Currency="TRY"):Promise<Product|null> {
 validCurrency(currency);
 const found=await query<{id:string}>(`SELECT p.id FROM products p JOIN categories c ON c.slug=p.category AND c.active=true WHERE p.status='published' AND($3=true OR p.fixture=false) AND($2<>'en' OR(length(trim(p.name_en))>0 AND length(trim(p.description_en))>0)) AND(p.slug=$1 OR EXISTS(SELECT 1 FROM product_routes r WHERE r.product_id=p.id AND r.locale=$2 AND r.slug=$1)) ORDER BY CASE WHEN EXISTS(SELECT 1 FROM product_routes r WHERE r.product_id=p.id AND r.locale=$2 AND r.slug=$1) THEN 0 ELSE 1 END,p.id LIMIT 1`,[slug,locale,localFixturesAllowed()]);
 if(!found.length)return null;
 const rows=await query<RawProduct>(`SELECT ${productColumns} FROM products p JOIN variants v ON v.product_id=p.id AND v.active=true ${currentPriceJoin} WHERE p.id=$2 GROUP BY p.id`,[currency,found[0].id]);
 return rows.length?mapProduct(rows[0],locale,currency):null;
}
export function validateCartToken(token:string) {requireCondition(typeof token==="string"&&/^[A-Za-z0-9_-]{32,128}$/.test(token),"INVALID_CART","Sepet anahtarı geçersiz.",401);}
export async function findOrCreateCart(token:string,connection?:Connection) {
 validateCartToken(token);
 const rows=await query("INSERT INTO carts(token_hash) VALUES($1) ON CONFLICT(token_hash) DO UPDATE SET token_hash=excluded.token_hash RETURNING *",[tokenHash(token)],connection);
 return rows[0];
}
/** Bootstrap never reads owner or item data; authorization belongs to the later snapshot/lock. */
export async function ensureCartExists(token:string){
 validateCartToken(token);await query('INSERT INTO carts(token_hash) VALUES($1) ON CONFLICT(token_hash) DO NOTHING',[tokenHash(token)]);
}
export function assertCartOwner(cart:Record<string,unknown>|undefined,callerUserId:string|null){
 requireCondition(cart&&(cart.user_id===null||cart.user_id===callerUserId),'CART_NOT_FOUND','Sepet bulunamadı. Sepetinizi yenileyin.',404);
}
/** All item writers and checkout retain the same row lock used by member-cart merging. */
export async function lockCallerCart(token:string,callerUserId:string|null,connection:Connection){
 const created=await findOrCreateCart(token,connection),[cart]=await query('SELECT * FROM carts WHERE id=$1 FOR UPDATE',[created.id],connection);assertCartOwner(cart,callerUserId);return cart;
}
async function projectCart(cart:{id:string;currency:string},currency:Currency,connection:Connection):Promise<Cart>{
 const rows=await query("SELECT ci.variant_id,ci.quantity,v.name variant_name,v.name_en variant_name_en,v.price_minor,v.currency,p.name product_name,p.name_en product_name_en,p.image,vp.amount_minor display_price_minor FROM cart_items ci JOIN variants v ON v.id=ci.variant_id JOIN products p ON p.id=v.product_id LEFT JOIN variant_prices vp ON vp.variant_id=v.id AND vp.currency=$3 AND vp.amount_minor>0 AND vp.valid_from<=now() AND(vp.valid_until IS NULL OR vp.valid_until>now()) WHERE ci.cart_id=$1 AND($2=true OR p.fixture=false) ORDER BY p.name,v.name",[cart.id,localFixturesAllowed(),currency],connection);
 const items=[];for(const row of rows)items.push({variantId:row.variant_id,quantity:row.quantity,productName:row.product_name,productNameEn:row.product_name_en,variantName:row.variant_name,variantNameEn:row.variant_name_en,priceMinor:Number(row.price_minor),displayPriceMinor:row.display_price_minor===null?null:Number(row.display_price_minor),image:row.image,available:await variantAvailability(row.variant_id,connection)});
 const canonical=items.reduce((sum,item)=>sum+BigInt(item.quantity)*BigInt(item.priceMinor),0n);requireCondition(canonical<=BigInt(Number.MAX_SAFE_INTEGER),"INVALID_MONEY","Sepet tutarı izin verilen sınırı aşıyor.");
 const pricesComplete=items.every(item=>item.displayPriceMinor!==null);const displayTotal=pricesComplete?items.reduce((sum,item)=>sum+BigInt(item.quantity)*BigInt(item.displayPriceMinor!),0n):null;
 requireCondition(displayTotal===null||displayTotal<=BigInt(Number.MAX_SAFE_INTEGER),"INVALID_MONEY","Sepet tutarı izin verilen sınırı aşıyor.");
 return {id:cart.id,items,subtotalMinor:Number(canonical),currency:cart.currency as Currency,displayCurrency:currency,displaySubtotalMinor:displayTotal===null?null:Number(displayTotal),pricesComplete};
}
export async function getCart(token:string,currency:Currency="TRY",callerUserId:string|null=null):Promise<Cart> {
 validCurrency(currency);await ensureCartExists(token);const connection=await pool.connect();
 try{await connection.query('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY');const [cart]=await query('SELECT id,user_id,currency FROM carts WHERE token_hash=$1',[tokenHash(token)],connection);assertCartOwner(cart,callerUserId);const result=await projectCart(cart as {id:string;currency:string},currency,connection);await connection.query('COMMIT');return result;}
 catch(error){await connection.query('ROLLBACK');throw error;}finally{connection.release();}
}
export async function setCartItem(token:string,variantId:string,quantity:number,callerUserId:string|null=null):Promise<Cart> {
 requireCondition(Number.isInteger(quantity)&&quantity>=0&&quantity<=99,"INVALID_QUANTITY","Adet 0 ile 99 arasında olmalıdır.");
 return transaction(async connection=>{
 const cart=await lockCallerCart(token,callerUserId,connection);
 if(quantity===0){await query("DELETE FROM cart_items WHERE cart_id=$1 AND variant_id=$2",[cart.id,variantId],connection);return projectCart(cart as {id:string;currency:string},'TRY',connection);}
 const rows=await query("SELECT v.id FROM variants v JOIN products p ON p.id=v.product_id WHERE v.id=$1 AND v.active=true AND p.status='published' AND($2=true OR p.fixture=false)",[variantId,localFixturesAllowed()],connection);
 requireCondition(rows.length,"PRODUCT_UNAVAILABLE","Ürün satışa açık değil.",409);
 requireCondition(await variantAvailability(variantId,connection)>=quantity,"INSUFFICIENT_STOCK","İstenen adet stokta yok.",409);
 await query("INSERT INTO cart_items(cart_id,variant_id,quantity) VALUES($1,$2,$3) ON CONFLICT(cart_id,variant_id) DO UPDATE SET quantity=excluded.quantity",[cart.id,variantId,quantity],connection);
 await query("UPDATE carts SET updated_at=now() WHERE id=$1",[cart.id],connection);
 return projectCart(cart as {id:string;currency:string},'TRY',connection);
 });
}
