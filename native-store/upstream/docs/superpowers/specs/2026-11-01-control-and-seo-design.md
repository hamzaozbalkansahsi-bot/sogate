# NODENO yönetim ve uluslararası SEO tasarımı

## Kullanıcının amacı ve yetkilendirilmiş kapsam

Mağazayı gerçekten yönetebileceği tek bir güvenli panel ve mobil/masaüstü için aynı gerçek içeriği indeksletebilen SEO altyapısı. Yalnız maket veya boş menüler teslim edilmez. Kullanıcı geliştirme ve Turhost yayınına yetki verdi; her modül için tekrar onay istenmez. Birinci sıra, indekslenme veya reklam sonucu garantisi verilmez.

Sahip e-postası: `hamzaozbalkan@gmail.com`. İlk kurulum sırrı yalnız özel yerel dosyada teslim edilir; sohbete, Git'e, URL'ye ve loglara yazılmaz. Sahip parolasını ve ikinci faktörünü kendisi kurar. Yönetim adresi `/yonetim`; `/admin` aynı girişe yönlenir.

Öncelikli pazarlar: Türkiye, Almanya, Birleşik Krallık, Kazakistan, Türkmenistan, Azerbaycan, Irak, Suriye, İran, Özbekistan ve Kırgızistan. Pazar ile dil ayrı kayıttır. Mevcut yayın dilleri `tr`, `en`, `ru`, `ar` ve RTL korunur. Almanca/Farsça/Türkmence/Azerice/Kazakça varmış gibi indekslenebilir sahte sayfa üretilmez. Bölgesel sayfa yayını için gerçek yerelleştirilmiş içerik ve ticari koşullar gerekir.

Ödeme/yasal firma ve gerçek Google/Apple etkinleştirmesi önceki kullanıcı kararıyla kapalıdır. Kargo, e-fatura, mesaj ve reklam servisleri için bilgi soruldu; servis bilgisi gelene kadar bağlantılar açıkça yapılandırılmamış görünür. Gerçek para çekimi, mali e-fatura, kargo etiketi veya dış mesaj gönderimi yapılmış gibi gösterilmez. Reklam bütçesi harcanmaz. Üçüncü taraf beceri onaysız kurulmaz; mevcut beceriler ve resmî kaynaklar yeterlidir.

## Değişmez kurallar

- Çalışma deposu `C:/Users/Hamza ÖZBALKAN/Desktop/Nodeno`; diğer projeler değişmez.
- NODENO logo/font/renkleri ve mevcut masaüstü/mobil görünüm korunur; gereksiz ok/emoji eklenmez.
- Kaynak ürün, SKU, ölçü, renk ve medya arşivi değişmez. Yönetim değişiklikleri sürümlü, denetlenen bir çalışma katmanıdır; kaynak kimlik ve teknik gerçekler korunur.
- Yalnız onaylı 5.129 medya referansı yayımlanır. Yeni görsel yüklemesi varsa özel karantinaya alınır; onaysız görsel mağazaya çıkmaz.
- Fiyat, stok, değerlendirme, indirim, sipariş, kargo, analiz ve bağlantı başarıları uydurulmaz.
- Hesap DB, yönetici sırları, anahtarlar, oturumlar ve belgeler web kökü/sürüm klasörü dışında `storageRoot` altında kalır.
- Her yazma işleminde sunucu yetkisi, CSRF/Origin, doğrulama, sürüm kontrolü ve işlem günlüğü uygulanır. Müşteri oturumu yönetici yetkisi vermez.
- PHP 8.x / PDO SQLite ve mevcut vanilla JavaScript kullanılır. Yeni ücretli hizmet, bulut DB veya istemci çerçevesi zorunlu değildir.

## Mimari sınırlar

`hosting/index.php` tek genel PHP girişidir. Yeni özel modüller `seo.php`, `control-store.php`, `control-auth.php`, `control-catalog.php`, `control-operations.php`, `control-marketing.php`, `control-analytics.php`, `control-http.php` olarak ayrılır. Mevcut `account.php` müşteri güvenliği korunur. Yönetim oturumu ayrı `__Host-NODENOADMIN` çerezidir; `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/` kullanır. Yönetim tabloları kalıcı SQLite içinde ayrı isim alanındadır; müşteri yetki modeli değiştirilmez.

`nodenoControlDatabase(storageRoot)` mevcut kalıcı kökü doğrular, ek tabloları sürümlü ve işlemsel kurar. Yönetici kimlikleri müşteri `users` tablosundan ayrıdır. Kaynak katalog dosyaları salt okunur; yayımlanmış çalışma katmanı `nodenoControlPublicState(db, catalog, config)` ile katalog/config/SEO'ya birlikte uygulanır. İlk kurulumda çalışma katmanı boştur ve ürün/fiyat/görsel verisi önceki canlıyla aynıdır.

