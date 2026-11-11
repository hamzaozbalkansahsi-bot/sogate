"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/checkout.tsx
 * Açıklama   : Sepet, ödeme ve güvenli sipariş ekranlarını sunar.
 */
import Image from "next/image";
import {useEffect,useRef,useState} from "react";
import Link from "./localized-link";
import {useRouter,useSearchParams} from "next/navigation";
import {ArrowRight,LockKeyhole,Minus,Plus,Check,Package,Trash2} from "lucide-react";
import {money,type Cart,type CheckoutResult,type OrderSummary} from "@/shared/contracts";
import {api,post,ApiError} from "./api";
import {CheckoutTotals,useCheckoutQuote} from "./checkout-totals";
import {localePath} from "@/shared/i18n";
import {useStore} from "./store-context";
import {Busy,Empty,PageHeading,Status} from "./ui";
import {AddressFields,useAddressProfile} from "./address-fields";
import type {SavedAddress} from "./address-book";

function cartProductName(item:Cart["items"][number],locale:"tr"|"en"){return locale==="en"&&item.productNameEn?item.productNameEn:item.productName;}
function cartVariantName(item:Cart["items"][number],locale:"tr"|"en"){return locale==="en"&&item.variantNameEn?item.variantNameEn:item.variantName;}

function SettlementNotice(){const {locale,currency,market}=useStore();return market?<p className="notice" role="note">{locale==="tr"?`Ürünleri ${currency} ile görüntülüyorsunuz. Seçtiğiniz teslimat ülkesi için ödeme ${market.settlementCurrency} olarak alınır. Diliniz, teslimat ülkeniz ve gösterim para biriminiz ayrı tercihlerdir.`:`Prices are displayed in ${currency}. For your selected delivery country, payment is collected in ${market.settlementCurrency}. Your language, delivery country and display currency are independent preferences.`}</p>:null;}
function missingPriceText(currency:string,locale:"tr"|"en"){return locale==="tr"?`Sepetinizdeki bir ürünün ${currency} fiyatı bulunmuyor. Alışveriş tercihlerinizi kontrol edin; fiyatı olmayan ürünle ödemeye devam edilemez.`:`A ${currency} price is unavailable for an item in your bag. Check your shopping preferences; checkout is unavailable while a required price is missing.`;}

export function CartPage(){const {user}=useStore();return <CartSession key={user?.id??"guest"}/>;}
function CartSession(){
 const {t,locale,currency,market,marketsLoading,marketsError,refreshCart}=useStore();
 const [record,setRecord]=useState<{key:string;cart:Cart}|null>(null),[revision,setRevision]=useState(0),[error,setError]=useState(""),[pending,setPending]=useState(false);
 const key=[currency,revision].join("|"),cart=record?.key===key?record.cart:null;
 useEffect(()=>{let active=true;api<Cart>(`/api/cart?currency=${currency}`).then(data=>{if(active){setRecord({key,cart:data});setError("");}}).catch(error=>{if(active)setError(error.message);});return()=>{active=false;};},[currency,revision,key]);
 async function update(id:string,quantity:number){setPending(true);try{await post("/api/cart",{variantId:id,quantity});setRevision(value=>value+1);refreshCart();setError("");}catch(e){setError((e as Error).message);}finally{setPending(false);}}
 const payable=!!market&&!marketsLoading&&!marketsError&&cart?.pricesComplete===true;
 return <div className="container section cart-page"><PageHeading title={t("cart")}/><Status error={error}/>{!cart?(error?<button className="button button-outline" onClick={()=>setRevision(value=>value+1)}>{t("retry")}</button>:<Busy/>):cart.items.length?<><SettlementNotice/>{marketsError&&<p className="notice" role="alert">{marketsError}</p>}{!marketsLoading&&!market&&<p className="notice" role="alert">{t("noCountry")}</p>}{!cart.pricesComplete&&<p className="notice" role="alert">{missingPriceText(currency,locale)}</p>}<div className="checkout-layout"><div className="cart-lines">{cart.items.map(item=><article className="cart-line" key={item.variantId}><Image unoptimized src={item.image} alt={cartProductName(item,locale)} width={128} height={150}/><div className="cart-line-info"><h2>{cartProductName(item,locale)}</h2><p className="muted">{cartVariantName(item,locale)}</p><p className="price">{typeof item.displayPriceMinor==="number"?money(item.displayPriceMinor,currency,locale):(locale==="tr"?`${currency} fiyatı bulunmuyor`:`Price unavailable in ${currency}`)}</p><div className="cart-line-controls"><div className="quantity-stepper"><button disabled={pending||item.quantity<=1} aria-label={locale==="tr"?"Adedi azalt":"Decrease quantity"} onClick={()=>update(item.variantId,item.quantity-1)}><Minus size={15}/></button><output aria-label={t("quantity")}>{item.quantity}</output><button disabled={pending||item.quantity>=item.available} aria-label={locale==="tr"?"Adedi artır":"Increase quantity"} onClick={()=>update(item.variantId,item.quantity+1)}><Plus size={15}/></button></div><button className="text-button" disabled={pending} onClick={()=>update(item.variantId,0)}><Trash2 size={15}/>{t("remove")}</button></div></div><strong className="cart-line-total">{typeof item.displayPriceMinor==="number"?money(item.displayPriceMinor*item.quantity,currency,locale):"—"}</strong></article>)}<Link href="/urunler" className="text-link">{t("continue")}<ArrowRight size={16}/></Link></div><aside className="order-summary"><h2>{t("summary")}</h2><div className="summary-row"><span>{t("subtotal")}</span><strong>{typeof cart.displaySubtotalMinor==="number"?money(cart.displaySubtotalMinor,currency,locale):"—"}</strong></div><p className="small muted">{t("taxIncluded")}</p>{payable?<Link className="button full" href="/odeme">{t("checkout")}<ArrowRight size={17}/></Link>:<button className="button full" disabled>{t("checkout")}<ArrowRight size={17}/></button>}<p className="secure-note"><LockKeyhole size={14}/>{t("safeSession")}</p></aside></div></>:<Empty title={t("emptyCart")} text={t("emptyCartText")} href="/urunler" label={t("discover")}/>}</div>;
}

