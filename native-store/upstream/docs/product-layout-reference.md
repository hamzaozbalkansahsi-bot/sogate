# Ürün sayfasının masaüstü düzeni

Tarih: 1 Kasım 2026. Kullanıcının karşılaştırma talebi üzerine ürün sayfasının görsel hiyerarşisi yeniden düzenlendi. Canlı kabul tamamlandı; sürüm ve sonuçlar son bölümde yer alır.

## Referans ve teşhis

Referans, Trendyol'un [resmî ürün entegrasyon dokümanındaki masaüstü ürün sayfası örneğidir](https://developers.trendyol.com/v3.0/docs/copy-of-1-product-services-best-practices). `pdp.png` 1696×958 boyutundadır; uluslararası mağaza görünümünü ve doküman açıklama işaretlerini içerir. Güncel Türkiye mağazasının girişli akışları test edilmiş sayılmaz. Açıklama işaretleri, başka markanın renkleri, ürün fotoğrafları ve işletme vaatleri NODENO'ya aktarılmaz.

Önceki NODENO düzeni büyük bir dış kart, dikey küçük görseller, aynı önemde iki satın alma düğmesi ve ilk ekranın çok altında kalan özelliklerden oluşuyordu. Genel taşma önleme kuralı `.wrap` için masaüstü genişlik sınırını da eziyordu; bu yüzden geniş monitörde içerik gereğinden fazla açılıyordu. İlk tarayıcı testi, temel özelliklerin ürün fotoğrafının altına düştüğünü göstererek başarısız oldu.

## Uygulanan düzen

- Ürün sayfası beyaz zeminde, büyük dış çerçeve olmadan sunulur. Genel masaüstü içerik sınırı yeniden işler; 1440 ve 1920 ekranlarda sütunlar gereksiz büyümez.
- Soldaki gerçek ürün görseli genişler. Galeri küçük görselleri fotoğrafın altına alınır. Tam ürün ve renk korunur; fotoğrafı doldurmak için ürünün kenarları kesilmez. Kaydırma, yakınlaştırma, sayaç ve klavye davranışı aynı gerçek galeriyi kullanır.
- Orta bölüm marka ve ürün adı, ürün kodu, satıcı, gerçek fiyat, renk, adet ve satın alma sırasını izler. Adet ve düğmeler masaüstünde aynı sırada bulunur. Sepete ekle ana eylemdir; Şimdi al ikincil, favori bağımsız bir düğmedir.
- Ödeme öncesi durum açıklaması ilgili eylemin hemen altında gösterilir. Ölçü/renk özellikleri, karşılaştırma/alan uyumu/koleksiyon araçları ve teslimat bilgisi bu alanı izler.
- Sağ sütun iki kısa karttır: gerçek ilgili ürün raflarına bağlantılar ile NODENO mağaza/yardım/teslimat bilgileri. Orta boy ekranda iki ana sütuna, telefonda tek sütuna geçilir.
- Benzer ve tamamlayıcı raf bağlantıları gerçek bölümlere gider; klavye odağı, sabit başlık mesafesi ve geri/ileri geçmişi korunur.
- Türkçe, İngilizce, Rusça ve Arapça/RTL aynı düzeni kullanır. NODENO logo, font ve renkleri korunur. Puan, satış adedi, kampanya, ücretsiz kargo veya ödeme yöntemi uydurulmaz.

## Değişiklik alanı

`web/app.js` yalnız ürün sunumu ve bölüm bağlantıları için değişir. `web/product-detail.css` ürün düzeninin sahibidir; eski masaüstü ürün kuralları `web/desktop-store.css` içinden kaldırılır. Yeni etiketler dört dilli sözlüğe eklenir; içe aktarma ve HTML önbellek sürümü birlikte ilerletilir.

Önceden var olan PDF kaynak hash güncellemeleri ve medya denetimi çalışmaları değiştirilmez veya bu görevin kod kaydına eklenmez. Derlemede katalog ürünleri, kategoriler ve fiyatlar önceki canlı verilerle ayrıca karşılaştırılır. Medya yayını yalnız mevcut doğrulama kapısından geçer.

## Kabul yöntemi

174 kaynak testi değişiklikten önce geçti. Yeni tarayıcı testi önce eski sayfada beklenen nedenle başarısız oldu. Yeni düzen; temel özelliklerin görsele eşlik etmesi, ana düğmenin ikincil düğmeden ayırt edilmesi, adet ve satın alma eylemlerinin birlikte kalması, gerçek renk/adetle sepete ekleme ve ilgili rafların çalışması üzerinden doğrulanır. Dört dil, Chromium/Windows WebKit, 390/1024/1440 ve ayrıca 1920 genişlikleri kapsanır.

Gerçek paket ve canlı kabul ayrı kaydedilir. Kaynak önizlemesi test amaçlıdır. Nihai kayıt `artifacts/product-layout-reference/delivery-record.json` olur. Fiziksel iPhone, gerçek ödeme ve Google/Apple sağlayıcı kabulü iddia edilmez. Ödeme ve sağlayıcı etkinleştirmesi kullanıcının önceki kararıyla beklemektedir.

## Canlı kabul

**YAYINLANDI VE CANLIDA DOĞRULANDI.** `852211f383c1da9e523aaf0229e871c64ea8621c2372e2b9d45484d99ed6d2d6`; kabul `2026-11-01T09:57:38.287424+00:00`. Kaynak `af2f05a`. 174 kaynak/18 dağıtım testi; gerçek paket ve canlıda ayrı ayrı 26 düzen, 18 alışveriş, 20 genel mağaza, 40 ürün sayfası ve 32 galeri kontrolü geçti. Dört HTTPS alan adı, 36 varlık hash değeri, 13 genel özel yol ve üç ek koleksiyon yolu kapalı olarak doğrulandı; 15 medya örneği birebir eşleşti.

Aynı 1440×1000 görünümünde satın alma alanı 177.5 piksel, temel özellikler 287.9 piksel yukarı taşındı. Galeri genişliği 505→528.6 piksel oldu. Ürün fotoğrafı kırpılmadan gösterilir. Önce/sonra görüntüler `artifacts/product-layout-reference/` içindedir.

Katalog ürünleri, kategoriler, fiyatlar ve medya sürümü önceki canlı tabanla aynıdır. Ödeme ve Google/Apple etkinleştirmesi kapalıdır. Yedek `/home/nodenoho/nodeno-backups/20261101T095129Z-852211f383c1-99ecff`. Makine kaydı `artifacts/product-layout-reference/delivery-record.json`.