`web/admin.html`, `admin.js`, `admin.css` yönetim kabuğudur. Genel HTML hiçbir müşteri/sipariş/sır içermez. API `/api/admin/*` varsayılan olarak reddeder. `/api/telemetry`, `/api/contact`, `/api/recommendations` ayrı sınırlı genel uçlardır. Ticaret açma düğmesi yasal ve servis hazırlığını atlayamaz.

## SEO

1. Ürün, kategori ve ana sayfa içeriği ilk HTML'de bulunur; kullanıcılara ve botlara aynı çıktı sunulur. Mevcut JavaScript bunu geliştirir; yükleme sırasında sunucu içeriği boşaltılmaz. JavaScript kapalı tarayıcı da ürün adı, fotoğraf, teknik içerik ve gerçek bağlantıları görür.
2. Başlık/açıklama/canonical/dil/RTL/Open Graph aynı sunucu bağlamından çıkar. Mağaza içi gezinmede meta bilgiler aynı kurala göre güncellenir. Arama, filtre, hesap, sepet, yönetim ve özel içerik indekslenmez. Geçersiz ürün/kategori 404 döner; boş SPA ile 200 verilmez.
3. Tercih edilen SEO alan adı `https://nodenohome.com` olur. Ziyaretçinin `.com`/`.com.tr` alan adı korunur; canonical tercih edilen kopyayı belirtir. Dört dil için karşılıklı, tam URL'li `hreflang` ve `x-default` vardır. Sahte ülke sayfaları yoktur.
4. Gerçek Product/ProductGroup, BreadcrumbList, Organization/WebSite verisi kullanılır. SKU/renk/variant URL ve görünür fiyat birebirdir. Bilinmeyen stok, puan, yorum, ücretsiz kargo ve teslim tarihi eklenmez.
5. `robots.txt`, site haritası indeksi ve dil bazlı ürün/kategori haritaları sağlanır. Görseller taramaya açılır. Site haritaları yalnız 200/indexlenebilir canonical URL'leri içerir. Gerçek değişim tarihi yoksa `lastmod` uydurulmaz.
6. Google/Bing/Yandex doğrulama kodları düz değer olarak güvenle kaydedilir. IndexNow sahiplik anahtarı ve değişiklik kuyruğu gerçek yanıtlarıyla izlenir; gönderildi ile indekslendi ayrılır. Google ürünleri için uygun olmayan Indexing API kullanılmaz. Search Console/Webmaster hesap doğrulaması gerektiren adımlar panelde ve kılavuzda belirtilir.

JS/Worker karşılığı `lib/seo.mjs` ve paketleme ortak SEO kurallarına uyar. PHP çıktısı asıl Turhost yayınıdır; iki çalışma zamanı metaveri ve indeksleme testleriyle karşılaştırılır.

## Yönetici güvenliği

- Bir kerelik kurulum, sabit sahip e-postası + rastgele yüksek entropili token + yeni parola + doğrulanmış TOTP ister. Token yalnız hash olarak özel sunucu dosyasında, süreli ve tek kullanımlıdır. Sahip mevcutsa yeniden kurulum kapalıdır.
- Parolalar `password_hash`; TOTP sırrı özel kökte anahtar dosyasıyla AEAD şifrelenir. Kurtarma kodları tek kullanımlı hashlerdir. Token, OTP, parola ve servis sırları loglanmaz.
- Oturum kimliği doğrulama/elevasyonda yenilenir. Boşta 15 dakika, mutlak 8 saat sınırı vardır; rol/aktiflik/auth_version her istek için denetlenir. Giriş/OTP/kurulum hız sınırı, tek kullanımlı OTP sayacı ve eş zamanlı sahip kurulum koruması bulunur.
- Owner, yönetici, katalog, operasyon, pazarlama, analiz rolleri sunucu izinlerine eşlenir. Rol/sır/finansal durum işlemleri yeniden doğrulama ister. Oturum ve müşteri kaydı karıştırılmaz; e-posta eşleşmesi yetki vermez.
- İşlem günlüğü aktör, hedef, zaman ve gizlilikten arındırılmış değişimi kaydeder. İstemci sürüm numarası eskimişse 409 döner; kayıp güncelleme olmaz.

## Gerçek modüller

### Katalog, fiyat ve kampanya

Arama/filtre, ürün ayrıntısı, yayında/taslak görünürlük, model/renk eşlemesi, yetkili pazarlama metni ve SEO alanları; onaylı medya seçimi. Kaynak SKU ve teknik gerçekler düzenlenmez. Fiyatlar tamsayı kuruşla, mağaza para birimiyle tutulur. Eş zamanlı fiyat değişimi, yürürlük zamanı ve fiyat geçmişi denetlenir. Çizili fiyat/indirim oranı gerçek uygun geçmişten çıkar; fiyat geçmişi yoksa referans fiyat uydurulmaz. Kampanya/koleksiyon/banner/kupon taslakları, kapsam, zaman ve kullanım sınırları kalıcıdır; yayına alma ayrıca denetlenir. Hiçbir demo kampanya canlıya yazılmaz.

