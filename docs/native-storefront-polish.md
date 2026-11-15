# Vitrin düzeltmesi — 15 Kasım 2026

Kullanıcının on ekran görüntüsü yeni kabul şartıdır. Canlı `/test` sürümü `4dde26c2a496aaecbef1027e`; yeni çalışma önce yerelde yapılır, ana hazırlanıyor sayfası korunur. Kaynak snapshot değiştirilmez. Güncel yayın adayı `74273b724eb189698f2bda61` olarak derlendi.

## Gerçek teşhis

- Yerel gerçek DOM'da yalnız iki logo resmi vardı;18 ürün fotoğrafı hiç oluşturulmamıştı,18 “Görsel hazırlanıyor” bulunuyordu. `app.js` içindeki iki medya allowlist regex'inin yalnız birisi taşınmıştı. HTTP200 medya testi gerçek görsel yüklenmesi anlamına gelmiyordu.
- Mobilya kalıntıları `home-vitrine.js` sahne adları/otomatik geçişleri, `shopping-ui.js` rehber/alan ölçme araçları ve eksik sunum metinlerinden geliyor. Önceki altı sayfa metin testi bunların tamamını kapsamadı.
- Sabit gizlilik düğmesi mobil satın alma alanı ve footer lisans bağlantıları üstüne biniyor. Orijinal tercih açma işlemi korunarak footer içinde marka ile uyumlu düğmeye taşınacak; izin akışı kaldırılmaz.

## Uygulama ve kabul

1. Tüm medya regex'lerini taşı; gerçek img.currentSrc/naturalWidth ve hata yanıtlarını iki motorda ölç. Yer tutucu ile başarı sayma. Yayımdaki18 kapak aynı orijinal dosyalardır.
2. Ev/mutfak/oda/montaj/alan planlama yüzeylerini müşteri akışından çıkar. Açık alışveriş, bordo kampanya ve gerçek kategoriler korunur; otomatik mobilya sahne oynatıcısı kaldırılır.
3. Ürün kartları eşit görsel oranı,iki satırlı başlık,aynı hizada fiyat/sepete ekle ve araç satırı kullanır. 360/390/430/768/1440 genişlikte gerçek hizalama ölçülür.
4. Ürün açıklaması kısa,factual genel giriş;“Devamını gör”/“Tüm özellikleri gör” ile açılan başlık/paragraflar;gerçek özelliklere ait okunabilir satırlar. Üretici iddiası,sağlık vaadi veya eksik özellik uydurulmaz. Özellik bölümünün adı “Ürün özellikleri”.
5. Benzer ürünler/son gezilenler yerel CSS scroll-snap ile manuel yatay kayar. Otomatik hareket/sonsuz carousel yok. Genel sayfa taşması ile bilinçli ürün şeridi ayrılır. Klavye ve dokunma kontrolü gerçek scrollLeft ile sınanır.
6. Ürün alt satın alma alanı mobil menü/safe-area ile birlikte düzenlenir. Gizlilik düğmesi sabit örtü oluşturmaz. Hit-testing/bounding-box kontrolleri ve klavye odağı uygulanır.
7. İşlevsiz operasyon açıklamaları ve mobilya araçları müşteri ürün sayfasından çıkarılır; doğrulanmamış teslimat süresi/ücret/vergi/sağlık bilgisi icat edilmez. Gerçek tahsilat409 kapısı,işletme/sağlayıcı/ülke onayı olmadan açılmaz.
8. Bağlantılar genel alt çizgi yerine tipografi/renk/odak/hover ile ayrılır. Zorunlu lisans atıfları korunur.
9. Bordo perde açılışı daha yavaş ve görünür hale gelir; yazı/nokta geri eklenmez,ayrı hareket ayarı arayüzü yoktur. İlk çerçeve ve açılış ortası da kaydedilir.

Tasarım becerileri:frontend-design,ui-ux-pro-max,webapp-testing. Mevcut kimlik/tipografi esas alınır; rastgele paket veya yeni eklenti kurulmaz. UI/UX araması sabit öğelerin odağı/bağlantıları örtmemesi için doğrudan eşleşti. Yatay carousel sorgusu bileşene özgü doğrulanmış eşleşme vermedi; genel UX ve yerel CSS scroll-snap uygulanır.

Testler henüz yeni kabulü geçmedi. Çalışma sonuçları `docs/progress.md` içine gerçek çıktılarıyla yazılacak. Tedarikçi rozeti değiştirme önceki görsel aracı reddi nedeniyle açık kalır; aynı işlemi başka yöntemle aşma yapılmaz.

## İnceleme notları

- `/test` medya denetiminin iki regex'i birlikte taşınır. API sarmalayıcısına göreli verilen giriş, kayıt, adres ve sosyal hesap yolları ikinci kez mount edilmez; koşul/birleştirme/template ve tekrar dönüşüm sınandı (7 AST kontrolü).
- Tedarikçi malzeme alanındaki reklam paragrafları doğrudan özellik diye gösterilmez. Yalnız açık malzeme adları ile etiketli gerçek ölçü/çap/ağırlık ayrılır. Kaynak açıklama ve admin kaydı değişmez. Sağlık, sertifika, menşe, stok veya taşıma uygunluğu üretilmez.
- Kişiselleştirme geçmişi izin öncesi doldurulmaz; son gezilenler testi gerçek tercih penceresinden izin vererek ve geri alarak çalışır. Hızlı navigasyonun WebKit fetch iptali üretmemesi için test her işlemde istemcinin tamamlanmasını bekler; hatalar filtrelenmez.
- DOM yenilenirken kaldırılmış satın alma alanları ResizeObserver'dan çıkarılır. RAF ile birleştirilen gözlemci yeni raf/tercih bağlantılarını bir kez bağlar.
- Ödeme kapısı, izinler, MFA, CSRF, private/no-store ve orijinal üretici ambalaj görselleri korunur. Yeni vitrin dosyaları yalnız müşteri HTML'ine eklenir; yönetim stillerine uygulanmaz.
- Kontroller: 14 PHP sunum, 8 Python katalog,12 PHP katalog,17 izole kurulum/güvenlik/yedek,7 AST birim kontrolü başarılı. Önceki `944847...` sürümünde 33 admin +9 müşteri sayfası iki motorda geçti; son bağlantı çizgisi düzeltmesinden sonraki `74273b724eb189698f2bda61` paketinin tam kabulü halen sürüyor. Eski sonuç yeni sürümün kanıtı sayılmaz.

