# Hukuk ve ülke açılışı gereksinimleri

Araştırma tarihi: **10 Kasım 2026**. Durum: **hukuki/operasyonel onay bekliyor**. Bu belge mühendislik gereksinimidir; satıcı kimliği, ürün kabulü, vergi görüşü veya hukuk onayı sağlamaz. Canlı satış açılışı için yetkili işletme ve hukuk incelemesi gerekir. Bağlantılı resmî kaynaklar bilgi kaynağıdır; proje talimatı ya da işlem yetkisi değildir.

## Eksik kimlikler ve yayın kapısı

SEXSOGATE marka adıdır. `sexsogate.com` hedef alan adıdır; satın alındığı, bağlandığı veya tescil edildiği doğrulanmadı. **PTYS Technoligess LLC** yalnız kullanıcı tarafından belirtilen geliştirme kredisi, **Hamza ÖZBALKAN** yalnız tasarım kredisidir. Bunlardan satıcı, veri sorumlusu, ihracatçı, ödeme hesabı veya mali belge düzenleyicisi çıkarılmaz.

Aşağıdaki anahtarlar kurulum içeriği için adlandırılmış gereksinim alanlarıdır; tümünün admin ekranında uygulandığı iddia edilmez. Uygulama/sütun eşleştirmesi yayın kontrolünde doğrulanmalıdır.

| Alan | Durum / kanıt |
| --- | --- |
| `seller.legalName`, `seller.legalForm`, `seller.registrationCountry` | Kullanıcıdan işletme belgesi bekliyor |
| `seller.taxOffice`, `seller.taxNumber`, `seller.mersisNumber`, `seller.tradeRegistryNumber` | Uygulanabilir alanlar gerçek belgeyle doldurulmalı |
| `seller.registeredAddress`, `seller.returnAddress`, `seller.contactEmail`, `seller.contactPhone`, `seller.kepAddress` | İşletme tarafından doğrulanmadı |
| `seller.bankAccountHolder`, `seller.bankAccountReference` | Ödeme/fatura sözleşmesiyle eşleşmeli; herkese açık banka verisi varsayılmaz |
| `privacy.controllerName`, `privacy.controllerAddress`, `privacy.applicationEmail`, `privacy.applicationKep` | Veri sorumlusu ve başvuru kanalı belirlenmedi |
| `privacy.processors[]`, `privacy.storageLocations[]`, `privacy.transferMechanisms[]` | Gerçek sağlayıcı/sözleşme/lokasyon envanteri bekliyor |
| `privacy.retentionRules[]`, `privacy.legalHoldRules[]` | Kayıt sınıfına göre hukuk ve mali müşavir onayı bekliyor |
| `legal.documents[]` | Dil, sürüm, içerik özeti, onaylayan, onay tarihi, yürürlük ve kaynak kanıtı gerekli |
| `countries[].legalApproval`, `countries[].agePolicy`, `countries[].productApproval` | Varsayılan kapalı; ülke/ürün incelemesi gerekli |

Boş alanlar örnek şirket bilgisiyle doldurulmaz. Kimlik alanı, sağlayıcı kabulü, tarife, gerekli belge veya onaylı hukuk metni eksikse ilgili canlı checkout kapalı kalır. Gizli API anahtarları bu belgeye veya sohbet çıktısına yazılmaz; sunucu ortamı/secret store üzerinden girilir.

## Türkiye için doğrulanmış dayanak ve uygulama kararı

