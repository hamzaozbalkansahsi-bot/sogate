/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/shared/contracts.ts
 * Açıklama   : Modüller arasında paylaşılan veri sözleşmeleri.
 */
import {formatMinorAmount} from "./money";
export type Locale = "tr" | "en";
export type Currency = "TRY" | "EUR" | "USD" | "GBP";
export type Role = "admin" | "catalog" | "warehouse" | "support" | "finance" | "marketing" | "customer";
export interface Variant { id: string; sku: string; name: string; nameEn?: string; priceMinor: number; currency: Currency; displayPriceMinor?: number | null; displayCurrency?: Currency; available: number; color?: string; size?: string; barcode?:string;weightGrams?:number;packageDimensions?:{lengthCm:number;widthCm:number;heightCm:number};batteryType?:string;batteryCapacityMah?:number;measurements?:string;ingredients?:string;hygieneSealed?:boolean;liquid?:boolean; }
export interface Product { id: string; slug: string; localizedSlugs?: {tr:string;en:string}; name: string; nameEn: string; description: string; descriptionEn: string; category: string; brand: string; image: string; imageAlt?:string; material: string; status: string; variants: Variant[]; warnings: string; care: string; warningsEn?: string; careEn?: string; manufacturer: string | null; fixture: boolean;origin?:string;warranty?:string;warrantyEn?:string;manufacturerContact?:{address?:string;email?:string};responsiblePerson?:{name:string;address?:string;email?:string;country?:string}; }
export interface CartItem { variantId: string; quantity: number; productName: string; variantName: string; productNameEn?: string; variantNameEn?: string; priceMinor: number; displayPriceMinor?: number | null; image: string; available: number; }
export interface Cart { id: string; items: CartItem[]; subtotalMinor: number; currency: Currency; displayCurrency?: Currency; displaySubtotalMinor?: number | null; pricesComplete?: boolean; }
export interface Market {countryCode:string;name:string;settlementCurrency:Currency;deliveryTerm:string;}
export interface MarketCurrency {currency:Currency;available:boolean;}
export interface MarketsResponse {markets:Market[];currencies:MarketCurrency[];}
export interface CheckoutInput { quoteToken: string; couponCode?: string; email: string; fullName: string; phone?: string; line1: string; city: string; region?: string; district?: string; postalCode?: string; country: string; locale: Locale; currency: Currency; idempotencyKey: string; privacyAccepted: boolean; termsAccepted: boolean; }
export interface CheckoutQuoteInput {country:string;currency:Currency;locale:Locale;couponCode?:string;}
export interface CheckoutQuote {quoteToken:string;expiresAt:string;currency:Currency;lines:{variantId:string;name:string;variantName:string;quantity:number;unitMinor:number;discountMinor:number;taxMinor:number;lineTotalMinor:number}[];subtotalMinor:number;discountMinor:number;shippingMinor:number;goodsTaxMinor:number;shippingTaxMinor:number;taxMinor:number;totalMinor:number;deliveryTerm:string;}
export interface OrderSummary { id: string; number: string; status: string; paymentStatus: string; fulfillmentStatus: string; currency: Currency; subtotalMinor: number; shippingMinor: number; taxMinor: number; discountMinor: number; totalMinor: number; createdAt: string; items: { variantId: string; name: string; sku: string; quantity: number; unitMinor: number }[]; shipments: { carrier: string; trackingNumber: string; status: string }[]; }
export interface CheckoutResult { orderId: string; number: string; totalMinor: number; currency: Currency; paymentUrl: string; trackingToken: string; }
export type CatalogFeature = 'liquid' | 'hygiene-sealed';
export const catalogQueryKeys = ['q','category','min','max','material','brand','size','color','power','features','available','sort','page','locale','currency'] as const;
export interface CatalogFilter { q?: string; category?: string; min?: number; max?: number; material?: string; brand?:string;size?:string;color?:string;power?:string;features?:CatalogFeature[];available?: boolean; sort?: string; page?: number; locale?:Locale;currency?:Currency; }
export interface CatalogFacet {value:string;count:number;label?:string;}
export interface CatalogFacets {categories:CatalogFacet[];brands:CatalogFacet[];materials:CatalogFacet[];sizes:CatalogFacet[];colors:CatalogFacet[];power:CatalogFacet[];features:CatalogFacet[];}
export type ProductSummary = Product;
export interface CatalogResult {products:ProductSummary[];facets:CatalogFacets;total:number;page:number;pageSize:number;}
export interface Principal { id: string; role: Role; mfa: boolean; mfaEnabled?: boolean; }
export function money(value: number, currency: Currency = "TRY", locale: Locale = "tr") { return formatMinorAmount(value,currency,2,locale === "tr" ? "tr-TR" : "en-GB"); }
export function projectedPrice(variant:Variant|undefined,currency:Currency):number|null {return variant?.displayCurrency===currency&&typeof variant.displayPriceMinor==="number"?variant.displayPriceMinor:null;}
