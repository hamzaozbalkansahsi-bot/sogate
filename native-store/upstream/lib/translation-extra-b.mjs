// Exact technical specifications from the audited source list (indices 0–319).
const source = [
  "Gömme kulplar",
  "Koku oluşumunu engellemek için arkalığında minik yuvarlak delikler",
  "Yenilenmiş sürgü ray mekanizması",
  "Çok amaçlı kullanım alanı ; Banyo,Mutfak,Ofis,Balkon",
  "24 çift ayakkabı ,terlik kapasiteli",
  "Estetik ayaklar",
  "Çok amaçlı kullanım alanı ; Banyo ,Mutfak , Ofis ,Balkon",
  "Sonoma / Karışık Renkli",
  "Kesonlu çalışma masası",
  "Ergonomik ve şık tasarımı sayesinde hem çalışma hem de bilgisayar masası olarak kullanılabilme özelliği",
  "Şık ve kullanışlı raflar",
  "5 adet geniş raflar",
  "Kaliteli masif ahşap doku",
  "Dayanıklı kanca",
  "Kırılmaz pantolon askılığı",
  "Bir pakette 5 adet ürün mevcuttur",
  "Ürün 1 koli 5 askıdan oluşmaktadır.",
  "Sonoma / Karışık",
  "Doğal ahşap dokulu ve lake parlaklığında beyaz renk uyumu",
  "3 adet yatak suntası",
  "Karyolalarımızla uyumlu yatak ölçüleri 90cm - 190 cm' dir.",
  "Karyolalarımızla uyumlu yatak ölçüleri 100 cm - 200 cm' dir.",
  "Sonoma Karışık Renkli",
  "Sonoma gövde ve renkli başlık uyumu",
  "2 adet yatak suntası",
  "Estetik retro ayak kullanılmıştır.",
  "1 adet yer değiştirilebilir dekoratif X raf",
  "2 adet yer değiştirilebilir dekoratif çapraz raf",
  "2 adet kilitli kapak",
  "Ofis mobilyaları ile uyumludur",
  "Askılık altı ilave ra",
  "35 çift ayakkabı ,terlik kapasiteli",
  "Çekmece üstü temperli cam",
  "2 geniş iç bölme",
  "Diğer raf modelleri ve renkleri ile farklı kombinler oluşturabilirsiniz",
  "Şık renkli kulplar",
  "Çekmece mekanizması teleskop ray",
  "Çok amaçlı kullanım alanı",
  "Ürün bambu malzemeden üretilmiştir.",
  "4 bölmeli (1 bölme uzun elbiselerin asılması için)",
  "2 adet geniş , 1 adet dar dayanıklı metal elbise askılığı",
  "2 adet geniş , 1 adet dar sabit raf",
  "Kapakların sert kapanmasını engelleyen frenli sürgü kapak mekanizmasıKaliteli bağlantı parçaları",
  "2 adet geniş hareketli raf",
  "Kablo kanal deliği",
  "1 adet geniş ve yüksek çekmece",
  "TV konulan alan ölçüsü ; Genişlik: 117 cm Derinlik: 40 cm",
  "Latte / Soft Beyaz",
  "Doğal ahşap doku ve soft beyaz uyumu",
  "Parlak beyaz 15 cm'lik modern sağlam yüksek ayaklar",
  "2 adet kablo çıkışlı",
  "2 adet sürgü kapak",
  "2 bölmeli açık raf",
  "Dört fonksiyonlu profesyonel oturak mekanizması",
  "Ayarlanabilir boyun ve bel desteği",
  "Ayarlanabilir kolçak yüksekliği",
  "Ayarlanabilir sırt açısı ve sabitleme özelliği",
  "İleri-geri ayarlanabilir oturum derinliği",
  "Terletmeyen ergonomik file sırt",
  "Geniş ve konforlu oturum minderi",
  "BIFMA standartlarında amortisör ve yıldız ayak",
  "360° dönebilen, sessiz ve parke çizmez tekerler",
  "Dayanıklı kontra plak oturum yapısı",
  "Kolay kurulum",
  "Çok amaçlı portatif tepsi",
  "Katlanabilen ayakları sayesinde az yer kaplar.",
  "Çok amaçlı kullanım alanı ; Balkon, Bahçe ,Mutfak , Ofis",
  "Not: Üzerine sıcak tencere, çaydanlık vb. ısıya duyarlı ürünler direk konulmamalıdır. 15 kg'den fazla ağırlık koymak, basmak veya merdiven olarak kullanmak tehlikeli olabilir.",
  "Evinizde ve ofisinizde portmanto veya yüklük olarak da kullanabilirsiniz.",
  "2 adet sabit",
  "Alüminyum şerit kapak",
  "8 bölmeli (1 bölme uzun elbiselerin asılması için)",
  "Mat krom kulplar",
  "Zemine zarar vermeyecek geniş ve estetik siyah yuvarlak ayaklar",
  "Metal kulplar",
  "Evinizde ve ofisinizde portmanto veya yüklük olarak da kullanabilirsiniz",
  "1 adet sabit üst ve bir adet geniş hareketli alt raf",
  "Sağlam gövde",
  "Bir pakette 8 adet ürün mevcuttur",
  "Ürün 1 koli 8 askıdan oluşmaktadır.",
  "Ev ve ofis kullanımına uygun tasarım",
  "12 askı alanı ile mont, şapka, çanta ve aksesuarlar için geniş kullanım kapasitesi",
  "51 cm taban çapı ile kompakt ve yerden tasarruf sağlayan yapı",
  "185 cm yüksekliği sayesinde uzun giysiler için uygun kullanım",
  "Döner başlık sayesinde eşyaları kolayca asma ve alma imkanı",
  "Metal destekler ile artırılmış stabilite",
  "Hafif yapısı sayesinde kolay taşınabilir kullanım",
  "Ürün, masif ahşap dokulu yapısı ve metal destek parçaları ile dayanıklı kullanım sunacak şekilde tasarlanmıştır.",
  "Ürün bileşenleri insan sağlığına zararlı madde içermez ve günlük kullanıma uygun malzemelerden üretilmiştir.",
  "12 askı alanı",
  "Mont, şapka, çanta ve aksesuarlar için geniş kullanım kapasitesi",
  "51 cm taban çapı ile kompakt yapı",
  "Döner başlık ile kolay kullanım",
  "1 adet kapaklı 3 raflı ayakkabılık bölmesi",
  "1 adet askılık üstü ilave raf",
  "12 çift ayakkabı , terlik kapasiteli",
  "Askılık altı ilave raf",
  "32 çift ayakkabı ,terlik kapasiteli",
  "28 çift ayakkabı , terlik kapasiteli",
  "Kapak içi 10 bölme",
  "8 adet hareketli ,",
  "Şık, krom kulplarEstetik, yuvarlak ayaklar",
  "32 çift ayakkabı , terlik kapasiteli",
  "Asimetrik dekoratif kapak",
  "8 adet hareketli , 1 adet sabit raf",
  "Köşe bağlantı aparatı",
  "1 adet yatak suntası",
  "Gövde ile sabit MDF Profil ayaklar",
  "Metal çerçeveli",
  "İki raflı dekoratif duvar ünitesi",
  "Farklı renk seçenekleri veya raflar ile özgün kombinler yaratma olanağı",
  "3 adet geniş sabit ra",
  "4 adet geniş sabit raf",
  "Konforlu tasarımı ve zarif detaylarıyla Boston Yönetici Koltuğu, ofis yaşamına kalite ve şıklık katar.",
  "Uzun çalışma saatlerinde ergonomik destek sunarken, dayanıklı malzemeleriyle de yıllarca kullanım sağlar.",
  "Ergonomik Tasarım",
  "Yüksek sırt yapısı sayesinde omurga sağlığınızı korur.",
  "Bel desteği, uzun oturumlarda bel boşluğunu destekler.",
  "Doğru oturma pozisyonu için mükemmel sırt ve omuz desteği sunar.",
  "Dayanıklı Suni Deri Kaplama",
  "Yumuşak ve kaliteli suni deri kaplama, lüks bir görünüm kazandırır.",
  "Leke tutmaz ve kolay temizlenebilir yüzeyiyle pratik kullanım sağlar.",
  "Aşınma ve yırtılmalara karşı dayanıklıdır.",
  "Yumuşak Sünger Dolgu",
  "Yüksek yoğunluklu sünger dolgusu, uzun süreli oturumlarda çökme yapmaz.",
  "Hem oturma minderi hem sırt kısmında maksimum konfor sunar.",
  "Oturum ve sırt minderi altında hava alır özel file kumaş ara katman ile ferahlık katar.",
  "Ayarlanabilir Yükseklik ve Sırt Yaslanma Mekanizması",
  "Gazlı amortisör sistemi ile oturma yüksekliği kişiye göre kolayca ayarlanabilir.",
  "Uzun süreli oturumlarda doğru masa yüksekliği için esneklik sağlar.",
  "Sırt yaslanma açısını istediğiniz konumda sabitleyebilir veya serbest bırakabiliriz.",
  "360° Dönebilme Özelliği",
  "360 derece dönebilen mekanizma, çalışma alanında özgürce hareket imkanı sunar.",
  "Kolay yön değiştirerek farklı alanlara erişimi hızlandırır.",
  "Yumuşak Kaplamalı Kolçaklar",
  "Yuvarlak ve ergonomik kolçaklar, kollarınız için ekstra destek sağlar.",
  "Doğal oturma pozisyonunu destekleyen açıyla tasarlanmıştır.",
  "Dayanıklı suni deri kaplaması içinde yumuşak sünger dolgusu vardır.",
  "Sağlam Yıldız Taban ve Sessiz Tekerlekler",
  "Dolgu plastik yıldız taban, sağlam ve dayanıklı yapısıyla güven verir.",
  "5 hareketli tekerlek, sessiz ve iz bırakmayan hareket kabiliyeti sunar.",
  "Parke, halı ve fayans zeminlerde kolayca kayar.",
  "Bas-Aç kapak mekanizmalı 1 adet çekmece",
  "Hem ev ,hem ofis kullanımı için uygundur,",
  "(110 x 70) boyutlarında üst tabla kullanım alanı",
  "Açılır retro ayaklar",
  "16 mm yonga levhadan üretilmiştir.",
  "KOLTUK MODELLERİMİZ İÇİN TIKLAYINIZ.",
  "1 adet kilitli çekmece,",
  "Ürün kurulumu için 2 kişi tavsiye edilmektedir.",
  "Lake Beyazı",
  "Kapak bölme içi 6 adet hareketli , 1 adet sabit raf",
  "Çok amaçlı kullanım alanı ; Banyo ,Mutfak , Ofis",
  "Özel üçgen ayak",
  "İsteğe bağlı olarak kapağın sağ veya sol tarafta kullanılabilme özelliği",
  "1 adet sabit ve 3 adet hareketli raf",
  "Baza sistemi sayesinde ek depolama alanı sağlar.",
  "Karyolalarımızla uyumlu yatak ölçüleri 90cm - 190 cm 'dir.",
  "1 adet geniş bölmeli çekmece",
  "Çok amaçlı kullanım alanı ; Banyo ,mutfak , ofis",
  "Geniş kapaklı bölme içi 5 adet hareketli raf",
  "Dar kapaklı bölme içi 3 adet hareketli raf",
  "Şık, mat krom kulplar",
  "Çok amaçlı kullanım alanı;Banyo, Mutfak, Ofis",
  "2 adet kapak bölmesi ve çekmecesi ile ergonomik kullanım özelliği",
  "Krom kaplama nokta kulp",
  "Çok amaçlı dolap özelliği ; Banyo, Mutfak, Ofis, Kiler, Antre, Balkon v.b",
  "3 hareketli, 1 sabit raf sayesinde ergonomik kullanım özelliği",
  "Çok amaçlı dolap özelliği ; Banyo,Mutfak,Ofis.vb",
  "Opsiyonel sağ-sol kullanılabilir dolap kapağı",
  "Özel kapaklı bölme içi 1 adet hareketli raf",
  "5 çekmecesi ile ergonomik kullanım özelliği",
  "Mobil tekerler sayesinde kolay taşınabilme özelliği",
  "Lake parlaklığında beyaz renk özel kapak bölmesi ve çekmecesi ile ergonomik kullanım özelliği",
  "Çok amaçlı dolap özelliği; banyo, mutfak, ofis, kiler, antre,balkon v.b",
  "Orta Bölüm Ölçüsü : 69 x 40,5 x 35 cm ( Genişlik x Yükseklik x Derinlik )",
  "Özel kapak bölmesi ile ergonomik kullanım özelliği",
  "Kapaklı bölme içi 1 adet sabit, 2 adet hareketli raf",
  "Açık bölme 1 adet sabit, 1 adet hareketli raf",
  "Çok amaçlı kullanım alanı; Banyo, Mutfak, Ofis, Balkon, Antre, Oda .",
  "Mobil tekerlekler sayesinde kolay taşınabilme özelliği",
  "3 tanesi hareketli olmak üzere toplam 4 adet raftan oluşan bölme",
  "1 adet düşer kapaklı sepetli bölme",
  "4 adet yüksek dekoratif ayak",
  "Çok amaçlı kullanım alanı ;Banyo, Mutfak, Balkon, Antre, Oda .",
  "Dekoratif kutu olarak kullanılabilen 2 adet raysız çekmece",
  "Çok amaçlı kullanım alanı ;Banyo, Mutfak, Balkon ,Antre ,Oda.",
  "4 bölmeli modül içi tasarım",
  "Oslo Cevizx",
  "Çalışma masasını tamamlar",
  "Duvara monte edilebilir",
  "2 adet bas-aç kapaklı bölme",
  "1 adet çekmece üstü bölme",
  "1 adet askılık",
  "2 adet askılık",
  "Orta bölüm sabit raf",
  "Opsiyonel hareketli raflar",
  "Özel kapak bölmesi ve çekmecesi ile ergonomik kullanım özelliği",
  "Hareketli raf",
  "Çok amaçlı dolap özelliği",
  "Banyo,mutfak,ofis.vb mobil tekerler sayesinde kolay taşınabilme özelliği",
  "Kapak içi 11 bölme",
  "9 adet hareketli , 1 adet sabit raf",
  "Teleskop raylı çekmece",
  "5 adet country ayak",
  "3 adet halka şeklinde siyah metal kulp",
  "Ürünün yerle temasını keserek / kaldırarak taşıyınız.",
  "Geniş çalışma yüzeyi",
  "Açık ve kapalı depolama alanları",
  "Dekoratif ve kişiselleştirebilir raf tasarımı",
  "Kolay temizlik imkanı sunan yüksek ayaklar",
  "Estetik ve düzenli bir görünüm sunan kablo kanal",
  "Gövde ile uyumlu kolay temizlik imkanı sunan yüksek ayaklar",
  "5 adet geniş ve kullanışlı raf",
  "Eşyalarınızı kolayca organize edebileceğiniz 3 çekmeceli depolama alanı",
  "1 adet geniş askı borusu",
  "1 adet geniş 1 adet dar sabit raf",
  "3 adet dar hareketli raf",
  "3 adet metal siyah country kulp",
  "Kablo kanalı",
  "2 adet metal siyah country kulp",
  "6 adet country ayak",
  "2 adet geniş askı borusu",
  "2 adet geniş 1 adet dar sabit raf",
  "1 adet geniş 2 adet dar hareketli raf",
  "4 adet metal siyah country kulp",
  "Teleskop raylı 2 adet çekmece",
  "3 adet geniş sabit raf",
  "3 adet geniş hareketli raf",
  "6 adet metal siyah country kulp",
  "Teleskop raylı 3 adet çekmece",
  "3 adet geniş 1 adet dar askı borusu",
  "4 adet geniş 1 adet dar sabit raf",
  "9 adet metal siyah country kulp",
  "2 adet teleskop raylı çekmece",
  "4 adet country ayak",
  "2 adet metal siyeh country kulp",
  "Teleskop raylı 4 adet geniş çekmece",
  "1 adet halka şeklinde siyah metal kulp",
  "100x200 yatak ile uyumlu",
  "Saklama ihtiyacını karşılamak için bazalı sistem",
  "4 Adet Country ayak",
  "Açılır masa mekanizması",
  "Geniş, derin ve kullanışlı",
  "Newyork ofis mobilyaları ile uyumludur.",
  "2 adet kilitlenebilir kapak",
  "2 Adet kilitlenebilir kısa kapak",
  "Ürün 3 adet hareketli olmak üzere toplam 4 raf 5 bölümden oluşmaktadır",
  "Sağlam kilit mekanizması",
  "Newyork ofis mobilyaları ile uyumlu",
  "Ürün 3 adet hareketli olmak üzere toplam 4 raf 5 bölümden oluşmaktadır.",
  "9 çift ayakkabı , terlik kapasiteli",
  "Günlük eşyaları kolayca gizleyebileceğiniz 2 kapaklı depolama alanı ve 4 bölmeli modül içi tasarım",
  "Kolay temizlik imkanı",
  "Çizilmelere ve darbelere dayanıklı elektrostatik boyalı yüksek metal ayak",
  "Dayanıklı metal gövde",
  "Dayanıklı profil gövde",
  "Metal kulp detayı",
  "Pratik kullanım sunan çekmece",
  "Modern ve zamansız tasarımıyla yatak odalarına sade bir şıklık kazandırır.",
  "3 kapılı yapısı sayesinde geniş ve düzenli bir depolama alanı sunar.",
  "Askı bölmesi ve raflı iç düzeni ile kıyafetlerinizi kolayca organize etmenizi sağlar.",
  "Yüksek kaliteli, melamin kaplı yonga levhadan üretilmiştir.",
  "E1 standartlarında, insan sağlığına zararsız malzeme kullanılmıştır.",
  "Mat beyaz yüzeyi ile ferah ve aydınlık bir görünüm oluşturur.",
  "Dayanıklı menteşe ve bağlantı elemanları uzun ömürlü kullanım sağlar.",
  "Ürün demonte olarak gönderilir, kurulum için gerekli tüm aksesuarlar paket içeriğinde yer alır.",
  "Kolay temizlenebilir yüzeye sahiptir.",
  "Kapaklı ve çekmeceli gövde yapısı",
  "Kapak yüzeylerinde estetik bir görünüm sunan zarif çıta detayları",
  "Çekmece kapak yüzeylerinde estetik bir görünüm sunan zarif çıta detayları",
  "2 adet çok amaçlı dekoratif kutu çekmece",
  "Özel tasarım 14 mm metal ayak",
  "2 adet sabit geniş raf",
  "3 adet hareketli geniş raf",
  "Dekoratif raf tasarımı",
  "Estetik ve düzenli bir görünüm sunan kablo kanalı",
  "Deterjanları koymak için çok amaçlı dolap",
  "Zemine zarar vermeyecek ayaklar",
  "Ürün; 1.kalite dayanıklı ve silinebilir şönil kumaş kaplama, dayanıklı açılır mekanizma ve yaylardn oluşmaktadır.",
  "Godiva / Mermer Desen",
  "Pool TV ünitesine uyumlu tamamlayıcı depolama modülü",
  "2 bölmeli modül içi tasarım",
  "Hareketli raflarla geniş kullanım alanı",
  "Ergonomik kullanıma uygun geniş, derin ve kullanışlı iç tasarım",
  "6 adet kullanışlı raf",
  "1 adet dayanıklı metal askı borusu",
  "Kaliteli bağlantı parçaları sayesinde sessiz kapaklar",
  "5 adet kullanışlı raf",
  "Kaliteli bağlantı parçaları sayesinde sessiz kapak",
  "Özel köşe bağlantıları sayesinde çökme ve dağılma yapmayan gövde yapısı",
  "Uyumlu yatak ölçüleri 100cm - 200 cm' dir",
  "Üst tabla ile kontrast renkte tasarlanan gizli çekmece",
  "Bas-Aç kapak mekanizmalı 2 adet çekmece",
  "Ek depolama alanı sağlayan iki adet çekmece",
  "Dayanıklı, geniş ve estetik papuç",
  "Ofis ya da ev ortamında kullanılabilir çok amaçlı 8 bölmeli kitaplık",
  "Açık raf sistemi sayesinde kolay erişim",
  "Ofis ya da ev ortamında kullanılabilir",
  "Oturum Yüksekliği (Ayaklar Dâhil) : 41 cm",
  "Oturum Derinliği (Yastıklar Sırtta) : 52 cm",
  "Oturum Genişliği (Kollar Hariç) : 100 cm",
  "Sırt yüksekliği (Sırt Yaslanma) : 40 cm",
  "Yatak Ölçüsü : Özellik Yok",
  "Ayak Adet : 4 Adet",
  "Ayak Yüksekliği : 7 cm",
  "İskelet : Ürün iç aksamı taşıyıcı kısımlarda %100 kereste, düz döşeme bölümleri yonga levha ile desteklenerek üretilmiştir. Ayak monte edilen kısımlarda taşıyıcıları desteklemek adına %100 masif kereste kullanmıştır.",
  "Ayak : Ayaklar kalıplarda hazırlanan taşıyıcı kapasitesi yüksek sert plastikten üretilmiştir.",
  "Sünger: Oturum süngerleri 12 cm 28DNSSoft Sünger Gri.",
  "Yastık : Şeker kırpıntı süngerden üretilen dolgu malzemesidir. Sırt yastıkları ürün kumasından 10 cm façalı olarak hazırlanmıştır.",
  "Kumaş: Kumaş % 100 yerli üretim dokuma polyester ve pamuk karışımıdır.",
  "Uygunluk : Çevre ve çocuk sağlığına uygun malzemeler ile üretilmiştir.",
  "Paket : Mobilya ambalajı ile paketlenmiş ve toz girmesini önleyici ince naylon ile korunmuştur.",
  "Paket Adet: Ürün 1 paket olarak gönderilmektedir.",
  "Kurulum: Ürün ayakları demonte olarak gönderilmektedir.",
  "Montaj: Ürün ayaklarını şarjlı tornavida ile monte edebilirsiniz.",
  "İçerik: Ayaklar ve bağlantı elemanları ürün paketinden çıkmaktadır.",
  "Açılabillir özellikli fonksiyonel yemek masası",
  "Alt tabla genişlik : 32 cm",
  "Malzeme : 1 mm boru profil ve 2 mm sac"
];
const rows = [];
const add = (index, en, ru, ar) => rows.push({ tr: source[index], en, ru, ar });

