#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-product-experience-browser.py
# Açıklama   : Gerçek ürün bilgisi, sayfa içi iade, kalıcı geri bildirim ve keşif akışlarını iki tarayıcıda doğrular.
import base64
import faulthandler
import hashlib
import hmac
import json
import os
import re
import secrets
import struct
import sys
import time
import traceback
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

from playwright.sync_api import Error as BrowserError, expect, sync_playwright
from native_browser_ready import NativePageReadiness

ROOT = Path(__file__).resolve().parent.parent
BASE = os.environ.get('SEXOGATE_NATIVE_TEST_URL', 'https://127.0.0.1:3188/test').rstrip('/')
SCOPE = os.environ.get('SEXOGATE_PRODUCT_EXPERIENCE_SCOPE', os.environ.get('SEXOGATE_MARKETPLACE_SCOPE', 'local'))
assert SCOPE in ('local', 'preview', 'remote')
assert (SCOPE == 'local' and BASE == 'https://127.0.0.1:3188/test') or (SCOPE == 'remote' and BASE == 'https://sexogate.com/test') or (SCOPE == 'preview' and re.fullmatch(r'https://sexogate\.com/test/native-preview-[a-f0-9]{16}', BASE)), 'PRODUCT_EXPERIENCE_SCOPE_INVALID'
REMOTE = BASE.startswith('https://sexogate.com')
ORIGIN = urlsplit(BASE).scheme + '://' + urlsplit(BASE).netloc
ACCESS = json.loads((ROOT / '.local' / ('php-stage-access.json' if REMOTE else 'php-access.json')).read_text('utf8'))
SELECTION = json.loads((ROOT / '.local/native-marketplace-selection.json').read_text('utf8'))
SCRIPT_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
WIDTHS = [360, 390, 430, 768, 1440]
FOLDER = ROOT / ('docs/screenshots/native-store-product-experience-' + SCOPE)
FOLDER.mkdir(parents=True, exist_ok=True)
REPORT = ROOT / ('.local/native-product-experience-' + SCOPE + '.json')
REPORT.unlink(missing_ok=True)
RESULTS = []
NAVIGATION_RETRIES = 0


def safe_error(kind, error, trace):
    message = str(error)
    for value in ACCESS.values():
        if isinstance(value, str) and len(value) >= 4:
            message = message.replace(value, '[private]')
    message = re.sub(r'(?im)^.*(?:cookie:|authorization:|x-csrf-token:).*$', '[private headers]', message)
    positions = [(Path(frame.filename).name, frame.lineno) for frame in traceback.extract_tb(trace)]
    print(kind.__name__ + ': ' + message[:1800] + ' ' + str(positions), file=sys.stderr)


sys.excepthook = safe_error
faulthandler.dump_traceback_later(300, repeat=True)


def navigate(page, target, wait_until='domcontentloaded'):
    global NAVIGATION_RETRIES
    try:
        return page.goto(target, wait_until=wait_until)
    except BrowserError as error:
        if REMOTE or 'net::ERR_TOO_MANY_RETRIES' not in str(error):
            raise
        NAVIGATION_RETRIES += 1
        print('Local HTTPS navigation retry: ' + urlsplit(target).path, flush=True)
        return page.goto(target, wait_until=wait_until)


def persist():
    temporary = REPORT.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(RESULTS, ensure_ascii=False, indent=2) + '\n', 'utf8')
    temporary.replace(REPORT)


def url(**query):
    return BASE + '/?' + urlencode(query)


def dismiss(page):
    gate = page.locator('.sexogate-age-accept')
    if gate.count():
        gate.click()
        page.locator('#sexogate-age-gate').wait_for(state='detached')
    consent = page.get_by_role('button', name='Yalnız gerekli', exact=True)
    if consent.count() and consent.is_visible():
        consent.click()
        consent.wait_for(state='hidden')


def settle(page, readiness):
    readiness.wait()
    deadline = time.monotonic() + 20
    # Gerçek kur isteğinin sonundaki yeniden çizim, ekran yakalama hedefini ayırabilir.
    while any(request.url.split('?', 1)[0] == readiness.optional_url for request in readiness.pending):
        assert time.monotonic() < deadline, 'PRODUCT_EXPERIENCE_FX_SETTLE_TIMEOUT'
        page.wait_for_timeout(50)
    readiness.wait()
    page.evaluate('()=>document.fonts.ready')


def no_overflow(page, label):
    assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth+1'), label


def local_text(value, locale='tr'):
    if isinstance(value, str):
        return value
    return (value or {}).get(locale) or (value or {}).get('en') or (value or {}).get('tr') or ''


def normalized(value):
    return value.casefold().replace('\u0307', '').strip()


