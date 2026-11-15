# Doğrudan NODENO uygulama kopyası

15 Kasım2026 kullanıcının son kararı: önce bütün NODENO uygulama kodu doğrudan alınır; ekranlar, menüler, modüller, dil/para/ödeme/alışveriş motoru yeniden yazılmaz. Yalnız marka ve tema katmanı SEXOGATE olur. Önceki parça parça PHP uyarlaması bu kararın yerine sunulamaz.

`upstream/` NODENO çalışma ağacından doğrudan alınan uygulama kaynaklarıdır. Git'e alınmamış güncel geliştirmeler dahildir.52 PHP/61 JavaScript motoru byte olarak aynıdır.768 dosya özgün byte'larıyla korunur; GitHub'ın anahtar taraması nedeniyle yalnız3 test dosyasındaki açık sahte Stripe sabitleri çalışma anında üretilen test verisine çevrilmiştir. Özgün/güvenli SHA256 çiftleri `source-manifest.json` içindedir; asıl NODENO klasörüne dokunulmamıştır. Burada arayüz veya iş kuralı yeniden yazılmaz. Tema `theme/` altında ayrıdır; derlenen yerel kopyada uygulanır.

Kaynak kapsamı: bütün web/hosting/lib modülleri, kurulum/derleme/operasyon kodları, testler ve teknik belgeler; ortak arayüz çevirileri ve ülke tarih/saat kayıtları. NODENO'nun `.env`, OAuth/sır, müşteri/oturum/sipariş/veritabanı, fiyat/ürün/bayi/medya arşivi ve onayları bu uygulamanın verisi değildir; alınmaz. Kaynak operasyon scriptleri referans olarak korunur, SEXOGATE yayın komutu olarak çalıştırılmaz.

Yerel kopyayı hazırlama:

```powershell
python scripts/copy-nodeno-source.py
python scripts/test-native-source.py
python scripts/build-native-store.py
```

Yerel çalıştırma bilgisi Git dışı `.local/native-store-build.json` dosyasına yazılır. PHP'nin özgün PDO SQLite motoru ayrı yerel depoda kullanılır; eski SEXOGATE MySQL kayıtları ve `/test` yayını değiştirilmez. Bu aşamada eski veritabanını düşürmek, diğer sohbetlerin dosyalarını silmek veya ana siteyi yayımlamak yoktur. NODENO'nun runtime kontrolleri ve dış servis kabul şartları kopyada da geçerlidir. Test edilmeyen modül çalışıyor sayılmaz.


Son kaynak:771 dosya;52 PHP ve61 JS motor dosyası değiştirilmeden çalıştırıldı. Son153 regresyon, iki tarayıcıda33 yönetim bölümü/9 müşteri yolu, beş genişlik ve11 dil seçiminin yerel sonuçları [devir kaydında](../docs/native-store-transfer.md). Güncel kopya şu an yereldedir; eski `/test` yayını değiştirilmedi. `--refresh` yalnız hash'i bozulmamış kaynak kopyasını yeniler ve eski sürümü özel yerel arşivde saklar.

15 Kasım son durum:yalnız [sexogate.com/test](https://sexogate.com/test) PHP/SQLite sürümü `d6ae100648e17c0204db628b` ile yayımlandı; ana site değişmedi. Ürün/kategori0, gerçek tahsilat kapalı. Mobilya ve dünya haritası yerine yetişkin metinleri/18+ katmanı uygulanır. Önceki "yerelde/yayımlanmadı" ifadeleri o aşamanın tarihsel kaydıdır; güncel [yayın kanıtı](../docs/native-test-deployment.md) esas alınır.
