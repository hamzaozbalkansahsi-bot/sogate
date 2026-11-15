# Ziyaretçi ülkesi ve mağaza dili

## 11 Kasım 2026 — üst menü, para birimi ve harita seçimi

Dil ve para birimi üst menüde yan yanadır; ana sayfa, kategori, ürün ve sepet aynı para birimi durumunu kullanır. Dil değişimi varsayılanı Türkçe → TRY, İngilizce → USD, Rusça → RUB, Arapça → SAR, Almanca → EUR, Azerbaycanca → AZN, Kazakça → KZT olarak yeniler. Türkmence, Özbekçe, Kırgızca ve Farsça için TCMB kapsamında olmayan para birimlerinin yerine USD kullanılır. Ardından kullanıcı para birimini ayrıca seçebilir. Elle seçilen para birimi, dil tekrar değiştirilene kadar yenilemede korunur. Eski tek başına KZT kaydı Türkçe görünümü KZT'ye kilitlemez.

Haritada veya ülke listesinde üzerine gelme/odak yalnız önizleme yapar. Tıklama ya da haritada Enter/Space, ülkeyi seçer; posteri kapatıp geçerli sayfayı ülkenin dili ve para birimiyle açar. Türkiye tr/TRY, Almanya de/EUR, Birleşik Krallık en/GBP, Kazakistan kk/KZT, Azerbaycan az/AZN, Türkmenistan tk/USD, Özbekistan uz/USD, Kırgızistan ky/USD, İran fa/USD, Irak ve Suriye ar/USD kullanır. Ülke adları da seçilen dildeki sözlükten gelir; tarayıcının başka dilde ad döndürmesine güvenilmez. Geçerli resmî kur alınamazsa yabancı fiyat tahmin edilmez; TRY gösterilir. Haftanın o ana kadarki en yüksek TCMB satış kuru hesabı değişmedi.

`nodeno.currency.preference.v2` kaydı dil, para birimi ve seçim kaynağını; `nodeno.market-country.v1` açıkça seçilmiş vitrin ülkesini saklar. Dil değiştirmek ülkeyi değiştirmez. Açık harita seçimi, bu tarayıcıdaki vitrin pazarını IP önerisinin önüne alır; sunucunun gerçek IP bilgisini veya erişim yetkisini değiştirmez. Gerçek teslimat ülkesi yine adres/teklif formunda doğrulanır. Bu kayıtlar zorunlu görünüm tercihleridir; analiz izni veya kişisel konum kaydı değildir.

Mobilde ürün görselini örten hızlı inceleme düğmesi gizlidir; ürünün görseli ve adı ürün sayfasını açar. Ürün sıraları iki tam kart gösterir. Masaüstü hızlı inceleme korunur. Para birimi seçicisi, normal ürünler, ölçülü ürünler ve kapak fiyatları aynı döviz durumu modülünü kullanır; farklı önbellek sorgularının ayrı para birimi durumları oluşturması giderildi. Kanıtlar `artifacts/mobile-market-20261111`, tarayıcı senaryoları `tests/browser/mobile_market.py` ve `mobile_market_live.py` içindedir.

Açık bir harita/pazar tercihi bulunmadığında Türkiye'den girişte ürünün uluslararası toplu alım kutusu, üst/alt menüdeki toptan satış çağrıları ve perakende takım oluşturucudaki toplu alım geçişi gizlenir. Yalnız İngilizce, Rusça veya Arapça seçmek Türkiye ziyaretçisini ihracat ziyaretçisi yapmaz. Perakende takım oluşturma ve seçili parçaları sepete ekleme korunur.

Yurt dışındaki doğrulanabilen IP ülkelerinde bu çağrılar açılır. Doğrudan paylaşılan toptan teklif sayfası ve toptan takım bağlantıları erişilebilir kalır; ülke tespiti bir erişim yetkisi veya teslimat uygunluğu kontrolü değildir. Teslimat ülkesi teklif formunda ayrıca seçilir. Ülke belirlenemezse toplu alım tanıtımı gizlenir.

## Dil seçimi

Desteklenen bir `lang` bağlantısı önceliklidir. Ardından ziyaretçinin dil seçicisinde kaydettiği tercih kullanılır. Tercih yoksa ülke eşlemesi uygulanır: Almanya Almanca, Azerbaycan Azerbaycanca, Kazakistan Kazakça, Türkmenistan Türkmence, Özbekistan Özbekçe, Kırgızistan Kırgızca ve İran Farsça açılır. Türkiye Türkçe; Rusya ve Belarus Rusça; Arapça kullanılan destek kapsamındaki ülkeler Arapça açılır. Diğer ülkeler İngilizce kullanabilir; desteklenen hedef ülkeler İngilizce veya Rusçaya düşürülmez. Arapça ve Farsça RTL korunur. Kanonik kayıt `data/store-locales.json`, kapsam ve bakım [hedef ülke dilleri belgesindedir](hedef-ulke-dilleri.md).