def validate_catalog(products):
    assert len(products) == 803 and len({product['id'] for product in products}) == 803, 'PRODUCT_EXPERIENCE_PUBLIC_SET'
    for product in products:
        for locale in ('tr', 'en'):
            title = local_text(product.get('name'), locale).strip()
            description = local_text(product.get('description'), locale).strip()
            story = product.get('storefrontStory', {}).get(locale, {})
            assert title and len(title) <= 300 and '*' not in title, ('PRODUCT_TITLE_NOISE', product['id'], locale)
            assert title.count('(') == title.count(')'), ('PRODUCT_TITLE_UNBALANCED', product['id'], locale)
            assert not re.search(r'\uFFFD|Ã.|Ä[±°]|Å[\u009e\u009f]', title + description), ('PRODUCT_ENCODING', product['id'], locale)
            brand = normalized(product.get('brand') or '')
            assert not brand or not normalized(title).startswith(brand + ' '), ('PRODUCT_DUPLICATE_BRAND', product['id'], locale)
            intro = story.get('intro', '').strip()
            assert description and intro and re.search(r'\s', intro) and len(re.findall(r'[^\W\d_]+', intro, re.UNICODE)) >= 2 and intro[-1] in '.!?', ('PRODUCT_DESCRIPTION_EMPTY_OR_FRAGMENT', product['id'], locale)
            assert intro in description, ('PRODUCT_DESCRIPTION_INTRO_LOST', product['id'], locale)
            for field in story.get('fields', []):
                assert field.get('title') and str(field.get('value', '')).strip(), ('PRODUCT_DESCRIPTION_FIELD_EMPTY', product['id'], locale)
                assert field['title'] + ': ' + str(field['value']) in description, ('PRODUCT_DESCRIPTION_FACT_LOST', product['id'], locale, field.get('key'))
            for text in story.get('paragraphs', []):
                assert text.strip() and text in description, ('PRODUCT_DESCRIPTION_PARAGRAPH_LOST', product['id'], locale)
            for field in ('care', 'safety'):
                assert not story.get(field) or story[field] in description, ('PRODUCT_DESCRIPTION_SAFETY_LOST', product['id'], locale, field)
            assert not re.search(r'yorumlarını inceleyin|Trendyol[’\']?a özel|Trendyol[’\']?dan satın', description, re.I), ('PRODUCT_PLATFORM_CTA', product['id'], locale)
        assert product.get('stockKnown') is False and product.get('stockQuantity') is None, 'INVENTORY_CHANGED'
        assert 'privateRetailReference' not in product and 'sourceVendor' not in product, 'PRIVATE_CATALOG_FIELDS'


def sample_products(products):
    jubels = next((p for p in products if normalized(p.get('brand', '')) == 'jubels' and all(word in normalized(local_text(p.get('name'))) for word in ('bordo', 'kalp', 'dantel'))), None)
    assert jubels, 'JUBELS_REPORTED_PRODUCT_MISSING'
    samples = [jubels]
    for root in ('sg_toys', 'sg_couples', 'sg_accessories', 'sg_care'):
        candidate = next((p for p in products if root in p.get('categoryIds', []) and p['id'] not in {item['id'] for item in samples}), None)
        if candidate:
            samples.append(candidate)
    assert len(samples) == 5, 'PRODUCT_EXPERIENCE_SAMPLE_ROOTS'
    return samples


def check_breadcrumb(page, product, locale):
    expected = local_text(product.get('name'), locale).strip()
    actual=page.locator('#product-title').inner_text().strip()
    assert actual == expected, ('PRODUCT_HEADING_MISMATCH',product['id'],actual,expected)
    assert page.locator('.breadcrumb').first.evaluate('e=>e.lastElementChild.textContent.trim()') == expected, 'BREADCRUMB_PRODUCT_NAME'
    names = page.locator('script[type="application/ld+json"]').evaluate_all('''nodes=>{
      const all=[];const visit=value=>{if(Array.isArray(value)){value.forEach(visit);return;}if(!value||typeof value!=="object")return;if(value["@type"]==="BreadcrumbList")all.push(value);if(value["@graph"])visit(value["@graph"]);};
      nodes.forEach(node=>visit(JSON.parse(node.textContent)));return all.map(value=>value.itemListElement?.at(-1)?.name);
    }''')
    assert expected in names, 'BREADCRUMB_SCHEMA_PRODUCT_NAME'


def check_heading(page, width):
    metrics = page.locator('#product-title').evaluate(r'''h=>{
      const box=h.getBoundingClientRect(),parent=h.parentElement.getBoundingClientRect(),s=getComputedStyle(h),words=[];
      if(h.childNodes.length===1&&h.firstChild.nodeType===3){const text=h.firstChild,textValue=text.textContent,re=/\S+/gu;let match;while((match=re.exec(textValue))){const range=document.createRange();range.setStart(text,match.index);range.setEnd(text,match.index+match[0].length);const rect=range.getBoundingClientRect();words.push({left:rect.left,right:rect.right,top:rect.top,width:rect.width});}}
      const lines=[];for(const word of words){let line=lines.find(v=>Math.abs(v.top-word.top)<2);if(!line){line={top:word.top,words:[]};lines.push(line);}line.words.push(word);}
      const canvas=document.createElement('canvas'),context=canvas.getContext('2d');context.font=s.font;const space=context.measureText(' ').width;
      const premature=lines.slice(0,-1).some((line,index)=>{const last=line.words.at(-1),next=lines[index+1].words[0];return box.right-last.right>=next.width+space+3;});
      return {width:box.width,parent:parent.width,maxWidth:s.maxWidth,fontSize:parseFloat(s.fontSize),br:h.querySelectorAll('br').length,premature,lines:lines.length};
    }''')
    assert metrics['br'] == 0 and metrics['width'] >= metrics['parent'] * .96, ('PRODUCT_HEADING_WIDTH', width, metrics)
    assert metrics['maxWidth'] == 'none' and not metrics['premature'], ('PRODUCT_HEADING_PREMATURE_WRAP', width, metrics)
    assert 20 <= metrics['fontSize'] <= 34, ('PRODUCT_HEADING_FONT', width, metrics)
    no_overflow(page, ('PRODUCT_HEADING_OVERFLOW', width))