### Sipariş, kargo, fatura ve sevkiyat

Gerçek mevcut müşteri siparişleri ve panel taslakları izlenir; kişisel veriler yetkiyle açılır. Sipariş durum geçişleri sürüm/idempotency/izin ile korunur. Ödeme açılmadan taslak gerçek ödenmiş siparişe çevrilmez. Ülke/ağırlık/sepet koşullu kargo kuralları, taşıyıcılar ve takip kayıtları yönetilir. Kargo ve fatura sağlayıcısı yokken etiket/fatura üretildi denmez. Taslak/proforma ve paketleme/sevkiyat listesi mali e-fatura gibi adlandırılmaz. Dış servis hazırlığı ve manuel kayıtlar birbirinden ayrılır. Kullanıcı hesabına bağlı kayıtlar yalnız doğru müşteriye görünür.

### Mesaj ve pazarlama

Gelen destek mesajları, durum/atama ve yanıt taslakları; e-posta/SMS şablonları ve teslimat kuyruğu. Servis yokken gönderim kapalıdır; pazarlama izni olmayan kişiye pazarlama gönderilemez. Açık operatör eylemi olmadan dış mesaj/reklam gönderilmez. Reklam için UTM bağlantıları, kampanya bütçe/sonuç kayıtları ve bağlantı hazırlığı vardır; dış reklam hesabında harcama veya sahte başarı yoktur. Sırlar yazma alanıdır, okuma API'sinde geri verilmez.

### Analiz, ürün sıralaması ve görünüm

İsteğe bağlı analiz onayı kapalı başlar. Onaysız ziyaretçi için telemetri ve üçüncü taraf piksel çalışmaz. Onaylı olaylar izinli olay türü/ürün/ülke/dil/cihaz alanlarıyla sınırlanır; e-posta, ham IP, serbest URL sorgusu ve mesajlar analiz kaydına girmez. Panel gerçek sayı veya açık boş durum gösterir.

Ürün sıralaması gerçek toplu görüntüleme/sepet sinyali, zaman etkisi, kategori uyumu ve operatör ağırlıklarıyla çalışır. Stok bilinmiyorsa varmış gibi davranılmaz; gizli ürün ve farklı renk tekrarları elenir. Veri yokken katalog sırası/kategori uyumu güvenli geri dönüştür. Sunucu sıralama sonucu gerçek vitrine bağlanır; arayüzde sahte kişiselleştirme iddiası yoktur. Ayarlar ve önizleme kaydedilir.

Görünüm yönetimi onaylı hero/koleksiyon görsellerini, vitrin sırasını ve dört dilli başlıkları yönetir. Rastgele HTML/JavaScript/CSS enjekte edilmez. Kanonik logo/font/renkler varsayılandır. Panelin kendi mobil gezinmesi, tabloları, formları ve gerçek kontrollerin klavye odağı doğrulanır.

## Teslim ve kabul

Her veri/güvenlik özelliği başarısız test → uygulama → başarılı test döngüsünden geçer. Kaynak testleri, PDO SQLite HTTP entegrasyonu, JS kapalı SEO, dört dil/RTL, yönetici yetki/CSRF/MFA, kalıcılık ve mağaza regresyonu çalıştırılır. Müşteri verisi/sır/ham kaynak genel paket dışında kalır. Tam medya kapısı ve yedekli Turhost dağıtımı korunur. Gerçek canlıda anonim reddi ve metaveri/sitemap/mağaza görüntüleri doğrulanır; canlıya test siparişi, sahte analiz veya demo kayıt eklenmez.

İş bitmeden yönetici kılavuzu, ilk kurulum ve servis hazırlık listesi, SEO kılavuzu ve güncel teslim kaydı yayımlanan sürümle eşleştirilir. İlk sıra veya gerçek ödeme/sağlayıcı kabulü yapılmış gibi raporlanmaz.

## Resmî başvuru kaynakları

- https://developers.google.com/search/docs/specialty/international/localized-versions
- https://developers.google.com/search/docs/appearance/structured-data/product-variants
- https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- https://developers.google.com/search/docs/specialty/ecommerce/designing-a-url-structure-for-ecommerce-sites
- https://www.bing.com/indexnow/getstarted
- https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html

### Kullanıcı yönlendirmesi: KolayBi

Muhasebe ve e-fatura için kullanıcı KolayBi seçti. Resmî API anahtarı ve Channel ile token alınır; sandbox/live ortamları ayrı tutulur. Cari, ürün, sipariş/fatura ve e-belge eşlemeleri özel, denetlenen adaptörle gerçekleştirilir. Başarısız veya sonucu belirsiz yazma isteği körlemesine tekrar edilmez. Fatura taslağı oluşturma ile GİB’e resmileştirme ayrı eylem ve yetkidir. Kargo/SMS/reklam için KolayBi’nin kapsamı varsayılmaz.
