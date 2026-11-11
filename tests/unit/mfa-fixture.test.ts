/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/mfa-fixture.test.ts
 * Açıklama   : E2E MFA hazırlığında gerçek HTTP doğrulaması ve sınırlı resmi kota beklemesini sınar.
 */
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import type {APIRequestContext,APIResponse,BrowserContext} from '@playwright/test';
const mocks=vi.hoisted(()=>({sleep:vi.fn(),enable:vi.fn()}));
vi.mock('node:timers/promises',()=>({setTimeout:mocks.sleep}));
vi.mock('../../src/server/auth',()=>({getAuth:()=>({api:{enableTwoFactor:mocks.enable}})}));
import {postMfaHttp,prepareMfaFixture} from '../e2e/helpers/mfa';
const response=(status:number,headers:Record<string,string>={}):APIResponse=>({status:()=>status,headers:()=>headers,dispose:vi.fn().mockResolvedValue(undefined)}) as unknown as APIResponse;
beforeEach(()=>{vi.clearAllMocks();mocks.sleep.mockResolvedValue(undefined);vi.stubEnv('APP_ENV','test');vi.stubEnv('DATABASE_URL','postgresql://fixture@127.0.0.1/sexsogate_test');});
afterEach(()=>vi.unstubAllEnvs());
describe('Bounded MFA fixture transport',()=>{
 it('does not repeat a non-429 failure',async()=>{
  const bad=response(400),post=vi.fn().mockResolvedValue(bad),body=vi.fn(()=>({code:'123456'}));
  expect(await postMfaHttp({post} as unknown as APIRequestContext,'/api/auth/two-factor/verify-totp',body)).toBe(bad);expect(post).toHaveBeenCalledTimes(1);expect(body).toHaveBeenCalledTimes(1);expect(mocks.sleep).not.toHaveBeenCalled();
 });
 it('waits for the official retry header and regenerates the TOTP body',async()=>{
  const post=vi.fn().mockResolvedValueOnce(response(429,{'x-retry-after':'2'})).mockResolvedValueOnce(response(200));let attempt=0;
  await postMfaHttp({post} as unknown as APIRequestContext,'/api/auth/two-factor/verify-totp',()=>({code:String(++attempt)}));
  expect(mocks.sleep).toHaveBeenCalledWith(2150);expect(post).toHaveBeenCalledTimes(2);expect(post.mock.calls[0][1].data.code).toBe('1');expect(post.mock.calls[1][1].data.code).toBe('2');
 });
 it.each([undefined,'-1','11','NaN','100000'])('rejects a missing or excessive retry window (%s)',async value=>{
  const post=vi.fn().mockResolvedValue(response(429,value===undefined?{}:{'x-retry-after':value}));
  await expect(postMfaHttp({post} as unknown as APIRequestContext,'/api/auth/two-factor/verify-totp',()=>({}))).rejects.toThrow('MFA_RETRY_WINDOW_INVALID');expect(post).toHaveBeenCalledTimes(1);expect(mocks.sleep).not.toHaveBeenCalled();
 });
 it('returns the second 429 without a third attempt',async()=>{
  const second=response(429,{'x-retry-after':'1'}),post=vi.fn().mockResolvedValueOnce(response(429,{'x-retry-after':'0'})).mockResolvedValueOnce(second);
  expect(await postMfaHttp({post} as unknown as APIRequestContext,'/api/auth/two-factor/verify-totp',()=>({}))).toBe(second);expect(post).toHaveBeenCalledTimes(2);expect(mocks.sleep).toHaveBeenCalledTimes(1);
 });
 it('uses the official server enable API and real HTTP verification',async()=>{
  mocks.enable.mockResolvedValue({response:{totpURI:'otpauth://totp/fixture?secret=JBSWY3DPEHPK3PXP'},headers:new Headers()});const ok=response(200),post=vi.fn().mockResolvedValue(ok),storageState=vi.fn().mockResolvedValue({cookies:[{domain:'127.0.0.1',path:'/',name:'fixture-session',value:'test-only'}]});
  expect(await prepareMfaFixture({request:{post,storageState},addCookies:vi.fn()} as unknown as BrowserContext,'test-only-password')).toBe(ok);expect(mocks.enable).toHaveBeenCalledTimes(1);expect(post).toHaveBeenCalledTimes(1);expect(post.mock.calls[0][0]).toBe('/api/auth/two-factor/verify-totp');expect(post.mock.calls[0][1].data).toEqual({code:expect.stringMatching(/^\d{6}$/),trustDevice:false});
 });
 it('copies official enable Set-Cookie headers to the browser jar before HTTP verification',async()=>{
  const headers=new Headers();headers.append('set-cookie','fixture-rotated=test-only-rotated; Path=/api/auth; HttpOnly; SameSite=Strict');mocks.enable.mockResolvedValue({response:{totpURI:'otpauth://totp/fixture?secret=JBSWY3DPEHPK3PXP'},headers});
  const addCookies=vi.fn(),post=vi.fn().mockResolvedValue(response(200)),storageState=vi.fn().mockResolvedValue({cookies:[{domain:'127.0.0.1',path:'/',name:'fixture-session',value:'test-only'}]});
  await prepareMfaFixture({request:{post,storageState},addCookies} as unknown as BrowserContext,'test-only-password');expect(addCookies).toHaveBeenCalledWith([{name:'fixture-rotated',value:'test-only-rotated',domain:'127.0.0.1',path:'/api/auth',httpOnly:true,secure:false,sameSite:'Strict'}]);expect(addCookies.mock.invocationCallOrder[0]).toBeLessThan(post.mock.invocationCallOrder[0]);
 });
 it('cannot prepare production MFA fixtures',async()=>{
  vi.stubEnv('APP_ENV','production');await expect(prepareMfaFixture({} as BrowserContext,'test-only-password')).rejects.toThrow('MFA_FIXTURE_ENVIRONMENT');expect(mocks.enable).not.toHaveBeenCalled();
 });
});
