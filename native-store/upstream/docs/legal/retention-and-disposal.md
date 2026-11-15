# Kişisel veri saklama ve imha prosedürü

Sürüm: 2026-11-10. İşletme içi başlangıç prosedürüdür. İşletme, envanterdeki her veri faaliyetine gerçek saklama nedeni ve süre atamalıdır. Bu metin bir zamanlayıcı kurmaz veya geçmiş kayıtları silmez. Bütün verilere aynı süre uygulanmaz.

## Roller ve kural

İşletme sahibi veri koruma operasyonundan sorumlu rolü ve yedeğini atar. Muhasebe gerçek satıcının fatura/defter sürelerini, hukuk itiraz/uyuşmazlık korumasını, teknik ekip canlı/yedek kopyaları belirler. İşleme nedeni sona eren ve başka geçerli saklama gerekçesi bulunmayan veriler silinir, yok edilir veya geri döndürülemez biçimde anonimleştirilir. İmha sürecinin ve periyodik işlemlerin kayıtları saklanır. Sicile kayıt/politika istisnası bulunması silme yükümlülüğünü kaldırmaz; periyodik imha aralığı altı ayı geçemez. [KVKK İmha Yönetmeliği](https://www.kvkk.gov.tr/Icerik/5441/KISISEL-VERILERIN-SILINMESI-YOK-EDILMESI-VEYA-ANONIM-HALE-GETIRILMESI-HAKKINDA-YONETMELIK).

## Başlangıç çizelgesi

| Kayıt grubu | Gözlenen sistem davranışı | İşletmenin uygulayacağı kontrol |
|---|---|---|
| Misafir iletişim/adres taslağı | Ödeme başlatılmadan sayfa belleğinde; hesap/adres defteri oluşturmaz. | Kişisel taslağı analitik veya hata günlüğüne eklemeyin. Gönderilmiş destek/teklif/ödeme kaydını bu geçici taslakla karıştırmayın. |
| Üyelik, adres defteri, hesap sepeti/favorisi | Hesap hizmeti için özel depoda; hesap silme yolu bulunur. Bütün kayıtlar için yaşa göre otomatik imha iddiası yoktur. | Hesap kapatma isteğinde ilgili veri gruplarını inceleyin. Hukuken saklanması gereken satış kaydını hesabın silinmesiyle yok etmeyin; üyelik verisinin gereksiz kopyalarını ayırın. |
| Kart siparişi, belge/onay, cayma ve teslimat kanıtı | Değişmez işlem kaydı özel depoda; ödeme iletişim bilgisi şifreli zarfla saklanır. | Mesafeli işlem yükümlülüklerine ilişkin bilgi ve belgelerde en az üç yıllık kayıt şartını ve daha uzun uygulanabilir vergi/ticaret/uyuşmazlık süresini belirleyin. Üç yıl doldu diye bütün faturaları otomatik silmeyin. |
| Stripe ödeme/iade referansı ve güvenlik bildirimi | Siparişin sağlayıcı kimliği, tutarı ve durumu; kart numarası NODENO'ya alınmaz. | Gerekli uyuşmazlık/muhasebe kayıtlarını koruyun; ham sağlayıcı yanıtı veya müşteri kartı içeren destek çıktısı biriktirmeyin. Stripe'ın kendi saklama süreleri sözleşmesinden ayrıca doğrulanır. |
| Destek ve ihracat/ölçülü teklif talebi | Özel işletme deposunda; tümüne otomatik süreli silme uygulanmıyor. | Talep kapanışında ticari/uyuşmazlık gereksinimini inceleyin. Gereksiz serbest metin ve ekleri ayıklayın. Gerçek süreyi amaç ve hukuki dayanakla envantere kaydedin. |
| İzinli analiz ve öneri olayları | Onay 90 gün; olaylar gün bazında tutulur. Eski olayların temizliği yeni olay işlendiğinde yapılır. İzin geri alındığında bağlı olaylar silinir. | 90 günlük hedefi bağımsız periyodik kontrolle denetleyin; hiç yeni olay gelmeyen depoda zamanında imha olduğunu varsaymayın. Sunucu HMAC kimliği kişiselle ilişkilendirilebilir kayıt kabul edilir. |
| Tarayıcı tercih ve sepet kayıtları | Yerel depolama; saklama türüne göre kullanıcı temizleyene veya oturum kapanana kadar kalabilir. | Çerez/depolama politikasını gerçek anahtarlarla eşleştirin. Tarayıcıdaki veriyi sunucunun sildiği söylenmez. |
| Hosting erişim/güvenlik günlükleri, yedekler | Turhost sözleşmesindeki gerçek süre ve erişimler teyit bekliyor. | Sağlayıcıdan etkin süre, yedek rotasyonu, silme ve yurtdışı erişim bilgisini alın; teyit edilmemiş gün sayısı yayımlamayın. |
| Yönetim denetim, izin/ret ve başvuru kayıtları | Yetkili işlem ve yanıt ispatı için gerekir. | Kanuni süreyi ve meşru ihtiyacı ayrı kaydedin. Parola, kurtarma kodu veya anahtarı denetim açıklamasına yazmayın. |

Mesafeli işlem kanıtları için [Yönetmelik m20'deki üç yıl](https://tuketici.ticaret.gov.tr/data/5e819a8e13b876a1b04c7a4a/Mesafeli%20S%C3%B6zle%C5%9Fmeler%20Y%C3%B6netmeli%C4%9Fi.pdf) asgari özel şarttır. PTYS'nin hangi ülke/tescil altında hangi belgeyi tutacağı muhasebe/hukukça kesinleştirilmeden genel bir “tüm veriler 10 yıl” kuralı konulmaz.

## Her imhada uygulanacak adımlar

1. İşlem grubu, tarih aralığı, canlı depolar ve aynı verinin türevlerini seçin. Kanuni saklama, açık şikâyet, chargeback, dava veya inceleme nedeniyle korunması gereken kayıtları işaretleyin. Genel ve süresiz koruma kararı vermeyin; gerekçe ve yeniden inceleme tarihi yazın.
2. Amaç sona ermişse yöntemi belirleyin. Silme, ilgili kullanıcı/işlem erişimlerini kaldırmalı; anonimleştirme kayıtlar başka veriyle birleştirilse dahi kişiyle ilişkilendirilememelidir. Yalnız adı kaldırmak veya kimliği hashlemek her durumda anonimleştirme değildir.
3. Yetkili teknik kişi işlemi önce kontrollü örnek üzerinde doğrular; satış toplamları, zorunlu işlem kanıtı ve hesap bütünlüğünün etkisini kontrol eder. Canlıda geniş kapsamlı komutları incelemesiz çalıştırmaz.
4. Gerekiyorsa veri aktarılmış alıcılara düzeltme/silme talebini iletin ve sonuç kanıtını alın. Sağlayıcının kendi yasal saklama gerekçesi varsa bunu yanıta açıkça yansıtın.
5. Yedekler için derhal seçici silme mümkün değilse erişimi sınırlandırın, rotasyon sonunu kaydedin, geri yüklemede silinen verinin yeniden aktifleşmesini önleyen talep/imha kaydını uygulayın. Süresiz “yedekte kalır” istisnası üretmeyin.
6. İmha tutanağında işlem kimliği, veri grubu/sayısı, tarih aralığı, gerekçe, yöntem, yetkililer, yedek/alıcı durumu ve kontrol sonucunu tutun. Müşteri içeriğini tutanağa kopyalamayın.

Tutanak şablonu: `işlem_id | talep/plan_referansı | başlangıç/bitiş_zamanı | veri_grubu | kapsam/sayı | korunan_kayıt_gerekçesi | yöntem | canlı_kontrol | yedek_rotasyonu | alıcı_teyidi | uygulayan | denetleyen | sonraki_kontrol`. Gerçek tutanaklar ve ekleri özel depoda tutulur. Her periyodik çevrimde gerçekleşmeyen işlem, nedeni ve yeni sorumlusu görünür kalır.
