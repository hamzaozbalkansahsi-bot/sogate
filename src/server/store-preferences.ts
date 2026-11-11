/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/store-preferences.ts
 * Açıklama   : İlk sunucu yanıtında dil ve gösterim para tercihini doğrulayarak okur.
 */
import {cookies,headers} from 'next/headers';
import type {Currency} from '../shared/contracts';
export async function storePreferences(){
 const locale=(await headers()).get('x-site-locale')==='en'?'en' as const:'tr' as const;
 const value=(await cookies()).get('sexsogate_currency')?.value;
 const currency:Currency=['TRY','EUR','USD','GBP'].includes(value??'')?value as Currency:'TRY';return {locale,currency};
}
