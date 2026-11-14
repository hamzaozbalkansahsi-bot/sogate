#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-php.py
# Açıklama   : PHP testlerine yalnız yerel MySQL test erişimini ortamdan sağlar; sırları yazdırmaz.
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
environment = os.environ.copy()
for line in (root / ".local/mysql/mysql.env").read_text("utf8").splitlines():
    if line.startswith("MYSQL_TEST_ADMIN_URL="):
        value = line.split("=", 1)[1]
        environment["MYSQL_TEST_ADMIN_URL"] = json.loads(value) if value.startswith('"') else value
php = root / ".local/php-runtime/php.exe"
result = subprocess.run([str(php), "vendor/bin/phpunit", *sys.argv[1:]], cwd=root / "hosting/php", env=environment)
raise SystemExit(result.returncode)
