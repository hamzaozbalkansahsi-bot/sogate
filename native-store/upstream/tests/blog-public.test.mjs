import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
const php=path.resolve('artifacts/runtime-php/php.exe');
const fixture=path.resolve('tests/fixtures/blog-public.php');
function run(action){const r=spawnSync(php,[fixture,action],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);return JSON.parse(r.stdout);}
test('article output escapes editorial text and uses real published date in schema',()=>{
 const {html}=run('article');assert.ok(html.includes('&lt;script&gt;'));assert.ok(!html.includes('<script>alert'));
 const ld=[...html.matchAll(/<script[^>]*type="application\/ld\+json"[^>]*>(.*?)<\/script>/gs)].map(x=>JSON.parse(x[1]));
 const article=ld.flat().find(x=>x['@type']==='BlogPosting');assert.equal(article.datePublished,'2026-11-12T09:31:00+03:00');assert.equal(article.inLanguage,'tr');assert.ok(article.mainEntityOfPage.endsWith('/blog/olcu-plani'));
});
test('sitemap exposes only supplied published IDs and real available language variants',()=>{
 const {xml}=run('sitemap');assert.ok(xml.includes('/blog/olcu-plani'));assert.ok(!xml.includes('future-draft'));assert.ok(!xml.includes('/blog/olcu-plani?lang=ru'));assert.ok(xml.includes('2026-11-12T09:31:00+03:00'));
});
test('search and pagination canonical avoid duplicate indexable searches',()=>{
 const {html}=run('search');assert.ok(html.includes('noindex,follow'));assert.ok(html.includes('name="q"'));assert.ok(html.includes('value="raf &amp; dolap"'));
});
test('Arabic shell sets RTL and calculator labels are localized',()=>{
 const {html}=run('arabic');assert.ok(html.includes('lang="ar" dir="rtl"'));assert.ok(html.includes('حساب كمية الطلاء'));assert.ok(!html.includes('>Oda genişliği<'));
});
test('language alternates retain equivalent tools, categories and pagination',()=>{
 const tool=run('tool-alternates').html;assert.ok(tool.includes('hreflang="en" href="https://nodenohome.com/blog?lang=en&amp;tool=paint"'));
 const category=run('category-alternates').html;assert.ok(category.includes('lang=en&amp;category=planning&amp;pg=2'));assert.ok(category.includes('<title>Ölçü ve planlama'));
 const article=run('article-tool').html;assert.ok(article.includes('rel="canonical" href="https://nodenohome.com/blog/olcu-plani"'));
});