def check_footer(page):
    metrics = page.locator('.store-footer .footer-grid>div').first.evaluate('''e=>{const s=getComputedStyle(e,'::after');return {content:s.content,width:parseFloat(s.width),parent:e.getBoundingClientRect().width,height:parseFloat(s.height),background:s.backgroundImage,color:s.backgroundColor,opacity:Number(s.opacity)};}''')
    assert metrics['content'] not in ('none', 'normal') and metrics['width'] >= metrics['parent'] * .8 and .7 <= metrics['height'] <= 3 and metrics['opacity'] > 0, ('FOOTER_DIVIDER_METRICS', metrics)
    assert metrics['background'] != 'none' or metrics['color'] not in ('transparent', 'rgba(0, 0, 0, 0)'), ('FOOTER_DIVIDER_COLOR', metrics)


def check_story_and_features(page, product, locale):
    intro = page.locator('.sg-product-intro')
    assert len(intro.inner_text().strip()) >= 24
    assert intro.evaluate('e=>parseFloat(getComputedStyle(e).fontSize)') >= 15.5, 'PRODUCT_INTRO_TOO_SMALL'
    details = page.locator('.sg-story-details')
    expect(details).to_have_count(1)
    details.locator('summary').focus()
    page.keyboard.press('Enter')
    expect(details).to_have_attribute('open', '')
    expanded = details.locator('.sg-story-expanded')
    assert len(expanded.inner_text().strip()) >= 40 and expanded.locator('p,li').count() >= 1, ('PRODUCT_STORY_MISSING', locale)
    assert expanded.locator('p,li').evaluate_all('nodes=>nodes.every(e=>parseFloat(getComputedStyle(e).fontSize)>=15.5)'), 'PRODUCT_PROSE_TOO_SMALL'
    highlights = page.locator('.sg-highlight-grid>div')
    assert highlights.count() >= 2, 'PRODUCT_HIGHLIGHTS_EMPTY'
    values = highlights.locator('dd').all_inner_texts()
    page.locator('[data-sg-open-features]').click()
    expect(page.locator('#sg-all-features')).to_have_attribute('open', '')
    all_values = page.locator('.sg-attribute-table dd').all_inner_texts()
    assert all(value.strip() in [v.strip() for v in all_values] for value in values), 'PRODUCT_HIGHLIGHT_NOT_IN_SPECIFICATIONS'
    assert product['code'] in all_values, 'PRODUCT_SPECIFICATION_SKU_MISSING'
    assert page.locator('.sg-attribute-table dd').evaluate_all('nodes=>nodes.every(e=>parseFloat(getComputedStyle(e).fontSize)>=13.5)'), 'PRODUCT_SPECIFICATION_TOO_SMALL'


def check_inline_returns(page):
    link = page.locator('.sg-product-section-nav a[href="#product-faq"]')
    before = page.url
    link.focus()
    page.keyboard.press('Enter')
    expect(page.locator('[data-sg-returns-details]')).to_have_attribute('open', '')
    assert urlsplit(page.url).query == urlsplit(before).query and urlsplit(page.url).fragment == 'product-faq', 'RETURN_LEFT_PRODUCT'
    assert page.locator('#product-faq li').count() >= 3 and page.locator('#product-faq').inner_text().strip(), 'RETURN_POLICY_EMPTY'
    page.go_back(wait_until='domcontentloaded')
    page.wait_for_function('(expected)=>location.href===expected', arg=before)
    page.wait_for_function('()=>document.activeElement!==document.body&&document.activeElement!==document.documentElement')