add(0, "Recessed handles", "Утопленные ручки", "مقابض غائرة");
add(1, "Small round holes in the back panel help prevent odours", "Небольшие круглые отверстия в задней стенке помогают предотвратить появление запахов", "فتحات دائرية صغيرة في اللوح الخلفي للمساعدة على منع تكون الروائح");
add(2, "Updated sliding rail mechanism", "Обновлённый механизм направляющих раздвижных дверей", "آلية سكك انزلاق محدثة");
add(3, "Multipurpose use: bathroom, kitchen, office, balcony", "Многоцелевое использование: ванная, кухня, офис, балкон", "استخدامات متعددة: الحمام والمطبخ والمكتب والشرفة");
add(4, "Capacity for 24 pairs of shoes or slippers", "Вместимость: 24 пары обуви или тапочек", "تتسع لـ 24 زوجًا من الأحذية أو النعال");
add(5, "Attractive legs", "Эстетичные ножки", "أرجل أنيقة");
add(6, "Multipurpose use: bathroom, kitchen, office, balcony", "Многоцелевое использование: ванная, кухня, офис, балкон", "استخدامات متعددة: الحمام والمطبخ والمكتب والشرفة");
add(7, "Sonoma / Multicoloured", "Сонома / Разноцветный", "سونوما / متعدد الألوان");
add(8, "Desk with drawer pedestal", "Письменный стол с тумбой", "مكتب مع وحدة أدراج");
add(9, "Its ergonomic, stylish design allows use as both a writing desk and a computer desk", "Эргономичный и стильный дизайн позволяет использовать его как письменный и компьютерный стол", "يتيح تصميمه المريح والأنيق استخدامه مكتبًا للكتابة أو للكمبيوتر");
add(10, "Stylish, practical shelves", "Стильные и практичные полки", "رفوف أنيقة وعملية");
add(11, "5 spacious shelves", "5 вместительных полок", "5 رفوف واسعة");
add(12, "Quality solid-wood texture", "Качественная фактура массива дерева", "ملمس خشب مصمت عالي الجودة");
add(13, "Durable hook", "Прочный крючок", "خطاف متين");
add(14, "Break-resistant trouser hanger", "Устойчивая к поломке вешалка для брюк", "علاقة بنطلونات مقاومة للكسر");
add(15, "One pack contains 5 items", "В одной упаковке 5 изделий", "تحتوي العبوة الواحدة على 5 قطع");
add(16, "The product consists of 5 hangers in 1 box.", "Комплект состоит из 5 вешалок в 1 коробке.", "يتكون المنتج من 5 علاقات في صندوق واحد.");
add(17, "Sonoma / Mixed", "Сонома / Смешанный", "سونوما / مختلط");
add(18, "Natural wood texture paired with lacquer-gloss white", "Сочетание натуральной древесной фактуры и белого цвета с лаковым блеском", "تناسق ملمس الخشب الطبيعي مع اللون الأبيض بلمعان اللاكيه");
add(19, "3 chipboard bed-base panels", "3 панели основания кровати из ДСП", "3 ألواح خشب حبيبي لقاعدة السرير");
add(20, "Compatible mattress size: 90 × 190 cm.", "Подходящий размер матраса: 90 × 190 см.", "مقاس المرتبة المتوافق: 90 × 190 سم.");
add(21, "Compatible mattress size: 100 × 200 cm.", "Подходящий размер матраса: 100 × 200 см.", "مقاس المرتبة المتوافق: 100 × 200 سم.");
add(22, "Sonoma Multicoloured", "Сонома разноцветный", "سونوما متعدد الألوان");
add(23, "Sonoma frame paired with a coloured headboard", "Корпус цвета сонома в сочетании с цветным изголовьем", "هيكل بلون سونوما متناسق مع لوح رأس ملون");
add(24, "2 chipboard bed-base panels", "2 панели основания кровати из ДСП", "لوحان من الخشب الحبيبي لقاعدة السرير");
add(25, "Features attractive retro-style legs.", "Оснащено эстетичными ножками в стиле ретро.", "مزود بأرجل أنيقة بطراز ريترو.");
add(26, "1 repositionable decorative X-shaped shelf", "1 переставляемая декоративная полка в форме X", "رف زخرفي واحد على شكل X قابل لتغيير موضعه");
add(27, "2 repositionable decorative diagonal shelves", "2 переставляемые декоративные диагональные полки", "رفان زخرفيان مائلان قابلان لتغيير موضعهما");
add(28, "2 lockable doors", "2 запираемые дверцы", "بابان قابلان للقفل");
add(29, "Compatible with office furniture", "Сочетается с офисной мебелью", "متوافق مع أثاث المكاتب");
add(30, "Additional shelf below the hanging rail", "Дополнительная полка под штангой для одежды", "رف إضافي أسفل علاقة الملابس");
add(31, "Capacity for 35 pairs of shoes or slippers", "Вместимость: 35 пар обуви или тапочек", "تتسع لـ 35 زوجًا من الأحذية أو النعال");
add(32, "Tempered glass above the drawer", "Закалённое стекло над ящиком", "زجاج مقسى فوق الدرج");
add(33, "2 spacious internal compartments", "2 вместительных внутренних отделения", "حجرتان داخليتان واسعتان");
add(34, "Create different combinations with other shelf models and colours", "Можно создавать различные сочетания с другими моделями и цветами полок", "يمكن تكوين تنسيقات مختلفة مع موديلات الرفوف وألوانها الأخرى");
add(35, "Stylish coloured handles", "Стильные цветные ручки", "مقابض ملونة أنيقة");
add(36, "Drawer with telescopic slides", "Ящик на телескопических направляющих", "درج بسكك تلسكوبية");
add(37, "Multipurpose use", "Многоцелевое использование", "استخدامات متعددة");
add(38, "Made from bamboo.", "Изготовлено из бамбука.", "مصنوع من الخيزران.");
add(39, "4 compartments, including 1 for hanging long garments", "4 отделения, включая 1 для длинной одежды на вешалках", "4 حجرات، منها حجرة واحدة لتعليق الملابس الطويلة");
add(40, "2 wide and 1 narrow durable metal hanging rails", "2 широкие и 1 узкая прочные металлические штанги для одежды", "قضيبان عريضان وقضيب ضيق لتعليق الملابس من معدن متين");
add(41, "2 wide and 1 narrow fixed shelves", "2 широкие и 1 узкая несъёмные полки", "رفان عريضان ورف ضيق ثابتة");
add(42, "Soft-close sliding-door mechanism prevents doors from slamming; quality fittings", "Раздвижной механизм с доводчиком предотвращает резкое закрывание дверей; качественная фурнитура", "آلية أبواب منزلقة بإغلاق هادئ تمنع ارتطام الأبواب؛ قطع تثبيت عالية الجودة");
add(43, "2 wide adjustable shelves", "2 широкие переставляемые полки", "رفان عريضان قابلان للتعديل");
add(44, "Cable-routing hole", "Отверстие для прокладки кабелей", "فتحة لتمرير الكابلات");
add(45, "1 wide, tall drawer", "1 широкий высокий ящик", "درج واحد عريض ومرتفع");
add(46, "TV area dimensions: width 117 cm, depth 40 cm", "Размеры места для телевизора: ширина 117 см, глубина 40 см", "أبعاد مساحة وضع التلفاز: العرض 117 سم، العمق 40 سم");
add(47, "Latte / Soft White", "Латте / Мягкий белый", "لاتيه / أبيض ناعم");
add(48, "Natural wood texture paired with soft white", "Сочетание натуральной древесной фактуры и мягкого белого цвета", "تناسق ملمس الخشب الطبيعي مع الأبيض الناعم");
add(49, "Modern, sturdy, glossy white legs, 15 cm high", "Современные прочные ножки глянцевого белого цвета высотой 15 см", "أرجل عصرية متينة باللون الأبيض اللامع بارتفاع 15 سم");
add(50, "2 cable outlets", "2 отверстия для вывода кабелей", "فتحتان لإخراج الكابلات");
add(51, "2 sliding doors", "2 раздвижные дверцы", "بابان منزلقان");
add(52, "Open shelving with 2 compartments", "Открытая полка с 2 отделениями", "رف مفتوح بحجرتين");
add(53, "Professional seat mechanism with four functions", "Профессиональный механизм сиденья с четырьмя функциями", "آلية مقعد احترافية بأربع وظائف");
add(54, "Adjustable neck and lumbar support", "Регулируемая поддержка шеи и поясницы", "دعم قابل للتعديل للرقبة وأسفل الظهر");
add(55, "Height-adjustable armrests", "Подлокотники с регулировкой высоты", "مساند ذراعين قابلة لتعديل الارتفاع");
add(56, "Adjustable backrest angle with locking function", "Регулировка угла наклона спинки с фиксацией", "زاوية مسند ظهر قابلة للتعديل والتثبيت");
add(57, "Seat depth adjusts forwards and backwards", "Регулировка глубины сиденья вперёд и назад", "عمق مقعد قابل للتعديل للأمام والخلف");
add(58, "Breathable ergonomic mesh backrest", "Эргономичная спинка из воздухопроницаемой сетки", "مسند ظهر شبكي مريح يسمح بمرور الهواء");
add(59, "Wide, comfortable seat cushion", "Широкая удобная подушка сиденья", "وسادة مقعد واسعة ومريحة");
add(60, "Gas lift and star base meeting BIFMA standards", "Газлифт и крестовина по стандартам BIFMA", "رافعة غازية وقاعدة نجمية وفق معايير BIFMA");
add(61, "Quiet, parquet-safe castors with 360° rotation", "Бесшумные колёсики с поворотом на 360°, не царапающие паркет", "عجلات هادئة تدور بزاوية 360° ولا تخدش الباركيه");
add(62, "Durable plywood seat structure", "Прочная фанерная конструкция сиденья", "هيكل مقعد متين من الخشب الرقائقي");
add(63, "Easy assembly", "Простая сборка", "سهل التجميع");
add(64, "Multipurpose portable tray", "Многофункциональный переносной поднос", "صينية محمولة متعددة الاستخدامات");
add(65, "Folding legs allow compact storage.", "Складные ножки позволяют экономить место при хранении.", "توفر الأرجل القابلة للطي مساحة عند التخزين.");
add(66, "Multipurpose use: balcony, garden, kitchen, office", "Многоцелевое использование: балкон, сад, кухня, офис", "استخدامات متعددة: الشرفة والحديقة والمطبخ والمكتب");
add(67, "Note: Do not place hot pots, kettles or similar hot items directly on the surface. Loading more than 15 kg, standing on it or using it as a ladder may be dangerous.", "Примечание: не ставьте горячие кастрюли, чайники и подобные горячие предметы прямо на поверхность. Нагрузка свыше 15 кг, вставание на изделие или использование его в качестве лестницы могут быть опасны.", "ملاحظة: لا تضع القدور أو أباريق الشاي الساخنة وما شابهها مباشرة على السطح. قد يكون وضع حمولة تزيد على 15 كجم أو الوقوف عليه أو استخدامه سلمًا أمرًا خطيرًا.");
add(68, "Can also be used as a coat or storage cupboard at home or in the office.", "Также можно использовать дома или в офисе как шкаф для верхней одежды или хранения вещей.", "يمكن استخدامه أيضًا خزانة للمعاطف أو للتخزين في المنزل أو المكتب.");
add(69, "2 fixed units", "2 неподвижных элемента", "قطعتان ثابتتان");
add(70, "Door with aluminium strip", "Дверца с алюминиевой полосой", "باب بشريط من الألومنيوم");
add(71, "8 compartments, including 1 for hanging long garments", "8 отделений, включая 1 для длинной одежды на вешалках", "8 حجرات، منها حجرة واحدة لتعليق الملابس الطويلة");
add(72, "Matt chrome handles", "Ручки из матового хрома", "مقابض كروم مطفية");
add(73, "Wide, attractive round black legs that protect the floor", "Широкие эстетичные круглые чёрные ножки, не повреждающие пол", "أرجل سوداء مستديرة عريضة وأنيقة لا تضر الأرضية");
add(74, "Metal handles", "Металлические ручки", "مقابض معدنية");
add(75, "Can also be used as a coat or storage cupboard at home or in the office", "Также можно использовать дома или в офисе как шкаф для верхней одежды или хранения вещей", "يمكن استخدامه أيضًا خزانة للمعاطف أو للتخزين في المنزل أو المكتب");
add(76, "1 fixed upper shelf and 1 wide adjustable lower shelf", "1 несъёмная верхняя и 1 широкая переставляемая нижняя полка", "رف علوي ثابت ورف سفلي عريض قابل للتعديل");
add(77, "Sturdy frame", "Прочный корпус", "هيكل متين");
add(78, "One pack contains 8 items", "В одной упаковке 8 изделий", "تحتوي العبوة الواحدة على 8 قطع");
add(79, "The product consists of 8 hangers in 1 box.", "Комплект состоит из 8 вешалок в 1 коробке.", "يتكون المنتج من 8 علاقات في صندوق واحد.");

