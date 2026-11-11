/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/proxy.ts
 * Açıklama   : Türkçe ve İngilizce URL yönlendirmesi ile sunucu dilini belirler.
 */
import {NextRequest,NextResponse} from 'next/server';
import {publicRedirect} from './server/seo-management';
export async function proxy(request:NextRequest){
 const pathname=request.nextUrl.pathname;const english=pathname==='/en'||pathname.startsWith('/en/');
 const destination=await publicRedirect(pathname);
 if(destination){const target=new URL(destination,process.env.APP_URL??request.url);target.search=request.nextUrl.search;return NextResponse.redirect(target,308);}
 const headers=new Headers(request.headers);headers.set('x-site-locale',english?'en':'tr');
 if(english){const target=new URL(request.url);target.pathname=pathname.slice(3)||'/';return NextResponse.rewrite(target,{request:{headers}});}
 return NextResponse.next({request:{headers}});
}
export const config={matcher:['/((?!api(?:/|$)|_next(?:/|$)|brand(?:/|$)|media(?:/|$)|fonts(?:/|$)|templates(?:/|$)|uploads(?:/|$)|robots\\.txt$|sitemap\\.xml$|sitemaps(?:/|$)|favicon\\.ico$).*)']};
