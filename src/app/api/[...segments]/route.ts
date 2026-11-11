/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/[...segments]/route.ts
 * Açıklama   : HTTP işlemini doğrulayıp yetkili veri akışına bağlar.
 */
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import * as commerce from '@/server/commerce';
import { getAuth, getPrincipal, requirePrincipal } from '@/server/auth';
import { pool } from '@/server/db';
import { HttpError, enforceSameOrigin, readJsonLimited, publicFailure } from '@/server/security';
import { addresses,contact,newToken,resolveCartOwner,enforceQuota,adminUsers } from '@/server/customer';
import {enforceCheckoutNetworkQuota} from '@/server/abuse';
import type { CheckoutInput,CheckoutQuoteInput } from '@/shared/contracts';
import {parseCatalogQuery,searchCatalog,ensureCartExists} from '@/server/commerce/catalog';
import {customerErrorMessage} from '@/shared/errors';
import {choosePaymentAction} from '@/server/providers/retry-policy';

export const runtime='nodejs';export const dynamic='force-dynamic';
type Context={params:Promise<{segments:string[]}>};
const privateHeaders={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'};
export async function GET(request:NextRequest,context:Context){return handle(request,context);}
export async function POST(request:NextRequest,context:Context){return handle(request,context);}

async function handle(request:NextRequest,context:Context){
  let cartToken=request.cookies.get('sg_cart')?.value;let changed=false;
  if(!cartToken||!/^[A-Za-z0-9_-]{43}$/.test(cartToken)){cartToken=newToken();changed=true;}
  const respond=(value:unknown,status=200)=>{const response=NextResponse.json(value,{status,headers:privateHeaders});if(changed)response.cookies.set('sg_cart',cartToken!,{httpOnly:true,sameSite:'lax',secure:process.env.APP_ENV==='production',path:'/',maxAge:60*60*24*30});return response;};
  try{
    const {segments}=await context.params;const [resource,id]=segments;const query=request.nextUrl.searchParams;const post=request.method==='POST';
    const quoteRequest=post&&resource==='checkout'&&id==='quote'&&segments.length===2;
    const checkoutRequest=post&&resource==='checkout'&&segments.length===1;
    if(resource==='checkout'&&!quoteRequest&&!checkoutRequest)throw new HttpError(404,'İşlem bulunamadı.');
    if(resource==='health'&&!post){await pool.query('SELECT 1');return respond({status:'ok',sales:process.env.LIVE_SALES_ENABLED==='true'?'gated':'closed'});}
    if(post){enforceSameOrigin(request,process.env.APP_URL??'http://127.0.0.1:3000');await enforceQuota(cartToken,quoteRequest?'checkout-quote':resource,checkoutRequest?10:30);}
    if(checkoutRequest)await enforceCheckoutNetworkQuota(request);
    if(quoteRequest)await enforceCheckoutNetworkQuota(request,'quote');
    const body=post?await readJsonLimited(request):undefined;
    let cartCallerId:string|null=null;
    if(resource==='cart'||checkoutRequest){
      const principal=await getPrincipal(request.headers);cartCallerId=principal?.id??null;
      await ensureCartExists(cartToken);
      const next=await resolveCartOwner(cartToken,principal);changed ||= next!==cartToken;cartToken=next;
    }
    if(quoteRequest){
      const principal=await getPrincipal(request.headers);
      return respond(await commerce.quoteCheckout(cartToken,body as CheckoutQuoteInput,principal?.id??null));
    }
    if(resource==='catalog'&&!post){const filter=parseCatalogQuery(query,{locale:request.headers.get('accept-language')?.toLowerCase().startsWith('en')?'en':'tr',currency:'TRY'},Boolean(id));if(id){const product=await commerce.getProduct(decodeURIComponent(id),filter.locale,filter.currency);if(!product)throw new HttpError(404,'Ürün bulunamadı.');return respond({product});}return respond(await searchCatalog(filter));}
    if(resource==='session'&&!post){const session=await getAuth().api.getSession({headers:request.headers});const p=session?await getPrincipal(request.headers):null;return respond({user:session&&p?{id:p.id,name:session.user.name,email:session.user.email,role:p.role,twoFactorEnabled:p.mfaEnabled===true,mfaVerified:p.mfa}:null});}
    if(resource==='cart'){
      if(post){const data=z.object({variantId:z.string().min(1).max(100),quantity:z.number().int().min(0).max(99)}).strict().parse(body);return respond(await commerce.setCartItem(cartToken,data.variantId,data.quantity,cartCallerId));}
      return respond(await commerce.getCart(cartToken,z.enum(['TRY','EUR','USD','GBP']).parse(query.get('currency')??'TRY'),cartCallerId));
    }
    if(checkoutRequest){
      const data=body as CheckoutInput;
      const provider=process.env.PAYMENT_PROVIDER==='stripe'?(await import('@/server/providers/stripe')).stripeProvider():null;
      const result=await commerce.checkout(cartToken,data,cartCallerId);
      if(provider){
        const base=process.env.APP_URL!;const orderUrl=new URL(`/siparis/${result.orderId}?token=${encodeURIComponent(result.trackingToken)}`,base).href;
        const state=(await pool.query('SELECT o.status,o.expires_at,p.status payment_status,p.provider_reference FROM orders o JOIN payments p ON p.order_id=o.id WHERE o.id=$1',[result.orderId])).rows[0];
        const plan=choosePaymentAction({orderStatus:state.status,paymentStatus:state.payment_status,expiresAt:state.expires_at,providerReference:state.provider_reference});
        if(plan==='order')result.paymentUrl=orderUrl;
        else if(plan==='resume'){
          const saved=await provider.resumeSession(state.provider_reference);
          if(saved.orderId!==result.orderId||saved.amountMinor!==result.totalMinor||saved.currency!==result.currency)throw new HttpError(409,'Ödeme oturumu siparişle eşleşmiyor.');
          if(saved.paymentStatus==='paid'||saved.status==='expired')await commerce.settleVerifiedPayment({eventId:`api-query:${saved.id}:${saved.paymentStatus==='paid'?'paid':'expired'}`,orderId:result.orderId,status:saved.paymentStatus==='paid'?'succeeded':'failed',amountMinor:saved.amountMinor,currency:saved.currency,timestamp:saved.created,providerReference:saved.id},'stripe');
          result.paymentUrl=saved.url??orderUrl;
        }else{const session=await provider.createSession({orderId:result.orderId,number:result.number,totalMinor:result.totalMinor,currency:result.currency,idempotencyKey:`checkout:${result.orderId}`,returnUrl:orderUrl,cancelUrl:orderUrl});await commerce.setPaymentReference(result.orderId,'stripe',session.id);result.paymentUrl=session.url;}
      }
      return respond(result);
    }
    if(resource==='test-payment'&&post){const data=z.object({orderId:z.string(),token:z.string(),outcome:z.enum(['succeeded','failed'])}).strict().parse(body);const event=await commerce.createTestPaymentEvent(data.orderId,data.token,data.outcome);await commerce.handlePayment(event.raw,event.signature);return respond({ok:true,orderId:data.orderId,trackingToken:data.token});}
    if(resource==='orders'&&!post){const principal=await getPrincipal(request.headers);if(id){const order=await commerce.getOrder(id,query.get('token'),principal?.id);if(!order)throw new HttpError(404,'Sipariş bulunamadı veya erişim süresi doldu.');return respond(order);}if(!principal)throw new HttpError(401,'Siparişlerinizi görmek için giriş yapın.');const rows=await pool.query('SELECT id FROM orders WHERE user_id=$1 ORDER BY created_at DESC LIMIT 50',[principal.id]);return respond({orders:await Promise.all(rows.rows.map(r=>commerce.getOrder(r.id,null,principal.id)))});}
    if(resource==='addresses'){const p=await requirePrincipal(request.headers);return respond(await addresses(p,body));}
    if(resource==='favorites'){const locale=z.enum(['tr','en']).parse(query.get('locale')??(request.headers.get('accept-language')?.startsWith('en')?'en':'tr'));const currency=z.enum(['TRY','EUR','USD','GBP']).parse(query.get('currency')??'TRY');const p=await requirePrincipal(request.headers);if(post){const data=z.object({productId:z.string(),active:z.boolean()}).strict().parse(body);if(data.active)await pool.query('INSERT INTO wishlists(user_id,product_id) VALUES($1,$2) ON CONFLICT DO NOTHING',[p.id,data.productId]);else await pool.query('DELETE FROM wishlists WHERE user_id=$1 AND product_id=$2',[p.id,data.productId]);}const rows=await pool.query('SELECT p.slug FROM products p JOIN wishlists w ON w.product_id=p.id WHERE w.user_id=$1 AND p.status=\'published\' ORDER BY w.created_at DESC LIMIT 100',[p.id]);return respond({items:(await Promise.all(rows.rows.map(r=>commerce.getProduct(r.slug,locale,currency)))).filter(Boolean)});}
    if(resource==='content'&&!post){const locale=z.enum(['tr','en']).parse(query.get('locale')??'tr');const slug=query.get('slug');const {publicContentPages}=await import('@/server/cms');const pages=await publicContentPages(slug,locale);return respond(slug?{page:pages[0]??null}:{pages});}
    if(resource==='legal'&&!post){const locale=z.enum(['tr','en']).parse(query.get('locale')??'tr');const result=await pool.query('SELECT kind,locale,title,body,version,body_hash,status FROM legal_documents WHERE locale=$1 AND kind=$2 AND status=\'effective\' AND (fixture=false OR $3=true) ORDER BY version DESC LIMIT 1',[locale,id,process.env.APP_ENV!=='production']);return respond({page:result.rows[0]??null});}
    if(resource==='contact'){if(post){if((body as {kind?:string})?.kind==='privacy'){const {privacyQuota}=await import('@/server/privacy-rate');await privacyQuota(request);}return respond(await contact(body,await getPrincipal(request.headers)),201);}const rows=await pool.query('SELECT key,value FROM settings WHERE key=ANY($1::text[])',[['seller.supportEmail','seller.phone','seller.address']]);const map=new Map(rows.rows.map(r=>[r.key,r.value]));return respond({contact:{email:map.get('seller.supportEmail')||undefined,phone:map.get('seller.phone')||undefined,address:map.get('seller.address')||undefined}});}
    if(resource==='returns'&&post){const data=z.object({orderId:z.string(),token:z.string().optional(),variantId:z.string(),quantity:z.number().int().positive(),reason:z.string().min(5).max(2000),sealIntact:z.boolean()}).strict().parse(body);const p=await getPrincipal(request.headers);const order=await commerce.getOrder(data.orderId,data.token??null,p?.id);if(!order)throw new HttpError(404,'Sipariş bulunamadı.');const {orderId,token,...details}=data;return respond(await commerce.requestReturn(orderId,token??null,details,p?.id),201);}
    if(resource==='admin'){
      const p=await requirePrincipal(request.headers,true);if(!id)throw new HttpError(404,'İşlem bulunamadı.');
      if(id==='orders'&&segments.length>=3){if(segments.length!==3)throw new HttpError(404,'Sipariş işlemi bulunamadı.');const {staffOrderDetail,staffFulfillmentAction}=await import('@/server/commerce/staff-orders');return respond(post?await staffFulfillmentAction(segments[2],body,p):await staffOrderDetail(segments[2],p));}
      if(id==='users')return respond(await adminUsers(p,body,request.headers));
      if(id==='taxes'){const {manageTax,listTaxes}=await import('@/server/shipping-tax');return respond(post?await manageTax(body,p):await listTaxes(p));}
      if(id==='integrations')return respond({rows:[{name:'Stripe',status:'İşletme/kategori kabulü ve test erişimi bekliyor'},{name:'Kargo',status:'Manuel sevk; taşıyıcı API erişimi bekliyor'},{name:'e-Fatura / e-Arşiv',status:'Satıcı ve sağlayıcı onayı bekliyor'},{name:'Pazaryerleri',status:'Kategori ve API kabulü bekliyor'}]});
      if(id==='seo'){const {seoReport}=await import('@/server/seo');return respond(await seoReport(p));}
      let command=body;
      if(post&&id==='returns'&&(body as {action?:string})?.action==='refund'){
        const password=z.string().min(12).parse((body as {password?:unknown}).password);
        await getAuth().api.verifyPassword({headers:request.headers,body:{password}}).catch(()=>{throw new HttpError(403,'Parola tekrar doğrulaması başarısız.');});
        command=Object.fromEntries(Object.entries(body as Record<string,unknown>).filter(([key])=>key!=='password'));
      }
      return respond(post?await commerce.adminAction(id,command,p):await commerce.adminList(id,p,Object.fromEntries(query)));
    }
    throw new HttpError(404,'İstenen işlem bulunamadı.');
  }catch(error){
    const locale=request.headers.get('accept-language')?.startsWith('en')?'en':'tr';
    if(error instanceof z.ZodError)return respond({error:locale==='en'?'Review the highlighted fields.':'Alanları kontrol edin.',code:'VALIDATION',fields:error.issues.map(i=>({path:i.path.join('.'),message:i.message}))},400);
    const e=publicFailure(error);const status=e.status;
    return respond({error:customerErrorMessage(e.code,status,e.message,locale),code:status<500?e.code:'SERVICE_UNAVAILABLE'},status);
  }
}
