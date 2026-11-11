/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : next.config.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import type { NextConfig } from "next";
const config: NextConfig = {
  distDir: process.env.NODE_ENV==='development'?'.next-local':'.next',
  skipProxyUrlNormalize: true,
  output: "standalone", poweredByHeader: false,
  logging: { incomingRequests: false },
  devIndicators: false,
  serverExternalPackages: ["pg", "pdfkit"],
  outputFileTracingIncludes: {
    '/api/orders/*/document':['./assets/fonts/*.ttf'],
    '/api/admin/social':['./assets/fonts/*.ttf','./assets/fonts/*-OFL.txt','./public/brand/logo-horizontal*.svg','./public/brand/symbol.svg','./public/media/atelier-*.svg'],
  },
  outputFileTracingExcludes: {
    '/*':['.env*','.local/**/*','.git/**/*','test-results/**/*','playwright-report/**/*','docs/**/*','tests/**/*'],
  },
  async headers() { return [{ source: "/:path*", headers: [
    { key: "X-Content-Type-Options", value: "nosniff" },
    { key: "Referrer-Policy", value: "no-referrer" },
    { key: "X-Frame-Options", value: "DENY" },
    { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
    { key: "Content-Security-Policy", value: `default-src 'self'; script-src 'self' 'unsafe-inline'${process.env.NODE_ENV==='development'?" 'unsafe-eval'":""}; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'` }
  ]}, { source: "/api/:path*", headers: [{key:"Cache-Control",value:"private, no-store"}] }, ...['hesap','sepet','odeme','siparis','yonetim','favoriler','veri-basvurusu'].flatMap(section=>['', '/en'].map(prefix=>({source:`${prefix}/${section}/:path*`,headers:[{key:'Cache-Control',value:'private, no-store'},{key:'X-Robots-Tag',value:'noindex, nofollow'}]})))]; }
}; export default config;
