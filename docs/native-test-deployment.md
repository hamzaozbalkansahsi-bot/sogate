# Native PHP test yayını

<!-- BEGIN NATIVE_FIRST_PAINT_DELIVERY_20261115 -->
## Güncel test yayını — 554e78f543311a4d7e250b89

Yalnız https://sexogate.com/test üzerinde etkin. İlk sunucu HTML'si artık istemciyle aynı küçük resimli kart düzenindedir; eski büyük yeşil kampanya ilk açılışta gösterilmez. Kaynak `f6463b3`, yayın yönlendirmesi `009c67f`, test kabuğu `f34775e`. 468 görünür ürün, 1.726 taslak; 6 ana+44 alt kategori tanımı, 18 dolu alt kategori. Ana hazırlanıyor site korunur ve gerçek tahsilat 409 ile kapalıdır.

Yerel ve özel önizlemede iki motor 33 yönetim+9 müşteri rotası, 11 dil/RTL, yaş, katalog ve görsel kabul geçti. Yayın sonrası iki motor 1 yönetim+9 müşteri smoke, görsel düzen, yaş ve ilk HTML; gerçek katalog/SEO/fiyat/medya/tekrar güvenliği ve HTTP korumaları geçti. JavaScript kapalı ilk HTML kontrolü 390/1440px ve 11 dilde yapıldı. Ekranlar `docs/screenshots/native-store-paint-remote/` ve `native-store-polish-remote/` altındadır. Bunlar fiziksel iPhone veya saha CWV ölçümü değildir.

İşçi aynı554e sürümünde sağlıklı; kendi dakikalık cron'u salt okunur kontrolde tek kayıt. Son gerçek şifreli geri yükleme 2 veritabanı, 41 tablo, 10.079 satır; bütünlük/FK/hash geçti. Tam medya felaket kurtarma ve sürekli yedek rotasyonu tamamlanmadı. Uygulama dosya geçişi, ortak test verisindeki ürün yayınını geri almaz.

Kur uç noktası 503 verdi. Görsel testler isteğe bağlı kur isteğini UI hazır olma ölçütünden ayırır; kritik istekler, gerçek istemci bileşeni, yükleme ekranı ve bütün işlevsel kontroller korunur. Kur/foreign-currency entegrasyonu kabul edilmiş sayılmaz. Ayrıntı `native-first-paint.md`. Önceki SSL/TCP kesintileri ve bazı ilk koşu zaman aşımları raporda korunur; kökeni tamamen çözülmedi. GitHub43757608050/f34775e faturalama kilidi yüzünden 0 adım; CI başarılı değildir. Aşağıdaki eski sürüm notları tarihsel akıştır.
<!-- END NATIVE_FIRST_PAINT_DELIVERY_20261115 -->

15 Kasım 2026. Kullanıcı doğrudan NODENO yazılım kopyasının yayımlanmasını istedi; NODENO ürünlerinin taşınmasını açıkça reddetti. Hedef yalnız **https://sexogate.com/test** ve yönetim **https://sexogate.com/test/yonetim**. Ana hazırlanıyor sayfası, DNS, gerçek tahsilat ve diğer projeler bu yayının kapsamında değildir.

## Veri sınırı ve gerçek durum