add(80, "Designed for home and office use", "Дизайн для дома и офиса", "تصميم مناسب للاستخدام في المنزل والمكتب");
add(81, "12 hanging points provide ample capacity for coats, hats, bags and accessories", "12 мест для подвешивания обеспечивают большую вместимость для пальто, шляп, сумок и аксессуаров", "12 موضعًا للتعليق توفر سعة كبيرة للمعاطف والقبعات والحقائب والإكسسوارات");
add(82, "Compact, space-saving design with a 51 cm base diameter", "Компактная конструкция с диаметром основания 51 см экономит место", "تصميم مدمج يوفر المساحة بقاعدة قطرها 51 سم");
add(83, "185 cm height accommodates long garments", "Высота 185 см подходит для длинной одежды", "ارتفاع 185 سم يناسب الملابس الطويلة");
add(84, "Rotating head makes hanging and retrieving items easy", "Вращающаяся верхняя часть позволяет легко вешать и снимать вещи", "رأس دوار يسهل تعليق الأغراض وأخذها");
add(85, "Metal supports provide increased stability", "Металлические опоры повышают устойчивость", "دعامات معدنية تعزز الثبات");
add(86, "Lightweight structure makes it easy to move", "Лёгкая конструкция удобна для переноски", "هيكل خفيف يسهل نقله");
add(87, "Designed for durability with a solid-wood-textured structure and metal support parts.", "Конструкция с фактурой массива дерева и металлическими опорными деталями рассчитана на долговечное использование.", "مصمم للاستخدام المتين بهيكل ذي ملمس خشب مصمت وقطع دعم معدنية.");
add(88, "The components contain no substances harmful to human health and are made from materials suitable for everyday use.", "Компоненты не содержат вредных для здоровья веществ и изготовлены из материалов, подходящих для повседневного использования.", "لا تحتوي مكونات المنتج على مواد ضارة بصحة الإنسان، وهي مصنوعة من مواد مناسبة للاستخدام اليومي.");
add(89, "12 hanging points", "12 мест для подвешивания", "12 موضعًا للتعليق");
add(90, "Ample capacity for coats, hats, bags and accessories", "Большая вместимость для пальто, шляп, сумок и аксессуаров", "سعة كبيرة للمعاطف والقبعات والحقائب والإكسسوارات");
add(91, "Compact structure with a 51 cm base diameter", "Компактная конструкция с диаметром основания 51 см", "هيكل مدمج بقاعدة قطرها 51 سم");
add(92, "Rotating head for easy use", "Вращающаяся верхняя часть для удобства использования", "رأس دوار لسهولة الاستخدام");
add(93, "1 enclosed shoe compartment with 3 shelves", "1 закрытое отделение для обуви с 3 полками", "حجرة أحذية واحدة بباب و3 رفوف");
add(94, "1 additional shelf above the hanging rail", "1 дополнительная полка над штангой для одежды", "رف إضافي واحد فوق علاقة الملابس");
add(95, "Capacity for 12 pairs of shoes or slippers", "Вместимость: 12 пар обуви или тапочек", "تتسع لـ 12 زوجًا من الأحذية أو النعال");
add(96, "Additional shelf below the hanging rail", "Дополнительная полка под штангой для одежды", "رف إضافي أسفل علاقة الملابس");
add(97, "Capacity for 32 pairs of shoes or slippers", "Вместимость: 32 пары обуви или тапочек", "تتسع لـ 32 زوجًا من الأحذية أو النعال");
add(98, "Capacity for 28 pairs of shoes or slippers", "Вместимость: 28 пар обуви или тапочек", "تتسع لـ 28 زوجًا من الأحذية أو النعال");
add(99, "10 compartments behind the doors", "10 отделений за дверцами", "10 حجرات خلف الأبواب");
add(100, "8 adjustable units", "8 переставляемых элементов", "8 قطع قابلة للتعديل");
add(101, "Stylish chrome handles and attractive round legs", "Стильные хромированные ручки и эстетичные круглые ножки", "مقابض كروم أنيقة وأرجل مستديرة جميلة");
add(102, "Capacity for 32 pairs of shoes or slippers", "Вместимость: 32 пары обуви или тапочек", "تتسع لـ 32 زوجًا من الأحذية أو النعال");
add(103, "Asymmetric decorative door", "Асимметричная декоративная дверца", "باب زخرفي غير متماثل");
add(104, "8 adjustable shelves and 1 fixed shelf", "8 переставляемых и 1 несъёмная полка", "8 رفوف قابلة للتعديل ورف واحد ثابت");
add(105, "Corner connector", "Угловой соединитель", "وصلة زاوية");
add(106, "1 chipboard bed-base panel", "1 панель основания кровати из ДСП", "لوح خشب حبيبي واحد لقاعدة السرير");
add(107, "MDF profile legs fixed to the frame", "Ножки из профиля МДФ, закреплённые на корпусе", "أرجل من قطاعات MDF مثبتة بالهيكل");
add(108, "Metal-framed", "С металлическим каркасом", "بإطار معدني");
add(109, "Decorative wall unit with two shelves", "Декоративный настенный модуль с двумя полками", "وحدة حائط زخرفية برفين");
add(110, "Create individual combinations with different colours or shelves", "Возможность создавать индивидуальные сочетания с разными цветами или полками", "إمكانية ابتكار تنسيقات مميزة بألوان أو رفوف مختلفة");
add(111, "3 wide fixed shelves", "3 широкие несъёмные полки", "3 رفوف عريضة ثابتة");
add(112, "4 wide fixed shelves", "4 широкие несъёмные полки", "4 رفوف عريضة ثابتة");
add(113, "With its comfortable design and elegant details, the Boston Executive Chair brings quality and style to office life.", "Благодаря удобному дизайну и изящным деталям кресло руководителя Boston привносит качество и стиль в офисную жизнь.", "يضيف كرسي المدير Boston الجودة والأناقة إلى أجواء المكتب بتصميمه المريح وتفاصيله الراقية.");
add(114, "Provides ergonomic support during long working hours, with durable materials for years of use.", "Обеспечивает эргономичную поддержку во время долгой работы, а прочные материалы рассчитаны на многолетнее использование.", "يوفر دعمًا مريحًا خلال ساعات العمل الطويلة، مع مواد متينة للاستخدام لسنوات.");
add(115, "Ergonomic Design", "Эргономичный дизайн", "تصميم مريح");
add(116, "The high backrest helps protect spinal health.", "Высокая спинка помогает сохранять здоровье позвоночника.", "يساعد مسند الظهر المرتفع على الحفاظ على صحة العمود الفقري.");
add(117, "Lumbar support fills the lower-back curve during long periods of sitting.", "Поясничная опора поддерживает изгиб поясницы при длительном сидении.", "يسند دعم أسفل الظهر تقوس المنطقة القطنية أثناء الجلوس لفترات طويلة.");
add(118, "Provides excellent back and shoulder support for a proper sitting position.", "Обеспечивает отличную поддержку спины и плеч для правильной посадки.", "يوفر دعمًا ممتازًا للظهر والكتفين للحفاظ على وضعية جلوس سليمة.");
add(119, "Durable Faux-Leather Upholstery", "Прочная обивка из искусственной кожи", "تنجيد متين من الجلد الصناعي");
add(120, "Soft, quality faux-leather upholstery creates a luxurious appearance.", "Мягкая качественная обивка из искусственной кожи придаёт роскошный вид.", "يمنح التنجيد الناعم عالي الجودة من الجلد الصناعي مظهرًا فاخرًا.");
add(121, "A stain-resistant, easy-to-clean surface makes everyday use practical.", "Устойчивая к пятнам и простая в уходе поверхность удобна в повседневном использовании.", "يوفر السطح المقاوم للبقع والسهل التنظيف استخدامًا عمليًا.");
add(122, "Resistant to wear and tearing.", "Устойчиво к истиранию и разрывам.", "مقاوم للتآكل والتمزق.");
add(123, "Soft Foam Padding", "Мягкое пенное наполнение", "حشوة إسفنجية ناعمة");
add(124, "High-density foam padding resists sagging during prolonged sitting.", "Наполнитель из пены высокой плотности не проседает при длительном сидении.", "تحافظ الحشوة الإسفنجية عالية الكثافة على شكلها دون هبوط أثناء الجلوس الطويل.");
add(125, "Provides maximum comfort in both the seat cushion and backrest.", "Обеспечивает максимальный комфорт сиденья и спинки.", "يوفر أقصى درجات الراحة في وسادة المقعد ومسند الظهر.");
add(126, "A special breathable mesh-fabric layer beneath the seat and back cushions adds ventilation.", "Специальный промежуточный слой из воздухопроницаемой сетчатой ткани под подушками сиденья и спинки обеспечивает вентиляцию.", "تضيف طبقة خاصة من النسيج الشبكي المسامي أسفل وسادتي المقعد والظهر تهوية إضافية.");
add(127, "Adjustable Height and Backrest Recline Mechanism", "Регулировка высоты и механизм наклона спинки", "ارتفاع قابل للتعديل وآلية إمالة مسند الظهر");
add(128, "The gas-lift system makes seat height easy to adjust to the user.", "Система газлифта позволяет легко настроить высоту сиденья под пользователя.", "يتيح نظام الرفع الغازي ضبط ارتفاع المقعد بسهولة حسب المستخدم.");
add(129, "Offers flexibility to achieve the right desk height during long periods of sitting.", "Позволяет подобрать правильную высоту относительно стола при длительном сидении.", "يوفر مرونة للوصول إلى الارتفاع المناسب للمكتب أثناء الجلوس الطويل.");
add(130, "The backrest recline angle can be locked in the desired position or left free.", "Угол наклона спинки можно зафиксировать в нужном положении или оставить свободным.", "يمكن تثبيت زاوية إمالة مسند الظهر في الوضع المطلوب أو تركها حرة الحركة.");
add(131, "360° Swivel", "Вращение на 360°", "دوران بزاوية 360°");
add(132, "The 360-degree swivel mechanism allows free movement around the workspace.", "Механизм вращения на 360 градусов обеспечивает свободу движений на рабочем месте.", "تتيح آلية الدوران بزاوية 360 درجة حرية الحركة في مساحة العمل.");
add(133, "Easy changes of direction allow quicker access to different areas.", "Лёгкая смена направления ускоряет доступ к разным зонам.", "يسهل تغيير الاتجاه للوصول بسرعة إلى مناطق مختلفة.");
add(134, "Soft-Padded Armrests", "Подлокотники с мягкой обивкой", "مساند ذراعين مبطنة وناعمة");
add(135, "Rounded ergonomic armrests provide extra support for the arms.", "Округлые эргономичные подлокотники обеспечивают дополнительную поддержку рук.", "توفر مساند الذراعين المستديرة والمريحة دعمًا إضافيًا للذراعين.");
add(136, "Designed at an angle that supports a natural sitting position.", "Спроектировано под углом, поддерживающим естественное положение при сидении.", "مصمم بزاوية تدعم وضعية الجلوس الطبيعية.");
add(137, "Soft foam padding is enclosed in durable faux-leather upholstery.", "Под прочной обивкой из искусственной кожи находится мягкий пенный наполнитель.", "تحتوي الكسوة المتينة من الجلد الصناعي على حشوة إسفنجية ناعمة.");
add(138, "Sturdy Star Base and Quiet Castors", "Прочная крестовина и бесшумные колёсики", "قاعدة نجمية متينة وعجلات هادئة");
add(139, "The solid plastic star base provides a sturdy, durable foundation.", "Цельная пластиковая крестовина обеспечивает прочную и долговечную опору.", "توفر القاعدة النجمية البلاستيكية المصمتة أساسًا قويًا ومتينًا.");
add(140, "5 castors provide quiet movement without leaving marks.", "5 колёсиков обеспечивают бесшумное передвижение без следов.", "تتيح 5 عجلات حركة هادئة دون ترك آثار.");
add(141, "Moves easily over parquet, carpet and tiled floors.", "Легко перемещается по паркету, ковру и плитке.", "يتحرك بسهولة على الباركيه والسجاد والبلاط.");
add(142, "1 drawer with a push-to-open mechanism", "1 ящик с механизмом открывания нажатием", "درج واحد بآلية فتح بالضغط");
add(143, "Suitable for both home and office use", "Подходит для дома и офиса", "مناسب للاستخدام في المنزل والمكتب");
add(144, "Tabletop working area: 110 × 70", "Рабочая поверхность столешницы: 110 × 70", "مساحة استخدام السطح العلوي: 110 × 70");
add(145, "Folding retro-style legs", "Складные ножки в стиле ретро", "أرجل قابلة للطي بطراز ريترو");
add(146, "Made from 16 mm particleboard.", "Изготовлено из ДСП толщиной 16 мм.", "مصنوع من ألواح خشب حبيبي بسماكة 16 مم.");
add(147, "CLICK TO VIEW OUR CHAIR MODELS.", "НАЖМИТЕ, ЧТОБЫ ПОСМОТРЕТЬ НАШИ МОДЕЛИ КРЕСЕЛ.", "اضغط لعرض موديلات الكراسي لدينا.");
add(148, "1 lockable drawer", "1 запираемый ящик", "درج واحد قابل للقفل");
add(149, "Two people are recommended for assembly.", "Рекомендуется собирать изделие вдвоём.", "يوصى بتجميع المنتج بواسطة شخصين.");
add(150, "Lacquer White", "Лаковый белый", "أبيض لاكيه");
add(151, "6 adjustable shelves and 1 fixed shelf in the enclosed compartment", "6 переставляемых и 1 несъёмная полка в закрытом отделении", "6 رفوف قابلة للتعديل ورف ثابت داخل الحجرة ذات الباب");
add(152, "Multipurpose use: bathroom, kitchen, office", "Многоцелевое использование: ванная, кухня, офис", "استخدامات متعددة: الحمام والمطبخ والمكتب");
add(153, "Special triangular leg", "Специальная треугольная ножка", "رجل مثلثة خاصة");
add(154, "The door can be fitted on the right or left as preferred", "Дверцу можно установить справа или слева по желанию", "يمكن تركيب الباب على اليمين أو اليسار حسب الرغبة");
add(155, "1 fixed shelf and 3 adjustable shelves", "1 несъёмная и 3 переставляемые полки", "رف ثابت و3 رفوف قابلة للتعديل");
add(156, "The storage-base system provides additional storage space.", "Система основания с нишей обеспечивает дополнительное место для хранения.", "يوفر نظام قاعدة السرير مساحة تخزين إضافية.");
add(157, "Compatible mattress size: 90 × 190 cm.", "Подходящий размер матраса: 90 × 190 см.", "مقاس المرتبة المتوافق: 90 × 190 سم.");
add(158, "1 drawer with a spacious compartment", "1 ящик с вместительным отделением", "درج واحد بحجرة واسعة");
add(159, "Multipurpose use: bathroom, kitchen, office", "Многоцелевое использование: ванная, кухня, офис", "استخدامات متعددة: الحمام والمطبخ والمكتب");

