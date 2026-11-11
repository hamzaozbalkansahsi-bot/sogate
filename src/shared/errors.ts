/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/shared/errors.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
const english:Record<string,string>={
 CHECKOUT_QUOTE_CHANGED:'Prices or order conditions have changed. Review the refreshed summary and continue again.',CHECKOUT_QUOTE_EXPIRED:'Your order summary has expired. Refresh it before continuing.',CHECKOUT_QUOTE_INVALID:'Your order summary could not be verified. Refresh it before continuing.',CHECKOUT_QUOTE_REQUIRED:'Refresh your order summary before continuing.',QUOTE_RATE_LIMIT:'Too many order summary requests. Please try again in one minute.',
 ADDRESS_PROFILE_REQUIRED:'Delivery address requirements are not available for this country yet.',ADDRESS_PROFILE_INVALID:'Review the address field configuration.',ADDRESS_INVALID:'Review the address fields required for this delivery country.',
 EMPTY_CART:'Add a product to your bag before continuing.',INVALID_CHECKOUT:'Review the address and required acknowledgements.',
 COUNTRY_NOT_APPROVED:'Sales to this delivery country are not available.',SHIPPING_NOT_CONFIGURED:'Delivery or the collection currency is not configured for this country.',
 PRODUCT_TAX_NOT_CONFIGURED:'Pricing is unavailable for these products and delivery country. Please review your delivery preference.',SHIPPING_TAX_NOT_CONFIGURED:'Delivery pricing is unavailable for this country. Please review your delivery preference.',PRICE_NOT_CONFIGURED:'A price is unavailable in the payment currency. Please review your shopping preferences.',
 PRODUCT_UNAVAILABLE:'A product in your bag is no longer available.',PRODUCT_NOT_ELIGIBLE:'A product cannot be delivered to the selected country.',
 INSUFFICIENT_STOCK:'The requested quantity is no longer available. Review your bag.',STOCK_CONFLICT:'The last available item was reserved by another order. Review your bag.',
 PAYMENT_ALREADY_PENDING:'A payment is already in progress for this bag. Continue using your private order link.',
 IDEMPOTENCY_CONFLICT:'This payment attempt was already used with different details.',LIVE_SALES_CLOSED:'Orders are currently unavailable.',
 LEGAL_DOCUMENTS_REQUIRED:'The required sales information is not yet available.',INVALID_COUPON:'This promotion code cannot be applied.',COUPON_INVALID:'This promotion code is no longer valid.',COUPON_MINIMUM:'Your bag does not meet the minimum amount for this promotion.',COUPON_MARGIN:'This promotion cannot be applied to the selected products.',COUPON_LIMIT:'This promotion has reached its usage limit.',
 MFA_REQUIRED:'Verify your session with two-step verification.',FORBIDDEN:'You do not have permission for this action.',
 RETURN_NOT_ALLOWED:'A return request cannot be opened for this order at this stage.',RETURN_QUANTITY:'The return quantity exceeds the remaining purchased quantity.',
 CHECKOUT_RATE_LIMIT:'Too many payment attempts. Please try again in one minute.',INVALID_CART:'Your bag could not be verified. Please open a new bag.',
 };
export function customerErrorMessage(code:string|undefined,status:number,original:string|undefined,locale:'tr'|'en'){
 if(locale==='tr')return status<500?original??'Alanları kontrol edin.':'İşlem şu anda tamamlanamadı. Lütfen yeniden deneyin.';
 return english[code??'']??(status===401?'Please sign in to continue.':status===404?'The requested item could not be found.':status===429?'Too many requests. Please try again shortly.':status>=500?'This service is currently unavailable. Please try again later.':'The request could not be completed. Review the details and try again.');
}
