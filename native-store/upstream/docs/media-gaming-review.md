# Birleşik marka yazısı denetimi

`scripts/media-gaming-review.py` donmuş `37fb` tarayıcısını değiştirmeden 5129 kayıtlı kaynak OCR raporunu birleşik `adoregaming`, `doregaming`, `adorgaming` ve `adoregame` sözcükleri için tarar. Tek başına `gaming` marka sayılmaz. İlgili 14 masa/koltuk ailesinin 198 kaynak URL'sinin bütün kareleri ayrı inceleme kapsamındadır. Özel kaynaklar ve raporlar `artifacts/media-gaming-review` altında kalır.

`--audit` kaynaklara yazmaz. `--apply-plans <JSON>` yalnız kaynak SHA'sına bağlı, önceden görsel olarak konumlandırılmış alanlardan inceleme adayları üretir. Kayıtlar `publicationReady:false` ve `visualAccepted:false` kalır. Küçük yazı eşleşmeleri birer adaydır; OCR veya şablon sonucu görsel kalite onayı yerine geçmez.

Kaynak dosya, maskeler, çıktı, boyutlar, MIME, ICC profili, EXIF yönü ve animasyon zaman çizelgesi finalizer tarafından bağımsız doğrulanır. Maskenin dışındaki RGB ve tüm alfa değerleri aynı kalır. Renkli yüzey aydınlatması kaynak komşuluğundan korunur; model isimleri, ürün kenarları, dikişler ve teknik oklar silinmez.

`scripts/media-gaming-chair-repair.py` kaynak sınırlarından tüm yazı alanını dolduran ayrı koltuk adayları üretir. Başka bir bölgeden dikiş veya mekanik parça kopyalamaz. Teknik çizimlerde alan dışına bağlı özgün çizgi bileşenleri ve ölçü okları korunur. Kırmızı ölçü işaretleri ayrı korunur; ara renk hesabına kırmızı taşınmaz. Bu adaylar da son görüntü ve yakın plan görülmeden seçilmez.

Şablonun bir teknik oka veya metal mekanizmaya benzediği durumlarda ham bulgu saklanır. `postGamingTemplateReview`, tam çıktı SHA'sını ve her bulgunun `sha256(json_bytes({frame,hit}))` değerini kapsayan açık `false_positive` görsel kararını gerektirir. Bu dar ROI kararı, bütün görselin yapısal onayı değildir; finalizer ayrıca tam çıktı SHA'sına bağlı son seçim kaydını ister. Bilinen birleşik marka OCR kalıntısı bu yolla geçersiz kılınamaz.

Üretim kapısı ve iki zorunlu bütün-katalog tarama ailesi [medya sonlandırma sözleşmesindedir](media-finalization.md). Bu yardımcılar ana manifesti, kaynak arşivi veya sunucuyu değiştirmez.
