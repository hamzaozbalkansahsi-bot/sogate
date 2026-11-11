/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/payments/webhook/route.ts
 * Açıklama   : HTTP işlemini doğrulayıp yetkili veri akışına bağlar.
 */
import {NextResponse} from 'next/server';
import {handlePayment} from '@/server/commerce';
export const runtime='nodejs';export const dynamic='force-dynamic';
export async function POST(request:Request){
 try {const raw=await request.text();if(Buffer.byteLength(raw)>1000000)return NextResponse.json({error:'İstek sınırı aşıldı.'},{status:413});return NextResponse.json(await handlePayment(raw,request.headers.get('x-payment-signature')??''),{headers:{'Cache-Control':'no-store'}});}
 catch(e){const error=e as {status?:number};return NextResponse.json({error:'Ödeme bildirimi doğrulanamadı.'},{status:error.status??400});}
}
