"""Read the installed Turhost checkbox state without submitting or saving forms."""
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import argparse
import importlib.util
import json
import re
import requests

ROOT = Path(__file__).resolve().parents[1]


class CheckboxReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.boxes = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag == 'input' and fields.get('type', '').lower() == 'checkbox':
            value = fields.get('value', '')
            self.boxes.append({'name': fields.get('name'), 'id': fields.get('id'), 'botValue': value if re.fullmatch(r'[A-Za-z0-9_-]{1,80}', value) else None, 'checked': 'checked' in fields})

    def handle_data(self, data):
        self.text.append(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    assert output.is_relative_to((ROOT/'artifacts').resolve())
    output.mkdir(exist_ok=True)
    spec = importlib.util.spec_from_file_location('hosting_probe', ROOT/'scripts/hosting-probe.py')
    hosting = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hosting)
    response = requests.get('https://srvc77.trwww.com:2083/frontend/jupiter/BlockBot/index.live.php', auth=hosting.credentials(), timeout=40, allow_redirects=False)
    reader = CheckboxReader()
    if response.status_code == 200:
        reader.feed(response.text)
    text = ' '.join(reader.text)
    result = {'checkedAt': datetime.now(timezone.utc).isoformat(), 'readOnly': True, 'httpStatus': response.status_code, 'settingsChanged': False, 'moduleTitleFound': 'Turhost Bot Engelleme' in text, 'checkboxes': reader.boxes, 'actualSearchEngineIpAccessProven': False}
    (output/'bot-module-state.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True))


if __name__ == '__main__':
    main()
