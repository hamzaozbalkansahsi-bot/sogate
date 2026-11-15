# Alışveriş sürümü kod ve arayüz incelemesi

İncelenen kapsam: yeni arama, ölçü, karşılaştırma, koleksiyon, hızlı inceleme ve sepet araçları; PHP hesap yönlendirmesi, sosyal birleştirme, paketleme ve dört dilli metinler. Medya işleme algoritmaları bu görevin değişiklik kapsamı değildir.

## Düzeltilen bulgular

- `web/shopping-ui.js` — Oturumun yüklenme durumundan anonim hazır duruma geçişinde misafir koleksiyonlarının okunması sağlandı. Sahip ve oturum değişiklikleri bekleyen istekleri geçersiz kılar.
- `web/shopping-ui.js` — SPA bağlantılarında varsayılan gezinmenin asenkron işleyiciden önce çalışabilme riski kaldırıldı. Alışveriş eylemi eşzamanlı olarak tanınır; yalnız sunucu işlemi asenkron yürür. Ctrl/Cmd ile bağlantı açma korunur.
- `web/shopping-ui.js` — Başka sekmenin koleksiyon sürümü üzerine yazılmaz. Hata kullanıcıya gösterilir ve son sürümü yeniden yükleme sunulur. Başarısız kayıtta koleksiyon adı taslağı korunur.
- `web/shopping-ui.js` — Önceki pencerenin bekleyen kaydı, sonradan açılan başka koleksiyon penceresini kapatamaz; pencere nesli ayrıca doğrulanır.
- `web/shopping-ui.js` — Sepet geri alma yalnız sepet içeriğiyle değil, seçili satırlar ve oturum sahibiyle de sınırlıdır. Arada seçim değişirse eski durum geri yazılmaz.
- `web/shopping-experience.css` — Gerçek mobil ekran görüntüsünde bildirim karşılaştırma şeridini kapatıyordu. Önce başarısız tarayıcı testi kaydedildi; bildirim ayrı yükseklikte konumlandırıldı. Dört motor/genişlik kontrolü geçti.
- `web/shopping-i18n.js` — Karşılaştırma kapsam etiketi ve çalışma zamanında seçilen durum başlıkları dört dilin sözlüğüne dahil edildi. Katalog ölçüleri değiştirilmedi.
- `web/shop-i18n.js` — Kaldırılmış JSON/TXT indirme eylemlerine ait eski yardım metni temizlendi. Yeni yerel geçmiş ve özel koleksiyon saklaması gizlilik metnine eklendi.

## Güvenlik ve veri kontrolü

Koleksiyon yolları mevcut aynı kaynak/CSRF/oturum ve hız sınırı sözleşmesini kullanır. Kullanıcı kimliği istek gövdesinden alınmaz. Sorgular parametrelidir; isimler HTML'e kaçırılarak yazılır. Gerçek katalog kimlikleri, isim uzunluğu, liste sayısı, ürün sayısı ve toplam kayıt sınırı hem istemcide hem sunucuda doğrulanır. Sürüm kontrolü ve yazma tek SQLite işlemi içindedir. Hesap birleştirme sınır ihlalinde sepet ve kimlikleri de geri alır. Hesap silme koleksiyon satırını yabancı anahtarla siler.

Özel koleksiyonlar tarayıcı web deposuna yazılmaz. Misafir koleksiyon aktarımı kullanıcı eylemidir. Karşılaştırma bağlantıları yalnız kamuya açık ürün kimliklerini taşır. Kişisel iletişim bilgileri son arama geçmişine otomatik kaydedilmez. Kalıcı hesap deposu sürüm paketinin dışındadır; dağıtım ona dosya kopyalamaz.

Kaynak güvenlik taraması gizli değerlerin eşleştiği dosya bulmadı; `.env.example` boş değerlerle kalır. Medya onay kapısı ve CSP gevşetilmedi. Vercel'in güncel arayüz kuralları semantik kontroller, form etiketleri, odak, görsel boyutları, iç kaydırma, RTL ve azaltılmış hareket açısından uygulandı. Kullanıcıya ait NODENO kimliği ve doğal dil kuralları önceliklidir.

## Doğrulama sınırları

174 Node/PHP kaynak testi ve 18 Python dağıtım testi geçti. Kaynak önizlemesinde iki motorlu üye koleksiyon testi; açık aktarım, kalıcılık, sürüm çakışması, yeniden deneme ve çıkış gizliliğini doğruladı. Ayrıca iki motorlu durum testi sepet seçim değişikliği sonrasında geri almanın kaldırılmasını, favorilerde adet korumayı, dört ürün sınırını ve onaylı koleksiyon silmeyi doğruladı.

Kesin paket ve canlı sonuçları [alışveriş deneyimi kabul kaydında](commerce-experience.md) tutulur. Windows WebKit gerçek bir iPhone değildir. Mevcut değişmemiş Windows WebKit CSP tanıları, önceki sürümdeki temel durumla ayrıca kaydedilir; sıfır konsol uyarısı iddia edilmez. Google/Apple sağlayıcı kabulü ve gerçek ödeme bu kapsamda açılmadı.
