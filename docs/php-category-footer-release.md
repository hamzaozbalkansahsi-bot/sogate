# PHP kategori, logo ve sosyal bağlantı güncellemesi

14 Kasım 2026 son kullanıcı talepleri: footer logosu ortalı, header logosu solda; simge yazının üstünde; sosyal bağlantılarda ikon ve hareket. Mobil kategori açılır listesinin yerine NODENO'nun tam sayfa görselli kategori yapısı alınır. Yalnız `sexogate.com/test` yayın kapsamındadır.

## Davranış

- Footer logosu bütün genişliklerde ortada, header logosu içerik başlangıcında. SVG'nin gereksiz yatay boşluğu daraltıldı; mevcut düzenlenebilir path geometrisi korunur. Simge ile yazının merkez farkı0.0000191px ölçüldü. Güncel doğal boyut458.008×269.088; HTML boyutları aynı oranı korur.
- Instagram, Facebook, X ve TikTok bağlantıları harici kütüphane/font gerektirmeyen yerel inline SVG simgeleri taşır. Simgeler proje için çizilmiş ağ tanıma işaretleridir; üçüncü taraf fotoğraf veya lisanslı ikon paketi kopyalanmadı. Link metni erişilebilir ad olarak kalır, dekoratif SVG gizlidir.
- Hover ve klavye odağında krem/bordo renk geçişi,3px yükselme, küçük ikon dönüşü ve ok hareketi var. `prefers-reduced-motion: reduce` durumunda dönüş/animasyon yok; kontrast ve odak halkası korunur.
- Mobil alt menü beş doğrudan bağlantıdır: Ana sayfa / Kategoriler / Favorilerim / Sepetim / Hesabım. Kategori düğmesi düz liste dialogu açmaz. Boş sepet rozeti gizlenir. Etkin bağlantı ve kategori sayfasının özel yerleşimi aynı belge içinde ileri/geri gezinmede güncellenir.
- Tam kategori sayfasında başlık, gerçek toplam ürün sayısı, mobilde iki sütun kategori görseli/adı/sayısı bulunur. Yalnız mevcut katalog gösterilir; şu anki üç test ürünü ve bir kategori gerçek tedarikçi aktarımı değildir. Mobil kategori sayfasında NODENO gibi logo, kategori şeridi ve footer gizlenir; arama/dil ve kalıcı alt menü kalır.

## Doğrulama ve yayın

İlk tarayıcı regresyonu footer hizasında; sonra SVG'nin%18.55 sol iç boşluğunda ve geri dönüşte eksik etkin bağlantı işaretinde başarısız oldu. Düzeltilmiş kontroller Chromium/WebKit ×360/390/430/768/1440 boyutlarında10/10 geçti. Klavye odağı, hover, azaltılmış hareket, kategoriye aynı belgede geçiş, gerçek ürün sayısı, iki sütun, yatay taşma ve geri dönüş denetlendi. Gerçek iPhone testi yapılmadı.

Yerel kanıtlar: `.local/php-category-brand-local.json`, `.local/php-category-brand-local.log`; ekranlar [390px header](screenshots/php-category-brand-local/chromium-header-390.png), [footer logosu](screenshots/php-category-brand-local/chromium-footer-logo-390.png), [sosyal bağlantılar](screenshots/php-category-brand-local/chromium-footer-390.png), [kategori](screenshots/php-category-brand-local/chromium-categories-390.png).42 sayfalık axe/klavye/harici istek kontrolü0 ihlal;10 footer/geri konumu ve2 kamu gezinmesi kontrolü geçti.

Paket `10396efcfb5b01e868f6f8cc`, SHA256 `c166a9720664e6658e9dcf228694fb5da9388e002fa6340df8132df11ae2786e`,3264 dosya/6.595.776 bayt. Temiz kurulum, şema doğrulama, aktivasyon, tek kullanımlık kurucu tokenı ve ZIP yol kaçışı reddi geçti. Kod commit'i `186e295`; tam suite123 test/482 assertion,08:02.541,48MB PASS. İlk denemede kalan eski dialog beklentisi, yeni kategori gridini ve dialogun yokluğunu denetleyen daha güçlü sözleşmeyle güncellendi; kontroller kapatılmadı.

Yayın öncesi yedek83 tablo/761 satır/92FK ve26 migration/hash/forward kontrolüyle yerelde geri yüklendi. Ardından yalnız `/test` yayımlandı. `--verify` özel kaynakların kapalı, kurucunun kaldırılmış, ana kökün değişmemiş olduğunu doğruladı. Sağlık cevabı `{"status":"ok","runtime":"php","database":true,"salesEnabled":false}`. Uzak Chromium/WebKit ×5 boyut10/10 kategori/logo/hareket,10/10 kamu/ikon/vitrin,10/10 footer sonu/resize/geri konumu;42 sayfa axe/klavye0 ihlal ve2/2 kamu gezinmesi geçti. Son uzak kabul15 Kasım2026 gecesinde tamamlandı.

