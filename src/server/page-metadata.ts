/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/page-metadata.ts
 * Açıklama   : Genel müşteri sayfalarında dile uygun başlık ve karşılıklı canonical bağlantıları üretir.
 */
import {headers} from 'next/headers';
import type {Metadata} from 'next';
export async function pageMetadata(path:string,trTitle:string,enTitle:string,trDescription:string,enDescription:string):Promise<Metadata>{
 const en=(await headers()).get('x-site-locale')==='en',english=path==='/'?'/en':`/en${path}`,canonical=en?english:path;
 const title=en?enTitle:trTitle,description=en?enDescription:trDescription;
 return {title,description,alternates:{canonical,languages:{'tr-TR':path,en:english,'x-default':path}},openGraph:{title,description,url:canonical,locale:en?'en_GB':'tr_TR',images:['/brand/share-preview.png']}};
}
