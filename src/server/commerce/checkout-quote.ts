/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/checkout-quote.ts
 * Açıklama   : Mevcut sepeti yazmasız snapshot içinde hesaplayıp özel toplam teklifi döndürür.
 */
import {pool,query} from '../db';
import type {CheckoutQuote,CheckoutQuoteInput} from '../../shared/contracts';
import {tokenHash,validateCartToken} from './catalog';
import {requireCondition} from './rules';
import {evaluateCheckoutPricing,parseQuoteInput,pricingQuoteBinding} from './checkout-pricing';
import {createQuoteToken} from './quote-token';
export async function quoteCheckout(token:string,untrustedInput:CheckoutQuoteInput,callerUserId:string|null=null):Promise<CheckoutQuote>{
 validateCartToken(token);const input=parseQuoteInput(untrustedInput),connection=await pool.connect();
 try{
  await connection.query('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY');
  const [cart]=await query('SELECT id,user_id FROM carts WHERE token_hash=$1',[tokenHash(token)],connection);requireCondition(cart&&(cart.user_id===null||cart.user_id===callerUserId),'EMPTY_CART','Sepetinize ürün ekleyin.',409);
  const pricing=await evaluateCheckoutPricing(cart.id,input,connection),signed=createQuoteToken(pricingQuoteBinding(cart.id,tokenHash(token),input,pricing));
  const result:CheckoutQuote={...signed,currency:input.currency,deliveryTerm:pricing.country.delivery_term,...pricing.totals,
   lines:pricing.items.map((item,index)=>{const line=pricing.productTaxes.lines[index];return {variantId:String(item.id),name:String(item.product_name),variantName:String(item.variant_display_name),quantity:Number(item.quantity),unitMinor:Number(item.price_minor),discountMinor:line.discountMinor,taxMinor:line.taxMinor,lineTotalMinor:line.grossMinor-line.discountMinor};})};
  await connection.query('COMMIT');return result;
 }catch(error){await connection.query('ROLLBACK');throw error;}finally{connection.release();}
}
