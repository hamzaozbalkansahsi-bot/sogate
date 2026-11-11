/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/imports.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import { createHash } from 'node:crypto';
import { realpath, stat } from 'node:fs/promises';
import path from 'node:path';
import ExcelJS from 'exceljs';
import { parse } from 'csv-parse/sync';
import sax from 'sax';
import { fromBuffer, type ZipFile, type Entry } from 'yauzl';
import { z } from 'zod';
import { query, transaction, type Connection } from './db';
import { HttpError } from './security';
import {storage} from './providers/storage';
import type { Principal } from '../shared/contracts';

export interface ImportError {row:number;field:string;message:string;}
export interface ImportPreview {previewId:string;rows:ImportRow[];errors:ImportError[];valid:boolean;formatVersion:number;productCount:number;variantCount:number;}
const legacyFields=['sku','name','nameEn','category','priceMinor','material','image'] as const;
export const importFields=[...legacyFields,'productKey','variantName','variantNameEn','size','color','weightGrams','packageDimensions','barcode','brand','manufacturer','origin','costMinor','priceEurMinor','priceUsdMinor','priceGbpMinor','description','descriptionEn','care','careEn','warnings','warningsEn','warranty','hygieneSealed','documentRefs','supplierId','taxClass','batteryType','batteryCapacityMah','ingredients','measurements','liquid'] as const;
const fields=importFields;
type ImportField=typeof fields[number];
const required:readonly ImportField[]=['sku','name','nameEn','category','priceMinor','material'];
const xlsxMime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
const limits={file:2*1024*1024,rows:1000,columns:40,cell:2000,zipEntries:150,entry:4*1024*1024,inflated:16*1024*1024,ratio:100};
const optionalText=(max=2000)=>z.string().min(1).max(max).optional();
const minor=z.number().int().min(0).max(9_000_000_000_000);
const rowSchema=z.object({
 rowNumber:z.number().int().min(2).max(1001),sku:z.string().regex(/^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$/),name:z.string().min(1).max(200),nameEn:z.string().min(1).max(200),category:z.string().regex(/^[a-z0-9][a-z0-9-]{0,79}$/),priceMinor:minor,material:z.string().min(1).max(200),
 image:z.string().max(240).refine(value=>value===''||/^\/media\/[A-Za-z0-9][A-Za-z0-9._-]*\.(png|jpe?g|webp|svg)$/.test(value)||/^\/uploads\/[a-f0-9-]{36}\.webp$/.test(value)),
 productKey:z.string().regex(/^[\p{L}\p{N}][\p{L}\p{N}._-]{0,99}$/u).optional(),variantName:optionalText(200),variantNameEn:optionalText(200),size:optionalText(100),color:optionalText(100),weightGrams:z.number().int().min(0).max(10000000).optional(),
 packageDimensions:z.object({lengthCm:z.number().positive().max(10000),widthCm:z.number().positive().max(10000),heightCm:z.number().positive().max(10000)}).strict().optional(),barcode:z.string().regex(/^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$/).optional(),
 brand:optionalText(100),manufacturer:optionalText(300),origin:z.string().regex(/^[A-Z]{2}$/).optional(),costMinor:minor.optional(),priceEurMinor:minor.optional(),priceUsdMinor:minor.optional(),priceGbpMinor:minor.optional(),description:optionalText(),descriptionEn:optionalText(),care:optionalText(),careEn:optionalText(),warnings:optionalText(),warningsEn:optionalText(),warranty:optionalText(),hygieneSealed:z.boolean().optional(),liquid:z.boolean().optional(),
 documentRefs:z.array(z.string().regex(/^[A-Za-z0-9_-]{1,100}$/)).max(20).refine(value=>new Set(value).size===value.length).optional(),supplierId:optionalText(100),taxClass:optionalText(100),batteryType:optionalText(100),batteryCapacityMah:z.number().int().min(1).max(1000000).optional(),ingredients:optionalText(),measurements:optionalText(),
}).strict().superRefine((row,context)=>{if(Boolean(row.variantName)!==Boolean(row.variantNameEn))context.addIssue({code:'custom',path:[row.variantName?'variantNameEn':'variantName'],message:'Seçenek adını Türkçe ve İngilizce birlikte girin.'});});
export type ImportRow=z.infer<typeof rowSchema>;
const formatVersion=2;
const environment=()=>process.env.APP_ENV??'development';
const checksum=(rows:ImportRow[],actorId:string,sourceEnvironment:string,errors:unknown)=>createHash('sha256').update(JSON.stringify({formatVersion,actorId,sourceEnvironment,rows,errors})).digest('hex');
const groupKey=(row:ImportRow)=>row.productKey?`group:${row.productKey}`:`row:${row.rowNumber}`;
const groups=(rows:ImportRow[])=>{const result=new Map<string,ImportRow[]>();for(const row of rows){const key=groupKey(row);result.set(key,[...(result.get(key)??[]),row]);}return result;};
const productFields:readonly (keyof ImportRow)[]=['name','nameEn','category','material','image','brand','manufacturer','origin','supplierId','description','descriptionEn','care','careEn','warnings','warningsEn','warranty'];
function groupErrors(rows:ImportRow[]):ImportError[]{const errors:ImportError[]=[];for(const group of groups(rows).values())if(group.length>1){for(const row of group){if(!row.variantName||!row.variantNameEn)errors.push({row:row.rowNumber,field:'variantName',message:'Çok varyantlı grupta Türkçe ve İngilizce seçenek adı zorunlu.'});if(productFields.some(field=>JSON.stringify(row[field]??null)!==JSON.stringify(group[0][field]??null)))errors.push({row:row.rowNumber,field:'productKey',message:'Aynı ürün grubunda ürün bilgileri çelişiyor; bütün ürün alanlarını tutarlı girin.'});}}return errors;}
const formulaPrefix=(value:string)=>/^[\s\uFEFF]*[=+\-@\t\r\n]/u.test(value);
function fail(message:string,status=400,code='IMPORT_REJECTED'):never {throw new HttpError(status,message,code);}

