"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/store-context.tsx
 * Açıklama   : Erişilebilir müşteri veya yönetim etkileşimini sunar.
 */
import {createContext,useContext,useEffect,useState,useRef,useSyncExternalStore,useCallback,type ReactNode} from "react";
import type {Currency,Locale,Market,MarketCurrency,MarketsResponse} from "@/shared/contracts";
import {translations,type TextKey} from "@/shared/i18n";
import {localePath} from "@/shared/i18n";
import {usePathname} from "next/navigation";
type User={id:string;name:string;email:string;role:string;twoFactorEnabled:boolean;mfaVerified?:boolean};
function sameUser(one:User|null,two:User|null){return one===two||!!one&&!!two&&(['id','name','email','role','twoFactorEnabled','mfaVerified'] as const).every(key=>one[key]===two[key]);}
type Context={locale:Locale;currency:Currency;displayCurrency:Currency;country:string;market:Market|null;settlementCurrency:Currency|null;markets:Market[];displayCurrencies:MarketCurrency[];marketsLoading:boolean;marketsError:string;refreshMarkets:()=>void;user:User|null;cartCount:number;refreshCart:()=>void;refreshUser:()=>void;setPreferences:(locale:Locale,currency:Currency,country:string)=>void;t:(key:TextKey)=>string};
const StoreContext=createContext<Context|null>(null);
function subscribePreferences(notify:()=>void){for(const event of ["sexsogate:preferences","popstate"])window.addEventListener(event,notify);return()=>{for(const event of ["sexsogate:preferences","popstate"])window.removeEventListener(event,notify);};}
function cookiePreferences(){const cookie=(name:string)=>document.cookie.split("; ").find(x=>x.startsWith(name+"="))?.split("=")[1];const locale=/^\/en(?:\/|$)/.test(window.location.pathname)?"en":"tr";return [locale,cookie("sexsogate_currency")||"TRY",cookie("sexsogate_country")||"TR"].join("|");}
export function AppProvider({children,initialLocale="tr",initialCurrency="TRY",initialCountry="TR"}:{children:ReactNode;initialLocale?:Locale;initialCurrency?:Currency;initialCountry?:string}) {
 const pathname=usePathname();
 const preferences=useSyncExternalStore(subscribePreferences,cookiePreferences,()=>`${initialLocale}|${initialCurrency}|${initialCountry}`);
 const [rawLocale,rawCurrency,country]=preferences.split("|");
 const locale:Locale=rawLocale==="en"?"en":"tr",currency:Currency=["TRY","EUR","USD","GBP"].includes(rawCurrency)?rawCurrency as Currency:"TRY";
 const [user,setUser]=useState<User|null>(null),[cartCount,setCartCount]=useState(0),[marketOptions,setMarketOptions]=useState<MarketsResponse|null>(null),[marketsError,setMarketsError]=useState("");
 const refreshMarkets=useCallback(()=>{fetch("/api/markets",{cache:"no-store",headers:{"Accept-Language":locale}}).then(async response=>{const data=await response.json();if(!response.ok)throw new Error(data.error);return data as MarketsResponse;}).then(data=>{setMarketOptions(data);setMarketsError("");}).catch(error=>setMarketsError(error.message));},[locale]);
 const markets=marketOptions?.markets??[],displayCurrencies=marketOptions?.currencies??[],market=markets.find(value=>value.countryCode===country)??null,settlementCurrency=market?.settlementCurrency??null;
 const sessionRequest=useRef<{generation:number;controller:AbortController|null}>({generation:0,controller:null}),cartRequest=useRef<{generation:number;controller:AbortController|null}>({generation:0,controller:null}),sessionOwner=useRef<string|null|undefined>(undefined);
 const refreshCart=useCallback(()=>{
  const state=cartRequest.current,generation=++state.generation;state.controller?.abort();const controller=new AbortController();state.controller=controller;
  fetch("/api/cart",{cache:"no-store",signal:controller.signal}).then(response=>response.ok?response.json():null).then(data=>{if(generation===state.generation&&!controller.signal.aborted&&data?.items)setCartCount(data.items.reduce((sum:number,item:{quantity:number})=>sum+item.quantity,0));}).catch(()=>{});
 },[]);
 const refreshUser=useCallback(()=>{
  const state=sessionRequest.current,generation=++state.generation;state.controller?.abort();const controller=new AbortController();state.controller=controller;
  fetch("/api/session",{cache:"no-store",signal:controller.signal}).then(response=>response.ok?response.json():null).then(data=>{
   if(generation!==state.generation||controller.signal.aborted)return;
   const next:User|null=data?.user??null,owner=next?.id??null;
   setUser(previous=>sameUser(previous,next)?previous:next);
   if(sessionOwner.current!==owner){sessionOwner.current=owner;cartRequest.current.generation++;cartRequest.current.controller?.abort();setCartCount(0);refreshCart();}
  }).catch(()=>{});
 },[refreshCart]);
 useEffect(()=>{
  refreshUser();const session=sessionRequest.current,cart=cartRequest.current;
  return()=>{session.generation++;session.controller?.abort();cart.generation++;cart.controller?.abort();};
 },[refreshUser]);
 useEffect(()=>{refreshMarkets();},[refreshMarkets]);
 useEffect(()=>{document.documentElement.lang=locale;document.documentElement.dir="ltr";},[locale]);
 function preferenceTarget(language:Locale){
  const current=new URL(window.location.href),currentLocale=/^\/en(?:\/|$)/.test(current.pathname)?"en":"tr";
  if(language!==currentLocale&&/^(?:\/en)?\/urun\/[^/]+\/?$/.test(current.pathname)){
   const fallback=localePath("/urunler",language);
   const alternateLanguage=language==="tr"?"tr-TR":"en";
   const alternate=document.querySelector<HTMLLinkElement>(`link[rel="alternate"][hreflang="${alternateLanguage}"]`)?.getAttribute("href");
   if(alternate){
    try{
     const target=new URL(alternate,current),productPath=language==="en"?/^\/en\/urun\/[a-z0-9]+(?:-[a-z0-9]+)*\/?$/:/^\/urun\/[a-z0-9]+(?:-[a-z0-9]+)*\/?$/;
     if(target.origin===current.origin&&!target.username&&!target.password&&productPath.test(target.pathname))return target.pathname+current.search+current.hash;
    }catch{/* An invalid alternate cannot change the navigation origin. */}
   }
   return fallback+current.search+current.hash;
  }
  const target=localePath(pathname+current.search+current.hash,language);
  return target.startsWith("/")?target:`/${target}`;
 }
 function setPreferences(l:Locale,c:Currency,co:string){const next=preferenceTarget(l);for(const [k,v] of [["locale",l],["currency",c],["country",co]])document.cookie=`sexsogate_${k}=${v}; Path=/; Max-Age=15552000; SameSite=Lax`;if(next!==window.location.pathname+window.location.search+window.location.hash)window.location.assign(next);else window.location.reload();}
 return <StoreContext.Provider value={{locale,currency,displayCurrency:currency,country,market,settlementCurrency,markets,displayCurrencies,marketsLoading:marketOptions===null&&!marketsError,marketsError,refreshMarkets,user,cartCount,refreshCart,refreshUser,setPreferences,t:key=>translations[locale][key]}}>{children}</StoreContext.Provider>;
}
export function useStore(){const context=useContext(StoreContext);if(!context)throw new Error("AppProvider missing");return context;}
