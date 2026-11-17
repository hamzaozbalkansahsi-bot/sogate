# 17 Kasım katalog genişletme

Bu çalışma yalnız `/test` kataloğunu büyütür. Ana hazırlanıyor sayfası, DNS, gerçek tahsilat ve diğer sohbetlerin dosyaları kapsam dışıdır. Önceki `b5e7e6913484a652360a2097` sürümü ve ilk dondurulmuş138 kaynak ayrıntısı değiştirilmez.

## Kaynak ve karar izi

`collect-native-marketplace-expansion.py` önceki ayrı araştırma kuyruğunun SQLite yedeğini alır; gerçek kategori sayfaları ve tekil ürün ayrıntılarını, sayfa numarası/kimlik/hash/zaman kanıtlarıyla okur. 401/403/429 durumunda durur. Yalnız aynı ürün kimliğine ve izinli aynı kaynağa yönlenen kanonik adres kabul edilir; çerez, proxy veya kimlik döndürme kullanılmaz. Hepsiburada403 engeli devam eder; bu kaynaktan ürün alındığı iddia edilmez.

Araştırma alanı `marketplace-expansion-20261117-research`, hazırlık alanı `marketplace-catalog-20261117` olarak ayrıdır. Mevcut16Kasım alanı donmuştur. Önceki ham dosyalara hardlink kullanılırsa yeni gözlem dosyası geçici dosya+atomik değiştirmeyle yazılır; eski inode üzerine yazılmaz. Hazırlayıcı her ham yanıtın SHA256 değerini gerçek baytlardan denetler. Son seçilmiş veri kümesi tekrar üretim için açılmaz.

Kaynak indirimsiz tutar `merchantListing.winnerVariant.price.sellingPrice.value` alanından doğrulanır. Final fiyat alt birimde `(kaynak×115+50)//100`; kuponlu/current/sepette indirimli fiyat veya tavsiye fiyatı taban yapılmaz. Ek Kasım indirimi yoktur. Gerçek ürün kodunun önüne yalnız `seo-` gelir; çakışma veya kod eksikliği ertelenir. İlk131 kimlik/SKU önceliği korunur.

## İlk51 inceleme kaydı

İnceleme denetimi51 ürünün gerçek başlık, kategori, beden, fiyat ve tüm kaynak galerisini özel kayıtta toplar. Önceki44 kapak için genel inceleme işareti, belirli bir logo/içerik sorunu kanıtı sayılmaz. Fotoğraf ancak gerçekten görüldükten ve hash'i eşleştirildikten sonra onaylanır. İnceleme paftaları yalnız özel küçük önizlemedir; sunulan ürün fotoğrafının baytları değiştirilmez. Üretici/ürün üstündeki gerçek kimlik ve güvenlik işaretleri korunur.

`native_marketplace_review_rules.py` yalnız15 denetlenmiş yetişkin oyuncağı kimliği için onaylı, olgusal kopya düzenlemesi sağlar. Orijinal başlık/iddia/açıklama/özellikler özel inceleme kaydında kalır. İlaç veya tedavi ürününün adı değiştirilerek yayımlanması sağlanmaz. Üç ürünün yalnız gerçek indirimsiz fiyatı kanıtlanmış seçili bedeni sunulabilir; diğer seçenekler kaynakta stok yokmuş gibi gösterilmeden özel gerekçeyle sunumdan ayrılır. `AJM9106` kaynağındaki `0-3 AY` tutarsızlığı bütün ürünü kapalı tutar. Öğrenci/okul/lise kodlu rol kıyafetleri koleksiyona alınmaz.

`native_marketplace_taxonomy.py` ham kaynak başlığı ve gerçek kategori ağacını kullanır. Üretilmiş İngilizce grup açıklaması sınıflandırma girdisi olmaz. Boxer/kostüm, kılıf/prezervatif, aksesuar/oyuncak ve zar/kart türleri ayrı ele alınır. Bilinmeyen kategori otomatik oyuncak sayılmaz. Eksik üretici, belge, maliyet, depo stoğu veya ülke kabulü uydurulmaz.

