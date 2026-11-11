/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/yonetim/[resource]/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {notFound} from "next/navigation";
import {AdminView} from "@/components/admin";
export default async function Page({params}:{params:Promise<{resource:string}>}){const {resource}=await params;if(!["social","compliance","privacy","products","lots","inventory","suppliers","orders","shipments","returns","content","countries","integrations","reports","jobs","audit","settings","launch","legal","seo","users","imports","variants","categories","brands","purchases","campaigns","media","taxes"].includes(resource))notFound();return <AdminView resource={resource}/>;}
