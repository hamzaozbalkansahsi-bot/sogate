/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/test-native-categories.mjs
 * Açıklama   : Kategori filtrelerinin Türkçe eşleşme ve aktif varyant kurallarını sınar.
 */
import test from 'node:test';import assert from 'node:assert/strict';
import {facetValues,matchesFacets,catalogFacets,appliedFacetCount} from '../native-store/storefront/category-core.js';
const product={id:'p',modelId:'model',brand:'İpek',facts:{materials:'Pamuk'},variantSelection:{mode:'matrix',axes:[{id:'size',values:[{id:'s',label:'S'},{id:'xl',label:'XL'}]},{id:'color',values:[{id:'black',label:'Siyah'},{id:'pink',label:'Pembe'}]}],variants:[{active:true,values:{size:'s',color:'pink'}},{active:true,values:{size:'xl',color:'black'}},{active:false,values:{size:'xl',color:'pink'}}]}};
test('Aktif matriste bulunmayan beden ve renk birlikte eşleşmez',()=>{assert.equal(matchesFacets(product,{size:'XL',color:'Pembe'}),false);assert.equal(matchesFacets(product,{size:'XL',color:'Siyah'}),true);assert.equal(matchesFacets(product,{size:'XL'}),true);});
test('Türkçe büyük küçük harf ve özgün etiketler korunur',()=>{assert.equal(matchesFacets(product,{brand:'ipek',color:'sİyah'}),true);assert.equal(catalogFacets([product]).brand[0].value,'İpek');assert.equal(matchesFacets({...product,brand:'Iğdır'},{brand:'ığdır'}),true);});
test('Seçenek modunda bağımsız beden ve renk değerleri çalışır',()=>{assert.equal(matchesFacets({...product,variantSelection:{...product.variantSelection,mode:'options'}},{size:'XL',color:'Pembe'}),true);});
test('Filtre adetleri model bazında tekilleştirilir',()=>{assert.equal(catalogFacets([product,{...product,id:'p2'}]).size.find(v=>v.value==='XL').count,1);assert.equal(appliedFacetCount({brand:'İpek',size:'XL',minPrice:'1',maxPrice:'2'}),3);});
test('Seçili beden renk seçeneklerini aktif birleşimlere daraltır',()=>{assert.deepEqual(catalogFacets([product],'tr',{size:'XL'}).color,[{value:'Siyah',count:1}]);assert.deepEqual(catalogFacets([product,{...product,id:'other',brand:'Diğer'}],'tr',{brand:'İpek'}).size.map(v=>v.count),[1,1]);});
test('Belirsiz malzeme paragrafı filtre seçeneği yapılmaz',()=>{assert.deepEqual(facetValues({...product,facts:{materials:'Ürünün hijyenik ve doğal yapısının daha uzun süre korunması için kaliteli malzemelerden üretilmiştir'}},'material'),[]);assert.deepEqual(facetValues(product,'material'),['Pamuk']);});
test('İnaktif varyantlar, boş değer ve incelemedeki renk filtreye girmez',()=>{assert.deepEqual(facetValues({...product,variantSelection:{...product.variantSelection,variants:[]}},'size'),[]);assert.deepEqual(facetValues({colorReviewPending:true,variantColor:{tr:'Siyah'}},'color'),[]);assert.equal(matchesFacets(product,{size:'XXXL'}),false);});
