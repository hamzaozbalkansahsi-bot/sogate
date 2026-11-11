/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/payments/stripe/route.ts
 * Açıklama   : HTTP işlemini doğrulayıp yetkili veri akışına bağlar.
 */
import {NextResponse} from 'next/server';
import {createHash} from 'node:crypto';
import {stripeProvider} from '@/server/providers/stripe';
import {transaction} from '@/server/db';
export const runtime='nodejs';export const dynamic='force-dynamic';
export async function POST(request:Request){
 try {
  const raw=await request.text();if(Buffer.byteLength(raw)>1000000)return NextResponse.json({error:'İstek sınırı aşıldı.'},{status:413});
  const provider=stripeProvider();const signature=request.headers.get('stripe-signature')??'';const event=provider.verifyEvent(raw,signature);
  if(event.livemode!==(process.env.APP_ENV==='production'))return NextResponse.json({error:'Ödeme ortamı eşleşmiyor.'},{status:400});
  const normalized=provider.verify(raw,signature);const hash=createHash('sha256').update(raw).digest('hex');
  await transaction(async client=>{
   const prior=await client.query('SELECT payload_hash FROM provider_events WHERE id=$1 FOR UPDATE',[event.id]);
   if(prior.rowCount){if(prior.rows[0].payload_hash!==hash)throw new Error('EVENT_COLLISION');return;}
   await client.query('INSERT INTO provider_events(id,provider,type,payload_hash,normalized,status) VALUES($1,\'stripe\',$2,$3,$4,$5)',[event.id,event.type,hash,normalized??{eventId:event.id,type:event.type},normalized?'pending':'review']);
   await client.query('INSERT INTO jobs(type,payload,dedupe_key) VALUES($1,$2,$3) ON CONFLICT DO NOTHING',[normalized?'payment.stripe':'payment.stripe-review',{eventId:event.id},`stripe:${event.id}`]);
  });
  return NextResponse.json({received:true},{headers:{'Cache-Control':'no-store'}});
 }catch(error){const e=error as {type?:string;status?:number};return NextResponse.json({error:'Bildirim doğrulanamadı veya güvenle kaydedilemedi.'},{status:e.type==='StripeSignatureVerificationError'?400:e.status??503});}
}
