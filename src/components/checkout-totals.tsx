"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/checkout-totals.tsx
 * Açıklama   : Sunucunun güncel sipariş özetini, kuponu ve ödeme öncesi bütün tutarları gösterir.
 */
import {useEffect,useState} from 'react';
import Image from 'next/image';
import {api} from './api';
import {Busy,Status} from './ui';
import {useStore} from './store-context';
import {money,type Cart,type CheckoutQuote,type Currency,type Locale} from '@/shared/contracts';
export function useCheckoutQuote({country,currency,locale,ready}:{country:string;currency:Currency|null;locale:Locale;ready:boolean}){
 const [coupon,setCoupon]=useState(''),[revision,setRevision]=useState(0),[expiredToken,setExpiredToken]=useState('');
 const key=[country,currency,locale,coupon,revision,ready].join('|');
 const [record,setRecord]=useState<{key:string;quote?:CheckoutQuote;error?:string}|null>(null);
 useEffect(()=>{
  if(!ready||!currency)return;let active=true;const controller=new AbortController();
  api<CheckoutQuote>('/api/checkout/quote',{method:'POST',body:JSON.stringify({country,currency,locale,...(coupon?{couponCode:coupon}:{})}),signal:controller.signal}).then(quote=>{if(active)setRecord({key,quote});}).catch(error=>{if(active)setRecord({key,error:(error as Error).message});});
  return()=>{active=false;controller.abort();};
 },[country,currency,locale,coupon,revision,ready,key]);
 const quote=ready&&record?.key===key?record.quote:null;
 useEffect(()=>{if(!quote)return;const timer=setTimeout(()=>setExpiredToken(quote.quoteToken),Math.max(0,new Date(quote.expiresAt).getTime()-Date.now()));return()=>clearTimeout(timer);},[quote]);
 return {quote,error:ready&&record?.key===key?record.error:undefined,pending:ready&&record?.key!==key,expired:!!quote&&quote.quoteToken===expiredToken,coupon,refresh:()=>setRevision(value=>value+1),applyCoupon:(value:string)=>{setCoupon(value.trim());setRevision(revision=>revision+1);}};
}
export function CheckoutTotals({pricing,cart,country,disabled=false}:{disabled?:boolean;pricing:ReturnType<typeof useCheckoutQuote>;cart:Cart;country:string}){
 const {locale,t}=useStore(),en=locale==='en',[draft,setDraft]=useState(pricing.coupon),quote=pricing.quote;
 return <>
 <div className="form-stack"><label>{en?'Promotion code':'İndirim kodu'}<input disabled={disabled} value={draft} onChange={event=>setDraft(event.target.value)} maxLength={60} autoComplete="off" onKeyDown={event=>{if(event.key==='Enter'){event.preventDefault();pricing.applyCoupon(draft);}}}/></label><div className="summary-row"><button className="text-button" type="button" disabled={disabled||pricing.pending} onClick={()=>pricing.applyCoupon(draft)}>{en?'Apply code':'Kodu uygula'}</button>{pricing.coupon&&<button className="text-button" type="button" disabled={disabled||pricing.pending} onClick={()=>{setDraft('');pricing.applyCoupon('');}}>{en?'Remove code':'Kodu kaldır'}</button>}</div></div>
 <Status error={pricing.error}/>{pricing.pending?<Busy/>:quote?<>
 {quote.lines.map(line=>{const item=cart.items.find(item=>item.variantId===line.variantId);return <div className="summary-product" key={line.variantId}>{item&&<Image unoptimized src={item.image} alt="" width={55} height={65}/>}<div><strong>{line.name}</strong><span>{line.variantName}</span><span>{line.quantity} × {money(line.unitMinor,quote.currency,locale)}</span></div><span>{money(line.unitMinor*line.quantity,quote.currency,locale)}</span></div>;})}
 <dl aria-label={en?'Order amounts':'Sipariş tutarları'}>
 {[[t('subtotal'),quote.subtotalMinor],[t('discount'),-quote.discountMinor],[t('shipping'),quote.shippingMinor]].map(([label,value])=><div className="summary-row" key={String(label)}><dt>{label}</dt><dd>{money(Number(value),quote.currency,locale)}</dd></div>)}
 <div className="summary-row total-row"><dt><strong>{t('total')}</strong></dt><dd><strong>{money(quote.totalMinor,quote.currency,locale)}</strong></dd></div>
 <div className="summary-row small muted"><dt>{en?'Tax included in total':'Toplama dahil vergi'}</dt><dd>{money(quote.taxMinor,quote.currency,locale)}</dd></div>
 </dl><p className="small muted">{en?'Delivery term':'Teslimat koşulu'}: {quote.deliveryTerm}{country!=='TR'&&quote.deliveryTerm==='DAP'&&(en?'. Import taxes and customs charges are not included.':'. İthalat vergileri ve gümrük masrafları dahil değildir.')}</p>
 {pricing.expired&&<p className="notice" role="alert">{en?'Your order summary has expired. Refresh it before continuing.':'Sipariş özetinin geçerlilik süresi doldu. Devam etmek için güncelleyin.'}</p>}
 </>:null}
 <button className="text-button" type="button" disabled={disabled||pricing.pending} onClick={pricing.refresh}>{en?'Refresh order summary':'Sipariş özetini güncelle'}</button>
 </>;
}