function authorize(principal:Principal) {
  if(!principal || !principal.id || !['admin','catalog'].includes(principal.role) || principal.mfa!==true) fail('İçe aktarma için iki adımlı doğrulamalı katalog veya yönetici yetkisi gerekir.',403);
}
function decode(data:Buffer):string {
  try {return new TextDecoder('utf-8',{fatal:true}).decode(data);} catch {return fail('Dosya UTF-8 kodlamasında olmalıdır.');}
}

function inspectXml(data:Buffer,filename:string) {
  const parserOptions={xmlns:false,strictEntities:true,position:false};
  const parser=sax.parser(true,parserOptions);
  let depth=0,elements=0,worksheetRows=0,worksheetCells=0;
  const worksheet=filename.startsWith('xl/worksheets/');
  parser.ondoctype=()=>fail('DOCTYPE ve dış varlık içeren dosyalar kabul edilmez.');
  parser.onsgmldeclaration=()=>fail('XML varlık ve SGML yönergeleri kabul edilmez.');
  parser.onprocessinginstruction=instruction=>{if(instruction.name.toLowerCase()!=='xml')fail('XML işlem yönergeleri kabul edilmez.');};
  parser.onerror=error=>{throw error;};
  parser.onopentag=tag=>{
    if(++depth>64||++elements>100000)fail('XLSX XML karmaşıklığı güvenli sınırı aşıyor.');
    const name=tag.name.split(':').pop()!.toLowerCase();
    const attributes=Object.fromEntries(Object.entries(tag.attributes).map(([key,value])=>[key,typeof value==='string'?value:value.value]));
    if(name==='relationship') {
      let target=String(attributes.Target??attributes.target??'').trim();
      try {for(let i=0;i<2;i++){const decoded=decodeURIComponent(target);if(decoded===target)break;target=decoded;}}catch{fail('Dış bağlantı veya geçersiz ilişki hedefi kabul edilmez.');}
      if(/^[a-z][a-z\d+.-]*:/i.test(target)||target.startsWith('//')||target.includes('\\'))fail('Dış bağlantı içeren XLSX kabul edilmez.');
    }
    if(worksheet&&name==='row') {
      if(++worksheetRows>1001||!/^\d+$/.test(attributes.r??'')||Number(attributes.r)>1001)fail('En fazla 1000 ürün satırı kabul edilir.');
    }
    if(worksheet&&name==='c') {
      const match=/^([A-Z]{1,3})([1-9]\d*)$/.exec(attributes.r??'');
      if(!match||Number(match[2])>1001)fail('En fazla 1000 ürün satırı kabul edilir.');
      const column=[...match[1]].reduce((sum,char)=>sum*26+char.charCodeAt(0)-64,0);
      if(column>limits.columns||++worksheetCells>(limits.rows+1)*limits.columns)fail('En fazla 40 kolon kabul edilir.');
    }
    if(['f','hyperlink','externallink','externalreference'].includes(name)) fail('Formül, dış bağlantı ve hyperlink içeren XLSX kabul edilmez.');
    for(const [key,value] of Object.entries(attributes)) {
      if(key.split(':').pop()!.toLowerCase()==='targetmode' && value.toLowerCase()==='external') fail('Dış bağlantı içeren XLSX kabul edilmez.');
      if(key.toLowerCase()==='contenttype' && /macroenabled|vbaproject|activex|oleobject/i.test(value)) fail('Makro veya gömülü nesne içeren XLSX kabul edilmez.');
    }
  };
  parser.onclosetag=()=>{depth--;};
  try {parser.write(decode(data)).close();} catch(error) {if(error instanceof HttpError)throw error;fail('XLSX içindeki XML geçersiz.');}
}