- Katalog **2.194 gerçek tedarikçi kaydı** içerir; 172 kaynak kategori yönetimde ayrıca incelenir. Son veri incelemesinde 468 kapak test vitrini için seçildi, 1.726 kayıt taslakta kaldı. Yeni kategori ağacı 6 ana grup ve 44 alt kategoriden oluşur; seçilen ürünler 18 alt kategoriyi doldurur. Boş alt kategoriler vitrinde çoğaltılmaz. Kurucu marka, kaynak namespace/hash ve taslak başlangıcını ayrıca doğrular; NODENO ürün/fiyat/görsel/müşteri/veritabanı veya işletme kimliği alınmaz. Kaynak testlerin referans kataloğu yayın ZIP'ine girmez. Etkin sürüm ve son kanıtlar `native-deployment-report.json` içindedir.
- Yalnız mevcut SEXOGATE rehberlerinden üç içerik bankası ve kendi yönetici erişimi kullanılır. Üyelik belgeleri TR/EN taslaktır. Eski MySQL inceleme verisi korunur. Yeni kaynak katalog kendi doğrulanmış dosyalarından özgün MFA/CSRF yönetim akışıyla SQLite kayıtlarına yüklendi; müşteri veya eski işletme verisi alınmadı.
- Gerçek ödeme **kapalıdır**. `/api/payments/checkout` dağıtım sınırında409 döner; arayüzden ayar değiştirmek bu sınırı kaldırmaz. Yeni ülke/ürün/belge/hukuk/Stripe kabulü olmadan satış açılamaz.
- Bu bir test uygulaması yayınıdır; bütün ticaret modülleri gerçek ürün ve dış sağlayıcıyla kabul edildi anlamına gelmez.

## Sunucuda çalışan yapı

PHP8.3.36, PDO SQLite/WAL, OpenSSL ve ZipArchive gerçek hostingte doğrulandı. Node sunucuda kullanılmaz. TypeScript AST aracı yalnız yerel JavaScript URL derlemesinde kullanılır.

`native-store/upstream` korunmuş kaynaktır. Yayın kopyasında marka/alan adı, kök URL'leri ve mağazanın sunum metinleri taşınır. `deploy/apply-store-theme.mjs` yetişkin ürünlerine uygun metinleri ve yaş karşılamasını ekler; mobilya hesaplayıcılarını müşteri rehberinden çıkarır. Bu derlenmiş paket, kaynak snapshot ile byte olarak aynı diye sunulmaz. `deploy/relocate.mjs` API/bağlantı köklerini taşırken çocuk yol ayraçlarını ve tarih ayraçlarını korur. Taşınan URL token'ları PHP yanıtında gerçek alt yola çevrilir; regex/JSON kaçışlı URL'ler önce ele alınır.

Kod ve kalıcı state web kökünün **dışındaki**, bu uygulamaya ait özel dizindedir. `releases/<id>` ayrı, `state` ortak ve kalıcıdır. Web kökünde yalnız test giriş dosyası/yönlendirme bulunur; özel PHP/SQLite/anahtarlar doğrudan HTTP'den sunulmaz. Eski `/test/app` ağacı ve MySQL korunur.

Özgün yönetici MFA, CSRF, kayıt sahipliği ve secure/HttpOnly `__Host-` çerezi devam eder. Mevcut kendi yönetici parola/TOTP bilgisi yerel `.local/php-stage-access.json` üzerinden güvenli sunucu kurulumuna alınır. Legacy kurtarma kodlarının yeni uygulamada aynı olduğu varsayılmaz. Parola/TOTP/anahtar Git'e veya sohbete yazılmaz.

Ana bekleme sayfasının sabit script hash'li CSP'si alt uygulamaya uygun değildir. Yalnız `/test/.htaccess`, uygulamanın aynı köken betik/stil politikasını belirler; `unsafe-inline` veya `unsafe-eval` açılmaz. Public CSS/JS/fontlarda önbellek, hassas API cevaplarında `private, no-store` korunur. Blog ve sosyal medya dosyaları genel statik yoluna alınmaz; özgün yayın/erişim doğrulamasından geçer. Yayımlanmamış rehber görseli404 döndü.

## İşçi ve sağlık durumunun anlamı

Yalnız bu uygulamanın CLI içerik işçisi cPanel cron'unda dakikada bir çalışır. Diğer cron komutları değişmedi; gerçek heartbeat ve içerik kuyruğu çalışması gözlendi. E-posta, ödeme mutabakatı, tedarikçi ve sosyal platform bağlantıları bu işçiyle tamamlanmış sayılmaz; dış sosyal yayın kapalıdır.

