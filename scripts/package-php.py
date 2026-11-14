#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/package-php.py
# Açıklama   : Sırsız, kilitli üretim bağımlılıklarıyla PHP test yayın arşivini hazırlar.
import argparse,hashlib,json,secrets,shutil,subprocess,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description='Sırsız PHP yayın paketi oluşturur.')
parser.add_argument('--output-root',type=Path,default=root/'.local/php-packages')
args=parser.parse_args()
identifier=secrets.token_hex(12);folder=args.output_root.resolve()/identifier;folder.mkdir(parents=True)
source=root/'hosting/php'
for name in ['src','templates','public','bin']:
    shutil.copytree(source/name,folder/name)
shutil.copytree(root/'migrations/mysql',folder/'migrations')
for name in ['composer.json','composer.lock']:
    shutil.copy2(source/name,folder/name)
result=subprocess.run([str(root/'.local/php-runtime/php.exe'),str(root/'.local/php-runtime/composer.phar'),'install','--no-dev','--no-interaction','--prefer-dist','--classmap-authoritative','--no-scripts'],cwd=folder)
if result.returncode:raise SystemExit(result.returncode)
manifest={p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
(folder/'manifest.json').write_text(json.dumps(manifest,sort_keys=True),encoding='utf8')
archive=folder.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in folder.rglob('*'):
        if p.is_symlink():raise ValueError('SYMLINK_NOT_ALLOWED')
        if p.is_file():z.write(p,p.relative_to(folder).as_posix())
report={'release':identifier,'archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':len(manifest),'bytes':archive.stat().st_size}
(root/'.local/php-package.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='archive'}))
