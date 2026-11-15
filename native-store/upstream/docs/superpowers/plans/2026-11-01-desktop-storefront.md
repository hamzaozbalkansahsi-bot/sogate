# NODENO masaüstü mağaza düzeni

Kullanıcı mevcut mağazanın masaüstünü, daha önce verdiği Trendyol/Hepsiburada referansları ve mobilde kabul edilen davranışlarla geliştirmemizi istedi. Bu çalışma mevcut sayfaları düzenler; yeni ödeme, stok, satıcı, değerlendirme veya teslimat iddiası üretmez.

## Tasarım

Kanonik NODENO Sans, lacivert #172D38, kırık beyaz #F5F2E9, lime #D8EC81, beyaz #FFFFFF ve sınır #DADDD6 korunur. 1440px içerik sınırı, açık ürün hiyerarşisi ve gerçek mobilya fotoğrafları kullanılır. Masaüstü ürün sayfasında galeri, seçim/satın alma ve teslimat/destek alanları ayrılır. Mobil galeri, sabit satın alma alanı ve alt gezinme korunur.

Referanslar: https://www.trendyol.com/adore-mobilya/london-cok-amacli-dolap-kirmizi-73x79x42-cm-gxyxd-p-2473461 ve https://www.hepsiburada.com/cok-amacli-dolaplar-c-60005008. Erişilebilir sayfa içeriği incelendi; NODENO'ya ait olmayan görsel, fiyat, yorum veya kampanya aktarılmaz. Yerel tasarım becerisinin önerdiği farklı font/renkler kanonik marka ile çeliştiği için uygulanmaz.

## Uygulama

- [x] Fiyat sırası, fiyat aralığı, renk ve kategori ağacı için anlamlı mantık testleri; ardından mevcut filtre motorunu genişletme.
- [x] Masaüstü stil dosyası, ürün destek alanı, renk önizlemeleri, odalara göre ana sayfa vitrinleri ve sepet önerileri.
- [x] Kategori filtrelerini gerçek verilerle çalıştırma; URL, geri/ileri ve mobil filtre penceresiyle uyum.
- [x] Dört dil/RTL ve kullanım kılavuzu güncellemesi.
- [x] Gerçek kaynak arayüzünü Chromium/Windows WebKit üzerinde mobil ve masaüstünde inceleme; galeri, filtre, sepet ve misafir akışını doğrulama.
- [x] Kod incelemesi ve normal derleme. Görsel denetiminin publicationReady kilidi korunur; kapalıysa yayın başarılı sayılmaz.

Yayın dışı diğer sohbete ait medya dosyaları, denetimleri ve betikleri değiştirilmez. Hesaplar, özel anahtarlar, katalog/fiyat verisi ve ürün görselleri bu işte değiştirilmez.
