#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-test-errors.py
# Açıklama   : Gerçek test hata biçiminde gizli başlıkların yazılmadığını doğrular.
import contextlib,io,json
from native_test_errors import safe_error

sample='APIRequestContext.get: read ECONNRESET\nGET /test/?lang=ru\nCookie: session=private-cookie\nAuthorization: Bearer private-auth\nX-CSRF-Token: private-csrf\nSet-Cookie: response=private-response'
out=io.StringIO()
with contextlib.redirect_stderr(out):safe_error(RuntimeError,RuntimeError(sample),None)
text=out.getvalue()
for value in ['private-cookie','private-auth','private-csrf','private-response']:assert value not in text
assert 'ECONNRESET'in text and 'GET /test/?lang=ru'in text
assert text.count('[private request headers redacted]')==4
print(json.dumps({'checks':6,'secretsRedacted':True,'usefulNetworkErrorRetained':True}))
