"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/error.tsx
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
export default function ErrorPage({reset}:{error:Error&{digest?:string};reset:()=>void}){return <div className="container section empty"><h1>Şu anda bu sayfayı açamıyoruz</h1><p>Lütfen biraz sonra yeniden deneyin.</p><button className="button" onClick={reset}>Yeniden dene</button></div>;}