export function Checkout(){const {user,country}=useStore();return <CheckoutSession key={(user?.id??"guest")+"|"+country}/>;}
function CheckoutSession(){
 const {t,locale,currency,country,market,settlementCurrency,marketsLoading,marketsError,user}=useStore(),router=useRouter();
 const active=useRef(true),paymentRequest=useRef<AbortController|null>(null);
 useEffect(()=>{active.current=true;return()=>{active.current=false;paymentRequest.current?.abort();};},[]);
 const [record,setRecord]=useState<{key:string;display:Cart;settlement:Cart|null}|null>(null),[revision,setRevision]=useState(0),[error,setError]=useState(""),[busy,setBusy]=useState(false),[idempotencyKey]=useState(()=>globalThis.crypto?.randomUUID?.()??"");
 const key=[currency,country,settlementCurrency,revision].join("|"),quote=record?.key===key?record:null,cart=quote?.settlement??quote?.display??null;
 useEffect(()=>{let active=true;async function load(){try{const display=await api<Cart>(`/api/cart?currency=${currency}`);const settlement=settlementCurrency===currency?display:settlementCurrency?await api<Cart>(`/api/cart?currency=${settlementCurrency}`):null;if(active){setRecord({key,display,settlement});setError("");}}catch(error){if(active)setError((error as Error).message);}}void load();return()=>{active=false;};},[currency,country,settlementCurrency,revision,key]);
 const {profile,loading:profileLoading,error:profileError}=useAddressProfile(country);
 const [savedAddresses,setSavedAddresses]=useState<SavedAddress[]>([]),[savedId,setSavedId]=useState("");
 useEffect(()=>{if(!user)return;let active=true;api<{addresses:SavedAddress[]}>("/api/addresses").then(data=>{if(active)setSavedAddresses(data.addresses.filter(address=>address.country===country));}).catch(()=>{});return()=>{active=false;};},[user,country]);
 const displayMissing=!!quote&&quote.display.pricesComplete!==true,settlementMissing=!!quote?.settlement&&quote.settlement.pricesComplete!==true;
 const priceReady=!!cart?.items.length&&!!profile&&!profileLoading&&!!market&&!!settlementCurrency&&!marketsLoading&&!marketsError&&!!quote?.settlement&&!displayMissing&&!settlementMissing;
 const pricing=useCheckoutQuote({country,currency:settlementCurrency,locale,ready:priceReady});
 const payable=priceReady&&!!pricing.quote&&!pricing.pending&&!pricing.expired;
 async function submit(event:React.FormEvent<HTMLFormElement>){
  event.preventDefault();if(busy||!idempotencyKey||!payable||!settlementCurrency||!pricing.quote)return;
  setBusy(true);setError("");const data=Object.fromEntries(new FormData(event.currentTarget)),controller=new AbortController(),path=window.location.pathname;paymentRequest.current=controller;
  try{
   const result=await post<CheckoutResult>("/api/checkout",{...data,country,currency:settlementCurrency,locale,idempotencyKey,quoteToken:pricing.quote.quoteToken,...(pricing.coupon?{couponCode:pricing.coupon}:{}),privacyAccepted:data.privacyAccepted==="on",termsAccepted:data.termsAccepted==="on"},{signal:controller.signal});
   if(!active.current||paymentRequest.current!==controller||controller.signal.aborted||window.location.pathname!==path)return;
   router.push(localePath(result.paymentUrl,locale));
  }catch(error){
   if(!active.current||paymentRequest.current!==controller||controller.signal.aborted||window.location.pathname!==path)return;
   setError((error as Error).message);setBusy(false);if(error instanceof ApiError&&['CHECKOUT_QUOTE_CHANGED','CHECKOUT_QUOTE_EXPIRED','CHECKOUT_QUOTE_INVALID','CHECKOUT_QUOTE_REQUIRED'].includes(error.code??''))pricing.refresh();
  }finally{if(paymentRequest.current===controller)paymentRequest.current=null;}
 }

 const summaryCurrency=settlementCurrency??currency;
 return <div className="container section"><div className="checkout-steps"><span className="active"><b>1</b>{t("stepAddress")}</span><span><b>2</b>{t("stepPayment")}</span><span><b>3</b>{t("stepDone")}</span></div><PageHeading title={t("checkoutTitle")} description={t("checkoutSub")}/>{!quote||!cart?<><Status error={error}/>{error?<button className="button button-outline" onClick={()=>setRevision(value=>value+1)}>{t("retry")}</button>:<Busy/>}</>:cart.items.length===0?<Empty title={t("emptyCart")} href="/urunler" label={t("discover")}/>:<><SettlementNotice/>{marketsError&&<p className="notice" role="alert">{marketsError}</p>}{!marketsLoading&&!market&&<p className="notice" role="alert">{t("noCountry")}</p>}{displayMissing&&<p className="notice" role="alert">{missingPriceText(currency,locale)}</p>}{settlementMissing&&settlementCurrency!==currency&&<p className="notice" role="alert">{missingPriceText(summaryCurrency,locale)}</p>}<form className="checkout-layout" onSubmit={submit}><div className="checkout-fields"><h2>{t("stepAddress")}</h2>{savedAddresses.length>0&&<label>{locale==="tr"?"Kayıtlı adres":"Saved address"}<select value={savedId} onChange={event=>setSavedId(event.target.value)}><option value="">{locale==="tr"?"Yeni teslimat adresi":"New delivery address"}</option>{savedAddresses.map(address=><option key={address.id} value={address.id}>{address.label} · {address.city}</option>)}</select></label>}<div className="form-grid"><label>{t("email")}<input name="email" type="email" autoComplete="email" required defaultValue={user?.email}/></label><label>{t("country")}<input value={market?.name??country} readOnly/></label></div><Status error={profileError}/>{profileLoading?<Busy/>:profile&&<div className="form-grid" key={profile.version+"|"+savedId}><AddressFields profile={profile} values={savedAddresses.find(address=>address.id===savedId)??{fullName:user?.name??""}}/></div>}<div className="checkout-privacy"><LockKeyhole size={22}/><p>{locale==="tr"?"Sipariş bildirimlerinde ürün adları yer almaz. Ayrıntıları yalnız güvenli sipariş sayfanızdan görüntüleyin.":"Order notifications do not include product names. View details only on your secure order page."}</p></div><div className="checkout-consents"><label className="checkbox"><input type="checkbox" name="privacyAccepted" required/><span>{t("privacyConsent")} <Link href="/yasal/gizlilik" target="_blank">{locale==="tr"?"Aydınlatma metnini oku":"Read the privacy notice"}</Link></span></label><label className="checkbox"><input type="checkbox" name="termsAccepted" required/><span>{t("termsConsent")} <Link href="/yasal/mesafeli-satis" target="_blank">{locale==="tr"?"Satış koşullarını oku":"Read the sales terms"}</Link></span></label></div><Status error={error}/></div><aside className="order-summary"><h2>{t("summary")}</h2><p className="small muted">{locale==="tr"?`Tahsilat para birimi: ${summaryCurrency}`:`Payment currency: ${summaryCurrency}`}</p><CheckoutTotals pricing={pricing} cart={cart} country={country} disabled={busy}/><button className="button full" type="submit" disabled={busy||!payable}>{busy?t("loading"):t("continuePayment")}<ArrowRight size={17}/></button><p className="secure-note"><LockKeyhole size={14}/>{t("safeSession")}</p></aside></form></>}</div>;
}