// Bound central-directory metadata AND actual inflated bytes before ExcelJS load.
async function inspectArchive(buffer:Buffer):Promise<void> {
  await new Promise<void>((resolve,reject)=>{
    let archive:ZipFile|undefined,finished=false,totalDeclared=0,totalActual=0,count=0;
    const seen=new Set<string>();
    const stop=(error:unknown)=>{if(finished)return;finished=true;archive?.close();reject(error instanceof HttpError?error:new HttpError(400,'XLSX arşivi geçersiz veya güvenli sınırları aşıyor.'));};
    fromBuffer(buffer,{lazyEntries:true,validateEntrySizes:true,strictFileNames:true,autoClose:true},(error,zip)=>{
      if(error||!zip){stop(error);return;}archive=zip;
      if(zip.entryCount>limits.zipEntries){stop(new HttpError(400,'XLSX en fazla 150 arşiv girdisi içerebilir.'));return;}
      zip.on('error',stop);
      zip.on('end',()=>{if(finished)return;finished=true;resolve();});
      zip.on('entry',(entry:Entry)=>{
        if(finished)return;
        try {
          const name=entry.fileName;
          if(++count>limits.zipEntries || seen.has(name)) fail('Arşivde çok fazla veya tekrarlanan dosya var.');
          seen.add(name);
          if(name.includes('..')||name.includes('\\')||name.startsWith('/')||/^[A-Za-z]:/.test(name)) fail('Arşiv dosya yolu geçersiz.');
          if(entry.isEncrypted() || ![0,8].includes(entry.compressionMethod)) fail('Şifreli veya desteklenmeyen XLSX arşivi.');
          const unixType=(entry.externalFileAttributes>>>16)&0xf000;
          if(unixType===0xa000) fail('Arşivde sembolik bağlantı kabul edilmez.');
          totalDeclared+=entry.uncompressedSize;
          if(entry.uncompressedSize>limits.entry||totalDeclared>limits.inflated||entry.uncompressedSize>Math.max(1024,entry.compressedSize*limits.ratio)) fail('XLSX açılmış boyutu veya sıkıştırma oranı güvenli sınırı aşıyor.');
          if(name.endsWith('/')){zip.readEntry();return;}
          const allowed=/^(?:\[Content_Types\]\.xml|_rels\/\.rels|docProps\/(?:app|core)\.xml|xl\/(?:workbook\.xml|styles\.xml|sharedStrings\.xml|_rels\/workbook\.xml\.rels|worksheets\/sheet[1-9]\d*\.xml|worksheets\/_rels\/sheet[1-9]\d*\.xml\.rels|theme\/theme[1-9]\d*\.xml))$/;
          if(!allowed.test(name)) fail('Makro, gömülü nesne, resim veya desteklenmeyen arşiv içeriği var.');
          zip.openReadStream(entry,(streamError,stream)=>{
            if(streamError||!stream){stop(streamError);return;}
            let size=0;const chunks:Buffer[]=[];
            stream.on('error',stop);
            stream.on('data',(chunk:Buffer)=>{
              size+=chunk.length;totalActual+=chunk.length;
              if(size>limits.entry||totalActual>limits.inflated||size>entry.uncompressedSize){stream.destroy();stop(new HttpError(400,'XLSX gerçek açılmış boyutu güvenli sınırı aşıyor.'));return;}
              chunks.push(chunk);
            });
            stream.on('end',()=>{
              if(finished)return;
              try {if(size!==entry.uncompressedSize)fail('Arşiv boyutu doğrulanamadı.');inspectXml(Buffer.concat(chunks),name);zip.readEntry();} catch(cause){stop(cause);}
            });
          });
        } catch(cause){stop(cause);}
      });
      zip.readEntry();
    });
  });
}

