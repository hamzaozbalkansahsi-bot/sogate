# Doğrudan NODENO uygulama kopyası — 15 Kasım2026

## Kullanıcının son kararı

“Uyarlama; önce direkt her şeyi ile al, sadece renk ve tema görünümü SEXOGATE gibi olacak.” Bu karar önceki parça parça PHP arayüzü yaklaşımının yerini alır. Yeni kaynak temel `native-store/upstream`, ayrı marka katmanı `native-store/theme` olur. Yönetim, menü, sayfa, alışveriş, dil/para/ödeme davranışları yeniden yazılmaz. Eski SEXOGATE/MySQL kaynakları ve veri kaydı geri dönüş için korunur; başka sohbetlerin dosyaları temizlenmez.

## Doğrudan alınan kaynak

NODENO'nun yakalanan çalışma ağacından **771 dosya /12.595.849 özgün bayt** alındı; Git'e henüz alınmamış güncel kod da dahildir. Son güvenli kopya12.595.829 bayttır. `native-store/source-manifest.json` kaynak commit'ini, zamanı, bütün SHA256 değerlerini ve3 test verisi istisnasını taşır:768 dosya doğrudan aynı,3 testte yalnız açık sahte Stripe sabitleri üretilen test verisine çevrilmiştir.52 PHP/61 JS uygulama motoru bütünüyle aynıdır. `native-store/.gitattributes` içe alınan dosyalarda Git'in satır sonunu değiştirip hash'i bozmasını engeller.

- Özgün vitrin, yönetim/sidebar/editör, menü/kategori/arama, ürün/galeri, sepet/favori/liste/karşılaştırma, checkout, müşteri/üyelik, blog/araçlar.
- Dil/RTL, ülke/para, tarih/saat, fiyatlandırma, Stripe/ödeme/iadeler, belge, tedarikçi, sosyal, rapor, SEO ve operasyon modülleri.
- Kaynak derleme/dağıtım araçları, testler, belgeler ve ortak arayüz çevirileri.

Kaynak dağıtım araçları referanstır; başka işletmenin sunucusunda çalıştırılmaz. `.env`, OAuth/sır, müşteri/oturum/sipariş/veritabanı ve NODENO'nun ticari katalog/fiyat/tedarikçi/görsel arşivi uygulamaya taşınmaz. Eski işletmenin ürünlerini veya satıcı kimliğini SEXOGATE'e atayarak boşluk doldurulmaz.

## Tema ve yerel çalışma

Çalışan yerel pakette **52 PHP ve61 JavaScript modülü değiştirilmeden** kullanılır. HTML marka alanları, CSS renkleri, lisanslı mevcut SEXOGATE fontları ve onaylı logo/ikonlar ayrı derleme/tema katmanında değiştirilir. UI sayfalarının şablonu, rota mantığı, API ve iş kuralları özgündür.

NODENO'nun özgün SQLite/WAL motoru ayrı yerel veri alanında korunur; MySQL'e yeniden port edilmez. Yeni state sürüm klasörünün/web kökünün dışında tutulur. İlk yanlış yerel yerleşim özgün güvenlik kontrolünde reddedildi; kontrol kaldırılmadan state kardeş özel klasöre alındı. Yerel yönetici yalnız mevcut SEXOGATE test erişiminden kurulur; NODENO hesabı/rolü/anahtarı kullanılmaz.

Yerel çalışma **https://127.0.0.1:3186**; PHP de yalnız loopback'te çalışır. Geliştirme TLS sertifikası yalnız özel yerel dizinde,7 günlüktür; sistemin sertifika güven deposu değiştirilmez. Güvenli `__Host-` çerezi/MFA/CSP korunur. Test için CSP'yi kapatmak yerine Playwright sürücüsü düzeltilmiştir. Yerel TLS/marka kabuğu yayın dağıtım sistemi değildir.

```powershell
python scripts/test-native-source.py
npm --prefix native-store run build
npm --prefix native-store run content:local
npm --prefix native-store run dev
npm --prefix native-store run test:core
npm --prefix native-store run test:browser
npm --prefix native-store run test:languages
```

Özel yerel yollar `.local/native-store-build.json` içinde; parola/anahtar çıktıya veya Git'e yazılmaz. Bilgisayarın önceden hazırlanmış `.local/php-runtime` ve mevcut yerel SEXOGATE test erişimi kullanılır. Test araçlarının Python bağımlılıkları mevcut ortamdan kullanılmış, yeni paket kurulmamıştır.

Ürün kataloğu bu kopyada henüz **boştur**; kaynak kod kopyası, eski MySQL katalog/sipariş verisinin migrasyonu değildir. Üç mevcut SEXOGATE rehberi özgün blog motoruna yerel içerik olarak bağlandı; özgün kuyruk ilk2 yazıyı yayımladı,1 yazı sırada. NODENO yazısı/kataloğu yayımlanmadı. Türkçe/İngilizce üyelik belgeleri açık yerel taslaktır; satıcı ve hukuk onayı yerine geçmez. Gerçek tahsilat kapalıdır.

