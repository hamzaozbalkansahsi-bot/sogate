/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/accessibility.spec.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import { test, expect, type Page, type TestInfo } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mkdir } from 'node:fs/promises';

const tags=['wcag2a','wcag2aa','wcag21aa','wcag22aa'];
async function ready(page:Page) {
  await page.waitForLoadState('networkidle');
  await page.evaluate(()=>document.fonts.ready);
}
async function acknowledgeAge(page:Page) {
  await page.context().addCookies([{name:'sexsogate_adult',value:'yes',domain:'127.0.0.1',path:'/'}]);
}
async function audit(page:Page,info:TestInfo) {
  const results=await new AxeBuilder({page}).withTags(tags).analyze();
  await info.attach('axe-results',{body:JSON.stringify({violations:results.violations,incomplete:results.incomplete},null,2),contentType:'application/json'});
  expect(results.violations,JSON.stringify(results.violations.map(issue=>({id:issue.id,impact:issue.impact,nodes:issue.nodes.map(node=>({target:node.target,summary:node.failureSummary}))})),null,2)).toEqual([]);
}

for(const route of ['/', '/urunler', '/odeme', '/hesap']) {
  test(`390px WCAG 2.2 AA automated audit: ${route}`,async({page},info)=>{
    await page.setViewportSize({width:390,height:844});
    await acknowledgeAge(page);await page.goto(route);await ready(page);
    await expect(page.locator('main')).toBeVisible();
    await audit(page,info);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  });
}

test('390px adult notice is accessible and keyboard focus stays in the dialog',async({page},info)=>{
  await page.setViewportSize({width:390,height:844});
  await page.goto('/');await ready(page);
  const dialog=page.getByRole('dialog',{name:'Yetişkinlere özel bir dünya'});
  await expect(dialog).toBeVisible();await audit(page,info);
  await dialog.getByRole('button',{name:'18 yaşından büyüğüm',exact:true}).focus();
  for(let i=0;i<6;i++) {
    await page.keyboard.press('Tab');
    expect(await dialog.evaluate(element=>element.contains(document.activeElement))).toBe(true);
  }
  await dialog.getByRole('button',{name:'18 yaşından büyüğüm',exact:true}).focus();
  await page.keyboard.press('Enter');await expect(dialog).not.toBeVisible();
  await expect(page.getByRole('heading',{name:/Tutkunu/})).toBeVisible();
});

test('before any tracking consent no third party request or advertising cookie is created',async({page})=>{
  const origins=new Set<string>();
  page.on('request',request=>{const url=new URL(request.url());if(url.protocol==='http:'||url.protocol==='https:')origins.add(url.origin);});
  await page.goto('/');await ready(page);
  const dialog=page.getByRole('dialog',{name:'Yetişkinlere özel bir dünya'});
  await expect(dialog).toBeVisible();
  await dialog.getByRole('button',{name:'18 yaşından büyüğüm',exact:true}).click();
  await expect(dialog).not.toBeVisible();await ready(page);
  await page.goto('/urunler');await ready(page);
  expect([...origins]).toEqual(['http://127.0.0.1:3000']);
  const cookieNames=(await page.context().cookies()).map(cookie=>cookie.name);
  expect(cookieNames.filter(name=>/^_(?:ga|gid|gat|fbp|fbc)(?:_|$)/i.test(name))).toEqual([]);
  const storageKeys=await page.evaluate(()=>[...Object.keys(localStorage),...Object.keys(sessionStorage)]);
  expect(storageKeys.filter(name=>/google.?analytics|facebook|hotjar|clarity|session.?replay/i.test(name))).toEqual([]);
});

test('390px RTL infrastructure preserves Arabic controls, focus and horizontal containment',async({page,browserName})=>{
  await page.setViewportSize({width:390,height:844});
  await acknowledgeAge(page);await page.goto('/');await ready(page);
  await page.evaluate(()=>{
    document.documentElement.dir='rtl';document.documentElement.lang='ar';
    const section=document.createElement('section');section.className='card form-stack';section.lang='ar';section.dir='rtl';section.setAttribute('aria-label','فحص اتجاه الواجهة');
    const heading=document.createElement('h2');heading.textContent='الخصوصية والاختيار';section.append(heading);
    for(const [text,type,value] of [['البريد الإلكتروني','email','local@example.invalid'],['العنوان','text','شارع الورد ١٢']]) {
      const label=document.createElement('label');label.textContent=text;
      const input=document.createElement('input');input.type=type;input.value=value;input.dir=type==='email'?'ltr':'auto';label.append(input);section.append(label);
    }
    document.querySelector('main')!.prepend(section);
  });
  await page.evaluate(()=>document.fonts.ready);
  expect(await page.evaluate(()=>getComputedStyle(document.documentElement).direction)).toBe('rtl');
  await expect(page.getByRole('heading',{name:'الخصوصية والاختيار'})).toBeVisible();
  await page.getByLabel('البريد الإلكتروني',{exact:true}).focus();await page.keyboard.press('Tab');
  const address=page.getByLabel('العنوان',{exact:true});await expect(address).toBeFocused();
  expect(await address.evaluate(element=>{const style=getComputedStyle(element);return style.outlineStyle!=='none'&&parseFloat(style.outlineWidth)>0;})).toBe(true);
  const clipped=await page.locator('button,a.button,input,select').evaluateAll(elements=>elements.filter(element=>{
    const bounds=element.getBoundingClientRect(),style=getComputedStyle(element);
    return bounds.width>0&&bounds.height>0&&style.visibility!=='hidden'&&(bounds.left< -1||bounds.right>window.innerWidth+1);
  }).map(element=>({tag:element.tagName,label:element.getAttribute('aria-label')||element.textContent?.trim().slice(0,60)})));
  expect(clipped).toEqual([]);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await mkdir('docs/screenshots',{recursive:true});
  await page.screenshot({path:`docs/screenshots/rtl-infrastructure${browserName==='chromium'?'':'-'+browserName}.png`,fullPage:true});
});
