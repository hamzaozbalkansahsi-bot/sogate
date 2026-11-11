/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/markets/route.ts
 * Açıklama   : Yayına uygun ülke ve fiyat listesi tercihlerini salt okunur sunar.
 */
import {NextResponse} from "next/server";
import {getMarkets} from "@/server/markets";
export const runtime="nodejs";
export const dynamic="force-dynamic";
const headers={"Cache-Control":"no-store","X-Robots-Tag":"noindex, nofollow"};
export async function GET(request:Request){try{return NextResponse.json(await getMarkets(),{headers});}catch{return NextResponse.json({error:request.headers.get("accept-language")?.startsWith("en")?"Shopping preferences are currently unavailable.":"Alışveriş tercihleri şu anda alınamıyor.",code:"MARKETS_UNAVAILABLE"},{status:503,headers});}}
