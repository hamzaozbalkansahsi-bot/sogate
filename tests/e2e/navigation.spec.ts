/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/navigation.spec.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import {test,expect} from '@playwright/test';
test('sabit kaynakta sayfa kendiliğinden tekrar yüklenmez',async({page})=>{
 const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 let navigations=0;page.on('request',request=>{if(request.isNavigationRequest()&&request.frame()===page.mainFrame())navigations++;});
 await page.goto('/',{waitUntil:'domcontentloaded'});await page.waitForTimeout(1500);expect(navigations).toBe(1);expect(errors).toEqual([]);
});
