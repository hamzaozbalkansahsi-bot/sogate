/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/imports.test.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import { describe, expect, it } from 'vitest';
import ExcelJS from 'exceljs';
import { deflateRawSync } from 'node:zlib';
import { commitImport, escapeImportCsvCell, getImportTemplate, parseImportFile, previewImport } from '../../src/server/imports';

const headers = 'sku,name,nameEn,category,priceMinor,material,image';
const valid = 'SG-OLCU,Ölçü ve Özellikler,Measurements and details,aksesuarlar,10001,Tekstil,/media/atelier-01.svg';
const csv = (line = valid) => Buffer.from('\uFEFF' + headers + '\r\n' + line + '\r\n', 'utf8');
const mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

describe('Gruplu katalog ve ileri alanlar',()=>{
 it('eski şablonu korurken aynı productKey altında gerçek varyant alanlarını çözer',async()=>{
  const content=headers+',productKey,variantName,variantNameEn,size,color,weightGrams,packageDimensions,barcode,costMinor,priceEurMinor,hygieneSealed\n'+valid+',İÇ-GİYİM,Bordo M,Burgundy M,M,Bordo,120,"{""lengthCm"":20,""widthCm"":15,""heightCm"":3}",8690000000001,3000,2500,true\n'+valid.replace('SG-OLCU','SG-L')+',İÇ-GİYİM,Bordo L,Burgundy L,L,Bordo,130,"{""lengthCm"":20,""widthCm"":15,""heightCm"":3}",8690000000002,3200,2600,true';
  const result=await parseImportFile(Buffer.from(content),'text/csv','group.csv');expect(result.errors).toEqual([]);expect(result.rows).toHaveLength(2);expect(result.rows[0]).toMatchObject({productKey:'İÇ-GİYİM',variantNameEn:'Burgundy M',size:'M',barcode:'8690000000001',costMinor:3000,priceEurMinor:2500,hygieneSealed:true});
 });
 it('aynı grupta çelişen ürün içeriğini ve belirsiz varyant adlarını satır hatası gösterir',async()=>{
  const result=await parseImportFile(Buffer.from(headers+',productKey\n'+valid+',GROUP\n'+valid.replace('SG-OLCU','SG-L').replace('Ölçü ve Özellikler','Farklı ürün')+',GROUP'),'text/csv','group.csv');expect(result.errors.some(e=>e.field==='productKey')).toBe(true);expect(result.errors.some(e=>e.field==='variantName')).toBe(true);
 });
 it('tek satırda da yalnız bir dilde seçenek adı verilirse diğer dili uydurmaz',async()=>{
  const tr=await parseImportFile(Buffer.from(headers+',variantName\n'+valid+',Bordo'),'text/csv','names.csv');expect(tr.errors.some(e=>e.field==='variantNameEn')).toBe(true);
  const en=await parseImportFile(Buffer.from(headers+',variantNameEn\n'+valid+',Burgundy'),'text/csv','names.csv');expect(en.errors.some(e=>e.field==='variantName')).toBe(true);
 });
 it('ileri JSON/sayı/boolean biçimini doğrular; stok ve lot bayraklarını kabul etmez',async()=>{
  const result=await parseImportFile(Buffer.from(headers+',weightGrams,hygieneSealed,packageDimensions,stock,lotTracking\n'+valid+',1.2,belki,"{""unit"":""inch""}",12,true'),'text/csv','invalid.csv');for(const field of ['weightGrams','hygieneSealed','packageDimensions','stock','lotTracking'])expect(result.errors.some(e=>e.field===field)).toBe(true);
 });
 it('kayıtlı özel medya yolunu biçim olarak kabul eder, dış görsel adresini kabul etmez',async()=>{
  expect((await parseImportFile(csv(valid.replace('/media/atelier-01.svg','/uploads/12345678-1234-1234-1234-123456789abc.webp')),'text/csv','media.csv')).errors).toEqual([]);expect((await parseImportFile(csv(valid.replace('/media/atelier-01.svg','https://example.test/item.png')),'text/csv','media.csv')).errors.some(e=>e.field==='image')).toBe(true);
 });
 it('geniş CSV/XLSX şablonları 40 kolon sınırını korur ve gerçek XLSX grup alanlarını kayıpsız okur',async()=>{
  const template=await getImportTemplate('xlsx','extended'),book=new ExcelJS.Workbook();await book.xlsx.load(template as unknown as Parameters<typeof book.xlsx.load>[0]);const sheet=book.worksheets[0];expect(sheet.columnCount).toBeLessThanOrEqual(40);const names=(sheet.getRow(1).values as string[]).slice(1);expect(names).toContain('productKey');expect(names).toContain('priceGbpMinor');const base:Record<string,string>={sku:'XLSX-İC'.replace('İ','I'),name:'İç Giyim Ölçüsü',nameEn:'Lingerie size',category:'aksesuarlar',priceMinor:'10001',material:'Tekstil',productKey:'ÖLÇÜ',variantName:'Bordo M',variantNameEn:'Burgundy M',size:'M',hygieneSealed:'false',packageDimensions:JSON.stringify({lengthCm:20,widthCm:10,heightCm:2})};sheet.addRow(names.map(name=>base[name]??''));const parsed=await parseImportFile(Buffer.from(await book.xlsx.writeBuffer()),mime,'group.xlsx');expect(parsed.errors).toEqual([]);expect(parsed.rows[0]).toMatchObject({productKey:'ÖLÇÜ',hygieneSealed:false,packageDimensions:{lengthCm:20,widthCm:10,heightCm:2}});expect((await getImportTemplate('csv','extended')).toString()).toContain('supplierId');
 });
});

