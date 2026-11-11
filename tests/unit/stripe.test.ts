/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/stripe.test.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import {describe,it,expect} from 'vitest';
import Stripe from 'stripe';
import {StripePaymentProvider} from '../../src/server/providers/stripe';
const secret='whsec_local_signature_fixture_not_an_account';
const config={secretKey:'sk_test_local_fixture_not_an_account',webhookSecret:secret,appEnv:'test',businessApproved:false};
function event(overrides:Record<string,unknown>={}){return JSON.stringify({id:'evt_test_unique',object:'event',type:'checkout.session.completed',livemode:false,created:Math.floor(Date.now()/1000),data:{object:{id:'cs_test_unique',object:'checkout.session',mode:'payment',payment_status:'paid',status:'complete',amount_total:12345,currency:'try',metadata:{orderId:'order-local'},payment_intent:'pi_test_unique',...overrides}}});}
describe('Stripe resmî SDK imza ve ödeme sınırı',()=>{
  it('ham gövdeyi imzadan önce değiştiren veya imzasız olayı reddeder',()=>{
    const provider=new StripePaymentProvider(config);const raw=event();const signature=Stripe.webhooks.generateTestHeaderString({payload:raw,secret});
    expect(()=>provider.verify(raw+' ',signature)).toThrow();expect(()=>provider.verify(raw,'')).toThrow();
    expect(provider.verify(raw,signature)).toMatchObject({eventId:'evt_test_unique',orderId:'order-local',amountMinor:12345,currency:'TRY',status:'succeeded'});
  });
  it('ödeme bekleyen Checkout tamamlanmasını tahsilat saymaz',()=>{
    const provider=new StripePaymentProvider(config);const raw=event({payment_status:'unpaid'});const sig=Stripe.webhooks.generateTestHeaderString({payload:raw,secret});
    expect(provider.verify(raw,sig)).toBeNull();
  });
  it('test ortamına canlı olay ve bilinmeyen para birimi alınamaz',()=>{
    const provider=new StripePaymentProvider(config);const raw=event({currency:'jpy'});const sig=Stripe.webhooks.generateTestHeaderString({payload:raw,secret});expect(()=>provider.verify(raw,sig)).toThrow();
    const live=JSON.stringify({...JSON.parse(event()),livemode:true});expect(()=>provider.verify(live,Stripe.webhooks.generateTestHeaderString({payload:live,secret}))).toThrow();
  });
  it('kategori kabulü olmadan canlı anahtar kullanımını reddeder',()=>{
    expect(()=>new StripePaymentProvider({...config,secretKey:'sk_live_not_real',appEnv:'production'})).toThrow();
  });
});
