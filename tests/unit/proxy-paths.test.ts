/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/proxy-paths.test.ts
 * Açıklama   : Genel yol adlarının statik dosya veya API önekleriyle yanlış dışlanmasını engeller.
 */
import {expect,it} from 'vitest';
import {unstable_doesMiddlewareMatch} from 'next/experimental/testing/server';
import {config} from '../../src/proxy';
it.each(['/brand-guide','/branding','/apiary','/media-guide','/en/urun/example'])('%s genel yolu yönlendirme denetimine girer',url=>{
 expect(unstable_doesMiddlewareMatch({config,nextConfig:{},url})).toBe(true);
});
it.each(['/api/private','/brand/logo-horizontal.svg','/_next/static/main.js','/sitemaps/products-0','/sitemap.xml'])('%s özel dosya yolu proxy dışındadır',url=>{
 expect(unstable_doesMiddlewareMatch({config,nextConfig:{},url})).toBe(false);
});