Her iki uzak motorda katalog oluşturma/stok/yayın/misafir sipariş, toplama/paketleme/sevk, karantina iadesi/kısmi para iadesi,15 yönetim modülü, sepet adet/seçim/kaldır/boşalt/geri alma, üç adımlı misafir checkout ve CSV önizleme/onay geçti. Bunlar izole test verisi ve test ödeme adaptörüyle yapıldı; gerçek Stripe/taşıyıcı/fatura erişimi olarak sunulmaz. Yerel kanıt `.local/php-category-operations-local.log`, uzak kanıt `.local/php-category-operations-remote.log`.

Gerçek son çıktı:

```text
python scripts/test-php.py
Time: 08:02.541, Memory: 48.00 MB
OK (123 tests, 482 assertions)

python scripts/test-php-accessibility.py --remote
{"pages":42,"keyboardAgeNotice":true,"keyboardExit":true,"unexpectedThirdPartyHosts":0,"failures":[]}

python scripts/publish-php-test.py --verify
PHP test release verified; private files blocked, installer removed, main site unchanged.
```

Uzak görseller: [header](screenshots/php-category-brand-remote/webkit-header-390.png), [ortalanmış footer logosu](screenshots/php-category-brand-remote/webkit-footer-logo-390.png), [sosyal bağlantılar](screenshots/php-category-brand-remote/webkit-footer-390.png), [tam kategori sayfası](screenshots/php-category-brand-remote/webkit-categories-390.png). Gerçek iPhone yerine WebKit benzetimidir.

Yayın ve operasyon testleri sonrasında yeni şifreli yedek83 tablo/901 satır/92FK ile tekrar geri yüklendi;26 migration/hash ve forward doğrulaması geçti. Gerçek PHP cron kontrolü `2026-11-14T21:03:02+00:00` anında `ok:true`, runtime8.3.36 verdi. Son `--verify` ana kökün değişmediğini yeniden doğruladı. Kaynak/paket karşılaştırmasında139 birinci taraf dosyasında uyuşmazlık yoktu; son commit sonrasında runtime kaynak değişikliği yapılmadı.

## GitHub kaydı ve CI engeli

Kod `186e295`, belge/ekran kanıtı `435a226`; yalnız izinli `hamzaozbalkansahsi-bot/sogate` deposunun `codex/local-commerce` dalına normal push yapıldı. Force push/merge yok. Paylaşılan AGENTS/progress dosyalarında yalnız bu görevin paragrafları index'e alındı; diğer sohbetlerin çalışma kopyaları bayt hash'iyle korunarak doğrulandı.

15 Kasım kontrolünde [PHP CI43641007476](https://github.com/hamzaozbalkansahsi-bot/sogate/actions/runs/43641007476) ve [uygulama CI43641007386](https://github.com/hamzaozbalkansahsi-bot/sogate/actions/runs/43641007386) failure döndü; her ikisinde0 adım çalışmıştı. Gerçek annotation: “The job was not started because your account is locked due to a billing issue.” Bu hesap engeli giderilmedi; CI başarılı gösterilmez ve kontroller kapatılmaz. Gerçek yerel123/482 ve uzak kabul sonuçları yukarıdaki gibidir. Node/Next kodu veya bu hesap için ücret/ödeme ayarı değiştirilmedi.

Komutlar:

```powershell
python scripts/test-php.py
python scripts/test-php-category-brand.py
python scripts/test-php-accessibility.py
python scripts/test-php-footer-navigation.py
python scripts/test-php-public-navigation.py
python scripts/package-php.py --output-root D:\sexogate-local-artifacts-20261114\builds
python scripts/test-php-install.py --sandbox-root D:\sexogate-local-artifacts-20261114\private-installs
python scripts/backup-php-test.py
python scripts/publish-php-test.py --deploy --package-root D:\sexogate-local-artifacts-20261114\builds
python scripts/test-php-category-brand.py --remote
```

Tüm NODENO eşdeğerliği [php-nodeno-parity.md](php-nodeno-parity.md) içinde modül bazında izlenir; bu dar güncelleme tam sistemi bitirmiş sayılmaz. Üç tedarikçi için gerçek tam katalog ve Liora ürün görselleri [tedarikçi araştırmasında](php-supplier-research.md) açık kayıtlıdır.
