# Tedarikçi katalogları: gerçek çekim ve kullanım durumu

15 Kasım 2026. Kullanıcının istediği xShopum, Liona ve Sistina kamu katalogları gerçekten çekildi. İlk araştırmadaki “katalog alınmadı” durumu aşağıdaki sonuçla değişmiştir. Başvuru, hesap açılışı, sözleşme veya sipariş verilmedi; başka işletmenin bayi erişimi kullanılmadı.

| Kaynak | Ürün kaydı | Kategori kaydı | Ayrıntısı çözümlenen | Yöntem |
| --- | ---: | ---: | ---: | --- |
| xShopum | 1.022 | 48 | 1.070 | Yalnız kamu WooCommerce Store API; tüm stok durumları ve boş kategoriler dahil |
| Liona | 544 | 75 | 619 | Resmî sitemap ve kamu ürün/kategori sayfaları |
| Sistina | 628 | 49 | 677 | Güncel `.com.tr` products.xml, collections.xml ve kamu sayfaları |
| Toplam | **2.194** | **172** | **2.366** | Kaynak başına tekil URL; markalar arasında veya varyant düzeyinde tekil SKU sayısı değildir |

İlk xShopum yaş formu denemesi gerekli Origin/Referer olmadan403 vermişti. Normal aynı kaynak form isteğiyle giriş bildirimi tamamlandı; özel bayi oturumu, anahtar veya erişim atlatma kullanılmadı. Son API çekiminde `stock_status=instock,outofstock,onbackorder` ile1.022 ürünün tamamı, `hide_empty=false` ile48 kategori alındı. Önceki varsayılan API sorgusunun668 ürün vermesi ve iki boş kategoriyi gizlemesi düzeltildi. Ürün HTML/sitemap verisi bu son xShopum çekimine katılmadı. Liona'nın Türkçe URL'si standart yüzde kodlamasıyla işlendi. Sistina kategori sayfasındaki ürün karuseli kategori adı sayılmaz; kategori h1'i esas alındı.

`parsed`, kaynak sayfanın ayrıştırıldığını belirtir. Bütün ürünlerin SKU, teknik belge, hak veya fiyat bilgisinin eksiksiz olduğu anlamına gelmez. Kalite alanlarının gerçek sayıları ve dosya hash'leri [çekim raporundadır](php-source-catalog-report.json).

## Verinin bulunduğu yer ve kullanım

Son xShopum API yanıtları ve çıktısı Git dışında `D:/sexogate-local-artifacts-20261114/private-installs/supplier-api-live-20261115/xshopum/` altındadır. Liona/Sistina önceki çekimleri korunur. Önceki yerel ham/sıkıştırılmış çıktılar Git dışında `D:/sexogate-local-artifacts-20261114/private-installs/supplier-catalog/<vendor>/` altındadır. Resmî URL ve yanıt hash'li özel önbellek aynı köktedir. `scripts/source-catalog.py` yeniden çekim aracıdır; `.ndjson.gz` taşıma dosyaları2 MB'ın altındadır. PHP/MySQL029 migration ile `source_catalog_batches` ve `source_catalog_records` kalıcı inceleme kaydı tutar. Eski sürümler korunur; ana yönetim ekranı her kaynağın son sürümünü gösterir.

Önbellek aynı çekimi yeniden üretmek içindir; mevcut kökü yeniden kullanmak kaynağı tazelemez. Yeni kaynak kontrolünde yeni tarih/saatli özel `--output-root` seçin. `observedAt` ayrıştırma zamanıdır; bayi stok güncelliği veya anlık fiyat garantisi değildir. PHP030 API kuyruğu ve saatlik zamanlama eklendi; hostingten gerçek isteğin HTTP403 alması nedeniyle otomatik bağlantı kapalıdır. Bayi stock/maliyet eşitlemesi hâlâ bağlı değildir. [API durumu ve kullanım](php-supplier-api-guide.md).

Yönetim → **Tedarikçi katalogları**: gerçek sayılar, ürün/kategori filtresi, sunucuda arama,40 kayıtlık sayfalar, kaynak başlığı/SKU/perakende fiyatı ve kaynak görsel bağlantıları. Kategori ve ürün kayıtları inceleme kuyruğundadır; müşteri kataloğunda otomatik yayımlanmaz. Katalog/yönetici oturumu ve MFA zorunludur. Yetkisiz kullanıcıya ham kayıt veya bayi bilgisi dönmez. Müşteri sayfaları ürün yayın/ülke ve hak denetimlerini korur.

Onaylı görsel ve işletmenin belirlediği Türkçe/İngilizce içerik, SKU, kategori, gerçek alış maliyeti ve satış fiyatıyla tek kayıttan kontrollü **taslak** oluşturulabilir. Bu işlem ülke uygunluğu veya satış onayı vermez. Kaynak açıklaması üretici belgesi gibi gösterilmez; tıbbi/sertifika/su geçirmezlik iddiaları doğrudan yayımlanmaz. Yeni çekim mevcut ürün metnini, satış fiyatını veya geçmiş siparişi değiştirmez.

