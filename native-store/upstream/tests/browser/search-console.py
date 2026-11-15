"""Verify the exact package's ownership tag in crawler HTML and after JS hydration."""
from pathlib import Path
import json, os, shutil, socket, subprocess, time
from playwright.sync_api import sync_playwright, expect

R = Path(__file__).resolve().parents[2]
E = R / 'artifacts/search-console-20261111'
proof = json.loads((E / 'release.json').read_bytes())
release = R / proof['release']
token = json.loads((release / 'private/config.json').read_bytes())['seo']['googleVerification']
runtime = E / 'browser-runtime'
(runtime / 'public').mkdir(parents=True, exist_ok=True)
(runtime / 'storage').mkdir(exist_ok=True)
for file in (release / 'public').iterdir():
    if file.is_file():
        shutil.copyfile(file, runtime / 'public' / file.name)
quote = lambda path: "'" + path.as_posix().replace("'", "\\'") + "'"
(runtime / 'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>" + quote(release / 'private') + ",'storageRoot'=>" + quote(runtime / 'storage') + "];", encoding='utf8')
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
origin = 'http://127.0.0.1:' + str(port)
log = (E / 'browser-server.log').open('w')
server = subprocess.Popen([str(R / 'artifacts/runtime-php/php.exe'), '-S', '127.0.0.1:' + str(port), '-t', str(runtime / 'public'), str(R / 'hosting/dev-router.php')], env={**os.environ, 'NODENO_TEST_PUBLIC': str(runtime / 'public'), 'NODENO_TEST_HTTPS': 'loopback-tls-only'}, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
checks = []
try:
    time.sleep(1)
    with sync_playwright() as pw:
        api = pw.request.new_context()
        assert api.get(origin + '/api/config').json()['seo']['googleVerification'] == token
        for lang in ['tr', 'en', 'ru', 'ar']:
            html = api.get(origin + '/?lang=' + lang)
            assert html.status == 200
            assert html.text().count('name="google-site-verification"') == 1 and 'content="' + token + '"' in html.text()
        for engine, width, lang in [('chromium', 1440, 'tr'), ('webkit', 390, 'ar')]:
            executable = Path.home() / 'AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe' if engine == 'chromium' else R / 'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
            browser = getattr(pw, engine).launch(executable_path=str(executable), headless=True)
            context = browser.new_context(viewport={'width': width, 'height': 844}, is_mobile=width < 768, has_touch=width < 768)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.route('**/media/**', lambda route: route.abort())
            page.route('**/assets/**', lambda route: route.abort())
            page.add_init_script("localStorage.setItem('nodeno.analytics.consent.v1','false');localStorage.setItem('nodeno.international-welcome.hidden','1')")
            for query in ['?lang=' + lang, '?lang=' + lang + '&page=catalog']:
                response = page.goto(origin + '/' + query, wait_until='networkidle')
                assert response.status == 200
                expect(page.locator('#page h1')).to_be_visible(timeout=45000)
                expect(page.locator('meta[name=google-site-verification]')).to_have_count(1)
                expect(page.locator('meta[name=google-site-verification]')).to_have_attribute('content', token)
            assert not errors, errors
            checks.append({'engine': engine, 'width': width, 'lang': lang, 'ssrAndHydratedTag': True, 'passed': True})
            context.close()
            browser.close()
        api.dispose()
    report = {'passed': True, 'live': False, 'releaseHash': proof['releaseHash'], 'ssrLanguages': ['tr', 'en', 'ru', 'ar'], 'checks': checks}
    (E / 'browser.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
finally:
    server.terminate()
    server.wait(timeout=10)
    log.close()
