#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_marketplace_copy.py
# Açıklama   : Reklam cümlelerini olgulara dokunmadan ayırır ve yalnız kanıtlı kamu kayıtlarına sürümlü düzeltme uygular.
import copy
import html
import re
import unicodedata

from native_marketplace_import_guard import canonical_data, fingerprint, normalize_generic_brand, PHP_TRIM

COPY_FIELDS = ('description_tr', 'seoDescription_tr', 'seoTitle_tr')
SENTENCE_BREAK = re.compile(r'(?<=[.!?])\s+|\r\n|\r|\n')


def _fold(value):
    text = unicodedata.normalize('NFKD', html.unescape(value).casefold().replace('ı', 'i'))
    return ''.join(c for c in text if not unicodedata.combining(c))


def _advertising_sentence(sentence):
    text = _fold(sentence)
    return bool(re.search(r'\btrendyol\b', text) and re.search(
        r'\byorumlarini\s+inceleyin\b|\bsatin\s+alin\b', text))


def _sentences(text):
    start = 0
    for match in SENTENCE_BREAK.finditer(text):
        yield text[start:match.start()], text[match.start():match.end()]
        start = match.end()
    yield text[start:], ''


def has_advertising(text):
    return isinstance(text, str) and any(_advertising_sentence(sentence) for sentence, _ in _sentences(text))


def clean_text(text):
    """Remove only a whole sentence containing both the platform and a known CTA."""
    if not isinstance(text, str):
        return text, []
    kept, removed = [], []
    for sentence, separator in _sentences(text):
        if _advertising_sentence(sentence):
            removed.append(sentence)
        else:
            kept.append(sentence + separator)
    return (''.join(kept).strip(PHP_TRIM), removed) if removed else (text, [])


def clean_data(data):
    target = copy.deepcopy(data)
    changed, removed = [], {}
    for key in COPY_FIELDS:
        if key not in data:
            continue
        value, sentences = clean_text(data[key])
        if sentences:
            target[key] = value
            changed.append(key)
            removed[key] = sentences
    return target, changed, removed


def protected_data(data, fields):
    if not set(fields).issubset(COPY_FIELDS):
        raise ValueError('COPY_PROTECTED_FIELDS_INVALID')
    return {key: value for key, value in data.items() if key not in fields}


def _known(initials):
    variants = {}
    for initial in initials:
        if not isinstance(initial, dict):
            continue
        for value in [canonical_data(initial), normalize_generic_brand(canonical_data(initial))]:
            variants[fingerprint(value)] = value
    return variants


def plan_copy(record, known_initials, public_ids, context, journal):
    identity = record.get('id') if isinstance(record, dict) else None
    skip = lambda reason: {'id': identity, 'action': 'skip', 'reason': reason, 'changedFields': []}
    if identity not in public_ids:
        return skip('not_existing_public_product')
    try:
        current = canonical_data(record['data'])
        variants = _known(known_initials)
        context_sha = fingerprint(context)
    except (KeyError, ValueError, TypeError):
        return skip('invalid_record_or_baseline')
    version, published = record.get('version'), record.get('publishedVersion')
    if type(version) is not int or type(published) is not int or published < 1 or version < published or current.get('visible') is not True:
        return skip('not_published_or_invalid_version')
    current_sha = fingerprint(current)
    prior = journal.get(identity, {})
    for original_sha, original in variants.items():
        target, fields, removed = clean_data(original)
        if not fields or any(not target[field] for field in fields):
            continue
        binding = {'id': identity, 'contextSha256': context_sha, 'baselineSha256': original_sha,
            'targetSha256': fingerprint(target), 'protectedSha256': fingerprint(protected_data(original, fields)),
            'changedFields': fields}
        if (isinstance(prior, dict) and all(prior.get(key) == value for key, value in binding.items())
                and prior.get('phase') == 'saved' and type(prior.get('fromVersion')) is int
                and type(prior.get('savedVersion')) is int and prior['fromVersion'] == published
                and version == prior['savedVersion'] == prior['fromVersion'] + 1
                and current_sha == binding['targetSha256']):
            return {'action': 'resume', 'data': target, 'removedSentences': sum(map(len, removed.values())), **binding}
    if version != published:
        return skip('concurrent_or_unconfirmed_public_draft')
    target, fields, removed = clean_data(current)
    if not fields:
        cleaned_variants = {fingerprint(clean_data(value)[0]) for value in variants.values()}
        return {'id': identity, 'action': 'already_clean' if current_sha in cleaned_variants else 'no_change',
                'changedFields': [], 'reason': 'no_matching_advertising_sentence'}
    if any(not target[field] for field in fields):
        return skip('empty_cleanup_requires_editor_review')
    if current_sha not in variants:
        return skip('manual_or_unknown_whole_record')
    if fingerprint(protected_data(current, fields)) != fingerprint(protected_data(target, fields)):
        raise ValueError('COPY_PROTECTED_FIELDS_CHANGED')
    return {'id': identity, 'action': 'update', 'data': target, 'changedFields': fields,
        'contextSha256': context_sha, 'baselineSha256': current_sha, 'targetSha256': fingerprint(target),
        'protectedSha256': fingerprint(protected_data(current, fields)), 'fromVersion': version,
        'removedSentences': sum(map(len, removed.values()))}


def apply_copy(api, record, known_initials, public_ids, context, journal, checkpoint):
    """Use the existing MFA API once per mutation; saved intents permit only exact recovery."""
    plan = plan_copy(record, known_initials, public_ids, context, journal)
    identity, action = plan['id'], plan['action']
    if action not in ('update', 'resume'):
        return {key: value for key, value in plan.items() if key != 'data'}
    if action == 'update':
        journal[identity] = {key: value for key, value in plan.items()
                             if key not in ('action', 'data', 'removedSentences')}
        journal[identity]['phase'] = 'prepared'
        checkpoint()
        saved = api('products/' + identity, {'version': record['version'], 'data': plan['data']}, 'PUT')['data']
        if (saved.get('id') != identity or saved.get('version') != record['version'] + 1
                or saved.get('publishedVersion') != record['publishedVersion']
                or fingerprint(canonical_data(saved.get('data'))) != plan['targetSha256']):
            raise ValueError('COPY_PUT_RESPONSE_MISMATCH')
        journal[identity].update(phase='saved', savedVersion=saved['version'])
        checkpoint()
    intent = journal[identity]
    fresh = api('products/' + identity + '/editor')['record']
    if (fresh.get('id') != identity or fresh.get('version') != intent['savedVersion']
            or fresh.get('publishedVersion') != intent['fromVersion']
            or fingerprint(canonical_data(fresh.get('data'))) != intent['targetSha256']):
        raise ValueError('COPY_CONCURRENT_DRAFT_BEFORE_PUBLISH')
    published = api('products/' + identity + '/publish', {'version': fresh['version']})['data']
    if (published.get('id') != identity or published.get('version') != fresh['version'] + 1
            or published.get('publishedVersion') != published.get('version')
            or fingerprint(canonical_data(published.get('data'))) != intent['targetSha256']
            or fingerprint(protected_data(published['data'], intent['changedFields'])) != intent['protectedSha256']):
        raise ValueError('COPY_PUBLISH_RESPONSE_MISMATCH')
    journal[identity].update(phase='published', publishedVersion=published['version'])
    checkpoint()
    return {'id': identity, 'action': 'resumed' if action == 'resume' else 'updated',
        'changedFields': plan['changedFields'], 'removedSentences': plan['removedSentences'],
        'protectedSha256': intent['protectedSha256'], 'fromVersion': intent['fromVersion'],
        'publishedVersion': published['version']}