async function readTable(buffer:Buffer,mime:string,filename:string):Promise<string[][]> {
  if(!buffer.length||buffer.length>limits.file)fail('Dosya boş olmamalı ve en fazla 2 MB olmalıdır.');
  if(!filename||filename.length>180||filename.includes('/')||filename.includes('\\')||[...filename].some(char=>char.charCodeAt(0)<32))fail('Dosya adı geçersiz.');
  const kind=path.extname(filename).toLowerCase();
  if(kind==='.csv') {
    if(!['text/csv','application/csv','application/vnd.ms-excel'].includes(mime.split(';')[0].trim().toLowerCase()))fail('CSV dosyasının türü geçersiz.');
    const text=decode(buffer);if(text.includes('\0')||/^\s*</.test(text))fail('CSV içerik türü geçersiz.');
    try {
      const first=parse(text,{bom:true,delimiter:',',record_delimiter:['\r\n','\n','\r'],skip_empty_lines:true,max_record_size:64000,to:1}) as string[][];
      const delimiter=first[0]?.length===1&&first[0][0].includes(';')?';':',';
      const rows=parse(text,{bom:true,delimiter,record_delimiter:['\r\n','\n','\r'],skip_empty_lines:true,max_record_size:64000,relax_column_count:false,cast:false,to:limits.rows+2,on_record:(record:string[])=>{if(record.length>limits.columns)fail('En fazla 40 kolon kabul edilir.');return record;}}) as string[][];
      if(rows.length>limits.rows+1)fail('En fazla 1000 ürün satırı içe aktarılabilir.');
      return rows;
    }catch(error){if(error instanceof HttpError)throw error;return fail('CSV satırları veya tırnak yapısı geçersiz.');}
  }
  if(kind!=='.xlsx'||mime!==xlsxMime||buffer.length<4||buffer.readUInt32LE(0)!==0x04034b50)fail('Yalnız doğrulanmış CSV veya XLSX dosyası kabul edilir.');
  await inspectArchive(buffer);
  try {
    const workbook=new ExcelJS.Workbook();await workbook.xlsx.load(buffer as unknown as Parameters<typeof workbook.xlsx.load>[0]);
    if(workbook.worksheets.length!==1)fail('XLSX dosyası yalnız bir çalışma sayfası içermelidir.');
    const sheet=workbook.worksheets[0];
    if(sheet.rowCount>limits.rows+1||sheet.columnCount>limits.columns)fail('En fazla 1000 satır ve 40 kolon kabul edilir.');
    const rows:string[][]=[];
    for(let number=1;number<=sheet.rowCount;number++) {
      const row:string[]=[];
      for(let column=1;column<=sheet.columnCount;column++) {
        const value=sheet.getRow(number).getCell(column).value;
        if(value===null||value===undefined)row.push('');
        else if(typeof value==='string'||typeof value==='number')row.push(String(value));
        else fail('XLSX hücreleri yalnız metin veya sayı olmalıdır; formül, bağlantı ve zengin içerik kabul edilmez.');
      }
      rows.push(row);
    }
    return rows;
  }catch(error){if(error instanceof HttpError)throw error;return fail('XLSX çalışma kitabı okunamadı.');}
}

