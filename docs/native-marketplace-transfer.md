# Pazaryeri katalog değişimi — 16 Kasım 2026

Kullanıcı eski vitrinin kaldırılmasını, Trendyol/Hepsiburada yetişkin ürünleri, fantezi giyim/kostüm, çift oyunları, zar/kart ve ilgili aksesuarların kaynak kodları korunarak `seo-` önekiyle alınmasını istedi. Fotoğraf/açıklama kullanım ve platform/tedarikçi logosu temizleme iznini bu iki kaynak için de ayrıca beyan etti. Yazılı sözleşme veya pazaryeri hesabı varlığı iddia edilmez. Gerçek üretici/marka/GTIN/model kimliği ve ürün üzerindeki güvenlik bilgileri değiştirilmez.

## Gerçek uygulama

- Eski 468 görünür ürün, önce izole yerel deneme ve SQLite yedeği; sonra taze şifreli, gerçekten geri yüklenmiş sunucu yedeği ardından mevcut MFA’lı yönetim API’siyle yayından kaldırıldı. Bu arşiv aşamasında etkin paket `0c0e76d696171c6fba60f5da` idi.
- Arşiv aşamasında `/test` kamu kataloğu 0; 2.194 yönetim kaydı, sürüm geçmişi, fiyatlar ve sipariş ilişkileri silinmedi. Bu işlem yalnız `unpublish`; kök hazırlanıyor sayfası, DNS, gerçek tahsilat ve diğer projeler aynı. Git dışı sonuçlar `.local/catalog-archive-local-20261116.json` ve `catalog-archive-remote-20261116.json`.
- İndirimsiz tutarın +%15’i alt birimde yarım yukarı yuvarlanır. `seo-` özgün `productCode` önüne eklenir; üretici kodu içindeki anlamlı parçalar silinmez. Platform model ID’si, gerçek kaynak kodu ve barkod farklı alanlardır. Fiyat veya gerçek kod eksikse değer uydurulmaz.
- Trendyol sayfasındaki `sellingPrice`, kuponlu/Plus/sepette indirimli fiyattan ayrı alınır; alan yolu ve ham fiyat nesnesi kanıtı saklanır. Örnek sayfada `originalPrice` alanı 1.779,62; indirimsiz, üstü çizili `sellingPrice` 1.999,62 olduğu için yalnız alan adına güvenilmedi. Tavsiye edilen perakende fiyatı fiyat tabanı yapılmaz.
- Yerel ayrıştırıcı `scripts/native_marketplaces.py`, 8 kontrolü geçen `test-native-marketplaces.py`; kalıcı SQLite kuyruk aracı `collect-native-marketplaces.py`. Kimlik, beden/renk, açıklama, görsel URL ve gözlem zamanı tutulur; satıcı şirket/adres/vergi bilgileri, yorumlar, puanlar, rozetler ve satış iddiaları aktarım DTO’suna alınmaz. Kaynakta bulunabilirlik depo stoğu veya bayilik/tedarik kabulü değildir.

## Erişim ve tamamlanma durumu

İlk dondurulmuş paket için Trendyol kamu kategori/ürün sayfalarından 138 ayrı ürün ayrıntısı ve 28 kaynak kategori alındı. Ham yanıtlar, gözlem zamanları ve 138 özgün kapak görseli Git dışı saklanır. Görseller gerçekten incelendi; logo/iddia/içerik incelemesi bekleyenler otomatik yayımlanmaz. Görsellerin baytları değiştirilmedi; ürün üzerindeki gerçek üretici ve güvenlik işaretleri korunur.

131 ürün yönetim aktarımına hazır: 80 görseli ve yayın koşulları incelenmiş vitrin ürünü, 51 özel inceleme kaydı. Yedi kaynak ürün gerçek kod eksikliği veya kod çakışması nedeniyle ertelendi. 40 üründe gerçek beden/renk matrisi var; matris seçimleri olmadan sepet satırı oluşturulamaz. Yerelde gerçek MFA yönetimi üzerinden iki kez aktarım, geçmiş fiyatın korunumu, özel taslak medyası ve “Ürüne git” yeniden yükleme sonrası sınandı. Bu paragraf uzak yayın tamamlandı anlamına gelmez; güncel etkin sürüm aşağıdaki yayın kanıtına göre kaydedilir.

İkinci kuyruk ilk paketi değiştirmeden ayrı yürütüldü: `seks-oyuncaklari-y-s8150` kategorisinde 11 gerçek sayfa; toplam 487 kayıt içinde 382 ayrıntı hazır, 105 inceleme gerektiriyor. Bu kayıtlar yayımlanmadı. Tek istek/saniye, 401/403/429 durumunda durma uygulanır. Bütün kategori veya bütün pazaryeri aktarıldı iddiası yoktur.