## Yerel kabul ve yayın

İlerleyen adımlar: kaynak/görsel incelemesini dondur; bağımsız veri, ham hash, fiyat, matris, yol kaçışı, içerik inceleme testlerini çalıştır; aynı PHP paketiyle yerel kabulü tamamla; gerçek sunucu önizlemesini sına; sonra yalnız `/test` etkin işaretçisini değiştir. Ana site dosya parmak izi her dış mutasyonda karşılaştırılır. Şifreli yedek yalnız indirilmez, SQLite bütünlük/yabancı anahtar/tablo sayılarıyla gerçekten geri yüklenir.

Yeni kayıtlarda mevcut MFA yönetim API'si kullanılır. İlk51 dokunulmamış taslağın yükseltilmesi donmuş ilk alanlar, sürüm ve fiyatla karşılaştırılır; elle düzenlenmiş, yayımlanmış veya eşzamanlı taslak ezilmez. `Ürüne git`, kaynak alanları ve SEO alanları korunur.

Çalıştırılan komutlar ve güncel yayın sayıları kabul sonrasında bu kayda eklenir. Araştırma sayısı, yönetim kaydı ve görünür ürün sayısı ayrı raporlanır; tam pazaryeri aktarımı veya canlı satış kabulü iddia edilmez.

## Yerelde doğrulanan genişletme

Kaynak havuzu1.010tekil kimlik:1.002gerçek ayrıntı ve8kapsam dışı gençlik/okul kodlu kayıt.24kategori sayfası,8kategori yolu; eski105teknik inceleme kaydı gerçek kaynaklardan çözüldü.17eski+6yeni kanonik yönlendirme için aynı ürün kimliği kanıtı tutulur.32gerçek kodun iç boşlukları yeni ayrıştırmada korundu;43kod çakışması ve1eksik indirimsiz fiyat ertelendi. Hazırlık958yeni yönetim ürünü/803vitrin adayı/155inceleme; eski2.194arşiv aynı.35kaynak kategori ve59mağaza kategori tanımı var; vitrinde37dolu kategori/5dolu kök bulunur. boş kök ürün uydurularak doldurulmaz.

İlk51ürünün45için içerik/görsel/seçenek sorunu çözüldü. Üç fiyat matrisinde yalnız kanıtlı winner bedenleri sunulur. Kalan6: `seo-AJM9106` yetişkin bedenleriyle `0-3AY` tutarsızlığı; `seo-KokteylFWM1` ve `seo-g6` görsellerinde kanıtsız iddia/gönderim vaadi; `seo-v-0009990` tedarikçi işareti; `seo-TM0027` gizleme işareti; `seo-FU1032` teyitsiz paketleme vaadi. Bu ürünlerin bütün kaynak galerileri incelendi. Yeni bir fotoğraf düzenleme/marka temizleme yapıldığı iddia edilmez.

Kaynak fotoğraflarında1.119hash doğrulanmış orijinal dosya yerel önbellekte; üç özel pafta manifestiyle gerçek inceleme kararları hash üzerinden bağlanır. Uygun alternatif kapak sırası sıfırdan farklı olabilir; tarayıcı testi seçilen gerçek kapağın hash’ini denetler.

Paket `e7f4feeb57497118bdaf4dd3`, veri kümesi `057fb50f7d5887fee341e3d5b4a3dd64`:3.152kaynak ürün,2.492manifest dosyası,12.504.223baytZIP/68.842.576baytaçılmış toplam. Gerçek katalog26.608.812bayta ulaştığı için yalnız tam `private/catalog.json` girişinin sınırı32.000.000bayt oldu; diğer dosyalar25.000.000/toplam80.000.000/5.000dosya üst sınırında. Saf kurucu negatif kontrolleri yeni sınırın üstünü ve diğer dosya/toplam sınırlarını reddeder.

