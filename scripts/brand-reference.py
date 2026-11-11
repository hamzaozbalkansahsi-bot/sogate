# Proje      : SEXSOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/brand-reference.py
# Açıklama   : Ekteki marka görselini incelemek için yerel referans çıktısı hazırlar.
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
ATTACH = Path.home() / '.codex/codex-remote-attachments/01a1c70a-fd9a-7171-9f28-9037c2c3d5d3/1D569AB2-3EC1-4372-A025-0AF65AE718F4'
reader = PdfReader(ATTACH / '2-Rapor_202845.pdf')
text = '\n\n'.join(f'=== PAGE {i+1} ===\n' + page.extract_text(extraction_mode='layout') for i, page in enumerate(reader.pages))
(ROOT / 'tmp/pdfs').mkdir(parents=True, exist_ok=True)
(ROOT / 'tmp/pdfs/reference.txt').write_text(text, encoding='utf-8')
print(text)
