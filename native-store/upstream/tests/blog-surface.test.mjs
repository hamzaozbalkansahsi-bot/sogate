import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {assessSurface, mountSurfaceTools} from '../web/blog-surface.js';

const base={material:'wood',finish:'bare',exposure:'dry-interior',condition:'sound'};
const choices={material:['wood','mdf','veneer','metal','plastic','ceramic','unknown'],finish:['bare','coated','unknown'],exposure:['dry-interior','water','exterior','unknown'],condition:['sound','peeling','damp','unknown']};
function forms(locales){
 const php=process.env.PHP_BINARY||process.env.NODENO_PHP||path.resolve('artifacts/runtime-php/php.exe');
 const code='require $argv[1]; echo json_encode(array_map(fn($locale)=>nodenoBlogSurfaceForm($locale),json_decode(stream_get_contents(STDIN),true)),JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR);';
 const r=spawnSync(php,['-r',code,path.resolve('hosting/blog-surface.php')],{input:JSON.stringify(locales),encoding:'utf8'});
 assert.equal(r.status,0,r.stderr||r.error?.message);return JSON.parse(r.stdout);
}
function copyFrom(html){
 const raw=html.match(/data-surface-copy="([^"]+)"/)?.[1];assert.ok(raw,'Localized text must be safely embedded');
 return JSON.parse(raw.replaceAll('&quot;','"').replaceAll('&#039;',"'").replaceAll('&lt;','<').replaceAll('&gt;','>').replaceAll('&amp;','&'));
}