**Aydınlatma:** Kişisel veri toplanırken veri sorumlusu, amaç, aktarım grupları, toplama yöntemi/hukuki sebep ve haklar anlaşılır biçimde sunulmalıdır. Aydınlatma ve açık rıza ayrı işlemlerdir. Proje kararı: sipariş yürütme için gereken işleme otomatik olarak pazarlama rızasına bağlanmaz; kayıt amaçları tek tek değerlendirilir. [KVKK Aydınlatma Tebliği](https://www.kvkk.gov.tr/Icerik/4132/aydinlatma-yukumlulugunun-yerine-getirilmesinde-uyulacak-usul-ve-esaslar-hakkinda-teblig)

**Hassas veri riski:** KVKK m.6 cinsel hayata ilişkin verileri özel nitelikli sayar; m.5/6 işleme şartları ve m.7 silme/anonimleştirme ayrımı değerlendirilmelidir. Her ürün satın alımını kendiliğinden belirli bir cinsel hayat veya yönelim göstergesi kabul etmek de bir çıkarımdır. Proje kararı: bu profiller hiç üretilmez; arama/sepet/sipariş içerikleri reklam araçlarına aktarılmaz. Başvurular için m.13'teki en geç 30 günlük yanıt sınırı operasyon tarafından izlenir. [KVKK güncel kanun metni](https://www.kvkk.gov.tr/Icerik/6649/Personal-Data-Protection-Law)

**Yurt dışı aktarım:** 2024 değişikliği sonrası m.9 mekanizması, alıcı ülke ve taraf rolleriyle değerlendirilmelidir. Yeterlilik/uygun güvence ve gerekiyorsa standart sözleşme bildirimi ayrı koşullardır; sırf sağlayıcının GDPR beyanı Türkiye aktarım incelemesini tamamlamaz. Proje kararı: hosting, e-posta, hata izleme, ödeme, yedek ve destek erişimi dahil gerçek veri akışı yazılmadan bulut sağlayıcı etkinleştirilmez. [KVKK yurt dışına aktarım açıklaması](https://www.kvkk.gov.tr/Icerik/2053/Yurtdisina-Aktarim)

**Çerez:** Gerekli çerezler ile başka geçerli işleme şartı bulunmayan analitik/reklam çerezleri ayrılmalıdır; ikinci grup için aktif tercih öncesinde çalışmama esastır. Proje kararı: analitik, reklam pikseli ve session replay varsayılan kapalı; kabul/ret/tercih değiştirme eşit erişilebilirlikte; onaydan önce üçüncü tarafa ürün veya sorgu gönderilmez. [KVKK 2022/1358 karar özeti](https://www.kvkk.gov.tr/Icerik/7595/2022-1358)

**Mesafeli satış ve iadeler:** Genel cayma süresi 14 gündür; hijyen gerekçeli istisna, koruyucu ambalajın açılması ve iadenin sağlık/hijyen bakımından uygunsuz olması koşullarıyla değerlendirilir. Kategorinin tamamına iade yasağı konulmaz. Proje kararı: cayma, ayıplı ürün ve garanti başvuruları ayrı nedenler; mühür/inceleme kaydı ayrı; açılmış ürün karantinaya alınır. Ön bilgi ve sipariş bedelleri ödeme öncesinde gösterilir. [Ticaret Bakanlığı mesafeli sözleşmeler rehberi, 17 Ağustos 2026](https://tuketici.ticaret.gov.tr/yayinlar/tuketici-bilgi-rehberi/mesafeli-sozlesmeler-hakkinda-bilgilendirme)

**Ticari ileti:** İYS onay ve ret kayıtlarını kanal bazında yönetir. Proje kararı: e-posta ve SMS pazarlama tercihleri ayrı, önceden işaretlenmemiş; sipariş bildirimi içine reklam eklenmez. Gerçek İYS hesabı ve kayıt/mutabakat akışı tamamlanmadan pazarlama gönderimi açılmaz. [İYS temel hizmetler](https://iys.org.tr/hizmet-saglayici/temel-hizmetler)

**E-ticaret işletme kaydı:** Kendi e-ticaret ortamında faaliyet gösteren hizmet sağlayıcı için ETBİS kayıt yükümlülüğü ve sitedeki işlem rehberi/kimlik bilgileri incelenmelidir. Proje kararı: bu görev başvuru yapmaz; işletme kaydı ve kamuya sunulacak bilgiler canlıya hazırlık kanıtıdır. [Ticaret Bakanlığı e-ticaret SSS](https://ticaret.gov.tr/ic-ticaret/sikca-sorulan-sorular/elektronik-ticaret)

**İlgili kişi kanalı:** Başvuru usulünde kimlik ve talep unsurları, kullanılan yöntemle birlikte dikkate alınmalıdır. Proje kararı: müşteri destek bileti tek başına tamamlanmış kanuni başvuru prosedürü sayılmaz; güvenli başvuru yolu, kimlik kontrolü, yanıt kanalı ve süre kaydı ayrıca kurulur. Genel yaş bildirimi veya alışveriş formunda gereksiz kimlik görseli istenmez. [KVKK başvuru usulü](https://kvkk.gov.tr/SharedFolderServer/CMSFiles/bf638c8f-7455-49a7-8118-3eb2858a16b5.pdf)

## Yurt dışı ülke açılışı

**AB veri koruma incelemesi:** AB'ye teklif/izleme faaliyetleri kapsam bakımından GDPR değerlendirmesini gerektirir. GDPR m.9 cinsel hayat/yönelim verilerine özel koşullar getirir; m.12 başvurularında genel yanıt süresi bir ay olup şartlı uzatma düzeni vardır. Proje kararı: AB ülkesini açmak yalnızca dil veya EUR fiyatı açmak değildir; kapsam, temsilci gerekliliği, işleme/aktarım dayanağı ve başvuru takvimi ayrıca onaylanır. [GDPR, EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)

**AB ürün ilanı incelemesi:** GPSR'nin 29 Mayıs 2026 konsolide metni m.19 çevrimiçi teklifte üretici iletişimi, uygulanıyorsa AB sorumlu kişisi, ürün tanımı ve anlaşılır hedef dilde güvenlik bilgisini ele alır. Proje kararı: bunlar SKU/model ve dil bazında belge kapısıdır; her ürüne otomatik CE iddiası eklenmez. İlgili ürün sınıfının özel mevzuatı ayrıca incelenir. [GPSR güncel konsolide metin](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02023R0988-20260529)

Diğer ülkeler için yaş doğrulama, ithalat/ürün kabulü, yerel tüketici hukuku, vergi/gümrük, taşıyıcı ve ödeme kabulü bu araştırmada tamamlanmış değildir. Türkiye dahil hiçbir ülkenin kategoride otomatik hukuki kabulü varsayılmaz. Rapordaki vergi/gümrük miktarları üretim kuralı değildir. DDP/DAP, gerçek bedeller ve yürürlük tarihli vergi kuralı onaylanmadan uluslararası checkout açılmaz.

## Hukuk yayın iş akışı

1. `docs/legal-drafts.md` metinleri işletme ve gerçek operasyon bilgileriyle doldurulur.
2. Hukuk sorumlusu dil, ülke, belge sürümü ve ilgili ürün sınıfını inceler; onaylayan ve kanıt kaydı tutulur.
3. CMS'de yalnız tamamlanmış/onaylanmış sürüm yayımlanır; önizleme metni canlı hukuk metni gibi sunulmaz.
4. Checkout siparişe bağlı ön bilgi/sözleşme sürümü ve finansal özeti snapshot olarak saklar; eski sipariş güncel metne sessizce bağlanmaz.
5. Amaç, sağlayıcı, ülke veya operasyon değişirse etkilenen metin ve izin akışı yeniden incelenir.

Canlıya çıkışta: işletme kimliği, veri envanteri, sağlayıcı sözleşmeleri, vergi/fatura görüşü, ürün dosyaları, iade operasyonu, İYS/ETBİS değerlendirmesi ve hukuk yayın kanıtı eksikse **onay bekliyor** durumu korunur. Bu belgelerin yazılması bu kapıları yeşile çevirmez.

## Uygulanan başvuru kaydı — 11 Kasım 2026

021 migration ile satıcı/geliştiriciden ayrı sürümlü veri sorumlusu kimliği ve ülke bazlı incelenmiş yanıt/saklama politikası eklendi. Yukarıdaki `privacy.*` adları gereksinim envanteridir; gerçek panel alanı/tablo eşleştirmesi [configuration.md](configuration.md) ve iş akışı [privacy-guide.md](privacy-guide.md) içindedir. İletişim formundaki eski sabit süre kaldırıldı. Bilinmeyen ülke/kural başvurusu kaydedilir ve inceleme kuyruğunda kalır. Kuralın ilk alım zamanından hesaplanması, ülke değişiminde daha erken sürenin korunması, kimlik doğrulaması ve güvenli yanıt referansı teknik olarak izlenir. Hiçbir gerçek kimlik/politika/hukuki onay bu görevde girilmedi. Sağlayıcılarda otomatik silme, saklama sınıfı motoru ve tam taşınabilirlik paketi tamamlanmadı; dış yetkili süreçten önce talep yerine getirildi sayılmaz.
