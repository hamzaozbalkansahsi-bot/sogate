/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/return-stock.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import {query,type Connection} from '../db';
import {requireCondition} from './rules';
import {lockPhysicalStockTargets} from './bundles';
interface ReturnRecord {id:string;order_id:string;variant_id:string;quantity:number;}
export interface ReturnStockLine {variantId:string;warehouseId:string;quantity:number;}
export async function receiveReturnStock(record:ReturnRecord,actorId:string,connection:Connection):Promise<ReturnStockLine[]> {
 const [line]=await query('SELECT quantity,snapshot FROM order_items WHERE order_id=$1 AND variant_id=$2',[record.order_id,record.variant_id],connection);
 requireCondition(line&&Number.isInteger(record.quantity)&&record.quantity>0&&record.quantity<=line.quantity,'RETURN_SNAPSHOT_REQUIRED','İadenin satış kaydı ve adedi doğrulanamadı.',409);
 const raw=line.snapshot?.bundleComponents;
 requireCondition(raw===undefined||raw===null||Array.isArray(raw),'RETURN_SNAPSHOT_INVALID','Satış bileşen kaydı doğrulanamadı.',409);
 const components:unknown[]=raw?.length?raw:[{variantId:record.variant_id,quantity:1}];
 requireCondition(components.length<=100,'RETURN_SNAPSHOT_INVALID','Satış bileşen kaydı doğrulanamadı.',409);
 const lines:ReturnStockLine[]=components.map(component=>{
  const c=component as {variantId?:unknown;quantity?:unknown};
  requireCondition(typeof c?.variantId==='string'&&c.variantId.length>0&&Number.isInteger(c.quantity)&&Number(c.quantity)>0,'RETURN_SNAPSHOT_INVALID','Satış bileşen kaydı doğrulanamadı.',409);
  const quantity=Number(c.quantity)*record.quantity;
  requireCondition(Number.isSafeInteger(quantity)&&quantity<=2147483647,'RETURN_QUANTITY','İade bileşen adedi geçersiz.',409);
  return {variantId:c.variantId,warehouseId:'main',quantity};
 }).sort((a,b)=>a.variantId.localeCompare(b.variantId));
 requireCondition(new Set(lines.map(l=>l.variantId)).size===lines.length,'RETURN_SNAPSHOT_INVALID','Tekrarlanan satış bileşeni doğrulanamadı.',409);
 await lockPhysicalStockTargets(lines.map(l=>l.variantId),connection);
 const balances=await query("SELECT variant_id FROM inventory_balance WHERE variant_id=ANY($1::text[]) AND warehouse_id='main' ORDER BY variant_id FOR UPDATE",[lines.map(l=>l.variantId)],connection);
 requireCondition(balances.length===lines.length,'RETURN_INVENTORY_REQUIRED','İade bileşenlerinin depo kayıtları doğrulanamadı.',409);
 for(const stock of lines) {
  await query('INSERT INTO return_stock_lines(return_id,variant_id,warehouse_id,quantity) VALUES($1,$2,$3,$4)',[record.id,stock.variantId,stock.warehouseId,stock.quantity],connection);
  await query('UPDATE inventory_balance SET quarantine=quarantine+$3 WHERE variant_id=$1 AND warehouse_id=$2',[stock.variantId,stock.warehouseId,stock.quantity],connection);
  await query("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,quarantine_quantity,reason,reference,actor_id) VALUES($1,$2,'return_received',0,$3,'İade kalite kontrolü bekliyor',$4,$5)",[stock.variantId,stock.warehouseId,stock.quantity,`return:${record.id}:${stock.variantId}`,actorId],connection);
 }
 return lines;
}
export async function getLockedReturnStockLines(returnId:string,connection:Connection):Promise<ReturnStockLine[]> {
 const rows=await query('SELECT variant_id,warehouse_id,quantity FROM return_stock_lines WHERE return_id=$1 ORDER BY variant_id,warehouse_id',[returnId],connection);
 requireCondition(rows.length,'RETURN_STOCK_LINES_REQUIRED','İadenin kabul edilmiş stok satırları doğrulanamadı.',409);
 await lockPhysicalStockTargets(rows.map(l=>l.variant_id),connection);
 const balances=await query("SELECT variant_id,warehouse_id FROM inventory_balance WHERE variant_id=ANY($1::text[]) AND warehouse_id='main' ORDER BY variant_id FOR UPDATE",[rows.map(l=>l.variant_id)],connection);
 requireCondition(balances.length===rows.length&&rows.every(l=>l.warehouse_id==='main'),'RETURN_INVENTORY_REQUIRED','İade depo satırları doğrulanamadı.',409);
 return rows.map(l=>({variantId:l.variant_id,warehouseId:l.warehouse_id,quantity:l.quantity}));
}
