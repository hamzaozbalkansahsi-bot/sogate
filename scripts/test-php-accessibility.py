#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-php-accessibility.py
# Açıklama   : Gerçek müşteri ekranlarında axe, yaş bildirimi klavyesi ve özel veri sızdırmayan ağ kontrolü.
import json,sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent.parent
remote='--remote' in sys.argv;base='https://sexogate.com/test' if remote else 'http://127.0.0.1:3183/test'
access=json.loads((root/('.local/php-stage-access.json' if remote else '.local/php-access.json')).read_text('utf8'))
axe=(root/'node_modules/axe-core/axe.min.js').read_text('utf8');results=[]
with sync_playwright() as p:
    for engine in ['chromium','webkit']:
        browser=getattr(p,engine).launch(headless=True);context=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce');page=context.new_page();page.set_default_navigation_timeout(60000 if remote else 30000);outside=set()
        page.on('request',lambda request:outside.add(urlparse(request.url).hostname) if urlparse(request.url).scheme in ['http','https'] and urlparse(request.url).hostname!=urlparse(base).hostname else None)
        try:
            page.goto(base+'/');page.wait_for_load_state('networkidle');page.locator('#age-notice[open]').wait_for()
            page.evaluate(axe)
            age_report=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})")
            results.append({'engine':engine,'path':'/ [age open]','width':390,'violations':[{'rule':v['id'],'impact':v['impact'],'targets':[n['target'] for n in v['nodes']]} for v in age_report['violations']],'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')})
            assert page.locator('#age-notice button').count()==2, 'Exit must be a keyboard-reachable action'
            page.locator('#age-accept').focus();page.keyboard.press('Tab');assert page.locator('#age-exit').evaluate('(node)=>node===document.activeElement')
            page.keyboard.press('Shift+Tab');assert page.locator('#age-accept').evaluate('(node)=>node===document.activeElement');page.keyboard.press('Enter');assert not page.locator('#age-notice').is_visible();assert page.locator('main').evaluate('(node)=>node===document.activeElement')
            for path in ['/','/urunler','/urun/saten-bag-detayi','/sepet','/hesap','/rehber','/sss','/en/hesap']:
                response=page.goto(base+path);assert response.status==200,(path,response.status);page.wait_for_load_state('networkidle');page.evaluate(axe)
                report=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})")
                violations=[{'rule':v['id'],'impact':v['impact'],'targets':[n['target'] for n in v['nodes']]} for v in report['violations']]
                results.append({'engine':engine,'path':path,'width':390,'violations':violations,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')})
            assert not outside, 'Unexpected third-party host'
            names=[c['name'] for c in context.cookies()];assert not any(n.startswith(('_ga','_fbp','_gcl')) for n in names),'Advertising cookie before consent'
            exit_context=browser.new_context();exit_page=exit_context.new_page()
            try:
                exit_page.goto(base+'/');exit_page.wait_for_load_state('networkidle');exit_page.locator('#age-exit').focus()
                with exit_page.expect_navigation():exit_page.keyboard.press('Enter')
                assert exit_page.url=='about:blank','Age exit did not leave the site'
            finally:exit_context.close()
        finally:context.close();browser.close()
target=root/('.local/php-accessibility-remote.json' if remote else '.local/php-accessibility-local.json');target.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
failed=[{'engine':r['engine'],'path':r['path'],'rules':[v['rule'] for v in r['violations']],'overflow':r['overflow']} for r in results if r['violations'] or r['overflow']]
print(json.dumps({'pages':len(results),'keyboardAgeNotice':True,'keyboardExit':True,'unexpectedThirdPartyHosts':0,'failures':failed}))
raise SystemExit(1 if failed else 0)
