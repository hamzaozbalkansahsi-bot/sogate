/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/veri-basvurusu/page.tsx
 * Açıklama   : İndekslenmeyen ilgili kişi başvuru ve güvenli durum sayfasını sunar.
 */
import {Suspense} from 'react';
import {headers} from 'next/headers';
import {PrivacyRequest} from '@/components/privacy-request';
export const dynamic='force-dynamic';
export async function generateMetadata(){return {title:(await headers()).get('x-site-locale')==='en'?'Data privacy request':'Veri gizliliği başvurusu',robots:{index:false,follow:false}};}
export default function Page(){return <Suspense><PrivacyRequest/></Suspense>;}
