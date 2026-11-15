# NODENO belge merkezi ve onay kayıtları

Belge merkezi `/legal?lang=tr` adresindedir. `lang=en`, `lang=ru` ve `lang=ar` aynı kapsamın çevirileridir; Arapça sağdan sola gösterilir. Alt menü, üyelik, ödeme, destek ve teklif formlarından ilgili aydınlatmaya ulaşılır. KVKK aydınlatması bir satış sözleşmesi veya genel açık rıza değildir.

| Adres | Belge |
|---|---|
| `/legal/pre-information` | Ön bilgilendirme |
| `/legal/sales` | Mesafeli satış sözleşmesi |
| `/legal/returns` | İptal, cayma, iade ve isteğe bağlı cayma bildirimi |
| `/legal/seller` | Gerçek satıcı ve iletişim |
| `/legal/kvkk` | Kişisel veriler aydınlatması |
| `/legal/privacy` | Gizlilik politikası |
| `/legal/cookies` | Çerez/depolama politikası ve tercihler |
| `/legal/membership` | Üyelik ve kullanım koşulları |
| `/legal/data-request` | İlgili kişi başvuru formu ve yolları |
| `/legal/wholesale` | Uluslararası toptan teklif koşulları |

Her sayfa yazdırılabilir ve HTML olarak indirilebilir. İndirilen belge stilini içerir ve betik çalıştırmaz. Dört dilde kaynak `data/legal/site-documents.*.json`, sürüm `2026-11-10.3`. Satış/iade metni özel ödeme ayarındaki aynı satıcı ve sürümden gelir. Metin düzenlemesinde dört dil tamamlanır ve sürüm artırılır.

## Üyelik

Üyelik kutusu yalnız üyelik sözleşmesini kabul eder; KVKK bağlantısı ayrıdır. Analiz veya pazarlama izni hesap açmanın şartı değildir. Ekran, sözleşmenin sürüm/özetini sunucudan alır. Eksik kabul veya eski/değiştirilmiş özetle kayıt reddedilir. Kullanıcı ile tam sözleşme anlık görüntüsü, dil, sürüm, özet ve sunucu zamanı tek işlemde kaydedilir. Yazma başarısızsa kullanıcı da oluşturulmaz. Bu kayıt pazarlama onayı değildir.

## Siparişin kalıcı kopyası

Gerçek ürün, renk/ölçü/yön ve seçili aksesuarlar, adet/takım, alıcı adresleri, net/KDV/toplam, satıcı ve kabul edilen satış/iade metni değişmez HTML kopyaya alınır. Kopya özel depoda şifreli tutulur ve bütünlük özeti kontrol edilir. Fatura, garanti veya tahsilat onayı değildir.

Güncel ödeme ekranı kopyayı indirir; müşteri saklayıp **Kart ekranına geç** ile Stripe'a ilerler. Belge akışı sürümünü göndermeyen eski açık ekranlar sipariş/Stripe oturumu oluşturulmadan reddedilir. Dönüş ekranı aynı kopyayı verir. Farklı misafir oturumu dosyayı indiremez; aynı misafir oturumu veya doğrulanmış hesap sahibi gerekir. Oturumunu kaybeden misafire müşteri hizmetleri orantılı doğrulamadan sonra yardımcı olur.

`served_at` dosyanın sunucudan sunulduğunu kaydeder; gerçekten saklama veya e-posta tesliminin ispatı değildir. Otomatik işlem e-postası bağlı değildir. İşletme gerçek kalıcı belge teslimini izler. Sonraki fiyat/metin değişikliği eski sipariş arşivini değiştirmez.

## Tercihler ve işletme işlemleri

İzin/ret 90 gündür; eski tarihsiz kabul yeniden sorulur. İzin öncesi otomatik son arama/ürün geçmişi kalıcı tutulmaz. Ret bunları temizler; istenen sepet/favori/dil işlevleri korunur. Analiz temizliği mağaza istekleri işlenirken çalışır; bütün yedeklerde tam 90. gün silme garantisi verilmez.

[Uyum takip kaydı](legal/compliance-register.md), veri envanteri, saklama, başvuru, ihlal ve aktarım prosedürleri ile garanti/kullanım belgesi teslim listeleri `docs/legal/` altındadır. Bunlar resmî başvuru veya imza yerine geçmez. PTYS Türkiye mükellefiyet/fatura/kayıt yolu, yabancı veri sorumlusu temsilcisi/VERBİS, gerçek aktarım güvenceleri, gerekiyorsa ETBİS ve pazarlama öncesi İYS ayrıca tamamlanır. Gerçek üretici/ithalatçı garanti ve Türkçe kullanım/montaj belgeleri tedarik edilir; düzenlenmemiş garanti şablonu müşteriye verilmez.

Resmî araştırma ve teknik/canlı kabul kanıtları `artifacts/legal-20261110` altındadır. Gerçek müşteri kayıtları bu klasöre veya Git'e kopyalanmaz.
