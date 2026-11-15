# NODENO mağaza tasarımı

Amaç, 667 gerçek mobilya ürününü arama, oda/kategori, ürün sayfası ve kalıcı seçim listeleriyle kolayca gezdirmek. Hepsiburada'nın doğrulanmış bilgi mimarisi ve PAZVION'un kategori, ürün, sepet ve hesap etkileşimleri referanstır; doğrulanmamış satış, fiyat, puan ve teslimat vaadi kullanılmaz.

## Tasarım kararı

Renkler: lacivert `#172D38`, fildişi `#F5F2E9`, lime `#D8EC81`, ikincil metin `#536770`, çizgi `#DADDD6`, beyaz `#FFFFFF`. Tüm tipografik roller, kurumsal paketteki yerel NODENO Sans 400/700 ile kurulur. Başlıklar 32–48px, gövde 16–18px, yardımcı metin 14px; ana eylemler en az48px. Logo orijinal SVG olarak doğal oranında kalır.

Seçilen yerleşim yoğun perakende düzenidir: beyaz başlıkta geniş arama, hesap/favori/sepet; altında kök kategoriler ve klavyeyle açılan kategori paneli. Ana vitrinde gerçek Lungo ürün fotoğrafı ve slogan; yanında iki gerçek kategori vitrini. Daire fotoğraflı kategoriler ve yatay ürün rafları mobilya keşfini hızlandırır. İmza öğesi, NODENO'nun koyu lacivert arama çerçevesi ile lime seçim eylemlerinin gerçek ahşap ürün fotoğraflarıyla birlikte kullanımıdır.

```text
Masaüstü: [logo] [          arama          ] [hesap] [favori] [sepet]
          [kategoriler] [oda] [ürün grupları] [destek]
          [gerçek ürün + slogan vitrini       ][kategori vitrini]
          [dairesel kategori gezintisi                         ]
          [yatay ürün rafları / gerçek son görüntülenenler      ]
Mobil:    [logo] [dil] [hesap]
          [             arama             ] (yapışkan)
          [vitrin] [kategori şeridi] [iki sütun ürün]
          [ana sayfa] [kategoriler] [favori] [sepet] [hesap]
```

Önceki geniş boşluklu tanıtım sayfası, daha çok ürün ve arama gösteren mağaza düzenine dönüşür. Fiyat verisi olmadan indirim/puan blokları eklemek yerine ürün adı, kod, kategori ve teklif listesi eylemleri kullanılır. Böylece referans alışveriş mekaniği korunurken NODENO'nun mobilya odağı ve kurumsal tasarımı görünür kalır.

Son görsel düzeltmede antre ve çocuk odası kartları, düz renk kutu ve küçük ürün fotoğrafı yerine gerçek yaşam alanı fotoğraflarıyla tüm yüzeyi doldurur: antre `/media/2738/0`, çocuk odası `/media/2595/1`. Fotoğraf altındaki lacivert geçiş, beyaz başlık ve tam cümlelerin okunaklılığını sağlar. Mobilde fotoğrafları küçültmemek için kartlar yatay kaydırılabilir; ikinci kartın kenarı devam eden içeriği gösterir. Dekoratif oklar kaldırılır; galeri, adet ve kapatma kontrollerinde aynı çizgi kalınlığındaki işlevsel SVG simgeleri kullanılır. UI/UX Pro Max'in resim üstü metin kontrastı ve dokunma önerileri, kullanıcı tarafından verilen marka paleti ve yerel yazı tipleri korunarak uygulanır.

## Sayfalar ve gerçek veri

`?page=home|catalog|cart|favorites|account|login|register|addresses|orders|shipping|help|checkout` ve mevcut `?product=id` bağlantıları yenileme ve tarayıcı geri dönüşünde korunur. Dil URL'de tutulur; Arapça RTL'dir, logo/fotoğraf ve ürün kodları aynalanmaz. Hesap oturumu, CSRF, profil, parola, adres, sunucu sepeti/favori eşleştirmesi gerçek API'yi kullanır. Oturumdan çıkış hesap seçimlerini tarayıcıdan temizler. Konuk seçimleri yalnız oturum açıldığında birleştirilir; sunucu sonrasında yetkilidir.

Ödeme ve sipariş oluşturma kapalıdır. Sepet TXT/JSON indirme, yazdırma, adet, seçme, silme ve favoriye taşıma sunar. Hesapta sipariş ve kargo kayıtları yoksa dürüst boş durum gösterilir. Parola sıfırlama e-posta gönderimi kurulmadığı için başarı iddiası üretmez. Teslimat/iade/kurulum yardım metinleri mevcut ticari sınırı açıklar.

## Kabul

667 ürünün arama/kategori/ürün bağlantıları; galeri, adet, favori ve sepet; gerçek kayıt/giriş/çıkış, sunucuda seçim ve adres CRUD; dört dil ve RTL; 390/768/1366px taşma, klavye odağı, hata/boş/yüklenme durumları, yenileme ve geri tuşu kontrol edilir. NODENO dışındaki referans kaynaklara yazılmaz. Yayın ve arka uç paketleme ana ajan tarafından yapılır.
