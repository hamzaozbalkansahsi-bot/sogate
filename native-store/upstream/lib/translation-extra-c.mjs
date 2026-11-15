// Exact technical specifications from the audited source list (indices 766–954).
const source = [
  "Geniş kullanışlı, açılır kapanır bölme",
  "Dekoratif makyaj aynası",
  "3 bölmeli masa üstü raf",
  "Dayanıklı ve Ergonomik Tasarım:",
  "Çelik iskelet ve 125 dereceye kadar arakaya yaslanma mekanizması, sağlam ve dayanıklı bir yapı sunar.",
  "Ergonomik tasarımı ve benzersiz ayak uzatma eki uzun oyun seansları boyunca mükemmel konfor sağlar.",
  "Uzun Süre Oturuma Uygun Yüksek Yoğunlukta Sünger:",
  "Temizlenebilir ve uzun ömürlü yüksek kaliteli özel tasarım Sentetik Deri kaplaması ile şıklığı bir araya getirir.",
  "Ayarlanabilir Özellikler:",
  "Yukarı aşağı yükseklik ayarı ve arkaya yaslanma kilit kontrolü ile kişisel konforunuzu ayarlayın.",
  "Ayak uzatma ileri-geri ayarı, 360 derece dönebilme özelliği ve 4 farklı renk seçeneği ile kişiselleştirme imkanları sınırsız.",
  "Ergonomik Tasarımlı Kolçaklar:",
  "2D (yukarı-aşağı ve ileri-geri) yumuşak yüzey kaplamalı ergonomik tasarımlı kolçaklar, kollarınızı doğru destekleyerek oyun performansınızı artırır.",
  "Ekstra Konfor Özellikleri:",
  "İsteğe göre takılıp çıkartılabilir bel ve boyun yastıkları, kişisel tercihlerinize göre konforu özelleştirme fırsatı sunar.",
  "Yüksek Kalite ve Güvenilirlik:",
  "3. sınıf uzun ömürlü yükseklik ayar amortisörü ve dayanıklı 35 cm çapında çelik yıldız ayak, ProX modelimizin kalitesini vurgular.",
  "Naylon kaplama 5cm çapında sessiz çalışan tekerler, zeminlere zarar vermeden sorunsuz hareket sağlar.",
  "Adore Gaming ProX Oyuncu Koltuğu, dayanıklılık, konfor ve şıklığı bir araya getirerek oyun dünyasında yeni bir standart belirliyor. Bu muhteşem koltukla, oyun deneyiminizin tadını çıkarın!",
  "Modern ve şık retro tasarım",
  "2 adet geniş ve kullanışlı raf",
  "Sürgü kapaklı yapı ile pratik kullanım",
  "Ev ve ofis kullanımına uygundur",
  "Konforlu tasarımı ve zarif detaylarıyla Boston Yönetici Koltuğu, ofis yaşamına kalite ve şıklık katar. Uzun çalışma saatlerinde ergonomik destek sunarken, dayanıklı malzemeleriyle de yıllarca kullanım sağlar.",
  "Kumanda kontrolü ile kalkış desteği",
  "Kullanışlı cep (kitap, dergi, telefon vb. için)",
  "120 dereceye kadar geriye yatma özelliği",
  "Ürün; yırtılmalara, aşınmaya ve solmaya karşı dayanıklı, nem emilimi yüksek ve silinebilir kumaş ve dayanıklı açılır mekanizma ve yaylardan oluşmaktadır.",
  "Yırtılmalara, aşınmaya ve solmaya karşı dayanıklı, nem emilimi yüksek ve silinebilir kumaş.",
  "1. kalite dayanıklı açılır mekanizma ve yaylar",
  "Ürün kurulumu için 1 kişi tavsiye edilmektedir.",
  "Oturma yüksekliği, kullanıcının ihtiyaçlarına göre kolayca ayarlanabilir.",
  "360 derece dönebilen yapısı ve sessiz, dayanıklı tekerlekleri sayesinde özgürce hareket edebilirsiniz.",
  "Yüksek kaliteli metal ayaklık ve dayanıklı ekose kumaş döşeme malzemesi.",
  "Siyah metal ayaklar, sağlamlık ve denge sağlarken modern bir dokunuş katar.",
  "Üst kısımda yer alan açık raf bölümleri, kitaplar, defterler, kırtasiye malzemeleri ve dekoratif eşyalar için ideal bir alan sunar.",
  "Kablolar için özel bir çıkış bölmesi, düzenli bir görünüm sağlar ve kablo karmaşasını önler.",
  "Masanın altındaki çapraz metal destekler, ekstra sağlamlık sağlar ve uzun süreli dayanıklılık sunar.",
  "Metal ayakların uçlarındaki vidalı pabuçlar zemin eğriliklerine karşı masanızı dengeli durmasına yardımcı olur ve parke gibi sert yüzeyleri çizmez.",
  "Doğal ahşap ve siyah metal kombinasyonu, modern, minimalist ve endüstriyel dekorasyon tarzlarına uyum sağlar.",
  "Kompakt yapısı, dar alanlarda dahi düzenli ve verimli bir çalışma alanı oluşturmanıza olanak tanır.",
  "Bel Destek Sistemi: Sırt kısmındaki özel bel desteği, omurgayı doğal kıvrımında tutarak bel ağrısı riskini en aza indirir. Özellikle uzun oturma sürelerinde vücut duruşunu korumaya yardımcı olur.",
  "Baş Desteği: Ayarlanabilir başlık, boyun ve baş bölgesine destek sağlayarak konforu artırır ve doğru oturma pozisyonunu destekler.",
  "Nefes Alabilir Kumaş: Hava akışını sağlayan file kumaş, terlemeyi önler ve uzun süreli kullanımlarda serin bir deneyim sunar.",
  "Dayanıklılık: Yüksek kaliteli file malzeme, uzun ömürlü bir kullanım için tasarlanmıştır ve deformasyona karşı dayanıklıdır.",
  "Yüksek Yoğunluklu Sünger: Geniş ve yumuşak oturma yüzeyi, ağırlığı eşit şekilde dağıtarak rahat bir oturma deneyimi sunar.",
  "Ergonomik Tasarım: Yastığın ön kısmındaki hafif eğim, bacaklara baskıyı azaltır ve kan dolaşımını destekler.",
  "Koltuk Açısı: Geri yaslanma özelliği, çalışırken veya dinlenirken farklı oturma pozisyonları sağlar.Geri yaslanma özelliği açılıp kapatılabilir.",
  "Katlanabilir ve Ayarlanabilir Kollar: Kullanıcının rahatlığına göre kolları yukarıya kaldırarak veya aşağıya indirerek ergonomik bir çalışma alanı oluşturabilirsiniz.",
  "360 Derece Dönüş: Koltuğun tabanı tam tur dönebilecek şekilde tasarlanmıştır, böylece hareket kabiliyetinizi artırır.",
  "Sessiz ve Dayanıklı Tekerlekler: Zemin üzerinde çizik bırakmadan hareket eder, ahşap, halı veya seramik gibi farklı zemin tiplerine uygundur.",
  "Sağlam Yıldız Ayak: Sağlam ve dayanıklı 5 kollu kalıp metal ayak yapısı,",
  "Fileli Sırtlık:",
  "Koltuk Minderi:",
  "Ayarlanabilir Fonksiyonlar:",
  "Kollar:",
  "Geniş ve Dayanıklı Yıldız Ayak:",
  "Sağlam Yıldız Ayak: Sağlam ve dayanıklı 5 kollu kalıp metal ayak yapısı.",
  "Sırt kısmında terletmeyen file kumaş",
  "Özel tasarım estetik görünümlü ve ergonomik bel desteği, estetik görünümlü katlanabilir kolçaklar",
  "Dayanıklı, özel kalıp yüksek dansite oturum minderi",
  "Kilitlenebilir yükseklik ve geriye yaslanma mekanizması",
  "1. Kalite uzun ömürlü yükseklik ayar amortisörü",
  "Estetik, çizilmelere karşı dayanıklı metal yıldız ayak",
  "Uzun ömürlü, zemin çizmeyen sessiz tekerler",
  "Kolay ve hızlı kurulum özelliği",
  "Elektrikli recliner mekanizması ile sırt yaslama ve ayak uzatma fonksiyonu",
  "Kumanda ile tek tuşla kolay ve zahmetsiz kullanım",
  "Şarjlı pil veya elektrik kablosu ile kullanım imkanı",
  "Yumuşak dokulu, dayanıklı ve uzun ömürlü döşemelik kumaş",
  "Vücudu destekleyen ergonomik sırt ve oturum yapısı",
  "Geniş ve konforlu kol dayama alanları",
  "Sağlam metal iskelet ve dayanıklı mekanizma yapısı",
  "Konfor ve Uyarlanabilirlik:",
  "Yukarı aşağı yükseklik ayarı, bel destek yukarı-aşağı ayarı",
  "İş gününüzü en iyi şekilde geçirebilmeniz için tasarlanmış bir oturma deneyimi",
  "Estetik ve Şık Tasarım:",
  "Modern ve profesyonel bir atmosfer oluşturan estetik sırt tasarımı",
  "Başlık Ayarı ve Ekstra Destek:",
  "Başlık yaslama yukarı-aşağı ayarı ile ekstra destek ve rahatlık",
  "Bel ve sırt destek ayarı ile ergonomik oturuş pozisyonunu destekleyen özellikler",
  "Dayanıklı Tekerlekler:",
  "Sessiz ve pürüzsüz hareket sağlayan tekerlekler ile sağlam metal demonte yıldız ayak uzun yıllar güvenle kullanım imkânı sunar.",
  "Kolay Bakım ve Temizlik:",
  "Yumuşak yüzey kaplamalı malzemeler, kolay temizlik ve bakım sağlar",
  "Ofis ortamında temiz ve düzenli bir görünümü sürdürmek için ideal malzemeler",
  "Profesyonellik ve Performans:",
  "İş performansınıza olumlu bir etki sağlayarak verimliliğinizi artırır",
  "Ayarlanabilir Yükseklik Ayarı:",
  "Yukarı aşağı yükseklik ayarı",
  "Arkaya yaslanma sertlik ayarı, gününüzü koltuğunuzun size özel konforunu ayarlamakla geçirebilmenizi sağlar",
  "Yumuşak Yüzey Kaplamalı Kolçaklar:",
  "Estetik ve ergonomik yumuşak yüzey kaplamalı kolçaklar, çalışma süresince rahat bir destek sunar",
  "Kolay temizlenebilir malzemeler, koltuğunuzun uzun ömürlü ve bakımlı kalmasını sağlar",
  "Dayanıklı Tekerlerler:",
  "360 Derece Hareket Kabiliyeti:",
  "360 derece hareket kabiliyeti, ofis içinde özgürce iletişim kurabilmenize yardımcı olur",
  "İşlevselliği ve kolay kullanımı ile Base Çalışma Sandalyesi, hem evde hem de işte yaşamınızı kolaylaştırır",
  "3 adet askı bölmesi",
  "2 adet fonksiyonel geniş çekmece",
  "Polimer Kompozit Ayak",
  "2 adet makine bölmesi",
  "Sürgülü tabla sistemi",
  "Dayanıklı gövde yapısı",
  "Hem ev hem ofis kullanımına uygunluk",
  "Su ve sıcak ile uzun süreli temasından kaçının. Nemli bir bezle temizlenebilir.",
  "Uzun süreli kullanıma uygun kaliteli döşeme",
  "4 adet geniş ve kullanışlı raf",
  "İki kapaklı yapı ile pratik kullanım",
  "Kapak içi bölme",
  "Estetik metal kulp",
  "5 adet metal askı",
  "Oval köşeli tasarım",
  "Metal destek aparatı",
  "10 adet raf bölmesi",
  "4 adet metal askı",
  "1 adet askı üstü raf",
  "Minderli oturma alanı",
  "3 adet estetik ve sağlam metal askı aparatı",
  "3 bölmeli alt dolap",
  "1 adet açık bölme",
  "Şerit led aydınlatma",
  "Estetik kulp",
  "2 adet kullanışlı raf",
  "Zemine zarar vermeyecek MDF malzemeye uyumlu profil ayak",
  "10 adet bölme",
  "Metal estetik kulp",
  "2 adet metal askı",
  "Çizilmelere ve darbelere dayanıklı metal ayak",
  "Çok bölmeli depolama alanı",
  "Geniş üst yüzey",
  "5 geniş bölme",
  "2 askı",
  "Özel tasarım metal kulp",
  "Geniş alt raf ile ekstra depolama alanı",
  "Dayanıklı ve sağlam ayak yapısı",
  "İki renkli modern tasarım",
  "Geniş ve kullanışlı yüzey",
  "Köşe kullanımına uygun fonksiyonel tasarım",
  "1 adet aynalı kapak",
  "5 adet raf alanı",
  "2 ayrı elbise askı bölümü",
  "Üst ve alt bölümlerde askılık alanı",
  "Geniş ve kullanışlı iç hacim",
  "Vücut Ağırlığına Duyarlı Mekanizma: Yeni nesil mekanizma, kullanıcının vücut ağırlığına göre sırt yaslanma direncini dengeler ve daha kontrollü bir oturma deneyimi sunar.",
  "Kademeli Kilitlenebilir Sırtlık: Sırt yaslanma mekanizması farklı kademelerde kilitlenerek çalışma ve dinlenme sırasında tercih edilen oturma pozisyonunun ayarlanmasını sağlar.",
  "Yüksek Dansite Oturum Süngeri: Ergonomik ve dayanıklı yüksek dansite sünger, uzun süreli kullanımlarda konforlu bir oturma alanı sunar ve formunu korumaya yardımcı olur.",
  "Nefes Alabilen File Sırtlık: Dayanıklı file yüzey, hava dolaşımını destekleyerek uzun süreli kullanımlarda daha ferah bir oturma deneyimi sağlar.",
  "Ayarlanabilir Bel Desteği: Kullanıcının oturma pozisyonuna göre ayarlanabilen bel desteği, sırt ve bel bölgesinin desteklenmesine yardımcı olur.",
  "Ayarlanabilir Kolçaklar: Yumuşak PU yüzeye sahip kolçaklar yukarı ve aşağı yönde ayarlanarak kolların çalışma alanına uygun konumlandırılmasını sağlar.",
  "Dayanıklı Metal Yıldız Ayak: Sağlam metal yıldız ayak yapısı, koltuğun dengeli ve güvenli bir şekilde kullanılmasına yardımcı olur.",
  "Sessiz ve Parke Dostu Tekerlekler: Dayanıklı tekerlekler sessiz ve akıcı hareket sağlarken parke gibi hassas zeminlerde çizilme riskini azaltmaya yardımcı olur.",
  "Ergonomik Tasarım ve Konfor:",
  "Vücut yapısına uyum sağlayan ergonomik sırt tasarımı ve ayarlanabilir bel desteği ile konforlu bir oturma deneyimi sunar. Uzun süreli çalışma saatlerinde sırt ve bel bölgesini destekler.",
  "Ayarlanabilir Başlık Desteği:",
  "Yukarı-aşağı ve ileri-geri ayarlanabilir başlık mekanizması sayesinde baş ve boyun bölgesine kişiselleştirilmiş destek sağlar.",
  "Çok Fonksiyonlu Kolçaklar:",
  "Farklı oturma pozisyonlarına uyum sağlayan çok fonksiyonlu kolçaklar, kolların rahat bir şekilde konumlandırılmasına yardımcı olur.",
  "Ayarlanabilir Bel Desteği:",
  "Ayarlanabilir bel desteği sayesinde kişisel ihtiyaçlara uygun ergonomik oturma pozisyonu oluşturulabilir.",
  "Çok Fonksiyonlu Mekanizma:",
  "Çok fonksiyonlu yeni nesil mekanizma, oturma pozisyonunun kişisel tercihlere göre ayarlanmasına olanak tanır. Yukarı-aşağı mandallı kontrol sistemi ile koltuk yüksekliği kolayca ayarlanabilir.",
  "Oturum Minderi Ayarı:",
  "İleri-geri ayarlanabilir oturum minderi sayesinde oturma derinliği kişisel ihtiyaçlara göre düzenlenebilir. Farklı vücut yapılarına uyum sağlayarak oturma konforunu artırır.",
  "Sırt Yaslanma ve Kilitleme Sistemi:",
  "Sırt yaslanma sertlik ayarı ile yaslanma direnci kişisel tercihlere göre düzenlenebilir. Sırt geri yaslanma kilidi sayesinde istenilen pozisyonda sabitlenebilir.",
  "Sessiz ve Estetik Tekerlekler:",
  "Geniş ve estetik tasarımlı sessiz tekerlekler sayesinde çalışma alanında rahat ve akıcı hareket imkânı sunar.",
  "Modern çizgileri, zarif renk uyumu ve fonksiyonel detaylarıyla ofis ve ev çalışma alanlarına estetik bir görünüm kazandırır.",
  "Ergonomik Tasarım ve Üstün Konfor:",
  "Tam ergonomik yapısı, birbirinden bağımsız ayarlanabilir sırt ve bel desteği sayesinde vücut yapısına uyum sağlayarak konforlu bir oturma deneyimi sunar. Uzun süreli çalışma saatlerinde rahatlığı destekler.",
  "Elektrikli Bel Masajı Özelliği:",
  "Bel desteğine entegre elektrikli masaj ünitesi sayesinde çalışma sırasında ekstra konfor sağlar. Masaj fonksiyonunun kullanılabilmesi için ürünün prize bağlanması gerekmektedir.",
  "Ayarlanabilir Sırt ve Bel Desteği:",
  "Birbirinden bağımsız ayarlanabilen sırt ve bel destekleri, kişisel oturma alışkanlıklarına uyum sağlar. Nefes alabilen file sırtlık ve ayarlanabilir bel desteği ile ergonomik oturma pozisyonunu destekler.",
  "Yeni Nesil Yaslanma Mekanizması:",
  "Ayarlanabilir ve kilitlenebilir geriye yaslanma mekanizması sayesinde farklı oturma pozisyonlarına kolayca geçiş yapılabilir. Kullanıcının tercih ettiği pozisyonda sırtlık sabitlenebilir.",
  "Ayarlanabilir Kolçaklar:",
  "Yumuşak PU yüzeye sahip yukarı-aşağı ayarlanabilir kolçaklar, kolların rahatça konumlandırılmasına yardımcı olur. Farklı çalışma masası yüksekliklerine uyum sağlar.",
  "Dayanıklı ve Konforlu Oturum Süngeri:",
  "Ergonomik yapıya sahip dayanıklı yüksek dansiteli oturum süngeri, uzun süreli kullanımlarda konforlu bir oturma alanı sunar.",
  "Nefes Alabilen File Sırtlık:",
  "Dayanıklı ve hava geçirgenliği sağlayan file sırtlık tasarımı, hava dolaşımını destekleyerek uzun çalışma saatlerinde ferah bir kullanım deneyimi sunar.",
  "Estetik ve Dayanıklı Naylon Yıldız Ayak:",
  "Modern tasarıma sahip dayanıklı naylon yıldız ayak, koltuğa sağlam bir temel oluştururken ofis ve ev çalışma alanlarına şık bir görünüm kazandırır.",
  "Sessiz ve Parke Çizmeyen Tekerlekler:",
  "Sessiz hareket sağlayan, parke yüzeyleri çizmeye karşı tasarlanmış dayanıklı tekerlekler sayesinde çalışma alanında rahat ve akıcı hareket imkânı sunar.",
  "Modern ve Fonksiyonel Tasarım:",
  "Şık görünümü, ergonomik detayları ve fonksiyonel özellikleriyle hem profesyonel ofislerde hem de ev çalışma ortamlarında konfor ve estetiği bir araya getirir."
];
const rows = [];
const add = (index, en, ru, ar) => rows.push({ tr: source[index - 766], en, ru, ar });

