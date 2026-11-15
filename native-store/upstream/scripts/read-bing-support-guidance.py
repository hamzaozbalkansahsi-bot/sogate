"""Read the public Bing guidance page in a fresh anonymous browser."""
from pathlib import Path
from datetime import datetime, timezone
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/indexnow-bing-guidance-20261112'
URL = 'https://www.bing.com/webmasters/help/webmaster-support-24ab5ebf?source=supportmail&type=generalguidance&action=usefulinfo'


def main():
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome',headless=True)
        context = browser.new_context(viewport={'width': 1366, 'height': 1000}, locale='en-US')
        page = context.new_page()
        response = page.goto(URL, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(8000)
        text = page.locator('body').inner_text(timeout=15000)
        links = page.locator('a[href]').evaluate_all('(els) => els.map(e => ({text:e.textContent.trim(),href:e.href})).filter(x => x.text)')
        record = {'checkedAt': datetime.now(timezone.utc).isoformat(), 'requestedUrl': URL, 'httpStatus': response.status if response else None, 'finalUrl': page.url, 'title': page.title(), 'bodyText': text, 'links': links, 'anonymous': True, 'supportMessageSent': False, 'indexNowNotificationSent': False}
        (OUT/'public-guidance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        page.screenshot(path=str(OUT/'public-guidance.png'),full_page=True)
        print(json.dumps(record,ensure_ascii=True))
        context.close()
        browser.close()


if __name__ == '__main__':
    main()