def check_collections_and_rails(page, readiness, catalog, config):
    groups = page.locator('.sg-product-collection')
    assert groups.count() >= 2
    for group in groups.all():
        assert group.locator('.sg-collection-mosaic img').count() == 3, 'COLLECTION_MOSAIC_MISSING'
        target = urlsplit(group.get_attribute('href'))
        assert target.path.startswith(urlsplit(BASE).path + '/') and any(key in parse_qs(target.query) for key in ('category', 'collection')), 'COLLECTION_TARGET_INVALID'
    groups.first.scroll_into_view_if_needed()
    page.wait_for_function('()=>{const images=[...document.querySelectorAll(".sg-product-collection:first-child .sg-collection-mosaic img")];return images.length===3&&images.every(e=>e.complete&&e.naturalWidth>0);}')
    links = page.locator('.sg-related-chips a')
    assert links.count() >= 3 and links.evaluate_all('nodes=>nodes.every(e=>{const u=new URL(e.href);return u.origin===location.origin&&u.searchParams.get("page")==="catalog"&&(u.searchParams.has("category")||u.searchParams.has("collection")||u.searchParams.has("brand"));})'), 'RELATED_DISCOVERY_LINKS_INVALID'
    for link in [*groups.all(), *links.all()]:
        params = parse_qs(urlsplit(link.get_attribute('href')).query)
        if params.get('category'):
            family = {params['category'][0]}
            while True:
                expanded = family | {c['id'] for c in catalog['categories'] if c.get('parentId') in family}
                if expanded == family:
                    break
                family = expanded
            assert any(family.intersection(item.get('categoryIds', [])) for item in catalog['products']), 'DISCOVERY_CATEGORY_HAS_NO_RESULTS'
        elif params.get('brand'):
            assert any((item.get('brand') or item.get('productBrand')) == params['brand'][0] for item in catalog['products']), 'DISCOVERY_BRAND_HAS_NO_RESULTS'
        elif params.get('collection'):
            collection = next((row for row in config.get('collections', []) if str(row['id']) == params['collection'][0] and row.get('data', {}).get('enabled')), None)
            assert collection, 'DISCOVERY_COLLECTION_MISSING'
            raw_ids = collection['data'].get('productIds', [])
            ids = raw_ids if isinstance(raw_ids, list) else [value.strip() for value in raw_ids.split(',')]
            assert any(item['id'] in ids for item in catalog['products']), 'DISCOVERY_COLLECTION_HAS_NO_RESULTS'
    for identifier in ('product-shelf-productSimilar', 'product-shelf-productComplementary', 'product-shelf-selection'):
        rail = page.locator('#' + identifier + ' .sg-product-rail')
        assert rail.locator('.product-card').count() >= 2, ('PRODUCT_RECOMMENDATION_EMPTY', identifier)
        rail.scroll_into_view_if_needed()
        assert rail.evaluate('e=>e.scrollWidth>e.clientWidth+10'), ('PRODUCT_RAIL_NOT_HORIZONTAL', identifier)
    rail = page.locator('#product-shelf-productSimilar .sg-product-rail')
    controls = page.locator('#product-shelf-productSimilar .sg-rail-controls')
    previous, following = controls.locator('[data-sg-step="-1"]'), controls.locator('[data-sg-step="1"]')
    rail.evaluate('e=>e.scrollTo({left:0,behavior:"instant"})')
    expect(previous).to_be_hidden()
    expect(following).to_be_visible()
    following.click()
    page.wait_for_function('e=>Math.abs(e.scrollLeft)>15', arg=rail.element_handle())
    expect(previous).to_be_visible()
    rail.evaluate('e=>e.scrollTo({left:e.scrollWidth-e.clientWidth,behavior:"instant"})')
    expect(following).to_be_hidden()
    expect(previous).to_be_visible()
    previous.click()
    page.wait_for_function('e=>Math.abs(e.scrollLeft)<e.scrollWidth-e.clientWidth-15', arg=rail.element_handle())
    expect(following).to_be_visible()
    rail.focus()
    page.keyboard.press('ArrowLeft')
    before = page.url
    links.first.click()
    readiness.wait()
    assert page.locator('#product-grid .product-card').count() > 0, 'DISCOVERY_LINK_RENDERED_NO_RESULTS'
    page.go_back(wait_until='domcontentloaded')
    settle(page, readiness)
    assert urlsplit(page.url).query == urlsplit(before).query, 'DISCOVERY_BACK_LOST_PRODUCT'