## Gerçek doğrulama

- İlk kaynak bütünlüğü testinde2 RED; kopyadan sonra2 PASS. Bütünlük hem kaydedilmiş hash'e hem mevcut NODENO kaynaklarına göre kontrol edilir.
- İlk seçilmiş arama/liste/sepet/misafir checkout/dil/tarih koşusu23/23 PASS.
- Özgün NODENO testlerinden32 dosya **146/146 PASS**,0 skipped,10,491 saniye. Test/uygulama koduna yama yapılmadı. Gerçek hesap HTTP'si, sahiplik/CSRF/oturum, MFA/rol, katalog/editör/operasyon, kampanya, ödeme/Stripe webhook/iadeler, blog kuyruğu ve mahremiyet kapsanır. Bu seçilmiş regresyon paketidir; NODENO'nun bütün test dosyaları çalıştırıldı denmez.
- İlk geniş koşuların eksik PHP yolu, state'in sürüm içinde olması ve kaynak düzeni/fixture eksikleri yerel test kabuğunda düzeltildi. Özgün testlerin667 ürünlük referansı ve hukuk corpus'u yalnız D: özel geçici test alanında kullanılır; uygulama veya Git/yayın paketine girmez. Bu, SEXOGATE katalog aktarımı veya hukuk onayı değildir.
- Son tam tarayıcı koşusu Chromium/WebKit ×360/390/430/768/1440; gerçek API yanıtı ve tamamlanmış render beklenerek33 yönetim bölümü ve9 müşteri/içerik yolu PASS; MFA/secure çerez doğrulandı, JS hatası0/izinsiz dış istek0. Kanıt `.local/native-browser.json`, `.local/native-browser-final.log` ve `docs/screenshots/native-store-local/`. Son logo/marka override'ları iki motorda ilgili admin/blog yolları ve5 genişlikte ayrıca PASS (`.local/native-browser-branding.json`). İlk sürücü hataları CSP'de string eval, aynı belge hash geçişinde HTTP yanıtı bekleme ve yanlış `saved` yoluydu. Özgün `favorites` yolu ve gerçek aynı belge akışı kullanılarak sürücü düzeltildi; uygulama kontrolleri kapatılmadı.

## Yayın durumu

Bu doğrudan kopya önce yereldedir; `sexogate.com/test` ve ana site bu aşamada değiştirilmedi. Önceki test yayını `4dbb961204505bceb41bb5be` yerinde kalır. Native kopyanın kök göreli URL/host kontrolleri, yayın/medya bütünlüğü, işçi/cron, ayrı kalıcı state ve `/test` alt yol kurulumu doğrulanmadan eski yayının üzerine konmaz. Kaynakta bulunan mobilyaya özgü ticari içerik/ülke/vergi varsayımları yetişkin ürünleri için onay sayılmaz. Ödeme hesabı/kategori kabulü ve hukuk/ürün/ülke şartları tamamlanmış gösterilemez.


## Kalıcılık ve son kopya

Yerel yeniden derleme aynı özel state yolunu ve mevcut yönetici kimliğini korudu; yeni sürüm dizini değişti, kullanıcı/state silinmedi. İleride aynı build komutuyla yeni boş bir müşteri deposu açılmaz. Yeni derleme blog bankası ve mevcut özel taslak belgeleri/kapakları önceki aynı SEXOGATE yerel sürümünden korur.

NODENO kaynak klasörü başka görevlerde güncelleniyordu. Son yakalamada771 dosyaya ulaşıldı; değişen referans dosyalarının önceki baytları D: özel yedeğine alındı. `copy-nodeno-source.py --refresh`, yalnız yerel kopya önceki kaydedilmiş hash ile aynıysa günceller; kullanıcı düzenlemesini ezmez. Yakalama zamanı `source-manifest.json` içindedir. Çalışan52 PHP/61 JS dosyasının son kaynak kopyasıyla farkı0 doğrulandı; kaynak klasör sonraki anlarda değişirse bu sabit snapshot'ın bozulduğu anlamına gelmez.

`native-store-checks` CI eklendi: kaydedilmiş bütün SHA256 değerleri,13 tema varlığı ve gerçek veri gerektirmeyen özgün23 JS regresyonu. Yerel146 testin veri/fixture kapsamıyla CI'nin23 testi aynı sonuç diye sunulmaz. GitHub hesabının önceki faturalama kilidi sürerse uzaktaki koşu ayrıca engel olarak kaydedilir.

Axe/WCAG denetimi, fiziksel iPhone, gerçek Stripe/taşıyıcı/fatura hesabı, canlı Native medya/dağıtım bütünlüğü ve `/test` alt yol aktivasyonu bu kaynak kopyası doğrulamasıyla tamamlandı sayılmaz.