`/test/api/deployment-status` gerçek SQLite `quick_check`, sürüm ve önizleme durumunu gösterir. `catalogReady=true`, `checkoutEnabled=false`, görünür ürün18 ve kaynak ürün2.194'tür. Özgün `/api/health` içindeki tam katalog/medya onay kapısı kaldırılmadı; henüz satış/ülke onayı verilmemiş tam medya/release kaydı nedeniyle bu kontrol satışa hazır değildir ve503 döner. Deployment kontrolü, bu medya kabulünü geçtiğimiz anlamına gelmez.

## Yerel kurulum ve yayın komutları

Bu bilgisayarın mevcut Git dışı PHP/erişim araçları ve D: özel çıktı alanı kullanılır; bunlar genel bir Linux geliştirme kurucusu değildir. Sunucuya yalnız doğrulanmış PHP paketi yüklenir.

```powershell
python scripts/verify-native-snapshot.py
node --test scripts/test-native-relocation.mjs
python scripts/build-native-stage.py
python scripts/prepare-native-stage-local.py
python scripts/run-native-stage-local.py
python scripts/test-native-installer.py
```

Tarayıcı kabulünde `SEXOGATE_NATIVE_TEST_URL` ve `SEXOGATE_NATIVE_TEST_SCOPE` yalnız izinli loopback/test/önizleme hedeflerini seçer. Yerel kabul hem tek parçalı `/test` hem uzun önizleme yolu için yapıldı. `test-native-browser.py` 33 yönetim bölümü/9 müşteri yolunu iki motorda ve beş genişlikte sınar; `--release-smoke` geçiş sonrası1 yönetim bölümü/9 yolu sınar. Bunlar aynı kapsam diye raporlanmaz. `test-native-languages.py` kataloglu vitrinde11 dil seçimini, sunucu/istemci metaverisini ve RTL yönünü sınar; ürün/hukuk çevirilerini onaylamaz.

```powershell
python scripts/publish-native-test.py prepare
# Önizleme URL'sinde aynı release için katalog/ilk HTML/tarayıcı/görsel/yaş/dil kabulü tamamlanır.
python scripts/publish-native-test.py activate
python scripts/test-native-stage-http.py
# Yayın sonrası tarayıcı smoke ve ilk HTML/gerçek görsel kontrolü yapılır.
python scripts/native-stage-operations.py cron
python scripts/native-stage-operations.py status
python scripts/native-stage-operations.py backup
```

`prepare` kurucuyu süreli token ile çalıştırır, ZIP/hash/yol/symlink/mükerrerlik/kaynak katalog denetimlerini yapar; kurucu ve payload silinir. Yönetici kimliği ve kalıcı state sonraki kurulumlarda sıfırlanmaz. `activate` ana site ve önceki test giriş dosyalarını tekrar doğrular, kontrollü giriş/yönlendirme geçişi yapar. İlk sağlık başarısızlığında geri dönüş vardır.

## Yedek ve geri dönüş

Önce eski MySQL'in şifreli yedeği yeni yerel veritabanına geri yüklendi:91 tablo/4.589 satır/103 FK,30 migration checksum ve30→30 PASS. Eski test giriş dosyaları ve özel yapılandırma ayrıca AES-GCM ile yedeklenip geri okunarak doğrulandı.

Yeni native verinin SQLite yedeği `VACUUM INTO` ile tutarlı snapshot olarak alınır. Veritabanları ve gerekli anahtar dosyaları AES-256-GCM ile şifreli ZIP'te indirilir. Yerelde hash, SQLite integrity, foreign key ve tablo satır sayıları doğrulanır. Gerçek sayılar güvenli özet raporunda kayıtlıdır. Bu, tam katalog medyası felaket geri yükleme testi değildir.8.546 orijinal rasterin yerel hash kopyası ve web dışı sunucu aktarımı doğrulandı; sürekli şifreli medya yedek/rotasyonu ayrı kurulmalıdır.