export function TestPayment(){
 const {user}=useStore(),params=useSearchParams(),orderId=params.get("order")??"",token=params.get("token")??"";
 return <TestPaymentSession key={JSON.stringify([user?.id??null,orderId,token])} orderId={orderId} token={token}/>;
}
function TestPaymentSession({orderId,token}:{orderId:string;token:string}){
 const {t,locale}=useStore(),router=useRouter(),[order,setOrder]=useState<OrderSummary|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState("");
 const active=useRef(true),paymentRequest=useRef<AbortController|null>(null);
 useEffect(()=>{active.current=true;return()=>{active.current=false;paymentRequest.current?.abort();};},[]);
 useEffect(()=>{
  if(!orderId||!token)return;
  const controller=new AbortController(),screen=window.location.pathname+window.location.search;
  const current=()=>active.current&&!controller.signal.aborted&&window.location.pathname+window.location.search===screen;
  api<OrderSummary>(`/api/orders/${encodeURIComponent(orderId)}?token=${encodeURIComponent(token)}`,{signal:controller.signal}).then(data=>{if(current())setOrder(data);}).catch(error=>{if(current())setError((error as Error).message);});
  return()=>controller.abort();
 },[orderId,token]);
 async function pay(outcome:"succeeded"|"failed"){
  if(busy||!order||!orderId||!token||paymentRequest.current)return;
  setBusy(true);setError("");const controller=new AbortController(),screen=window.location.pathname+window.location.search;paymentRequest.current=controller;
  const current=()=>active.current&&paymentRequest.current===controller&&!controller.signal.aborted&&window.location.pathname+window.location.search===screen;
  try{
   const result=await post<{orderId:string;trackingToken:string}>("/api/test-payment",{orderId,token,outcome},{signal:controller.signal});
   if(!current())return;
   router.replace(localePath(`/siparis/${result.orderId}?token=${encodeURIComponent(result.trackingToken||token)}`,locale));
  }catch(error){if(current()){setError((error as Error).message);setBusy(false);}}
  finally{if(paymentRequest.current===controller)paymentRequest.current=null;}
 }
 return <div className="container narrow section"><div className="test-payment card"><span className="tag">SANDBOX</span><PageHeading title={t("testPayment")} description={t("testNotice")}/>{order&&<><p>{t("orderNumber")}: <strong>{order.number}</strong></p><p className="product-price">{money(order.totalMinor,order.currency,locale)}</p></>}<Status error={error}/><div className="form-stack"><button className="button" type="button" disabled={busy||!order} onClick={()=>pay("succeeded")}><Check size={18}/>{t("testSuccess")}</button><button className="button button-outline" disabled={busy||!order} onClick={()=>pay("failed")}>
 {t("testFailure")}</button><Link className="text-link" href="/sepet">{t("back")}</Link></div></div></div>;
}

