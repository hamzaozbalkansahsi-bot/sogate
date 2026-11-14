/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/seed-php-guides.mjs
 * Açıklama   : Yetkili test CMS'ine özgün TR/EN rehberleri ekler; mevcut yazıları değiştirmez.
 */
import {chromium} from 'playwright';
import {readFile,writeFile,rename} from 'node:fs/promises';
import {createHmac} from 'node:crypto';
const remote=process.argv.includes('--remote'),base=remote?'https://sexogate.com/test':'http://127.0.0.1:3183/test',origin=new URL(base).origin,access=JSON.parse(await readFile(remote?'.local/php-stage-access.json':'.local/php-access.json','utf8')),stateFile=remote?'.local/php-editorial-seed-remote.json':'.local/php-editorial-seed-local.json';
let state={};try{state=JSON.parse(await readFile(stateFile,'utf8'));}catch{}
function otp(secret){let bits='';for(const c of secret)bits+='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'.indexOf(c).toString(2).padStart(5,'0');const key=Buffer.from(bits.match(/.{8}/g).map(b=>parseInt(b,2))),t=Buffer.alloc(8);t.writeBigUInt64BE(BigInt(Math.floor(Date.now()/30000)));const h=createHmac('sha1',key).update(t).digest(),offset=h[19]&15;return ((h.readUInt32BE(offset)&0x7fffffff)%1000000).toString().padStart(6,'0');}
const entries=[
 ['tr','beden-tablosunu-okumak','Beden tablosunu doğru okumak','Etiketteki bedenden önce ürünün kendi ölçü tablosuna bakın.','Alışveriş rehberi',`## Her ürünün tablosu ayrı olabilir
Aynı beden adı, farklı marka veya modellerde aynı ölçüyü ifade etmeyebilir. Seçtiğiniz ürünün sayfasındaki üretici tablosunu esas alın. Başka bir üründeki ölçüyü otomatik olarak uygulamayın.

## Ölçü birimini kontrol edin
Tabloda santimetre mi, başka bir birim mi kullanıldığını kontrol edin. Vücut ölçüsü ile ürünün düz zemindeki ölçüsü farklı bilgidir. Tablonun hangisini gösterdiği açık değilse sipariş vermeden önce sorun.

## Seçeneği son kez gözden geçirin
Ürün sayfasında beden ve rengi seçtikten sonra sepetteki seçenek adını yeniden kontrol edin. Aynı ürünün farklı seçenekleri sepette birleştirilirse toplam adet değişebilir; sipariş özetindeki miktarı da inceleyin.

## Bilgi eksikse tahmin etmeyin
Ölçü, kumaş veya kalıp bilgisi yayımlanmamışsa bu özellikleri ürüne atfetmeyin. İletişim adresimize ürün bağlantısı ve öğrenmek istediğiniz ölçüyle yazabilirsiniz. Mahrem fotoğraf veya kimlik belgesi göndermeniz gerekmez.`],
 ['tr','urun-bakiminda-uretici-talimati','Ürün bakımında önce üretici talimatı','Temizlik, saklama ve şarj bilgilerini modelin kendi belgesinden doğrulayın.','Ürün bilgileri',`## Model bilgisini eşleştirin
Kutu veya kılavuzdaki model adıyla ürün kaydını karşılaştırın. Benzer görünen iki ürünün malzemesi, elektronik yapısı veya bakım yöntemi farklı olabilir. Başka bir modelin talimatını doğrudan uygulamayın.

## Malzeme adından sonuç çıkarmayın
Malzemenin adı tek başına suya dayanıklılık, belirli bir temizleyiciye uygunluk veya sertifika kanıtı değildir. Yalnız üreticinin açıkça belirttiği yöntemleri ve uyumluluk bilgilerini esas alın. Açıklanmayan bir özelliği var kabul etmeyin.

## Elektronik ürünlerde sınırları koruyun
Şarj cihazı, pil, temizleme ve sıvıyla temas konusunda ilgili modelin talimatlarını izleyin. Bağlantı noktası veya kapak bulunması tek başına su geçirmezlik anlamına gelmez. Eksik belgeyi kullanımdan önce üretici veya destek kanalı üzerinden sorun.

## Saklama bilgisini kontrol edin
Üreticinin belirttiği sıcaklık, saklama ve ambalaj koşullarını izleyin. Lot ya da son kullanma bilgisi bulunan ürünlerde bu alanları kontrol edin. Hasarlı veya şüpheli bir üründe kullanımı durdurup sipariş kaydınızdan destek isteyin.`],
 ['tr','guvenli-siparis-takibi','Sipariş bağlantınızı güvenle saklayın','Siparişinizi izlerken ve destek alırken paylaşmanız gerekmeyen bilgiler.','Mahremiyet',`## Bağlantı kişisel erişim sağlar
Misafir siparişlerinde ayrıntılar güvenli takip bağlantısıyla açılır. Bu bağlantıyı herkese açık bir gönderiye veya gruba eklemeyin. Sipariş numarası tek başına ayrıntılara erişim sağlamaz; özel bağlantıyı yine de kişisel bilgi gibi koruyun.

## Destek mesajını kısa tutun
Sipariş numarası, ilgili ürün satırı ve sorunun kısa açıklaması başlangıç için yeterlidir. Kart numarası, CVV, hesap parolası, kimlik belgesi veya mahrem kullanım görüntüsü göndermeyin. Başvuru için gerekli ek bilgi olursa amaç ve yöntem ayrıca açıklanmalıdır.

## Paketleri ayrı ayrı izleyin
Bir sipariş farklı paketlerde hazırlanabilir. Sipariş ekranındaki gerçek taşıyıcı ve takip kaydını kontrol edin. Kısmi sevk, bütün siparişin teslim edildiği anlamına gelmez. Eksik teslimatta hangi paketin veya ürün satırının eksik olduğunu belirtin.

## İade adımlarını ayırın
İade talebinin alınması, ürünün teslim alınması, kalite incelemesi ve para iadesi ayrı durumlardır. Güncel sonucu güvenli sipariş ekranından izleyin. Gönderim yapmadan önce başvurunuza verilen adres ve yöntemi kullanın.`],
 ['en','reading-size-charts','How to read a size chart','Check the product’s own measurements before relying on a size label.','Shopping guide',`## Use the chart for the exact product
The same size label can represent different measurements across brands and models. Use the manufacturer’s chart for the item you selected rather than carrying over a size from another product.

## Check the units and measurement type
Check whether the chart uses centimetres or another unit. Body measurements and flat garment measurements are different. If the chart does not explain which is shown, ask before placing an order.

## Review the selected option
After selecting a size and colour, check the option name again in your cart. Combining options of the same product can change the quantity, so review the order summary too.

## Ask when information is missing
Do not assume a fit, fabric or measurement that has not been provided. Email us with the product link and the detail you need. There is no need to send intimate photographs or identity documents.`],
 ['en','manufacturer-care-instructions','Start with the manufacturer’s care instructions','Confirm cleaning, storage and charging details for the exact model.','Product information',`## Match the model
Compare the model on the packaging or manual with the product record. Similar-looking products can have different materials, electronics and care requirements. Do not automatically apply another model’s instructions.

## Do not infer features from a material name
A material name alone does not establish water resistance, cleaner compatibility or certification. Follow the methods and compatibility information explicitly stated by the manufacturer. An undocumented feature should not be assumed.

## Check electronic product limits
Follow the model’s instructions for charging, batteries, cleaning and liquid contact. A cover or connector does not by itself establish waterproofing. Ask for missing documentation before use.

## Review storage information
Follow the manufacturer’s stated storage, temperature and packaging conditions. Check lot and expiry details where provided. Stop using a damaged or questionable item and request support through your order record.`],
 ['en','keeping-order-links-private','Keep your order link private','Information you do and do not need to share when tracking an order.','Privacy',`## Treat the link as private access
Guest order details open through a secure tracking link. Do not post that link publicly or in a group. An order number alone does not grant access, but the private link still needs to be protected.

## Keep support messages focused
The order number, relevant item and a brief description are enough to start. Do not send card numbers, CVV, passwords, identity documents or intimate usage images. Any further information request should explain its purpose and method.

## Track packages individually
An order may be prepared in separate packages. Check the real carrier and tracking record on the order screen. A partial shipment does not mean the whole order has arrived. Identify the missing package or item when reporting an issue.

## Separate the return stages
A return request, physical receipt, quality review and refund are separate stages. Follow the current status on the secure order screen. Use the address and method supplied for your request before sending an item back.`]
];
async function persist(){await writeFile(stateFile+'.tmp',JSON.stringify(state,null,2));await rename(stateFile+'.tmp',stateFile);}
const browser=await chromium.launch({headless:true});const context=await browser.newContext();context.setDefaultNavigationTimeout(60000);const page=await context.newPage();
try{
 await page.goto(base+'/');await page.waitForLoadState('networkidle');if(await page.locator('#age-accept').isVisible())await page.locator('#age-accept').click();await page.goto(base+'/yonetim/giris');const gate=page.locator('form[action$="/_access"]');if(await gate.count()){await gate.locator('[name="username"]').fill(access.stageUser);await gate.locator('[name="password"]').fill(access.stagePassword);await Promise.all([page.waitForNavigation({waitUntil:'networkidle'}),gate.getByRole('button').click()]);}
 const login=page.locator('form[data-api="/api/auth/login"]');await login.locator('[name="email"]').fill(access.email);await login.locator('[name="password"]').fill(access.password);await login.getByRole('button').click();await page.locator('form[data-api="/api/auth/mfa/login"]').waitFor();await new Promise(resolve=>setTimeout(resolve,30500-Date.now()%30000));await page.locator('[name="code"]').fill(otp(access.totpSecret));await page.locator('form[data-api="/api/auth/mfa/login"] button').click();await page.waitForURL('**/yonetim');
 async function api(data){const s=await(await context.request.get(base+'/api/session')).json();const r=await context.request.post(base+'/api/admin/content',{headers:{Origin:origin,'X-CSRF-Token':s.csrfToken},data});const result=await r.json();if(!r.ok())throw Error(result.code||'CONTENT_WRITE_FAILED');return result;}
 const report=[];for(const [locale,slug,title,summary,topic,body] of entries){const url=base+(locale==='en'?'/en':'')+'/blog/'+slug;const existing=await context.request.get(url);if(existing.status()===200){report.push({locale,slug,status:'existing; preserved'});continue;}if(existing.status()!==404)throw Error('BLOG_READ_FAILED');const key=locale+':'+slug;if(!state[key]){state[key]=(await api({kind:'guide',locale,slug,title,summary,body,metadata:{topic}})).id;await persist();}await api({action:'publish',id:state[key]});const check=await context.request.get(url);if(check.status()!==200||!(await check.text()).includes(title))throw Error('PUBLICATION_READBACK_FAILED');report.push({locale,slug,status:'published; verified'});}console.log(JSON.stringify(report));
}catch(error){let message=String(error);for(const secret of [access.password,access.stagePassword,access.totpSecret,...(access.recoveryCodes||[])].filter(Boolean))message=message.split(secret).join('[redacted]');console.error(message.slice(0,800));process.exitCode=1;}finally{await context.close();await browser.close();}
