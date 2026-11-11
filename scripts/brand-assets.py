# Proje      : SEXSOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/brand-assets.py
# Açıklama   : Özgün marka vektörlerini ve lisanslı yerel font varlıklarını hazırlar.
"""Reproducible original SVG assets and licensed local font acquisition."""
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape
import re
import json
import hashlib
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'public/brand'
M = ROOT / 'public/media'
F = ROOT / 'public/fonts'
T = ROOT / 'tmp/pdfs'
for directory in [B, M, F, T]:
    directory.mkdir(parents=True, exist_ok=True)

def fetch(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 Chrome/131.0.0.0 Safari/537.36'})
    with urlopen(req, timeout=45) as response:
        return response.read()

sources = {}
for directory, filename in [('playfairdisplay', 'PlayfairDisplay[wght].ttf'), ('montserrat', 'Montserrat[wght].ttf'), ('notosansarabic', 'NotoSansArabic[wdth,wght].ttf')]:
    base = 'https://raw.githubusercontent.com/google/fonts/main/ofl/' + directory + '/'
    (F / (directory + '-OFL.txt')).write_bytes(fetch(base + 'OFL.txt'))
    ttf_path = T / filename
    ttf_path.write_bytes(fetch(base + filename.replace('[', '%5B').replace(']', '%5D').replace(',', '%2C')))
    sources[directory] = {'source': base + filename, 'license': base + 'OFL.txt', 'sha256': hashlib.sha256(ttf_path.read_bytes()).hexdigest()}

# Official Google Fonts CSS supplies already licensed, script-specific WOFF2 files.
css_url = 'https://fonts.googleapis.com/css2?family=Montserrat:wght@400..700&family=Noto+Sans+Arabic:wght@400..600&family=Playfair+Display:wght@400..700&display=swap'
css = fetch(css_url).decode()
font_css = []
for block in re.findall(r'/\*.*?\*/\s*@font-face\s*\{.*?\}', css, re.S):
    subset_match = re.search(r'/\*\s*(.*?)\s*\*/', block)
    subset = subset_match.group(1)
    family = re.search(r"font-family: '([^']+)'", block).group(1)
    keep = subset in {'latin', 'latin-ext', 'cyrillic', 'cyrillic-ext'} or (family == 'Noto Sans Arabic' and subset == 'arabic')
    if not keep:
        continue
    url = re.search(r'url\((https://fonts.gstatic.com/[^)]+)\)', block).group(1)
    filename = family.lower().replace(' ', '-') + '-' + subset + '.woff2'
    (F / filename).write_bytes(fetch(url))
    font_css.append(block.replace(url, '/fonts/' + filename))
if not font_css:
    # Some Google CSS user agents receive TTF instead of WOFF2. Container-only
    # compression preserves the complete original glyphs and font names.
    for directory, filename, family, weight in [
        ('playfairdisplay', 'PlayfairDisplay[wght].ttf', 'Playfair Display', '400 700'),
        ('montserrat', 'Montserrat[wght].ttf', 'Montserrat', '400 700'),
        ('notosansarabic', 'NotoSansArabic[wdth,wght].ttf', 'Noto Sans Arabic', '400 600'),
    ]:
        face = TTFont(T / filename)
        face.flavor = 'woff2'
        face.save(F / (directory + '-variable.woff2'))
        font_css.append('@font-face { font-family: "' + family + '"; font-style: normal; font-weight: ' + weight + '; font-display: swap; src: url("/fonts/' + directory + '-variable.woff2") format("woff2"); }')
(F / 'fonts.css').write_text('\n\n'.join(font_css) + '\n', encoding='utf-8')
(F / 'sources.json').write_text(json.dumps({'checked': '2026-11-10', 'cssSource': css_url, 'families': sources}, indent=2), encoding='utf-8')

# Wordmark is outlined from the licensed Playfair Display font, not a raster image.
font = TTFont(T / 'PlayfairDisplay[wght].ttf')
glyphs = font.getGlyphSet()
cmap = font.getBestCmap()
upm = font['head'].unitsPerEm
def outline(text, x, baseline, size, tracking=0):
    scale = size / upm
    paths = []
    cursor = x
    for char in text:
        name = cmap.get(ord(char))
        if name:
            pen = SVGPathPen(glyphs)
            glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cursor, baseline)))
            paths.append('<path d="' + pen.getCommands() + '"/>')
            cursor += glyphs[name].width * scale + tracking
    return ''.join(paths), cursor-x-tracking

