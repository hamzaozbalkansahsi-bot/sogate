"""Match the supplied NODENO PDF index to immutable supplier SKUs.

No network, fuzzy matching, new products or edits to the source catalogue.
"""
import csv
import hashlib
import io
import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "output/pdf/NODENO_Mobilya_Katalogu_2026_Paylasim_Son.pdf"
EXPECTED_PDF_SHA = "326f3d643638e1bbf2a69f91786f1e2f03ad559d61762a3ab4551a27bcb12238"
CODE = re.compile(r"^Ndn-(?:ZSP-)?[A-Z]{3}-\d{2,4}-[A-Z]{2}-\d$")


def main():
    current = ROOT / 'data/catalog-identities.json'
    if current.exists() and json.loads(current.read_bytes()).get('sourcePdf', {}).get('sha256') != EXPECTED_PDF_SHA:
        raise ValueError('The completed catalogue supersedes this historical import. Use import-complete-catalog.py.')
    pdf_bytes = PDF.read_bytes()
    if hashlib.sha256(pdf_bytes).hexdigest() != EXPECTED_PDF_SHA:
        raise ValueError("The supplied PDF has changed; review it before importing.")
    source_bytes = (ROOT / "data/catalog-source.json").read_bytes()
    source = json.loads(source_bytes)
    names = json.loads((ROOT / "data/catalog-name-translations.json").read_bytes())
    notes = json.loads((ROOT / "data/catalog-identity-notes.json").read_bytes())
    by_code = {p["code"]: p for p in source["products"]}
    if len(by_code) != len(source["products"]):
        raise ValueError("Duplicate source SKU")
    entries = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        if len(doc) != 86:
            raise ValueError("Unexpected PDF page count")
        for index in range(77, 85):
            lines = doc[index].get_text().splitlines()
            for n, line in enumerate(lines):
                if CODE.fullmatch(line):
                    name, page = lines[n + 1:n + 3]
                    if not page.isdigit() or not 3 <= int(page) <= 76:
                        raise ValueError("Invalid catalogue page")
                    if line not in doc[int(page) - 1].get_text():
                        raise ValueError("Index SKU missing from its product page")
                    entries.append({"code": line, "name": name, "cataloguePage": int(page), "indexPage": index + 1})
    if len(entries) != 423 or len({e["code"] for e in entries}) != 423:
        raise ValueError("PDF index lost products or contains duplicate SKUs")
    matched, pdf_only = [], []
    for entry in entries:
        original = by_code.get(entry["code"][4:])
        if original is None:
            pdf_only.append(entry)
            continue
        translated = names.get(entry["name"])
        if not translated or translated.get("tr") != entry["name"] or any(not translated.get(lang) for lang in ("en", "ru", "ar")):
            raise ValueError("Missing reviewed name translations")
        record = {"id": str(original["id"]), "sourceCode": original["code"], "sourceName": original["title"], **entry}
        if record["id"] in notes:
            note = notes[record["id"]]
            if note["sourceCode"] != original["code"]:
                raise ValueError("Technical note attached to wrong product")
            record["notes"] = note["notes"]
        matched.append(record)
    matched_ids = {e["id"] for e in matched}
    unmatched = [{"id": str(p["id"]), "code": p["code"], "name": p["title"]} for p in source["products"] if str(p["id"]) not in matched_ids]
    mapping = {"schema": 1, "sourcePdf": {"file": PDF.name, "sha256": EXPECTED_PDF_SHA, "pages": 86},
               "sourceCatalogSha256": hashlib.sha256(source_bytes).hexdigest(),
               "counts": {"pdf": len(entries), "source": len(source["products"]), "matched": len(matched), "pdfOnly": len(pdf_only), "websiteOnly": len(unmatched)},
               "names": names, "products": matched, "pdfOnly": pdf_only, "websiteOnly": unmatched}
    if mapping["counts"] != {"pdf": 423, "source": 667, "matched": 381, "pdfOnly": 42, "websiteOnly": 286}:
        raise ValueError("Catalogue coverage changed; review before importing")
    (ROOT / "data/catalog-identities.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Excel-readable UTF-8 CSV, separate from the unchanged source PDF.
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Durum", "Site ürün kimliği", "Eski kod", "Katalog kodu", "Katalog adı", "Katalog sayfası", "Dizin sayfası"])
    for item in matched:
        writer.writerow(["Eşleşti", item["id"], item["sourceCode"], item["code"], item["name"], item["cataloguePage"], item["indexPage"]])
    for item in unmatched:
        writer.writerow(["Yalnız sitede", item["id"], item["code"], "", item["name"], "", ""])
    for item in pdf_only:
        writer.writerow(["Yalnız katalogda", "", item["code"][4:], item["code"], item["name"], item["cataloguePage"], item["indexPage"]])
    report = ROOT / "output/catalog/NODENO_Katalog_Eslestirme.csv"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(output.getvalue(), encoding="utf-8-sig", newline="")
    print(json.dumps({"matched": len(matched), "websiteOnly": len(unmatched), "pdfOnly": len(pdf_only), "sourceUnchanged": True}))


if __name__ == "__main__":
    main()
