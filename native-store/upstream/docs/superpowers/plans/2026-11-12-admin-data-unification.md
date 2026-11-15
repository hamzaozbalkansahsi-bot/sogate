# Yönetim ekranlarını mağaza verisiyle birleştirme

İlk kullanıcı talebi: ürün editöründe ad/açıklama/SEO/fiyat alanlarının boş gelmesi. Ek talepler: firma ekranında `default` başlığı; ülkeler, öneri ayarları, koleksiyonlar ve toptan kayıtların boş olması; gelişmiş gerçek analiz; ücretli Ayrshare yerine doğrudan resmî sosyal API bağlantıları.

- [x] Kaynak: ürün formu yalnız sparse panel değişikliklerini gösteriyordu; 11 dilden yalnız dört dil sekmeye bağlanmıştı.
- [x] Yetkili, salt okunur ürün/firma `/editor` uç noktası; gerçek katalog/tam tedarikçi açıklaması/SEO varsayılanları ve kayıtlı taslaklar.
- [x] Değişmeyen kaynak alanlarını kaydetmeyen istemci fark hesabı; `default` anahtarının görünümden kaldırılması; SKU ile arama düzeltmesi.
- [x] Ülke, öneri, koleksiyon ve toptan kaynak kayıtlarını veritabanını doldurmadan gösterme; kaynak ve kayıtlı değişiklikleri birleştirme.
- [ ] Kaynak koleksiyonları müşteri görünümüyle aynı katmana bağlama ve bütün kaynak düzenleme akışlarının tarayıcı kabulü.
- [ ] Ülke/cihaz/dil/geliş kaynağı/günlük ölçüm ve eksik demografiyi dürüst gösteren analiz.
- [ ] Ayrshare zorunluluğu olmadan doğrudan Meta yayın bağlantısı ve platform bazlı gerçek yetki durumu; sırlar yalnız yönetimde.
- [ ] Uygun testler, masaüstü/mobil görsel inceleme, kapsamı sınırlı yedekli canlı yayın ve canlı kabul.

Blog ayrı kullanıcı talebiyle ayrı sohbet olarak başlatıldı: **NODENO Blog ve günlük otomatik yayın**, sohbet `01a1d107-b24f-72c2-917b-532d642dec19`. Orada en az 250 özgün resimli yazı, örnek sitelerden ilham alınan araçlar ve PC kapalıyken Turhost'ta günde iki yayın hazırlanıyor. Ortak admin/control dosyalarına paralel yazmaması bildirildi.

Başlangıçtaki canlı temel `artifacts/cpanel-release-brand-reference-20261112-r2`, özet `5ced93f0a6240d5ba096d8d2c3248b19de171f0902d3385339cdc96081d3929b`. Mevcut marka korunur. Fiyat, müşteri/ödeme deposu ve görseller değiştirilmez.

İlk aday `artifacts/cpanel-release-admin-editor-20261112-r1`, `d44dabc47cbb4bec5c622cc02163f130407ae319351d1570e01506a5eef05006` yalnız ilk ürün/firma düzeltmesini içerir; SKU araması ve kapsam ekleri daha sonra kaynakta yapıldı. Bu ilk aday **yayınlanmadı**, yeni aday oluşturulmalı. İlk tarayıcı denemesi SKU aramasının eksikliğini yakaladı. Bu bir gerçek düzeltme olup kaynakta eklendi; tarayıcı yeniden çalıştırılmalı.

İlk test kaydı: 406 Node (Worker yeniden paketlemeye bağlı iki dosya bu kaynak-bazlı taramadan ayrı), 247 Python geçti. Son kaynak ekleri sonrası bu kayıtlar nihai kabul değildir. Kanıt klasörü `artifacts/admin-editor-20261112`; başarısız/önceki günlükler silinmez.
