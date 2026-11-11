# Güvenlik ve mahremiyet tasarım sözleşmesi

Tarih: 11 Kasım 2026. Bu dosya kontrol sözleşmesini ve kaynakta uygulanan sınırları tarif eder. **Test kanıtı değildir.** Gerçek komut, sonuç ve kod incelemesi [progress.md](progress.md) ile [test-evidence.md](test-evidence.md) içinde tutulur; aşağıdaki beklentiler kanıtsız PASS sayılmaz.

## Tehdit ve veri sınırı

Korunan varlıklar: oturumlar, sipariş/adres/iletişim verileri, ürün tercihleri, depo stok defteri, para hareketleri, sağlayıcı anahtarları ve yönetici yetkileri. Başlıca tehditler: kullanıcılar arası kayıt erişimi, çalışan rolünden fazla veri dönüşü, sahte veya tekrarlanan ödeme bildirimi, eşzamanlı stok kaybı, dosya/URL üzerinden sunucu erişimi ve üçüncü taraf izleme sızıntısıdır.

Veri sorumlusu, işleyenler, sunucu/yedek lokasyonları ve aktarım mekanizması işletme tarafından henüz doğrulanmış değildir. Geliştirme veya tasarım kredisi bu rolleri tayin etmez. Şu anki yerel test kaydı gerçek müşteri ve işletme verisi olarak üretime taşınmamalıdır. Hukuki dayanaklar ve onay kapıları [hukuk gereksinimlerinde](./legal-requirements.md) izlenir.

## Kontrol ve doğrulama matrisi

| Alan | Beklenen kontrol | Kanıt / olumsuz senaryo |
| --- | --- | --- |
| Kimlik | Bakımı süren oturum kütüphanesi; sunucuda doğrulama | Geçersiz/süresi dolmuş oturum API'ye erişemez |
| Yetki | Her istekte rol, işlem ve kayıt sahipliği; varsayılan ret | A kullanıcısı B siparişini, depo rolü maliyeti okuyamaz |
| Admin | MFA zorunluluğu, yeniden doğrulama gerektiren kritik işlemler | MFA'sız admin canlı operasyon açamaz |
| Oturum | Üretimde Secure/HttpOnly/SameSite, süre sonu ve çıkışta iptal | Çıkışta eski token tekrar kullanılamaz; çerez özellikleri ölçülür |
| CSRF | Mutasyonlarda doğrulanmış origin ve framework/kütüphane koruması | Başka origin'den fiyat/stok/rol değişikliği reddedilir |
| SQL/XSS | Parametreli sorgu, şema doğrulama, güvenli metin render | SQL/XSS içeren girdi sorgu veya script olarak çalışmaz |
| Ödeme | İmza, tutar, para birimi, sipariş eşleşmesi ve idempotency | Yanlış/imzasız/tekrar olay ikinci işlem oluşturmaz |
| Kart | Sağlayıcı sayfası/tokenizasyon; PAN/CVV kaydı yok | Log ve veri şeması kart verisi barındırmaz |
| Stok | İşlem/kilit veya atomik koşullu güncelleme | Son ürüne iki eşzamanlı girişimde en fazla biri rezervasyon alır |
| Dosya | Boyut, tür, içerik ve yetki kontrolü; karantina | MIME sahteciliği, executable/SVG/HTML ve aşırı dosya reddedilir |
| Dış URL | Onaylı hedef, DNS/IP ve yönlendirme denetimi | Localhost/private/link-local, metadata ve redirect kaçışı engellenir |
| Önbellek | Hassas HTML/API `private, no-store`; CDN/PWA dışı | İkinci kullanıcı birincinin siparişini cache'den alamaz |
| Gizli anahtar | Yalnız sunucu ortamı; örnek env boş; log redaksiyonu | Client bundle, Git geçmişi, hata metni ve CI logu taranır |
| İş kuyruğu | Kalıcı iş, tekrar sınırı, tekil anahtar ve yetkili yeniden çalıştırma | Timeout/işçi kapanması ikinci tahsilat veya etiket oluşturmaz |
| Yedek | DB/medya ayrı, erişim sınırlı, şifreli saklama, restore provası | İzole staging'e dönüşte sipariş/stok/belge ilişkileri doğrulanır |

Oturum ve no-store tercihleri [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet) rehberine dayanır. SameSite tek başına tam CSRF çözümü sayılmaz; [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) yaklaşımıyla uygulamanın mutasyon sınırları ayrıca test edilir. Yalnız URL metnini filtrelemek DNS rebinding/yönlendirme riskini çözmez; [OWASP SSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html) bağlantı hedefinin de doğrulanmasını önerir. Dosya uzantısına tek başına güvenilmez; [OWASP File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) doğrultusunda içerik, boyut, depolama ve izinler birlikte ele alınır.

