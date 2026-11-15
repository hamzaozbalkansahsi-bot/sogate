# NODENO sosyal medya motoru

Amaç: bilgisayar ve Codex kapalıyken Turhost üzerinde çalışan, yönetim panelinden izlenen içerik ve gelen kutusu işleyicisi. Viral olma veya arama sırası garantisi verilmez; erişim, izlenme ve dönüşüm yalnız gerçek kaynaklardan raporlanır.

## Tasarım

Mevcut PHP, SQLite/WAL ve MFA/RBAC yönetimi korunur. NODENO Sans, lacivert `#172D38`, fildişi `#F5F2E9`, açık yeşil `#D8EC81`, gri `#536770` kullanılır. Panelin ana öğesi ürün görselleriyle haftalık yayın kuyruğudur; kanal bağlantıları, neden beklediği, önizleme ve son işlem görünürdür. Boş analitikler sıfır başarı izlenimi vermek yerine “Veri bekleniyor” gösterir.

## İş sırası

- [x] Resmî platform belgeleri, bağlantı ve lisans sınırları.
- [x] Özel depolamada kalıcı içerik, iş, trend, ölçüm ve gelen kutusu tabloları; yönetici izinleri, sürüm kontrolü ve şifreli servis anahtarları.
- [x] Aynı işi iki kez yayınlamayan, kilitli sunucu işçisi; belirsiz uzak sonuçlarda kör yeniden gönderim yerine uzlaştırma.
- [x] Gerçek katalogla platforma özel metin/görsel/video planı; günlük sınırlar, ilgililik, tekrar kontrolü ve telifli müzik engeli.
- [x] Yayın/analiz/gelen kutusu için Ayrshare adaptörü ve doğrulanmış kanal yetenekleri. Bağlantı olmadan “aktif” gösterilmez. Ücretli servis üyeliği satın alınmaz.
- [x] İsteğe bağlı OpenAI metin üretimi; bütçe ve anahtar olmadan ücretli çağrı yapılmaz. Platform kuralları ve sipariş işlemleri için insan devri.
- [x] Yönetimden içerik üretme/düzenleme/zamanlama/durdurma, trend ve müzik kaydı, yanıt taslağı/iletim, gerçek ölçümler.
- [x] Davranış ve güvenlik testleri, masaüstü/mobil kabulü, işletim rehberi.
- [x] Mevcut canlı sürümün ticari verilerini koruyan yayın; yalnız bu motorun sunucu zamanlayıcısı; canlı kalp atışı ve kabul kanıtları.

## İşletme sınırları

Kullanıcı tam otonom içerik ve gelen yorum/mesaj yanıtlarını istedi. Başkalarına ilk mesaj gönderilmez, takip/etkileşim botu yapılmaz. X AI yanıtları platformun yazılı izni olmadan açılamaz. Ticari müzik lisansı ülke/platform/süre bazında saklanır; popüler şarkı otomatik olarak lisanslı kabul edilmez. Kuruluş belgeleri, ödeme, iade, kişisel sipariş ve hukuki şikâyetler otomatik karara bağlanmaz.

Üretim ve platform API anahtarları henüz sağlanmadı. Kullanıcı önce ücretsiz altyapının tamamlanmasını istedi; ücretli üretim ve abonelik satın alma kapalıdır. Sonuç raporunda çalışan yerel/sunucu bileşenleri ile dış hesap onayı gerektiren adımlar ayrı belirtilir.

## Canlı kabul — 12 Kasım 2026

Ücretsiz çekirdek Turhost üzerinde yayımlandı. Dört alan adı aynı sürümle 3.602 ürün ve mevcut ödeme durumunu koruyor. Dakikalık özel zamanlayıcı kuruldu; ilk gerçek çalışmada 49 plan, 3 görsel, sıfır dış yayın ve sıfır ücretli rezerv doğrulandı. Toplam 16 davranış/paketleme testi geçti. Gerçek hesaplara yayın, mesaj/yorum API izinleri ve ücretli AI/video üretimi bu aşamada açılmadı.
