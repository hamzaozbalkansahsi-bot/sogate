/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/abuse.test.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import {describe,it,expect} from 'vitest';
import {checkoutNetworkPolicy,type CheckoutNetworkConfig} from '../../src/server/abuse';
const config:CheckoutNetworkConfig={appEnv:'production',trustedProxyEnabled:true,clientIpHeader:'x-real-ip',secret:'isolated-unit-only-secret-with-over-32-characters'};
const request=(ip?:string,extra:Record<string,string>={})=>new Request('https://example.invalid/api/checkout',{method:'POST',headers:{...(ip?{'x-real-ip':ip}:{}),...extra}});
describe('Checkout trusted network quota policy',()=>{
 it('fails closed without an explicitly configured production proxy boundary',()=>{
  for(const change of [{trustedProxyEnabled:false},{clientIpHeader:''},{clientIpHeader:'x-forwarded-for'},{secret:'short'},{appEnv:''}]) {
   try{checkoutNetworkPolicy(request('192.0.2.1'),{...config,...change});expect.unreachable();}
   catch(error){expect((error as {status:number}).status).toBe(503);}
  }
 });
 it('requires a valid single client IP and never falls back to spoofable forwarded chains',()=>{
  for(const ip of [undefined,'not-an-ip','192.0.2.1, 192.0.2.2','0192.0.2.1','2001:db8::1%eth0','[2001:db8::1]']) {
   expect(()=>checkoutNetworkPolicy(request(ip,{'x-forwarded-for':'192.0.2.1'}),config)).toThrow();
  }
 });
 it('hashes an IPv4 identity independently from cart cookies and forwarded values',()=>{
  const one=checkoutNetworkPolicy(request('192.0.2.1',{cookie:'sg_cart=one','x-forwarded-for':'203.0.113.1'}),config);
  const two=checkoutNetworkPolicy(request('192.0.2.1',{cookie:'sg_cart=two','x-forwarded-for':'203.0.113.2'}),config);
  expect(one).toEqual(two);expect(one.max).toBe(10);expect(one.key).toMatch(/^checkout-network:[a-f0-9]{64}$/);
  expect(one.key).not.toContain('192.0.2.1');
  expect(checkoutNetworkPolicy(request('192.0.2.2'),config).key).not.toBe(one.key);
 });
 it('groups equivalent IPv6 forms and rotating lower64 addresses into the same subnet',()=>{
  const one=checkoutNetworkPolicy(request('2001:db8:1:2::1'),config);
  expect(checkoutNetworkPolicy(request('2001:0DB8:0001:0002:ABCD:0000:0000:0009'),config).key).toBe(one.key);
  expect(checkoutNetworkPolicy(request('2001:db8:1:3::1'),config).key).not.toBe(one.key);
 });
 it('does not permit IPv4-mapped IPv6 spelling to bypass the IPv4 bucket',()=>{
  const one=checkoutNetworkPolicy(request('192.0.2.1'),config);
  expect(checkoutNetworkPolicy(request('::ffff:192.0.2.1'),config).key).toBe(one.key);
  expect(checkoutNetworkPolicy(request('0:0:0:0:0:ffff:c000:0201'),config).key).toBe(one.key);
 });
 it('uses one local aggregate100 quota independent of all untrusted headers',()=>{
  const local={...config,appEnv:'development',trustedProxyEnabled:false,clientIpHeader:''};
  const one=checkoutNetworkPolicy(request('192.0.2.1'),local);
  expect(checkoutNetworkPolicy(request('2001:db8::1'),local)).toEqual(one);
  expect(one.max).toBe(100);
  expect(checkoutNetworkPolicy(request(),{...local,appEnv:'test'})).toEqual(one);
 });
 it('keeps price-summary requests in a separate bounded network bucket',()=>{
  const payment=checkoutNetworkPolicy(request('192.0.2.1'),config),quote=checkoutNetworkPolicy(request('192.0.2.1'),config,'quote');
  expect(quote.key).not.toBe(payment.key);expect(quote.max).toBe(60);expect(payment.max).toBe(10);
  expect(checkoutNetworkPolicy(request('::ffff:192.0.2.1'),config,'quote')).toEqual(quote);
  expect(()=>checkoutNetworkPolicy(request('192.0.2.1'),{...config,trustedProxyEnabled:false},'quote')).toThrow();
 });
});
