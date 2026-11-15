# NODENO

**İyi tasarım. Kolay yaşam.** / **Good design. Easy living.**

Türkçe, İngilizce, Rusça ve Arapça mobilya mağazası. Kaynak Adore bayilik kataloğudur. Mevcut 667 ürünün satış fiyatları, doğrulanmış güncel Adore fiyatlarına %40 eklenerek belirlendi. Yasal satıcı ve ödeme altyapısı tamamlanmadığından tahsilat ve sipariş oluşturma kapalıdır. Listeyi indirmek sipariş vermez veya firmaya mesaj göndermez.

**Güncel yayın:** Mobil düzen ve üyelik gerektirmeyen iletişim/adres/bilgi kontrolü `d53b68f4a8f278f7590e9f68aca9072a3c004fc9289848db3ceee3399faef2b2` sürümüyle canlıda doğrulandı (2026-10-31T22:37:22.944Z). WebKit/Chromium, dört dil, 216 mobil görünüm, sekiz misafir akışı, 156 genel yerleşim ve 136 kaynak testi geçti. Yatay sınırlar, sabit çubuklar ve klavye alanı düzeltildi. Kullanıcının onayladığı kapsam ödeme öncesidir; tahsilat ve sipariş oluşturma kapalıdır. [Mobil ve misafir kullanım](docs/mobile-guest-checkout.md).

**Önceki renk yayını:** Kısa adlar ve renk seçimi `c24f6ea75cae83c932186d243c9300a8ac2855ab13bda7a45ff7c4baa833bf10` sürümüyle canlıda doğrulandı (2026-10-31T21:49:22.190Z). 667 satış kodu korunarak 404 renk kaydı 129 ailede, toplam 392 mağaza modeli halinde sunulur. Dört dil/RTL, seçili renk/fiyat/fotoğraf/kod, sepet ve çıktılar tamamlandı; 131 kaynak testi, 16 canlı varyant görünümü ve 156 yerleşim kontrolü geçti. [Renk seçenekleri](docs/product-variants.md).

**Önceki galeri yayını:** Büyütülmüş galeri `d26231c501cfda1fb671ae85fa09a324dc2dc15eff71e813d3fd4f0e59363764` sürümüyle canlıda doğrulandı (2026-10-31T21:13:42.541Z). Parmakla kaydırma, önceki/sonraki düğmeleri, klavye, fotoğraf sayacı ve seçim/odak dönüşü dört dilde tamamlandı. 124 kaynak testi ve 14 canlı galeri kontrolü geçti. [Galeri kullanımı](docs/photo-gallery.md).

**Önceki mobil kategori yayını:** Mobil kategoriler `e2585e101082664b3b881b20877e80b06a31bcbc0c7f1eb6162a5efa8013ef2b` sürümüyle canlıda doğrulandı (2026-10-31T21:04:25.185Z). Görselli oda/alt kategori kartları, dört dil/RTL, yenileme ve geri gezinme tamamlandı; 124 kaynak testi, 24 canlı kategori görünümü ve 156 yerleşim kontrolü geçti. [Kategori düzeni](docs/mobile-categories.md).