export async function parseImportFile(buffer:Buffer,mime:string,filename:string,mapping:Record<string,string>={}):Promise<{rows:ImportRow[];errors:ImportError[]}> {
  if(!mapping || typeof mapping!=='object'||Array.isArray(mapping)||Object.entries(mapping).some(([field,value])=>!fields.includes(field as ImportField)||typeof value!=='string'||value.length>200))fail('Kolon eşlemesi geçersiz.');
  const table=await readTable(buffer,mime,filename);
  const header=table[0]?.map(cell=>cell.trim())??[];
  if(!header.length||header.length>limits.columns||header.some(cell=>!cell||cell.length>200||formulaPrefix(cell))||new Set(header).size!==header.length)fail('Kolon başlıkları boş, mükerrer veya geçersiz olamaz.');
  const errors:ImportError[]=[],rows:ImportRow[]=[],seen=new Set<string>();
  const mapped=new Map<ImportField,number>();
  for(const field of fields) {
    const index=header.indexOf(mapping[field]??field);
    if(index>=0)mapped.set(field,index);else if(required.includes(field))errors.push({row:1,field,message:'Zorunlu kolon eksik veya eşlenmemiş.'});
  }
  const used=new Set(mapped.values());
  if(used.size!==mapped.size)fail('Bir kaynak kolon birden fazla alana eşlenemez.');
  for(let index=1;index<table.length;index++) {
    const cells=table[index];if(cells.every(cell=>cell===''))continue;
    const number=index+1, get=(field:ImportField)=>cells[mapped.get(field)??-1]?.trim()??'';
    for(let col=0;col<cells.length;col++) {
      const field=[...mapped.entries()].find(([,source])=>source===col)?.[0]??header[col]??'kolon';
      if(cells[col].length>limits.cell)errors.push({row:number,field,message:'Hücre en fazla 2000 karakter olabilir.'});
      if(formulaPrefix(cells[col]))errors.push({row:number,field,message:'Formül veya tehlikeli hücre ön eki kabul edilmez.'});
      if([...cells[col]].some(char=>char.charCodeAt(0)<32&&!['\t','\n','\r'].includes(char)))errors.push({row:number,field,message:'Kontrol karakteri kabul edilmez.'});
      if(!used.has(col)&&cells[col]!=='')errors.push({row:number,field,message:'Bu kolon desteklenmiyor; veriyi kaldırın veya desteklenen alana eşleyin.'});
    }
    const price=get('priceMinor');const candidate:Record<string,unknown>={rowNumber:number,sku:get('sku'),name:get('name'),nameEn:get('nameEn'),category:get('category'),priceMinor:/^\d+$/.test(price)?Number(price):Number.NaN,material:get('material'),image:get('image')};
    const numeric=new Set(['weightGrams','costMinor','priceEurMinor','priceUsdMinor','priceGbpMinor','batteryCapacityMah']);
    for(const field of fields){if(legacyFields.includes(field as typeof legacyFields[number]))continue;const value=get(field);if(value==='')continue;
      if(numeric.has(field))candidate[field]=/^\d+$/.test(value)?Number(value):Number.NaN;
      else if(field==='hygieneSealed'||field==='liquid')candidate[field]=value==='true'?true:value==='false'?false:value;
      else if(field==='documentRefs')candidate[field]=value.split('|').map(part=>part.trim());
      else if(field==='packageDimensions'){try{candidate[field]=JSON.parse(value);}catch{candidate[field]=value;}}
      else candidate[field]=value;
    }
    const result=rowSchema.safeParse(candidate);
    if(!result.success)for(const issue of result.error.issues)errors.push({row:number,field:String(issue.path[0]),message:issue.path[0]==='image'?'Görsel yalnız yerel medya yolu olabilir; dış URL çekilmez.':issue.path[0]==='priceMinor'?'Fiyat 0–9000000000000 arasında tam sayı alt birim olmalıdır.':'Alan zorunluluğu, uzunluğu veya biçimi geçersiz.'});
    const sku=String(candidate.sku).toLocaleLowerCase('en-US');
    if(seen.has(sku))errors.push({row:number,field:'sku',message:'Dosyada aynı SKU birden fazla kez bulunuyor.'});seen.add(sku);
    rows.push(result.success?result.data:{...candidate,priceMinor:Number.isFinite(candidate.priceMinor)?candidate.priceMinor:0} as ImportRow);
  }
  if(!rows.length)errors.push({row:2,field:'sku',message:'En az bir ürün satırı gerekli.'});
  const barcodes=new Set<string>();for(const row of rows)if(row.barcode){if(barcodes.has(row.barcode))errors.push({row:row.rowNumber,field:'barcode',message:'Dosyada aynı barkod birden fazla varyantta kullanılmış.'});barcodes.add(row.barcode);}
  errors.push(...groupErrors(rows));
  return {rows,errors};
}