add(160, "5 adjustable shelves inside the wide enclosed compartment", "5 переставляемых полок в широком закрытом отделении", "5 رفوف قابلة للتعديل داخل الحجرة العريضة ذات الباب");
add(161, "3 adjustable shelves inside the narrow enclosed compartment", "3 переставляемые полки в узком закрытом отделении", "3 رفوف قابلة للتعديل داخل الحجرة الضيقة ذات الباب");
add(162, "Stylish matt chrome handles", "Стильные ручки из матового хрома", "مقابض أنيقة من الكروم المطفي");
add(163, "Multipurpose use: bathroom, kitchen, office", "Многоцелевое использование: ванная, кухня, офис", "استخدامات متعددة: الحمام والمطبخ والمكتب");
add(164, "2 enclosed compartments and a drawer provide convenient use", "2 закрытых отделения и ящик обеспечивают удобство использования", "حجرتان بأبواب ودرج لاستخدام عملي ومريح");
add(165, "Chrome-plated knob", "Хромированная ручка-кнопка", "مقبض دائري مطلي بالكروم");
add(166, "Multipurpose cupboard for the bathroom, kitchen, office, pantry, hallway, balcony, etc.", "Многофункциональный шкаф для ванной, кухни, офиса, кладовой, прихожей, балкона и т. д.", "خزانة متعددة الاستخدامات للحمام والمطبخ والمكتب والمخزن والمدخل والشرفة وغيرها");
add(167, "3 adjustable shelves and 1 fixed shelf provide convenient use", "3 переставляемые и 1 несъёмная полка обеспечивают удобство использования", "3 رفوف قابلة للتعديل ورف ثابت لاستخدام مريح");
add(168, "Multipurpose cupboard for the bathroom, kitchen, office, etc.", "Многофункциональный шкаф для ванной, кухни, офиса и т. д.", "خزانة متعددة الاستخدامات للحمام والمطبخ والمكتب وغيرها");
add(169, "Cupboard door can be fitted on the right or left", "Дверцу шкафа можно установить справа или слева", "يمكن تركيب باب الخزانة على اليمين أو اليسار");
add(170, "1 adjustable shelf inside the special enclosed compartment", "1 переставляемая полка в специальном закрытом отделении", "رف واحد قابل للتعديل داخل الحجرة الخاصة ذات الباب");
add(171, "5 drawers provide convenient use", "5 ящиков обеспечивают удобство использования", "5 أدراج لاستخدام مريح");
add(172, "Castors make it easy to move", "Колёсики позволяют легко перемещать изделие", "عجلات تسهل النقل");
add(173, "Special enclosed compartment and drawer in lacquer-gloss white provide convenient use", "Специальное закрытое отделение и ящик белого цвета с лаковым блеском обеспечивают удобство использования", "حجرة خاصة بباب ودرج باللون الأبيض بلمعان اللاكيه لاستخدام مريح");
add(174, "Multipurpose cupboard for the bathroom, kitchen, office, pantry, hallway, balcony, etc.", "Многофункциональный шкаф для ванной, кухни, офиса, кладовой, прихожей, балкона и т. д.", "خزانة متعددة الاستخدامات للحمام والمطبخ والمكتب والمخزن والمدخل والشرفة وغيرها");
add(175, "Middle section dimensions: 69 × 40.5 × 35 cm (width × height × depth)", "Размеры средней секции: 69 × 40,5 × 35 см (ширина × высота × глубина)", "أبعاد القسم الأوسط: 69 × 40.5 × 35 سم (العرض × الارتفاع × العمق)");
add(176, "Special enclosed compartment provides convenient use", "Специальное закрытое отделение обеспечивает удобство использования", "حجرة خاصة بباب لاستخدام مريح");
add(177, "1 fixed shelf and 2 adjustable shelves in the enclosed compartment", "1 несъёмная и 2 переставляемые полки в закрытом отделении", "رف ثابت ورفان قابلان للتعديل داخل الحجرة ذات الباب");
add(178, "Open compartment with 1 fixed shelf and 1 adjustable shelf", "Открытое отделение с 1 несъёмной и 1 переставляемой полкой", "حجرة مفتوحة برف ثابت ورف قابل للتعديل");
add(179, "Multipurpose use: bathroom, kitchen, office, balcony, hallway, room", "Многоцелевое использование: ванная, кухня, офис, балкон, прихожая, комната", "استخدامات متعددة: الحمام والمطبخ والمكتب والشرفة والمدخل والغرفة");
add(180, "Castors make it easy to move", "Колёсики позволяют легко перемещать изделие", "عجلات تسهل النقل");
add(181, "Compartment with 4 shelves in total, 3 of them adjustable", "Отделение с 4 полками, из которых 3 переставляемые", "حجرة تضم 4 رفوف إجمالًا، منها 3 قابلة للتعديل");
add(182, "1 basket compartment with a drop-down door", "1 отделение с корзиной и откидной дверцей", "حجرة واحدة بسلة وباب يفتح إلى الأسفل");
add(183, "4 tall decorative legs", "4 высокие декоративные ножки", "4 أرجل زخرفية مرتفعة");
add(184, "Multipurpose use: bathroom, kitchen, balcony, hallway, room", "Многоцелевое использование: ванная, кухня, балкон, прихожая, комната", "استخدامات متعددة: الحمام والمطبخ والشرفة والمدخل والغرفة");
add(185, "2 drawers without runners that can be used as decorative boxes", "2 ящика без направляющих, которые можно использовать как декоративные коробки", "درجان دون سكك يمكن استخدامهما صندوقين للزينة");
add(186, "Multipurpose use: bathroom, kitchen, balcony, hallway, room", "Многоцелевое использование: ванная, кухня, балкон, прихожая, комната", "استخدامات متعددة: الحمام والمطبخ والشرفة والمدخل والغرفة");
add(187, "Internal module layout with 4 compartments", "Внутренняя конструкция модуля с 4 отделениями", "تصميم داخلي للوحدة بأربع حجرات");
add(188, "Oslo Walnut", "Орех Осло", "جوز أوسلو");
add(189, "Complements the desk", "Дополняет письменный стол", "يكمل مكتب العمل");
add(190, "Can be wall-mounted", "Можно закрепить на стене", "يمكن تثبيته على الحائط");
add(191, "2 compartments with push-to-open doors", "2 отделения с дверцами, открывающимися нажатием", "حجرتان بأبواب تفتح بالضغط");
add(192, "1 compartment above the drawer", "1 отделение над ящиком", "حجرة واحدة فوق الدرج");
add(193, "1 hanging rail", "1 штанга для одежды", "قضيب واحد لتعليق الملابس");
add(194, "2 hanging rails", "2 штанги для одежды", "قضيبان لتعليق الملابس");
add(195, "Fixed shelf in the middle section", "Несъёмная полка в средней секции", "رف ثابت في القسم الأوسط");
add(196, "Optional adjustable shelves", "Дополнительные переставляемые полки", "رفوف قابلة للتعديل اختيارية");
add(197, "Special enclosed compartment and drawer provide convenient use", "Специальное закрытое отделение и ящик обеспечивают удобство использования", "حجرة خاصة بباب ودرج لاستخدام مريح");
add(198, "Adjustable shelf", "Переставляемая полка", "رف قابل للتعديل");
add(199, "Multipurpose cupboard", "Многофункциональный шкаф", "خزانة متعددة الاستخدامات");
add(200, "For the bathroom, kitchen, office, etc.; castors make it easy to move", "Для ванной, кухни, офиса и т. д.; колёсики позволяют легко перемещать изделие", "للحمام والمطبخ والمكتب وغيرها؛ عجلات تسهل النقل");
add(201, "11 compartments behind the doors", "11 отделений за дверцами", "11 حجرة خلف الأبواب");
add(202, "9 adjustable shelves and 1 fixed shelf", "9 переставляемых и 1 несъёмная полка", "9 رفوف قابلة للتعديل ورف ثابت");
add(203, "Drawer with telescopic slides", "Ящик на телескопических направляющих", "درج بسكك تلسكوبية");
add(204, "5 country-style legs", "5 ножек в стиле кантри", "5 أرجل بطراز ريفي");
add(205, "3 black metal ring handles", "3 чёрные металлические ручки-кольца", "3 مقابض حلقية من المعدن الأسود");
add(206, "Lift the product clear of the floor when moving it.", "При перемещении поднимайте изделие над полом.", "ارفع المنتج عن الأرض عند نقله.");
add(207, "Spacious work surface", "Просторная рабочая поверхность", "سطح عمل واسع");
add(208, "Open and enclosed storage areas", "Открытые и закрытые места для хранения", "مساحات تخزين مفتوحة ومغلقة");
add(209, "Decorative, customisable shelf design", "Декоративный дизайн полок с возможностью персонализации", "تصميم رفوف زخرفي قابل للتخصيص");
add(210, "Tall legs make cleaning easy", "Высокие ножки облегчают уборку", "أرجل مرتفعة تسهل التنظيف");
add(211, "Cable channel for a neat, attractive appearance", "Кабель-канал для аккуратного и эстетичного вида", "قناة كابلات لمظهر أنيق ومرتب");
add(212, "Tall legs that match the frame and make cleaning easy", "Высокие ножки в тон корпуса облегчают уборку", "أرجل مرتفعة متناسقة مع الهيكل تسهل التنظيف");
add(213, "5 spacious, practical shelves", "5 вместительных практичных полок", "5 رفوف واسعة وعملية");
add(214, "Storage area with 3 drawers for organising belongings easily", "Место для хранения с 3 ящиками для удобной организации вещей", "مساحة تخزين بثلاثة أدراج لتسهيل ترتيب أغراضك");
add(215, "1 wide hanging rail", "1 широкая штанга для одежды", "قضيب عريض واحد لتعليق الملابس");
add(216, "1 wide and 1 narrow fixed shelf", "1 широкая и 1 узкая несъёмная полка", "رف عريض ورف ضيق ثابتان");
add(217, "3 narrow adjustable shelves", "3 узкие переставляемые полки", "3 رفوف ضيقة قابلة للتعديل");
add(218, "3 black metal country-style handles", "3 чёрные металлические ручки в стиле кантри", "3 مقابض من المعدن الأسود بطراز ريفي");
add(219, "Cable channel", "Кабель-канал", "قناة كابلات");
add(220, "2 black metal country-style handles", "2 чёрные металлические ручки в стиле кантри", "مقبضان من المعدن الأسود بطراز ريفي");
add(221, "6 country-style legs", "6 ножек в стиле кантри", "6 أرجل بطراز ريفي");
add(222, "2 wide hanging rails", "2 широкие штанги для одежды", "قضيبان عريضان لتعليق الملابس");
add(223, "2 wide and 1 narrow fixed shelves", "2 широкие и 1 узкая несъёмные полки", "رفان عريضان ورف ضيق ثابتة");
add(224, "1 wide and 2 narrow adjustable shelves", "1 широкая и 2 узкие переставляемые полки", "رف عريض ورفان ضيقان قابلة للتعديل");
add(225, "4 black metal country-style handles", "4 чёрные металлические ручки в стиле кантри", "4 مقابض من المعدن الأسود بطراز ريفي");
add(226, "2 drawers with telescopic slides", "2 ящика на телескопических направляющих", "درجان بسكك تلسكوبية");
add(227, "3 wide fixed shelves", "3 широкие несъёмные полки", "3 رفوف عريضة ثابتة");
add(228, "3 wide adjustable shelves", "3 широкие переставляемые полки", "3 رفوف عريضة قابلة للتعديل");
add(229, "6 black metal country-style handles", "6 чёрных металлических ручек в стиле кантри", "6 مقابض من المعدن الأسود بطراز ريفي");
add(230, "3 drawers with telescopic slides", "3 ящика на телескопических направляющих", "3 أدراج بسكك تلسكوبية");
add(231, "3 wide and 1 narrow hanging rails", "3 широкие и 1 узкая штанги для одежды", "3 قضبان عريضة وقضيب ضيق لتعليق الملابس");
add(232, "4 wide and 1 narrow fixed shelves", "4 широкие и 1 узкая несъёмные полки", "4 رفوف عريضة ورف ضيق ثابتة");
add(233, "9 black metal country-style handles", "9 чёрных металлических ручек в стиле кантри", "9 مقابض من المعدن الأسود بطراز ريفي");
add(234, "2 drawers with telescopic slides", "2 ящика на телескопических направляющих", "درجان بسكك تلسكوبية");
add(235, "4 country-style legs", "4 ножки в стиле кантри", "4 أرجل بطراز ريفي");
add(236, "2 black metal country-style handles", "2 чёрные металлические ручки в стиле кантри", "مقبضان من المعدن الأسود بطراز ريفي");
add(237, "4 wide drawers with telescopic slides", "4 широких ящика на телескопических направляющих", "4 أدراج عريضة بسكك تلسكوبية");
add(238, "1 black metal ring handle", "1 чёрная металлическая ручка-кольцо", "مقبض حلقي واحد من المعدن الأسود");
add(239, "Compatible with a 100 × 200 mattress", "Подходит для матраса 100 × 200", "متوافق مع مرتبة بمقاس 100 × 200");

