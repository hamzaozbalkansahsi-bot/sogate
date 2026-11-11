/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/markets.ts
 * Açıklama   : Onaylı teslimat ülkelerini ve gerçek fiyat listesi bulunabilirliğini sunar.
 */
import {query} from "./db";
import type {Currency,MarketsResponse} from "../shared/contracts";
const supported:Currency[]=["TRY","EUR","USD","GBP"];
export async function getMarkets():Promise<MarketsResponse>{
 const allowFixtures=["development","test"].includes(process.env.APP_ENV??"");
 const countries=await query("SELECT code,name,currency,delivery_term FROM country_rules WHERE enabled=true AND product_approved=true AND age_approved=true AND payment_approved=true AND shipping_approved=true AND tax_approved=true AND legal_approved=true AND shipping_minor IS NOT NULL AND currency=ANY($1::text[]) AND(fixture=false OR $2=true) AND EXISTS(SELECT 1 FROM country_address_profiles ap WHERE ap.country=country_rules.code AND ap.status='approved' AND ap.approved_by IS NOT NULL AND(ap.fixture=false OR $2=true)) ORDER BY CASE WHEN code='TR' THEN 0 ELSE 1 END,name",[supported,allowFixtures]);
 const prices=await query("SELECT DISTINCT vp.currency FROM variant_prices vp JOIN variants v ON v.id=vp.variant_id JOIN products p ON p.id=v.product_id JOIN categories c ON c.slug=p.category AND c.active=true WHERE v.active=true AND p.status='published' AND(p.fixture=false OR $1=true) AND vp.amount_minor>0 AND vp.valid_from<=now() AND(vp.valid_until IS NULL OR vp.valid_until>now())",[allowFixtures]);
 const available=new Set(prices.map(row=>String(row.currency)));
 return {markets:countries.map(row=>({countryCode:row.code,name:row.name,settlementCurrency:row.currency as Currency,deliveryTerm:row.delivery_term})),currencies:supported.map(currency=>({currency,available:available.has(currency)}))};
}