Trendyol `/sr` ve Hepsiburada kamu kategori/ürün uçları HTTP403 verdi. Engellenen uç tekrar zorlanmadı; proxy, CAPTCHA aşma veya kimlik döndürme yapılmadı. Hepsiburada arama önbelleği güncel fiyat/katalog kanıtı sayılmadı ve ürün aktarılmadı. Resmî satıcı API’leri başka satıcıların bütün pazaryeri kataloğunu indirme yetkisi olarak yorumlanmaz: [Trendyol belgeleri](https://developers.trendyol.com/tr/), [Hepsiburada katalog açıklaması](https://developers.hepsiburada.com/tr/companies/hepsiburada?guide=katalog-onemli-bilgiler&product=katalog-urun-entegrasyonu&view=guide).

**Tam katalog aktarımı tamamlanmadı.** Kaynak sayısı, incelenen ayrıntı, yönetim kaydı ve kamu ürünü ayrı sayılır. Kaynak bulunabilirliği kendi depo stoğu veya tedarik sözleşmesi değildir. Satışın kapalı olması fiyat, görsel veya SKU uydurmayı gerektirmez.

## Son fiyat ve erişim kararı

Kullanıcı kaynak indirimsiz 1.000 TL → **1.150 TL nihai satış fiyatı** kararını verdi. Ek %20 Kasım indirimi uygulanmaz; pazaryeri eski fiyatı SEXOGATE indirim geçmişi sayılmaz. Kullanıcı bilinen ürün sayfalarının tek tek okunmasını istedi. Engellenmiş `/sr` toplu araması tekrar edilmeden ilk 36 ürün ayrıntısından başlanarak ilk paket 138 ayrı ayrıntıya ulaştı. Bu ayrı uçların başarılı olması tam katalog erişimi veya Hepsiburada kabulü değildir. Görsel, kod, varyant ve yayımlanma durumları ayrıca doğrulanır.

Kategori düzeltmesi: kaynak Fantezi İç Giyim3096/Fantezi Kostüm3097 ve gerçek oyuncak kategori kimlikleri, başlıktaki belirsiz “hediye/şarj/harness” alt dizilerinden önce değerlendirilir. Dokümanı olmayan dikleştirme/ilişki süresi gibi iddialar incelemeye alınır; kategori kapağı ilgisiz ürünle doldurulmaz. İlk82 adaydan iki ek iddia engeliyle80 aday kaldı. Dört dolu kök: iç giyim24, çift ürünleri10, oyuncaklar43, aksesuar3; bakım/hediye boşluğu uydurma ürünle kapatılmaz.

SEO regresyonu: markası bilinmeyen üründe yanlış kapsamlı marka kancası SSR503 üretiyordu; kendi türetme katmanında düzeltildi.80yayın adayı×11dil=880sayfa/7.041kontrol; uyarılar hata, gerçek SKU/fiyat, sahte marka/puan/stok bilgisi yok. Kaynak NODENO değiştirilmedi. `scripts/test-native-marketplace-seo.php` bu koşulu her yayın kanıtında zorunlu sınar.

## 17 Kasım etkin test yayını

`https://sexogate.com/test` sürümü `b5e7e6913484a652360a2097`:131yeni yönetim kaydı/80kamu ürünü/51inceleme. Eski2.194yönetim kaydı korunur ve eski468ürün yeniden yayımlanmaz. Yönetimde yeni ürünleri `seo-` koduyla arayın; yayımlanmış üründe **Ürüne git** bağlantısı kaydı yeniden yükledikten sonra da çalışır. Kaynak alanı veya belge belirtilmemişse veri uydurulmaz.

Yerel14, gerçek sunucu önizlemesi13 kabul grubu geçti. Etkin adreste Chromium/WebKit yönetim MFA+ürün listesi ve9müşteri rotası, iade girişi, güvenlik başlıkları ve gizli dosya engelleri yeniden sınandı. Geçici önizleme kaldırıldı. Öncesinde ve sonrasında gerçek şifreli veritabanı geri yükleme yapıldı; mevcut cron işleri korunarak yeni worker doğrulandı. Ana hazırlanıyor sayfası/DNS/gerçek tahsilat değiştirilmedi. Kanonik kanıt `native-deployment-report.json`.

Tam pazaryeri aktarımı tamamlanmış değildir; Hepsiburada403 ve ikinci244ek hazır ayrıntının içerik/görsel incelemesi açıktır. Gerçek para iadesi/taşıyıcı/fatura API bağlantısı yerine test veya denetlenmiş manuel referans kullanıldığı açıkça ayrılır.