export const statusText:Record<string,[string,string]>={awaiting_payment:["Ödeme bekleniyor","Awaiting payment"],confirmed:["Onaylandı","Confirmed"],partially_shipped:["Kısmen sevk edildi","Partially shipped"],shipped:["Sevk edildi","Shipped"],completed:["Tamamlandı","Completed"],cancelled:["İptal edildi","Cancelled"],payment_exception:["Ödeme incelemede","Payment under review"],pending:["Bekliyor","Pending"],succeeded:["Ödendi","Paid"],failed:["Başarısız","Failed"],partially_refunded:["Kısmen iade edildi","Partially refunded"],refunded:["İade edildi","Refunded"],unfulfilled:["Hazırlanıyor","Preparing"],delivered:["Teslim edildi","Delivered"],not_shipped:["Sevk bekliyor","Awaiting shipment"]};
export function translatedStatus(status:string,locale:"tr"|"en"){return statusText[status]?.[locale==="tr"?0:1]??(locale==="tr"?"İşlemde":"Processing");}

export function OrderPage({id}:{id:string}){const {t,locale,refreshCart}=useStore(),params=useSearchParams(),[order,setOrder]=useState<OrderSummary|null>(null),[error,setError]=useState(""),[message,setMessage]=useState(""),[showReturn,setShowReturn]=useState(false),[busy,setBusy]=useState(false);const token=params.get("token")??"";useEffect(()=>{api<OrderSummary>(`/api/orders/${encodeURIComponent(id)}${token?`?token=${encodeURIComponent(token)}`:""}`).then(setOrder).catch(e=>setError(e.message));refreshCart();},[id,token,refreshCart]);async function requestReturn(e:React.FormEvent<HTMLFormElement>){e.preventDefault();setBusy(true);try{const data=new FormData(e.currentTarget);await post("/api/returns",{orderId:id,token,variantId:String(data.get("variantId")),quantity:Number(data.get("quantity")),reason:String(data.get("reason")),sealIntact:data.get("sealIntact")==="on"});setMessage(t("returnSent"));setShowReturn(false);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}return <div className="container section"><Status error={error} message={message}/>{!order&&!error?<Busy/>:order&&<><div className="order-success"><span className="success-mark"><Check size={28}/></span><PageHeading title={order.paymentStatus==="succeeded"?t("orderReceived"):t("orderPending")} description={`${t("orderNumber")}: ${order.number}`}/><p className="small muted">{t("trackingPrivate")}</p></div><div className="checkout-layout"><div><div className="card"><a className="button button-outline" href={`/api/orders/${encodeURIComponent(id)}/document${token?`?token=${encodeURIComponent(token)}`:""}`} download>{locale==="tr"?"Sipariş ve sözleşme özeti (PDF)":"Order and agreement summary (PDF)"}</a><p className="small muted">{locale==="tr"?"Bu belge fatura yerine geçmez.":"This summary is not a tax invoice."}</p></div><div className="order-state-grid"><div><Package size={24}/><span>{t("orders")}</span><strong>{translatedStatus(order.status,locale)}</strong></div><div><LockKeyhole size={24}/><span>{t("payment")}</span><strong>{translatedStatus(order.paymentStatus,locale)}</strong></div></div><div className="card"><h2>{t("products")}</h2>{order.items.map((item,i)=><div className="summary-row" key={i}><div><strong>{item.name}</strong><p className="small muted">{item.sku} · {item.quantity} {t("quantity")}</p></div><strong>{money(item.unitMinor*item.quantity,order.currency,locale)}</strong></div>)}</div>{order.shipments.length>0&&<div className="card"><h2>{t("shipping")}</h2>{order.shipments.map((s,i)=><div key={i}><strong>{s.carrier}</strong><p>{s.trackingNumber}</p><p>{translatedStatus(s.status,locale)}</p></div>)}</div>}{["succeeded","partially_refunded"].includes(order.paymentStatus)&&<div className="card"><button className="button button-outline" onClick={()=>setShowReturn(!showReturn)}>{t("requestReturn")}</button>{showReturn&&<form className="form-stack" onSubmit={requestReturn}><label>{t("products")}<select name="variantId" required>{order.items.map((item,i)=><option value={(item as typeof item&{variantId:string}).variantId} key={i}>{item.name} · {item.quantity} {t("quantity")}</option>)}</select></label><label>{t("quantity")}<input name="quantity" type="number" min="1" max="99" defaultValue="1" required/></label><label className="checkbox"><input name="sealIntact" type="checkbox"/>{locale==="tr"?"Hijyen mührü açılmadı":"The hygiene seal is intact"}</label><label>{t("returnReason")}<textarea name="reason" required minLength={5} maxLength={1000}/></label><button className="button" disabled={busy}>{busy?t("loading"):t("sendRequest")}</button></form>}</div>}</div><aside className="order-summary"><h2>{t("summary")}</h2>{[[t("subtotal"),order.subtotalMinor],[t("discount"),-order.discountMinor],[t("shipping"),order.shippingMinor],[t("tax"),order.taxMinor]].map(([label,value])=><div className="summary-row" key={label}><span>{label}</span><span>{money(Number(value),order.currency,locale)}</span></div>)}<div className="summary-row total-row"><strong>{t("total")}</strong><strong>{money(order.totalMinor,order.currency,locale)}</strong></div><Link className="text-link" href="/urunler">{t("continue")}<ArrowRight size={16}/></Link></aside></div></>}</div>;}
