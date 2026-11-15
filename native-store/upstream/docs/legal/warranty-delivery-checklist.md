# Garanti belgesi ve teslim kaydı kontrolü

Sürüm: 2026-11-10. Her ürün/model için gerçek üretici/ithalatçı belgesi ve mevzuattaki ürün sınıfı incelenir. Garanti belgesi düzenleme ve tüketiciye verme, satış sözleşmesi ve faturadan ayrı iştir. Kapsamdaki malların belgesini üretici/ithalatçı düzenler; tüketiciye verme ve bunun ispatı satıcıdadır. Satış faturası garanti belgesi yerine geçmez. [Ticaret Bakanlığı garanti bilgisi](https://tuketici.ticaret.gov.tr/yayinlar/tuketici-bilgi-rehberi/garanti-belgeleri-hakkinda-bilgilendirme).

## Tedarik aşaması

- Gerçek üretici ve varsa ithalatçının unvan, adres, telefon ve yetkili belge kaynağını alın. NODENO marka varlığı veya görseldeki logo, üreticinin hukuki kimliğini tahmin ederek değiştirme gerekçesi değildir.
- Ürün cinsi/modeli, seri numarası varsa seri numarası ve teknik katalogla belgeyi eşleştirin. Belge başka ürüne aitse kullanmayın.
- Garanti süresi, başlangıcı ve azami tamir süresini ürünün gerçek sınıfı ve güncel mevzuatla doğrulayın. Bütün kapı/kapak/mobilyaya tek süre veya tek servis süresi atamayın. İlgili listedeki yasal asgari süreden az taahhüt kullanmayın.
- Gerçek yetkili servis/üretici başvuru yolunu, gerekiyorsa satış sonrası hizmet yeterliliği bilgisini doğrulayın. Sahte servis ağı, sertifika veya imza/kaşe üretmeyin. Güvenlik ve bakım kılavuzu ürünle eşleşsin.

## Siparişe bağlama ve tüketiciye teslim

1. Gerçek sipariş/fatura numarası, fatura tarihi, ürün/seçenek/adet ve varsa seri bilgilerini eşleştirin. Fatura henüz yoksa belgeyi kesinleşmiş garanti belgesi gibi göndermeyin.
2. Teslimin gerçek tarih ve yerini kaydedin; garanti başlangıcını sipariş veya ödeme tarihiyle gelişigüzel değiştirmeyin. Birden fazla koli/parça için eksik teslim kaydını ayrı tutun.
3. Üretici/ithalatçı belgesindeki bütün parçalar kapsamı, ücretsiz onarım ve kanuni seçimlik hakları koruyun. Kullanım hatası değerlendirmesini gerekçesiz veya yalnız satıcının talimatıyla otomatik redde dönüştürmeyin.
4. Belgeyi ve ilgili kılavuzu yazılı veya kalıcı ortamda müşteriye verin; kağıt/elektronik teslim, sürüm ve teslim kanıtını özel işlem kaydına ekleyin. Genel politika bağlantısını ürüne özgü belge yerine koymayın.
5. Müşteriye şikâyet/başvuru kanalını gösterin. Ayıplı mal haklarını yalnız “servis kabul ederse” koşuluna bağlamayın; iade/cayma işini garanti onarımıyla karıştırmayın.

[İç garanti şablonu](warranty-template.html), gerçek düzenleyici, ürün ve zorunlu alanlar doldurulup yetkili kişi tarafından doğrulanmadıkça **düzenlenmiş garanti belgesi değildir**. İmzacı ve imza/kaşe usulünü gerçek yetkili belirler; boş alana otomatik şirket imzası eklenmez. Belge hazırlanırken ilgili mevzuat ve üretici belgesiyle çelişki varsa işletme/hukuk sorumlusu çözmeden kesin belge teslimi yapılmaz.

İç kontrol kaydı: `sipariş_ref | ürün/model | üretici/ithalatçı_belge_ref | ürün_sınıfı_dayanağı | süre_tamir_teyidi | fatura_ref | gerçek_teslim_tarihi | kılavuz_sürümü | belge_teslim_yöntemi/zamanı | müşteri_alındı_ref | kontrol_eden`. Bu başlıklar gerçek müşteri verileriyle Git dışında kullanılır.
