/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/helpers/sign-in.ts
 * Açıklama   : Gerçek arayüz girişinde yalnız resmî 429 bekleme süresine uyarak bir kez yeniden dener.
 */
import {setTimeout as delay} from 'node:timers/promises';
import type {Page,Locator,Response} from '@playwright/test';
export async function submitSignIn(page:Pick<Page,'waitForResponse'>,button:Pick<Locator,'click'>):Promise<Response>{
 async function attempt(){const [response]=await Promise.all([page.waitForResponse(response=>new URL(response.url()).pathname==='/api/auth/sign-in/email'&&response.request().method()==='POST'),button.click()]);return response;}
 const response=await attempt();if(response.status()!==429)return response;
 const value=response.headers()['x-retry-after']??response.headers()['retry-after'];
 if(typeof value!=='string'||!/^\d{1,2}$/.test(value)||Number(value)>60)throw new Error('SIGN_IN_RETRY_WINDOW_INVALID');
 await delay(Number(value)*1000+150);
 return attempt();
}