export function escapeImportCsvCell(value:string):string {
  const safe=formulaPrefix(value)?"'"+value:value;
  return '"'+safe.replaceAll('"','""')+'"';
}
export async function getImportTemplate(format:'csv'|'xlsx'='csv',mode:'legacy'|'extended'='legacy'):Promise<Buffer> {
  if(!['legacy','extended'].includes(mode))fail('Şablon kapsamı geçersiz.');const templateFields=mode==='extended'?fields:legacyFields;
  if(format==='csv')return Buffer.from('\uFEFF'+templateFields.join(',')+'\r\n','utf8');
  if(format!=='xlsx')fail('Şablon biçimi geçersiz.');
  const workbook=new ExcelJS.Workbook();workbook.creator='SEXSOGATE';
  const sheet=workbook.addWorksheet('Ürünler');sheet.addRow([...templateFields]);sheet.views=[{state:'frozen',ySplit:1}];
  sheet.getRow(1).font={bold:true,color:{argb:'FF5A0A20'}};
  for(let column=1;column<=templateFields.length;column++)sheet.getColumn(column).width=column===2||column===3?32:22;
  return Buffer.from(await workbook.xlsx.writeBuffer());
}

async function validateDatabaseRows(rows:ImportRow[],connection?:Connection):Promise<ImportError[]> {
 const errors:ImportError[]=[];const locked=connection?' FOR KEY SHARE':'';
 if(!(await query("SELECT id FROM warehouses WHERE id='main'"+locked,[],connection)).length)errors.push({row:1,field:'depo',message:'Ana depo kaydı bulunamadı. Depo kurulumunu tamamlayın; otomatik depo oluşturulmaz.'});
 const categories=new Set((await query<{slug:string}>('SELECT slug FROM categories WHERE active=true'+locked,[],connection)).map(row=>row.slug));
 const existing=new Set((await query<{sku:string}>('SELECT lower(sku) sku FROM variants WHERE lower(sku)=ANY($1::text[])',[rows.map(r=>r.sku.toLowerCase())],connection)).map(r=>r.sku));
 const barcodes=new Set((await query<{barcode:string}>('SELECT barcode FROM variants WHERE barcode=ANY($1::text[])',[rows.flatMap(r=>r.barcode?[r.barcode]:[])],connection)).map(r=>r.barcode));
 const brands=new Set((await query<{slug:string}>('SELECT slug FROM brands WHERE active=true'+locked,[],connection)).map(r=>r.slug));
 const suppliers=new Set((await query<{id:string}>('SELECT id FROM suppliers WHERE archived=false'+locked,[],connection)).map(r=>r.id));
 const refs=[...new Set(rows.flatMap(r=>r.documentRefs??[]))];const docs=new Set((await query<{id:string}>('SELECT id FROM product_documents WHERE id=ANY($1::text[])'+locked,[refs],connection)).map(r=>r.id));
 for(const row of rows){
  const add=(field:string,message:string)=>errors.push({row:row.rowNumber,field,message});
  if(!categories.has(row.category))add('category','Etkin kategori kaydı bulunamadı; önce kategori oluşturun.');
  if(existing.has(row.sku.toLowerCase()))add('sku','Bu SKU katalogda zaten bulunuyor.');
  if(row.barcode&&barcodes.has(row.barcode))add('barcode','Bu gerçek barkod başka varyantta kayıtlı.');
  if(row.brand&&!brands.has(row.brand))add('brand','Etkin marka bağlantı adı bulunamadı; otomatik marka oluşturulmaz.');
  if(row.supplierId&&!suppliers.has(row.supplierId))add('supplierId','Etkin tedarikçi kaydı bulunamadı.');
  if(row.documentRefs?.some(ref=>!docs.has(ref)))add('documentRefs','Mevcut belge kimliği bulunamadı; URL veya yeni belge otomatik oluşturulmaz.');
  if(row.image){let known=false;
   if(/^\/media\/[A-Za-z0-9][A-Za-z0-9._-]*\.(png|jpe?g|webp|svg)$/.test(row.image)){
    try{const root=await realpath(path.resolve('public/media')),file=await realpath(path.resolve('public','.'+row.image));known=file.startsWith(root+path.sep)&&(await stat(file)).isFile();}catch{/* Eksik dosya satır hatasıdır. */}
   }else if(/^\/uploads\/[a-f0-9-]{36}\.webp$/.test(row.image)){
    const objectKey=`products/${row.image.split('/').pop()}`;const [media]=await query<{rights_reference:string}>('SELECT rights_reference FROM media_assets WHERE object_key=$1 AND mime_type=\'image/webp\''+locked,[objectKey],connection);
    if((media?.rights_reference?.trim().length??0)>=5){known=true;if(process.env.STORAGE_PROVIDER!=='s3')try{known=(await storage().get(objectKey,{maxBytes:8*1024*1024,timeoutMs:5000})).length>0;}catch{known=false;}}
   }
   if(environment()==='production'&&/^\/media\/atelier-\d+\.svg$/.test(row.image))known=false;
   if(!known)add('image','Görsel bilinen ve hak kaynağı kayıtlı medyada bulunamadı veya bu ortamda kullanılamaz.');
  }
 }
 return errors;
}