## Birbirinden ayrı kalan ticari veriler

- Kaynaktaki fiyat **kamu perakende fiyatıdır**, bayi alış maliyeti veya bizim satış fiyatımız değildir.
- Kamu `InStock`/`OutOfStock` bilgisi yalnız gözlemdir. `supplierQuantity=null`; doğrulanmış teklif, fiziksel depo bakiyesi veya rezervasyon oluşturulmaz.
- Görsel URL'sinin alınması yayınlama/değiştirme izni vermez. Kaynak görselleri özel incelemede bağlantı olarak sunulur; müşteri ekranlarına kopyalanmaz.
- Bayi XML/API, güncel maliyet/stok, kullanım hakkı, gönderim/iadeler ve kanal kabulü ayrıca doğrulanmalıdır. Bu katalog çekimi gerçek dropshipping sipariş entegrasyonu değildir.

Git dışı `.env.local` içindeki boş `XSHOPUM_XML_URL`, `LIONA_XML_URL`, `SISTINA_XML_URL` alanları güvenli giriş yeridir. Mevcut sırlar korunur. Bu alanlar şu an otomatik feed/stock adaptörü değildir; anahtar varlığını bağlantı başarısı diye göstermeyin. Ayrı ücret/şartlar resmî bayi sözleşmesiyle doğrulanmalıdır.

## Kaynaklar ve izin bekleyen konular

[xShopum](https://www.xshopum.com/), [bayilik](https://www.xshopum.com/sex-shop-bayilik/), [XML rehberi](https://www.xshopum.com/xml-entegrasyon-rehberi/), [resmî WooCommerce Store API](https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/products/), [Liona sitemap](https://www.liona.com.tr/sitemap_index.xml), [Liona bayilik](https://www.liona.com.tr/liona-ucretsiz-fantazi-ic-giyim-dropshipping-xml-bayilik), [Sistina ürün sitemap](https://sistinaicgiyim.com.tr/products.xml), [Sistina kategori sitemap](https://sistinaicgiyim.com.tr/collections.xml), [Sistina bayilik](https://sistinaicgiyim.com.tr/ic/toptan-bayilik). Kontrol tarihi15 Kasım2026; koşullar canlı satış öncesinde yazılı güncellenmelidir.

Liora'nın kanonik yüzü [kimlik rehberinde](brand-face-liora.md) korunur. Gerçek SKU fotoğrafını kullanma/değiştirme hakkı henüz teyit edilmediği için Liora üzerinde tedarikçi ürününü gösteren yeni görsel üretilmedi. Genel katalog resmi bu hakkı kanıtlamaz. İzinli ürün referansıyla yeni editoryal sunum hazırlanabilir; özgün ürün fotoğrafı ve teknik ayrıntıları ayrıca korunur.

## Çalıştırma

```powershell
python scripts/test-source-catalog.py
python scripts/source-catalog.py --vendor all --output-root D:/sexogate-local-artifacts-20261114/private-installs/supplier-catalog
.local/php-runtime/php.exe hosting/php/bin/source-catalog.php --vendor liona --file D:/sexogate-local-artifacts-20261114/private-installs/supplier-catalog/liona/liona.ndjson.gz
python scripts/test-php-source-browser.py
```

Uzak aktarım yalnız yetkili `/test` yayını ve yerel kabulden sonra MFA'lı yönetim formuyla yapılır. `test-php-source-browser.py --remote --import-catalogs --catalog-root <özel-katalog-kökü>` idempotent anahtar kullanır, gerçek sayıları iki motorda ve yönetim erişilebilirliğini doğrular. Yayın/test kanıtları `docs/progress.md` içindeki güncel kayıtla değerlendirilir; bu belgenin yazılması tek başına uzak dağıtım yapıldığı anlamına gelmez.


## Doğrulanan `/test` yayını — 15 Kasım2026

Etkin sürüm `3b0904e15c3912cfad36979d` (PHP/MySQL29). Üç gerçek gzip dosyası MFA'lı yönetim formundan uzak test veritabanına aktarıldı. Chromium ve WebKit son sürümde2.194 ürün/170 kategori/2.364 ayrıştırılmış kayıt doğruladı; üç yönetim sayfası axe/taşma PASS. Kaynak verisi hâlâ özel incelemededir, satışa yayımlanmamıştır. Son veritabanı yedeği kaynak kayıtlarıyla88 tablo/3.482 satır/98 FK ve29 migration checksum'u doğrulanarak yerelde geri yüklendi. Ana site değişmedi ve gerçek tahsilat kapalıdır.
