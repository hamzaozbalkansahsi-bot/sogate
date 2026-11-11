# Hukuki içerik taslakları ve yayın alanları

Tarih: 10 Kasım 2026. **Tüm bölümler taslaktır; canlıda onaylı hukuk metni olarak yayımlanamaz.** Bu dosya içerik ekibine/hukuk incelemesine başlangıç metni verir. `{{alan}}` ifadeleri içerik veri eşleme alanlarıdır; boşlukları uydurma bilgilerle doldurmayın ve bu işaretleri müşteriye göstermeyin. Zorunlu alan eksikse ilgili belge yayınlanmaz. Dayanaklar ve araştırma sınırı `docs/legal-requirements.md` içindedir.

Her belge kaydı `key`, `locale`, `version`, `status`, `body`, `effectiveAt`, `approvedBy`, `approvedAt`, `approvalEvidence` alanlarını taşımalıdır. `status=draft` varsayılandır. Ödeme öncesinde kullanılan işlem belgeleri siparişe bağlı içerik/sürüm ve fiyat snapshot'ıyla saklanır. Burada veri sözleşmesi tarif edilmesi tüm CMS alanlarının uygulanmış olduğunu göstermez.

## KVKK aydınlatma metni / `privacy-notice`

**İçerik taslağı:** SEXSOGATE hizmetlerinde kişisel verilerinizin işlenmesine ilişkin bu açıklamanın veri sorumlusu `{{privacy.controllerName}}`, iletişim adresi `{{privacy.controllerAddress}}` ve başvuru kanalı `{{privacy.applicationChannel}}`dır. Hesap, sipariş, teslimat, ödeme mutabakatı ve destek işlemlerinde talebinizi yerine getirmek için gereken bilgiler işlenir. Hangi veri grubunun hangi amaçla ve hukuki sebeple işlendiği `{{privacy.processingTable}}` tablosunda; paylaşım yapılan alıcı grupları ve amaçları `{{privacy.recipientTable}}` bölümünde açıklanır. Verilerin nasıl toplandığı, saklama yaklaşımı ve haklarınızı kullanma yolları `{{privacy.collectionAndRights}}` bölümündedir.

