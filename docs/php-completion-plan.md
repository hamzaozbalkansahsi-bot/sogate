# PHP sistem tamamlama planı

Hedef: mevcut SEXOGATE ticaret ve operasyon işlevlerini aynı PHP/MySQL runtime'da bağlamak; Node gerektirmeden yalnız `/test` yayınını ilerletmek. Kanonik kapsam `product-spec.md`, güncel iş modeli `dropshipping-guide.md`. Testler ve gerçek dış bağlantılar ayrı izlenir.

Mimari: sürümlü MySQL migration, PDO işlemleri, modül servisleri, açık alanlı rol DTO'ları, Twig sayfaları ve dar HTTP komutları. Eski kaynaklar okunur; diğer sohbetlerin TypeScript/UI dosyaları değiştirilmez. Sırlar Git dışında, tahsilat kapalı, ana site/DNS korunur.

Her adım: önce gözlenebilir başarısız kabul testi, sonra uygulama, ilgili test + bütün PHP suite, kullanım belgesi ve yalnız doğrulanmış test yayını. Onay bekleme yerine mevcut açık geliştirme/yayın yetkisiyle ilerlenir. Dış kabul/anahtar gerektiren işlem uydurulmaz.

- [ ] `014_fulfillment_returns.sql`, `Fulfillment.php`, `Returns.php`, `OperationsTest.php`: paket hazırlığı ve barkodlu toplama/paketleme → gerçek takipli kısmi sevk; iadede onay/teslim alma/QC/karantina ve kısmi para iadesi. Önce son adet/çifte paket, açılmış mühür/restock ve fazla iade testleri. Komut: `python scripts/test-php.py --filter OperationsTest`.
- [ ] `Providers/PaymentProvider.php`, `Providers/StripeProvider.php`, `Payments.php`, sağlayıcı testleri: resmî SDK ile session/status/refund/cancel, ham webhook imzası ve kalıcı inbox; belirsiz timeout'ta aynı idempotency anahtarı, sırası değişen olay ve mutabakat. Gerçek anahtar yokken yerel kontrollü HTTP yanıtları yalnız sınır testi sayılır.
- [ ] `Customers.php` ve testleri: sahiplikli adres/favori/iade/geçmiş; anonim sepetin girişte deterministik birleşmesi, MFA/rol/oturum yönetimi ve rıza tercihleri. Kullanıcı A→B erişimi, miktar birleştirme ve pazarlama yetkisi reddi sınanır.
- [ ] `Content.php`, `Seo.php` ve testleri: taslak/yayın, rehber/SSS/koleksiyon/banner, değişmez hukuk sürümleri/onay akışı, gerçek Product/Offer/slug/canonical/sitemap/redirect ve SEO kontrolü; özel test alanında noindex korunur.
- [ ] `Purchasing.php`, `InventoryManagement.php`, `Import.php` ve testleri: tedarikçi/PO, lotlu mal kabulü/sayım/karantina/geri çağırma, set tanımı ve CSV/XLSX inceleme; yanlış tek satır tüm kabulü geri alır, dış stok depo sayılmaz.
- [ ] `Markets.php`, `Reporting.php`, `Administration.php` ve testleri: ülke/dil/kur/fiyat/vergi kabul ekranları, gerçek katkı/azalan stok/ödeme/iade raporları, kuyruk retry ve işlem geçmişi, satıcı/entegrasyon/rol kurulumları. Depoya finans alanı ve pazarlamaya toplu müşteri geçmişi dönmez.
- [ ] `Kernel.php` ve yalnız PHP şablonları: tüm servislerin müşteri/admin ekranlarını bağla; doğal Türkçe/İngilizce, gerçek boş durum, mobil klavye/erişilebilirlik. Diğer sohbetlerin tasarım kaynakları korunur.
- [ ] Bütün PHP suite, sözdizimi/bağımlılık denetimi, Chromium/WebKit/360–1440/RTL altyapısı, güvenlik ve yedek geri yükleme. Yerel kabulden sonra paket/kurulum ve `/test` gerçek kabulü; önceki yayına dönüş ve kaynak manifesti kaydı.

Özellikle incelenecek sınırlar: aynı siparişten eşzamanlı iki paket, depo/tedarikçi kaynak karışması, geç/tekrarlanan sağlayıcı sonucu, sipariş snapshot'ı ile sonradan değişen set/ürün, ortadaki hata sonrası kısmi stok/para yazımı. Bu sınırlar sahip modülün kabul testlerinde kanıtlanır.

Canlı satışın dış önkoşulları: gerçek satıcı/vergi/banka/destek, gerçek ürün/stok/görsel ve belgeler, Stripe kategori/işletme kabulü, sağlayıcı anahtarları, taşıyıcı/fatura/SMTP/S3 ve onaylı hukuk/ülke kuralları. Teknik tamamlanma bu onayların yerine geçmez.
