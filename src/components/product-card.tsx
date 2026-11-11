"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/product-card.tsx
 * Açıklama   : Erişilebilir müşteri veya yönetim etkileşimini sunar.
 */
import Image from "next/image";
import Link from "./localized-link";
import {Heart,ArrowUpRight} from "lucide-react";
import {useState} from "react";
import {useStore} from "./store-context";
import {post} from "./api";
import {money,type Product} from "@/shared/contracts";
import {selectCatalogDisplay} from '@/shared/catalog-display';
import {categoryLabel} from "@/shared/i18n";
export function ProductCard({product}:{product:Product}){
 const {locale,t,user,currency}=useStore(),[saved,setSaved]=useState(false),[feedback,setFeedback]=useState("");
 const {variant,priceMinor:price}=selectCatalogDisplay(product.variants,currency),available=product.variants.some(v=>v.available>0),projectionReady=product.variants.every(v=>v.displayCurrency===currency),slug=product.localizedSlugs?.[locale]??product.slug;
 return <article className="product-card"><div className="product-image-wrap"><Link className="product-link" href={`/urun/${slug}`} aria-label={locale==="en"?product.nameEn:product.name}><Image unoptimized src={product.image} alt={product.imageAlt||(locale==="en"?product.nameEn:product.name)} width={420} height={470} loading="lazy"/></Link><button className={`wishlist-button icon-button ${saved?"active":""}`} type="button" aria-label={t("favorites")} aria-pressed={saved} onClick={async()=>{if(!user){setFeedback(t("loginRequired"));return;}try{await post("/api/favorites",{productId:product.id,active:!saved});setSaved(!saved);setFeedback("");}catch(e){setFeedback((e as Error).message);}}}><Heart size={19} fill={saved?"currentColor":"none"}/></button>{!available&&<span className="stock-pill">{t("soldOut")}</span>}</div><div className="product-meta"><span className="product-category">{categoryLabel(product.category,locale)}</span><Link href={`/urun/${slug}`}><h3>{locale==="en"?product.nameEn:product.name}</h3></Link><div className="product-bottom"><span className="price">{!projectionReady?t("loading"):price===null?(locale==="tr"?`${currency} fiyatı bulunmuyor`:`Price unavailable in ${currency}`):money(price,currency,locale)}</span><Link className="product-detail-link" href={`/urun/${slug}`} aria-label={`${product.name} — ${t("details")}`}><ArrowUpRight size={18}/></Link></div><p className="variant-caption">{product.variants.length} {locale==="tr"?"seçenek":"options"}{variant?.name?` · ${locale==="en"?(variant.nameEn||variant.name):variant.name}`:""}</p>{feedback&&<p className="small error" role="status">{feedback}</p>}</div></article>;
}
