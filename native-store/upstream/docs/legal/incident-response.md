# Kişisel veri ihlali müdahale planı

Sürüm: 2026-11-10. Bir müşterinin verisine yetkisiz erişim, yanlış kişiye belge gönderimi, kayıp cihaz/yedek, sızmış sır veya kişisel verilerin hukuka aykırı elde edilmesi belirtisinde bu plan açılır. Genel servis kesintisi otomatik olarak kişisel veri ihlali diye ilan edilmez; olayın gerçek etkisi araştırılır.

## Önceden atanacak roller

İşletme sahibi, olay koordinatörü ve yedeğini; hosting/teknik müdahale yetkilisini; veri koruma/hukuk değerlendirmesini; müşteri iletişimini belirler. Turhost, ödeme sağlayıcısı ve diğer gerçek sağlayıcılardaki güvenlik başvuru kanalları özel iletişim çizelgesine kaydedilir. Parola, API anahtarı, müşteri listesi veya kişisel kimlik belgesi bu plana eklenmez.

## Öğrenme anı ve bildirim

Kanuni olmayan yollarla kişisel verilerin başkalarınca elde edildiğinin öğrenilmesinde Kurula bildirim gecikmeksizin, öğrenmeden itibaren en geç **72 saat** içinde yapılır. Etkilenen kişiler belirlendikten sonra kendilerine makul en kısa sürede uygun yoldan bildirim yapılır. Bütün bilgi tamamlanmadı diye ilk bildirim geciktirilmez; eksikler takip bilgisiyle tamamlanır. Gecikme varsa gerçek nedeni kaydedilir. [KVKK 24.01.2019 tarihli 2019/10 kararı](https://www.kvkk.gov.tr/Icerik/5362/Veri-Ihlali-Bildirimi).

Saat hesabında takvim saati kullanın; hafta sonu veya mesai bitimi nedeniyle 72 saati iş gününe çevirmeyin. `tespit/öğrenme_zamanı`, saat dilimi ve `72_saat_sonu` ayrı yazılır. Yabancı veri sorumlusu yapısındaki temsilci/ilgili yetkili bildirim görevini üstlenir; atamanın belirsizliği olayı sahipsiz bırakmaz. Başka ülke bildirimi gerekiyorsa kendi süresi ayrıca değerlendirilir.

## İlk müdahale

1. Olay kimliği üretin ve öğrenme saatini koruyun. Uyarının kaynağını, etkilenen sistemleri ve ilk bulguyu kaydedin. Kimlerin bildiğini ve hangi işlemi yaptığını saatli çizelgeye yazın.
2. Yetkisiz erişimi sınırlayın: ilgili oturum/erişimi kapatma, sızdığı doğrulanan sırları güvenli döndürme veya etkilenen erişim yolunu geçici sınırlama kararını yetkili teknik kişi uygular. Tüm mağazayı veya veritabanını gerekçesiz silmeyin. Kişisel veriyi veya anahtarı hata ekranında yayımlamayın.
3. Delili koruyun: zaman, dosya/olay kimliği, erişim kaydı ve ilgili yapılandırmanın güvenli kopyasını, erişimi kısıtlı olay klasörüne alın. Hash ve teslim zinciri kullanın. Delil toplarken kapsam dışı müşteri verisini çoğaltmayın.
4. Sağlayıcıyla gerçek güvenlik kanalı üzerinden iletişime geçin. NODENO tarafından bildirim yapıldı mı, sağlayıcı kendi rolünde hangi işlemleri yaptı, hangi veri/ülke/alt sağlayıcı etkilendi sorularını yazılı sorun. Tedarikçinin cevabını beklemek kendi bildirim süresini durdurmaz.

## Etki ve karar kaydı

Olay dosyasında veri türü, ilgili kişi grubu, yaklaşık kişi/kayıt sayısı, şifreleme/anahtarın etkilenip etkilenmediği, yetkisiz alıcı, erişim süresi, olası sonuçlar ve alınan tedbirler değerlendirilir. “Şifreliydi” sonucunu anahtarın aynı olayda erişilebilir olup olmadığını incelemeden rahatlatıcı gerekçe yapmayın. Özel nitelikli veri veya ödeme/kart bilgisi varsa gerçek kapsamını ayrı belirleyin; NODENO'nun kart tutmadığı genel kuralını vaka incelemesi yerine kullanmayın.

Kurula bildirim ve ilgili kişi iletişimi yetkili işletme tarafından resmî kanaldan yapılır. Sistem bu dosya nedeniyle otomatik bildirim göndermez. Başvuru alındısı, gönderilen metnin sürümü ve tarih/saat özel dosyada saklanır. Bildirim yapılmamasına karar veriliyorsa olgular, gerekçe, değerlendiren ve yeniden inceleme koşulu yazılır.

## İlgili kişiye iletişim için içerik listesi

Gerçek olayı ve öğrenilme zamanını anlaşılır anlatın; etkilenen veri kategorilerini, muhtemel etkileri, alınan tedbirleri, kişinin yapabileceği işlemleri ve erişilebilir irtibatı belirtin. Kesinleşmeyen kişi sayısını kesin sayı gibi vermeyin. Başka müşterinin verisini veya yeni bir güvenlik açığının kullanım ayrıntısını duyuruya koymayın. Müşteriden parola/kart kodu istemeyin.

## Kurtarma ve kapanış

Temizliği doğruladıktan sonra gerekli sistemleri geri açın; sipariş/iade durumlarını ve kayıt bütünlüğünü uzlaştırın. Silinmiş veya kapatılmış verilerin yedekten tekrar etkinleşmesini önleyin. Kök neden, uygulanan düzeltme, tekrar kontrolü ve sorumluyu belirleyin. Sağlayıcı sözleşmesi/tedbir/aydınlatma gerekiyorsa güncelleyin; bildirilen olgular değiştiğinde takip bildirimi gereğini değerlendirin.

Olay takip başlığı: `olay_id | öğrenme_zamanı/saat_dilimi | 72_saat_sonu | koordinatör | kapsam | delil_referansı | sınırlama | Kurul_bildirimi/alındı | kişi_bildirimi | tedarikçi_talebi | kalan_eksik | kurtarma_kontrolü | kök_neden | kapanış_onayı`. İlk tatbikatta gerçek müşteri verisi veya gerçek dışı Kurul bildirimi kullanılmaz.