add(240, "Storage-base system meets storage needs", "Основание с нишей для хранения вещей", "نظام قاعدة بمساحة تخزين يلبي احتياجات التخزين");
add(241, "4 country-style legs", "4 ножки в стиле кантри", "4 أرجل بطراز ريفي");
add(242, "Extendable table mechanism", "Механизм раздвижения стола", "آلية تمديد الطاولة");
add(243, "Wide, deep and practical", "Широкое, глубокое и практичное исполнение", "واسع وعميق وعملي");
add(244, "Compatible with Newyork office furniture.", "Сочетается с офисной мебелью Newyork.", "متوافق مع أثاث المكاتب Newyork.");
add(245, "2 lockable doors", "2 запираемые дверцы", "بابان قابلان للقفل");
add(246, "2 short lockable doors", "2 короткие запираемые дверцы", "بابان قصيران قابلان للقفل");
add(247, "The product has 4 shelves in total, 3 of them adjustable, forming 5 compartments", "В изделии 4 полки, из которых 3 переставляемые, образующие 5 отделений", "يحتوي المنتج على 4 رفوف إجمالًا، منها 3 قابلة للتعديل، لتكوين 5 حجرات");
add(248, "Sturdy locking mechanism", "Прочный запирающий механизм", "آلية قفل متينة");
add(249, "Compatible with Newyork office furniture", "Сочетается с офисной мебелью Newyork", "متوافق مع أثاث المكاتب Newyork");
add(250, "The product has 4 shelves in total, 3 of them adjustable, forming 5 compartments.", "В изделии 4 полки, из которых 3 переставляемые, образующие 5 отделений.", "يحتوي المنتج على 4 رفوف إجمالًا، منها 3 قابلة للتعديل، لتكوين 5 حجرات.");
add(251, "Capacity for 9 pairs of shoes or slippers", "Вместимость: 9 пар обуви или тапочек", "تتسع لـ 9 أزواج من الأحذية أو النعال");
add(252, "Two-door storage area keeps everyday belongings out of sight, with a 4-compartment internal layout", "Место для хранения за двумя дверцами позволяет убрать повседневные вещи с глаз; внутри 4 отделения", "مساحة تخزين ببابين لإخفاء الأغراض اليومية بسهولة، مع تصميم داخلي بأربع حجرات");
add(253, "Easy to clean", "Легко очищается", "سهل التنظيف");
add(254, "Tall metal leg with an electrostatic coating resistant to scratches and impacts", "Высокая металлическая ножка с электростатическим покрытием, устойчивым к царапинам и ударам", "رجل معدنية مرتفعة بطلاء كهروستاتيكي مقاوم للخدوش والصدمات");
add(255, "Durable metal frame", "Прочный металлический каркас", "هيكل معدني متين");
add(256, "Durable profile frame", "Прочный каркас из профиля", "هيكل متين من القطاعات");
add(257, "Metal handle detail", "Деталь в виде металлической ручки", "تفصيل بمقبض معدني");
add(258, "Drawer for practical use", "Практичный ящик", "درج لاستخدام عملي");
add(259, "Its modern, timeless design brings understated elegance to bedrooms.", "Современный дизайн вне времени придаёт спальне сдержанную элегантность.", "يضفي تصميمه العصري الذي يحتفظ برونقه أناقة بسيطة على غرف النوم.");
add(260, "The three-door design offers spacious, organised storage.", "Трёхдверная конструкция обеспечивает вместительное и упорядоченное хранение.", "يوفر التصميم بثلاثة أبواب مساحة تخزين واسعة ومنظمة.");
add(261, "The hanging compartment and shelved interior make clothes easy to organise.", "Отделение со штангой и внутренние полки помогают удобно организовать одежду.", "تسهل حجرة التعليق والتنظيم الداخلي بالرفوف ترتيب ملابسك.");
add(262, "Made from high-quality melamine-faced particleboard.", "Изготовлено из высококачественной ДСП с меламиновым покрытием.", "مصنوع من ألواح خشب حبيبي عالية الجودة ومكسوة بالميلامين.");
add(263, "Uses materials meeting E1 standards that are harmless to human health.", "Использованы безопасные для здоровья материалы стандарта E1.", "تستخدم مواد وفق معايير E1 وغير ضارة بصحة الإنسان.");
add(264, "The matt white surface creates a fresh, bright appearance.", "Матовая белая поверхность создаёт свежий и светлый облик.", "يمنح السطح الأبيض المطفي مظهرًا مشرقًا ومنعشًا.");
add(265, "Durable hinges and fittings ensure long-lasting use.", "Прочные петли и крепёжные элементы обеспечивают длительный срок службы.", "توفر المفصلات وقطع التثبيت المتينة استخدامًا طويل الأمد.");
add(266, "The product is supplied flat-packed; all accessories required for assembly are included in the package.", "Изделие поставляется в разобранном виде; вся необходимая для сборки фурнитура входит в комплект.", "يأتي المنتج مفككًا، وتشمل العبوة جميع الملحقات اللازمة للتجميع.");
add(267, "Has an easy-to-clean surface.", "Имеет поверхность, которую легко очищать.", "يتميز بسطح سهل التنظيف.");
add(268, "Frame with doors and drawers", "Корпус с дверцами и ящиками", "هيكل بأبواب وأدراج");
add(269, "Elegant moulding details give the door surfaces an attractive appearance", "Изящные планки придают поверхностям дверей эстетичный вид", "تفاصيل شرائح أنيقة تمنح أسطح الأبواب مظهرًا جميلًا");
add(270, "Elegant moulding details give the drawer fronts an attractive appearance", "Изящные планки придают фасадам ящиков эстетичный вид", "تفاصيل شرائح أنيقة تمنح واجهات الأدراج مظهرًا جميلًا");
add(271, "2 multipurpose decorative box drawers", "2 многофункциональных декоративных ящика-короба", "درجان صندوقيان زخرفيان متعددا الاستخدامات");
add(272, "Specially designed 14 mm metal leg", "Металлическая ножка специального дизайна, 14 мм", "رجل معدنية بتصميم خاص، 14 مم");
add(273, "2 wide fixed shelves", "2 широкие несъёмные полки", "رفان عريضان ثابتان");
add(274, "3 wide adjustable shelves", "3 широкие переставляемые полки", "3 رفوف عريضة قابلة للتعديل");
add(275, "Decorative shelf design", "Декоративный дизайн полок", "تصميم رفوف زخرفي");
add(276, "Cable channel for a neat, attractive appearance", "Кабель-канал для аккуратного и эстетичного вида", "قناة كابلات لمظهر أنيق ومرتب");
add(277, "Multipurpose cupboard for storing detergents", "Многофункциональный шкаф для хранения моющих средств", "خزانة متعددة الاستخدامات لوضع المنظفات");
add(278, "Floor-safe legs", "Ножки, не повреждающие пол", "أرجل لا تضر الأرضية");
add(279, "The product features first-quality durable, wipe-clean chenille upholstery, a durable opening mechanism and springs.", "Изделие состоит из прочной обивки из шенилла первого сорта, допускающей протирание, прочного механизма раскладывания и пружин.", "يتكون المنتج من كسوة شينيل متينة وعالية الجودة قابلة للمسح، وآلية فتح متينة ونوابض.");
add(280, "Godiva / Marble Pattern", "Годива / Мраморный рисунок", "غوديفا / نقش رخامي");
add(281, "Complementary storage module compatible with the Pool TV unit", "Дополнительный модуль хранения, совместимый с ТВ-тумбой Pool", "وحدة تخزين مكملة ومتوافقة مع وحدة التلفاز Pool");
add(282, "Internal module layout with 2 compartments", "Внутренняя конструкция модуля с 2 отделениями", "تصميم داخلي للوحدة بحجرتين");
add(283, "Adjustable shelves offer versatile space", "Переставляемые полки расширяют возможности использования пространства", "توفر الرفوف القابلة للتعديل مساحة استخدام واسعة");
add(284, "Wide, deep and practical interior designed for ergonomic use", "Широкое, глубокое и практичное внутреннее пространство для удобного использования", "تصميم داخلي واسع وعميق وعملي لاستخدام مريح");
add(285, "6 practical shelves", "6 практичных полок", "6 رفوف عملية");
add(286, "1 durable metal hanging rail", "1 прочная металлическая штанга для одежды", "قضيب معدني متين واحد لتعليق الملابس");
add(287, "Quality fittings ensure quiet doors", "Качественная фурнитура обеспечивает бесшумную работу дверей", "قطع تثبيت عالية الجودة تجعل حركة الأبواب هادئة");
add(288, "5 practical shelves", "5 практичных полок", "5 رفوف عملية");
add(289, "Quality fittings ensure a quiet door", "Качественная фурнитура обеспечивает бесшумную работу дверцы", "قطع تثبيت عالية الجودة تجعل حركة الباب هادئة");
add(290, "Special corner joints keep the frame from sagging or coming apart", "Специальные угловые соединения предотвращают проседание и расшатывание корпуса", "تمنع وصلات الزوايا الخاصة هبوط الهيكل أو تفككه");
add(291, "Compatible mattress size: 100 × 200 cm", "Подходящий размер матраса: 100 × 200 см", "مقاس المرتبة المتوافق: 100 × 200 سم");
add(292, "Concealed drawer in a colour contrasting with the top panel", "Скрытый ящик контрастного по отношению к верхней панели цвета", "درج مخفي بلون متباين مع اللوح العلوي");
add(293, "2 drawers with push-to-open mechanisms", "2 ящика с механизмом открывания нажатием", "درجان بآلية فتح بالضغط");
add(294, "Two drawers provide additional storage space", "Два ящика обеспечивают дополнительное место для хранения", "درجان يوفران مساحة تخزين إضافية");
add(295, "Durable, wide and attractive foot pad", "Прочный, широкий и эстетичный подпятник", "قاعدة رجل متينة وعريضة وأنيقة");
add(296, "Multipurpose 8-compartment bookcase for office or home use", "Многофункциональный стеллаж с 8 отделениями для офиса или дома", "مكتبة متعددة الاستخدامات بثماني حجرات للمكتب أو المنزل");
add(297, "Open shelving provides easy access", "Открытые полки обеспечивают лёгкий доступ", "نظام رفوف مفتوحة يسهل الوصول إلى الأغراض");
add(298, "Suitable for office or home use", "Подходит для офиса или дома", "مناسب للاستخدام في المكتب أو المنزل");
add(299, "Seat height (including legs): 41 cm", "Высота сиденья (с ножками): 41 см", "ارتفاع المقعد (شامل الأرجل): 41 سم");
add(300, "Seat depth (with cushions against the backrest): 52 cm", "Глубина сиденья (с подушками у спинки): 52 см", "عمق المقعد (مع الوسائد عند مسند الظهر): 52 سم");
add(301, "Seat width (excluding armrests): 100 cm", "Ширина сиденья (без подлокотников): 100 см", "عرض المقعد (دون مسندي الذراعين): 100 سم");
add(302, "Backrest height: 40 cm", "Высота спинки: 40 см", "ارتفاع مسند الظهر: 40 سم");
add(303, "Bed dimensions: not specified", "Размер спального места: не указан", "أبعاد السرير: غير محددة");
add(304, "Number of legs: 4", "Количество ножек: 4", "عدد الأرجل: 4");
add(305, "Leg height: 7 cm", "Высота ножек: 7 см", "ارتفاع الأرجل: 7 سم");
add(306, "Frame: The internal load-bearing sections are made from 100% timber, with flat upholstered sections reinforced with particleboard. The areas where the legs attach use 100% solid timber to reinforce the supports.", "Каркас: внутренние несущие части изготовлены из 100% пиломатериала, плоские обивочные участки усилены ДСП. В местах крепления ножек для усиления опор используется 100% массив дерева.", "الهيكل: تصنع الأجزاء الداخلية الحاملة من خشب بنسبة 100%، مع تدعيم أقسام التنجيد المسطحة بألواح خشب حبيبي. ويستخدم خشب مصمت بنسبة 100% في مواضع تثبيت الأرجل لتعزيز الدعامات.");
add(307, "Legs: Moulded from hard plastic with a high load-bearing capacity.", "Ножки: изготовлены методом формования из твёрдого пластика с высокой несущей способностью.", "الأرجل: مصنوعة من بلاستيك صلب مقولب ذي قدرة تحمل عالية.");
add(308, "Foam: Seat cushions use grey 28 DNS Soft foam, 12 cm thick.", "Пена: в сиденьях используется серая пена 28 DNS Soft толщиной 12 см.", "الإسفنج: وسائد المقعد من إسفنج رمادي ناعم 28 DNS بسماكة 12 سم.");
add(309, "Cushions: Filled with fine shredded foam. The back cushions are made from the product fabric with a 10 cm gusset.", "Подушки: наполнены мелкой пенополиуретановой крошкой. Подушки спинки изготовлены из ткани изделия с боковиной шириной 10 см.", "الوسائد: حشوة من فتات الإسفنج الناعم. تصنع وسائد الظهر من قماش المنتج بجوانب بعرض 10 سم.");
add(310, "Fabric: A woven polyester-and-cotton blend, 100% domestically produced.", "Ткань: тканая смесь полиэстера и хлопка, 100% отечественного производства.", "القماش: نسيج من مزيج البوليستر والقطن، من إنتاج محلي بنسبة 100%.");
add(311, "Suitability: Made from materials suitable for environmental and child health.", "Безопасность: изготовлено из материалов, безопасных для окружающей среды и здоровья детей.", "الملاءمة: مصنوع من مواد ملائمة للبيئة وصحة الأطفال.");
add(312, "Packaging: Packed in furniture packaging and protected by a thin plastic film to keep dust out.", "Упаковка: мебельная упаковка с защитной тонкой полиэтиленовой плёнкой, предотвращающей попадание пыли.", "التغليف: مغلف بعبوة مخصصة للأثاث ومحمي بغشاء بلاستيكي رقيق لمنع دخول الغبار.");
add(313, "Package count: The product comes in 1 package.", "Количество упаковок: изделие поставляется в 1 упаковке.", "عدد العبوات: يأتي المنتج في عبوة واحدة.");
add(314, "Assembly: The product legs are supplied unattached.", "Сборка: ножки изделия поставляются отдельно, без установки.", "التركيب: تأتي أرجل المنتج غير مثبتة.");
add(315, "Assembly: The legs can be fitted using a cordless screwdriver.", "Монтаж: ножки можно установить с помощью аккумуляторного шуруповёрта.", "التجميع: يمكن تثبيت الأرجل باستخدام مفك براغي لاسلكي.");
add(316, "Contents: The legs and fasteners are included in the product package.", "Комплектация: ножки и крепёжные элементы находятся в упаковке изделия.", "المحتويات: الأرجل وقطع التثبيت مرفقة داخل عبوة المنتج.");
add(317, "Functional dining table with an extending feature", "Функциональный обеденный стол с возможностью раздвижения", "طاولة طعام عملية قابلة للتمديد");
add(318, "Lower panel width: 32 cm", "Ширина нижней панели: 32 см", "عرض اللوح السفلي: 32 سم");
add(319, "Material: 1 mm tubular profile and 2 mm sheet metal", "Материал: трубный профиль 1 мм и листовой металл 2 мм", "المادة: قطاعات أنبوبية بسماكة 1 مم وصفائح معدنية بسماكة 2 مم");

export const extraTranslationsB = rows;
