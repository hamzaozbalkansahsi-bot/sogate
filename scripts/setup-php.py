#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/setup-php.py
# Açıklama   : Yerel MySQL erişimini PHP kurulumuna ortam üzerinden taşır.
import json,os,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent.parent
env=os.environ.copy()
for line in (root/'.local/mysql/mysql.env').read_text('utf8').splitlines():
    if line.startswith('MYSQL_TEST_ADMIN_URL='):
        value=line.split('=',1)[1];env['MYSQL_TEST_ADMIN_URL']=json.loads(value) if value.startswith('"') else value
raise SystemExit(subprocess.run([str(root/'.local/php-runtime/php.exe'),str(root/'hosting/php/bin/setup-local.php')],env=env).returncode)