def check_gallery(page, readiness, product, engine):
    page.goto(url(product=product['id'], lang='tr'), wait_until='domcontentloaded')
    settle(page, readiness)
    page.set_viewport_size({'width': 390, 'height': 1000})
    total = len(product['images'])
    assert total >= 2, 'GALLERY_MULTI_IMAGE_CASE_REQUIRED'
    thumbs = page.locator('.gallery-thumbs [data-gallery]')
    expect(thumbs).to_have_count(total)
    seo_images = page.locator('script[type="application/ld+json"]').evaluate_all('''nodes=>{const images=[];const visit=value=>{if(Array.isArray(value)){value.forEach(visit);return;}if(!value||typeof value!=="object")return;if(["Product","ProductGroup"].includes(value["@type"]))images.push(...(Array.isArray(value.image)?value.image:[value.image]).filter(v=>typeof v==="string"));Object.values(value).forEach(visit);};nodes.forEach(node=>visit(JSON.parse(node.textContent)));return images;}''')
    for source in product['images']:
        if '/gallery/' in source:
            assert any(urlsplit(value).path == source for value in seo_images), 'GALLERY_EXTRA_SEO_IMAGE_MISSING_OR_DOUBLE_MOUNT'
    assert page.locator('.gallery-thumbs .image-fallback,.gallery-slide .image-fallback').count() == 0, 'GALLERY_RENDERER_REJECTED_REAL_MEDIA'
    for index, thumb in enumerate(thumbs.all()):
        thumb.scroll_into_view_if_needed()
        expect(thumb.locator('img')).to_have_count(1)
        page.wait_for_function('image=>image.complete&&image.naturalWidth>0', arg=thumb.locator('img').element_handle())
        if '/gallery/' in product['images'][index]:
            thumb.click()
            slide = page.locator('.gallery-slide[data-gallery-slide="' + str(index) + '"]')
            slide.scroll_into_view_if_needed()
            expect(slide.locator('img')).to_have_count(1)
            page.wait_for_function('image=>image.complete&&image.naturalWidth>0', arg=slide.locator('img').element_handle())
            assert urlsplit(slide.locator('img').get_attribute('src')).path == product['images'][index], 'GALLERY_EXTRA_PHOTO_NOT_RENDERED'
    assert all(not button.is_visible() for button in page.locator('[data-gallery-step]').all()), 'SMALL_GALLERY_ARROWS_VISIBLE'
    assert not page.locator('.gallery-points').is_visible(), 'SMALL_GALLERY_POINTS_VISIBLE'
    last = thumbs.last
    last.evaluate('e=>e.blur()')
    last.click()
    expect(last).to_have_attribute('aria-pressed', 'true')
    mouse = last.evaluate('e=>({width:parseFloat(getComputedStyle(e).outlineWidth),style:getComputedStyle(e).outlineStyle})')
    assert mouse['width'] == 0 or mouse['style'] == 'none', 'MOUSE_GALLERY_FOCUS_CHROME'
    page.keyboard.press('Tab')
    last.focus()
    keyboard = last.evaluate('e=>({visible:e.matches(":focus-visible"),width:parseFloat(getComputedStyle(e).outlineWidth),color:getComputedStyle(e).outlineColor})')
    assert keyboard['visible'] and keyboard['width'] >= 2 and keyboard['color'] in ('rgb(142, 15, 56)', 'rgb(90, 10, 32)'), ('GALLERY_FOCUS_THEME', keyboard)
    before_scroll = page.evaluate('()=>scrollY')
    page.locator('.zoom-hint').click()
    dialog = page.locator('#photo-dialog[open]')
    expect(dialog).to_be_visible()
    assert dialog.locator('.image-fallback').count() == 0, 'LIGHTBOX_RENDERER_REJECTED_REAL_MEDIA'
    expect(dialog.locator('.photo-slide img')).to_have_count(total)
    for index in range(total):
        image = dialog.locator('.photo-slide').nth(index).locator('img')
        dialog.locator('.photo-slide').nth(index).scroll_into_view_if_needed()
        page.wait_for_function('image=>image.complete&&image.naturalWidth>0', arg=image.element_handle())
    dialog.locator('.photo-slide').last.scroll_into_view_if_needed()
    counter = page.locator('#photo-counter')
    expect(counter).to_have_text(str(total) + ' / ' + str(total))
    following = dialog.locator('[data-photo-step="1"]')
    previous = dialog.locator('[data-photo-step="-1"]')
    expect(following).to_be_enabled()
    following.click()
    expect(counter).to_have_text('1 / ' + str(total))
    previous.click()
    expect(counter).to_have_text(str(total) + ' / ' + str(total))
    page.keyboard.press('ArrowRight')
    expect(counter).to_have_text('1 / ' + str(total))
    page.keyboard.press('ArrowLeft')
    expect(counter).to_have_text(str(total) + ' / ' + str(total))
    page.screenshot(path=str(FOLDER / (engine + '-gallery-wrap-390.png')))
    page.keyboard.press('Escape')
    expect(page.locator('#photo-dialog')).not_to_be_visible()
    restored = page.locator('.gallery-slide[data-gallery-slide="' + str(total - 1) + '"]')
    expect(restored).to_be_focused()
    focus = restored.evaluate('e=>({visible:e.matches(":focus-visible"),color:getComputedStyle(e).outlineColor,width:parseFloat(getComputedStyle(e).outlineWidth)})')
    assert focus['visible'] and focus['width'] >= 2 and focus['color'] in ('rgb(142, 15, 56)', 'rgb(90, 10, 32)'), ('GALLERY_RETURN_FOCUS_THEME', focus)
    assert abs(page.evaluate('()=>scrollY') - before_scroll) <= 8, 'GALLERY_CLOSE_CHANGED_SCROLL'
    return total


def check_mega(page, readiness, engine):
    page.set_viewport_size({'width': 1440, 'height': 1000})
    trigger = page.locator('#category-trigger')
    trigger.focus()
    page.keyboard.press('Enter')
    menu = page.locator('#mega-menu.sg-mega-menu')
    expect(menu).to_be_visible()
    assert menu.locator('a.sg-mega-card').count() >= 3
    assert menu.locator('.sg-mega-root-photo img').count() == menu.locator('.sg-mega-root-photo').count(), 'MEGA_ROOT_PHOTO_FALLBACK'
    page.wait_for_function('''()=>{const nodes=[...document.querySelectorAll('#mega-menu .sg-mega-card-photo img,#mega-menu .sg-mega-root-photo img')].filter(e=>{const r=e.getBoundingClientRect();return r.top<innerHeight&&r.bottom>0;});return nodes.length>=3&&nodes.every(e=>e.complete&&e.naturalWidth>0);}''')
    assert menu.locator('[data-mega]').count() >= 3
    page.screenshot(path=str(FOLDER / (engine + '-mega-1440.png')))
    page.keyboard.press('Escape')
    expect(menu).to_be_hidden()
    expect(trigger).to_be_focused()