`native-stage-operations.py` yayından sonra gerektiğinde yalnız tek rastgele bakım dosyasına süreli, token kontrollü yol açar. İşlem sonunda dosya/token kaydı kaldırılır ve özgün `/test/.htaccess` geri konur; beklenmeyen eşzamanlı yönlendirme değişikliği ezilmez. Sırlar yalnız yerel `.env.local` ve sunucunun özel alanındadır. Yedek anahtarı `BACKUP_ENCRYPTION_KEY` sohbet veya Git'e konmaz. Sürekli periyodik yedek saklama/rotasyon otomasyonu ayrıca kurulmalıdır.

Hostingte aynı saniyede değişen yönlendirme dosyası bazen404/405 üretti. Geçici kuraldan önce mtime'ın farklı saniyeye geçmesi sağlanır; yalnız bakım dosyasının hiç çalışmadığını gösteren404/405 için sınırlı tekrar vardır. Diğer hata cevabı başarı sayılmaz. Son gerçek şifreli restore2DB/41tablo/6.797satır PASS; kurucu/bakım dosyaları temizliği ve ana site fingerprint'i ayrıca yeniden doğrulandı.

```powershell
python scripts/publish-native-test.py rollback
```

Bu komut yalnız bu yayının giriş/yönlendirmesini doğrulanmış şifreli yedekten geri getirir. Eski uygulama/DB silinmediğinden yıkıcı migration veya tablo geri alma gerekmez. Yeni native state de silinmez. Başka bir dağıtım dosyaları değiştirmişse geri dönüş durur; başka işin değişikliği ezilmez.

## Kabul ve kalan koşullar

Kaynak çekirdek regresyonu153 PASS; URL taşıma7 PASS; gerçek PHP HTTP kurucusunda22 güvenlik/kurulum/yedek senaryosu PASS. ZIP traversal, mutlak yol, nokta takma adı, symlink, mükerrer giriş, token/TTL,103 karakterli TOTP ve beş bozuk kategori ağacı ele alındı. Kaynak snapshot ve13 marka varlığı doğrulandı. Gerçek yerel/uzak tarayıcı, dil, header, kurucu temizliği, CLI heartbeat ve restore kanıtları `docs/native-deployment-report.json` ile `docs/progress.md` içindedir.

## Yetişkin mağazası katmanı

NODENO'nun mobilya metinleri ve dünya haritalı karşılaması SEXOGATE deneyimine ait değildir. Güncel derleme; mobilya/kurulum/toplu mobilya alımı metinlerini, boya ve oda araçlarını, kaynak işletmenin fatura unvanı iddiasını müşteri sunumundan çıkarır. İlk HTML, PHP'nin ürettiği SEO ve istemcinin sonradan güncellediği başlık/açıklama/OG metni yetişkin koleksiyonlarına uygundur. HTTP kontrolü PHP fallback'ini, tarayıcı başlığı kontrolü ikinci istemci kaynağını yakaladı. İkisi birlikte düzeltildi; derleme sırasında4 temel dilde deterministik istemci SEO kabulü ve tarayıcı testinde11 dilde hem gerçek HTTP hem sayfa açıldıktan sonraki başlık kabulü vardır. Kaynak işletme klasörü ve korunmuş snapshot değiştirilmez.

Bordo kemer ve krem yüzeyli yerel `dialog`, 18+ beyanı ve çıkış seçeneği sunar. Escape ile beyan atlanamaz; klavye odağı ve onaydan sonra misafir gezintisi sınanır. Beyan en fazla30 gün, yalnız sürüm ve bitiş zamanı ile cihazda saklanır; üyelik, doğum tarihi veya kimlik istenmez. Bu marka bildirimi ülke bazlı güçlü yaş doğrulaması yerine geçmez. Gerçek tahsilatın kapalı olması devam eder.

