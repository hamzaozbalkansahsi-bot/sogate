"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/localized-link.tsx
 * Açıklama   : Erişilebilir müşteri veya yönetim etkileşimini sunar.
 */
// Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
// Dosya: src/components/localized-link.tsx | Açıklama: Müşteri bağlantılarında yayımlanmış dil URL'sini korur.
import NextLink from "next/link";
import type {ComponentProps} from "react";
import {useStore} from "./store-context";
import {localePath} from "@/shared/i18n";
export default function LocalizedLink({href,...props}:ComponentProps<typeof NextLink>){const {locale}=useStore();return <NextLink href={typeof href==="string"?localePath(href,locale):href} {...props}/>;}
