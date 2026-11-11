# SEXSOGATE veri modeli ve uygulanan sınırlar

Güncelleme: 11 Kasım 2026. Şema kaynağı migrations/*.sql; veri erişimi src/server/db.ts ve modüler sunucu servisleridir. Tablo varlığı ekran/dış servis akışının tamamlandığını göstermez; gerçek durum docs/progress.md ve docs/integrations.md içindedir.

Önceki çekirdek kontrol noktası [checkpoint-core.md](checkpoint-core.md) içindedir. 025 ve oturum değişikliklerini içeren dondurulmuş sürümün yerel kabulü tarihsel kontrol noktasıdır. Ardından açılan sepet/checkout sahipliği ve bozuk JSON yanıtı düzeltmelerinin güncel sonucu [progress.md](progress.md) ile [test-evidence.md](test-evidence.md) içindedir; önceki PASS yeni kaynak sürümüne aktarılmaz.

## Temel tipler ve kimlik

- İş kayıtları text UUID; Better Auth kimliği kütüphanenin text değeridir. Kaynak ve PostgreSQL UTF-8.
- Para SQL bigint alt birim; giriş/sipariş tutarları güvenli tamsayı sınırlarıyla doğrulanır. Oran/dağıtımda BigInt kullanılır. `formatMinorAmount` BigInt değerleri ve yapılandırılmış 0/2/3 basamaklı gösterimi, Arapça dahil yerel rakam düzenini korur. Bu biçimlendirme altyapısı yeni tahsilat parası açmaz: mevcut katalog/checkout para birimleri TRY/EUR/USD/GBP ve iki alt birim basamağıdır; raporda birbirine eklenmez.
- Anonim sepet ve misafir takip token'ı DB'de hash olarak saklanır. Rol/fiyat/stok istemci değerine dayanmaz.
- Fiilî tahsis deposu main'dir. Ek depo şeması, çok depolu tahsis/transfer operasyonu tamamlandı demek değildir.

## Kayıt kümeleri

| Alan | Gerçek tablolar/alanlar | Bağ ve uygulanan sınır |
|---|---|---|
| Katalog | categories, brands, products, variants | Slug/SKU tekil; varsa gerçek barkod tekil. Kategori ve products.supplier_id FK; products.brand bugün metin etiketi, brands'a katı FK değildir. Ürün/varyant ve arşiv/aktiflik ayrıdır. Menşe/üretici, ölçüler ve attributes.warranty açık beyan olarak tutulur; uygunluk onayı değildir. |
| Dil/SEO | products.translations, products.seo, variants.name_en, product_routes, public_redirects | EN bakım/uyarı/varyant adı; dil başına title/description/alt ve tekil slug. product_routes ürün+dil, dil+slug tekilliğini korur. Denetimli genel 308 yönlendirmeler ayrı kayıttır; teknik/içerik değişikliği yeniden inceleme gerektirir. |
| Uygunluk | product_documents, product_eligibility, product_compliance_events, compliance_commands, product_contact_profiles, shipping_approvals | SKU/model/ülke/tür/tarih/ref, sürümlü belge inceleme/iptal ve aktör izi; ülke onayı yalnız yöneticiye aittir. Yayın/checkout aynı aktörlü uygunluk ve gerekli exact belgeyi denetler; yayın onay oluşturmaz. Teknik bilgi ve kaynaklı üretici/sorumlu iletişim UI'si var; private belge referansı ve maliyet public DTO'ya girmez. Raw PDF yükleme/tarama yoktur. |
| Fiyat/kur | variant_prices, exchange_rates, country_rules.currency | Gösterim parası ile ülkenin tahsilat parası ayrıdır. Her ikisi gerçek sabit fiyat listesine dayanır; eksik listede fiyat veya kur uydurulmaz. Fiyat listesi transaction/audit ile güncellenir; gerçek kur servisi ve kapsamlı kur operasyonu yok. |
| Vergi/ülke | variants.tax_class, country_rules, tax_rules, shipping_tax_rules | Her SKU'nun sınıfı+ülke+yürürlük için tam bir ürün kuralı gerekir; başka sınıfa '*' fallback yapılmaz. Kargo vergisinin onay/kaynak/tarihi ayrıdır. Sınıf, dönem ve başlangıç tekilliği migration015 ile korunur; çakışan etkin kurallar checkout'ta reddedilir. |
| Kampanya | coupons, coupon_usage | Oran/minimum/kullanım/katkı/süre; kullanım rezervasyonu ödeme/iptal/süre sonuna bağlı ve eşzamanlı korunur. |
| Depo | warehouses, warehouse_locations, inventory_balance, inventory_movements | Kullanılabilir fiziksel miktar, karantina, güvenlik/minimum stok ayrı. Hareket kaydı ve negatif stok CHECK; fiilî tahsis deposu main. |
| Lot ve geri çağırma | variants.lot_tracking/expiry_required, inventory_lots, inventory_lot_balances, reservation_lots, lot_operations | Lot bakiyesi toplam depo bakiyesine bağlıdır. FEFO tahsisi, tarih/karantina/geri çağırma filtresi ve idempotent hareketler uygulanır. Fiziksel lot okutma, çok depo/transfer ve lotu bilinmeyen iadenin yeniden atfı tamamlanmadı. |
| Set | bundle_components, variants.bundle_version, bundle_changes, order_items.snapshot.bundleComponents | UI arama/adet/önizleme ve beklenen sürümle kayıt; aktör/gerekçe/eski-yeni tanım geçmişi. Bileşenler atomik rezerve/tüketilir; eski sipariş snapshot'ı korunur. Üst SKU ve fiziksel bileşen ayrı ülke/exact belge denetiminden geçer; bileşenin tek başına yayını gerekmez. Pasif/fixture/iç içe set ve fiziksel üst stok dönüşüm sınırları ile stok kabul regresyonları yerelde doğrulandı. |
| Tedarik | suppliers, purchase_orders, purchase_items, purchase_receipts, purchase_receipt_items, purchase_receipt_lots | Normal/lotlu kabul, alınan/kalan miktar, aktörlü v2 hash ve eski v1 tekrar uyumu. Kabul-lot-SKU-hareket bileşik FK'leri ve alınan adet CHECK'i; fiziksel toplam, karantina payı, teslimat/lot kaynakları ayrıdır. Tedarikçi stoğu satış stoğu değildir. |
| Sepet | carts, cart_items | Token hash tekil, opsiyonel kullanıcı, miktar1–99. Birleştirme işlemsel; checkout sahipliği yeniden çözer, başka hesaba bağlı token yeni boş kabiliyete dönüşür. |
| Sipariş | orders, order_items, reservations, order_history | Sepet+idempotency tekil, request/tracking hash, süreli rezervasyon; fiyat/vergi/maliyet/ürün/dil/set snapshot. Sipariş/ödeme/sevk durumları ayrıdır. |
| Ödeme | payments, payment_events, provider_events | Sağlayıcı referansı/olay tekil; tutar/para/sipariş eşleşir. İmzadan sonra normalize inbox ve payload hash kalıcılaşır. PAN/CVV alanı veya akışı yok. |
| Sevk | shipments, shipment_items | Gerçek taşıyıcı/takip ve kısmi paket satırları; idempotency+request hash farklı içerikli tekrarı reddeder. Taşıyıcı etiket/takip olay API'si bağlı değil. |
| Personel hazırlığı | fulfillment_tasks, fulfillment_task_items, fulfillment_commands | Ödenmiş siparişten ayrılan miktar; picking/packing/packed/shipped/cancelled. picked≤quantity, packed≤picked; order+request_key ve komut hash'i tekrarı korur. Shipped görev bir shipment'a bağlıdır; bu kayıtlar ikinci satış stok düşümü üretmez. |
| İade stok | returns, return_stock_lines | Başvuru/karar/kabul/QC ayrı. SKU/depo/miktar satırları satış snapshot'ından türetilir; set üst SKU'suna hayalî stok yazılmaz. |
| Para iadesi | refunds | Başvuruya tekil; tutar/vergi/indirim ve geri alınan maliyet payı. Pending başarı değildir; yalnız doğrulanmış sonuç toplamı bir kez artırır. |
| Fatura referansı | invoice_references | Doğrulanmış satıcı ve finans yetkisiyle dış numara/sağlayıcı/tür/aktör/açıklama. Resmî belge üretimi veya doğrulanmış e-Fatura bağlantısı değildir. |
| Yapısal CMS | cms_regions, cms_region_revisions | TR/EN hero/navigation/footer/collection, bölge+dil tekilliği; değişmez sürüm JSON'u, taslak/yayın/arşiv ve publish_at. Koleksiyon ürün kimlikleri payload referansıdır; FK/onay yerine servis yayın ve runtime uygunluk denetimi yapar. |
| Rehber/SSS | content_pages.kind/fixture, content_revisions.status/publish_at/kind/published_by | Mevcut içerik kaynağı genişletilir; ikinci rehber tablosu yoktur. Guide/faq/campaign/page ayrımı, sürüm ve zamanlı yayın. Eski yazıcı aynı revision kaynağıyla uyumludur. |
| Sosyal çıktı | Mevcut products/variants/variant_prices, CMS sürümleri, media_assets, audit_log | Yeni paralel katalog tablosu yoktur. Aynı SKU/dil/güncel fiyat ve hak/hash kaydından yedi düzenlenebilir SVG şablonu üretilir; özel indirme ve hash audit'i var. Fiyat/metin/görsel snapshot'ı dosyadadır; sosyal hesaba yayın veya reklam kabulü yoktur. |
| Hukuk | legal_documents, legal_approval_log, order_agreements | Dil/sürüm; taslak/onay/yürürlük/arşiv ve tür+dil başına tek yürürlükte sürüm. Sipariş tam metin/dil/sürüm/hash/kabul zamanını ayrıca saklar. CMS bu onayı devralmaz. |
| Müşteri | customer_addresses, wishlists, consent_records, contact_requests | Üye adreslerinde sahiplik denetimli oluştur/oku/güncelle/sil ve onaylı adres profili bağlantısı var. İzin/başvuru türleri ayrıdır. Ticari ileti/IYS ve otomatik saklama/silme operasyonu bu tablolardan türemez. |
| Adres profili | country_address_profiles, country_address_events, orders.address_profile_id, customer_addresses.address_profile_id | Ülkeye bağlı değişmez alan/dil/kaynak sürümü; yönetici MFA ve yeniden parola doğrulamasıyla onay/arşiv. Checkout yürürlükteki sürümü doğrular; eski siparişin adres alanları/sürüm snapshot'ı korunur. Profil ülkeyi satışa açmaz. |
| Veri sorumlusu/ilgili kişi | privacy_controllers, privacy_policies, privacy_requests, privacy_request_events, privacy_responses | Satıcıdan ayrı sürümlü veri sorumlusu, ülke/süre/saat dilimi/kaynak politikası; hashlenmiş takip token'ı, kimlik incelemesi, son tarih ve tekil yanıt. Yerel sahiplik/rol/süre/UI doğrulaması çekirdek kontrol noktasında kayıtlıdır. Talep kaydı otomatik veri silmez. |
| Import | import_preview, import_batches, catalog_import_document_links | format_version=2, kaynak ortam, aktör, satırlar+hataları kapsayan hash, süre ve commit kilidi. productKey ile yeni ürün grubu; gerçek ayrı varyant/fiyat listeleri; yalnız main depoda sıfır bakiye. Mevcut belge bağlantısı sadece review_required; ülke/belge onayı oluşturmaz. |
| Kanallar | channel_mappings | Kanal/SKU/fiyat/kota modeli var; gerçek pazaryeri sipariş/stok eşitleme aktif değil. |
| Oturum | user, session, account, verification, twoFactor, rateLimit, session_mfa | Resmî Better Auth şeması, DB rolü, süreli kullanıcı+oturum MFA işareti. Oturum silinince MFA cascade temizlenir; hesap bayrağı yeterli değildir. |
| İş/güvenlik/ayar | jobs, audit_log, request_limits, settings, media_assets | Dedupe/lease/retry/başarısız iş; işlem kaydı; HMAC ağ kotası; boş gerçek satıcı alanları; özel medya/hak kaydı. İlk şemadaki redirect_rules, güncel public_redirects motoru değildir. Adaptör gerçek S3/SMTP/kanal testi yerine geçmez. |

## Kritik işlem sözleşmeleri

### Katalog okuma, facet ve kart temsili

Facetler yeni bir stok veya ürün tablosu değildir; yayımlanmış ürün, etkin kategori ve varyant kayıtlarından istek anında türetilir. Marka/malzeme ürün alanıdır; beden/renk/güç türü ve gerçek sıvı/hijyen mührü bayrakları varyant alanıdır. `power`, `battery_type` metnidir; pil adından şarj, sertifika veya su geçirmezlik çıkarılmaz. Seçenekler özgün Türkçe değerleri korur; boş alanlar facet üretmez. Ortam fixture sınırı ve tamamlanmış dil içeriği genel okumada da uygulanır.

Fiyat, beden, renk, güç, özellik ve stok koşulları aynı varyantta birleşir. Arama/fiyat/bulunabilirlik facet bağlamını belirler; diğer seçili facetler alternatif seçenekleri yok etmez. Facet sayısı farklı ürün adedidir. `searchCatalog`, ürünleri, facetleri, toplamı ve 24 kayıtlık sayfayı tek SQL okuma snapshot'ında döndürür; bulunabilirlik LIMIT/OFFSET öncesinde uygulanır. `listProducts` eski ürün dizisi sözleşmesini korur. Doğrudan API bilinmeyen/yinelenen tekil alan veya geçersiz değerleri reddeder; SSR/UI ilgisiz URL parametrelerini filtre nesnesine taşımaz. Arama sorgusu kaydı eklenmez.

Katalog ve `variantAvailability` yalnız checkout'ın kullandığı `main` deposunu sayar; başka depodaki miktar ana depodan sevk edilebilir görünmez. Lot ve set hesapları aynı güvenlik payı/aktif rezervasyon sınırını izler. Kartın `selectCatalogDisplay` seçimi, sunucunun `min(amount_minor)` sıralamasıyla aynı eşleşen varyant kümesindeki seçili para biriminin en düşük geçerli fiyatını ve o varyantın adını birlikte kullanır. Eksik fiyat sıfır veya başka para birimi fiyatı değildir. Bu okumalar rezervasyon veya ülke/belge onayı oluşturmaz. Rehber: [catalog-filter-guide.md](catalog-filter-guide.md).

### Stok ve rezervasyon

Checkout ana depoda normal SKU veya set bileşenlerini sıralı kilitler. Fiziksel kullanılabilirden aktif rezervasyon ve güvenlik payı düşülür. Başka depo miktarı kilitli ana depo tahsisini karşılayamaz. Doğrulanmış ödeme rezervasyonu ve satış hareketini bir kez tüketir. Süresi dolmuş/iptal rezervasyona gelen başarı negatif stok/otomatik sevk yerine payment_exception üretir.

Lot takibi yalnız toplam stok, karantina ve etkin rezervasyon bütün depolarda sıfırken açılır; geçmiş stok için lot uydurulmaz. expiry_required yalnız lot_tracking ile birlikte geçerlidir. Takipli SKU'da genel stok artırma ve lotsuz satın alma kabulü kapalıdır. Lotlu kabul toplam ve lot bakiyesini aynı işlemde değiştirir. Uygun lotlar FEFO ile ayrılıp reservation_lots'a yazılır; ödeme yeniden lot seçmek yerine aynı tahsisi tüketir. Europe/Istanbul etiket gününden itibaren tarihi geçen lot satılamaz. Recall kalan stoğu karantinaya alır, ilişkili sevki kapatır; müşteri bildirimi üretmez. Lotu bilinmeyen iade karantinası lot bakiyesine veya satılabilir stoğa tahminen dağıtılmaz.

### Satın alma kabulü ve lot kaynağı — 025

`purchase_receipts.source_reference` teslimat belgesini; `request_version` eski v1 ile yeni v2 hash sözleşmesini ayırır. `purchase_receipt_lots` anahtarı `(receipt_id, variant_id, lot_id)`; tekil `movement_id` ve bileşik FK'ler kabul satırı, lot ve hareketin aynı SKU'ya ait olmasını zorunlu kılar. `quantity > 0`, `0 ≤ quarantine_quantity ≤ quantity` ve `purchase_items` için `0 ≤ received ≤ quantity` CHECK'leri vardır. Mevcut hatalı veriye migration sessiz düzeltme uygulamaz.

PO kalemlerinin kalan miktarı, SKU'nun güncel takip/tarih politikası ve lot adet toplamı sunucuda tekrar doğrulanır. `receiveLotStock` aynı transaction içinde toplam/lot bakiyesini ve tek gerçek hareketi yazar; kabul ayrıntıları, alınan miktar ve PO durumu birlikte commit edilir. Bir hatalı satır karma kabulün tamamını geri alır. Karantinaya alınan adet fiziksel kabul toplamının içindedir; PO kalanını azaltır fakat satışa açılmaz. Aynı üretici lotunun tarihi değiştirilemez; geri çağırma ve mevcut lot karantina durumuyla çelişen kabul reddedilir.

V2 hash aktör ve canonical SKU/lot sırasını içerir. Aynı anahtar/aktör/içerik önceki sonucu döndürür; v1 yalnız mevcut eski kaydın aynı içerik/aktörle tekrarı içindir. Doğrudan lot kabulü ve PO kabulü ortak anahtar kilidini paylaşır. Yeni anahtarla aynı fiziksel teslimatın tekrar elle girilmesini belge metni tek başına engellemez.

Bir lotun birden çok PO kaynağı olabilir. `lotSources` gerçek ilişki ve doğrudan kabul kayıtlarından maliyetsiz DTO üretir; teslimat `receiptSourceReference` ile lot `sourceReference` ayrıdır. Eski ilişkisiz kayıttan kaynak uydurulmaz. FEFO tahsisi lota bağlı kalır; satılmış belirli adet tek PO'ya atfedilmez. Bu istemci paneli için yeni finans veya satış-atıf tablosu yoktur. Rehber: [purchase-lot-guide.md](purchase-lot-guide.md).

Oturum/sepet yenilemesindeki istek nesli ve AbortController istemci state'idir; yeni DB yetkisi veya kolon değildir. Sunucu kayıt sahipliğini her istekte doğrulamaya devam eder. Eski A yanıtının B oturumunu ezmesi regresyonu düzeltme sonrası iki motorda geçti; kanonik kanıt kaydındadır.

### Gruplu katalog içe aktarma

Eski yedi kolonlu şablon korunur; geniş CSV/XLSX 38 alan taşır. productKey yoksa satır ayrı üründür; varsa aynı gruptaki ürün düzeyi alanlar tutarlı olmalıdır. Seçenek adları iki dil birlikte verilir; çok satırlı grupta zorunludur. SKU/barkod, teknik veriler ve TRY/EUR/USD/GBP listeleri varyant bazındadır. Ürünler draft kalır, fiziksel stok/hareket/lot/eligibility oluşmaz. Yeni sıfır inventory_balance satırı SKU'yu normal stok seçicisine açar; ana depo yoksa önizleme reddedilir.

Önizlemenin hash'i aktör, format, ortam, normalleştirilmiş satır ve hata listesini kapsar. V1/bilinmeyen sürüm veya ortam değiştirilmiş önizleme yeniden yükleme ister. Commit'te önizleme ve varyant yazımı kilitlenir; SKU/barkod, kaynak referansları, grup ve medya tekrar denetlenir. Doküman kapsamı yeni SKU'ya kopyalanmaz; catalog_import_document_links yalnız inceleme girdisidir. 2 MB/1000 satır/40 kolon/2000 karakter, formül/ZIP/XML/SSRF sınırları korunur. Stok, lot açma ve bilinmeyen dolu alanlar satır hatasıdır.

### CMS sürümü ve ilk HTML

Yapısal alanlar ile rehber/SSS aynı tür hizmet değildir; ilgili mevcut kaynaklar tekil kalır. Taslak kaydetmek yürürlükteki sürümü değiştirmez. Yayın zamanı UTC'ye çevrilir; sunucu her okumada zamanı gelmiş uygun sürümü seçer, worker veya açık tarayıcı gerekmez. Arşiv geçmişi silmez; eski yayını kendiliğinden diriltmez ve planlanan sayfa yayınlarını iptal eder.

Kampanya/menü/footer ilk sunucu HTML'inde aynı istek içindeki CMS snapshot'ından gelir; React.cache istekler arası kalıcı içerik önbelleği değildir. Koleksiyon üyeleri yayın anında ve genel okumada etkin kategori/varyant ve dil içeriğiyle filtrelenir. Kapalı ürün koleksiyonda görünmez; bu yayın filtresi ülke/ödeme/stok uygunluğu değildir. Yetkili taslak önizlemesi özel kalır. Taslak, gelecek veya arşiv CMS kaydı medyayı anonim erişime açmaz. Geliştirici/tasarımcı kredileri satıcı kimliği veya düzenlenebilir hukuk metni değildir.

### İlgili kişi başvuru modeli

021 migration ve privacy.ts; veri sorumlusu kimliğini hukuki satıcıdan ayrı kaydeder. Onaylı veri sorumlusu sürümü, ülke politikası ve kaynak/kanıt/saklama notu olmadan süre veya hukuk onayı uydurulmaz. Politika gün veya takvim ayı ve PostgreSQL saat dilimiyle süre hesaplar. Yeni yönlendirme/kural mevcut son tarihi uzatmaz. Kural yokken başvuru alınabilir; due_at boş kalır ve değerlendirme/yanıt kapalıdır.

Başvuru received → in_review → responded/rejected; kimlik durumu ayrıca pending → verified'dır. Üyede hesap/e-posta sahipliği, misafirde hashlenmiş rastgele token denetlenir. Misafir token'ı yalnız referans/durum/tarih döndürür; özet ve yanıt gövdesi kendi hesabı olan üyeye açılır. Numara tek başına yetmez. Yapılandırma yöneticiye, operasyon yönetici/destek rolüne ve MFA'ya bağlıdır. Yanıt öncesinde kimlik ve onaylı kural gereklidir; doğrulama referansı ayrı olayda, hash'i audit'te tutulur. Bildirim e-postası şifreli outbox verisidir; gerçek SMTP teslimatı yoktur.

Bu model silme/taşınabilirlik talebini kaydeder; otomatik silme, anonimleştirme, dış sistem ihracatı veya hukuki saklama kararını uygulamaz. Yerel controller/policy fixture'ı production onayı değildir. Yerel doğrulama ve sürüm sınırı [privacy-guide.md](privacy-guide.md) ile kanonik kanıt kaydındadır; gerçek SMTP ve hukuki operasyon kabulü bekler.

### Yayın ve teknik değişiklik

Yayın gerekli TR/EN içerik ve uygunluk denetimine bağlıdır. Yayındaki ürün güvenlik/tanıtım alanı değişikliği inceleme ve uygunluk iptali üretir. Teknik varyant değişikliği belge/taşıyıcı onayını da iptal eder; yayınlı ürüne yeni varyant inceleme gerektirir. Fiyat listesi kendi audit'li transaction'ındadır. Geçmiş sipariş fiyatı veya metni yeniden katalogdan hesaplanmaz.

### İade ve QC

Kabul, order_items.snapshot.bundleComponents varsa bileşen miktarı × iade adedini, yoksa satılan normal varyantı kullanır. return_stock_lines bu sonucu saklar. Ana depo satırları kilitlenir; kabul yalnız karantinayı artırır. Açık mühür veya onaysız QC otomatik satışa dönüş üretmez. Açıkça olumlu QC bütün kabul satırlarını atomik bırakır. Genel stok bırakma, refund_pending/refund_failed dahil iade karantinasını aşamaz.

Migration012 eski normal iadeye yalnız bağlantı ekler; stok üretmez. Eski hatalı sürümle kabul edilmiş set iadesi varsa migration bilinçli durur: üst SKU/bileşen stoğu mutabık hale getirilmeden sessizce yeniden yorumlanmaz.

### Para, vergi ve sağlayıcı

Fiyatlar KDV dahil alt birim olarak kalır. Küresel kupon önce satırların brüt ağırlığına tamsayı olarak dağıtılır; her satır indirim sonrası kendi SKU sınıfı oranıyla hesaplanır. Sipariş satırı sınıf/kural/oran/kaynak/yürürlük ve brüt/indirim/vergi/net paylarını snapshot olarak saklar. Siparişin ürün vergisi bu satırların toplamıdır; ayrı kargo vergisi ürün satırlarına dağıtılmaz.

Eksik veya birden fazla etkin sınıf kuralı checkout'u durdurur. '*' yalnız SKU'nun açık sınıfı '*' olduğunda eşleşir. Production'da örnek ürün vergi kuralı veya onay kaynağı eksik gerçek kural kullanılamaz. Kısmi iadede satılmış satırın değişmez indirim/vergi payı bölünür; son parça kalan alt birimleri alır. Sonraki katalog/vergi değişikliği geçmiş iadeyi değiştirmez. Pending iade kapasitede tutulur, başarıyla dönmüş tutara eklenmez. Offline sağlayıcı callback testi gerçek Stripe hareketi değildir. Gerçek oranların ve ülke/gümrük uygulamasının hukuki onayı ayrıca gerekir.

### Dil yolları, gösterim ve personel

products.slug ile dil bazlı product_routes ayrı alanlardır. SEO düzenlemesi dilin canonical yolunu ve metadata'sını günceller; eski eşdeğer ürün adresleri 308 ile son adrese düzleşir. public_redirects yalnız güvenli, mevcut genel hedeflere izin verir; özel yollar, dış URL, döngü ve zincirler reddedilir. Runtime hedefin hâlâ açık olduğunu tekrar kontrol eder. Canonical/sitemap/yönlendirme uygunluğunda aktif kategori ve en az bir aktif varyant ortak koşuldur; EN ayrıca ad/açıklama ister. Örnek ürünler sitemap/ürün şemasına katılmaz.

Gösterim fiyatı gerçek fiyat listesinin projeksiyonudur; tahsilat para birimini değiştirmez. Product/Offer üreticisi eksik gösterim fiyatına veya farklı tahsilat parasına satın alınabilir Offer eklemez. Fiyat veya metadata alanı ödeme hesabının kaynağı değildir.

Personel sipariş ayrıntısında rol bazlı alan seçilir: depo, maliyet/tutar/ödeme referansı/e-posta/geçmiş yerine sevk için gereken az veriyi alır. SKU veya varsa gerçek barkodla toplama/paketleme sayacı doğrulanır; ayrılan ve sevk edilen miktarlar transaction altında sınırlandırılır. Personel testi fiziksel lot etiketi doğrulaması veya çok depo kabulü değildir; lot/FEFO modülünün ayrı yerel kanıtı vardır.

### Hukuk, sahiplik ve kalıcı işler

Hukuk onayı/yürürlüğü audit'lidir; placeholder reddedilir. order_agreements tam içerik kopyasıdır; kaynak hukuk metni değişince müşterinin yetkili PDF/JSON'u değişmez. Özel sipariş belge erişimi önce sahiplik veya güvenli takip token'ını denetler.

İşler transaction'da kalıcılaşır, lease ile alınır. Olay/iş dedupe yerel yan etkileri sınırlar; dış hizmette en az bir kez işlenme ihtimali için sağlayıcı idempotency ve mutabakat gerekir. SMTP başarısızlığı yeni tahsilat veya başarılı e-posta iddiası üretmez. Şemadaki her durum için tam yönetim UI'si/geçişi mevcut değildir.

## Migration ve kanıt sınırı

- 001–006: çekirdek ticaret, resmî auth, hukuk/SEO, müşteri/medya, provider inbox/kota, sevk request hash ve kupon kullanımı.
- 010: oturuma bağlı MFA. 011: operasyon, EN, mal kabulü, taşıyıcı kabulü ve iade payları.
- 012: değişmez iade stok satırları. 013: onaylı/tarihli kargo vergisi. 014: özgün metne dokunmayan Türkçe arama fonksiyonu.
- 015: SKU vergi sınıfı ve sınıf/dönem kısıtları. 016: TR/EN tekil ürün yolları ve denetimli genel yönlendirmeler. 017: personel toplama/paketleme görevleri ve idempotent komutlar.
- 018: SKU lot bayrakları, lot bakiyesi/rezervasyon tahsisi ve idempotent lot işlemleri.
- 019: import sürüm/ortamı, ürün tedarikçi FK'sı, varyant ölçüsü ve onaysız mevcut belge referansları.
- 020: yapısal CMS bölgeleri/sürümleri ve mevcut içerik revision kaynağında tür/zaman/yayın alanları.
- 021: ayrı veri sorumlusu, süre politikası, ilgili kişi başvurusu/olay/yanıt ve takvimsel son tarih işlevi.
- 022: set sürümü ve eski/yeni tanım geçmişi. 023: belge/uygunluk aktörü, inceleme/iptal, özel olay/komut ve kaynaklı işletme iletişimi. 024: ülke adres profili/sürüm/olay ve sipariş/üye adresi bağlantıları.
- 025: kabul başlığında teslimat kaynağı/hash sürümü, kabul-lot-SKU-hareket bileşik FK'leri ve alınan adet sınırı.

Numara aralığı eksik dosya varsayımı değildir; uygulanmış checksum değiştirilmez. Facet/kart ve para biçimlendirmesi migration gerektirmedi; 022 set modeline aittir. [Set](bundle-guide.md), [belge/teknik bilgi](compliance-guide.md), [sosyal](social-guide.md), [adres](address-guide.md) ve [lotlu satın alma](purchase-lot-guide.md) kapsamı kodda vardır; son toplu kabul kanonik kayıttadır. Fiziksel lot/paket doğrulaması, lotu bilinmeyen iadenin yeniden atfı, çok depo, mevcut ürünü güncelleyen import, fuzzy arama ve gerçek ülke/kanal/sağlayıcı onayları açık kalır.
