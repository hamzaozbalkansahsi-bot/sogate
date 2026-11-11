/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/measure-lab.mjs
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import {chromium} from '@playwright/test';
import {writeFile} from 'node:fs/promises';
const base=process.env.LAB_URL??'http://127.0.0.1:3002';
const browser=await chromium.launch({headless:true});
const records=[];
try{
 for(const width of [390,1440]){
  const context=await browser.newContext({viewport:{width,height:1000}});await context.addCookies([{name:'sexsogate_adult',value:'yes',url:base}]);const page=await context.newPage();
  await page.addInitScript(()=>{
   window.__sexsogateLab={lcp:0,cls:0,interactionMax:0};
   new PerformanceObserver(list=>{for(const entry of list.getEntries())window.__sexsogateLab.lcp=entry.startTime;}).observe({type:'largest-contentful-paint',buffered:true});
   new PerformanceObserver(list=>{for(const entry of list.getEntries())if(!entry.hadRecentInput)window.__sexsogateLab.cls+=entry.value;}).observe({type:'layout-shift',buffered:true});
   new PerformanceObserver(list=>{for(const entry of list.getEntries())if(entry.interactionId)window.__sexsogateLab.interactionMax=Math.max(window.__sexsogateLab.interactionMax,entry.duration);}).observe({type:'event',buffered:true,durationThreshold:16});
  });
  await page.goto(base,{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(1200);
  await page.locator('.header-actions button').first().click();await page.keyboard.press('Escape');await page.waitForTimeout(300);
  const data=await page.evaluate(()=>({...window.__sexsogateLab,navigation:performance.getEntriesByType('navigation')[0].toJSON(),overflow:document.documentElement.scrollWidth>window.innerWidth}));
  records.push({width,lcpMs:Math.round(data.lcp),cls:Number(data.cls.toFixed(4)),observedInteractionMaxMs:data.interactionMax,overflow:data.overflow,ttfbMs:Math.round(data.navigation.responseStart)});await context.close();
 }
 await writeFile('docs/performance-report.json',JSON.stringify({recordedAt:new Date().toISOString(),url:base,environment:'Local production build, Chromium desktop engine, unthrottled localhost, one navigation sample per viewport',fieldData:false,inpFieldP75:null,note:'Observed interaction maximum is a small laboratory sample, not field INP. Real device Safari and field p75 remain unmeasured.',records},null,2));
 console.log(JSON.stringify(records));
}finally{await browser.close();}