add(766, "Spacious, practical compartment that opens and closes", "Вместительное практичное открывающееся отделение", "حجرة واسعة وعملية قابلة للفتح والإغلاق");
add(767, "Decorative vanity mirror", "Декоративное зеркало для макияжа", "مرآة زينة للماكياج");
add(768, "Desktop shelf with 3 compartments", "Настольная полка с 3 отделениями", "رف فوق المكتب بثلاث حجرات");
add(769, "Durable, Ergonomic Design:", "Прочная и эргономичная конструкция:", "تصميم متين ومريح:");
add(770, "A steel frame and a reclining mechanism that tilts back up to 125 degrees provide a strong, durable structure.", "Стальной каркас и механизм наклона спинки до 125 градусов обеспечивают прочную и долговечную конструкцию.", "يوفر الهيكل الفولاذي وآلية الإمالة للخلف حتى 125 درجة بنية قوية ومتينة.");
add(771, "The ergonomic design and distinctive footrest extension provide excellent comfort throughout long gaming sessions.", "Эргономичная конструкция и особая выдвижная подставка для ног обеспечивают отличный комфорт во время длительных игровых сеансов.", "يوفر التصميم المريح ومسند القدمين القابل للتمديد والمميز راحة ممتازة خلال جلسات اللعب الطويلة.");
add(772, "High-Density Foam for Prolonged Sitting:", "Пена высокой плотности для длительного сидения:", "إسفنج عالي الكثافة مناسب للجلوس الطويل:");
add(773, "Specially designed, high-quality synthetic-leather upholstery combines style with an easy-to-clean, long-lasting finish.", "Высококачественная обивка из искусственной кожи специального дизайна сочетает стиль, простоту очистки и долговечность.", "يجمع التنجيد المصمم خصيصًا من الجلد الصناعي عالي الجودة بين الأناقة وسهولة التنظيف وطول العمر.");
add(774, "Adjustable Features:", "Регулируемые функции:", "خصائص قابلة للتعديل:");
add(775, "Adjust the height and backrest recline lock for personalised comfort.", "Настраивайте высоту и фиксацию наклона спинки для индивидуального комфорта.", "اضبط الارتفاع وقفل إمالة مسند الظهر لتحقيق راحتك الشخصية.");
add(776, "Forward-and-back footrest adjustment, 360-degree swivel and 4 colour options offer extensive personalisation.", "Регулировка подставки для ног вперёд и назад, вращение на 360 градусов и 4 варианта цвета предоставляют широкие возможности персонализации.", "يوفر ضبط مسند القدمين للأمام والخلف والدوران بزاوية 360 درجة و4 خيارات ألوان إمكانات واسعة للتخصيص.");
add(777, "Ergonomically Designed Armrests:", "Эргономичные подлокотники:", "مساند ذراعين بتصميم مريح:");
add(778, "Soft-surfaced, ergonomic 2D armrests adjust up and down and forwards and backwards, supporting the arms correctly to improve gaming performance.", "Эргономичные подлокотники 2D с мягкой поверхностью регулируются вверх-вниз и вперёд-назад, правильно поддерживая руки для повышения игровой результативности.", "تدعم مساند الذراعين المريحة ذات السطح الناعم والتعديل ثنائي الأبعاد للأعلى والأسفل وللأمام والخلف الذراعين بشكل صحيح لتعزيز أداء اللعب.");
add(779, "Extra Comfort Features:", "Дополнительные функции комфорта:", "خصائص راحة إضافية:");
add(780, "Removable lumbar and neck cushions let you customise comfort to your preferences.", "Съёмные подушки для поясницы и шеи позволяют настроить комфорт по своим предпочтениям.", "تتيح وسادتا أسفل الظهر والرقبة القابلتان للفك والتركيب تخصيص الراحة حسب تفضيلاتك.");
add(781, "High Quality and Reliability:", "Высокое качество и надёжность:", "جودة عالية وموثوقية:");
add(782, "A long-lasting class 3 height-adjustment gas lift and a durable steel star base with a 35 cm diameter highlight the quality of our ProX model.", "Долговечный газлифт 3-го класса для регулировки высоты и прочная стальная крестовина диаметром 35 см подчёркивают качество модели ProX.", "تؤكد الرافعة الغازية طويلة العمر من الفئة 3 لضبط الارتفاع والقاعدة النجمية الفولاذية المتينة بقطر 35 سم جودة موديل ProX.");
add(783, "Quiet nylon-coated castors, 5 cm in diameter, provide smooth movement without damaging floors.", "Бесшумные колёсики с нейлоновым покрытием диаметром 5 см обеспечивают плавное движение без повреждения пола.", "توفر العجلات الهادئة المكسوة بالنايلون بقطر 5 سم حركة سلسة دون إتلاف الأرضيات.");
add(784, "The Adore Gaming ProX Gaming Chair sets a new standard in gaming by combining durability, comfort and style. Enjoy your gaming experience with this exceptional chair!", "Игровое кресло Adore Gaming ProX задаёт новый стандарт в мире игр, сочетая прочность, комфорт и стиль. Наслаждайтесь игрой в этом замечательном кресле!", "يرسي كرسي الألعاب Adore Gaming ProX معيارًا جديدًا في عالم الألعاب، إذ يجمع المتانة والراحة والأناقة. استمتع بتجربة اللعب مع هذا الكرسي المميز!");
add(785, "Modern, stylish retro design", "Современный стильный дизайн в духе ретро", "تصميم ريترو عصري وأنيق");
add(786, "2 spacious, practical shelves", "2 вместительные практичные полки", "رفان واسعان وعمليان");
add(787, "Sliding doors for practical use", "Раздвижные дверцы для удобства использования", "أبواب منزلقة لاستخدام عملي");
add(788, "Suitable for home and office use", "Подходит для дома и офиса", "مناسب للاستخدام في المنزل والمكتب");
add(789, "With its comfortable design and elegant details, the Boston Executive Chair brings quality and style to office life. It provides ergonomic support during long working hours, with durable materials for years of use.", "Благодаря удобному дизайну и изящным деталям кресло руководителя Boston привносит качество и стиль в офисную жизнь. Оно обеспечивает эргономичную поддержку во время долгой работы, а прочные материалы рассчитаны на многолетнее использование.", "يضيف كرسي المدير Boston الجودة والأناقة إلى أجواء المكتب بتصميمه المريح وتفاصيله الراقية. ويوفر دعمًا مريحًا خلال ساعات العمل الطويلة، مع مواد متينة للاستخدام لسنوات.");
add(790, "Remote-controlled assistance when standing up", "Помощь при вставании с управлением с пульта", "مساعدة على النهوض بالتحكم عن بعد");
add(791, "Practical pocket for books, magazines, phones, etc.", "Удобный карман для книг, журналов, телефона и т. д.", "جيب عملي للكتب والمجلات والهاتف وغيرها");
add(792, "Reclines up to 120 degrees", "Наклоняется назад до 120 градусов", "يميل للخلف حتى 120 درجة");
add(793, "The product features wipe-clean fabric with high moisture absorption and resistance to tearing, wear and fading, together with a durable opening mechanism and springs.", "Изделие состоит из ткани, допускающей протирание, с высоким влагопоглощением и устойчивостью к разрывам, истиранию и выцветанию, а также прочного механизма раскладывания и пружин.", "يتكون المنتج من قماش قابل للمسح وعالي الامتصاص للرطوبة ومقاوم للتمزق والتآكل وبهتان اللون، مع آلية فتح متينة ونوابض.");
add(794, "Wipe-clean fabric with high moisture absorption and resistance to tearing, wear and fading.", "Ткань, допускающая протирание, с высоким влагопоглощением и устойчивостью к разрывам, истиранию и выцветанию.", "قماش قابل للمسح وعالي الامتصاص للرطوبة ومقاوم للتمزق والتآكل وبهتان اللون.");
add(795, "First-quality durable opening mechanism and springs", "Прочные механизм раскладывания и пружины первого сорта", "آلية فتح ونوابض متينة من الدرجة الأولى");
add(796, "One person is recommended for assembly.", "Рекомендуется сборка одним человеком.", "يوصى بتجميع المنتج بواسطة شخص واحد.");
add(797, "Seat height can be easily adjusted to the user's needs.", "Высота сиденья легко регулируется под потребности пользователя.", "يمكن ضبط ارتفاع المقعد بسهولة حسب احتياجات المستخدم.");
add(798, "Move freely with the 360-degree swivel structure and quiet, durable castors.", "Вращение на 360 градусов и бесшумные прочные колёсики обеспечивают свободу передвижения.", "يمكنك التحرك بحرية بفضل الهيكل الدوار بزاوية 360 درجة والعجلات الهادئة والمتينة.");
add(799, "High-quality metal footrest and durable plaid-fabric upholstery.", "Высококачественная металлическая подставка для ног и прочная обивка из клетчатой ткани.", "مسند قدمين معدني عالي الجودة وتنجيد من قماش متين بنقشة مربعات.");
add(800, "Black metal legs provide strength and stability while adding a modern touch.", "Чёрные металлические ножки обеспечивают прочность и устойчивость, добавляя современный акцент.", "توفر الأرجل المعدنية السوداء القوة والثبات وتضيف لمسة عصرية.");
add(801, "The open shelves at the top provide an ideal space for books, notebooks, stationery and decorative items.", "Открытые полки в верхней части идеально подходят для книг, тетрадей, канцелярских принадлежностей и предметов декора.", "توفر الرفوف المفتوحة في الجزء العلوي مساحة مثالية للكتب والدفاتر والأدوات المكتبية وقطع الزينة.");
add(802, "A dedicated cable outlet keeps the appearance tidy and prevents tangled cables.", "Специальное отверстие для кабелей сохраняет аккуратный вид и предотвращает их спутывание.", "تحافظ فتحة مخصصة للكابلات على مظهر مرتب وتمنع تشابكها.");
add(803, "Crossed metal supports beneath the desk add strength and long-term durability.", "Перекрёстные металлические опоры под столом повышают прочность и долговечность.", "توفر الدعامات المعدنية المتقاطعة أسفل المكتب قوة إضافية ومتانة طويلة الأمد.");
add(804, "Screw-adjustable foot pads on the metal legs help keep the desk level on uneven floors and do not scratch hard surfaces such as parquet.", "Винтовые подпятники на металлических ножках помогают выровнять стол на неровном полу и не царапают твёрдые поверхности, например паркет.", "تساعد قواعد الأرجل المعدنية القابلة للضبط بالبراغي على موازنة المكتب فوق الأرضيات غير المستوية، ولا تخدش الأسطح الصلبة مثل الباركيه.");
add(805, "The natural wood and black metal combination suits modern, minimalist and industrial interiors.", "Сочетание натурального дерева и чёрного металла подходит для современных, минималистичных и индустриальных интерьеров.", "يناسب مزيج الخشب الطبيعي والمعدن الأسود أنماط الديكور العصرية والبسيطة والصناعية.");
add(806, "The compact structure lets you create an organised, efficient workspace even in small areas.", "Компактная конструкция позволяет организовать упорядоченное и эффективное рабочее место даже на небольшой площади.", "يتيح الهيكل المدمج إنشاء مساحة عمل منظمة وفعالة حتى في الأماكن الضيقة.");
add(807, "Lumbar Support System: Special lumbar support in the backrest maintains the spine's natural curve to minimise the risk of lower-back pain. It helps maintain posture, especially during prolonged sitting.", "Система поддержки поясницы: специальная опора в спинке сохраняет естественный изгиб позвоночника, снижая риск боли в пояснице. Она помогает поддерживать осанку, особенно при длительном сидении.", "نظام دعم أسفل الظهر: يحافظ الدعم الخاص في مسند الظهر على الانحناء الطبيعي للعمود الفقري لتقليل خطر آلام أسفل الظهر. ويساعد على الحفاظ على وضعية الجسم، خاصة أثناء الجلوس الطويل.");
add(808, "Head Support: The adjustable headrest supports the neck and head, increasing comfort and encouraging a proper sitting position.", "Поддержка головы: регулируемый подголовник поддерживает шею и голову, повышает комфорт и способствует правильной посадке.", "دعم الرأس: يسند مسند الرأس القابل للتعديل الرقبة والرأس لزيادة الراحة ودعم وضعية الجلوس الصحيحة.");
add(809, "Breathable Fabric: Mesh fabric promotes airflow, prevents sweating and provides a cool experience during prolonged use.", "Дышащая ткань: сетчатая ткань обеспечивает воздухообмен, предотвращает потоотделение и сохраняет прохладу при длительном использовании.", "قماش مسامي: يسمح النسيج الشبكي بتدفق الهواء ويمنع التعرق ويوفر إحساسًا بالانتعاش أثناء الاستخدام الطويل.");
add(810, "Durability: The high-quality mesh material is designed for long-lasting use and resists deformation.", "Долговечность: высококачественный сетчатый материал рассчитан на длительное использование и устойчив к деформации.", "المتانة: صممت المادة الشبكية عالية الجودة للاستخدام طويل الأمد ومقاومة التشوه.");
add(811, "High-Density Foam: The wide, soft seating surface distributes weight evenly for comfortable sitting.", "Пена высокой плотности: широкая мягкая поверхность сиденья равномерно распределяет вес для комфортного сидения.", "إسفنج عالي الكثافة: يوزع سطح الجلوس الواسع والناعم الوزن بالتساوي لجلوس مريح.");
add(812, "Ergonomic Design: The slight slope at the front of the cushion reduces pressure on the legs and supports circulation.", "Эргономичный дизайн: небольшой наклон передней части подушки снижает давление на ноги и способствует кровообращению.", "تصميم مريح: يقلل الميل الخفيف في مقدمة الوسادة الضغط على الساقين ويدعم الدورة الدموية.");
add(813, "Chair Angle: The recline function provides different sitting positions for working or relaxing. Reclining can be enabled or disabled.", "Угол наклона кресла: функция наклона спинки позволяет принимать разные положения для работы или отдыха. Наклон можно включать и отключать.", "زاوية الكرسي: تتيح خاصية الإمالة للخلف أوضاع جلوس مختلفة للعمل أو الراحة. ويمكن تفعيل الإمالة أو إيقافها.");
add(814, "Foldable, Adjustable Armrests: Raise or lower the armrests to create an ergonomic workspace suited to your comfort.", "Складные регулируемые подлокотники: поднимайте или опускайте подлокотники для создания удобного эргономичного рабочего места.", "مساند ذراعين قابلة للطي والتعديل: ارفع مسندي الذراعين أو اخفضهما لإنشاء مساحة عمل مريحة تناسبك.");
add(815, "360-Degree Swivel: The chair base is designed to rotate a full turn, increasing freedom of movement.", "Вращение на 360 градусов: основание кресла позволяет выполнять полный оборот, повышая свободу движений.", "دوران بزاوية 360 درجة: صممت قاعدة الكرسي لتدور دورة كاملة، مما يزيد حرية الحركة.");
add(816, "Quiet, Durable Castors: Move without scratching the floor and suit different surfaces, including wood, carpet and ceramic tiles.", "Бесшумные прочные колёсики: перемещаются без царапин на полу и подходят для разных покрытий, включая дерево, ковёр и керамическую плитку.", "عجلات هادئة ومتينة: تتحرك دون خدش الأرضية، وتناسب أسطحًا مختلفة مثل الخشب والسجاد وبلاط السيراميك.");
add(817, "Sturdy Star Base: Strong, durable five-spoke moulded metal base", "Прочная крестовина: надёжное долговечное пятилучевое основание из формованного металла", "قاعدة نجمية متينة: قاعدة معدنية مقولبة قوية ومتينة بخمسة أذرع");
add(818, "Mesh Backrest:", "Сетчатая спинка:", "مسند ظهر شبكي:");
add(819, "Seat Cushion:", "Подушка сиденья:", "وسادة المقعد:");
add(820, "Adjustable Functions:", "Регулируемые функции:", "وظائف قابلة للتعديل:");
add(821, "Armrests:", "Подлокотники:", "مساند الذراعين:");
add(822, "Wide, Durable Star Base:", "Широкая прочная крестовина:", "قاعدة نجمية عريضة ومتينة:");
add(823, "Sturdy Star Base: Strong, durable five-spoke moulded metal base.", "Прочная крестовина: надёжное долговечное пятилучевое основание из формованного металла.", "قاعدة نجمية متينة: قاعدة معدنية مقولبة قوية ومتينة بخمسة أذرع.");
add(824, "Breathable mesh fabric on the backrest", "Воздухопроницаемая сетчатая ткань на спинке", "قماش شبكي يسمح بالتهوية في مسند الظهر");
add(825, "Specially designed, attractive ergonomic lumbar support and attractive foldable armrests", "Эстетичная эргономичная поясничная опора специального дизайна и эстетичные складные подлокотники", "دعم مريح لأسفل الظهر بتصميم خاص وأنيق، ومساند ذراعين أنيقة قابلة للطي");
add(826, "Durable, specially moulded high-density seat cushion", "Прочная подушка сиденья высокой плотности специальной формовки", "وسادة مقعد متينة وعالية الكثافة بقالب خاص");
add(827, "Lockable height and recline mechanism", "Механизм регулировки высоты и наклона с фиксацией", "آلية ارتفاع وإمالة للخلف قابلة للتثبيت");
add(828, "First-quality, long-lasting height-adjustment gas lift", "Высококачественный долговечный газлифт для регулировки высоты", "رافعة غازية لضبط الارتفاع عالية الجودة وطويلة العمر");
add(829, "Attractive, scratch-resistant metal star base", "Эстетичная металлическая крестовина, устойчивая к царапинам", "قاعدة نجمية معدنية أنيقة ومقاومة للخدوش");
add(830, "Long-lasting, quiet castors that do not scratch floors", "Долговечные бесшумные колёсики, не царапающие пол", "عجلات هادئة وطويلة العمر لا تخدش الأرضيات");
add(831, "Easy, quick assembly", "Простая и быстрая сборка", "تجميع سهل وسريع");
add(832, "Electric recliner mechanism for reclining the backrest and extending the footrest", "Электрический механизм реклайнера для наклона спинки и выдвижения подставки для ног", "آلية استرخاء كهربائية لإمالة مسند الظهر وتمديد مسند القدمين");
add(833, "Easy, effortless one-button operation with the remote control", "Простое управление одной кнопкой пульта без усилий", "تشغيل سهل دون عناء بزر واحد من جهاز التحكم");
add(834, "Can operate with a rechargeable battery or power cable", "Возможность работы от аккумулятора или сетевого кабеля", "يمكن تشغيله ببطارية قابلة للشحن أو بكابل كهربائي");
add(835, "Soft-textured, durable, long-lasting upholstery fabric", "Мягкая на ощупь, прочная и долговечная обивочная ткань", "قماش تنجيد ناعم الملمس ومتين وطويل العمر");
add(836, "Ergonomic backrest and seat structure that support the body", "Эргономичная конструкция спинки и сиденья поддерживает тело", "تصميم مريح لمسند الظهر والمقعد يدعم الجسم");
add(837, "Wide, comfortable armrest areas", "Широкие удобные подлокотники", "مساحات عريضة ومريحة لإسناد الذراعين");
add(838, "Sturdy metal frame and durable mechanism", "Прочный металлический каркас и долговечный механизм", "هيكل معدني قوي وآلية متينة");