def svg(width, height, content, title, extra=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title" {extra}><title id="title">{escape(title)}</title>{content}</svg>\n'

metal = '<defs><linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#FBE6DD"/><stop offset=".23" stop-color="#E7B4BD"/><stop offset=".46" stop-color="#FFF5EE"/><stop offset=".65" stop-color="#B66C80"/><stop offset=".83" stop-color="#E7B4BD"/><stop offset="1" stop-color="#FBE6DD"/></linearGradient></defs>'
def mark(color='url(#metal)', small=False):
    # Hand-built curves preserve the arch, S, horns and graceful tail relationship.
    arch = '<path d="M44 220V106C44 24 196 24 196 106V220" fill="none" stroke="'+color+'" stroke-width="2.8" opacity=".8"/>'
    if not small:
        arch += '<path d="M59 219V106C59 42 181 42 181 106V219M76 219V91M164 219V91" fill="none" stroke="'+color+'" stroke-width="1.3" opacity=".48"/>'
    horns = '<path d="M80 51C55 44 64 18 83 5C71 24 77 35 97 39ZM160 51C185 44 176 18 157 5C169 24 163 35 143 39Z" fill="'+color+'"/>'
    s = '<path d="M172 57V104H167C159 75 143 51 119 51C98 51 82 62 82 80C82 101 106 112 132 125C163 140 181 159 178 184C175 218 148 238 116 238C94 238 78 230 65 224L57 239H52V184H58C68 213 88 230 113 230C139 230 153 217 153 199C153 178 131 166 105 153C74 138 55 119 58 93C62 60 89 41 119 41C136 41 151 46 163 52L168 57Z" fill="'+color+'"/>'
    tail = '<path d="M18 229C42 202 70 212 101 229C137 249 192 245 218 202" fill="none" stroke="'+color+'" stroke-width="5" stroke-linecap="round"/><path d="M204 205L229 184L220 217L216 206Z" fill="'+color+'"/>'
    return arch+horns+s+tail

(B/'symbol.svg').write_text(svg(240,260,metal+mark(),'SEXSOGATE - S, kemer, boynuz ve kuyruk simgesi'),encoding='utf-8')
for suffix, color in [('dark','#5A0A20'),('light','#FBF4EF')]:
    (B/f'symbol-{suffix}.svg').write_text(svg(240,260,mark(color),'SEXSOGATE tek renk simge'),encoding='utf-8')

wordmark, wm_width = outline('SEXSOGATE',0,85,83,3)
tagline, tagline_width = outline('Tutkunu Keşfet.',0,36,31,2)
horizontal_content = metal+'<g transform="translate(12 7) scale(.36)">'+mark()+'</g><g fill="#5A0A20" transform="translate(112 13)">'+wordmark+'</g>'
(B/'logo-horizontal.svg').write_text(svg(690,114,horizontal_content,'SEXSOGATE'),encoding='utf-8')
for suffix, color in [('dark','#5A0A20'),('light','#FBF4EF')]:
    content = '<g transform="translate(12 7) scale(.36)">'+mark(color)+'</g><g fill="'+color+'" transform="translate(112 13)">'+wordmark+'</g>'
    (B/f'logo-horizontal-{suffix}.svg').write_text(svg(690,114,content,'SEXSOGATE'),encoding='utf-8')
vertical = metal+'<g transform="translate(225 10) scale(1)">'+mark()+'</g><g fill="url(#metal)" transform="translate(65 270)">'+wordmark+'</g><g fill="#E7B4BD" transform="translate('+str((690-tagline_width)/2)+' 365)">'+tagline+'</g>'
(B/'logo-vertical.svg').write_text(svg(690,420,vertical,'SEXSOGATE - Tutkunu Keşfet.'),encoding='utf-8')
(B/'favicon.svg').write_text(svg(32,32,'<rect width="32" height="32" rx="7" fill="#5A0A20"/><g transform="translate(3 1) scale(.108)">'+mark('#FBF4EF',True)+'</g>','SEXSOGATE'),encoding='utf-8')
(B/'social-profile.svg').write_text(svg(1080,1080,'<rect width="1080" height="1080" rx="180" fill="#5A0A20"/>'+metal+'<path d="M130 955V420C130 23 950 23 950 420V955" fill="none" stroke="#E7B4BD" stroke-width="2" opacity=".25"/><g transform="translate(240 190) scale(2.5)">'+mark()+'</g>','SEXSOGATE sosyal profil'),encoding='utf-8')

silk = '<defs><linearGradient id="bg" x1="0" y1=".5" x2="1" y2=".4"><stop stop-color="#5A0A20"/><stop offset=".65" stop-color="#300511"/><stop offset="1" stop-color="#1D020B"/></linearGradient><linearGradient id="fold" x1="0" y1="0" x2=".7" y2="1"><stop stop-color="#26020C"/><stop offset=".37" stop-color="#8E0F38"/><stop offset=".48" stop-color="#E7B4BD"/><stop offset=".52" stop-color="#A92750"/><stop offset=".63" stop-color="#5A0A20"/><stop offset="1" stop-color="#170208"/></linearGradient><linearGradient id="silk" x1="0" y1="0" x2="1" y2=".8"><stop stop-color="#370511"/><stop offset=".4" stop-color="#8E0F38"/><stop offset=".52" stop-color="#B85C76"/><stop offset=".58" stop-color="#5A0A20"/><stop offset="1" stop-color="#26030C"/></linearGradient><radialGradient id="glow"><stop stop-color="#E7B4BD" stop-opacity=".22"/><stop offset="1" stop-color="#E7B4BD" stop-opacity="0"/></radialGradient></defs><rect width="1600" height="900" fill="url(#bg)"/><ellipse cx="1150" cy="390" rx="450" ry="450" fill="url(#glow)"/><path d="M840 900V340C840-70 1440-70 1440 340V900" fill="none" stroke="#E7B4BD" stroke-opacity=".25" stroke-width="1.5"/><path d="M870 900V345C870-20 1410-20 1410 345V900" fill="none" stroke="#E7B4BD" stroke-opacity=".13"/><path d="M780 900C880 640 1040 630 1122 448C1190 289 1270 232 1600 210V900Z" fill="url(#fold)"/><path d="M910 900C1120 595 1200 633 1300 470C1400 310 1480 360 1600 277V900Z" fill="url(#silk)"/><path d="M1090 900C1250 710 1460 790 1600 585V900Z" fill="url(#fold)"/><path d="M970 900C1090 645 1205 620 1290 484" fill="none" stroke="#E7B4BD" stroke-opacity=".18" stroke-width="2"/>'
(B/'hero-silk.svg').write_text(svg(1600,900,silk,'Bordo ipek kıvrımları ve zarif kapı kemeri'),encoding='utf-8')

# Original, intentionally non-photographic development fixture illustrations.
product_defs = '<defs><linearGradient id="fabric" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#A24B65"/><stop offset=".28" stop-color="#6E1531"/><stop offset=".5" stop-color="#A7546E"/><stop offset=".7" stop-color="#5A0A20"/><stop offset="1" stop-color="#350713"/></linearGradient><linearGradient id="rose"><stop stop-color="#F6D6CD"/><stop offset=".5" stop-color="#C58695"/><stop offset="1" stop-color="#E7B4BD"/></linearGradient><radialGradient id="floor"><stop stop-color="#5A0A20" stop-opacity=".17"/><stop offset="1" stop-color="#5A0A20" stop-opacity="0"/></radialGradient></defs>'
drawings = [
    '<path d="M98 290C170 263 190 270 222 283M378 283C410 270 430 263 502 290" fill="none" stroke="#8E0F38" stroke-width="9"/><path d="M152 262C189 246 236 244 300 263C364 244 411 246 448 262L432 345C414 380 352 388 319 343L300 320L281 343C248 388 186 380 168 345Z" fill="url(#fabric)"/><path d="M162 273C210 255 253 263 300 278C347 263 390 255 438 273" fill="none" stroke="#E7B4BD" stroke-width="2"/><path d="M181 330C219 360 251 354 278 317M322 317C349 354 381 360 419 330" fill="none" stroke="#E7B4BD" stroke-opacity=".55" stroke-width="2"/>',
    '<path d="M211 145L237 150L242 214H358L363 150L389 145L410 240L366 276L390 455C325 477 275 477 210 455L234 276L190 240Z" fill="url(#fabric)"/><path d="M243 213C260 244 285 237 300 221C315 237 340 244 357 213" fill="none" stroke="#E7B4BD" stroke-width="3"/><path d="M218 440C273 460 327 460 382 440" fill="none" stroke="#E7B4BD" stroke-width="2"/><path d="M255 265C265 328 260 388 246 438M347 265C335 328 340 388 354 438" fill="none" stroke="#E7B4BD" stroke-opacity=".28" stroke-width="2"/>',
    '<path d="M151 240L300 192L449 240L300 291Z" fill="#A7546E"/><path d="M151 240V405L300 465V291Z" fill="#5A0A20"/><path d="M449 240V405L300 465V291Z" fill="#3C0919"/><path d="M139 220L300 171L461 220V252L300 306L139 252Z" fill="url(#fabric)"/><path d="M280 180L303 174L328 298V453L300 465L280 456V299Z" fill="url(#rose)"/><path d="M302 214C220 220 206 159 235 152C264 145 288 191 302 214C320 179 347 147 367 163C387 180 359 214 302 214Z" fill="none" stroke="#E7B4BD" stroke-width="12"/>',
    '<path d="M203 190C240 200 360 200 397 190L416 406C410 465 190 465 184 406Z" fill="url(#fabric)"/><path d="M194 222C241 243 358 243 406 222" fill="none" stroke="#E7B4BD" stroke-width="3"/><path d="M214 195C229 161 372 161 386 195" fill="none" stroke="#5A0A20" stroke-width="6"/><path d="M211 220C218 281 192 268 167 294M390 220C381 280 409 266 435 294" fill="none" stroke="#5A0A20" stroke-width="4"/><path d="M300 274C253 274 266 312 300 323C345 339 322 364 286 350" fill="none" stroke="#E7B4BD" stroke-width="4"/>',
    '<path d="M220 195C195 215 194 259 218 281C242 303 278 296 293 271C311 242 297 205 271 192C253 183 232 184 220 195Z" fill="none" stroke="url(#rose)" stroke-width="24"/><path d="M328 285C301 300 291 337 308 366C326 396 366 405 392 383C417 363 419 326 397 301C377 279 351 274 328 285Z" fill="none" stroke="url(#rose)" stroke-width="24"/><path d="M284 272L316 302" stroke="#8E0F38" stroke-width="10" stroke-linecap="round"/><path d="M278 277L310 308" stroke="#E7B4BD" stroke-width="3"/>',
    '<path d="M272 151H328V207C350 217 364 231 364 262V414C364 448 236 448 236 414V262C236 231 250 217 272 207Z" fill="url(#rose)"/><rect x="263" y="137" width="74" height="55" rx="7" fill="#5A0A20"/><rect x="248" y="285" width="104" height="95" rx="1" fill="#FBF4EF"/><path d="M300 301C278 300 281 319 301 326C326 336 314 354 288 345" fill="none" stroke="#8E0F38" stroke-width="3"/><path d="M267 368H333" stroke="#E7B4BD" stroke-width="2"/>',
]
names = ['Saten göz maskesi', 'Saten gecelik', 'Bordo hediye kutusu', 'Kadife saklama kesesi', 'Çift aksesuarı', 'Bakım ürünü ambalajı']
for i,(drawing,name) in enumerate(zip(drawings,names),1):
    scene = product_defs+'<rect width="600" height="600" fill="#F3E6E8"/><path d="M0 490C180 455 405 445 600 490V600H0Z" fill="#EAD9DC"/><ellipse cx="300" cy="470" rx="210" ry="45" fill="url(#floor)"/>'+drawing
    (M/f'atelier-{i:02}.svg').write_text(svg(600,600,scene,name+' - yerel geliştirme illüstrasyonu'),encoding='utf-8')

def social(theme, story=False):
    width, height = 1080, 1920 if story else 1350
    dark = theme == 'dark'
    bg, fg = ('#5A0A20','#FBF4EF') if dark else ('#FBF4EF','#5A0A20')
    content = '<rect width="1080" height="'+str(height)+'" fill="'+bg+'"/>'+metal
    content += '<path d="M100 '+str(height-80)+'V560C100 50 980 50 980 560V'+str(height-80)+'" fill="none" stroke="'+('#E7B4BD' if dark else '#B7808D')+'" stroke-width="2" opacity=".5"/>'
    content += '<g transform="translate(420 160)">'+mark('url(#metal)' if dark else '#5A0A20')+'</g>'
    content += '<g fill="'+fg+'" transform="translate(255 450)">'+wordmark+'</g>'
    content += f'<text x="540" y="{755 if not story else 850}" fill="{fg}" font-family="Playfair Display, Georgia, serif" font-size="104" text-anchor="middle">Tutkunu</text><text x="540" y="{880 if not story else 975}" fill="{fg}" font-family="Playfair Display, Georgia, serif" font-size="104" font-style="italic" text-anchor="middle">Keşfet.</text>'
    content += f'<text x="540" y="{height-175}" fill="{fg}" font-family="Montserrat, Arial, sans-serif" font-size="24" letter-spacing="5" text-anchor="middle">YENİ KOLEKSİYON</text><path d="M455 {height-125}H625M607 {height-137}L625 {height-125}L607 {height-113}" fill="none" stroke="{fg}" stroke-width="2"/>'
    return svg(width,height,content,'SEXSOGATE düzenlenebilir '+('hikâye' if story else 'gönderi')+' tasarım şablonu')
for theme in ['light','dark']:
    (B/f'social-post-{theme}.svg').write_text(social(theme),encoding='utf-8')
    (B/f'social-story-{theme}.svg').write_text(social(theme,True),encoding='utf-8')
cover_content = '<rect width="1640" height="624" fill="#5A0A20"/>'+metal+'<g transform="translate(100 135) scale(1.3)">'+mark()+'</g><g fill="#FBF4EF" transform="translate(470 165)">'+wordmark+'</g><g fill="#E7B4BD" transform="translate(480 290)">'+tagline+'</g><path d="M1220 624V250C1220 30 1550 30 1550 250V624" fill="none" stroke="#E7B4BD" opacity=".35"/>'
(B/'social-cover.svg').write_text(svg(1640,624,cover_content,'SEXSOGATE sosyal kapak'),encoding='utf-8')

og = '<rect width="1200" height="630" fill="#5A0A20"/>'+metal+'<path d="M825 630V235C825-5 1130-5 1130 235V630" fill="none" stroke="#E7B4BD" stroke-width="2" opacity=".35"/><g transform="translate(887 188) scale(.7)">'+mark()+'</g><g fill="#FBF4EF" transform="translate(75 138)">'+wordmark+'</g><g fill="#E7B4BD" transform="translate(80 278) scale(1.5)">'+tagline+'</g><text x="82" y="490" fill="#FBF4EF" font-family="Montserrat, Arial, sans-serif" font-size="19" letter-spacing="4">YAKINLIĞI YENİDEN TANIMLA</text>'
(B/'share-preview.svg').write_text(svg(1200,630,og,'SEXSOGATE - Tutkunu Keşfet. paylaşım önizlemesi'),encoding='utf-8')
product_social = '<rect width="1080" height="1350" fill="#5A0A20"/>'+metal+'<g fill="#FBF4EF" transform="translate(255 75)">'+wordmark+'</g><g transform="translate(120 300) scale(1.4)">'+product_defs+'<rect width="600" height="600" fill="#F3E6E8"/>'+drawings[0]+'</g><text data-field="product-title" x="90" y="1180" fill="#FBF4EF" font-family="Playfair Display, Georgia, serif" font-size="59">Saten Göz Maskesi</text><text data-field="product-cta" x="90" y="1250" fill="#E7B4BD" font-family="Montserrat, Arial, sans-serif" font-size="25">Kendine ayırdığın bir an.</text>'
(B/'social-product-dark.svg').write_text(svg(1080,1350,product_social,'SEXSOGATE düzenlenebilir ürün tanıtımı'),encoding='utf-8')
collection_social = '<rect width="1080" height="1350" fill="#FBF4EF"/>'+metal+'<g fill="#5A0A20" transform="translate(255 75)">'+wordmark+'</g><path d="M90 1060V540C90 25 990 25 990 540V1060" fill="#F3E6E8"/><g transform="translate(210 280) scale(1.1)">'+product_defs+drawings[2]+'</g><text data-field="collection-title" x="90" y="1110" fill="#5A0A20" font-family="Playfair Display, Georgia, serif" font-size="69">Yakınlığı yeniden</text><text x="90" y="1205" fill="#5A0A20" font-family="Playfair Display, Georgia, serif" font-size="69">tanımla.</text><text data-field="collection-cta" x="90" y="1280" fill="#5A0A20" font-family="Montserrat, Arial, sans-serif" font-size="24" letter-spacing="3">HEDİYE KOLEKSİYONU</text>'
(B/'social-collection-light.svg').write_text(svg(1080,1350,collection_social,'SEXSOGATE düzenlenebilir koleksiyon tanıtımı'),encoding='utf-8')
information_social = '<rect width="1080" height="1350" fill="#FBF4EF"/>'+metal+'<g fill="#5A0A20" transform="translate(255 75)">'+wordmark+'</g><g transform="translate(465 260) scale(.6)">'+mark('#5A0A20')+'</g><text data-field="article-title" x="90" y="600" fill="#5A0A20" font-family="Playfair Display, Georgia, serif" font-size="77">Özenle sakla.</text><path d="M90 665H990" stroke="#E7B4BD" stroke-width="2"/><g data-field="article-summary" fill="#24191D" font-family="Montserrat, Arial, sans-serif" font-size="29"><text x="90" y="765">Üreticinin bakım talimatını incele.</text><text x="90" y="835">Her ürünü uygun koşullarda sakla.</text><text x="90" y="905">Ambalaj ve kullanım uyarılarını koru.</text></g><text data-field="article-cta" x="90" y="1210" fill="#5A0A20" font-family="Montserrat, Arial, sans-serif" font-size="24" letter-spacing="3">REHBERİ KEŞFET</text>'
(B/'social-information-light.svg').write_text(svg(1080,1350,information_social,'SEXSOGATE düzenlenebilir bilgilendirici kart'),encoding='utf-8')
print(json.dumps({'brandFiles':len(list(B.glob('*.svg'))),'mediaFiles':len(list(M.glob('*.svg'))),'fontFiles':len(list(F.glob('*.woff2'))),'fontBytes':sum(p.stat().st_size for p in F.glob('*.woff2'))},indent=2))
