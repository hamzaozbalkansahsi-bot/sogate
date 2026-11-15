# Tedarikçi ve yurt dışına aktarım hazırlık listesi

Sürüm: 2026-11-10. [Tedarikçi kaydı](supplier-transfer-register.csv), mevcut ve planlanan akışların ayrı takibidir. Boş imza/bildirim sütunları işlem yapılmadığını veya kanıtın alınmadığını gösterir. Bu dosya taraflarca imzalanmış standart sözleşme, Kurul izni veya Kuruma bildirim değildir.

## Her sağlayıcı için tamamlayın

1. **Akışı çıkarın.** Gerçek sözleşme tarafı, sunucu/veri merkezi, dışarıdan destek erişimi, bağlı şirket/alt işleyen ülkeleri ve veri kategorilerini listeleyin. Türkiye'de sunucu bulunması tek başına yabancı erişimin olmadığını kanıtlamaz. PTYS'nin yabancı şirket olmasını veri aktarım değerlendirmesini atlamak için kullanmayın.
2. **Rolü belirleyin.** Kimin hangi amaç ve araca karar verdiğini yazın. Bir sağlayıcı bazı amaçlarda veri işleyen, bazı amaçlarda ayrı veri sorumlusu olabilir. Stripe'ın güncel [DPA rol ve aktarım hükümleri](https://stripe.com/legal/dpa) bunu açıklar. NODENO'nun API ile gönderdiği veri ile müşterinin Stripe ekranına doğrudan girdiği veriyi ayırın.
3. **İşleme dayanağını belirleyin.** Önce faaliyete uygun KVKK m5/m6 şartını, sonra ayrıca m9 aktarım yolunu değerlendirin. Bir satış sözleşmesinin bulunması düzenli yabancı hizmet aktarımında m9 değerlendirmesini gereksiz kılmaz. Genel “her yere aktarıma rıza” kutusu kurmayın.
4. **Gerçek aktarım yolunu belgeleyin.** Uygulanabilir yeterlilik kararı varsa kapsamını doğrulayın; aksi durumda gerçek uygun güvenceyi belirleyin. Arızi istisnalar yalnız düzenli/sürekli olmayan aktarımlar için dar kapsamlıdır. Sürekli ödeme veya bulut kullanımını varsayılan arızi aktarım saymayın. [KVKK aktarım çerçevesi](https://www.kvkk.gov.tr/Icerik/2053/Yurtdisina-Aktarim).
5. **Tedarikçi yükümlülüklerini tamamlayın.** Veri kapsamı, amaç, gizlilik, yetkiler, alt işleyen, güvenlik, ihlal bildirimi, başvuru desteği, silme/iade ve denetim koşullarını gerçek sözleşmeyle eşleştirin. Genel AB standart maddesi veya İngilizce DPA'nın Türk standardını otomatik tamamladığını söylemeyin.
6. **Aydınlatmayı eşleştirin.** Veri alınırken bildirilen alıcı grubu ve amaç, gerçek akışla aynı olmalıdır. Hizmete henüz geçilmemişse müşteri verisi gönderildiği veya hukuki işlemin bitirildiği iddia edilmez. Yeni amaç/alıcıda bildirimi ve gerekli kontrolleri önce tamamlayın.
7. **Kanıtı saklayın.** Onaylayan rol, gerçek imza tarihleri, sözleşme sürümü, bildirim alındısı, yeniden inceleme tarihi ve sağlayıcı değişikliklerini özel depoda tutun. Kişisel müşteri eklerini kayıt CSV'sine koymayın.

## Türk standart sözleşmesi yolu seçildiyse

- Kurumun [resmî dört standart sözleşme metninden](https://www.kvkk.gov.tr/Icerik/7938/Standart-Sozlesmeler-ve-Baglayici-Sirket-Kurallarina-Iliskin-Dokumanlar-Hakkinda-Kamuoyu-Duyurusu) gerçek veri aktaran/alıcı rollerine uyan modülü seçin. Seçimlik maddeler dışındaki zorunlu metni kısaltmayın veya değiştirmeyin.
- Tarafların tam unvan/adreslerini ve yetkili imzacılarını gerçek belgelerle eşleştirin. Eklerde gerçek kişiler/veri kategorileri, amaç, sıklık, süre, ülkeler, alıcı/alt işleyen ve teknik/idari tedbirler yer alsın. Bilinmeyen ülke veya tedbiri tamamlanmış gibi yazmayın.
- Her iki tarafın yetkili imzasını ve imza tarihini alın. Geçmiş aktarımı düzeltiyormuş gibi geriye etkili tarih üretmeyin. Yabancı tarafın yetki belgeleri/tercüme usulünü gerçek dosyayla kontrol edin.
- İmzalar tamamlanınca **beş iş günü** bildirim takvimini açın. Fizikî/KEP veya resmî Standart Sözleşme Bildirim Modülü yolu için yetkili kişiyi ve yedeğini atayın; gerçek alındıyı dosyalayın. İmzalı metnin varlığıyla bildirim yapılmasını ayrı sütunlarda izleyin. [KVKK standart sözleşme usul duyurusu](https://www.kvkk.gov.tr/Icerik/8170/Yurt-Disina-Kisisel-Veri-Aktariminda-Kullanilacak-Standart-Sozlesmelerde-Dikkat-Edilmesi-Gereken-Hususlara-Iliskin-Kamuoyu-Duyurusu).
- Taraf/akış değişikliği, sona erme ve sonraki aktarımları hukuk sorumlusuyla izleyin. Hazırlanmış taslağı müşteriye “Kurul onaylı firmamız” ifadesiyle sunmayın.

## Diğer açık işler

Yabancı veri sorumlusu temsilcisi/VERBİS gerçek atama ve kayıt işidir. Türkiye çalışan/ciro muafiyetini PTYS'ye otomatik taşımayın; [Ekim 2025 VERBİS rehberindeki soru 46 ve 51](https://www.kvkk.gov.tr/Icerik/5384/SORULARLA-VERBIS) üzerinden değerlendirin. Temsilciye yalnız form doldurmakla görev verilmiş sayılmaz.

Henüz bağlı olmayan reklam, SMS, e-posta, sosyal giriş veya fatura hizmetinde bu dosya otomatik aktivasyon yapmaz. Pazarlamada ayrıca kanal onayı, ret ve gerçek İYS kayıt yolu; faturada gerçek satıcının mükellefiyet ve belge düzeni tamamlanmalıdır. [Uyum kaydı](compliance-register.md) açık işleri birlikte izler.