function crc32(data:Buffer) {
  let crc = 0xffffffff;
  for (const byte of data) {
    crc ^= byte;
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
  }
  return (crc ^ 0xffffffff) >>> 0;
}
// Independent ZIP fixture builder: dangerous archives never need ExcelJS to parse.
function zip(entries:{name:string;content:string;declaredSize?:number}[]) {
  const locals:Buffer[] = [], central:Buffer[] = [];
  let offset = 0;
  for (const entry of entries) {
    const name = Buffer.from(entry.name), raw = Buffer.from(entry.content), compressed = deflateRawSync(raw), crc = crc32(raw);
    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50); local.writeUInt16LE(20,4); local.writeUInt16LE(8,8); local.writeUInt32LE(crc,14);
    local.writeUInt32LE(compressed.length,18); local.writeUInt32LE(entry.declaredSize??raw.length,22); local.writeUInt16LE(name.length,26);
    locals.push(local,name,compressed);
    const directory = Buffer.alloc(46);
    directory.writeUInt32LE(0x02014b50); directory.writeUInt16LE(20,4); directory.writeUInt16LE(20,6); directory.writeUInt16LE(8,10);
    directory.writeUInt32LE(crc,16); directory.writeUInt32LE(compressed.length,20); directory.writeUInt32LE(entry.declaredSize??raw.length,24);
    directory.writeUInt16LE(name.length,28); directory.writeUInt32LE(offset,42);
    central.push(directory,name); offset += local.length + name.length + compressed.length;
  }
  const centralBuffer = Buffer.concat(central), end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50); end.writeUInt16LE(entries.length,8); end.writeUInt16LE(entries.length,10);
  end.writeUInt32LE(centralBuffer.length,12); end.writeUInt32LE(offset,16);
  return Buffer.concat([...locals,centralBuffer,end]);
}

async function workbookBuffer(value:unknown = 'SG-XLSX') {
  const workbook = new ExcelJS.Workbook(), sheet = workbook.addWorksheet('Ürünler');
  sheet.addRow(headers.split(','));
  sheet.addRow([value,'Ölçü ve Özellikler','Measurements and details','aksesuarlar',10001,'Tekstil','/media/atelier-01.svg']);
  return Buffer.from(await workbook.xlsx.writeBuffer());
}

