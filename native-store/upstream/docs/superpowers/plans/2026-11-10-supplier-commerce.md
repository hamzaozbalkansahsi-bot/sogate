# Tedarikçi kataloğu ve alış takibi

Amaç: Alka Ahşap ve Altın İş Ağaç ürünlerini kaynak kanıtlarıyla arşivlemek, birim ve varyantlarını koruyarak kataloglamak; bütün ürünleri tedarikçilerine bağlamak ve gerçekleşen alışları satış fiyatından ayrı izlemek.

Kullanıcının doğrudan uygulama talimatı kapsamında aynı oturumda ilerlenir. Mevcut çalışma ağacındaki başka değişiklikler korunur.

## Tasarım

- Kaynak HTML/JSON ve görseller özel `artifacts/supplier-expansion` arşivinde hashleriyle saklanır. SKU ve sayfa kimliği ayrı alanlardır. NODENO kodu `ND-ALK-…` / `ND-ALT-…` olur; aynı SKU farklı ölçülerde tekrar ederse değişmez sayfa kimliği eklenir. Kimlikler sonraki taramalarda değişmez.
- Alka/Altın İş için güncel koşulsuz KDV dahil satıcı fiyatı ×1,20; Adore için ×1,30, kuruşa yarım yukarı yuvarlama. Eski fiyatı tekrar çarpmak yok. Metre/adet/takım birimleri korunur. Doğrulanmayan fiyat boş kalır.
- Aynı ürün olduğu ancak kanıtla anlaşılan kayıtlar gruplanır; benzer fotoğraf tek başına ürün birleştirmez. Kaynak kodlar kaybolmaz.
- Yönetim: tedarikçiler, ürün eşleştirme ve doğrudan kaynak bağlantıları, gerçekleşen alış kalemleri (tarih, miktar, birim, para birimi, belge/sipariş referansı), fiyat listesi yükle/karşılaştır/onayla. Alış fiyatı kaydı otomatik perakende fiyatı değiştirmez.
- Listeyle çalışan Göktaş ve diğer firmalar için son alınan liste tarihine göre 15 günlük panel uyarısı ve ayrıca Codex hatırlatması. E-posta gönderimi yapılmaz.
- Yeni ürünler medya ve dil incelemesi tamamlanana kadar yönetim hazırlık kataloğunda kalır. Üretim medya kapısı kaldırılmaz. Kur hesabı mevcut haftanın en yüksek TCMB döviz satış kuru ilkesini korur.

## Uygulama ve doğrulama sırası

1. Kaynak ayrıştırma, kuruş aritmetiği, değişmez kimlik, tekrar tarama idempotansı ve hatalı fiyat testlerini önce çalıştır; ardından ithalatçıyı geliştir. Sitemap kapsam raporu ve indirme hata listesi üret.
2. Tedarikçi kayıtları ve bütün mevcut ürünlerin kaynak eşleştirmesini hazırla. Eksik bağlantıları uydurmadan raporla. Yeni stok arşivinden görselli PDF ve aranabilir HTML katalog üret; örnek PDF sayfalarını render edip incele.
3. PHP yönetim kaynakları ve özel tedarikçi ekranı ekle. Yetki, CSRF, sürüm çakışması, tedarikçi/SKU eşleştirmesi, alış doğrulama, CSV liste farkı ve onay testlerini çalıştır.
4. Adore fiyat kuralını 1,30 yapıp canlı kaynaktan fiyatları yenile. Kaynak sayfa hash doğrulaması korunur; doğrulanmayanlar fiyatlandırılmaz.
5. Yönetim arayüzünü masaüstü ve mobilde gerçek yerel PHP/SQLite ile doğrula; kullanıcı rehberini güncelle. Üretim paketi yalnız bütün yayın kapıları geçerse hazırlanıp canlı kabulü ayrıca kaydedilir.

## İnceleme odağı

KDV hariç/dahil fiyat karışması; metre fiyatının adede dönüşmesi; aynı SKU farklı tedarikçi çakışması; dosyadaki formül/XSS içerikleri; tekrar yüklemenin alışları ve fiyat listesini çoğaltması; yönetim dışına alış fiyatı sızıntısı; eski kaynağın güncelmiş gibi yayınlanması.
