import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {summarizeSpecs,groupSpecs} from '../web/product-specs.js';

const localized=(tr,en=tr,ru=tr,ar=tr)=>({tr,en,ru,ar});
const spec=(label,value)=>({label:localized(label),value:typeof value==='string'?localized(value):value});

test('explicit source axis order produces compact width, height and depth without changing numbers',()=>{
 const input=[spec('Ürün Ölçüleri','91 x 105 x 37 cm ( Genişlik x Yükseklik x Derinlik )')];
 assert.deepEqual(summarizeSpecs(input,'tr'),[
  {key:'width',labelKey:'dimensionWidth',value:'91 cm'},
  {key:'height',labelKey:'dimensionHeight',value:'105 cm'},
  {key:'depth',labelKey:'dimensionDepth',value:'37 cm'},
 ]);
 const range=summarizeSpecs([spec('Ürün Ölçüleri','64,5 × 112-120 × 65.5 cm (GxYxD)')],'en');
 assert.deepEqual(range.map(row=>row.value),['64,5 cm','112-120 cm','65.5 cm']);
});

test('axis names are never guessed from number position or a conflicting order',()=>{
 for(const value of ['91 x 105 x 37 cm','91 x 105 x 37 cm (YxGxD)','91 x 105 cm (GxYxD)','91 x 105 x 37 x 2 cm (GxYxD)','91 x 105 x 37 mm (GxYxD)','0 x 105 x 37 cm (GxYxD)']){
  const input=[spec('Ürün Ölçüleri',value)],summary=summarizeSpecs(input,'tr');
  assert.ok(summary.every(row=>!['width','height','depth'].includes(row.key)),value);
  assert.deepEqual(summary,[{key:'dimensions',label:'Ürün Ölçüleri',value}],value);
 }
});

test('locale-specific facts remain complete and the summary stays within six useful facts',()=>{
 const input=[
  spec('Ürün Ölçüleri','91x105x37 cm (GxYxD)'),
  {label:localized('Ürün Rengi','Colour','Цвет','اللون'),value:localized('Mat Beyaz','Matt white','Матовый белый','أبيض مطفي')},
  spec('Ürün Malzemesi',localized('16 mm Yonga Levha','16 mm particleboard','ДСП 16 мм','خشب حبيبي 16 مم')),
  spec('Koli bilgisi',localized('Ürün 2 koliden oluşmaktadır.','2 packages','2 упаковки','عبوتان')),
  spec('Ürün Rengi','İkinci renk kaydı'),spec('Ürün Malzemesi','İkinci malzeme kaydı'),
  spec('Ürün Özellikleri','25 çift ayakkabı, terlik kapasitesi\n4 adet hareketli raf'),
 ];
 const before=JSON.stringify(input);
 for(const lang of ['tr','en','ru','ar']){
  const result=summarizeSpecs(input,lang);
  assert.equal(result.length,6);
  assert.equal(result.find(row=>row.key==='color').value,input[1].value[lang]);
  assert.equal(result.find(row=>row.key==='material').value,input[2].value[lang]);
  assert.equal(result.find(row=>row.key==='packaging').value,input[3].value[lang]);
  assert.equal(new Set(result.map(row=>row.key)).size,result.length);
 }
 assert.equal(JSON.stringify(input),before);
});

test('long or multiline prose is left intact for full specifications rather than clipped into a fact',()=>{
 const long='Ürünün teknik bilgisini oluşturan uzun açıklama. '.repeat(5);
 const input=[spec('Ürün Rengi','Beyaz\nFarklı renk açıklaması'),spec('Ürün Malzemesi',long),spec('Koli Bilgisi','Ürün iki koliden oluşur.\nİçerik ayrıca belirtilmiştir.'),spec('Ürün Özellikleri','Kapak hariç, yalnız gardırop gövdesidir.')];
 const before=JSON.stringify(input);
 assert.deepEqual(summarizeSpecs(input,'tr'),[]);
 const grouped=groupSpecs(input);
 assert.strictEqual(grouped.features[0].spec,input[3]);
 assert.equal(JSON.stringify(input),before);
});

test('full grouping preserves source objects and indexes exactly once, including label variants',()=>{
 const input=[
  spec('Ürün Ölçüleri','80x90x30 cm'),spec('Koli bilgisi','2 koli'),spec('Ürün Özellikler','Açık arka yüz'),
  spec('Ürün Malezemesi','18 mm Yonga Levha'),spec('Ürün Kurulumu','2 kişi tavsiye edilir.'),
  spec('Bakım ve Temizlik','Nemli bezle temizleyin.'),spec('Ürün Notu','Özel kaynak notu.'),
  spec('Ürün Rengi','Beyaz'),spec('Ürün Malzemesi','Metal ayak'),null,
 ];
 const groups=groupSpecs(input),flat=Object.values(groups).flat();
 assert.deepEqual(Object.keys(groups),['attributes','features','materials','assembly','care','other']);
 assert.deepEqual(groups.attributes.map(row=>row.index),[0,1,7]);
 assert.deepEqual(groups.materials.map(row=>row.index),[3,8]);
 assert.equal(flat.length,input.length);
 assert.deepEqual(flat.map(row=>row.index).sort((a,b)=>a-b),input.map((_,index)=>index));
 for(const row of flat)assert.strictEqual(row.spec,input[row.index]);
});

test('every genuine catalogue technical row survives grouping without source mutation',async()=>{
 const source=JSON.parse(await readFile(new URL('../data/catalog-source.json',import.meta.url),'utf8'));
 const before=JSON.stringify(source);
 for(const product of source.products){
  const rows=product.specs||[],groups=groupSpecs(rows),flat=Object.values(groups).flat();
  assert.equal(flat.length,rows.length,product.id);
  assert.deepEqual(flat.map(row=>row.index).sort((a,b)=>a-b),rows.map((_,index)=>index),product.id);
  for(const row of flat)assert.strictEqual(row.spec,rows[row.index],product.id);
  for(const lang of ['tr','en','ru','ar'])assert.ok(summarizeSpecs(rows,lang).length<=6,product.id+'/'+lang);
 }
 assert.equal(JSON.stringify(source),before);
});

test('missing inputs and absent translations neither invent facts nor throw',()=>{
 assert.deepEqual(summarizeSpecs(undefined,'ar'),[]);
 assert.deepEqual(Object.values(groupSpecs(null)).flat(),[]);
 assert.deepEqual(summarizeSpecs([null,{label:{en:'Colour'},value:{en:'White'}}],'en'),[]);
 const row=spec('Ürün Rengi','Beyaz');
 assert.equal(summarizeSpecs([row],'unknown')[0].value,'Beyaz');
});
