# Kişisel veri başvuruları

Yerel geliştirme kapsamı; canlı hukuk onayı değildir. Veri sorumlusu, hukuki satıcı ve geliştirme kredisi ayrı kayıtlardır.

## Müşteri

`/veri-basvurusu` ve `/en/veri-basvurusu` üzerinden üyelik veya pazarlama izni vermeden başvuru oluşturulur. E-posta, konu ve talebi açıklayan metin yeterlidir; ülke biliniyorsa eklenir. Kimlik belgesi, kart veya gereksiz hassas bilgi yüklenmez. İletişim formundaki kişisel veri konusu da aynı kayıt sistemine girer.

Başvuru sonunda verilen özel bağlantı güvenli saklanmalıdır. Token yalnız hash olarak kaydedilir. Bağlantı yalnız referans, durum ve tarihleri gösterir. Başka hesaba giriş yapılması ayrıntıları açmaz. Başvuru hesabına bağlıysa sahibi Hesap → Veri başvuruları alanından kendi talep metni ve yanıtını okuyabilir. Misafir ayrıntıları yalnız ayrıca doğrulanmış güvenli kanaldan teslim edilir.

Sayfalar no-store, API private/no-store ve ikisi de noindex/no-follow yanıtı verir; referrer gönderilmez. Bu başlıklar sahiplik denetiminin yerine geçmez.

## Yönetim

Yönetici veya müşteri hizmetleri rolü, MFA ile `/yonetim/privacy` kuyruğunu açabilir. Depo, katalog, pazarlama ve finans başvuru içeriğine erişemez. Arama/sayfalama sunucudadır.

1. Ülke ve uygulanacak kuralı inceleyin. Bilinmeyen ülke veya eksik kural başvuruyu düşürmez; son yanıt zamanı inceleme bekler ve kuyruğun başında görünür.
2. Kimliği güvenli kanaldan doğrulayın ve asgari kanıt referansını yazın. Hesap eşleştirme seçeneği yalnız e-postası doğrulanmış eşleşen hesapta çalışır. Kimlik belgesini serbest metne kopyalamayın.
3. Onaylı süre/saklama kuralı varsa değerlendirmeye alın.
4. Erişim, düzeltme, silme, anonimleştirme veya ret değerlendirmesini ilgili sistemlerde yetkili süreçle tamamlayın. Mali kayıtlar ve yasal saklama ayrıca değerlendirilir.
5. Başvuranın dilinde yanıtı ve güvenli teslim/dış işlem referansını kaydedin. Kısmi yerine getirme ve gerekçeli ret ayrı sonuçlardır. Kimlik doğrulanamıyorsa kişisel veri açıklamadan ayrı gerekçeli yanıt geçişi kullanılır.

Bu sürüm **otomatik veri silme, finansal kaydı yok etme veya bütün sağlayıcılardan veri taşınabilirliği arşivi üretme motoru değildir**. Yönetici kaydı, tamamlanan dış işlemin izlenebilir kanıtıdır. İşlemi gerçekte yapmadan “yerine getirildi” seçilmemelidir. Bu kapsamın ötesindeki veri sınıfı bazlı otomasyon tamamlanmadı.

## Kimlik ve süre yapılandırması

Yalnız yönetici, MFA ve yeniden parola doğrulamasıyla yeni sürüm kaydeder. Gerçek hukuki unvan/adres/başvuru e-postası ile belge inceleme referansı girilir. Geliştirici kredisinden bu alanlar doldurulmaz. Yeni veri sorumlusu onayı eski ülke politikalarını yayından kaldırır; eski başvurular bağlı oldukları sürümü korur.

Politika alanları: `country`, `unit` (`days`/`months`), `count`, `timeZone`, HTTPS `source`, hukuk inceleme `evidence`, `retentionNote`, `approve`. Ülke başına onaylı sürüm, ilk alım zamanına göre takvim günü/ayı hesaplar; ay sonu ve saat dilimi PostgreSQL ile çözülür. Ülke değişimi veya ilk kuralın sonradan onayı mevcut daha erken son tarihi uzatmaz. Yeni kurallar eski başvurunun sürümünü sessizce değiştirmez. Otomatik yasal süre/uzatma hakkı varsayılmaz; belirli süreyi hukuk incelemesi belirler.

Development/test kimlik ve politikaları fixture olarak işaretlenir; production kapısında kullanılamaz. Canlı checkout, gerçek onaylı veri sorumlusu ve satışa açık her gerçek ülke için onaylı yanıt/saklama politikası olmadan açılmaz. Gizlilik/başvuru hukuk metni aktivasyonu da gerçek veri sorumlusu gerektirir. Hiçbir gerçek kimlik/kural bu görevde doldurulmadı.

## Bildirim ve veri minimizasyonu

Alındı/yanıtlandı bildirimi kalıcı `email.privacy` işi olarak kuyruklanır. E-posta alıcısı ve özel bağlantı AES-256-GCM ile şifreli payload içindedir. `BETTER_AUTH_SECRET` en az 32 karakter olmalıdır; kaybolması bekleyen şifreli işleri okunamaz yapar, anahtar devri planlanmalıdır. SMTP yapılandırılmadığından gerçek gönderim doğrulanmadı. Konu satırı genel kalır; talep metni, ürün veya kimlik belgesi içermez. Misafirin sonraki durum bildiriminde yeni açık token üretilmez; ilk özel bağlantısı kullanılır.

Audit kaydı başvuru ID, eylem ve kanıt referansının hash'ini saklar; e-posta/talep metni/token içermez. Kanıt referansının kendisi sadece yetkili başvuru ayrıntısındadır. Ağ kotası ayrı HMAC anahtarı kullanır; düz IP saklanmaz. Reverse proxy güven sınırı eksikse production başvurusu sessizce korumasız açılmaz.

## Doğrulama

`npx tsx --env-file=.env.local scripts/privacy-integration.ts`: ayrı geçici yerel veritabanında **13/13 PASS**. Sahiplik/token alan sınırı, şifreli outbox, rol/MFA, ay sonu, sürüm koruma, ülke geçişi, gerçek eşzamanlı onay/alım kilidi, kimlik reddi, test/production ayrımı, iletişim yönlendirmesi ve canlı onay kapıları ile boş ileri sayfada toplamın korunması sınandı. UI, SMTP teslimi, gerçek hukuk süreci ve bütün sistemlerde silme/aktarılma bu DB sonucu ile tamamlandı sayılmaz; güncel toplu sonuç `docs/test-evidence.md` içinde tutulur.
