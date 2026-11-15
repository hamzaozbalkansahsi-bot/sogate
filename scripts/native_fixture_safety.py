#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_fixture_safety.py
# Açıklama   : Üç kaynak testindeki açık sahte Stripe sabitini üretilen test verisine dönüştürür.
import re

FILES = {
    'tests/payment-activation.test.mjs',
    'tests/payment-documents-maintenance.test.mjs',
    'tests/private-maintenance.test.mjs',
}

def safe_fixture(name, raw):
    if name not in FILES:
        return raw
    def replace(match):
        if not re.search(rb'fixture|isolated|dummy|example|notreal|testonly', match[1], re.I):
            raise RuntimeError('UNRECOGNISED_STRIPE_LITERAL_IN_SOURCE_TEST: ' + name)
        return b"('rk_live_'.str_repeat('F',32))"
    return re.sub(rb"'(rk_live_[A-Za-z0-9_]{16,})'", replace, raw)
