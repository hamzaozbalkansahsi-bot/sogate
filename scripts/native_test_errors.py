# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_test_errors.py
# Açıklama   : Tarayıcı testlerinin hata çıktısında oturum ve kimlik başlıklarını gizler.
import re,sys

def safe_error(kind,error,trace):
 message=re.sub(r'^.*(?:cookie:|authorization:|x-csrf-token:).*$','[private request headers redacted]',str(error),flags=re.M|re.I)
 print(kind.__name__+': '+message[:2000],file=sys.stderr)
