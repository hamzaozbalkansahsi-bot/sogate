# Ürün bilgisi ve keşif deneyimi

Bu kayıt, 17 Kasım 2026 ürün sayfası düzeltmesinin kapsamını ve doğrulama yöntemini tutar. Yayın sonucu ancak kabul ve dağıtım kanıtları oluştuğunda buraya eklenir. Hedef yalnız `https://sexogate.com/test`; ana site ve NODENO çalışma dizini kapsam dışıdır.

## Kaynak ve metinler

958 içe alınmış kaydın açıklama alanlarında 935 pazaryeri reklam metni ve 23 boş açıklama bulundu; özgün ham yanıt hashleri ayrıca doğrulandı. Bunlar ürüne ait açıklama sayılmaz. Bu bulgu, kaynak sitenin başka alanlarında veya sonradan yüklenen içerikte hiçbir ürün bilgisi bulunmadığı iddiası değildir. `product-editorial-data.json` değişmez kaynaktaki izinli nitelikleri ayırır; `editorial.php` yalnız ürün adı ve bu niteliklerden Türkçe/İngilizce anlatım üretir. Olmayan malzeme, ölçü, bakım, sertifika veya sağlık iddiası eklenmez. Kısıtlı kaynak bilgisi uzun dolgu metniyle gizlenmez.

Ürün başlığından marka tekrarları ve paket içeriğine ait yıldızlı ekler ayrılır. Paket bileşenleri ayrıca gösterilir. Ürün adı breadcrumb'ın son öğesidir; SKU ayrı ürün bilgisi olarak korunur. Orijinal kod, fiyat, varyant matrisi, stok ve inceleme engelleri değiştirilmez. Kullanıcının yönetimden yazdığı gerçek açıklama korunur.

## Ürün ekranı

- Bilinen özellikler küçük başlık/değer kartlarında; bütün bilgiler açılabilir bir listede gösterilir.
- İlk paragraf özet anlatımdır. Kaynakta gerçek devam bilgisi olduğunda “Devamını gör” açılır. Metinler paragraf, liste ve paket içeriği olarak ayrılır.
- İade ve iptal özeti aynı ürün ekranında açılır. Gerçek başvuru için iade merkezine ayrıca bağlantı verilir.
- Görselli koleksiyon kartları üç gerçek, yayımlanmış ürün görselinden oluşur. Sayılar gerçek katalog üyeliğini gösterir.
- Ana sayfadaki dört koleksiyon kampanya kartında fotoğraf, ayrılan alanın tamamını doldurur. İç giyim fotoğrafının odağı ürün bölgesindedir. Bu sunum yalnız kampanya kartlarına uygulanır; ürün kartları ve ayrıntı fotoğrafları ürünü bütünüyle gösterir.
- Benzer ürünler, öneriler ve son gezilenler yatay raftır. Satış verisi olmadan “Popüler” iddiası kurulmaz; “Seçili ürünler” kullanılır.
- Desktop kategori menüsü gerçek ürün fotoğraflı kartlar kullanır; boş kategoriler önerilmez. Footer marka bölümü gül metalik, uçları yumuşayan ince çizgiyle bağlantılardan ayrılır.

## Kalıcı etkileşim kuralları

Yatay raflarda sistem kaydırma çubuğu görünmez. Tema okları gerçekten gizlenir: başlangıçta sol ok yoktur; ilerleyince görünür, başa dönünce kaybolur. Son uçta sağ ok gizlenir. Kaydırma, klavye, RTL ve işletim sisteminin azaltılmış hareket tercihi korunur. Küçük fotoğraf şeridinde ek ok/çubuk yoktur.

Büyütülmüş galeri fare ve klavye ile iki yönde döngüseldir. Son fotoğraftan sonra ilk fotoğraf gelir. Fareyle kapatıldığında varsayılan siyah odak çerçevesi kalmaz; klavye odağı temayla uyumlu biçimde görünür.

## Kalıcı geri bildirim