def feedback_flow(page, context, product, engine, hidden_id):
    endpoint = BASE + '/api/product-feedback'
    assert context.request.get(BASE + '/api/admin/product-feedback').status == 401, 'FEEDBACK_ADMIN_PUBLIC'
    bootstrap = context.request.get(endpoint)
    assert bootstrap.status == 200 and 'no-store' in bootstrap.headers.get('cache-control', ''), 'FEEDBACK_BOOTSTRAP_SECURITY'
    csrf = bootstrap.json()['csrfToken']
    valid = {'productId': product['id'], 'reason': 'title', 'note': 'Yerel/önizleme kalite kontrolü: güvenlik doğrulaması.', 'key': secrets.token_hex(16)}
    headers = {'Origin': ORIGIN, 'X-CSRF-Token': csrf}
    assert context.request.post(endpoint, data=valid, headers={**headers, 'X-CSRF-Token': 'tampered'}).status == 403, 'FEEDBACK_CSRF_ACCEPTED'
    headers['X-CSRF-Token'] = context.request.get(endpoint).json()['csrfToken']
    assert context.request.post(endpoint, data=valid, headers={**headers, 'Origin': 'https://invalid.example'}).status == 403, 'FEEDBACK_ORIGIN_ACCEPTED'
    headers['X-CSRF-Token'] = context.request.get(endpoint).json()['csrfToken']
    assert context.request.post(endpoint, data={**valid, 'productId': hidden_id}, headers=headers).status == 404, 'FEEDBACK_HIDDEN_PRODUCT_ACCEPTED'
    headers['X-CSRF-Token'] = context.request.get(endpoint).json()['csrfToken']
    assert context.request.post(endpoint, data={**valid, 'unexpected': True}, headers=headers).status == 422, 'FEEDBACK_UNKNOWN_FIELD_ACCEPTED'
    trigger = page.locator('[data-sg-feedback]').first
    trigger.focus()
    trigger.click()
    dialog = page.locator('dialog[data-sg-feedback-dialog][open]')
    expect(dialog).to_be_visible()
    dialog.locator('input[name=reason][value=title]').check()
    note = 'Yerel/önizleme kalite kontrolü: ' + SCOPE + ' / ' + engine + '. Başlık, ürün bilgileri, ölçü ve özellikler kontrolü. Bu kayıt teknik testtir; müşteri şikâyeti değildir.'
    dialog.locator('textarea[name=note]').fill(note)
    submit = dialog.locator('button[type=submit]')
    expect(submit).to_be_enabled()
    page.screenshot(path=str(FOLDER / (engine + '-feedback-form.png')))
    with page.expect_request(lambda request: request.url == endpoint and request.method == 'POST') as posted:
        with page.expect_response(lambda response: response.url == endpoint and response.request.method == 'POST') as returned:
            submit.click()
    request = posted.value
    response = returned.value
    assert response.status in (200, 201), 'FEEDBACK_SUBMISSION_FAILED'
    data = response.json()
    reference = data['reference']
    assert re.fullmatch(r'SGF-\d{6}-[A-F0-9]{12}', reference) and data['status'] == 'received'
    expect(dialog.locator('[data-feedback-success]')).to_be_visible()
    assert reference in dialog.locator('[data-feedback-reference]').inner_text()
    retry = context.request.post(endpoint, data=request.post_data_json, headers={'Origin': ORIGIN, 'X-CSRF-Token': request.header_value('x-csrf-token')})
    assert retry.status == 200 and retry.json()['reference'] == reference and retry.json()['duplicate'] is True, 'FEEDBACK_DUPLICATED'
    page.screenshot(path=str(FOLDER / (engine + '-feedback-success.png')))
    dialog.locator('[data-feedback-success] [data-feedback-close]').click()
    expect(dialog).to_have_count(0)
    expect(trigger).to_be_focused()
    return reference, note


