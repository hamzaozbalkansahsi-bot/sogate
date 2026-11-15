import {readFileSync} from 'node:fs';
const registry=JSON.parse(readFileSync(new URL('../data/store-locales.json',import.meta.url),'utf8'));
export const storeLocales=Object.freeze(Object.keys(registry.locales));
export function normalizeStoreLocale(value){return typeof value==='string'&&Object.hasOwn(registry.locales,value)?value:null;}
export function localeForCountry(country){return registry.targetCountries[country]||registry.additionalCountries[country]||null;}
export function localeCurrency(locale){const id=normalizeStoreLocale(locale);if(!id)throw new TypeError('unsupported_store_locale');return registry.locales[id].currency;}
export function isRtlLocale(locale){return registry.locales[normalizeStoreLocale(locale)]?.direction==='rtl';}
export const localeRegistry=Object.freeze(registry);
