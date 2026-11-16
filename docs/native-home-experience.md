# Ana sayfa ve ortak mağaza düzeni

16 Kasım 2026. Kullanıcı yayın hedefini açıkça `/test` içindeki mağaza ana sayfası ve ortak düzen olarak belirledi. `sexogate.com` kökündeki hazırlanıyor sayfası bu işin dışındadır.

## Referans ve uygulama

[Trendyol ana sayfası](https://www.trendyol.com/) 16 Kasım 2026 tarihinde resmî HTML ve uygulama içi tarayıcıdaki gerçek masaüstü görünümüyle incelendi. İlk otomatik headless erişimin 403 sonucu başarılı görsel inceleme sayılmadı; uygulama içi tarayıcıda sayfa açıldı, zorunlu olmayan çerezler reddedildi ve açılış penceresi kapatıldı. Kaynak sitenin fotoğraf, logo, satıcı, yorum ve satış verileri taşınmadı.

- Ortak masaüstü header: solda mevcut onaylı dikey logo, geniş arama, dil/para ve hesap/favori/sepet eylemleri; altta kategori satırı. Mobil alt menü ve kategori sayfasındaki kompakt arama korunur.
- Dolu kökler ve alt kategorilerden en çok on görselli kısayol.
- Kampanya kartlarından önce yatay Seçili ürünler rafı. Katalog sırasındaki baskın grubun bütün rafı doldurmasını önlemek için kökler arasında sırayla model seçilir.
- Dört kompakt görselli koleksiyon alanı, ilgili kategori rafı ve sekmeli Keşfedebileceğin ürünler. Aynı raf model tekrarı yapmaz; varsayılan ek raflar mümkün oldukça farklı modeller kullanır.
- Keşif sekmesi URL, klavye odağı ve kaydırma konumuyla birlikte çalışır. Beden/renk filtrelemek ya da sekme seçmek sepet varyantı seçilmiş sayılmaz.
- Blog, yardım, e-posta ve mevcut yönetilen koleksiyon bağlantıları çalışır. Son gezilenler yalnız mevcut izinli geçmiş varsa gösterilir.
- Satıcı mağazası, satıcı puanı, uydurma çok satan/indirim/kupon/kargo rozeti veya geri sayım eklenmez. Marka, krem/bordo renkler ve mevcut fontlar korunur.

## Kaynaklar ve doğrulama

`home-core.js` ve `home-model.php` aynı model seçimini uygular; `home-renderers.js`, `home.php`, `home.css`, `home-copy.json` ve `home-build.mjs` türetilmiş PHP paketini oluşturur. Korunan `native-store/upstream` değiştirilmez, hosting üzerinde Node kullanılmaz. İlk HTML ve istemci aynı ürün sırasını seçer; sonradan büyük kampanya düzenine dönüşmez. HomeCategory URL’si sunucu ve istemcide noindex,follow kullanır.

```powershell
node --test scripts/test-native-home.mjs
python scripts/test-native-home-browser.py
python scripts/build-native-stage.py
```

Durum: **Yalnız test ortamında çalışıyor ve test edildi.** `https://sexogate.com/test` üzerinde etkin paket `0c0e76d696171c6fba60f5da`, kaynak `06d111c3d97338e5ed25077d62abce1de94d58c5`. ZIP SHA256 `537856e71eeac4ad076d9d75c285c8c15844598996377dc37603506815c1c709`. Yerel ve özel önizlemede 11 kabul grubu, etkin adreste ana sayfa/kategori/ürün düğmesi/sepet iki motor turu geçti. Prototip kabul sayılmadı; bütün bu sonuçlar nihai, değiştirilmemiş paket üzerindedir. 47 Node, 23 PHP varyant, 18 katalog, 14 içerik kontrolü; 60 PHP syntax ve 79 JS modülü derleme kontrolünden geçti. Kanıtlar `native-home-local-results.json`, `native-home-preview-results.json`, `native-home-remote-results.json` ve `native-deployment-report.json`. Ana site aynı, tahsilat HTTP409 ile kapalıdır. Worker ve iki SQLite veritabanının şifreli geri yüklemesi doğrulandı; medya geri yüklemesi yapılmadı.

Tam WCAG denetimi, fiziksel iPhone testi ve saha Core Web Vitals ölçümü ayrı açık işlerdir. Gerçek tahsilat, işletme/ödeme/ülke/vergi/kargo/hukuk kabulüne kadar kapalıdır. Mevcut aralıklı uzak bağlantı sorunu ve GitHub CI faturalama engeli çözülmüş sayılmaz.

Yeni kaynak commit’inin GitHub CI işleri hesap faturalama kilidi nedeniyle sıfır adımda kaldı; CI başarılı sayılmaz. Görsel kanıtlar `docs/screenshots/native-store-home-local/`, `native-store-home-preview/`, `native-store-home-remote/` altındadır.

Bu teslimde üç ilk deneme zaman aşımı kaydı tutuldu: önizlemede yönetim ürün API’si, Azerbaycanca dil girişi ve etkin adreste kategori sayfası yüklemesi. Aynı paket, test kodu, süre sınırları, TLS ve hazır olma kurallarıyla bağımsız tekrarlar geçti. Dil tekrarı aynı release/script hash’li checkpoint ile yalnız başarısız girişi yeniden sınadı. Bunlar bağlantı kök nedeninin giderildiği iddiası değildir; ayrıntılar yayın raporundadır.