add(839, "Comfort and Adaptability:", "Комфорт и адаптация:", "الراحة وقابلية التكيف:");
add(840, "Up-and-down height adjustment and lumbar-support height adjustment", "Регулировка высоты кресла и поясничной опоры вверх-вниз", "تعديل ارتفاع المقعد ودعم أسفل الظهر للأعلى والأسفل");
add(841, "A seating experience designed to help you make the most of your working day", "Комфортная посадка, созданная для продуктивного рабочего дня", "تجربة جلوس مصممة لمساعدتك على الاستفادة المثلى من يوم عملك");
add(842, "Attractive, Stylish Design:", "Эстетичный и стильный дизайн:", "تصميم جميل وأنيق:");
add(843, "An attractive backrest design creates a modern, professional atmosphere", "Эстетичный дизайн спинки создаёт современную профессиональную атмосферу", "تصميم أنيق لمسند الظهر يضفي أجواء عصرية واحترافية");
add(844, "Headrest Adjustment and Extra Support:", "Регулировка подголовника и дополнительная поддержка:", "تعديل مسند الرأس ودعم إضافي:");
add(845, "Up-and-down headrest adjustment provides extra support and comfort", "Регулировка подголовника вверх-вниз обеспечивает дополнительную поддержку и комфорт", "يوفر تعديل مسند الرأس للأعلى والأسفل دعمًا وراحة إضافيين");
add(846, "Lumbar and back support adjustment helps achieve an ergonomic sitting position", "Регулировка поддержки поясницы и спины способствует эргономичной посадке", "يساعد ضبط دعم أسفل الظهر والظهر على تحقيق وضعية جلوس مريحة");
add(847, "Durable Castors:", "Прочные колёсики:", "عجلات متينة:");
add(848, "Castors that move quietly and smoothly, together with a sturdy detachable metal star base, provide dependable use for many years.", "Колёсики с бесшумным плавным ходом и прочная разборная металлическая крестовина обеспечивают надёжное использование на долгие годы.", "توفر العجلات الهادئة والسلسة الحركة مع القاعدة النجمية المعدنية المتينة القابلة للفك استخدامًا موثوقًا لسنوات طويلة.");
add(849, "Easy Care and Cleaning:", "Простой уход и очистка:", "سهولة العناية والتنظيف:");
add(850, "Materials with soft surface coverings allow easy cleaning and care", "Материалы с мягким покрытием поверхности просты в очистке и уходе", "تسهل المواد ذات الكسوة السطحية الناعمة التنظيف والعناية");
add(851, "Ideal materials for maintaining a clean, tidy appearance in the office", "Материалы, подходящие для поддержания чистого и аккуратного вида в офисе", "مواد مثالية للحفاظ على مظهر نظيف ومرتب في المكتب");
add(852, "Professionalism and Performance:", "Профессионализм и эффективность:", "الاحترافية والأداء:");
add(853, "Positively affects work performance to improve productivity", "Положительно влияет на результаты работы и повышает продуктивность", "يؤثر إيجابيًا في أداء عملك لزيادة إنتاجيتك");
add(854, "Adjustable Height:", "Регулируемая высота:", "ارتفاع قابل للتعديل:");
add(855, "Up-and-down height adjustment", "Регулировка высоты вверх-вниз", "تعديل الارتفاع للأعلى والأسفل");
add(856, "Recline tension adjustment lets you tailor the chair's comfort to your preferences throughout the day", "Регулировка жёсткости наклона позволяет подстраивать комфорт кресла под свои предпочтения в течение дня", "يتيح ضبط مقاومة الإمالة للخلف تخصيص راحة الكرسي حسب تفضيلاتك طوال اليوم");
add(857, "Soft-Surfaced Armrests:", "Подлокотники с мягкой поверхностью:", "مساند ذراعين بسطح ناعم:");
add(858, "Attractive, ergonomic armrests with soft surface coverings provide comfortable support while you work", "Эстетичные эргономичные подлокотники с мягкой поверхностью обеспечивают удобную поддержку во время работы", "توفر مساند الذراعين الأنيقة والمريحة ذات الكسوة الناعمة دعمًا مريحًا أثناء العمل");
add(859, "Easy-to-clean materials help keep the chair well maintained and long lasting", "Простые в очистке материалы помогают поддерживать кресло в хорошем состоянии и продлевают срок службы", "تساعد المواد سهلة التنظيف على الحفاظ على الكرسي بحالة جيدة وعمر طويل");
add(860, "Durable Castors:", "Прочные колёсики:", "عجلات متينة:");
add(861, "360-Degree Mobility:", "Подвижность на 360 градусов:", "حركة بزاوية 360 درجة:");
add(862, "360-degree mobility helps you communicate freely around the office", "Подвижность на 360 градусов помогает свободно общаться в офисе", "تساعدك الحركة بزاوية 360 درجة على التواصل بحرية داخل المكتب");
add(863, "With its functionality and ease of use, the Base Task Chair makes everyday life easier at home and at work", "Благодаря функциональности и простоте использования рабочий стул Base облегчает повседневную жизнь дома и на работе", "يسهل كرسي العمل Base حياتك في المنزل والعمل بفضل وظائفه وسهولة استخدامه");
add(864, "3 hanging compartments", "3 отделения для одежды на вешалках", "3 حجرات لتعليق الملابس");
add(865, "2 spacious, functional drawers", "2 вместительных функциональных ящика", "درجان واسعان وعمليان");
add(866, "Polymer Composite Leg", "Ножка из полимерного композита", "رجل من مركب بوليمري");
add(867, "2 appliance compartments", "2 отделения для бытовой техники", "حجرتان للأجهزة");
add(868, "Sliding panel system", "Система выдвижной панели", "نظام لوح منزلق");
add(869, "Durable frame structure", "Прочная конструкция корпуса", "بنية هيكل متينة");
add(870, "Suitable for both home and office use", "Подходит для дома и офиса", "مناسب للاستخدام في المنزل والمكتب");
add(871, "Avoid prolonged contact with water and heat. Can be cleaned with a damp cloth.", "Избегайте длительного контакта с водой и нагрева. Можно протирать влажной тканью.", "تجنب ملامسته للماء والحرارة لفترات طويلة. يمكن تنظيفه بقطعة قماش رطبة.");
add(872, "Quality upholstery suitable for long-term use", "Качественная обивка для длительного использования", "تنجيد عالي الجودة مناسب للاستخدام طويل الأمد");
add(873, "4 spacious, practical shelves", "4 вместительные практичные полки", "4 رفوف واسعة وعملية");
add(874, "Two-door design for practical use", "Двухдверная конструкция для удобства использования", "تصميم ببابين لاستخدام عملي");
add(875, "Compartment behind the door", "Отделение за дверцей", "حجرة خلف الباب");
add(876, "Attractive metal handle", "Эстетичная металлическая ручка", "مقبض معدني أنيق");
add(877, "5 metal hooks", "5 металлических крючков", "5 خطافات معدنية");
add(878, "Design with rounded corners", "Дизайн со скруглёнными углами", "تصميم بزوايا مستديرة");
add(879, "Metal support bracket", "Металлический опорный кронштейн", "دعامة معدنية");
add(880, "10 shelf compartments", "10 отделений с полками", "10 حجرات رفوف");
add(881, "4 metal hooks", "4 металлических крючка", "4 خطافات معدنية");
add(882, "1 shelf above the hooks", "1 полка над крючками", "رف واحد فوق الخطافات");
add(883, "Cushioned seating area", "Место для сидения с подушкой", "مساحة جلوس مبطنة");
add(884, "3 attractive, sturdy metal hooks", "3 эстетичных прочных металлических крючка", "3 خطافات معدنية أنيقة ومتينة");
add(885, "Lower cabinet with 3 compartments", "Нижний шкаф с 3 отделениями", "خزانة سفلية بثلاث حجرات");
add(886, "1 open compartment", "1 открытое отделение", "حجرة مفتوحة واحدة");
add(887, "LED strip lighting", "Светодиодная ленточная подсветка", "إضاءة بشريط LED");
add(888, "Attractive handle", "Эстетичная ручка", "مقبض أنيق");
add(889, "2 practical shelves", "2 практичные полки", "رفان عمليان");
add(890, "Floor-safe profile leg coordinated with the MDF material", "Ножка из профиля в сочетании с МДФ, не повреждающая пол", "رجل من القطاعات متناسقة مع مادة MDF ولا تضر الأرضية");
add(891, "10 compartments", "10 отделений", "10 حجرات");
add(892, "Attractive metal handle", "Эстетичная металлическая ручка", "مقبض معدني أنيق");
add(893, "2 metal hooks", "2 металлических крючка", "خطافان معدنيان");
add(894, "Scratch- and impact-resistant metal leg", "Металлическая ножка, устойчивая к царапинам и ударам", "رجل معدنية مقاومة للخدوش والصدمات");
add(895, "Storage area with multiple compartments", "Место для хранения с несколькими отделениями", "مساحة تخزين متعددة الحجرات");
add(896, "Spacious top surface", "Просторная верхняя поверхность", "سطح علوي واسع");
add(897, "5 spacious compartments", "5 вместительных отделений", "5 حجرات واسعة");
add(898, "2 hooks", "2 крючка", "خطافان");
add(899, "Specially designed metal handle", "Металлическая ручка специального дизайна", "مقبض معدني بتصميم خاص");
add(900, "Wide lower shelf provides extra storage space", "Широкая нижняя полка обеспечивает дополнительное место для хранения", "رف سفلي عريض يوفر مساحة تخزين إضافية");
add(901, "Durable, sturdy leg structure", "Прочная и надёжная конструкция ножек", "بنية أرجل متينة وقوية");
add(902, "Modern two-tone design", "Современный двухцветный дизайн", "تصميم عصري بلونين");
add(903, "Spacious, practical surface", "Просторная практичная поверхность", "سطح واسع وعملي");
add(904, "Functional design suitable for corner placement", "Функциональный дизайн для размещения в углу", "تصميم عملي مناسب للاستخدام في الزوايا");
add(905, "1 mirrored door", "1 зеркальная дверца", "باب واحد بمرآة");
add(906, "5 shelf spaces", "5 секций с полками", "5 مساحات للرفوف");
add(907, "2 separate clothes-hanging sections", "2 отдельных отделения для одежды на вешалках", "قسمان منفصلان لتعليق الملابس");
add(908, "Hanging space in the upper and lower sections", "Места для подвешивания одежды в верхней и нижней секциях", "مساحة لتعليق الملابس في القسمين العلوي والسفلي");
add(909, "Spacious, practical interior", "Вместительное практичное внутреннее пространство", "حيز داخلي واسع وعملي");