İlk derlemede seçenek derleyicisi128MB sınırını aştı. Aynı3.152şemayı eski yöntemle256MB altında ölçen gerçek karşılaştırmada tepe163.577.856bayttı; her kaynak kovasını tek kez okuyup bırakan uygulamada128MB bütçe altında109.051.904bayt ve tam şema eşliği doğrulandı. Seçenek10JS testi önce/sonra geçti. Kontrol kapatılmadı, genel bellek sınırı büyütülmedi.

Çalışan yerel komutlar: `test-native-marketplaces.py`9, `test-native-marketplace-paths.py`23, `test-native-marketplace-taxonomy.py`24, `test-native-marketplace-review-rules.py`20, `test-native-marketplace-import-guard.py`14 ve `test-native-marketplace-acceptance.py`20 test geçti. Toplayıcının `--self-test` sözleşmeleri geçti. Kaynak kabulü6veri/2.884payload/32kurucu/70.665SEO/53+53iade/17+17olay-sıralama kontrolü geçti.803ürün×11dil=8.833SSRürün sayfası. Kaynak okumaları dondurulmuş ilk alan için salt okunur/immutable ve doluWAL reddiyle yapılır.

Yerel MFA aktarımında958kayıt/803görünür ürün doğrulandı. İlk80yayın kaydı hash eşliğiyle korundu;45eski incelemenin27si zaten güvenli aktarım yoluyla,18i donmuş alan/sürüm/fiyat karşılaştırmasıyla yükseldi. Gerçek para, fatura veya taşıyıcı API çağrısı yok. Bu bölüm tek başına uzak yayın kanıtı değildir; etkin yayın sonucu ayrıca kaydedilir.

## Müşteri açıklamalarının ayrı CMS düzeltmesi

Yerel fonksiyonel kabuller mevcut pakette geçti. Son metin denetiminde803kamu ürününün785inde kaynak LD açıklamasından gelen `yorumlarını inceleyin, Trendyol’a özel…satın alın` reklam cümlesi bulundu. Bu cümleler ürün özelliği değildir. `native_marketplace_copy.py` yalnız platform+bilinenCTA birlikte bulunan tam cümleyi ayırır;2.6cm gibi ondalıklar, SKU, fiyat, ölçü ve diğer diller korunur.20saf ve gerçek kaynak denetimi geçti.

Bu düzeltme yeniden kaynak üretimi veya NODENO değişikliği değildir. Gerçek MFA yönetim API’si ve mevcut CMS sürüm geçmişiyle yalnız dondurulmuş16/17ilk alanları tamamen eşleşen mevcut kamu kayıtları güncellenir. Elle düzenleme/eşzamanlı taslak engeldir; başka alan veya gizli ürün yayımlanmaz. PUTsonrası freshGET ve expected-versionPUBLISH; bağlam+veri kümesiyle bağlı kalıcı niyet ve doğrulanmış yeniden okuma gerekir. Kaynak/hash/fiyat/noncopyalan koruması ve785düzeltmenin gerçek HTTPsonucu `.local/native-marketplace-copy-<scope>.json` içinde tutulur. Satıcı/platform kaynağı özel inceleme alanında korunur; müşteri metninden reklam cümlesinin kaldırılması gerçek marka kimliğini değiştirmez.

Yayın kapısı müşteri metni kanıtını da zorunlu tutar: yerel15/önizleme14grup; önceki14fonksiyonel grup raporu ayrıca saklanır.20negatif kapı testi eksik/eski/yanlış kaynak/sürüm/sayı ve korunmayan alan kanıtını reddetti. CMSdüzeltmesi sonrası uygun metin/SSRkontrolü eklenir; etkileşim testleri daha önceki gerçek çalıştırmalardır, tekrar çalıştırılmış diye gösterilmez.