**Önceki ürün özellikleri yayını:** Ürün özelliklerini yenileyen PHP sürümü `d8819841dfe0f39cd5956c2afac24e1799a756e0d231e802fe6a3fd2ad3b6cac`, [nodenohome.com](https://nodenohome.com) üzerinde yayında ve canlıda doğrulandı. 124 Node/PHP testi; yerel ve canlı ortamda ayrı ayrı 84 görünüm, 16 bölüm gezinme kontrolü ve 20 ek gezinme senaryosu; ayrıca 156 canlı yerleşim kontrolü geçti. Dört dil, masaüstü/mobil ve RTL kapsandı. Önceki fiyatlı d5 yayınının 667 Ndn- kodu ve doğrulanmış +%40 fiyatı korundu. Tam PDF 709 ürün/168 sayfadır; PDF'deki 42 eksik site kaydı kullanıcının değerlendirmesi için bekletilir. Ayrıntılar [özellik düzeninde](docs/product-specs.md), [fiyatlandırmada](docs/catalogue-pricing.md) ve [teslim kaydında](docs/teslim-durumu.md).

Ürün sayfasında adet ve sepete ekleme alanının ardından en fazla dört kısa teknik bilgi gösterilir. Tam teknik değerler aşağıdaki okunabilir alanlarda ve açılabilir gruplarda eksiksiz korunur. Yalnız gövde, kapak veya üst modül içeren on ürünün kapsamı satın alma alanında ayrıca belirtilir. Masaüstü, mobil, dört dil ve Arapça RTL aynı düzeni kullanır. Bölüm bağlantıları ve aynı ürün içinde geri gezinme galeri/adet/açılmış bölümleri korur; doğrudan bölüm bağlantısı ve yenileme hedef bölüme gider. Çizili fiyat bileşenleri bu sürüme dahildir; indirim oranı henüz seçilmediğinden `mode: preserve` ile 667 fiyat ve sıfır indirim iddiası korunur.

Hazırlanan sürüm; arama önerileri, çok seviyeli kategori paneli, ürün listesi ve tam ürün sayfaları, seçilebilir sepet satırları, favoriler, mobil alt gezinme ve filtre çekmecesi sunar. Gerçek PHP/SQLite üyeliğinde giriş/kayıt/çıkış, profil/parola, adres defteri ve hesaba bağlı sepet/favori verisi bulunur. Konuk seçimleri bu tarayıcıda kalır; başarılı girişte hesaba bir kez birleştirilir. Çıkışta kişisel seçimler ve hesap ekranı verileri tarayıcıdan temizlenir. Kullanım adımları [mağaza kılavuzunda](docs/magaza-kullanim-kilavuzu.md), teknik sözleşme [üyelik çalışma zamanında](docs/account-runtime.md) açıklanır.

Tek çalışma klasörü `C:/Users/Hamza ÖZBALKAN/Desktop/Nodeno` dizinidir. Önceki çalışma bu klasöre dosyaları ve Git geçmişi korunarak taşındı. Başka proje klasörleri değiştirilmedi.

## Kurumsal kimlik ve iletişim

Kanonik bilgiler `data/brand.json` dosyasındadır: **nodenohome.com**, **info@nodenohome.com**, **0850 305 84 78**, sosyal medya **@nodenohome**. Marka adı yasal firma unvanı olarak varsayılmaz. Telefonun WhatsApp desteği veya e-posta kutusunun teslimat durumu doğrulanmış sayılmaz.

Kullanıcının gönderdiği orijinal SVG logoları, #172D38 lacivert / #F5F2E9 fildişi / #D8EC81 lime renkleri ve NODENO Sans 400/700 fontları kullanılır. Fontlar yerel sunulur; `web/assets/fonts/OFL.txt` lisansı korunur. Seçili dosyaların kaynakla bire bir eşleşen SHA-256 kayıtları `data/brand-assets.json` içindedir. Orijinal ZIP ve açılmış referans paketi korunur, sunucu paketine eklenmez.

Güncel indirilebilir marka paketi `artifacts/brand/NODENO_Tam_Marka_Paketi_Guncel_2026-10-31.zip` dosyasındadır: 123 dosya, 19.257.079 bayt. Orijinal tasarım dosyaları korunarak güncel kurumsal JSON/TXT, dört dilli HTML iletişim kartı, vCard ve dosya manifestleri eklendi. Kaynaktaki kırpılmış kelime logosu ve boş PNG kusurları paket içinde açıkça işaretlendi; iletişim kartında sağlam yatay logo kullanıldı. Ayrıntılar ve SHA-256 değeri `docs/marka-guncellemesi.md` içindedir.

Kullanıcı alan adını Turhost'tan satın aldığını doğruladı. 31.10.2026 tarihinde **nodenohome.com** ve **www.nodenohome.com** için DNS ve güvenilir HTTPS erişimi doğrulandı. İki alan adı, nodenohome.com.tr hesabının `/home/nodenoho/public_html` dizinini paylaşır; .com.tr adresine yönlendirme yapılmaz. Turhost kayıtları ve sertifika durumu `docs/alan-adi-kurulumu.md` içindedir. E-posta kutusunun çalıştığı bu web doğrulamasından çıkarılmaz.

Önceki marka/katalog, API ve PHP paketi Turhost'a yüklendi. Bu başlangıç yayınının doğrulanmış özeti `a0cc1a0f3db5c098b59ad12157a884705e1a0d5145a4d94832003225ee621767` değeridir. İki HTTPS alan adı, 19 genel varlığın SHA-256 eşleşmesi, gerçek ürün görseli ve 10 özel yolun erişime kapalı olması doğrulandı. Önceki arayüzün dört dilde 1366/768/390 kontrolleri de geçti. Bu tarihsel kayıt güncel sürümün kabulü yerine geçmez; sürüme bağlı güncel kanıtlar [teslim kaydında](docs/teslim-durumu.md) belirtilir.

## Çalıştırma

Node.js 22.13 veya üzeri gerekir. Uygulamanın çalışma zamanı paket bağımlılığı yoktur.

```powershell
npm test
npm run build
npm run validate
npm run dev
```

Yerel adres: http://127.0.0.1:4173 . `dist/server/index.js` yerel katalog önizlemesi ve önceki Sites yayını için tek Worker dosyasıdır. Gerçek üyelik oturumu için PHP, PDO SQLite ve ayrı kalıcı veri dizini gerekir; yalnız Node önizlemesi üyelik kabulü sayılmaz. PHP paketleme ve sınama adımları [cPanel çalışma zamanında](docs/cpanel-runtime.md) açıklanır. Kaynak dosyalar `web/`, `lib/`, `data/`, `hosting/` ve `scripts/` altındadır. `.openai/hosting.json` tarihsel Sites proje kimliğini korur; güncel yayın hedefi kullanıcının Turhost hosting hesabıdır.

## Katalog ve veri sınırları

`data/catalog-source.json` kaynak kayıtları, referans perakende fiyatlarını, özgün açıklamaları ve görsel URL'lerini saklar. Bunlar bayi stok/fiyat beslemesi değildir. Kamuya açık API, kaynak fiyatlarını veya stok vaadini göstermez. `artifacts/source-catalog/` ham arşiv ve aktarım raporudur; kaynak Git deposuna ve yayın paketine alınmaz.

`lib/catalog.mjs` mağaza görünümünü üretir. Kaynak satıcının teslimat koşulları, garanti taahhüdü ve telefon bilgileri NODENO sözüne dönüştürülmez. Türkçe özgün açıklamalar korunur. Diğer dillerde kısa açıklamalar doğrulanmış ürün adı, ölçü ve renk alanlarından oluşturulur. Çevirisi tamamlanmamış teknik metin özgün dilinde gösterilir ve ürün ayrıntısında belirtilir; uzun kaynak pazarlama metinlerinin bire bir eksiksiz çevirisi olduğu iddia edilmez.

Bu yayında 667 ürün başlığı, 104 kategori ve ticari koşullardan ayrılmış tüm teknik satırlar İngilizce, Rusça ve Arapça karşılıklarla doğrulandı. Ek sözlük 955 özgün teknik satırın 2.865 çevirisini içerir. Çeviri açığı olan ürünle yayın derlemesi durur. Kaynakta eksik olan iki ürünün açıklama/teknik alanları bu sayımın dışında açıkça raporlanır.

Kaynak satıcının kupon/indirim kampanyaları mağazada ticari teklif olarak sunulmaz; bu gruplar nötr koleksiyon seçkileri adıyla korunur. Kaynak açıklaması satıcıya ait fiyat, kargo veya garanti taahhüdü içeriyorsa kamuya açık kısa açıklama yalnız ürün kodu, adı, ölçüsü ve renginden oluşturulur; tam kaynak metin arşivde korunur.

Kataloğu yeniden almak için PowerShell 7 ile `scripts/fetch-adore-catalog.ps1`, ardından `scripts/normalize-adore-catalog.py` kullanılır. Ayrıştırıcı Python bağımlılığı `requirements-catalog.txt` içindedir. Kaynak robots kuralları korunur; giriş gerektiren bayi stok/fiyat beslemesi ve ürün konfigüratörü bu kamuya açık aktarımın yerine geçmez.

Görseller `/media/ürün-kimliği/sıra?v=mediaVersion` üzerinden sunulur. PHP üretim rotası yalnız onaylı yerel dosyaları Turhost'un web kökü dışındaki kalıcı görsel kasasından okur; temizlenmiş ve değiştirilmemiş bütün onaylı dosyalar hostinge yüklenir. Eksik ya da değiştirilmiş dosya tedarikçi kaynağından tamamlanmaz. Sağ tık/sürükleme sınırlandırması tarayıcıda görüntülenen dosyaların mutlak kopya koruması değildir. Ürün paylaşımı, ekran görüntüsü ve metin kopyalama engellenmez.

## Google Drive

Kullanıcı Google Drive aşamasını erteledi ve görsellerin doğrudan hostinge yüklenmesini istedi. Gelecekte kullanılacak hedef `nodenohome@gmail.com` adresidir; hesap ve özel klasör henüz bağlı değildir. Bu sürüm Drive'a dosya yazmaz. İleride aktarım istenirse `scripts/drive-migrate.mjs` ve `docs/drive-setup.md` kullanılabilir; OAuth bilgileri hiçbir istemci dosyasına yazılmaz.

## Hesaplar ve işletim

Hazırlanan PHP paketi üyelik kodunu web kökü dışındaki `private/account.php` dosyasında taşır. Hesaplar, adresler, sepet/favoriler ve oturumlar `/home/nodenoho/nodeno-data` altında, sürüm dizinlerinden bağımsız saklanır. Yeniden yayın bu dizini içermez, üzerine yazmaz ve silmez. SQLite verisi ayrıca tutarlı biçimde yedeklenmelidir; yalnız public site yedeği hesap yedeği değildir.

Parola değişimi diğer oturumları geçersiz kılar. Hesap silme mevcut parola ve açık kullanıcı seçimi ister; gerçek sipariş kaydı bulunan hesabın silinmesi reddedilir. Sipariş API'si yalnız gerçek kayıtları okur; sipariş ve gönderi üretmez. E-posta doğrulama ve parola sıfırlama e-postası yapılandırılmamıştır; gönderim başarı mesajı verilmez. [Yayın otomasyonu](docs/deployment-automation.md) bu kalıcı veri ayrımını ve sürüm kabulünü açıklar.

## Satışa açmak için eksik işletme bilgileri

- E-posta hizmetinin ve müşteri iletişimi teslimatının doğrulanması.
- Yasal firma unvanı, adres ve ilgili satış/iadeler/gizlilik metinlerinin işletme tarafından tamamlanması.
- Onaylı NODENO fiyat listesi, vergiler, para birimleri, ülke bazlı teslimat bedelleri ve stok beslemesi.
- Gerçek ödeme kuruluşu hesabı, sunucuda doğrulanan ödeme/geri bildirim akışı ve iade süreci.
- Google Drive aktarımı kullanıcı tarafından ertelendi; mağazanın Turhost yayını için bağımlılık değildir.
- Uzun kaynak pazarlama açıklamaları için işletmenin isterse yapacağı bire bir metin çevirisi; mevcut yabancı dil kısa açıklamaları doğrulanmış ürün bilgilerinden uyarlanmıştır.

Bu bilgiler tamamlanmadan ödeme veya sipariş alınmış izlenimi açılmaz. **Adres ve özet** sayfası seçili ürünleri ve kayıtlı adresleri gösterebilir; ödeme düğmesi kapalıdır ve sipariş yazılmaz. 667 ürün ve 104 kategorilik katalog, gerçek üyelik ve hostingle sunulan görseller önceki Turhost yayınlarında doğrulanmıştır; güncel sürümün kabul kaydı belgenin başındadır. SSL sertifikası 29.01.2027 tarihinde sona erer. Hesapta AutoSSL kapalıdır; yenileme yardımcısı elle çalıştırılır ve zamanlanmış yenileme henüz kurulmamıştır.