add(910, "Weight-Sensitive Mechanism: The new-generation mechanism balances backrest recline resistance according to the user's body weight, providing a more controlled sitting experience.", "Механизм, реагирующий на вес тела: механизм нового поколения регулирует сопротивление наклону спинки в зависимости от веса пользователя, обеспечивая более контролируемую посадку.", "آلية تستجيب لوزن الجسم: توازن آلية الجيل الجديد مقاومة إمالة مسند الظهر حسب وزن المستخدم، لتوفير تجربة جلوس أكثر تحكمًا.");
add(911, "Multi-Position Locking Backrest: The recline mechanism locks at different levels, allowing the preferred sitting position to be set for work or rest.", "Спинка с многоступенчатой фиксацией: механизм наклона фиксируется в разных положениях, позволяя выбрать удобную посадку для работы или отдыха.", "مسند ظهر بقفل متعدد الوضعيات: تثبت آلية الإمالة في درجات مختلفة لضبط وضعية الجلوس المفضلة أثناء العمل أو الراحة.");
add(912, "High-Density Seat Foam: Ergonomic, durable high-density foam provides a comfortable seating area during prolonged use and helps retain its shape.", "Пена сиденья высокой плотности: эргономичная прочная пена высокой плотности обеспечивает комфорт при длительном использовании и помогает сохранять форму.", "إسفنج مقعد عالي الكثافة: يوفر الإسفنج المريح والمتين وعالي الكثافة مساحة جلوس مريحة أثناء الاستخدام الطويل، ويساعد على الحفاظ على شكله.");
add(913, "Breathable Mesh Backrest: The durable mesh surface promotes air circulation for a fresher sitting experience during prolonged use.", "Дышащая сетчатая спинка: прочная сетчатая поверхность способствует циркуляции воздуха и обеспечивает свежесть при длительном сидении.", "مسند ظهر شبكي مسامي: يدعم السطح الشبكي المتين دوران الهواء لتجربة جلوس أكثر انتعاشًا أثناء الاستخدام الطويل.");
add(914, "Adjustable Lumbar Support: Lumbar support adjusts to the user's sitting position and helps support the back and lower back.", "Регулируемая поддержка поясницы: поясничная опора настраивается под посадку пользователя и помогает поддерживать спину и поясницу.", "دعم قابل للتعديل لأسفل الظهر: يمكن ضبط الدعم حسب وضعية جلوس المستخدم للمساعدة على إسناد الظهر والمنطقة القطنية.");
add(915, "Adjustable Armrests: Armrests with a soft PU surface adjust up and down to position the arms appropriately for the workspace.", "Регулируемые подлокотники: подлокотники с мягкой поверхностью из ПУ регулируются вверх-вниз, позволяя удобно расположить руки относительно рабочего места.", "مساند ذراعين قابلة للتعديل: تضبط المساند ذات السطح الناعم من البولي يوريثان PU للأعلى والأسفل لوضع الذراعين بما يناسب مساحة العمل.");
add(916, "Durable Metal Star Base: The sturdy metal star base helps keep the chair balanced and secure during use.", "Прочная металлическая крестовина: надёжное металлическое основание помогает сохранять устойчивость и безопасность кресла при использовании.", "قاعدة نجمية معدنية متينة: تساعد القاعدة المعدنية القوية على استخدام الكرسي بثبات وأمان.");
add(917, "Quiet, Parquet-Friendly Castors: Durable castors provide quiet, smooth movement while helping reduce the risk of scratches on delicate floors such as parquet.", "Бесшумные колёсики для паркета: прочные колёсики обеспечивают тихое плавное движение и помогают снизить риск царапин на чувствительных покрытиях, например паркете.", "عجلات هادئة وملائمة للباركيه: توفر العجلات المتينة حركة هادئة وسلسة، وتساعد على تقليل خطر الخدش على الأرضيات الحساسة مثل الباركيه.");
add(918, "Ergonomic Design and Comfort:", "Эргономичный дизайн и комфорт:", "تصميم مريح وراحة:");
add(919, "An ergonomic backrest that follows the body's shape and adjustable lumbar support provide comfortable sitting. They support the back and lower back during long working hours.", "Эргономичная спинка, повторяющая форму тела, и регулируемая поясничная опора обеспечивают комфортную посадку. Они поддерживают спину и поясницу во время долгой работы.", "يوفر تصميم مسند الظهر المريح والمتكيف مع شكل الجسم ودعم أسفل الظهر القابل للتعديل تجربة جلوس مريحة، مع إسناد الظهر والمنطقة القطنية خلال ساعات العمل الطويلة.");
add(920, "Adjustable Headrest Support:", "Регулируемая поддержка головы:", "دعم رأس قابل للتعديل:");
add(921, "The headrest adjusts up and down and forwards and backwards to provide personalised support for the head and neck.", "Подголовник регулируется вверх-вниз и вперёд-назад, обеспечивая индивидуальную поддержку головы и шеи.", "تتيح آلية مسند الرأس القابلة للضبط للأعلى والأسفل وللأمام والخلف دعمًا مخصصًا للرأس والرقبة.");
add(922, "Multifunctional Armrests:", "Многофункциональные подлокотники:", "مساند ذراعين متعددة الوظائف:");
add(923, "Multifunctional armrests adapt to different sitting positions and help position the arms comfortably.", "Многофункциональные подлокотники подстраиваются под разные положения при сидении и помогают удобно расположить руки.", "تتكيف مساند الذراعين متعددة الوظائف مع أوضاع جلوس مختلفة وتساعد على وضع الذراعين براحة.");
add(924, "Adjustable Lumbar Support:", "Регулируемая поддержка поясницы:", "دعم قابل للتعديل لأسفل الظهر:");
add(925, "Adjustable lumbar support allows an ergonomic sitting position tailored to individual needs.", "Регулируемая поясничная опора позволяет создать эргономичную посадку с учётом индивидуальных потребностей.", "يتيح دعم أسفل الظهر القابل للتعديل تحقيق وضعية جلوس مريحة تناسب الاحتياجات الشخصية.");
add(926, "Multifunctional Mechanism:", "Многофункциональный механизм:", "آلية متعددة الوظائف:");
add(927, "The new-generation multifunctional mechanism allows the sitting position to be adjusted to personal preferences. A lever-operated up-and-down control system makes chair height easy to adjust.", "Многофункциональный механизм нового поколения позволяет настроить посадку по личным предпочтениям. Рычажная система управления вверх-вниз обеспечивает простую регулировку высоты кресла.", "تتيح آلية الجيل الجديد متعددة الوظائف ضبط وضعية الجلوس حسب التفضيلات الشخصية. ويسهل نظام التحكم بالذراع للأعلى والأسفل تعديل ارتفاع الكرسي.");
add(928, "Seat Cushion Adjustment:", "Регулировка подушки сиденья:", "ضبط وسادة المقعد:");
add(929, "The seat cushion adjusts forwards and backwards, allowing seat depth to be tailored to individual needs. It accommodates different body shapes to improve sitting comfort.", "Подушка сиденья регулируется вперёд-назад, позволяя настроить глубину по индивидуальным потребностям. Она подстраивается под разные типы телосложения для большего комфорта.", "تتيح وسادة المقعد القابلة للضبط للأمام والخلف تعديل عمق الجلوس حسب الاحتياجات الشخصية. وتتكيف مع أشكال الجسم المختلفة لتعزيز الراحة.");
add(930, "Backrest Recline and Locking System:", "Система наклона и фиксации спинки:", "نظام إمالة مسند الظهر وتثبيته:");
add(931, "Backrest tension adjustment allows recline resistance to be set to personal preferences. The recline lock secures the backrest in the desired position.", "Регулировка жёсткости наклона позволяет настроить сопротивление спинки по личным предпочтениям. Фиксатор удерживает спинку в нужном положении.", "يتيح ضبط شد مسند الظهر تعديل مقاومة الإمالة حسب التفضيلات الشخصية. ويثبت قفل الإمالة المسند في الوضع المطلوب.");
add(932, "Quiet, Attractive Castors:", "Бесшумные эстетичные колёсики:", "عجلات هادئة وأنيقة:");
add(933, "Wide, attractively designed quiet castors provide comfortable, smooth movement around the workspace.", "Широкие бесшумные колёсики эстетичного дизайна обеспечивают удобное плавное передвижение по рабочему пространству.", "توفر العجلات الهادئة والعريضة ذات التصميم الأنيق حركة مريحة وسلسة في مساحة العمل.");
add(934, "Modern lines, elegant colour coordination and functional details bring an attractive look to office and home workspaces.", "Современные линии, изящное сочетание цветов и функциональные детали придают эстетичный вид офисным и домашним рабочим пространствам.", "تضفي الخطوط العصرية وتناسق الألوان الأنيق والتفاصيل العملية مظهرًا جميلًا على مساحات العمل في المكتب والمنزل.");
add(935, "Ergonomic Design and Superior Comfort:", "Эргономичный дизайн и превосходный комфорт:", "تصميم مريح وراحة فائقة:");
add(936, "The fully ergonomic structure and independently adjustable back and lumbar supports adapt to the body's shape for comfortable sitting. They promote comfort during long working hours.", "Полностью эргономичная конструкция и независимо регулируемые опоры спины и поясницы подстраиваются под телосложение для комфортной посадки. Они обеспечивают удобство во время долгой работы.", "يتكيف التصميم المريح بالكامل مع شكل الجسم بفضل دعمي الظهر وأسفل الظهر القابلين للتعديل بشكل مستقل، لتوفير تجربة جلوس مريحة ودعم الراحة خلال ساعات العمل الطويلة.");
add(937, "Electric Lumbar Massage Function:", "Функция электрического массажа поясницы:", "خاصية تدليك كهربائي لأسفل الظهر:");
add(938, "An electric massage unit integrated into the lumbar support provides extra comfort while working. The product must be plugged into a power outlet to use the massage function.", "Электрический массажный блок, встроенный в поясничную опору, обеспечивает дополнительный комфорт во время работы. Для использования массажа изделие необходимо подключить к розетке.", "توفر وحدة تدليك كهربائية مدمجة في دعم أسفل الظهر راحة إضافية أثناء العمل. ويجب توصيل المنتج بمقبس كهربائي لاستخدام خاصية التدليك.");
add(939, "Adjustable Back and Lumbar Support:", "Регулируемая поддержка спины и поясницы:", "دعم قابل للتعديل للظهر وأسفل الظهر:");
add(940, "Independently adjustable back and lumbar supports adapt to individual sitting habits. The breathable mesh backrest and adjustable lumbar support encourage an ergonomic sitting position.", "Независимо регулируемые опоры спины и поясницы подстраиваются под индивидуальные привычки сидения. Дышащая сетчатая спинка и регулируемая поясничная опора способствуют эргономичной посадке.", "يتكيف دعما الظهر وأسفل الظهر القابلان للتعديل بشكل مستقل مع عادات الجلوس الشخصية. ويدعم مسند الظهر الشبكي المسامي ودعم أسفل الظهر القابل للتعديل وضعية جلوس مريحة.");
add(941, "New-Generation Recline Mechanism:", "Механизм наклона нового поколения:", "آلية إمالة من الجيل الجديد:");
add(942, "The adjustable, lockable recline mechanism makes it easy to switch between sitting positions. The backrest can be fixed in the user's preferred position.", "Регулируемый механизм наклона с фиксацией позволяет легко менять положение при сидении. Спинку можно закрепить в предпочитаемом пользователем положении.", "تتيح آلية الإمالة للخلف القابلة للتعديل والتثبيت الانتقال بسهولة بين أوضاع جلوس مختلفة. ويمكن تثبيت مسند الظهر في الوضع الذي يفضله المستخدم.");
add(943, "Adjustable Armrests:", "Регулируемые подлокотники:", "مساند ذراعين قابلة للتعديل:");
add(944, "Armrests with a soft PU surface adjust up and down to help position the arms comfortably. They accommodate different desk heights.", "Подлокотники с мягкой поверхностью из ПУ регулируются вверх-вниз и помогают удобно расположить руки. Они подходят для столов разной высоты.", "تساعد مساند الذراعين ذات السطح الناعم من البولي يوريثان PU والقابلة للضبط للأعلى والأسفل على وضع الذراعين براحة، وتناسب ارتفاعات المكاتب المختلفة.");
add(945, "Durable, Comfortable Seat Foam:", "Прочная и комфортная пена сиденья:", "إسفنج مقعد متين ومريح:");
add(946, "Durable high-density seat foam with an ergonomic structure provides a comfortable seating area during prolonged use.", "Прочная пена сиденья высокой плотности с эргономичной формой обеспечивает комфорт при длительном использовании.", "يوفر إسفنج المقعد المتين وعالي الكثافة بتصميمه المريح مساحة جلوس مريحة أثناء الاستخدام الطويل.");
add(947, "Breathable Mesh Backrest:", "Дышащая сетчатая спинка:", "مسند ظهر شبكي مسامي:");
add(948, "The durable, breathable mesh backrest promotes air circulation, providing a fresh experience during long working hours.", "Прочная воздухопроницаемая сетчатая спинка способствует циркуляции воздуха и обеспечивает свежесть во время долгой работы.", "يدعم مسند الظهر الشبكي المتين والمسامي دوران الهواء لتوفير إحساس بالانتعاش خلال ساعات العمل الطويلة.");
add(949, "Attractive, Durable Nylon Star Base:", "Эстетичная прочная нейлоновая крестовина:", "قاعدة نجمية من النايلون أنيقة ومتينة:");
add(950, "The modern, durable nylon star base provides a sturdy foundation for the chair while adding style to office and home workspaces.", "Прочная нейлоновая крестовина современного дизайна обеспечивает надёжную опору креслу и придаёт стильный вид офисным и домашним рабочим пространствам.", "توفر القاعدة النجمية المتينة من النايلون بتصميمها العصري أساسًا قويًا للكرسي، وتضفي مظهرًا أنيقًا على مساحات العمل في المكتب والمنزل.");
add(951, "Quiet Castors That Do Not Scratch Parquet:", "Бесшумные колёсики, не царапающие паркет:", "عجلات هادئة لا تخدش الباركيه:");
add(952, "Durable, quiet castors designed to resist scratching parquet surfaces allow comfortable, smooth movement around the workspace.", "Прочные бесшумные колёсики, разработанные для защиты паркетных поверхностей от царапин, обеспечивают удобное плавное перемещение по рабочему пространству.", "تتيح العجلات المتينة والهادئة والمصممة للحد من خدش أسطح الباركيه حركة مريحة وسلسة في مساحة العمل.");
add(953, "Modern, Functional Design:", "Современный функциональный дизайн:", "تصميم عصري وعملي:");
add(954, "Its stylish appearance, ergonomic details and functional features combine comfort and aesthetics in both professional offices and home workspaces.", "Стильный вид, эргономичные детали и функциональные возможности сочетают комфорт и эстетику как в профессиональных офисах, так и на домашних рабочих местах.", "يجمع مظهره الأنيق وتفاصيله المريحة وخصائصه العملية بين الراحة والجمال في المكاتب المهنية ومساحات العمل المنزلية.");

export const extraTranslationsC = rows;