Sosyal bağlantılar görünür yazısız dört SVG ikonudur; erişilebilir adları, klavye odağı ve azaltılmış hareket tercihi vardır. Gizlilik tercihi footer akışında tema renkli bir düğmedir; bağlantı veya satın alma alanının üzerine sabitlenmez. Footer sonrasında yalnız mobil alt menüye ayrılan yaklaşık84px kalır. Header logo hizası solda, footer logo hizası ortadadır. Bu davranışlar `scripts/test-native-adult-store.py` ve `scripts/test-native-storefront-polish.py` ile iki motorda denetlenir.

Varlık revizyonu tema, dağıtım kodu ve kaynak manifest'inden türetilir. Yeni paket tüm modül/stil sorgu revizyonlarını değiştirir; eski iPhone/PWA önbelleğinin mobilya metinlerini sürdürmesi önlenir. Native sürümden sonraki önizleme için parent yönlendirmesinde yalnız ilgili rastgele önizleme girişine yol açılır; kurucuya açılan tek dosyalık istisna işlem sonunda kaldırılır. Önizlemenin gerçekten yeni release ve kendi basePath'i olduğu ayrıca denetlenir.

İlk yerel TLS bağlantı kuyruğu CSS yüklemelerini aksattı; test kabuğu düzeltildi. Uzun alt yol regex kaçışı düzeltildi. Uzak20 saniyelik yükleme timeout'u sonrası public varlık cache'i düzeltildi; fonksiyonel uzak navigasyon bütçesi60 saniyedir, performans hedefi geçti denmez. İlk geçişte ana sitenin CSP mirası JavaScript'i engelledi; doğrulanmış eski sürüme geri dönüldü, yalnız alt uygulama başlığı ayrılıp önizlemede yeniden test edildi.

Gerçek Stripe/taşıyıcı/fatura kabulü, gerçek ürün/stok/görsel belgeleri, ülke/yaş kuralları, onaylı hukuk/satıcı kimliği, tüm yedek rotasyonu, tam WCAG/klavye, fiziksel iPhone ve CWV saha ölçümü bu test yayınıyla tamamlanmış sayılmaz. İlk 153 testin dış sağlayıcıları izole fixture'dır; gerçek tahsilat yapılmadı.

## 15 Kasım kaynak katalog ve yeni yetişkin girişi

İlk katalog sürümü `4dde26c2a496aaecbef1027e`, kaynak commitleri `f511d8d` ve `afa3ec6` idi; güncel etkin sürüm raporda tutulur. Kurulumun revision0 API yanıtında taslak kataloğu döndürmemesi ayrıca test edilir. Katalog işleminde mevcut fiyat/içerik ezilmez; 40 kayıtlık güvenli tekrarlar, gerçek stok kodu çakışması, güncel MFA ve yetki denetlenir. Dinamik kategori metni 11 dilde şablonla üretilir; sözlük hatası gizlenmez.256 MB bellek bütçesi yerel/hosting kabulünde doğrulandı.

Girişteki üst yazı ve nokta kaldırıldı. Bordo perde açılışı, kemer çizgisi ve ışık katmanı kullanılır; üyelik istenmez, ek hareket ayarı arayüzü yoktur. Mevcut30 günlük yaş beyanı korunur. Yeni ilk ekran gizli pencerede görülebilir. Ekranlar `docs/screenshots/native-store-adult-remote/`, hareket kaydı `docs/screenshots/native-store-adult-local/age-opening.webm`.

Katalog hazırlama, alanların doğruluk sınırları, ürün paneli ve açık SEO/rozet işleri [katalog kılavuzunda](native-catalog-loading.md); gerçek sayımlar [raporda](native-catalog-report.json). `prepare-native-catalog.py` yalnız özel yerel kaynaklarla çalışır. `publish-native-catalog-media.py` geçici token/yol, hash/MIME/boyut denetimi ve ana site fingerprint kontrolüyle web dışı fotoğraf aktarır; payload/helper sonunda kaldırılır. Gerçek ödeme, stok teyidi, vergi/hukuk/ülke/satıcı ve sağlayıcı kabulü halen kapalıdır.
