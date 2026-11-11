/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/layout.tsx
 * Açıklama   : Sayfa kabuğu, dil ve gezinme düzenini kurar.
 */
import type {Metadata} from 'next';
import localFont from 'next/font/local';
import {headers,cookies} from 'next/headers';
import type {Currency} from '@/shared/contracts';
import {AppProvider} from '@/components/store-context';
import './globals.css';
const display=localFont({src:'../../public/fonts/playfairdisplay-variable.woff2',variable:'--font-display',display:'swap',weight:'400 900'});
const body=localFont({src:'../../public/fonts/montserrat-variable.woff2',variable:'--font-body',display:'swap',weight:'100 900'});
const arabic=localFont({src:'../../public/fonts/notosansarabic-variable.woff2',variable:'--font-arabic',display:'swap',weight:'100 900',preload:false});
export const metadata:Metadata={metadataBase:new URL(process.env.APP_URL??'http://127.0.0.1:3000'),title:{default:'SEXSOGATE — Tutkunu Keşfet.',template:'%s | SEXSOGATE'},description:'Yakınlığa, kendine ve birlikte geçirdiğin zamana yer aç. SEXSOGATE koleksiyonlarını keşfet.',applicationName:'SEXSOGATE',icons:{icon:[{url:'/brand/favicon-16.png',sizes:'16x16',type:'image/png'},{url:'/brand/favicon-32.png',sizes:'32x32',type:'image/png'}]},openGraph:{siteName:'SEXSOGATE',locale:'tr_TR',images:[{url:'/brand/share-preview.png',width:1200,height:630}]},robots:process.env.APP_ENV==='production'?{index:true,follow:true}:{index:false,follow:false}};
export default async function RootLayout({children}:{children:React.ReactNode}){
 const locale=(await headers()).get('x-site-locale')==='en'?'en':'tr',saved=await cookies();
 const rawCurrency=saved.get('sexsogate_currency')?.value,rawCountry=saved.get('sexsogate_country')?.value;
 const currency:Currency=['TRY','EUR','USD','GBP'].includes(rawCurrency??'')?rawCurrency as Currency:'TRY';
 const country=/^[A-Z]{2}$/.test(rawCountry??'')?rawCountry!:'TR';
 return <html lang={locale} className={`${display.variable} ${body.variable} ${arabic.variable}`}><body><AppProvider initialLocale={locale} initialCurrency={currency} initialCountry={country}>{children}</AppProvider></body></html>;
}