`/api/product-feedback`, yayımlanmış ürün için izinli konu ve isteğe bağlı açıklama alır; sipariş veya değerlendirme üretmez. Aynı cihaz/işlem anahtarı tekrarında ikinci kayıt oluşmaz. Kimlik doğrulama çerezi, Origin, CSRF, gövde sınırı, ürün görünürlüğü, hız sınırı ve şifreli not uygulanır. Kullanıcıdan e-posta, adres, ürün tercih profili veya IP istenmez.

Yönetimde “Ürün geri bildirimleri” sayfası vardır. Kayıt durumları alındı/inceleniyor/çözüldü/reddedildi olarak sürüm kontrollü güncellenir. Yönetim oturumu ve MFA gerekir; katalog yetkileri sunucuda denetlenir. Notlar ve kayıtlar 180 gün, kısa işlem/hız kayıtları 24 saat tutulur; bunlar operasyonel tercihlerdir, kanuni zorunlu süre iddiası değildir. Kalıcı worker süreli temizliği yürütür.

## Yönetimde kullanım

`/test/yonetim/urun-geri-bildirimleri` sayfasını yetkili yönetim oturumu ve MFA ile açın. Durum filtresinden yeni başvuruları bulun; ayrıntıda ürün, konu, not ve işlem geçmişini inceleyin. Gerekli katalog düzeltmesini ürün düzenleyicisinde yapıp yayımlayın; ardından başvuruyu inceleniyor, çözüldü veya reddedildi olarak açıklamasıyla güncelleyin. Geri bildirim bir fiyat değişikliği, para iadesi veya müşteri değerlendirmesi oluşturmaz. Eşzamanlı değişiklik uyarısında kaydı yenileyip son durumu inceleyin.

Ürün düzenleyicisindeki “İncelenmiş ek galeri fotoğraflarını göster” alanı yalnız bu incelemeyle onaylanmış ek fotoğrafları yönetir. Kapatılıp yayımlandığında ek fotoğraflar vitrin ve medya erişiminden kaldırılır; eski onaylı kapak galerisi korunur. Yeni bir kaynaktan fotoğraf almak bu alanla otomatik onaylanmaz.

## Kaynak galeri denetimi

İlk gerçek kamu denetimi: 803 ürünün 770'inde tek fotoğraf vardı; bu ürünlerin 677'sinin kaynağında birden fazla fotoğraf bulunuyordu. Kapakla sınırlı aktarım eksikliği doğrulandı. Kaynak fotoğrafları ayrı özel önbellekte, orijinal byte ve SHA korunarak toplanır. Önceden reddedilmiş 46 fotoğraf otomatik olarak geri eklenmez.

Yeni galeri kayıtları ürün kimliği, değişmez ham kaynak SHA'sı, bütün eski medya hashleri, kaynak fotoğraf indeksi/URL'si ve gerçekten incelenmiş ek fotoğraf hashine bağlanır. Kaynak JSON değişmez; ek galeri onay katmanı ayrıdır. Görsel inceleme yapılmamış, yanlış ürün, açık cinsel eylem, belirsiz yaş, tedarikçi promosyonu veya doğrulanmamış sağlık iddiası taşıyan görseller yayına alınmaz. Normal üretici ambalaj markası, tedarikçi reklamından ayrı değerlendirilir.

Yönetici ek galeriyi kapatabilir. Galeri uç noktası güncel yayım/uygunluk/onay durumunu yeniden denetler ve `private, no-store` kullanır. Yalnız web kökü dışındaki hash dosyası sunulur; dış URL'ye sunucudan istek yapılmaz.

## Hosting belleği ve arşiv sınırı

İlk büyük galeri paketi, yerel PHP işçisinin varsayılan 128 MB sınırında durdu; başarısız paket etkinleştirilmedi. İnceleme, 2.194 arşiv kaydının yaklaşık 20,7 MB JSON içerdiğini ve her müşteri isteğinde gereksiz yüklenmesini buldu. Tam 3.152 kaynak kayıt ve hashleri yönetim/içe aktarma için korunur. Müşteri/işçi, aynı kaynaktaki 958 yeni kaydın doğrulanmış sıkıştırılmış görünümünü kullanır; yayımlanan küme 803 olarak kalır.

