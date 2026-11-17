#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/prepare-native-product-editorial.py
# Açıklama   : Değişmez katalogdan yalnız ürün anlatımında kullanılabilecek gerçek nitelikleri özel ek girdiye ayırır.
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = {
    'Renk', 'Materyal', 'Malzeme', 'Materyal Bileşeni', 'Kumaş Tipi', 'Desen', 'Dokuma Tipi',
    'Siluet', 'Yaka Tipi', 'Kol Tipi', 'Kol Boyu', 'Kalıp', 'Boy', 'Boy / Ölçü', 'Hacim',
    'Adet', 'Paket İçeriği', 'Titreşim', 'Çalışma Tipi', 'Özellik', 'Aroma',
    'Ürün Güvenliği Bilgisi', 'Yıkama Talimatı', 'Bakım Talimatı', 'Kullanım Uyarısı',
}


def main():
    selection = json.loads((ROOT / '.local/native-marketplace-selection.json').read_text('utf8'))
    prepared = Path(selection['path'])
    raw = (prepared / 'catalog-data.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != selection['sha256']:
        raise ValueError('EDITORIAL_SOURCE_HASH_MISMATCH')
    catalog = json.loads(raw)
    work = {key: value for path in (prepared / 'catalog-workbench').glob('*.json')
            for key, value in json.loads(path.read_text('utf8')).items()}
    records = {}
    for product in catalog['products'][2194:]:
        entry = work[product['id']]
        if product['code'] != 'seo-' + entry['source']['sourceSku']:
            raise ValueError('EDITORIAL_SOURCE_CODE_MISMATCH')
        records[product['id']] = {
            'sku': product['sku'], 'sourceCode': entry['source']['sourceSku'],
            'sourceSha256': entry['source']['htmlSha256'],
            'rawOriginalTitle': entry.get('rawSourceTitle') or product['name']['tr'],
            'catalogName': {locale: product['name'].get(locale, '') for locale in ('tr', 'en')},
            'catalogSeoTitle': {locale: product.get('seoTitle', {}).get(locale, '') for locale in ('tr', 'en')},
            'catalogSeoDescription': {locale: product.get('seoDescription', {}).get(locale, '') for locale in ('tr', 'en')},
            'catalogFacts': product['facts'],
            'attributes': [a for a in entry.get('sourceAttributes', []) if a.get('name') in ALLOWED],
            'activeSizes': list(dict.fromkeys(a['value'] for v in entry.get('sourceVariants', [])
                if v.get('isActive') is True for a in v.get('attributes', []) if a.get('name') == 'Beden')),
        }
    result = {'schema': 1, 'dataset': selection['dataset'], 'catalogSha256': selection['sha256'], 'products': records}
    output = ROOT / 'native-store/storefront/product-editorial-data.json'
    output.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf8')
    if hashlib.sha256((prepared / 'catalog-data.json').read_bytes()).hexdigest() != selection['sha256']:
        raise ValueError('EDITORIAL_SOURCE_CHANGED')
    print(json.dumps({'products': len(records), 'sourcePreserved': True, 'output': str(output.relative_to(ROOT))}))


if __name__ == '__main__':
    main()
