import {chromium,webkit} from '../../artifacts/qa/node_modules/playwright/index.mjs';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash,randomBytes} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import assert from 'node:assert/strict';
const origin=process.env.NODENO_SOCIAL_UI_URL;
assert.equal(origin,'https://127.0.0.1:4189');
const folder='artifacts/social-auth';await mkdir(folder,{recursive:true});
const sourceHash=createHash('sha256').update(await readFile('web/app.js')).digest('hex');
const sourceHashes=Object.fromEntries(await Promise.all(['web/app.js','web/styles.css','web/shop-i18n.js','web/index.html','web/assets/auth/google.png','web/assets/auth/apple.svg'].map(async file=>[file,createHash('sha256').update(await readFile(file)).digest('hex')])));
const runId=Date.now().toString(36);
const report={testOnly:true,sourceOverride:false,origin,appSha256:sourceHash,sourceHashes,providerSetupDeferred:true,checks:[],flows:[],errors:[]};
async function seedVerifiedSocialSession(context,scenario,lang){
 const preview=JSON.parse(await readFile('artifacts/social-auth/preview.json','utf8'));assert.equal(preview.testOnly,true);
 const storage=path.join(preview.temporaryRoot,scenario),cookie=(await context.cookies(origin)).find(c=>c.name==='NODENOSESSID');assert.ok(cookie);
 const browser=randomBytes(32).toString('hex'),identity={provider:'google',subject:'ui-sub-'+scenario+'-'+runId,email:`social-${scenario}-${runId}@example.test`,emailVerified:true,name:'Deniz Social'};
 const quote=value=>"'"+value.replaceAll('\\','\\\\').replaceAll("'","\\'")+"'";
 const program=`require ${quote(path.resolve('hosting/account.php'))};$input=json_decode($argv[1],true);$db=nodenoAccountDatabase($input['storage']);$flow=nodenoSocialCreateFlow($db,'google',['clientId'=>'fixture.apps.googleusercontent.com','callback'=>'https://nodenohome.com/api/account/oauth/google/callback'],['sessionId'=>$input['sessionId'],'browser'=>$input['browser'],'user'=>null,'intent'=>'login','locale'=>$input['locale']]);$data=nodenoSocialClaimFlow($db,$flow['state'],'google',$input['browser']);nodenoSocialSaveVerified($db,$flow['state'],$data,$input['identity']);echo json_encode(['state'=>$flow['state']]);`;
 const result=spawnSync(process.env.PHP_BINARY||'php',['-r',program,JSON.stringify({storage,identity,browser,locale:lang,sessionId:cookie.value})],{encoding:'utf8'});assert.equal(result.status,0,result.stderr||result.stdout);
 await context.addCookies([{name:'__Secure-NODENOOAUTH',value:browser,domain:'127.0.0.1',path:'/api/account/oauth',secure:true,httpOnly:true,sameSite:'None'}]);
 return JSON.parse(result.stdout).state;
}
for(const engine of ['chromium','webkit']){
 const browser=await(engine==='chromium'?chromium:webkit).launch({headless:true,executablePath:engine==='chromium'?'C:/Users/Hamza ÖZBALKAN/AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe':'C:/Users/Hamza ÖZBALKAN/Desktop/Nodeno/artifacts/runtime-browsers/webkit-2370/Playwright.exe'});
 try{
  for(const lang of ['tr','en','ru','ar']){
   const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,ignoreHTTPSErrors:true,extraHTTPHeaders:{'X-Nodeno-Test-Scenario':engine+'-'+lang}});
   const health=await(await context.request.get(origin+'/api/health')).json();assert.equal(health.testOnly,true);assert.equal(health.appSha256,sourceHash);
   const page=await context.newPage();page.on('pageerror',e=>report.errors.push(e.message));
   const requests=[];page.on('request',r=>{requests.push({method:r.method(),url:r.url()});});
   async function ready(){await page.locator('#social-auth-options[aria-busy=false]').waitFor();await page.waitForFunction(()=>{const images=[...document.querySelectorAll('.social-signin img')];return images.length===2&&images.every(img=>img.complete&&img.naturalWidth>0);});await page.locator('.social-signin img').evaluateAll(images=>Promise.all(images.map(image=>image.decode())));}
   async function frame(){const d=await page.evaluate(()=>({x:scrollX,w:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth}));assert.equal(d.x,0);assert.ok(d.doc<=d.w+1&&d.body<=d.w+1,JSON.stringify(d));}
   for(const width of [320,390,1366]){
    await page.setViewportSize({width,height:844});
    for(const route of ['login','register']){
     await page.goto(`${origin}/?page=${route}&lang=${lang}`,{waitUntil:'domcontentloaded'});await ready();
     for(const provider of ['google','apple']){assert.equal(await page.locator(`[data-social-login=${provider}]`).isDisabled(),true);assert.ok(await page.locator(`[data-social-login=${provider}] img`).evaluate(img=>img.complete&&img.naturalWidth>0));}
     await frame();report.checks.push({engine,lang,width,route,bothProvidersDisabled:true,emailFormAvailable:await page.locator('#field-email').isVisible(),noOverflow:true});
     if(width===390)await page.screenshot({path:`${folder}/ui-${engine}-${lang}-${route}.png`});
    }
   }
   await page.setViewportSize({width:390,height:844});await page.goto(origin+'/?page=register&lang='+lang,{waitUntil:'domcontentloaded'});await ready();
   const email=`auth-ui-${engine}-${lang}-${runId}@example.test`,password='Auth-UI-test-password-2026';
   await page.locator('#field-name').fill('Deniz Test');await page.locator('#field-email').fill(email);await page.locator('#field-password').fill(password);await page.locator('#field-repeatPassword').fill(password);await page.locator('[name=privacy]').check();
   await page.locator('#register-form button[type=submit]').click();await page.locator('#connected-accounts[aria-busy=false]').waitFor();
   assert.equal(await page.locator('#profile-form #field-email').inputValue(),email);
   for(const provider of ['google','apple'])assert.equal(await page.locator(`[data-social-link=${provider}]`).isDisabled(),true);
   assert.equal(await page.locator('#password-form [name=currentPassword]').count(),1);await frame();
   await page.locator('#connected-accounts').scrollIntoViewIfNeeded();await page.screenshot({path:`${folder}/ui-${engine}-${lang}-connected.png`});
   const old=await page.evaluate(()=>({cookie:document.cookie,storage:JSON.stringify({...localStorage})}));assert.ok(!old.cookie.includes('NODENOSESSID'));assert.ok(!old.storage.includes(password));
   const social=await(await context.request.get(origin+'/api/account/social')).json();assert.equal(social.providers.google.ready,false);assert.equal(social.providers.apple.ready,false);assert.equal(social.hasPassword,true);
   assert.equal(requests.filter(r=>!r.url.startsWith(origin)).length,0,'no Google or Apple calls before provider setup');
   await page.evaluate(async()=>{const session=await(await fetch('/api/account')).json();await fetch('/api/account/logout',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':session.csrfToken},body:'{}'});});
   await page.goto(origin+'/?page=login&lang='+lang,{waitUntil:'domcontentloaded'});await ready();
   const state=await seedVerifiedSocialSession(context,engine+'-'+lang,lang);
   await page.goto(origin+'/api/account/oauth/complete?flow='+state,{waitUntil:'domcontentloaded'});await page.locator('#connected-accounts[aria-busy=false]').waitFor();
   assert.equal(await page.locator('#password-form [name=currentPassword]').count(),0);assert.equal(await page.locator('#delete-account-form').count(),0);
   await page.locator('[data-action=social-focus-password]').click();assert.equal(await page.locator('#password-form #field-password').evaluate(e=>e===document.activeElement),true);
   const socialPassword='Social-browser-password-2026';await page.locator('#password-form #field-password').fill(socialPassword);await page.locator('#password-form #field-repeatPassword').fill(socialPassword);await page.locator('#password-form button').click();
   await page.locator('#password-form [name=currentPassword]').waitFor();assert.equal(await page.locator('#delete-account-form').count(),1);
   await page.locator('[data-social-unlink=google]').click();await page.locator('#social-dialog[open]').waitFor();await page.locator('#social-confirm-password').fill(socialPassword);await page.locator('#social-connect-form button[type=submit]').click();
   await page.locator('#social-dialog').waitFor({state:'hidden'});await page.locator('[data-social-link=google]').waitFor();assert.equal(await page.locator('#social-dialog-content input').count(),0);
   assert.equal(requests.filter(r=>!r.url.startsWith(origin)).length,0);
   const storageAfter=await page.evaluate(()=>JSON.stringify({...localStorage}));assert.ok(!storageAfter.includes(socialPassword));await frame();
   report.flows.push({engine,lang,registration:true,localPasswordPreserved:true,connectedAccountsDisabled:true,noExternalProviderRequests:true,noPasswordInBrowserStorage:true,socialProfilePasswordCreation:true,socialDisconnectWithPassword:true,verifiedIdentityFixture:true});
   await context.close();console.log(JSON.stringify(report.flows.at(-1)));
  }
 }catch(error){report.passed=false;report.failure=error.message;await writeFile(`${folder}/ui-report.json`,JSON.stringify(report,null,2));throw error;}
 finally{await browser.close();}
}
assert.deepEqual(report.errors,[]);report.passed=true;await writeFile(`${folder}/ui-report.json`,JSON.stringify(report,null,2));console.log(JSON.stringify({passed:true,testOnly:true,views:report.checks.length,accountFlows:report.flows.length,appSha256:sourceHash}));