Ek galeri binding önbelleği yalnız küçük kimlik ve kaynak metadata'sı tutar. Fotoğraf isteği tek tam ürünü okur; tam ürünleri kalıcı belleğe eklemez. Yönetim bağlamı kullanılmayan mağaza hikâyesi yapılarını tutmaz; ad, fiyat, açıklama ve diğer iş verileri aynı kalır. Eski boş koleksiyonlar için SEO kodu gereksiz yüklenmez. 10.538 yerel dil/hikâye çıktısının hashleri sadeleştirme öncesi/sonrası eşleşti.

Yeni veri yolunun testleri, hash/bozuk gzip/boyut/veri kümesi eşleşmesini, yönetim 3.152 kayıt ve 2.194 başlangıç offset sözleşmesini ve gerçek 128 MB çalışmayı doğrulamak zorundadır. Yönetim şeması tam 3.152 kaydı kullanır; yalnız `GET /api/admin/products`, zaten SQLite'dan gelen 958 kayıt/803 yayımlanmış/155 inceleme listesini kullanır. Yazma ve içe aktarma yolları tam kaynağı korur. 80 MB kurulum açılım sınırı yükseltilmez. Son çalışan sürümün bellek ölçümü yayın kanıtına ayrıca yazılır; tek yerel ölçüm eşzamanlı hosting yükü garantisi değildir.

## SEO ve hukuk kaynakları

Kontrol tarihi: 17 Kasım 2026.

