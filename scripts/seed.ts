/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/seed.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import pg from "pg";
import { createHash } from "node:crypto";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const fixtureProducts=[
 {slug:"bordo-duyusal-maske",name:"Bordo Duyusal Maske",nameEn:"Burgundy Sensory Mask",category:"aksesuarlar",material:"Saten",price:89000,cost:29000,variant:"Bordo · Tek beden",description:"Yumuşak dokulu, ayarlanabilir bağcıklı sade bir aksesuar.",descriptionEn:"A softly textured accessory with an adjustable tie."},
 {slug:"atelier-saten-kimono",name:"Atelier Saten Gecelik",nameEn:"Atelier Satin Nightdress",category:"ic-giyim",material:"Saten",price:169000,cost:69000,variant:"Gül kurusu · M",description:"İnce askılı bir siluet ve sade saten doku.",descriptionEn:"A fine-strap silhouette with a simple satin texture."},
 {slug:"yakinlik-hediye-kutusu",name:"Yakınlık Hediye Kutusu",nameEn:"Intimacy Gift Box",category:"hediye-setleri",material:"Karton",price:125000,cost:45000,variant:"Bordo · Standart",description:"Özel anlar için yeniden kullanılabilir, kurdele detaylı hediye kutusu. İçerik seçimi ayrı yapılır.",descriptionEn:"A reusable gift box finished with a ribbon. Contents are selected separately."},
 {slug:"saten-saklama-kesesi",name:"Kadife Saklama Kesesi",nameEn:"Velvet Storage Pouch",category:"aksesuarlar",material:"Kadife",price:49000,cost:19000,variant:"Bordo · Standart",description:"Kişisel aksesuarlarınızı ayrı tutmak için bağcıklı saklama kesesi.",descriptionEn:"A drawstring velvet pouch to keep personal accessories separate."},
 {slug:"rose-ince-kurdele",name:"Yakınlık Aksesuar Halkaları",nameEn:"Closeness Accessory Rings",category:"cift-urunleri",material:"Metal",price:39000,cost:14000,variant:"Gül metalik · İkili",description:"Birlikte seçilen anlara eşlik eden, gül metalik tonlu bir çift aksesuar halkası.",descriptionEn:"A pair of rose-toned accessory rings for moments chosen together."},
 {slug:"krem-seyahat-cantasi",name:"Krem Bakım Şişesi",nameEn:"Cream Care Bottle",category:"bakim",material:"Cam",price:79000,cost:31000,variant:"Krem · Standart",description:"Kişisel bakım düzeniniz için sade bir şişe ambalajı. Kozmetik içerik içermez.",descriptionEn:"A simple bottle for your personal care arrangement. Contains no cosmetic formulation."}
];
export async function seedFixtureAddressProfile(client:Pick<pg.Client,'query'>,country='TR') {
 if(!['development','test'].includes(process.env.APP_ENV??''))throw new Error('Fixture address profile requires development or test');
 const exists=await client.query('SELECT fixture FROM country_rules WHERE code=$1',[country]);if(!exists.rows[0]?.fixture)throw new Error('Fixture address profile requires a fixture country');
 const fields=[
  {id:'fullName',label:{tr:'Ad soyad',en:'Full name'},required:true,minLength:2,maxLength:120,format:'text'},
  {id:'phone',label:{tr:'Telefon',en:'Phone'},required:true,minLength:7,maxLength:30,format:'text'},
  {id:'line1',label:{tr:'Adres',en:'Address'},required:true,minLength:5,maxLength:300,format:'text'},
  {id:'city',label:{tr:'Şehir',en:'City'},required:true,minLength:2,maxLength:100,format:'text'},
  {id:'postalCode',label:{tr:'Posta kodu',en:'Postal code'},required:true,minLength:3,maxLength:15,format:'text'},
 ];
 const result=await client.query("INSERT INTO country_address_profiles(country,version,fields,status,fixture,reference,created_by,approved_by,approved_at) SELECT $1,1,$2,'approved',true,'Yalnız izole geliştirme/test alanları; gerçek ülke onayı değildir','fixture-seed','fixture-seed',now() WHERE NOT EXISTS(SELECT 1 FROM country_address_profiles WHERE country=$1) ON CONFLICT DO NOTHING RETURNING id",[country,JSON.stringify(fields)]);
 return {id:result.rows[0]?.id as string|undefined,created:result.rows.length>0};
}
// Yalnız editoryal örnek içeriği yükler; ana seed girişinin DB/ortam kısıtları korunur.
export async function seedContent(client:Pick<pg.Client,'query'>) {
 if(!["development","test"].includes(process.env.APP_ENV??""))throw new Error("Fixture content requires development or test");
  const content=[
   ["rehber","tr","Yakınlığa alan açın","Kendinize ve birlikte paylaştığınız anlara zaman ayırın. Aksesuar seçerken malzeme, ölçü, bakım adımları ve üretici uyarılarını inceleyin. Sağlıkla ilgili sorularınız için bir uzmana danışın."],
   ["rehber","en","Make room for closeness","Take time for yourself and the moments you share. Review materials, sizing, care instructions and manufacturer warnings when choosing accessories. Consult a professional for health questions."],
   ["sss","tr","Sık sorulan sorular","Siparişimi nasıl takip ederim? Sipariş sonunda verilen güvenli bağlantıyı kullanabilirsiniz. İade süreci nasıl işler? Hesabınızdan veya güvenli sipariş bağlantınızdan başvuru yapabilirsiniz; ürün, mühür durumu ve geçerli kurallar incelenir."],
   ["sss","en","Frequently asked questions","How can I track my order? Use the secure link provided after checkout. How do returns work? Request a return through your account or secure order link. Product condition, seal and applicable rules will be reviewed."],
   ["iletisim","tr","Size yardımcı olalım","Siparişinizle ilgili yardım için güvenli sipariş sayfanızı kullanın. İletişim bilgileri işletme kurulumu tamamlandığında yayımlanır."],
   ["iletisim","en","How can we help?","For order assistance, use your secure order page. Contact details will be published after business setup is complete."]
  ];
  for(const [slug,locale,title,body]of content){
   const kind=slug==="sss"?"faq":slug==="home-campaign"?"campaign":slug==="iletisim"?"page":"guide";
   const inserted=await client.query("INSERT INTO content_pages(slug,locale,title,body,status,kind,fixture) VALUES($1,$2,$3,$4,'published',$5,true) ON CONFLICT DO NOTHING RETURNING id",[slug,locale,title,body,kind]);
   if(inserted.rows.length)await client.query("INSERT INTO content_revisions(page_id,version,title,body,status,kind,publish_at) SELECT id,version,title,body,status,kind,publish_at FROM content_pages WHERE id=$1 ON CONFLICT DO NOTHING",[inserted.rows[0].id]);
  }
}