Bu depoda güvenilir, geliştirici tarafından üretilmiş marka SVG'leri bulunması, kullanıcı SVG yüklemesine izin verildiği anlamına gelmez. Uzaktan tedarikçi içerikleri doğrudan HTML olarak çalıştırılmaz veya kataloğa otomatik yayımlanmaz. Arşiv/CSV/XLSX girişlerinde dosya boyutu, satır/adet sınırı, formül enjeksiyonu ve mükerrer SKU ayrı test alanıdır.

## Lotlu satın alma kabulünün güvenlik sınırı

025 kabul-lot-SKU-hareket FK'leri yanlış SKU'ya kaynak bağlanmasını; miktar CHECK'leri alınan/kabul edilen adet sınırının aşılmasını önler. PO, kalem, fiziksel SKU, ana depo ve lot satırları kilitlenir. Kabul, lot/toplam bakiye, tek stok hareketi ve PO kalanının güncellenmesi aynı transaction'dadır; karma isteğin hatalı satırı bütün yazımı geri alır. Karantina fiziksel kabulün alt kümesidir ve satışa dönüş kararı değildir.

Yeni v2 tekrar anahtarı aktör ve canonical SKU/lot içeriğine bağlıdır. Eski v1 yalnız mevcut kaydın aynı aktör/içerikle tekrarına izin verir; yeni belgesiz kabul açmaz. Doğrudan lot girişi ile PO kabulü ortak anahtar kilidini kullanır. Aynı teslimat farklı yeni anahtarlarla elle girilirse belge metni kesin mükerrerlik kanıtı sağlamaz; operasyonel teslimat kontrolü hâlâ gerekir.

`GET /api/admin/lots?view=sources` gerçek MFA ile hem lot hem satın alma okuma yetkisi ister. Yönetici/katalog/depo/finans maliyetsiz kaynak DTO'sunu okuyabilir; destek/pazarlama/müşteri alamaz. Yanıt gerçek kayıt kimliği, tedarikçi adı, kabul/karantina adedi, ayrı teslimat/lot referansı ve tarihle sınırlıdır; birim fiyat, maliyet, banka veya iletişim alanı içermez. Tek SQL snapshot'ında arama/sayfa/toplam; HTTP'de bilinmeyen/yinelenen parametre ve geçersiz sayfa reddi, `private, no-store` uygulanır. Referans düz metindir; dış URL fetch veya raw HTML yoktur. Bir lotun birden çok PO kaynağı olması tek tek satış adedini o PO'ya bağlamaz. Kaynak referansı hukuki/üretici belgesinin dış doğrulaması değildir. Ayrıntı: [purchase-lot-guide.md](purchase-lot-guide.md).

## Eski oturum ve sepet yanıtlarını ayırma

`store-context.tsx` oturum ve sepet isteklerini ayrı artan nesil ve AbortController ile izler. Yeni yenileme önceki isteği iptal eder; yanıt yalnız hâlâ güncel nesil ve iptal edilmemiş istek için state'e uygulanır. Oturum sahibi değişince bekleyen sepet isteği geçersizleşir, sayaç sıfırlanır ve yeni kapsamda yüklenir. Cleanup iki akışı da geçersizleştirir. Checkout ve test ödeme ekranları eski hesabın/siparişin geç tamamlanan yanıtıyla yeni ekrana yönlenmez. İstemci iptali sunucuda tamamlanmış sipariş veya ödeme işlemini geri almaz; sunucu rol/sahiplik sınırları ayrıca korunur.

`.local/session-refresh-red.log`, eski A oturum yanıtının daha yeni B oturumunu ekranda ezdiği RED senaryosunu korur. Nesil/iptal düzeltmesinden sonra aynı regresyon Chromium ve WebKit'te GREEN oldu; checkout ve sandbox ödeme yanıtının hesap değişiminden sonra yönlendirme yapmaması da önceki dondurulmuş kontrol noktasında geçti. Sonradan açılan sepet/checkout sahipliği ve bozuk JSON yanıtı düzeltmeleri için bu tarihsel sonuç yeni PASS sayılmaz. Kaynak kimliği ve güncel sonuç [kanonik test kaydındadır](test-evidence.md). Yerel kabul gerçek sağlayıcı, üretim oturumu veya bağımsız penetrasyon testi değildir.

## Veri minimizasyonu envanteri