- [Google: taranabilir bağlantılar](https://developers.google.com/search/docs/crawling-indexing/links-crawlable).
- [Google: e-ticaret site yapısı](https://developers.google.com/search/docs/specialty/ecommerce/help-google-understand-your-ecommerce-site-structure).
- [Google: spam politikaları](https://developers.google.com/search/docs/essentials/spam-policies).
- [Ticaret Bakanlığı: mesafeli sözleşmeler](https://tuketici.ticaret.gov.tr/yayinlar/tuketici-bilgi-rehberi/mesafeli-sozlesmeler-hakkinda-bilgilendirme).

“Bunlar da ilgini çekebilir” bağlantıları gerçek ilgili kategori/marka sonuçlarına gider. Gezinti ve tarama içindir; anahtar kelime yığını, sıralama veya indekslenme garantisi değildir. `/test` ortamının noindex kuralı korunur.

İade özeti taslak işletme metnidir. Hijyen istisnası açılmış koruyucu unsur ve niteliği gereği sağlık/hijyen bakımından iadeye elverişsizlik koşulunu ayırır. Ayıplı ürün hakları kaldırılmaz. Kullanıcının sağlam paketleme ve taşıyıcıya teslim yükümlülüğü ayrıca açıklanır. Gerçek taşıyıcı/iade ödeme/fatura işlemleri kabul edilmeden açılmaz.

## NODENO koordinasyonu

Kullanıcının açık talebiyle “NODENO satış sitesini oluştur” sohbetine ürün bilgisi, açıklama, iade, geri bildirim, öneri, görselli kategori, başlık ve footer kapsamı iletildi. Bu, NODENO tarafının tamamlandığı veya yayımlandığı anlamına gelmez. Kullanıcının kendisinin ilettiğini belirttiği galeri, kaydırma ve breadcrumb talimatları tekrar gönderilmedi.

## Doğrulama ve yayın durumu

Etkin test sürümü **`929ff578f9c4828e5752174f`**, veri kümesi `057fb50f7d5887fee341e3d5b4a3dd64` ve arşiv SHA `3e2d80bf0ce5c376251b6955b66346981204efd8f392284d165a10cb48f23dab`. [Kanonik yayın raporu](native-deployment-report.json) `active_verified` durumundadır. Yayın yalnız [sexogate.com/test](https://sexogate.com/test) kapsamındadır; ana site, NODENO ve diğer sohbetlerin alanları değişmedi. Gerçek tahsilat kapalıdır.

958 yeni yönetim kaydının 803'ü görünür, 155'i incelemededir; 44 kaynak kayıt ertelenmiştir. Tam 3.152 kaynak/arşiv kaydı korunur. 59 kategori tanımı, 37 dolu kategori ve 5 dolu kök vardır. Fiyat, `seo-` SKU, varyant matrisi, stok ve yayın engelleri bu içerik/galeri düzeltmesiyle değiştirilmedi.

935 reklam/23 boş bulgusu, aktarılmış açıklama alanlarına aittir; kaynak sitenin bütün ürün bilgisinin bulunmadığı anlamına gelmez. Mevcut gerçek niteliklerden TR/EN anlatım üretildi; 418 başlık temizlendi, yönetici metni ve özgün özel kaynaklar korundu. Kaynakta olmayan özellik, bakım, malzeme, sertifika veya sağlık vaadi eklenmedi. 551 ürüne 1.523 ek galeri slotu/1.443 özgün varlık bağlandı: toplam 874→2.397 slot, 236 tek fotoğraf/567 çok fotoğraflı ürün. 991 slot beklemede, 14 tekrar dışarıda; önceki 46 ret geri açılmadı.

Tam kabul yerelde **16 grup/19 gerçek komut**, özel önizlemede **15 grup/16 gerçek komut** geçti. Ürün deneyiminin **21 davranışı**, Chromium/WebKit ile yerel, önizleme ve etkin test alanında aynı release/dataset üzerinde 6 gerçek yürütmeyle doğrulandı; genişlikler 360/390/430/768/1440 px. Güncel özel önizleme ve önceki V7 önizlemesi kaldırıldı; ana site hash'i korundu. Kampanya kartları gerçek V8 CSS'iyle, yanıt değiştirme/stil ekleme/CSP aşma olmadan 10 hedefli senaryoda ayrıca kontrol edildi. Hedefli smoke'un `fullReleaseAcceptance=false` durumu korunur; tam kabulün yerine geçmez.

| Gerçek kontrol | Sonuç |
| --- | --- |
| `python -B -X utf8 scripts/test-native-product-modules.py` | 10 komut; JS ürün/menü/galeri 21/16/11; PHP ürün 22, editoryal 23.022, geri bildirim 48/48, galeri 72/72, runtime 82. |
| `python -B -X utf8 scripts/test-native-product-runtime-memory.py` | 4 gerçek PHP CLI yolu, `memory_limit=128M`; worker/customer/adminSchema/adminProducts 74/86/122/66 MiB. |
| `python -B -X utf8 .local/resume-product-experience-local-v8.py` | Önceden geçen 13 grup korundu; kesilen 6 grubun 6 gerçek yürütmesi kaydedildi; son tam kapı 16 grup. |
| `python -B -X utf8 scripts/run-native-marketplace-acceptance.py --scope preview --base https://sexogate.com/test/native-preview-5204cb2040336112` | 15 kabul grubu/16 gerçek komut; sonrasında önizleme emekliye ayrıldı. |
| Kaynak/PHP/kurulum/SEO/iade | 6/2884/32/70.665 kontrol; 8.833 SEO sayfası; iade çekirdeği 53, sıralama 17. |

İlk V8 yerel koşu, eski `polish` testinin kampanya fotoğrafını `contain` beklemesi yüzünden `CROPPED_PRODUCT_IMAGE` hatası verdi. Orijinal hata/log/hash ve 13 başarılı grup korundu. Yalnız test beklentisi kampanya `cover`, ürün fotoğrafı `contain` ayrımına uyarlandı; kalan altı grup 6 gerçek yürütmeyle tamamlandı ve tam kabul kapısı yeniden geçti. Bu hata uygulama değişikliği gizlenerek veya assertion kapatılarak geçirilmedi. Önceki c3 ham kaynak okuma zaman aşımı ve yeni kullanıcı isteği nedeniyle durdurulmuş, hiç etkinleşmemiş V7 önizleme ayrı tarihsel kanıtlardır.

Etkin V8 ilk kontrolünde iki tarayıcı işi sürerken ürün testinin ekranında “503 Service Unavailable / temporarily busy” yazısı görüldü; özgün gezintinin HTTP durum kodu kaydedilmedi. İlk başarısızlık, log ve ekran hashleri korundu; HTTP, gezinti ve iade grupları geçmişti. Değişmeyen güçlü ürün testi daha sonra tek iş olarak iki motorda geçti. Bu yalnız işlevsel tekrardır; kök neden ve eşzamanlı kapasite doğrulanmış veya düzelmiş sayılmaz.

Doğru hesabı doğrulayan iki salt okunur cPanel isteği HTTP 200/API success ile tamamlandı. 17 Kasım 17:01:45–46 UTC istek aralığındaki tek toplu örnekte kullanım/üst sınır: CPU 83/100, bellek 167.862.272/1.073.741.824, IOPS 0/2000, IO 2.418.688/104.857.600, süreç 3/100. Entry-process, fault/geçmiş ve sayaç zaman damgası verilmedi. Bu tek örnek önceki meşgul sayfanın kök nedenini veya kapasite yeterliliğini kanıtlamaz. [Kaynak kullanım tanısı](native-product-experience-active-resource-diagnostic.json), [resmî cPanel uç nokta belgesi](https://api.docs.cpanel.net/specifications/cpanel.openapi/resource-usage-and-statistics/resourceusage-get_usages).

Güncel şifreli yedek **2 DB/56 tablo/22.944 satır** olarak gerçek geri yükleme ve foreign-key kontrolünden geçti. Yayın öncesi e7 yedeği 2 DB/52 tablo/22.889 satır olarak ayrıca geri yüklenmişti. Worker ve cron sağlığı, başka cron işlerinin korunması, özgün medya hashleri ve ana sitenin değişmemesi raporda kayıtlıdır. Veritabanı geri yüklemesi bütün medya yedeğinin geri yüklenmesi sayılmadı. 128M ölçümü yerel PHP CLI'dır; admin şemasının 122 MiB tepe değeri hosting altında eşzamanlı yük garantisi değildir.

Kaynak commitleri `cf6c7d2`, `91ffa0b`, `fe325e7`, `ac14afa`. Güncel CI kaydı `ac14afa187e3ae845692df892435953f8f589a41` için iki resmi GitHub işi, faturalama kilidi yüzünden **0 test adımıyla başarısız**: yerel/önizleme kabulü CI başarısı değildir.

**Açık işler ve sınırlar:** CWV saha ölçümü ve LCP/INP/CLS hedefleri, kontrollü eşzamanlı hosting yükü, fiziksel cihaz testi ve bütün medyanın yedekten geri yüklenmesi doğrulanmadı. 551 galeri binding dosyası/3.946.911 byte okuma yolu açık optimizasyon konusudur; V7 altında alınmış iki kontrolsüz katalog GET örneği V8 performans kabulü veya gecikmenin kök neden kanıtı değildir. Etkin V8 meşgul sayfa olayı için kök neden/kapasite konusu açık kalır; son sıralı işlevsel geçiş bunu kapatmaz. Gerçek tahsilat, para iadesi, fatura düzeltmesi ve taşıyıcı işlemleri işletme/hukuk/sağlayıcı kabulleri tamamlanmadan kapalıdır.

Gerçek V8 kampanya ekranları: [Chromium 390](screenshots/native-store-product-experience-campaign-v8/chromium-390.png), [Chromium 1440](screenshots/native-store-product-experience-campaign-v8/chromium-1440.png), [Webkit 390](screenshots/native-store-product-experience-campaign-v8/webkit-390.png), [Webkit 1440](screenshots/native-store-product-experience-campaign-v8/webkit-1440.png). Diğer kanıtlar: [yerel kabul](native-product-experience-local-acceptance.json), [önizleme kabul](native-product-experience-preview-acceptance.json), [etkin iki motor kontrolü](native-product-experience-active-results.json), [modüller](native-product-experience-module-results.json), [128M bellek](native-product-experience-memory-results.json), [galeri incelemesi](native-product-experience-gallery-review.json), [gerçek kampanya smoke'u](native-product-experience-campaign-layout-smoke.json), [ilk V8 hata](native-product-experience-v8-failed-attempt.json), [etkin alandaki meşgul sayfa olayı](native-product-experience-active-availability-incident.json), [ayrı sıralı işlevsel tekrar](native-product-experience-active-sequential-retry.json), [CI](native-product-experience-ci-results.json).
