#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_marketplace_paths.py
# Açıklama   : Pazaryeri seçim kaydını ve izinli özel katalog yollarını birlikte doğrular.
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

BASE = Path('D:/sexogate-local-artifacts-20261114/private-installs')
SOURCE_NAMES = ('marketplace-catalog-20261116', 'marketplace-catalog-20261117')
LEGACY_PRODUCTS = 2194


@dataclass(frozen=True)
class MarketplacePaths:
    source: Path
    prepared: Path
    media: Path
    legacyMedia: Path
    legacyPrepared: Path


def _path(value, error):
    if not isinstance(value, (str, Path)) or not str(value) or '\x00' in str(value):
        raise ValueError(error)
    path = Path(value)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError(error)
    return path


def _location(path, base, *, directory=True):
    try:
        if path.resolve() != path or not path.is_relative_to(base):
            raise ValueError('MARKETPLACE_PATH_ESCAPE')
        if path.exists() and (not path.is_dir() if directory else not path.is_file()):
            raise ValueError('MARKETPLACE_PATH_TYPE_INVALID')
    except (OSError, RuntimeError):
        raise ValueError('MARKETPLACE_PATH_UNREADABLE') from None


def _integer(selection, key):
    value = selection.get(key)
    if type(value) is not int or value < 0:
        raise ValueError('MARKETPLACE_COUNT_INVALID')
    return value


def marketplace_paths(selection: Mapping, *, _test_base: Path | None = None) -> MarketplacePaths:
    """Seçim yollarını okur; geçici test tabanı yalnız açık test parametresiyle değişir."""
    if not isinstance(selection, Mapping):
        raise ValueError('MARKETPLACE_SELECTION_INVALID')
    for key, length in [('dataset', 32), ('sha256', 64)]:
        value = selection.get(key)
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{' + str(length) + '}', value, re.I):
            raise ValueError('MARKETPLACE_' + key.upper() + '_INVALID')
    new_count = _integer(selection, 'newProducts')
    if _integer(selection, 'products') != LEGACY_PRODUCTS + new_count:
        raise ValueError('MARKETPLACE_PRODUCT_COUNT_MISMATCH')
    if _integer(selection, 'sourceProducts') < new_count:
        raise ValueError('MARKETPLACE_SOURCE_COUNT_MISMATCH')

    # Üretim tabanı seçim veya ortam değişkenlerinden alınmaz.
    base = _path(BASE if _test_base is None else _test_base, 'MARKETPLACE_BASE_INVALID')
    _location(base, base)
    prepared = _path(selection.get('path'), 'MARKETPLACE_PREPARED_PATH_INVALID')
    allowed = tuple(base / name for name in SOURCE_NAMES)
    if prepared.name != 'prepared' or prepared.parent not in allowed:
        raise ValueError('MARKETPLACE_SOURCE_ROOT_NOT_ALLOWED')
    source = prepared.parent
    media = _path(selection.get('mediaRoot'), 'MARKETPLACE_MEDIA_PATH_INVALID')
    legacy_media = _path(selection.get('legacyMediaRoot'), 'MARKETPLACE_LEGACY_MEDIA_PATH_INVALID')
    if media != source / 'media':
        raise ValueError('MARKETPLACE_MEDIA_ROOT_MISMATCH')
    if legacy_media != base / 'native-catalog-20261115' / 'media':
        raise ValueError('MARKETPLACE_LEGACY_MEDIA_ROOT_MISMATCH')
    legacy_prepared = base / 'native-catalog-20261115' / 'prepared'
    for path in [source, prepared, media, legacy_media.parent, legacy_media, legacy_prepared]:
        _location(path, base)

    catalog = prepared / 'catalog-data.json'
    _location(catalog, base, directory=False)
    if catalog.exists():
        try:
            with catalog.open('rb') as handle:
                digest = hashlib.file_digest(handle, 'sha256').hexdigest()
        except OSError:
            raise ValueError('MARKETPLACE_CATALOG_UNREADABLE') from None
        if digest != selection['sha256'].lower():
            raise ValueError('MARKETPLACE_CATALOG_HASH_MISMATCH')
    return MarketplacePaths(source, prepared, media, legacy_media, legacy_prepared)
