/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/reports.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import {query} from '../db';
export async function operationReports() {
 const sales=await query("SELECT currency,count(*)::int orders,coalesce(sum(total_minor),0) revenue_minor,coalesce(sum(tax_minor),0) tax_minor,coalesce(sum(discount_minor),0) discount_minor,coalesce(sum(cost_minor),0) cost_minor,coalesce(sum(fee_minor),0) fee_minor,coalesce(sum(advertising_minor),0) advertising_minor,coalesce(sum(return_provision_minor),0) return_provision_minor FROM orders WHERE payment_status IN('succeeded','partially_refunded','refunded') AND status<>'payment_exception' GROUP BY currency ORDER BY currency");
 const refunds=await query("SELECT p.currency,coalesce(sum(r.amount_minor),0) amount,coalesce(sum(r.tax_minor),0) tax,coalesce(sum(r.restocked_cost_minor),0) cost FROM refunds r JOIN payments p ON p.id=r.payment_id WHERE r.status='succeeded' GROUP BY p.currency");
 const shipments=await query('SELECT o.currency,coalesce(sum(s.cost_minor),0) amount FROM shipments s JOIN orders o ON o.id=s.order_id GROUP BY o.currency');
 const failures=await query("SELECT currency,count(*)::int n FROM payments WHERE status='failed' GROUP BY currency");
 const [stock]=await query('SELECT count(*)::int low FROM inventory_balance WHERE on_hand<=minimum_stock+safety_stock');
 const rows:Record<string,unknown>[]=[];
 for(const sale of sales) {
  const refund=refunds.find(r=>r.currency===sale.currency),shipping=shipments.find(r=>r.currency===sale.currency);
  const netRefund=Number(refund?.amount??0)-Number(refund?.tax??0);
  const contribution=Number(sale.revenue_minor)-Number(sale.tax_minor)-Number(sale.cost_minor)-Number(sale.fee_minor)-Number(sale.advertising_minor)-Number(sale.return_provision_minor)-Number(shipping?.amount??0)-netRefund+Number(refund?.cost??0);
  const row=(metric:string,value:number,unit='alt birim')=>({metric,value,unit,currency:sale.currency});
  rows.push(row('Ödenen sipariş',sale.orders,'adet'),row('Tahsilat toplamı',Number(sale.revenue_minor)),row('Ortalama sepet',sale.orders?Number((BigInt(sale.revenue_minor)+BigInt(Math.floor(sale.orders/2)))/BigInt(sale.orders)):0),row('Hesaplanan sipariş katkısı',contribution),row('Başarılı iade',Number(refund?.amount??0)),row('İade vergi payı',Number(refund?.tax??0)));
 }
 for(const failure of failures)rows.push({metric:'Başarısız ödeme',value:failure.n,unit:'adet',currency:failure.currency});
 rows.push({metric:'Azalan stok',value:stock.low,unit:'varyant',currency:null});
 return {rows,total:rows.length,page:1,definitions:{contribution:'Tahsilat eksi sipariş vergisi, ürün maliyeti, kayıtlı komisyon/reklam/iade karşılığı, kargo maliyeti ve vergi hariç iadeler; yeniden satışa alınan iadelerin snapshot maliyeti eklenir. Net işletme kârı değildir.',currency:'Her para birimi ayrı gösterilir. Kurla çevrilmez veya birbirine eklenmez.',advertising:'Yalnız kaydedilmiş sipariş reklam payıdır; gerçek muhasebe gideri olarak sunulmaz.'}};
}
