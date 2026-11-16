/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-home.mjs
 * Açıklama   : Ana sayfa seçimlerinin yayın, model tekilliği ve sunucu eşliğini doğrular.
 */
import test from 'node:test';import assert from 'node:assert/strict';import {spawnSync}from'node:child_process';import{fileURLToPath}from'node:url';import path from'node:path';
import {homeModel,categoryMembers,uniqueHomeProducts}from'../native-store/storefront/home-core.js';
const categories=[{id:'a',parentId:null},{id:'sg_lingerie',parentId:null},{id:'empty',parentId:null},{id:'child',parentId:'a'},{id:'grandchild',parentId:'child'}];
const item=(id,category,extra={})=>({id,modelId:id,categoryIds:[category],images:['/media/'+id+'/0'],...extra});
const products=[item('a1','grandchild'),item('a2','a'),...Array.from({length:24},(_,i)=>item('l'+i,'sg_lingerie')),item('hidden','a',{hidden:true}),item('draft','a',{published:false}),item('no-photo','a',{images:[]})],catalog={products,categories};
test('Sadece yayımlanmış görselli modeller seçilir',()=>assert.equal(uniqueHomeProducts(products).length,26));
test('Alt kategori ailesi ve döngü güvenli hesaplanır',()=>{assert.deepEqual(categoryMembers(products,categories,'a').map(p=>p.id),['a1','a2','hidden','draft','no-photo']);assert.equal(categoryMembers(products,[...categories,{id:'a',parentId:'grandchild'}],'a').length,5);});
test('Baskın tek kategori ilk rafı kaplamaz',()=>{const m=homeModel(catalog);assert.deepEqual(m.selection.slice(0,4).map(p=>p.id),['a1','l0','a2','l1']);assert.equal(new Set(m.selection.map(p=>p.modelId)).size,8);assert.equal(m.roots.length,2);});
test('Diğer raflar varsayılan durumda aynı modelleri tekrarlamaz',()=>{const m=homeModel(catalog),a=new Set(m.selection.map(p=>p.id)),b=new Set(m.lingerieProducts.map(p=>p.id));assert.ok(m.lingerieProducts.every(p=>!a.has(p.id)));assert.ok(m.discovery.every(p=>!a.has(p.id)&&!b.has(p.id)));});
test('Sekme yalnız seçilen kökün gerçek ürünlerini gösterir',()=>{const m=homeModel(catalog,{category:'a'});assert.deepEqual(m.discovery.map(p=>p.id),['a1','a2']);assert.equal(homeModel(catalog,{category:'not-public'}).selected,null);});
test('Taslak öne çıkan görseli ve bilinmeyen son ürün gizlenir',()=>{const m=homeModel(catalog,{featuredId:'hidden',recentIds:['l3','l3','hidden','unknown']});assert.ok(m.campaigns.every(v=>v.category));assert.deepEqual(m.recent.map(p=>p.id),['l3']);});
test('Boş katalogda sahte raf veya kampanya oluşmaz',()=>{const m=homeModel({products:[],categories});for(const k of ['selection','campaigns','discovery','roots','shortcuts'])assert.deepEqual(m[k],[]);});
test('İlk PHP yanıtı ve tarayıcı aynı ürün sırasını seçer',()=>{
 const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),php=process.platform==='win32'?path.join(root,'.local/php-runtime/php.exe'):'php';
 const code="require 'native-store/storefront/home-model.php';$v=json_decode(stream_get_contents(STDIN),true,512,JSON_THROW_ON_ERROR);echo json_encode(sexogateHomeModel($v['catalog'],$v['options']),JSON_THROW_ON_ERROR);";
 for(const options of [{},{category:'a'},{category:'sg_lingerie',featuredId:'l5'},{category:'unknown'}]){const r=spawnSync(php,['-r',code],{cwd:root,input:JSON.stringify({catalog,options}),encoding:'utf8'});assert.equal(r.status,0,r.stderr);const server=JSON.parse(r.stdout),client=homeModel(catalog,options);for(const field of ['selection','discovery','lingerieProducts','roots','shortcuts'])assert.deepEqual(server[field].map(p=>p.id),client[field].map(p=>p.id),field);assert.deepEqual(server.campaigns.map(v=>v.product.id),client.campaigns.map(v=>v.product.id));}
});