describe('Katalog içe aktarma dosya sınırları', () => {
  it('UTF-8 BOM ve Türkçe metni fiyatı alt birimde koruyarak okur', async () => {
    const result = await parseImportFile(csv(),'text/csv','urunler.csv');
    expect(result.errors).toEqual([]);
    expect(result.rows[0]).toMatchObject({sku:'SG-OLCU',name:'Ölçü ve Özellikler',priceMinor:10001,material:'Tekstil'});
  });
  it('tırnak içindeki virgül ve çift tırnakları gerçek CSV kurallarıyla okur', async () => {
    const result = await parseImportFile(csv(valid.replace('Ölçü ve Özellikler','"Ölçü, ""Özel"" Ürün"')),'text/csv','urunler.csv');
    expect(result.rows[0].name).toBe('Ölçü, "Özel" Ürün');
  });
  it('Türkçe kolon adlarını açık eşlemeyle kabul eder', async () => {
    const result = await parseImportFile(Buffer.from('Kod;Ad;English;Kategori;Fiyat;Malzeme\nSG-1;İç Giyim;Lingerie;aksesuarlar;12000;Tekstil'), 'text/csv', 'liste.csv', {sku:'Kod',name:'Ad',nameEn:'English',category:'Kategori',priceMinor:'Fiyat',material:'Malzeme'});
    expect(result.errors).toEqual([]); expect(result.rows[0].name).toBe('İç Giyim');
  });
  it.each(['=HYPERLINK("x")',' +cmd','-10','@SUM(A1)','\tUrun','\rUrun'])('formül enjeksiyonu hücresini reddeder: %s', async (value) => {
    const line = valid.replace('Ölçü ve Özellikler','"' + value.replaceAll('"','""') + '"');
    const result = await parseImportFile(csv(line),'text/csv','urunler.csv');
    expect(result.errors.some(error=>error.field==='name' && /formül/i.test(error.message))).toBe(true);
  });
  it('dosya içindeki mükerrer SKU ve geçersiz fiyatı satır bazında gösterir', async () => {
    const result = await parseImportFile(csv(valid+'\n'+valid+'\n'+valid.replace('SG-OLCU','SG-OTHER').replace('10001','1.5')),'text/csv','urunler.csv');
    expect(result.errors.some(error=>error.row===3 && error.field==='sku')).toBe(true);
    expect(result.errors.some(error=>error.row===4 && error.field==='priceMinor')).toBe(true);
  });
  it('uzak görsel URLsi ve eşlenmeyen kolon verisini sessizce içe almaz', async () => {
    const remote = await parseImportFile(csv(valid.replace('/media/atelier-01.svg','http://127.0.0.1/secret')),'text/csv','urunler.csv');
    expect(remote.errors.some(error=>error.field==='image')).toBe(true);
    const extra = await parseImportFile(Buffer.from(headers+',stock\n'+valid+',100'),'text/csv','urunler.csv');
    expect(extra.errors.some(error=>error.field==='stock')).toBe(true);
  });
  it('eksik zorunlu kolonları ve tekrarlanan başlıkları reddeder', async () => {
    const missing = await parseImportFile(Buffer.from('sku,name\nSG-1,Ürün'),'text/csv','liste.csv');
    expect(missing.errors.some(error=>error.row===1 && error.field==='nameEn')).toBe(true);
    await expect(parseImportFile(Buffer.from('sku,sku\nA,B'),'text/csv','liste.csv')).rejects.toThrow();
  });
  it('2MB, 1000 satır, hücre uzunluğu, UTF8 ve tür sınırlarını uygular', async () => {
    await expect(parseImportFile(Buffer.alloc(2*1024*1024+1),'text/csv','big.csv')).rejects.toThrow();
    await expect(parseImportFile(csv(Array.from({length:1001},(_,i)=>valid.replace('SG-OLCU','SG-'+i)).join('\n')),'text/csv','big.csv')).rejects.toThrow();
    const long = await parseImportFile(csv(valid.replace('Ölçü ve Özellikler','a'.repeat(2001))),'text/csv','liste.csv');
    expect(long.errors.length).toBeGreaterThan(0);
    await expect(parseImportFile(Buffer.from([0xff,0xfe,0x61]),'text/csv','invalid.csv')).rejects.toThrow();
    await expect(parseImportFile(csv(),'image/png','image.png')).rejects.toThrow();
    await expect(parseImportFile(csv(),mime,'fake.xlsx')).rejects.toThrow();
  });
  it('gerçek XLSX metin ve sayı hücrelerini okur', async () => {
    const result = await parseImportFile(await workbookBuffer(),mime,'urunler.xlsx');
    expect(result.errors).toEqual([]); expect(result.rows[0]).toMatchObject({sku:'SG-XLSX',name:'Ölçü ve Özellikler',priceMinor:10001});
  });
  it('XLSX formül ve hyperlink hücrelerini parser yüklemesinden önce reddeder', async () => {
    await expect(parseImportFile(await workbookBuffer({formula:'1+1',result:2}),mime,'formula.xlsx')).rejects.toThrow();
    await expect(parseImportFile(await workbookBuffer({text:'SG-LINK',hyperlink:'https://example.invalid'}),mime,'link.xlsx')).rejects.toThrow();
  });
  it('arşiv boyutu/oranı, macro, embedded, path traversal ve XXE dosyalarını reddeder', async () => {
    const dangerous = [
      zip([{name:'xl/workbook.xml',content:'<workbook/>',declaredSize:5*1024*1024}]),
      zip([{name:'xl/workbook.xml',content:'a'.repeat(200000)}]),
      zip([{name:'xl/vbaProject.bin',content:'macro'}]),
      zip([{name:'xl/embeddings/a.bin',content:'ole'}]),
      zip([{name:'../secret.xml',content:'<x/>'}]),
      zip([{name:'xl/workbook.xml',content:'<!DOCTYPE x [<!ENTITY leak SYSTEM "file:///secret">]><x>&leak;</x>'}]),
      zip([{name:'xl/_rels/workbook.xml.rels',content:'<Relationships><Relationship TargetMode="&#69;xternal" Target="http://127.0.0.1"/></Relationships>'}]),
      zip([{name:'[Content_Types].xml',content:'<Types><Override ContentType="application/vnd.ms-excel.sheet.macroEnabled.main+xml"/></Types>'}]),
    ];
    for (const data of dangerous) await expect(parseImportFile(data,mime,'unsafe.xlsx')).rejects.toThrow();
  });
  it('seyrek ama devasa XLSX satır ve kolon indekslerini parser yüklemesinden önce engeller', async () => {
    const row=zip([{name:'xl/worksheets/sheet1.xml',content:'<worksheet><sheetData><row r="9999999"><c r="A9999999"><v>1</v></c></row></sheetData></worksheet>'}]);
    await expect(parseImportFile(row,mime,'sparse.xlsx')).rejects.toThrow('1000');
    const col=zip([{name:'xl/worksheets/sheet1.xml',content:'<worksheet><sheetData><row r="1"><c r="XFD1"><v>1</v></c></row></sheetData></worksheet>'}]);
    await expect(parseImportFile(col,mime,'wide.xlsx')).rejects.toThrow('40');
  });
  it('TargetMode yazılmasa da uzak ilişki hedefini XML önkontrolünde reddeder',async()=>{
    const rel=zip([{name:'xl/_rels/workbook.xml.rels',content:'<Relationships><Relationship Target="https://example.invalid/private"/></Relationships>'}]);
    await expect(parseImportFile(rel,mime,'external.xlsx')).rejects.toThrow('Dış bağlantı');
  });
  it('CSV ve XLSX şablonu ürün üretmeden yalnız kolon başlıkları taşır', async () => {
    expect((await getImportTemplate('csv')).toString('utf8').replace(/^\uFEFF/,'').trim()).toBe(headers);
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.load(await getImportTemplate('xlsx') as unknown as Parameters<typeof workbook.xlsx.load>[0]);
    expect(workbook.worksheets).toHaveLength(1); expect(workbook.worksheets[0].rowCount).toBe(1);
    expect(workbook.worksheets[0].getRow(1).getCell(2).value).toBe('name');
  });
  it('CSV dışa aktarma formül ön eklerini etkisizleştirir', () => {
    expect(escapeImportCsvCell('=1+1')).toBe('"\'=1+1"');
    expect(escapeImportCsvCell('Ölçü, "özel"')).toBe('"Ölçü, ""özel"""');
  });
  it('önizleme ve onayı katalog/yönetici MFA yetkisiyle sınırlar', async () => {
    for (const principal of [{id:'x',role:'warehouse' as const,mfa:true},{id:'x',role:'catalog' as const,mfa:false}]) {
      await expect(previewImport(csv(),'text/csv','liste.csv',{},principal)).rejects.toThrow();
      await expect(commitImport('some-preview',principal)).rejects.toThrow();
    }
  });
});