test('all complete choices give a verification plan, never product approval',()=>{
 for(const material of choices.material)for(const finish of choices.finish)for(const exposure of choices.exposure)for(const condition of choices.condition){
  const result=assessSurface({material,finish,exposure,condition});
  assert.equal(result.verificationRequired,true);assert.ok(result.steps.length>=4);assert.equal(new Set(result.steps).size,result.steps.length);
  assert.ok(result.steps.includes('verify-product'));assert.ok(result.steps.includes('representative-sample'));
  assert.ok(!['ready','approved','safe'].includes(result.status));
 }
 assert.deepEqual(base,{material:'wood',finish:'bare',exposure:'dry-interior',condition:'sound'});
});
test('unknown choices identify each missing fact and invalid values cannot produce a plan',()=>{
 const result=assessSurface({material:'unknown',finish:'unknown',exposure:'unknown',condition:'unknown'});
 assert.equal(result.status,'identify-first');
 for(const key of ['identify-material','identify-finish','identify-exposure','inspect-condition'])assert.ok(result.steps.includes(key));
 for(const input of [undefined,null,[],{},'wood',{...base,material:'<script>'},{...base,finish:'laminate-proof'},{...base,exposure:0},{...base,condition:'diagnosed'}])assert.throws(()=>assessSurface(input),RangeError);
});
test('moisture and loose coatings take priority over colour or product selection',()=>{
 const damp=assessSurface({...base,material:'mdf',condition:'damp'});assert.equal(damp.status,'moisture-first');assert.equal(damp.steps[0],'moisture-source');assert.ok(damp.steps.includes('check-stability'));
 const peeling=assessSurface({...base,finish:'unknown',condition:'peeling'});assert.equal(peeling.status,'stability-first');assert.equal(peeling.steps[0],'loose-finish');assert.ok(peeling.steps.includes('identify-finish'));
});
test('material and exposure branches retain their own practical checks',()=>{
 for(const [material,step]of [['wood','wood-system'],['mdf','mdf-edges'],['veneer','thin-veneer'],['metal','metal-system'],['plastic','plastic-system'],['ceramic','ceramic-system']])assert.ok(assessSurface({...base,material}).steps.includes(step));
 assert.ok(assessSurface({...base,finish:'coated'}).steps.includes('existing-finish'));
 assert.ok(assessSurface({...base,exposure:'water'}).steps.includes('water-system'));
 assert.ok(assessSurface({...base,exposure:'exterior'}).steps.includes('exterior-system'));
});
test('PHP form provides four labelled native selects, safe copy and isolated binding in all languages',()=>{
 const htmls=forms(['tr','en','ru','ar','invalid-locale','tr']);const ids=[];
 htmls.forEach((html,index)=>{
  assert.match(html,/class="blog-tool/);assert.match(html,/data-blog-surface/);assert.ok(!html.includes('data-blog-tool='));
  assert.equal((html.match(/<select\b/g)||[]).length,4);assert.match(html,/<output\b/);assert.match(html,/<ol\b[^>]*data-surface-steps/);
  assert.match(html,/aria-live="polite"/);assert.match(html,/<button\b[^>]*data-surface-submit[^>]*disabled/);assert.ok(!/onclick=|onchange=|<script\b|style=/i.test(html));
  for(const name of Object.keys(choices)){
   const select=html.match(new RegExp('<select\\b[^>]*name="'+name+'"[^>]*>'))?.[0];assert.ok(select);
   const id=select.match(/id="([^"]+)"/)?.[1];assert.ok(id);assert.ok(html.includes('<label for="'+id+'">'));ids.push(id);
  }
  assert.ok(html.includes(index===3?'dir="rtl"':'dir="ltr"'));
  const copy=copyFrom(html);
  for(const material of choices.material)for(const finish of choices.finish)for(const exposure of choices.exposure)for(const condition of choices.condition){
   const plan=assessSurface({material,finish,exposure,condition});assert.equal(typeof copy.statuses[plan.status],'string');
   for(const step of plan.steps)assert.ok(copy.steps[step]?.trim(),step);
  }
 });
 assert.equal(ids.length,new Set(ids).size,'Multiple tool instances must not share label IDs');
 assert.match(htmls[0],/Yüzey ön kontrolü/);assert.match(htmls[1],/Surface pre-check/);assert.match(htmls[2],/Проверка поверхности/);assert.match(htmls[3],/فحص أولي للسطح/);
 assert.match(htmls[4],/lang="tr"/);
});
test('mount updates text and list safely, handles invalid input and binds each form once',()=>{
 const copy=copyFrom(forms(['tr'])[0]);const listeners={};const output={textContent:'',dataset:{},focus(){this.focused=true;}};
 const list={children:[],replaceChildren(...nodes){this.children=nodes;}};const button={disabled:true};
 const fields=Object.fromEntries(Object.entries(base).map(([key,value])=>[key,{value,attributes:{},setAttribute(k,v){this.attributes[k]=v;},removeAttribute(k){delete this.attributes[k];}}]));
 const form={dataset:{surfaceCopy:JSON.stringify(copy)},elements:{namedItem:name=>fields[name]},ownerDocument:{createElement:()=>({textContent:''})},querySelector:selector=>selector==='[data-surface-status]'?output:selector==='[data-surface-steps]'?list:selector==='[data-surface-submit]'?button:null,addEventListener:(name,fn)=>{listeners[name]=fn;}};
 const root={querySelectorAll:()=>[form]};assert.equal(mountSurfaceTools(root),1);assert.equal(mountSurfaceTools(root),0);
 assert.equal(button.disabled,false);assert.equal(output.dataset.surfaceState,'verification-required');assert.ok(list.children.length>=4);assert.ok(list.children.every(x=>x.textContent));
 fields.condition.value='damp';listeners.change();assert.equal(output.dataset.surfaceState,'moisture-first');assert.equal(list.children[0].textContent,copy.steps['moisture-source']);
 fields.material.value='<img src=x onerror=alert(1)>';listeners.change();assert.equal(output.dataset.surfaceState,'invalid');assert.equal(list.children.length,0);assert.equal(output.textContent,copy.invalidSelection);assert.equal(fields.material.attributes['aria-invalid'],'true');
 fields.material.value='mdf';let prevented=false;listeners.submit({preventDefault(){prevented=true;}});assert.equal(prevented,true);assert.equal(fields.material.attributes['aria-invalid'],undefined);assert.equal(output.dataset.surfaceState,'moisture-first');
 assert.equal(mountSurfaceTools(),0,'Import and mounting remain safe outside a browser');
 const js=readFileSync(new URL('../web/blog-surface.js',import.meta.url),'utf8');assert.ok(!/innerHTML|\beval\s*\(|\bfetch\s*\(/.test(js));
});