def otp():
    secret = ACCESS['totpSecret']
    key = base64.b32decode(secret + '=' * ((8 - len(secret) % 8) % 8))
    digest = hmac.new(key, struct.pack('>Q', int(time.time()) // 30), hashlib.sha1).digest()
    offset = digest[-1] & 15
    return str((struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7fffffff) % 1000000).zfill(6)


def admin_feedback(page, context, readiness, reference, note, engine):
    page.goto(BASE + '/yonetim', wait_until='domcontentloaded')
    readiness.wait()
    page.locator('[name=email]').fill(ACCESS['email'])
    page.locator('[name=password]').fill(ACCESS['password'])
    page.get_by_role('button', name='Devam et', exact=True).click()
    page.locator('#verify').wait_for()
    time.sleep(30.1 - time.time() % 30)
    page.locator('[name=proof]').fill(otp())
    page.locator('#verify button[type=submit]').click()
    page.locator('.sidebar').wait_for()
    readiness.wait()
    session = context.request.get(BASE + '/api/admin/session').json()
    assert session.get('user', {}).get('role') == 'owner'
    assert any(cookie['secure'] and cookie['httpOnly'] for cookie in context.cookies()), 'FEEDBACK_ADMIN_COOKIE'
    source = context.request.get(BASE + '/api/admin/catalog-source').json()
    assert source['dataset'] == SELECTION['dataset'], 'PRODUCT_EXPERIENCE_DATASET_MISMATCH'
    endpoint = BASE + '/api/admin/product-feedback/' + reference
    current = context.request.get(endpoint).json()
    assert current['note'] == note and current['status'] == 'new'
    headers = {'Origin': ORIGIN, 'X-CSRF-Token': session['csrfToken']}
    assert context.request.patch(endpoint, data={'version': current['version'] + 3, 'status': 'resolved', 'note': 'Yerel/önizleme kalite kontrolü: eski sürüm testi.'}, headers=headers).status == 409, 'FEEDBACK_VERSION_GUARD'
    assert context.request.patch(endpoint, data={'version': current['version'], 'status': 'resolved', 'note': '', 'unexpected': True}, headers=headers).status == 422, 'FEEDBACK_ADMIN_UNKNOWN_FIELD'
    page.goto(BASE + '/yonetim/urun-geri-bildirimleri', wait_until='domcontentloaded')
    page.locator('[data-feedback-list]').wait_for()
    item = page.locator('[data-feedback-list] article').filter(has=page.get_by_role('heading', name=reference, exact=True))
    expect(item).to_have_count(1)
    item.get_by_role('button', name='İncele', exact=True).click()
    form = page.locator('[data-feedback-review]')
    form.wait_for()
    form.locator('select[name=status]').select_option('resolved')
    review_note = 'Yerel/önizleme kalite kontrolü tamamlandı; teknik test kaydı incelendi.'
    form.locator('textarea[name=note]').fill(review_note)
    with page.expect_response(lambda response: response.url == endpoint and response.request.method == 'PATCH') as updated:
        form.get_by_role('button', name='İncelemeyi kaydet', exact=True).click()
    assert updated.value.status == 200, 'FEEDBACK_ADMIN_REVIEW_FAILED'
    final = updated.value.json()
    assert final['status'] == 'resolved' and final['version'] == current['version'] + 1
    assert final['history'][0]['status'] == 'resolved' and final['history'][0]['note'] == review_note
    page.reload(wait_until='domcontentloaded')
    item = page.locator('[data-feedback-list] article').filter(has=page.get_by_role('heading', name=reference, exact=True))
    expect(item).to_have_count(1)
    expect(item).to_contain_text('Çözüldü')
    item.get_by_role('button', name='İncele', exact=True).click()
    expect(page.locator('[data-feedback-detail]')).to_contain_text(note)
    expect(page.locator('[data-feedback-detail]')).to_contain_text(review_note)
    headers['X-CSRF-Token'] = context.request.get(BASE + '/api/admin/session').json()['csrfToken']
    stale = context.request.patch(endpoint, data={'version': current['version'], 'status': 'new', 'note': ''}, headers=headers)
    assert stale.status == 409 and context.request.get(endpoint).json()['status'] == 'resolved', 'FEEDBACK_STALE_REOPENED'
    page.screenshot(path=str(FOLDER / (engine + '-admin-feedback.png')))
    return final['version']


with sync_playwright() as playwright:
    for engine in ('chromium', 'webkit'):
        NAVIGATION_RETRIES = 0
        faulthandler.cancel_dump_traceback_later()
        faulthandler.dump_traceback_later(300, repeat=True)
        print(engine + ': product experience', flush=True)
        browser = getattr(playwright, engine).launch()
        context = browser.new_context(ignore_https_errors=not REMOTE, viewport={'width': 390, 'height': 1000})
        page = context.new_page()
        page.set_default_timeout(60000)
        readiness = NativePageReadiness(page, BASE, 60000)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        try:
            status = context.request.get(BASE + '/api/deployment-status', timeout=60000).json()
            release = status['release']
            catalog = context.request.get(BASE + '/api/catalog', timeout=60000).json()
            products = catalog['products']
            validate_catalog(products)
            print(engine + ': catalog facts validated', flush=True)
            samples = sample_products(products)
            product = samples[0]
            raw = json.loads((Path(SELECTION['path']) / 'catalog-data.json').read_text('utf8'))
            public_ids = {item['id'] for item in products}
            hidden_id = next(item['id'] for item in raw['products'] if item['id'].startswith('sg_ty_') and item['id'] not in public_ids)
            for sample in samples:
                print(engine + ': sample ' + sample['id'], flush=True)
                navigate(page, url(product=sample['id'], lang='tr'))
                settle(page, readiness)
                dismiss(page)
                check_breadcrumb(page, sample, 'tr')
                fields=[row for row in sample.get('storefrontStory',{}).get('tr',{}).get('fields',[]) if row.get('key')!='productCode']
                assert page.locator('.sg-highlight-grid>div').count() >= min(2,len(fields)), ('PRODUCT_FEATURES_MISSING',sample['id'])
            navigate(page, url(product=product['id'], lang='tr'))
            settle(page, readiness)
            for width in WIDTHS:
                page.set_viewport_size({'width': width, 'height': 1000})
                page.evaluate('()=>document.fonts.ready')
                check_heading(page, width)
                check_footer(page)
                if width in (390, 1440):
                    page.evaluate('()=>window.scrollTo({top:0,left:0,behavior:"instant"})')
                    page.screenshot(path=str(FOLDER / (engine + '-title-' + str(width) + '.png')))
            page.set_viewport_size({'width': 390, 'height': 1000})
            print(engine + ': story and inline returns', flush=True)
            check_story_and_features(page, product, 'tr')
            page.locator('.sg-product-story').scroll_into_view_if_needed()
            page.screenshot(path=str(FOLDER / (engine + '-story-390.png')))
            check_inline_returns(page)
            config = context.request.get(BASE + '/api/config', timeout=60000).json()
            print(engine + ': collections and rails', flush=True)
            check_collections_and_rails(page, readiness, catalog, config)
            page.locator('.sg-product-collections').scroll_into_view_if_needed()
            page.screenshot(path=str(FOLDER / (engine + '-collections-390.png')))
            headings = page.locator('.product-shelf h2').all_inner_texts()
            popularity = config.get('productPopularity', {})
            verified_popularity = popularity.get('source') == 'fulfilled-order-lines' and popularity.get('asOf') and any(type(popularity.get('counts', {}).get(item['id'])) is int and popularity['counts'][item['id']] > 0 for item in products if item['id'] != product['id'])
            assert ('Popüler ürünler' in headings) == bool(verified_popularity), 'FABRICATED_POPULARITY'
            if not verified_popularity:
                assert 'Seçili ürünler' in headings
            print(engine + ': feedback public flow', flush=True)
            reference, note = feedback_flow(page, context, product, engine, hidden_id)
            gallery_product = next((item for item in products if any('/gallery/' in source for source in item.get('images', []))), None)
            assert gallery_product, 'GALLERY_MULTI_IMAGE_PRODUCT_MISSING'
            print(engine + ': gallery', flush=True)
            gallery_count = check_gallery(page, readiness, gallery_product, engine)
            navigate(page, url(product=product['id'], lang='en'))
            print(engine + ': English and RTL', flush=True)
            settle(page, readiness)
            check_breadcrumb(page, product, 'en')
            check_story_and_features(page, product, 'en')
            page.locator('[data-sg-feedback]').first.click()
            english_dialog = page.locator('dialog[data-sg-feedback-dialog][open]')
            expect(english_dialog.locator('h2')).to_have_text('Give feedback')
            page.keyboard.press('Escape')
            expect(english_dialog).to_have_count(0)
            navigate(page, url(product=product['id'], lang='ar'))
            settle(page, readiness)
            assert page.locator('html').get_attribute('dir') == 'rtl'
            no_overflow(page, 'PRODUCT_EXPERIENCE_RTL_OVERFLOW')
            page.locator('.sg-story-details summary').focus()
            page.keyboard.press('Enter')
            expect(page.locator('.sg-story-details')).to_have_attribute('open', '')
            navigate(page, url(product=product['id'], lang='tr'))
            settle(page, readiness)
            check_mega(page, readiness, engine)
            print(engine + ': feedback admin MFA', flush=True)
            reviewed_version = admin_feedback(page, context, readiness, reference, note, engine)
            assert context.request.get(BASE + '/api/deployment-status').json()['release'] == release, 'RELEASE_CHANGED_DURING_PRODUCT_TEST'
            assert not errors, errors
            result = {'engine': engine, 'base': BASE, 'scope': SCOPE, 'release': release, 'dataset': SELECTION['dataset'], 'scriptSha256': SCRIPT_SHA, 'visibleNew': len(products), 'pageErrors': 0, 'realPayments': False,
                'titlesNormalized': True, 'richDescriptions': True, 'featuredFacts': True, 'inlineReturns': True, 'feedbackPersistence': True, 'feedbackSecurity': True, 'adminFeedbackMfa': True, 'relatedCollections': True, 'discoveryLinks': True, 'recommendationRails': True, 'truthfulPopularity': True, 'headingNaturalWrap': True, 'footerDivider': True, 'illustratedMegaMenu': True, 'keyboardAndRtl': True, 'breadcrumbProductName': True,
                'galleryWrap': True, 'railArrowsLogical': True, 'thumbNoChrome': True, 'focusTheme': True, 'galleryScrollPreserved': True,
                'widths': WIDTHS, 'samples': len(samples), 'galleryImageCount': gallery_count, 'feedbackReference': reference, 'feedbackReviewedVersion': reviewed_version, 'qaFeedbackClearlyLabelled': True, 'ordersCreated': False, 'realRefunds': False, 'sourceSnapshotChanged': False, 'localNavigationRetries': NAVIGATION_RETRIES}
            RESULTS.append(result)
            persist()
            print(json.dumps(result, ensure_ascii=False), flush=True)
        except Exception:
            try:
                page.locator('input[name=password],input[name=proof],input[name=code]').evaluate_all('nodes=>nodes.forEach(e=>e.value="")')
                page.screenshot(path=str(FOLDER / (engine + '-diagnostic.png')), timeout=5000)
            except Exception:
                pass
            raise
        finally:
            context.close()
            browser.close()
