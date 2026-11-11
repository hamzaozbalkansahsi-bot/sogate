/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/sign-in-fixture.test.ts
 * Açıklama   : Giriş testinin kota sıfırlamadan resmî bekleme süresini ve tek tekrar sınırını koruduğunu sınar.
 */
import {beforeEach,describe,it,expect,vi} from 'vitest';
import type {Page,Locator,Response} from '@playwright/test';
const mocks=vi.hoisted(()=>({sleep:vi.fn()}));
vi.mock('node:timers/promises',()=>({setTimeout:mocks.sleep}));
import {submitSignIn} from '../e2e/helpers/sign-in';
function fixture(statuses:number[],retry?:string){
 const replies=statuses.map(status=>({status:()=>status,headers:()=>retry===undefined?{}:{'x-retry-after':retry}} as unknown as Response));
 const page={waitForResponse:vi.fn().mockImplementation(()=>Promise.resolve(replies.shift()))} as unknown as Pick<Page,'waitForResponse'>;
 const button={click:vi.fn().mockResolvedValue(undefined)} as unknown as Pick<Locator,'click'>;
 return {page,button};
}
beforeEach(()=>{vi.clearAllMocks();mocks.sleep.mockResolvedValue(undefined);});
describe('real sign-in fixture rate handling',()=>{
 it('leaves successful and non-rate-limit failures untouched',async()=>{for(const status of [200,401,403,500]){const {page,button}=fixture([status]);expect((await submitSignIn(page,button)).status()).toBe(status);expect(button.click).toHaveBeenCalledTimes(1);}});
 it('waits for the official window before one fresh UI submit',async()=>{let release=()=>{};const gate=new Promise<void>(resolve=>{release=resolve;});mocks.sleep.mockImplementation(()=>gate);const {page,button}=fixture([429,200],'24'),task=submitSignIn(page,button);await vi.waitFor(()=>expect(mocks.sleep).toHaveBeenCalledWith(24150));expect(button.click).toHaveBeenCalledTimes(1);release();expect((await task).status()).toBe(200);expect(button.click).toHaveBeenCalledTimes(2);});
 it('rejects absent, unbounded or malformed retry hints',async()=>{for(const retry of [undefined,'-1','61','1.5','999','tomorrow']){const {page,button}=fixture([429],retry);await expect(submitSignIn(page,button)).rejects.toThrow('SIGN_IN_RETRY_WINDOW_INVALID');expect(button.click).toHaveBeenCalledTimes(1);}});
 it('returns a second429 without resetting quotas or further retries',async()=>{const {page,button}=fixture([429,429],'0'),task=submitSignIn(page,button);expect((await task).status()).toBe(429);expect(button.click).toHaveBeenCalledTimes(2);});
});