## Son yerel kabul

- `build-native-store.py`: son temiz sürüm derlemesi PASS;771 kaynak,52 değişmemiş PHP/61 değişmemiş JS; katalog0, tahsilat kapalı. Aynı özel state ve mevcut yönetici korunur. Derleme çıktısı `.local/native-build-final.log`.
- Python10 dosya AST,52 PHP lint ve62 JS sözdizimi kontrolü PASS; çalışan pakette52/61 motor byte eşliği PASS (`.local/native-static-final.log`).
- Chromium'da11 dilin kategori sayfası HTTP200, gerçek dil seçimi ve Arapça/Farsça RTL PASS;0 JS hatası (`test-native-languages.py`, `.local/native-languages.json`, `.local/native-languages-final.log`). Bu boş katalog/dil seçim kontrolüdür; gerçek ürün ve hukuk çevirilerinin tamamlandığı anlamına gelmez.
- İlk ek dil koşusunda boş kategori SEO metni503 ve sonrasında miras alınan izin açıklamasının eksik çevirisi JS hatası üretti. Motorun eksik çeviriyi reddetme davranışı korunarak, yalnız belirli boş katalog ve arayüz metinleri `theme/locale-meta.json`/`compile-native-meta.py` üzerinden veri olarak tamamlandı; gelişigüzel dil fallback'i eklenmedi.
- Yerel HTTPS kabuğunda eksik PUT aktarımı düzeltildi. Özgün API, kimliksiz durum değişikliğini403 ile reddetti;501 kabuk hatası artık yok. PHP/JS çekirdeği değiştirilmedi.
- Git index'indeki771 kaynak dosyası ile13 tema varlığının SHA256 değerleri ayrı ayrı doğrulandı; kaynak klasörüne bakmakla yetinilmedi.803 dosyalık bilinen sır/özel anahtar taramasında eşleşme0 (`.local/native-secret-scan.json`); genel güvenlik sertifikası değildir.
- Yeni dosyaların whitespace kontrolü PASS. Byte olarak korunmuş kaynak ve lisanslarda CRLF'yi doğru yorumlayan kontrolde146 mevcut biçim bulgusu bulunuyor; kaynak/lisans byte'ları değiştirilerek gizlenmedi. Tam `git diff --cached --check` başarılı diye raporlanmaz; `.local/native-upstream-whitespace.log` gerçek kayıttır.
- Yeni CI'nin özgün23 testi yerelde23/23 PASS (`.local/native-ci-local.log`). Uzak GitHub koşusu ayrıca kaydedilir; faturalama kilidi yerel sonuçla yeşil gösterilemez.

GitHub ilk push'u, üç test dosyasındaki açık sahte `rk_live_` sabitlerini anahtar olarak sınıflandırarak GH013 ile reddetti. İstisna bağlantısı kullanılmadı. Yalnız bu üç regresyon dosyasındaki sahte değerler PHP içinde üretilen açık dummy veriye çevrildi; test assertion'ları ve52 PHP/61 JS motoru değişmedi. Özgün/güvenli dosya hash çiftleri manifest'te; `native_fixture_safety.py` aynı güvenli aktarımı tekrar üretir ve tanınmayan sabitte durur. Asıl NODENO kaynağı değiştirilmedi. Son kaynak karşılaştırması2/2 PASS; üç dosyanın hepsini kapsayacak şekilde genişletilmiş34 dosya **153/153 PASS**,0 skipped,10,990 saniye (`.local/native-core-tests-final.log`, `.local/native-core-tests-after-fixture.log`). Python AST son sayı11; son temiz derleme de PASS. İlk yerel, yayımlanmamış commit düzeltilerek normal push yapılır; remote geçmişi değiştirilmez.

Güvenli kaynak commit'i `8009314`, izinli `codex/local-commerce` dalına **normal push edildi**. Commit içindeki771 kaynak ve13 varlığın hash'i ayrıca doğrulandı. [Native CI43689128352](https://github.com/hamzaozbalkansahsi-bot/sogate/actions/runs/43689128352) `completed/failure`,0 adım: “The job was not started because your account is locked due to a billing issue.” Uzak testler çalışmadı; yerel153 PASS bunun yerine CI sonucu diye sunulmaz. Canlı uygulama yayını yapılmadı.

15 Kasım son durum:yalnız [sexogate.com/test](https://sexogate.com/test) PHP/SQLite sürümü `d6ae100648e17c0204db628b` ile yayımlandı; ana site değişmedi. Ürün/kategori0, gerçek tahsilat kapalı. Mobilya ve dünya haritası yerine yetişkin metinleri/18+ katmanı uygulanır. Önceki "yerelde/yayımlanmadı" ifadeleri o aşamanın tarihsel kaydıdır; güncel [yayın kanıtı](native-test-deployment.md) esas alınır.
