"""Import exact identities from the completed PDF, keeping 42 records for review."""
import csv
import hashlib
import io
import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]


def main():
    proof = json.loads((ROOT / 'artifacts/catalog-expansion/pdf/complete-identities.json').read_bytes())
    pdf = ROOT / 'output/pdf' / proof['outputPdf']['file']
    if pdf.name != 'NODENO_Mobilya_Katalogu_2026_Tam_Katalog.pdf' or hashlib.sha256(pdf.read_bytes()).hexdigest() != proof['outputPdf']['sha256']:
        raise ValueError('Complete PDF identity mismatch')
    source_bytes = (ROOT / 'data/catalog-source.json').read_bytes()
    source = json.loads(source_bytes)
    originals = {str(p['id']): p for p in source['products']}
    notes = json.loads((ROOT / 'data/catalog-identity-notes.json').read_bytes())
    names, products, pdf_only = {}, [], []
    with fitz.open(pdf) as doc:
        if len(doc) != proof['outputPdf']['pages']:
            raise ValueError('Complete PDF page count changed')
        for row in proof['products']:
            row = {**row, 'name': {lang: re.sub(r'\s+', ' ', value).strip() for lang, value in row['name'].items()}}
            title = row['name']['tr']
            index_text = doc[row['indexPage'] - 1].get_text()
            folded = lambda value: re.sub(r'\s+', ' ', value).strip()
            if row['code'] not in index_text or folded(title) not in folded(index_text):
                raise ValueError('Code/name absent from actual full PDF index: ' + row['code'])
            if row['code'] not in doc[row['cataloguePage'] - 1].get_text():
                raise ValueError('Code absent from actual product page: ' + row['code'])
            if row['id'] is None:
                pdf_only.append({'code': row['code'], 'name': title, 'cataloguePage': row['cataloguePage'], 'indexPage': row['indexPage']})
                continue
            original = originals.get(row['id'])
            if not original or row['sourceCode'] != original['code'] or row['code'] != 'Ndn-' + original['code']:
                raise ValueError('Wrong source identity')
            if title in names and names[title] != row['name']:
                raise ValueError('Conflicting name translations')
            names[title] = row['name']
            entry = {'id': row['id'], 'sourceCode': original['code'], 'sourceName': original['title'], 'code': row['code'], 'name': title, 'cataloguePage': row['cataloguePage'], 'indexPage': row['indexPage']}
            if row['id'] in notes:
                if notes[row['id']]['sourceCode'] != original['code']:
                    raise ValueError('Wrong part note identity')
                entry['notes'] = notes[row['id']]['notes']
            products.append(entry)
    if len(products) != 667 or len({p['id'] for p in products}) != 667 or len(pdf_only) != 42 or len({p['code'] for p in proof['products']}) != 709:
        raise ValueError('Incomplete full-catalogue coverage')
    mapping = {'schema': 1, 'sourcePdf': proof['outputPdf'], 'originalPdf': proof['sourcePdf'], 'sourceCatalogSha256': hashlib.sha256(source_bytes).hexdigest(),
               'counts': {'pdf': 709, 'source': 667, 'matched': 667, 'pdfOnly': 42, 'websiteOnly': 0}, 'names': names, 'products': products, 'pdfOnly': pdf_only, 'websiteOnly': []}
    (ROOT / 'data/catalog-identities.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['Durum', 'Site ürün kimliği', 'Kaynak kod', 'NODENO kodu', 'Katalog adı', 'Katalog sayfası', 'Dizin sayfası'])
    for entry in products:
        writer.writerow(['Sitede ve katalogda', entry['id'], entry['sourceCode'], entry['code'], entry['name'], entry['cataloguePage'], entry['indexPage']])
    for entry in pdf_only:
        writer.writerow(['Siteye ekleme değerlendirmede', '', entry['code'][4:], entry['code'], entry['name'], entry['cataloguePage'], entry['indexPage']])
    report = ROOT / 'output/catalog/NODENO_Katalog_Eslestirme_Tam.csv'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(output.getvalue(), encoding='utf-8-sig', newline='')
    print(json.dumps({'mapped': len(products), 'pdfOnlyPendingReview': len(pdf_only), 'sourceUnchanged': True, 'pdfSha256': proof['outputPdf']['sha256']}))


if __name__ == '__main__':
    main()
