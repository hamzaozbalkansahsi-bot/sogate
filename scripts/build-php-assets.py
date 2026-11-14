#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/build-php-assets.py
# Açıklama   : Ortak marka kaynaklarını değiştirmeden PHP yayın varlıklarını hazırlar.
from pathlib import Path
import shutil
root=Path(__file__).resolve().parent.parent
target=root/'hosting/php/public/assets'
target.mkdir(parents=True,exist_ok=True)
css=(root/'src/app/globals.css').read_text('utf8').replace('@import "tailwindcss";','')
(target/'site.css').write_text(css,encoding='utf8')
for directory,pattern in [('brand','*.svg'),('media','atelier-*.svg'),('fonts','*.woff2')]:
    (target/directory).mkdir(exist_ok=True)
    for file in (root/'public'/directory).glob(pattern):
        shutil.copy2(file,target/directory/file.name)
for file in (root/'public/fonts').glob('*OFL*'):
    shutil.copy2(file,target/'fonts'/file.name)
app_assets=root/'public/brand/app'
if app_assets.is_dir():
    (target/'brand/app').mkdir(exist_ok=True)
    for file in app_assets.iterdir():
        if file.is_file() and file.suffix in ['.svg','.png','.ico','.webp']:
            shutil.copy2(file,target/'brand/app'/file.name)
fonts=(root/'public/fonts/fonts.css').read_text('utf8').replace('/fonts/','./fonts/')
(target/'fonts.css').write_text(fonts,encoding='utf8')
print('PHP assets prepared; shared source files unchanged.')