Elle seçilen dil `nodeno.language.v1` yerel kaydında ve `nodeno_language` tercih çerezinde tutulur. Çerez, bir sonraki HTTP yanıtının da aynı dilde hazırlanmasını sağlar. Otomatik ülke dili kalıcı manuel tercih diye kaydedilmez. Önceki sürümden kalmış yerel dil tercihi ilk açılışta korunup çereze aktarılır. Bağlantılar mevcut dili taşır; URL'de geçerli bir dil varsa özellikle seçilmiş bağlantı olarak değerlendirilir.

## Sunucu ve veri kaynağı

`hosting/visitor-market.php`, PHP'nin doğrudan `REMOTE_ADDR` değerini yerel IPv4/IPv6 aralıklarında ikili aramayla bulur. Tarayıcı dili, `country` sorgusu, `CF-IPCountry` ve `X-Forwarded-For` başlıkları ülke kanıtı sayılmaz. Şu an Turhost'un önünde güvenilen bir CDN/proxy yapılandırması bulunmuyor; ileride eklenirse gerçek ziyaretçi IP'si yalnız güvenilen proxy adresleri doğrulanarak aktarılmalıdır.

IP adresi başka bir konum servisine gönderilmez ve bu özellik tarafından kaydedilmez. Kesin cihaz konumu istenmez. `/api/visitor-context` yalnız ülke, uluslararası görünürlük ve önerilen dili döndürür; IP adresini döndürmez. HTML ve bu yanıt `no-store` ile ziyaretçiler arasında önbelleğe alınmaz. VPN/proxy kullanılıyorsa çıkış IP'sinin ülkesi algılanır; IP tabanlı ülke bilgisi kesin konum kanıtı değildir.

Veri kaynağı [DB-IP Country Lite](https://db-ip.com/db/download/ip-to-country-lite), Kasım 2026 sürümü, CC BY 4.0 lisanslıdır. Lisansın gerektirdiği `IP Geolocation by DB-IP` bağlantısı sayfa altında yer alır. 362.998 IPv4 ve 369.798 IPv6 aralığı 16.203.112 baytlık iki özel dosyada tutulur. Kaynak URL/özeti, lisans ve çıktı özetleri `data/geo/geo-license.json` içindedir. Veriler özel sürüm dizininde yayımlanır; herkese açık ürün API'sine veya web köküne eklenmez.

Aylık güncelleme: `python scripts/update-country-db.py --month YYYY-MM`. Ardından normal kaynak testleri, paketleme, medya yayın kapısı ve Turhost dağıtımı yapılır. Zamanlanmış güncelleme kurulmadı. Derleme, dosya özetleri ve kayıt boyları uyuşmazsa durur. Veri dosyası eksik/bozuksa ülke belirlenemez ve mağaza ülkeye bağlı toplu alım çağrısını gizler.

## Doğrulama

`tests/visitor-market.test.mjs` ülke/dil ayrımını, tercih önceliklerini, IPv4/IPv6 aralık sınırlarını, IPv4-mapped IPv6'yı, sahte proxy başlıklarını ve eksik/bozuk veri dosyasını denetler. `tests/browser/visitor-market.py` gerçek PHP ülke okuyucusunu, özel ve yayımlanmayan IP test girdisiyle 11 ülke/bilinmeyen durumunda Chromium mobil/masaüstü ve WebKit mobilde çalıştırır. Ürün kutusu, menüler, takım geçişi, perakende takım kutusu, manuel dil, sunucuda tercih, URL önceliği, canonical dili ve yatay taşma kontrol edilir. Canlı kontrol gerçek test bağlantısının çıkış ülkesini kullanır; başka ülkelerden fiziksel bağlantı yapılmış gibi raporlanmaz.

Kanıtlar `artifacts/visitor-market` altındadır. Yayın sırasında fiyatların 24 saatlik doğrulama süresi dolduğu için tedarikçi fiyatları yeniden kontrol edildi. 666 fiyat doğrulandı ve tutarları aynı kaldı. `4639 / AGT-144EL-BB-1` sayfasında tam SKU eşleşmediğinden eski fiyat doğrulanmış gibi korunmadı; ürün kalır, fiyatı doğrulanana kadar gösterilmez. Kontrol `prices-refresh-review.json` dosyasındadır.
