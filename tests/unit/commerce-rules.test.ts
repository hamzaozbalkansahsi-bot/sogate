/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/commerce-rules.test.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import { describe, expect, it } from "vitest";
import { allocateMinor, assertPermission, calculateTotals, assertTestEnvironment, validatePaymentEnvelope, signPayment, availableStock, DomainError } from "../../src/server/commerce/rules";

describe("commerce money and guards", () => {
  it("uses integer inclusive tax and preserves partial allocations", () => {
    expect(calculateTotals(10001, 500, 1000, 2000)).toEqual({subtotalMinor:10001,discountMinor:1000,shippingMinor:500,taxMinor:1500,totalMinor:9501});
    const shares=allocateMinor(100,[1,1,1]);
    expect(shares).toEqual([34,33,33]);
    expect(shares.reduce((a,b)=>a+b,0)).toBe(100);
  });
  it("rejects money outside safe integer or invalid discounts",()=>{
    expect(()=>calculateTotals(1.1,0,0,2000)).toThrow(DomainError);
    expect(()=>calculateTotals(100,0,101,2000)).toThrow(DomainError);
  });
  it("denies warehouse finance and marketing customer export",()=>{
    expect(()=>assertPermission({id:"w",role:"warehouse",mfa:true},"reports","read")).toThrow(DomainError);
    expect(()=>assertPermission({id:"m",role:"marketing",mfa:true},"customers","read")).toThrow(DomainError);
    expect(()=>assertPermission({id:"w",role:"warehouse",mfa:true},"inventory","write")).not.toThrow();
    expect(()=>assertPermission({id:"a",role:"admin",mfa:false},"settings","write")).toThrow(DomainError);
  });
  it("denies test adapter outside development and test",()=>{
    expect(()=>assertTestEnvironment("production")).toThrow(DomainError);
    expect(()=>assertTestEnvironment("staging")).toThrow(DomainError);
    expect(()=>assertTestEnvironment(undefined)).toThrow(DomainError);
    expect(()=>assertTestEnvironment("development")).not.toThrow();
  });
  it("does not allow reservations or safety stock to create negative availability",()=>{
    expect(availableStock(3,2,1)).toBe(0);
    expect(availableStock(1,5,1)).toBe(0);
  });
});

describe("payment envelopes",()=>{
  const secret="unit-test-secret-with-at-least-32-characters";
  const event={id:"evt-a",orderId:"order-a",amountMinor:12345,currency:"TRY",status:"succeeded",timestamp:1770000000};
  it("requires authentic exact raw body and recent timestamp",()=>{
    const raw=JSON.stringify(event), signature=signPayment(raw,secret);
    expect(validatePaymentEnvelope(raw,signature,secret,1770000010)).toEqual(event);
    expect(()=>validatePaymentEnvelope(raw+" ",signature,secret,1770000010)).toThrow(DomainError);
    expect(()=>validatePaymentEnvelope(raw,"",secret,1770000010)).toThrow(DomainError);
    expect(()=>validatePaymentEnvelope(raw,signature,secret,1770000400)).toThrow(DomainError);
  });
  it("rejects malformed currency, fractional totals and future events",()=>{
    for(const change of [{currency:"ZZZ"},{amountMinor:1.1},{timestamp:1770000400}]){
      const raw=JSON.stringify({...event,...change});
      expect(()=>validatePaymentEnvelope(raw,signPayment(raw,secret),secret,1770000000)).toThrow(DomainError);
    }
  });
});
