# Personel sipariş ayrıntısı ve paket hazırlığı

Siparişler ve ödemeler listesinden **Siparişi aç** seçilir. Ekran ve API aynı rol sınırlarına uyar; gizli alanları yalnız arayüzde saklamakla yetinilmez.

| Rol | Sipariş ayrıntısındaki kapsam | İşlem |
|---|---|---|
| Depo / sevkiyat | Yalnız ödemesi doğrulanmış siparişin SKU/adetleri, paketleri, gerekli teslimat adı/adres/telefonu; maliyet, fiyat/toplam, e-posta, ödeme referansı ve geçmiş yok | Toplama, paketleme, manuel sevk |
| Müşteri hizmetleri | Sipariş/adet/sevk, ilgili iletişim ve teslimat; maliyet/finansal ödeme referansı yok | Bu ekranda salt okunur; iade mevcut ayrı akışta |
| Finans | Sipariş/adet/sevk ve tahsilat/iade tutarları; müşteri adresi/e-postası yok | Bu ekranda salt okunur; para iadesi mevcut ayrı yetkili akışta |
| Yönetici | Operasyon ve finans alanları | Toplama, paketleme, manuel sevk |
| Katalog, pazarlama, müşteri | Personel sipariş ayrıntısına erişim yok | Yok |

Her istek doğrulanmış, süresi geçmemiş MFA oturumu gerektirir. API: `GET /api/admin/orders/{id}`; işlem: aynı adrese POST. Yanıtlar `private, no-store` ve `noindex,nofollow` taşır.

## Yeni paket hazırlama

1. **Paket adedi · SKU** alanlarında bu pakete girecek miktarları seçin ve **Paket hazırlığı oluştur** düğmesini kullanın. Kalan sipariş adedinden mevcut sevkler ve diğer aktif hazırlıklar düşülür. Aynı adedi iki personel eşzamanlı olarak ayıramaz.
2. Toplama sırasında üreticinin kayıtlı gerçek barkodunu okutun veya siparişteki SKU'yu girin. **Doğrulanan adet** ile **Toplamayı doğrula** işlemini tamamlayın. Eşleşmeyen kod veya fazla adet reddedilir; barkod yoksa uydurulmaz.
3. Tüm ürünler toplandığında paketleme kontrolü açılır. Ürünü pakete koyarken SKU/barkodu tekrar doğrulayın ve **Paketlemeyi doğrula** düğmesini kullanın. Toplama bitmeden paketleme, paketleme bitmeden bu akıştan sevk yapılamaz.
4. Sevke hazır pakette taşıyıcının gerçek belgesindeki **Gerçek taşıyıcı adı** ve **Gerçek takip numarası** girilir. **Manuel sevki kaydet**, yalnız doğrulanmış paket miktarını mevcut siparişe bağlar. Taşıyıcı API'si çağırmaz, ücretli etiket oluşturmaz ve gerçek taşıyıcı kabulünün yerine geçmez.
5. Sevk miktarı siparişin bir bölümü ise kalan adet görünür kalır. Tekrar gönderilen aynı komut ikinci paket/sevk oluşturmaz. Sevkten önce görev iptal edilebilir; ayrılan miktar yeni hazırlığa açılır. Sevk kaydı bu ekrandan silinmez.

Ödeme veya sipariş durumu işlem sırasında değişmişse sunucu yeniden kontrol eder. İstemcinin gösterdiği miktara güvenilmez. Görev, komut ve audit kayıtları kalıcıdır; komut tekrarları aynı içerik/aktörle sınanır. Toplama/paketleme, ödeme sırasında düşmüş stoğu ikinci kez düşürmez; burada ayrılan miktar siparişin sevk edilecek miktarıdır.

## Mevcut manuel sevkle uyumluluk

Eski **Sevkiyatlar → Yeni kayıt** akışı, aktif hazırlığa ayrılmamış uygun siparişler için korunur. Bu yol barkod kontrolü yapmış sayılmaz. Aktif toplama/paketleme görevine ayrılmış miktarı tüketemez. Yeni doğrulamalı akış `/api/admin/orders/{id}` üzerinden yürütülür; `fulfillmentTaskId` taşıyan sevkte paket içeriği sunucuda birebir doğrulanır. Her eski manuel sevkin zorunlu barkod kapısından geçtiği iddia edilmez.

## Vergi sınıfı

Yeni ürünün ilk seçeneğinde ve varyant create/update formunda **Vergi sınıfı** alanı bulunur. Varsayılan `*` ortak sınıftır; özel sınıf açıkça SKU'ya kaydedilir. Boş veya yalnız boşluk içeren sınıf reddedilir. Sınıf değişikliği teknik değişiklik sayılır; yayın/ülke uygunluğu yeniden incelenir. Bu alan gerçek vergi oranı veya hukuki sınıflandırma onayı değildir. Oran ve yürürlük kuralları finans/yönetici tarafından ayrıca tanımlanır; özel sınıfın kuralı eksikse ortak sınıfa sessizce düşülmez.

## Doğrulama kaydı

`npx tsx --env-file=.env.local scripts/staff-orders-integration.ts`: eksik modülle ilk RED; uygulama sonrası **11/11 kontrol geçti**. Kontroller: alan küçültme/roller/MFA, ödenmemiş sipariş engeli, görev idempotency ve yarış, yanlış kod/fazla adet, barkod/SKU, ikinci paket kontrolü, eski manuel yolun görev miktarını tüketememesi, kısmi sevk/tekrar, durum değişimi/iptal ve vergi sınıfı kalıcılığı.

Aynı değişikliklerle `scripts/operations-integration.ts` **14/14** geçti. 11 Kasım 01:14 son kontrolünde `npm test` **15 dosya / 93 test**, ilgili dokuz kaynak/test dosyasının ESLint kontrolü ve typecheck geçti. Bu sayılar gözlenen o kaynak durumuna aittir; paralel eklenen modüllerin sonraki son toplu koşusu ayrıca kaydedilir.

`npx playwright test tests/e2e/staff-orders.spec.ts --output=.local/staff-final --reporter=line`: **Chromium + WebKit 2/2, 9,9 saniye, retry 0**. Gerçek oturum/MFA, depo alan küçültmesi, sipariş satırından ayrıntı, iki SKU kontrolü, kısmi manuel sevk, DB'de tek paket ve 390 px taşma kontrolü birlikte çalıştı. `docs/screenshots/staff-order-mobile.png` üretildi ve incelendi. Gerçek cihaz deneyi yapılmadı.

İlk denemelerde eski dev şeması ve Turbopack'ın kendi çıktılarını izleyen HMR döngüsü vardı; başarılı sayılmadı. Kararlı Webpack dev sunucusunda aynı akış geçti. Kaynak incelemesinde görülen geç favori para/dil doğrulaması için ayrıca RED gözlendi: geçersiz para birimiyle POST 400 yerine 200 verdi. Doğrulama mutasyondan önceye taşındı; aynı E2E artık 400 ve sıfır favori yazımı denetler. Test veri tabanı, açık development/test ortamı ve bu projenin yerel DB adıyla sınırlandırılır.

Gerçek barkod okuyucu donanımı, fiziksel depo prova kabulü, taşıyıcı etiketi/API'si ve gerçek satış operasyonu henüz doğrulanmadı. Set bileşenlerinin tek tek okutulması bu sürümün kapsamı değildir; siparişte satılan SKU ve miktarı doğrulanır.
