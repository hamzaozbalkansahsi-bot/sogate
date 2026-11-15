# NODENO tasarım anayasası

Bu dosya kullanıcının kalıcı arayüz tercihlerini kaydeder. Marka, katalog ve güvenlik kuralları kök AGENTS.md ile birlikte uygulanır. 12/11/2026 tarihli tarih/saat tercihi tüm yeni ve mevcut müşteri ve yönetim ekranlarını kapsar.

## Tarih, saat ve seçilen ülke

- Türkiye varsayılanında görünen tarih kesin olarak `gg/aa/yyyy` biçimindedir: `12/11/2026`. Noktalı, ayı yazıyla veya `yyyy-aa-gg` biçimi kullanılmaz.
- Türkiye varsayılanında saat 24 saatlik `SS:dd` biçimindedir: `22:05`. AM/PM kullanılmaz; saat dilimi açıkça `Europe/Istanbul` seçilir. Cihazın/sunucunun saat dilimine bırakılmaz.
- Ülke seçildiğinde tarih sırası, ayırıcılar, yerel rakamlar ve 12/24 saat tercihi seçilen ülkenin kurallarına otomatik geçer. İş kayıtlarının Gregoryen takvim günü korunur. Dil seçimi ülke tercihini değiştirmez; dil ve ülke ayrı ayarlardır.
- Ülke değişiminde saat dilimi de o ülkeye uyarlanır. Birden çok saat dilimi olan ülkelerde, cihazın saat dilimi o ülkeye aitse kullanılır; aksi halde belgelenmiş ülke varsayılanı kullanılır. İşletmenin yayın takvimi, ödeme kaydı ve gerçek zaman damgaları bu gösterim tercihi nedeniyle kaydırılmaz.
- Ülke tercihi sayfa yenilemesi ve blog/mağaza/yönetim geçişlerinde korunur. Tüm ekranlar aynı biçimlendirici ve tercih kaynağını kullanır; ayrı ayrı elle tarih birleştiren bileşenler eklenmez.
- Sadece takvim tarihi olan bilgiler saat dilimi dönüşümüyle bir önceki/sonraki güne kaydırılmaz. Gerçek olay zamanları UTC/ISO olarak saklanır, seçilen ülke saat diliminde gösterilir.
- Veritabanı, API, HTML `datetime`, sitemap, RSS ve JSON-LD gibi makine sözleşmeleri standart ISO/UTC biçimini korur. İnsanın gördüğü metin ülke biçiminde gösterilir. ISO tarih müşteriye ham metin olarak sunulmaz.
- Tarih/saat girişleri de seçili saat diliminde açılır ve doğru UTC anına çevrilerek kaydedilir. Yaz/kış saati değişiminde var olmayan bir yerel saat sessizce başka saate kaydırılmaz.
- Türkiye, Birleşik Krallık, ABD, Almanya, Arapça/RTL ve UTC gün sınırı örnekleri test edilmeden tarih/saat değişikliği tamamlandı sayılmaz.

## Marka ve erişilebilirlik

Güncel NODENO logosu, kanonik marka paleti ve NODENO Sans kullanılır. Tarih ve saatler okunaklı, gerektiğinde `<time datetime="…">` ile işaretlenir. Renk, ok veya sembol tek başına tarih durumu anlatmaz. Mobilde kesilme veya yatay taşma oluşmaz.
