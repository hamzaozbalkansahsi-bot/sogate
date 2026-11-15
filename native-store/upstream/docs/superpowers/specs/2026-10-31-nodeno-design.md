# NODENO mağazası tasarımı

Kullanıcı tüm tasarım, geliştirme ve yayını tek görevde yetkilendirdi. NODENO bağımsız bir marka ve projedir; Lyvora ERP dosyaları, hesapları ve yayınları bu işin kapsamı dışındadır.

Amaç, Adore bayilik kapsamındaki bütün ürünlerin NODENO konseptinde Türkçe, İngilizce, Rusça ve Arapça sunulduğu mobil uyumlu bir mağazadır. Slogan Türkçe “İyi tasarım. Kolay yaşam.”, İngilizce “Good design. Easy living.” olur. Arapçada belge yönü RTL değişir. Model adları ve ürün kodları korunur, üretici markası NODENO üretimi gibi gösterilmez.

Kullanıcı 31.10.2026 tarihinde alan adı, firma, ödeme ve fiyat bilgilerinin henüz belli olmadığını ve görsel/metinlerin NODENO markasıyla kullanımının bayilik sözleşmesinde bulunduğunu belirtti. Bu nedenle ilk yayın tahsilat yapmayan katalog ve teklif sepetidir. Fiyat, stok, teslim süresi, yasal firma, iletişim, ödeme başarısı veya sipariş kaydı uydurulamaz. Teklif listesinin indirilmesi talebin firmaya ulaştığı anlamına gelmez.

Kamuya açık 102 kategori ve 669 ürün site haritası adresi, robots kurallarına uygun ve tanımlanmış istemciyle okunur. Kaynak alanlar, bütün görseller, açıklamalar, teknik bilgiler ve tarihler ayrı ham arşivde korunur. Başarısız adres ve eksik alanlar raporlanır. Kaynak perakende fiyatı satış fiyatı değildir. Kullanıcıya ürün koduyla arama, kategori keşfi, ürün ayrıntısı, galeri, favoriler, yerel sepet ve teklif listesi dışa aktarımı sunulur.

Mimari: bağımlılıksız ES modül tabanlı Cloudflare Worker, derleme anında paketlenen katalog ve statik arayüz. Tarayıcıda yalnız cihaza özel sepet/dil/favori saklanır; ödeme veya sipariş verisi alınmaz. Görseller sunucuda yalnız kayıtlı ürün/görsel kimliğiyle çözümlenir. Keyfi URL proxy'si, istemciye açık Google tokenı veya Drive paylaşım izni yoktur. Görsel sağ tık/sürükleme sınırlandırılır; ürün paylaşımı, metin kopyalama, erişilebilirlik ve ekran görüntüsü açık kalır. Ekrana gelen görselin mutlak kopya koruması olduğu iddia edilmez.

Yeni Google hesabı henüz bağlı olmadığından mevcut kişisel Drive'a dosya yazılmaz. Tekrar çalıştırılabilen, deneme raporlu, OAuth ile yetkilenen taşıma aracı hazırlanır; gerçek aktarım ancak yeni hedef klasör ve yetkiyle yapılabilir. Bu bağımlılık teslim raporunda açık tutulur. Geçişe kadar görseller izinli kaynak sunucudan gelir.

Görsel sistem: açık mimari taş #ECECE7, espresso #302D26, orman mürekkebi #23433E, beyaz ürün sahnesi #F7F7F3, soluk zeytin #A4A68C. Manrope/DM Sans/Noto Sans Arabic. Büyük fotoğraflı asimetrik hero, sakin kategori rayı, okunaklı ürün ızgarası, özgün NODENO kelime logosu. Sahte istatistik, değerlendirme ve promosyon yoktur.

Kabul: tam kaynak sayımı, aktarım hata raporu, gerçek ürün kimlikleri/görselleri, dört dilde kritik akış, Arapça RTL, 390/768/1366 ekran kontrolü, klavye/diyalog davranışı, kalıcı yerel sepet, paylaşım bağlantısı, güvenli medya proxy'si, ilgili Yardım sayfası ve gerçek Sites yayın sonucu. Eksik Google hesabı, ödeme, alan adı ve ticari bilgiler tamamlandı diye raporlanmaz.