export async function previewImport(buffer:Buffer,mime:string,filename:string,mapping:Record<string,string>|undefined,principal:Principal):Promise<ImportPreview>{
 authorize(principal);const parsed=await parseImportFile(buffer,mime,filename,mapping);parsed.errors.push(...await validateDatabaseRows(parsed.rows));
 const [record]=await query<{id:string}>('INSERT INTO import_preview(actor_id,rows,errors,sha256,format_version,source_environment) VALUES($1,$2,$3,$4,$5,$6) RETURNING id',[principal.id,JSON.stringify(parsed.rows),JSON.stringify(parsed.errors),checksum(parsed.rows,principal.id,environment(),parsed.errors),formatVersion,environment()]);
 return {previewId:record.id,...parsed,valid:parsed.errors.length===0,formatVersion,productCount:groups(parsed.rows).size,variantCount:parsed.rows.length};
}

export async function commitImport(previewId:string,principal:Principal):Promise<{previewId:string;created:number;variants:number;alreadyCommitted:boolean}>{
 authorize(principal);if(typeof previewId!=='string'||!/^[0-9a-f-]{36}$/i.test(previewId))fail('Önizleme kimliği geçersiz.');
 return transaction(async connection=>{
  const [preview]=await query<{id:string;actor_id:string;rows:unknown;errors:unknown;sha256:string;status:string;created_at:Date;format_version:number;source_environment:string}>('SELECT * FROM import_preview WHERE id=$1 FOR UPDATE',[previewId],connection);
  if(!preview||preview.actor_id!==principal.id)fail('Önizleme bulunamadı.',404);
  if(preview.format_version!==formatVersion||preview.source_environment!==environment())fail('Önizleme biçimi veya ortamı değişti; dosyayı yeniden yükleyin.',409);
  const decoded=z.array(rowSchema).min(1).max(limits.rows).safeParse(preview.rows);if(!decoded.success)fail('Önizleme verisi geçersiz.',409);const rows=decoded.data,grouped=groups(rows);
  if(checksum(rows,preview.actor_id,preview.source_environment,preview.errors)!==preview.sha256)fail('Önizleme bütünlüğü doğrulanamadı; dosyayı yeniden yükleyin.',409);
  const counts={previewId,created:grouped.size,variants:rows.length};if(preview.status==='committed')return {...counts,alreadyCommitted:true};
  if(preview.status!=='preview'||!Array.isArray(preview.errors)||preview.errors.length||groupErrors(rows).length)fail('Hatalı veya geçersiz önizleme onaylanamaz.',409);
  if(Date.now()-new Date(preview.created_at).getTime()>60*60*1000)fail('Önizleme süresi doldu; dosyayı yeniden yükleyin.',409);
  await connection.query("SET LOCAL lock_timeout='3s'; SET LOCAL statement_timeout='15s'");await connection.query('LOCK TABLE variants IN SHARE ROW EXCLUSIVE MODE');
  if((await validateDatabaseRows(rows,connection)).length)fail('Katalog önizlemeden sonra değişti; dosyayı yeniden yükleyip satır hatalarını inceleyin.',409);
  const imported=[];
  for(const group of grouped.values()){
   const row=group[0];const slug=row.name.toLocaleLowerCase('tr-TR').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replaceAll('ı','i').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,90)||'urun';
   const [product]=await query<{id:string}>("INSERT INTO products(slug,name,name_en,category,image,material,status,fixture,brand,manufacturer,origin,supplier_id,description,description_en,care,warnings,translations,attributes) VALUES($1,$2,$3,$4,$5,$6,'draft',$7,coalesce((SELECT name FROM brands WHERE slug=$8),''),$9,$10,$11,$12,$13,$14,$15,$16,$17) RETURNING id",[`${slug}-${previewId.slice(0,8)}-${row.rowNumber}`,row.name,row.nameEn,row.category,row.image,row.material,environment()!=='production',row.brand??null,row.manufacturer??null,row.origin??null,row.supplierId??null,row.description??'',row.descriptionEn??'',row.care??'',row.warnings??'',JSON.stringify({en:{care:row.careEn??'',warnings:row.warningsEn??''}}),JSON.stringify({...(row.warranty?{warranty:row.warranty}:{}),importFormatVersion:formatVersion})],connection);
   for(const item of group){
    const [variant]=await query<{id:string}>('INSERT INTO variants(product_id,sku,name,name_en,price_minor,cost_minor,currency,barcode,size,color,weight_grams,package_dimensions,hygiene_sealed,tax_class,battery_type,battery_capacity_mah,ingredients,measurements,liquid) VALUES($1,$2,$3,$4,$5,$6,\'TRY\',$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18) RETURNING id',[product.id,item.sku,item.variantName??'Standart',item.variantNameEn??'Standard',item.priceMinor,item.costMinor??0,item.barcode??null,item.size??null,item.color??null,item.weightGrams??0,item.packageDimensions?JSON.stringify(item.packageDimensions):null,item.hygieneSealed??false,item.taxClass??'*',item.batteryType??null,item.batteryCapacityMah??null,item.ingredients??null,item.measurements??null,item.liquid??false],connection);
    await query("INSERT INTO inventory_balance(variant_id,warehouse_id) VALUES($1,'main')",[variant.id],connection);
    for(const [currency,amount]of [['TRY',item.priceMinor],['EUR',item.priceEurMinor],['USD',item.priceUsdMinor],['GBP',item.priceGbpMinor]] as const)if(amount!==undefined)await query('INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES($1,$2,$3)',[variant.id,currency,amount],connection);
    for(const reference of item.documentRefs??[])await query('INSERT INTO catalog_import_document_links(variant_id,document_id,preview_id) VALUES($1,$2,$3)',[variant.id,reference,previewId],connection);
    imported.push({...item,productId:product.id,variantId:variant.id});
   }
  }
  await query('INSERT INTO import_batches(id,status,source,rows,errors,actor_id) VALUES($1,\'committed\',\'catalog-upload\',$2,\'[]\'::jsonb,$3)',[previewId,JSON.stringify(imported),principal.id],connection);
  await query('UPDATE import_preview SET status=\'committed\' WHERE id=$1',[previewId],connection);
  await query('INSERT INTO audit_log(actor_id,action,resource,resource_id,details) VALUES($1,\'catalog.import\',\'catalog\',$2,$3)',[principal.id,previewId,JSON.stringify({...counts,formatVersion,checksum:preview.sha256})],connection);
  return {...counts,alreadyCommitted:false};
 });
}