**Yayın için:** Gerçek veri envanteri, süreç bazlı hukuki sebep, veri sorumlusu ve alıcı/lokasyon kayıtları doldurulmalı. Sipariş işleme, üyelik, pazarlama ve çerez tercihleri tek bir “KVKK onayı”na bağlanmaz. Aydınlatma ile rıza ayrı sunulur. [Aydınlatma Tebliği](https://www.kvkk.gov.tr/Icerik/4132/aydinlatma-yukumlulugunun-yerine-getirilmesinde-uyulacak-usul-ve-esaslar-hakkinda-teblig)

## Gizlilik ve güvenlik politikası / `privacy-policy`

**İçerik taslağı:** Sipariş ve hesap bilgilerinize yalnız gerekli işlemler için erişilir. Bildirimlerde ürün ayrıntılarını göstermeyen iletişim tercihleri sunulur; sipariş ayrıntılarına güvenli hesabınızdan veya yetkili takip bağlantınızdan erişebilirsiniz. İletişim ve teslimat sağlayıcıları, veri lokasyonları ve güvenlik/saklama uygulamaları `{{privacy.actualOperations}}` bölümünde açıklanır. Pazarlama tercihlerinizi `{{privacy.preferenceRoute}}` üzerinden yönetebilirsiniz.

**Yayın için:** Uygulanmayan şifreleme, anonimlik veya güvenlik garantisi yazılmamalı. Gerçek altyapı ve test kanıtıyla karşılaştırılmalı. Katalog tercihlerinden cinsel hayat/yönelim/sağlık profili çıkarılmaz; reklam için kimlikle birleştirilmez.

## Çerez politikası / `cookie-policy`

**İçerik taslağı:** Bu sitedeki çerez ve benzeri kayıtların adı, amacı, sağlayıcısı ve süresi `{{cookies.inventory}}` tablosunda gösterilir. Temel işlevler için gereken kayıtlarla isteğe bağlı analitik/reklam tercihleri ayrı yönetilir. İsteğe bağlı tercihlerinizi kabul edebilir, reddedebilir veya `{{cookies.preferencesRoute}}` üzerinden değiştirebilirsiniz. Reddetmek alışveriş yapmanızı engellemez.

**Yayın için:** Tarayıcıda gerçekten oluşan isim ve sürelerle tablo doldurulmalı; kullanılmayan servis varmış gibi yazılmamalı. Onay gerektiren servis izin öncesi yüklenmez. [KVKK çerez kararı](https://www.kvkk.gov.tr/Icerik/7595/2022-1358)

## Kullanım koşulları / `terms-of-use`

**İçerik taslağı:** SEXSOGATE yetişkinlere yönelik ürün ve bilgilendirme sunar. Ürün seçerken üretici uyarılarını ve hedef ülkeye ilişkin satış/teslimat koşullarını inceleyin. Siteyi hukuka aykırı erişim, başkasının hesabını kullanma veya sistemin çalışmasını bozma amacıyla kullanmayın. İşletme iletişimi, içerik hakları ve uyuşmazlık başvuru yolları `{{terms.operatorAndContact}}` bölümünde açıklanır. Tüketicinin emredici hakları sözleşme metniyle kaldırılmaz.

**Yayın için:** Yaş politikası ülkeye göre incelenmeli. Basit 18+ bildirimi evrensel hukuki yaş doğrulaması gibi sunulmamalı; sağlık/tıbbi fayda iddiaları ürün belgesine dayanmalı.

## Üyelik sözleşmesi / `membership-terms`

**İçerik taslağı:** Üyelik, adreslerinizi ve siparişlerinizi güvenli biçimde yönetmenizi sağlar. Hesap bilgilerinizin doğruluğunu koruyun; parolanızı paylaşmayın. Oturumlarınızı ve iletişim tercihlerinizi hesap ekranından yönetin. Üyelik, kampanya mesajlarına izin verdiğiniz anlamına gelmez. Misafir alışverişi seçeneği mevcuttur. Hesap kapatma talebi, zorunlu saklama kapsamındaki işlem kayıtlarıyla birlikte `{{membership.closureProcess}}` sürecinde değerlendirilir.

**Yayın için:** Parola sıfırlama, çıkış/iptal ve kapatma süreci gerçek işlevle eşleşmeli; üyeliği gereksiz yere alışveriş ön koşulu yapmamalı.

## Ön bilgilendirme / `pre-contract-information`

**İçerik taslağı:** Satıcı `{{seller.legalName}}`; adres ve iletişim `{{seller.contactDetails}}`. Siparişinizin ürün/varyant, miktar ve temel nitelikleri `{{order.lines}}` bölümündedir. Vergi dahil ürün bedeli, indirim, kargo, diğer geçerli ücretler, tahsilat para birimi ve ödenecek toplam `{{order.priceSummary}}` olarak gösterilir. Teslimat yeri/yöntemi, taahhüt ve olası ek bedeller `{{order.deliveryTerms}}`; cayma/şikâyet/iade usulü `{{order.consumerRights}}` bölümündedir.

**Yayın için:** Sunucuda yeniden hesaplanan gerçek sipariş özeti kullanılmalı; gizli ücret, otomatik seçili ücretli hizmet veya eksik satıcı kimliğiyle checkout açılmamalı. [Ticaret Bakanlığı mesafeli satış rehberi](https://tuketici.ticaret.gov.tr/yayinlar/tuketici-bilgi-rehberi/mesafeli-sozlesmeler-hakkinda-bilgilendirme)

## Mesafeli satış sözleşmesi / `distance-selling-contract`

**İçerik taslağı:** Taraflar `{{seller.legalName}}` ve siparişte tanımlı alıcıdır. Konu, `{{order.lines}}` ürünlerinin `{{order.priceSummary}}` bedelleriyle ve `{{order.deliveryTerms}}` koşullarıyla teslimidir. Ödeme, siparişin işlenmesi, ifa, cayma, iade, ayıplı ürün ve uyuşmazlık yolları `{{contract.approvedClauses}}` bölümündedir. İşlem anındaki sözleşme sürümüne `{{contract.accessRoute}}` yoluyla erişebilirsiniz.

**Yayın için:** Sipariş/ödeme/teslimat durumu ayrılmalı; hukukça onaylı maddeler, kalıcı saklama ve sonradan erişim gerçek işleyişle eşleşmeli.

## Teslimat ve gizli paketleme / `shipping-policy`

**İçerik taslağı:** Teslimat seçenekleri ve ücretleri adres ve ürün kapsamına göre sipariş öncesinde gösterilir. Desteklenen ülkeler, taşıyıcı, taahhüt ve takip bilgisi `{{shipping.actualRules}}` bölümündedir. Ambalajın dış görünümünde ürün ayrıntılarını azaltan paketleme uygulanması, fatura veya gümrükte doğru ürün beyanını değiştirmez. Gecikme/hasar başvurusu için `{{seller.supportChannel}}` kullanılabilir.

**Yayın için:** Gerçek depo paketleme prosedürü ve taşıyıcı tarifesi doğrulanmalı; teslimat süresi veya tüm dünyaya gönderim uydurulmamalı.

## Cayma, iade ve ayıplı ürün / `returns-policy`

**İçerik taslağı:** Sipariş ekranından veya `{{returns.applicationChannel}}` üzerinden başvuru yapabilirsiniz. Başvurunuzun cayma, hasar/ayıp veya garanti nedeni ayrı kaydedilir. Ürün ve ülkeye uygulanan koşullar `{{returns.approvedRules}}` bölümündedir. Hijyen mührü durumu ve inceleme sonucu gerekçesi size bildirilir. İade gönderim yöntemi, ücret ve ödeme iadesi süreci `{{returns.operationalTerms}}` bölümünde açıklanır. Ayıplı ürün hakları genel bir kategori yasağıyla kaldırılmaz.

**Yayın için:** Kapalı mühür, açılmış ambalaj, ayıplı ürün ve ülke kuralı ayrı değerlendirilir. İadenin depoya alınması yeniden satışa kabul değildir. [Mesafeli satış rehberi](https://tuketici.ticaret.gov.tr/yayinlar/tuketici-bilgi-rehberi/mesafeli-sozlesmeler-hakkinda-bilgilendirme)

## Ticari ileti tercihi / `marketing-consent`

**İçerik taslağı:** Kampanya ve yeni koleksiyon duyurularını almak istediğiniz kanalı seçebilirsiniz: e-posta / SMS. Her kanal ayrı ve isteğe bağlıdır. Tercihinizi `{{marketing.preferenceRoute}}` üzerinden değiştirebilir, iletilerdeki ret yolunu kullanabilirsiniz. Bu seçim siparişinizin verilmesi veya işlem bildirimlerinin alınması için ön koşul değildir. Gönderen kimliği ve iletişim kaydı `{{marketing.senderDetails}}` bölümündedir.

**Yayın için:** Kutular işaretli gelmez; gerçek gönderen ve İYS süreçleri doğrulanır. [İYS temel hizmetler](https://iys.org.tr/hizmet-saglayici/temel-hizmetler)

## İlgili kişi başvurusu / `data-subject-request`

**İçerik taslağı:** Kişisel verilerinize ilişkin talebinizi `{{privacy.applicationChannel}}` yoluyla iletebilirsiniz. Başvurunun kapsamını ve size yanıt verilebilecek bilgiyi belirtin. Başvuru yöntemi ve gerekli kimlik/talep unsurları `{{privacy.applicationInstructions}}` bölümünde açıklanır. Talebinizin alınması, kimlik kontrolü, değerlendirilmesi ve yanıtı kayıt altına alınır. Gereksiz hassas bilgi veya kimlik görseli göndermemenizi öneririz; ek bilgi gerekirse güvenli yöntem bildirilir.

**Yayın için:** İlgili başvuru yönteminin kanuni unsurları hukuk tarafından belirlenmeli; destek kutusu otomatik tam prosedür sayılmamalı. Mali saklama/uyuşmazlık kayıtları için ayrı değerlendirme yapılır. [KVKK başvuru usulü](https://kvkk.gov.tr/SharedFolderServer/CMSFiles/bf638c8f-7455-49a7-8118-3eb2858a16b5.pdf)

## Amaç bazlı açık rıza / `explicit-consent`

**İçerik taslağı:** `{{consent.controllerName}}` tarafından `{{consent.specificPurpose}}` amacıyla `{{consent.specificDataCategories}}` bilgilerimin `{{consent.processingAndRecipients}}` kapsamında işlenmesine ilişkin ayrı açıklamayı okudum. Bu isteğe bağlı işlem için tercihimi serbestçe belirleyebilirim. Vermediğim rıza nedeniyle temel alışveriş işlemi engellenmez; tercihim `{{consent.withdrawalRoute}}` yoluyla geri alınabilir. Rızanın kapsamı, süresi ve geri alma sonrası uygulama `{{consent.scopeAndConsequences}}` bölümünde açıklanır.

**Yayın için:** Gerçekte açık rıza gerektiren belirli işlem bulunmadan genel/boş bir rıza kutusu oluşturulmaz. İşlem amaçları, veri kategorileri ve alıcılar tek tek doldurulur. Aydınlatma, sözleşme ve ticari iletiyle birleştirilmez; alanlar boşken onay/yayın kapalıdır. Bu taslak, tüm sipariş işlemlerinin açık rızaya dayandığı anlamına gelmez. [Aydınlatma ve rızanın ayrılması](https://www.kvkk.gov.tr/Icerik/4132/aydinlatma-yukumlulugunun-yerine-getirilmesinde-uyulacak-usul-ve-esaslar-hakkinda-teblig)

## Ayıplı ürün başvurusu / `defective-product-policy`

**İçerik taslağı:** Teslim aldığınız üründe hasar, çalışmama veya açıklamayla uyuşmazlık olduğunu düşünüyorsanız `{{defective.applicationChannel}}` üzerinden siparişinize bağlı başvuru oluşturabilirsiniz. İnceleme için gereken ürün/teslimat bilgisi ve güvenli gönderim yolu `{{defective.inspectionProcess}}` bölümünde açıklanır. Başvurunuz cayma talebinden ayrı değerlendirilir; hijyen ambalajının durumu tek başına genel hak kaybı gerekçesi yapılmaz. Değerlendirme sonucu ve uygulanacak çözüm gerekçesiyle bildirilir. İlgili yasal haklar ve yetkili başvuru yolları `{{defective.approvedRights}}` bölümünde yer alır.

**Yayın için:** Gerçek servis, garanti ve taşıma prosedürü doğrulanmalı. Müşteriden gereksiz mahrem fotoğraf/sağlık bilgisi istenmemeli; ürün incelenmeden otomatik yeniden satış stokuna alınmamalı. Ürün ve ülke özelindeki hak/süreler hukuk tarafından tamamlanmalıdır.

## Admin taslak yükleme sözleşmesi

`scripts/legal-drafts.ts` yalnız bu dosyadaki **İçerik taslağı** paragraflarını alır; yayın notları müşteri metni gövdesine eklenmez. Her taslak Türkçe, `draft`, `fixture=false` olarak eklenir; `approved/effective` yapılmaz. Mevcut belge veya geçmiş sipariş snapshot'ı değiştirilmez. Aynı gövde hash'i yeniden yüklenmez; yeni sürüm numarası mevcut en büyük sürümden sonra seçilir.

Belge eşlemeleri: `privacy-notice→privacy`, `privacy-policy→privacy_policy`, `cookie-policy→cookies`, `terms-of-use→usage`, `membership-terms→membership`, `pre-contract-information→pre_information`, `distance-selling-contract→terms`, `shipping-policy→shipping`, `returns-policy→returns`, `marketing-consent→consent`, `data-subject-request→data_request`, `explicit-consent→explicit_consent`, `defective-product-policy→defective`.

`{{...}}` alanları yalnız yetkili admin önizlemesinde kalabilir; bunları içeren belge onaylanamaz veya yürürlüğe alınamaz. Gerçek satıcı bilgileri boşken yürürlüğe alma ayrıca engellenir. Müşteri yalnız onaylı/yürürlükteki sürüme erişir. İngilizce hukuk çevirisi bu taslak yükleyiciyle üretilmez; ilgili ülke/dil yayını için ayrı tamamlanıp onaylanmalıdır.

## Yerel yükleme ve doğrulama

```powershell
npx tsx --env-file=.env.local scripts/legal-drafts.ts
npx tsx --env-file=.env.local scripts/legal-drafts-integration.ts
```

10 Kasım 2026'da ilk yükleyici testi işlev uygulanmadan başarısız çalıştırıldı. Uygulama sonrasında placeholderlı belgeyi onaylama testi de önce başarısız oldu (`Missing expected rejection`); sunucu guard'ı eklendikten sonra **6/6 PostgreSQL kontrolü geçti**. Kontroller yeni rastgele isimli yerel `*_legal_test` DB'de yürütülüp yalnız o DB kaldırıldı; `seed.ts` ortam/DB korumaları gevşetilmedi.

Doğrulanan davranışlar: 13 taslağın admin'e gövdesiyle görünmesi; destek rolünün yalnız effective belge meta verisi alması; tekrar yüklemede kopya oluşmaması; placeholder onayının reddi; gerçek satıcı alanı boşken doldurulmuş/onaylı belgeyi etkinleştirmenin reddi; production'da taslak yükleyicinin çalışmaması; kaynak hukuk gövdesi/başlığı/hash'i sonradan değiştirilse de siparişte kabul edilmiş snapshot'ın değişmemesi.

Yerel development DB'ye aynı komutla **13 taslak eklendi, 0 mevcut kayıt değiştirildi**. Otomatik onay veya yayın yapılmadı. Bu kayıtlar hukuk onayı, tamamlanmış İngilizce çeviri veya canlı satış izni değildir. İleride dosyadaki gövde değişirse yeni draft sürümü açılır; eski sipariş ve belge üzerine yazılmaz.
