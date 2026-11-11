/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/not-found.tsx
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import Link from "next/link";
export default function NotFound(){return <div className="container section empty"><div className="empty-arch">S</div><h1>Bu sayfa bulunamadı</h1><p>Bağlantıyı kontrol edin veya ana sayfaya dönün.</p><Link className="button" href="/">Ana sayfaya dön</Link></div>;}
