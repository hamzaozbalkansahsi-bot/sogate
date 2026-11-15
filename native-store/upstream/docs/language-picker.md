# Mobil dil seçici kesilmesi

Kullanıcının iPhone görüntüsünde TR etiketinin ikinci harfi kırpılıyordu. Gerçek eski pakette WebKit, 390 piksel genişlikte sorun yeniden üretildi: seçici 46 piksel, yazı genişliği 19,52 piksel; doğal göstergeye ayrılan alandan sonra metne yalnız 14 piksel kalıyordu (`artifacts/language-picker/red.log`, eski paket ekranı).

Kontrol 68 piksele genişletildi; doğal gösterge yerine aynı seçicinin üzerinde işlevsel SVG gösterge ayrı konumlandırıldı. Yerel dil menüsü, erişilebilir adı, klavye odağı ve seçim davranışı korundu. CSS sürüm bağlantısı yenilendi. Değişiklik yalnız üst bilgi dil kontrolü ve stil sürümüyle sınırlıdır.

Yeni gerçek paket: `0ba468acc04cc378af916232ee6ba2fc3a4f5c0912ce1087cca204fd56bd4229`. Chromium ve Windows WebKit üzerinde dört dil, 320/390/430/768/1024/1440 piksel, ana sayfa/kategoriler toplam 96 senaryo geçti. Metin için yeterli alan, kontrol yüksekliği, dil değişimi, üst bilgi çakışması ve yatay taşma doğrulandı. WebKit Türkçe ekranı gözle incelendi; TR tam okunuyor. Fiziksel iPhone testi yapılmadı.

Kaynak suite 226/226; dağıtım yardımcı testleri 18/18. Kanıtlar `artifacts/language-picker` altında. İlgisiz medya/katalog değişiklikleri korunur. Yayın ve gerçek canlı kabul tamamlandı.


Yayın: `6403788` uygulama kaynağı, yukarıdaki tam sürüm kimliği; zorunlu medya denetimi geçti. `uploaded_verified_health=ok`. Yedek `/home/nodenoho/nodeno-backups/20261101T183029Z-0ba468acc04c-3dd432`.

Canlı: `tests/browser/language-picker.py --live` Chromium ve Windows WebKit üzerinde aynı 96 senaryoyu geçirdi (`live.log`, `live-report.json`). Güvenilir HTTPS ile gerçek sürüm kimliği doğrulandı. `live-webkit-tr.png` gözle incelendi; TR tam okunuyor. Gerçek müşteri/talep/sipariş oluşturulmadı. Açık önemli kod inceleme bulgusu yok.