export async function seed(databaseUrl=process.env.DATABASE_URL) {
 if(!["development","test"].includes(process.env.APP_ENV??""))throw new Error("Fixture seed is only allowed in development or test");
 if(!databaseUrl || !/^\/sexsogate_(dev|test)$/.test(new URL(databaseUrl).pathname))throw new Error("Fixture seed requires a dedicated sexsogate_dev or sexsogate_test database");
 const client=new pg.Client({connectionString:databaseUrl});await client.connect();
 try {
  await client.query("BEGIN");
  for(const [slug,name,nameEn]of[["aksesuarlar","Aksesuarlar","Accessories"],["ic-giyim","İç Giyim","Lingerie"],["hediye-setleri","Hediye Setleri","Gift Sets"],["cift-urunleri","Çift Ürünleri","For Couples"],["bakim","Bakım","Care"],["oyuncaklar","Oyuncaklar","Toys"]]) {
   await client.query("INSERT INTO categories(slug,name,name_en) VALUES($1,$2,$3) ON CONFLICT DO NOTHING",[slug,name,nameEn]);
  }
  await client.query("INSERT INTO warehouses(id,name) VALUES('main','Ana Depo') ON CONFLICT DO NOTHING");
  await client.query("INSERT INTO warehouse_locations(warehouse_id,code) VALUES('main','A-01') ON CONFLICT DO NOTHING");
  await client.query("INSERT INTO country_rules(code,name,enabled,product_approved,age_approved,payment_approved,shipping_approved,tax_approved,legal_approved,shipping_minor,currency,fixture) VALUES('TR','Türkiye',true,true,true,true,true,true,true,6900,'TRY',true) ON CONFLICT DO NOTHING");
  await client.query("INSERT INTO country_rules(code,name) VALUES('DE','Almanya'),('GB','Birleşik Krallık'),('US','Amerika Birleşik Devletleri'),('AE','Birleşik Arap Emirlikleri') ON CONFLICT DO NOTHING");
  await seedFixtureAddressProfile(client);
  await client.query("INSERT INTO tax_rules(country,rate_bps,valid_from,fixture) SELECT 'TR',2000,'2026-01-01',true WHERE NOT EXISTS(SELECT 1 FROM tax_rules WHERE country='TR')");
  for(const [index,p] of fixtureProducts.entries()) {
   const sku=`LOCAL-${String(index+1).padStart(3,'0')}`;
   const variantNameEn=['Burgundy · One size','Dusty rose · M','Burgundy · Standard','Burgundy · Standard','Rose metal · Pair','Cream · Standard'][index];
   const translations={en:{warnings:'For adults only. Check the manufacturer instructions before use.',care:'Check the care label before use. Store separately in a dry place.'}};
   const existing=await client.query('SELECT p.id,p.fixture FROM products p LEFT JOIN variants v ON v.product_id=p.id WHERE p.slug=$1 OR v.sku=$2 LIMIT 1',[p.slug,sku]);
   if(existing.rows.length){if(existing.rows[0].fixture){await client.query('UPDATE products SET name=$2,name_en=$3,description=$4,description_en=$5,material=$6,translations=$7,updated_at=now() WHERE id=$1 AND fixture=true',[existing.rows[0].id,p.name,p.nameEn,p.description,p.descriptionEn,p.material,JSON.stringify(translations)]);await client.query('UPDATE variants SET name=$2,name_en=$3 WHERE product_id=$1 AND sku=$4',[existing.rows[0].id,p.variant,variantNameEn,sku]);}continue;}
   const product=await client.query("INSERT INTO products(slug,name,name_en,description,description_en,category,image,material,status,warnings,care,fixture,translations) VALUES($1,$2,$3,$4,$5,$6,$7,$8,'published',$9,$10,true,$11) RETURNING id",[p.slug,p.name,p.nameEn,p.description,p.descriptionEn,p.category,`/media/atelier-0${index+1}.svg`,p.material,"Yalnız yetişkinler içindir. Üretici kullanım bilgileri kontrol edilmelidir.","Kullanımdan önce bakım etiketini kontrol edin. Ayrı ve kuru bir yerde saklayın.",JSON.stringify(translations)]);
   const variant=await client.query("INSERT INTO variants(product_id,sku,name,name_en,price_minor,cost_minor) VALUES($1,$2,$3,$4,$5,$6) RETURNING id",[product.rows[0].id,sku,p.variant,variantNameEn,p.price,p.cost]);
   const id=variant.rows[0].id;
   await client.query("INSERT INTO inventory_balance(variant_id,warehouse_id,on_hand,minimum_stock) VALUES($1,'main',$2,3)",[id,12+index*3]);
   await client.query("INSERT INTO inventory_movements(variant_id,warehouse_id,type,quantity,reason,reference) VALUES($1,'main','receipt',$2,'İzole geliştirme başlangıcı',$3)",[id,12+index*3,`seed:${id}`]);
   await client.query("INSERT INTO product_eligibility(variant_id,country,approved,review_note,approved_by,approved_at) VALUES($1,'TR',true,'Yalnız izole geliştirme senaryosu','fixture-seed',now())",[id]);
   await client.query("INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES($1,'TRY',$2)",[id,p.price]);
  }
  await seedContent(client);
  for(const locale of ["tr","en"])for(const kind of ["privacy","terms"]) {
   const title=locale==="tr"?(kind==="terms"?"Mesafeli satış koşulları":"Gizlilik ve aydınlatma"):kind==="terms"?"Distance sales terms":"Privacy notice";
   const body=locale==="tr"?"Güvenli Alışveriş — Bu metin yalnız izole test sözleşmesidir. Hukuki satıcı, teslimat, iade ve kişisel veri koşulları yetkili hukuk incelemesinden sonra yayımlanır.":"Private Shopping — This agreement is an isolated test fixture. Seller, delivery, returns and privacy terms require authorised legal review before publication.";
   await client.query("INSERT INTO legal_documents(kind,locale,title,body,version,status,body_hash,effective_at,fixture) VALUES($1,$2,$3,$4,1,'effective',$5,now(),true) ON CONFLICT DO NOTHING",[kind,locale,title,body,createHash("sha256").update(body).digest("hex")]);
  }
  for(const [key,value]of[["seller.name",""],["seller.taxNumber",""],["seller.address",""],["seller.supportEmail",""],["seller.phone",""],["seller.bankAccount",""],["launch.backupVerified",false],["launch.securityReviewed",false],["launch.legalApproved",false],["launch.catalogVerified",false],["launch.providerApproved",false]])await client.query("INSERT INTO settings(key,value) VALUES($1,$2) ON CONFLICT DO NOTHING",[key,JSON.stringify(value)]);
  await client.query("COMMIT");console.log("Local fixture catalog created; production fixture seed is prohibited.");
 }catch(error){await client.query("ROLLBACK");throw error;}finally{await client.end();}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href)seed().catch(()=>{console.error("Fixture seed refused or failed. Check environment and dedicated database.");process.exitCode=1;});