Önizlemede ilk ürün düğmesi testi390px ekran yakalarken kur isteğinin tamamlanmasıyla DOM yenilendi ve `Element is not attached` verdi. Uygulama kaynağı değiştirilmedi; test yalnız gerçek kur isteğinin sonlanmasını en fazla20s bekleyip render/font hazırlığını tekrar denetler. Geometri, tek satır,44/48px hedef, favori/karşılaştırma/seçim/paylaşım ve RTL koşulları korunur. Yerel ve gerçek önizleme iki motorda yeniden geçti; başarısız ilk deneme kaydı saklandı. Ek yerel gerçek gözlemde kur beklerken yazılan3adet ve odak korundu; kaynak incelemesindeki olası miktar kaybı yeniden üretilmedi. Bu fonksiyonel bekleme performans hedefinin geçtiği iddiası değildir.

<!-- BEGIN EXPANSION_ACTIVE_20261117 -->
## 17 Kasım genişletilmiş etkin test yayını

Yalnız `https://sexogate.com/test` üzerinde `e7f4feeb57497118bdaf4dd3` / `057fb50f7d5887fee341e3d5b4a3dd64` etkin ve yeniden doğrulandı. Vitrin 80 üründen **803 ürüne** çıktı; **958 yeni yönetim kaydı**, 155 inceleme kaydı, 59 kategori tanımı/37 dolu kategori/5 dolu kök var. İlk 51 incelemenin 45'i çözüldü; altı gerçek engel [inceleme raporunda](native-marketplace-old-review-results.json). 1.002 gerçek kaynak ayrıntısının 43 kod çakışması ve bir eksik indirimsiz fiyat nedeniyle 44'ü ertelendi. Eski 2.194 arşiv kaydı korunur ve vitrinde gösterilmez. Özgün kod `seo-` ile, indirimsiz fiyat +%15 nihai tutarla saklandı; ek Kasım indirimi yok.

Yerel 15, gerçek önizleme 14 kabul grubu geçti. Önizlemede 785 ürünün pazaryeri reklam cümlesi CMS sürümleriyle temizlendi; etkin adreste tekrar kontrol 0 değişiklik/0 kalan CTA ile idempotent geçti. Fiyat, SKU, varyant ve diğer alanlar korundu. 803 ürünün kapak hashleri iki motorda gerçek HTTP ile sınandı. Etkin adreste Chromium/WebKit MFA yönetimi, 9 müşteri rotası, beş ekran genişliği, iade girişi ve özel dosya erişim engelleri yeniden geçti. Geçici önizleme kaldırıldı. Kaynak SEO kontrolü 803×11=8.833 sayfa/70.665 denetimdir; organik sıralama veya saha performansı sonucu değildir.

Ana site parmak izi aynı; DNS ve diğer sohbetlerin işleri değişmedi. Mevcut cron işleri korunup yeni worker heartbeat'i doğrulandı. Şifreli yedek gerçekten açılıp 2 veritabanı/52 tablo/22873 satır ve yabancı anahtarlar denetlendi; tam medya geri yükleme çalıştırılmadı. 9.607 özel medya dosyası hash ile doğrulandı. Gerçek tahsilat/para iadesi/taşıyıcı/e-belge API'leri kapalı; yerel ödenmiş fixture sunucuya taşınmadı. Hepsiburada403 ve tam pazaryeri kapsamı açıktır.

GitHub Actions hesap faturalama kilidi nedeniyle 0 adım çalıştırdı; CI başarılı sayılmaz. Kanonik [yayın raporu](native-deployment-report.json), [genişletme kılavuzu](native-marketplace-expansion.md), [yerel kabul](native-marketplace-local-acceptance.json) ve [önizleme kabulü](native-marketplace-preview-acceptance.json) gerçek sonuçları ayırır.
<!-- END EXPANSION_ACTIVE_20261117 -->