| Veri sınıfı | Amaç | Erişim sınırı | Silme/saklama kararı |
| --- | --- | --- | --- |
| Hesap ve oturum | Kimlik ve güvenlik | Hesap sahibi; yetkili güvenlik işlemi | Oturum iptali ile mali kayıt silme ayrılır |
| Sepet | Seçilen ürünleri ve hesaplamayı sürdürmek | Güvenli anonim token veya sahip hesap | Aktif kullanım ve makul temizlik süresi yapılandırılmalı |
| Adres/iletişim | Sipariş/teslimat ve işlem bildirimi | Müşteri, işlem için gereken yetkili çalışan | Operasyon + kanuni saklama matrisi onaylanmalı |
| Sipariş/ödeme | Sözleşme, mutabakat, iade | Sahip müşteri; işleve göre yetkili rol | Mali saklama ve hukuki hold ayrı; rastgele süre yazılmaz |
| Ürün tercihi/arama | Talep edilen katalog deneyimi | Gerekli istek kapsamı | Ham sorgu kalıcı loga/analitiğe yazılmaz |
| Pazarlama tercihi | İzin/ret ve ispat | Müşteri; sınırlı yetkili rol | Kanal/metin sürümü/tarih; İYS süreci onaylanmalı |
| Destek/iade | Başvuruyu sonuçlandırmak | İlgili görevli | Hassas serbest metin ve ekler en az düzeyde tutulmalı |
| İşlem kaydı | Yetki, stok ve finansal izlenebilirlik | Denetim için yetkili rol | Ham hassas payload yerine hedef/sonuç/referans |
| Yedek | Kurtarma | Yetkili operasyon | Şifreleme, süre, rotasyon ve silme etkisi planlanmalı |

Kesin saklama süreleri, hukuki satıcı ve ülke kuralları belirlenmeden kanuni süre gibi doldurulmaz. Silme talebinde hesap erişimi, pazarlama tercihi, anonimleştirme ve zorunlu mali saklama farklı işlemlerdir. Yedekten dönüşten sonra daha önce uygulanmış silme/ret kararlarının yeniden yürütülmesi gerekir.

## Mahremiyet davranışı

- E-posta konusu, SMS ve telefon önizlemelerinde ürün adı bulunmaz. Detay güvenli sipariş ekranındadır.
- Gizli paketleme, doğru fatura ve gümrük beyanını ortadan kaldırmaz; depo prosedürüyle desteklenmelidir.
- Pazarlama rolüne müşteri listesi ve satın alma geçmişi toplu indirme yetkisi verilmez. Depo yanıtında maliyet/kârlılık ve gereksiz müşteri geçmişi bulunmaz.
- Cinsel hayat, yönelim veya sağlık profili çıkarılmaz. Ürün tercihi veya arama ifadesi kullanıcı kimliğiyle reklam segmentine dönüştürülmez.
- Session replay, reklam pikseli ve üçüncü taraf analitik varsayılan kapalıdır. Bir tercih kutusu var diye herhangi bir sağlayıcı otomatik etkinleştirilmez.
- Destek ekranına tam ödeme payload'ı, kimlik görseli veya sırf alışveriş için doğum tarihi taşınmaz. Ülke yaş kuralı güçlü doğrulama istiyorsa uygun hizmet bağlanana kadar o satış kapalıdır.

## Olay ve kurtarma iş akışı

İlgili kişi başvuruları ayrı `privacy_requests` kuyruğunda, yönetici/müşteri hizmetleri MFA sınırıyla yürütülür. Anonim takip token'ı ayrıntılı veri erişimi vermez. Ülke politikası ve veri sorumlusu sürümlüdür; ilk alım zamanı korunur, ülke değişimi son tarihi uzatmaz. Üyelik/pazarlama izni zorunlu değildir. E-posta işi şifreli payload taşır; audit özel talep metni yerine kimlik/eylem/hash saklar. Reverse proxy/erişim logları özel token/query değerlerini kaydetmemelidir. Gerçek saklama/silme/aktarım incelemesi ve başvuranın kimliği doğrulanmadan veriler açıklanmaz. İş akışı ve otomasyonun açık sınırları [privacy-guide.md](privacy-guide.md) içindedir.

Şüpheli erişimde ilgili oturum/entegrasyon sınırlandırılır; delil için gereksiz müşteri payload'ı çoğaltılmaz. Olay kaydı kim/ne/zaman/hedef/sonuç bilgisine odaklanır. İşletme veri ihlali değerlendirmesi, yetkili kişilere eskalasyon ve mevzuat bildirimini yürütmelidir; yazılımın log tutması bu görevi tamamlamaz.

Dağıtım öncesi yetki testleri, bağımlılık taraması, production test-adaptör engeli, sır sızıntısı kontrolü, sağlık kontrolleri ve geri yükleme provası gereklidir. WAF, CDN, hosting şifrelemesi, anahtar rotasyonu, haricî güvenlik testi veya gerçek cihaz testi bu belgede tarif edildi diye tamamlanmış sayılmaz.
