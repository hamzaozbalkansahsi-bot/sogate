import {localeMetadata} from './locale-registry.js?v=storefront-recovery-20261112-r1';
import {countryLocale,visitorMarket} from './visitor-market.js?v=storefront-recovery-20261112-r1';
export const marketPreferenceKey='nodeno.currency.preference.v2';
const supported=new Set(['TRY','USD','EUR','GBP','RUB','AZN','KZT','AED','SAR','JPY','CHF','CAD']);
export function languagePreference(locale){locale=Object.hasOwn(localeMetadata,locale)?locale:'en';return {locale,currency:localeMetadata[locale].currency,source:'language'};}
export function countryPreference(country){if(!visitorMarket(country).country)throw new TypeError('invalid_market_country');return {locale:countryLocale(country),currency:({TR:'TRY',DE:'EUR',GB:'GBP',AZ:'AZN',KZ:'KZT',KG:'USD',RU:'RUB',AE:'AED',SA:'SAR',JP:'JPY',CH:'CHF',CA:'CAD'}[country]||'USD'),source:'country',country};}
export function restorePreference(locale,value){return value&&value.locale===locale&&supported.has(value.currency)&&['language','manual','country'].includes(value.source)?value:languagePreference(locale);}
