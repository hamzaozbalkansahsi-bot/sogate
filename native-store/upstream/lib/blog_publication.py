"""Shared, offline production gate for compiled blog content and private illustrations."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.blog_bundle import unpack_bundle

LOCALES = ('tr', 'en', 'ru', 'ar')
BLOG_INPUTS = ('blog-bank.json', 'blog-images.json', 'blog-images.bin')


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _content(value):
    if not isinstance(value, dict):
        raise ValueError('blog_locale_body_invalid')
    if value.get('testOnly'):
        raise ValueError('blog_test_only_rejected')
    if not all(_text(value.get(key)) for key in ('title', 'description', 'intro')):
        raise ValueError('blog_locale_body_invalid')
    sections = value.get('sections')
    if not isinstance(sections, list) or len(sections) < 4:
        raise ValueError('blog_locale_body_invalid')
    for section in sections:
        if not isinstance(section, dict) or not _text(section.get('heading')):
            raise ValueError('blog_locale_body_invalid')
        paragraphs = section.get('paragraphs')
        if not isinstance(paragraphs, list) or not paragraphs or not all(map(_text, paragraphs)):
            raise ValueError('blog_locale_body_invalid')
        if 'list' in section and (not isinstance(section['list'], list) or not all(map(_text, section['list']))):
            raise ValueError('blog_locale_body_invalid')
    for key in ('keywords', 'checklist'):
        items = value.get(key)
        if not isinstance(items, list) or len(items) < 3 or not all(map(_text, items)):
            raise ValueError('blog_locale_body_invalid')


def _image(value, bundled):
    if not isinstance(value, dict):
        raise ValueError('blog_image_reference_invalid')
    if value.get('testOnly'):
        raise ValueError('blog_test_only_rejected')
    if value.get('storage') != 'private-bundle' or value.get('kind') != 'original-diagram':
        raise ValueError('blog_image_reference_invalid')
    url, digest = value.get('url'), value.get('sha256')
    if not isinstance(url, str) or url not in bundled or not isinstance(digest, str):
        raise ValueError('blog_image_reference_invalid')
    if hashlib.sha256(bundled[url]['bytes']).hexdigest() != digest:
        raise ValueError('blog_image_hash_mismatch')
    if not _text(value.get('alt')) or any(type(value.get(key)) is not int or value[key] < 1 for key in ('width', 'height')):
        raise ValueError('blog_image_reference_invalid')


def validate_blog_publication(files):
    """Validate exact package bytes, including historical images retained in the bundle.

    Older releases without a blog remain valid. Static editorial files are rejected
    even in those releases because they bypass the published-article HTTP boundary.
    """
    if any(name.lower().startswith('public/assets/blog/') for name in files):
        raise ValueError('public_editorial_image_rejected')
    if 'private/blog-bank.json' not in files:
        if any('private/' + name in files for name in BLOG_INPUTS[1:]):
            raise ValueError('blog_input_unavailable')
        return {'present': False}
    try:
        bank = json.loads(files['private/blog-bank.json'])
        index = json.loads(files['private/blog-images.json'])
        blob = files['private/blog-images.bin']
    except (KeyError, ValueError, TypeError, UnicodeError):
        raise ValueError('blog_bundle_or_bank_unavailable') from None
    if not isinstance(bank, dict) or bank.get('publicationReady') is not True:
        raise ValueError('blog_publication_not_ready')
    if bank.get('testOnly') or (isinstance(index, dict) and (index.get('testOnly') or
            isinstance(index.get('files'), dict) and any(isinstance(row, dict) and row.get('testOnly') for row in index['files'].values()))):
        raise ValueError('blog_test_only_rejected')
    if type(bank.get('schemaVersion')) is not int or bank['schemaVersion'] != 1 or bank.get('timezone') != 'Europe/Istanbul' or bank.get('dailySlots') != ['09:30', '18:30']:
        raise ValueError('blog_bank_contract_invalid')
    articles = bank.get('articles')
    if not isinstance(articles, list) or len(articles) < 250:
        raise ValueError('blog_bank_incomplete')
    bundled = unpack_bundle(index, blob)
    identities, slugs = set(), set()
    for article in articles:
        _content(article)
        identity, slug = article.get('id'), article.get('slug')
        if not isinstance(identity, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,99}', identity) or identity in identities:
            raise ValueError('blog_article_identity_invalid')
        if not isinstance(slug, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,150}', slug) or slug in slugs:
            raise ValueError('blog_article_identity_invalid')
        identities.add(identity)
        slugs.add(slug)
        _image(article.get('image'), bundled)
        locales = article.get('locales')
        if not isinstance(locales, dict) or not set(LOCALES[1:]).issubset(locales):
            raise ValueError('blog_translations_incomplete')
        for translation in locales.values():
            _content(translation)
            _image(translation.get('image'), bundled)
    return {'present': True, 'articles': len(articles), 'locales': list(LOCALES), 'bundledImages': len(bundled)}


def read_blog_files(directory, source=False):
    directory = Path(directory)
    base = directory / ('data' if source else 'private')
    files = {}
    for name in BLOG_INPUTS:
        path = base / name
        if not path.exists():
            if source or (name == 'blog-bank.json' and any((base / item).exists() for item in BLOG_INPUTS[1:])):
                raise ValueError('blog_input_unavailable')
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError('blog_input_not_regular')
        files['private/' + name] = path.read_bytes()
    if not source:
        public = directory / 'public'
        for item in public.rglob('*'):
            relative = item.relative_to(public).as_posix()
            if (relative.lower().startswith('assets/blog/') or relative.lower() == 'assets/blog') and (item.is_file() or item.is_symlink()):
                # File names suffice; forbidden public contents are never read.
                files['public/assets/blog/forbidden'] = b''
                break
    return files


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--source-root', type=Path)
    group.add_argument('--release', type=Path)
    args = parser.parse_args()
    try:
        result = validate_blog_publication(read_blog_files(args.source_root or args.release, source=args.source_root is not None))
    except (ValueError, TypeError, OSError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r'[a-z_]+', str(error)) else 'blog_publication_input_invalid'
        print(code, file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