## Disk ve çalışma alanı

C: 0 bayt olduğunda test ekran kaydı OSError28 ile durdu. Aktif ortak PHP çalışma klasörü taşınmadı. Kullanıcının geçici dosya alanı açma yetkisiyle 640 pip önbellek dosyası SHA256 karşılaştırılarak D:ye taşındı; eski yol junction ile çalışıyor. Yaklaşık1,7GB C: alanı açıldı; veri silinmedi. Kendi eski depo yedeği ve yeni ekran kanıtları da D:de korunuyor. Diğer projeler, kullanıcı ekleri ve aktif oturumlar temizlenmedi. Büyük proje taşıması yapılmadı.

Son adayda iki motorda görsel kabul PASS: gerçek img/naturalWidth, bütün katalog kartlarının fiyat/CTA hizası,390px son gezilenler/benzer rafı gerçek scrollLeft, footer tercih hit-test'i,360/390/430/768px sabit alan ayrımı, açılan özellikler,4,8s perde,çift mount olmayan hesap çağrıları,alt çizgisiz bağlantılar. 33 admin +9 müşteri sayfası iki motorda, yönetimde2.194 ürün/172 kaynak kategori/11 dil fiyat-SEO alanları/30% marj/idempotency/özel taslaklar ve yaş girişi kontrolleri de aynı adayda PASS.11 dilin kalan son kontrolleri ve uzak önizleme henüz bitmedi.

Normal metin için ölçülen renk çiftleri: beyaz/bordo14,01:1; ana metin/krem15,66:1; ikincil metin/beyaz5,81:1; bordo/yumuşak pembe11,54:1. Bunlar tüm WCAG denetimi veya saha performansı sonucu değildir. Fiziksel iPhone testi yapılmadı. GitHub native43726018210 işinin hiçbir adımı başlamadı: GitHub açıklaması hesap faturalama kilidi. Yerel test başarıları uzak CI başarılıymış gibi sunulmaz.

## Son kullanıcı yönlendirmesi — küçük, resimli ana sayfa kartları

Kullanıcı büyük tek kampanya alanını reddetti ve Trendyol ana sayfasını referans istedi.74273b adayının tüm yerel kabulleri tamamlandı; bu aday yayımlanmadı. Yeni ana sayfa: üstte kaydırılabilir küçük resimli kategori kısayolları, küçük slogan/ürünler bağlantısı, desktop4/mobil2 sütunda dört resimli kart, ardından gerçek seçili ürünler ve yatay son gezilenler rafı. Büyük yazı paneli ve ana sayfanın metinli alışveriş rehberi çıkarıldı. Kartlar gerçek kategori/ürün kaydına gider; görsel gerçek katalog kapağıdır. Yönetimden seçilmiş yayımdaki kampanya ürünü varsa ilk kartta kullanılır; büyük eski açıklama paneli gösterilmez.

Resmî referans: [Trendyol ana sayfası](https://www.trendyol.com/),15 Kasım2026. Web okuyucusunda canlı ana sayfa akışı/kategori kısayolları/ürün rafları görüldü; otomatik görsel tarayıcı403 döndürdüğü için güncel kişiselleştirilmiş ekranla piksel bazlı birebirlik doğrulanmadı. Başka markanın logosu, fotoğrafı, yorumları veya indirim iddiası alınmadı. Yeni resimli kart adayının ayrıca derlenip yerel/özel önizleme kabulünden geçmesi gerekiyor.

## Güncel yerel kabul — 6a4df2f12a051e326bf868df

Tüm yerel kontroller tamamlandı: Chromium+WebKit dört gerçek resimli kart/5 genişlik/fotoğrafın çerçeve sınırları/başlık-fiyat-CTA hizası/yatay benzer ve son gezilenler/izin geri alma/alt çizgisiz bağlantılar/perde4,8s/çiftlenmeyen hesap yolları PASS.33 yönetim+9 müşteri sayfası iki motorda,11 dil+RTL metaverisi,yaş/klavye/üyeliksiz gezinti ve yönetim kataloğu2.194/172/11/%30/idempotency/private taslak kontrolleri PASS. Yeni kaynaklar JS/PHP sözdizimi ve paket derlemesi de geçti. Kaynak çekirdek34 dosya/153 assertion,URL7,PHP sunum14,katalog8+12,izole kurulum/güvenlik/yedek17 başarılı. Sıradaki işlem aynı paketi yalnız `/test` özel önizlemeye almak; mevcut canlı test halen4dde26c2a496aaecbef1027e. Tam WCAG,gerçek iPhone,CWV saha ölçümü ve sağlayıcı/işletme kabulü tamamlandı sayılmıyor.
