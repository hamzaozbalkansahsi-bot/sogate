# KVKK ilgili kişi başvurusu iş akışı

Sürüm: 2026-11-10. Müşteri, ziyaretçi, teklif sahibi veya hesabını kapatan kişinin kişisel veri talebini karşılamak için kullanılır. Operasyon sorumlusu ve yedeği işletme tarafından atanır. [Takip CSV'sinin](data-subject-request-tracker.csv) gerçek vaka kopyası kişisel verilerle birlikte Git/web kökü dışında tutulur.

## Kabul ve süre

İlgili kişi, yazılı/imzalı başvuru, güvenli elektronik imza, mobil imza, gerçekten mevcut KEP kanalı, daha önce sisteme bildirdiği kayıtlı e-posta veya başvuruya yönelik uygulamayla talebini iletebilir. Özel bir form kullanılması şart koşulmaz. Henüz açılmamış KEP adresi yayımlanmaz. Başvurunun gerektirdiği kimlik ve iletişim bilgileri alınır; kimlik doğrulamada gereksiz belge/kart fotoğrafı istenmez. Yetkisiz kişiye hesap verisi verilmez. [KVKK başvuru usulleri duyurusu](https://www.kvkk.gov.tr/Icerik/6938/Kurumumuza-Yapilan-Sikayetlerin-Usul-Sartlarina-Iliskin-Kamuoyu-Duyurusu).

Talep mümkün olan en kısa sürede, en geç otuz gün içinde sonuçlandırılır. Genel kural ücretsiz yanıttır; istisnai maliyet ancak mevzuattaki tarife ve koşullarla ele alınır. Sırf “kimlik teyidi bekleniyor” veya “tedarikçi cevaplamadı” diye süre kendiliğinden uzatılmaz. Gerekli açıklama isteme, alınan/gönderilen yanıtlar ve süre değerlendirmesi kayda geçirilir. [KVKK uygulama rehberi, başvuru bölümü](https://www.kvkk.gov.tr/SharedFolderServer/CMSFiles/a3b2290a-a61b-4faa-b6dc-5202630a0fd3.pdf).

## Personelin uygulayacağı işlem

1. **Alındı kaydı:** Talebin özgün metnini, geldiği kanalı ve ulaşma tarih/saatini özel dosyaya alın; `KVK-YYYY-NNNN` biçiminde kişisel veri içermeyen referans üretin. Son yanıt gününü kaydedin ve sorumluya görev atayın. Kimlik belgesi numarasını takip tablosuna koymayın.
2. **Kimlik/yetki:** Hesaba kayıtlı e-posta ve mevcut doğrulama yöntemini kullanın. Kimliği veya vekâlet yetkisi belirsizse yalnız gerekli ek bilgiyi güvenli kanaldan isteyin. Bir kişinin sistemde olup olmadığını doğrulanmamış üçüncü kişiye açıklamayın. İmzalı başvuru ve yabancı başvuru sahibinin zorunlu bilgilerini usulüne göre tamamlayın.
3. **Kapsam:** Talebin öğrenme, erişim, düzeltme, silme, alıcı bilgisi, üçüncü kişilere bildirim, münhasıran otomatik olumsuz sonuca itiraz veya zarar talebinden hangilerini içerdiğini belirleyin. Destek şikâyeti ile veri başvurusu aynı mesajdaysa iki işi de izleyin.
4. **Veriyi bulma:** Üyelik/adres, sepet/favori, teklif/destek, ödeme/sipariş, izinli analiz ve ilgili günlüklerde gerçekten işlenen veriyi arayın. Başka alıcıya aktarıldıysa sağlayıcı kayıt sorumlusuyla işlemi başlatın. Ayrı bir kişinin verisini erişim paketinden çıkarın; parola hashini, oturum/anahtar sırlarını paylaşmayın.
5. **Hukuki değerlendirme:** Saklama gerekçesi kalmamış veriyi imha prosedürüne alın. Kanuni saklama veya açık uyuşmazlık gerektiren kısmı gerekçesiyle ayırın. Hesap kapatma tüm satış/fatura kanıtının silindiği anlamına gelmez. Veri yoksa neyin araştırıldığını belirterek doğru yanıt verin; kayıt oluşturup “bulduk” demeyin.
6. **Uygulama ve kanıt:** Düzeltme/silme işleminin sonucu ve gerekiyorsa alıcılara bildirimi kaydedin. Kısıtlanacak erişimleri belirleyin. Yedeklerde yeniden etkinleşme riskini imha prosedürüyle yönetin. Otomatik karar itirazında gerçek insan incelemesi yapın; analitik rızasını geri almak alışverişi engellememelidir.
7. **Yanıt ve teslim:** Sonucu, kabul edilen/reddedilen kısımları ve somut gerekçeyi anlaşılır biçimde yazın. Yasal başvuru/şikâyet yolunu açıklayın. Doğrulanmış kanala güvenli şekilde gönderin ve alındı/gönderim kanıtını saklayın. Yanıtı yalnız iç kayda eklemek müşteriye bildirim değildir. [KVKK yanıt bildirim usulü](https://www.kvkk.gov.tr/Icerik/9024/ilgili-kisilerin-basvurularina-verilecek-cevabin-bildirim-usulune-iliskin-kamuoyu-duyurusu).

## Yanıt şablonu

> Başvuru referansı: [referans]  
> Veri sorumlusu: PTYS Technologies L.L.C. / NODENO  
> Başvurunun ulaşma tarihi ve kanalı: [gerçek bilgi]  
> Talebiniz: [talepleri ayrı ayrı özetleyin]  
> İncelenen kayıt grupları: [gerçek kapsam]  
> Sonuç ve gerçekleştirilen işlemler: [her talep için kabul/ret ve gerekçe]  
> Saklanması gereken kısım varsa kapsam, dayanak ve süre: [gerçek bilgi]  
> Düzeltme/silmenin alıcılara bildirimi ve yedek durumu: [gerçek sonuç]  
> Ekler ve güvenli teslim yöntemi: [bilgi]  
> Yetkili yanıtlayan ve tarih: [bilgi]  
> İtiraz/başvuru yolları: [olaya uygulanabilir kanuni yollar]

Tebliğde gereken başvuru/yanıt kimlik alanları yalnız özel vaka dosyasında bulunur; örnek, depo veya halka açık raporda gerçek TCKN/pasaport/adres gösterilmez. Kayıt tablosundaki son tarih bir hatırlatmadır; görev/süre takibi ve müşteriye gönderim bu belge tarafından otomatik yapılmaz.
