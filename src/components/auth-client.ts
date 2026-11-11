"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/auth-client.ts
 * Açıklama   : Erişilebilir müşteri veya yönetim etkileşimini sunar.
 */
import {createAuthClient} from "better-auth/react";
import {twoFactorClient} from "better-auth/client/plugins";
export const authClient=createAuthClient({plugins:[twoFactorClient()]});
