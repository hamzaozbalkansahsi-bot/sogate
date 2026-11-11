/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/shared/cms-types.ts
 * Açıklama   : Yapısal içerik bölgelerinin ve sürümlü sayfaların ortak veri sözleşmesi.
 */
import type {Locale,Product} from './contracts';
export type CMSLink={label:string;href:string};
export type HeroContent={kind:'hero';eyebrow:string;title:string;italic:string;description:string;cta:CMSLink;image?:string};
export type NavigationContent={kind:'navigation';links:CMSLink[];categoryLinks:CMSLink[]};
export type FooterContent={kind:'footer';description:string;columns:{title:string;links:CMSLink[]}[]};
export type CollectionContent={kind:'collection';title:string;description:string;image:string;productIds:string[];featured:boolean};
export type CMSPayload=HeroContent|NavigationContent|FooterContent|CollectionContent;
export type CMSRevision={id:string;regionId:string;key:string;locale:Locale;kind:CMSPayload['kind'];version:number;status:'draft'|'published'|'archived';publishAt:string|null;createdAt:string;fixture:boolean;active:boolean;payload:CMSPayload};
export type CMSPage={id:string;slug:string;locale:Locale;title:string;body:string;kind:'guide'|'faq'|'campaign'|'page';version:number;status:'draft'|'published'|'archived';publishAt:string|null;fixture:boolean;revisionId?:string};
export type PublicCollection=CollectionContent&{key:string};
export type PublicCMS={regions:{hero?:HeroContent;navigation?:NavigationContent;footer?:FooterContent};collections:PublicCollection[];products?:Product[];collection?:PublicCollection|null;page?:number;total?:number};
