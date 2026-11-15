"""Read-only live acceptance; never starts Checkout, sends webhooks or writes orders."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse, hashlib, json, secrets, urllib.parse, urllib.request

R = Path(__file__).resolve().parents[1]
E = R / 'artifacts/stripe-sandbox-20261110'
HOSTS = ['nodenohome.com', 'www.nodenohome.com', 'nodenohome.com.tr', 'www.nodenohome.com.tr']
FILES = ['payments.js', 'admin-payments.js', 'app.js', 'admin.js', 'admin.html']


def inspect(host, release=None):
    def get(path):
        url = 'https://' + host + path
        url += ('&' if '?' in path else '?') + 'payment_acceptance=' + secrets.token_hex(6)
        request = urllib.request.Request(url, headers={'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(request, timeout=40) as response:
            assert urllib.parse.urlparse(response.url).hostname == host
            return response.read()
    health = json.loads(get('/api/health'))
    status = json.loads(get('/api/payments/status'))
    config = json.loads(get('/api/config'))
    assert health['mediaReady'] is True and health['checkoutEnabled'] is True
    assert status['enabled'] is True and status['test'] is False and status['currency'] == 'TRY'
    assert config['checkoutEnabled'] is True
    assert status['seller']['termsVersion'] == '2026-11-10.2'
    assert status['freight'] == {'kind': 'recipient_pays', 'includedInCharge': False, 'feeMinor': None}
    record = {'host': host, 'hostPreserved': True, 'releaseHash': health['releaseHash'],
              'mediaReady': True, 'mediaApproved': health['mediaApproved'],
              'paymentEnabled': True, 'testMode': False, 'checkoutEnabled': True,
              'termsRevision': status['termsRevision'], 'termsVersion': status['seller']['termsVersion'],
              'seller': status['seller']['name'], 'currency': 'TRY', 'freightPreserved': True}
    if release is not None:
        manifest = json.loads((release / 'private/release.json').read_bytes())
        assert health['releaseHash'] == manifest['releaseHash']
        hashes = {}
        for name in FILES:
            actual = get('/' + name)
            assert actual == (release / 'public' / name).read_bytes(), host + '/' + name
            hashes[name] = hashlib.sha256(actual).hexdigest()
        record['publicModuleHashes'] = hashes
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture-baseline', action='store_true')
    args = parser.parse_args()
    proof = json.loads((E / 'release-preparation.json').read_bytes())
    release = None if args.capture_baseline else R / proof['release']
    with ThreadPoolExecutor(max_workers=4) as pool:
        checks = list(pool.map(lambda host: inspect(host, release), HOSTS))
    if not args.capture_baseline:
        before = json.loads((E / 'live-baseline.json').read_bytes())
        previous = {row['host']: row for row in before['domains']}
        for row in checks:
            assert all(row[key] == previous[row['host']][key] for key in
                       ['termsRevision', 'termsVersion', 'seller', 'currency', 'mediaApproved'])
            assert row['termsRevision'] == before['prePublicationTermsRevision']
        hook = json.loads((E / 'webhook-live.json').read_bytes())
        assert hook['livemode'] is True and hook['status'] == 'enabled'
        assert set(['checkout.session.completed', 'checkout.session.expired',
                    'checkout.session.async_payment_succeeded', 'checkout.session.async_payment_failed',
                    'refund.created', 'refund.updated', 'refund.failed']) <= set(hook['enabled_events'])
    record = {'passed': True, 'checkedAt': datetime.now(timezone.utc).isoformat(),
              'domains': checks, 'ordersCreated': 0, 'realCharges': 0,
              'sandboxOrdersSentToProduction': 0}
    if args.capture_baseline:
        # Observed read-only immediately before the pointer changed; no seller details are stored here.
        record['prePublicationTermsRevision'] = 'a68235627fa1620b7d75cbf3619d25a0f0ea6313e6f8b8a25eb074c827ddebf0'
        record['capturedAfterPublication'] = True
    target = E / ('live-baseline.json' if args.capture_baseline else 'live-acceptance.json')
    target.write_text(json.dumps(record, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'passed': True, 'domains': len(checks), 'phase': 'baseline' if args.capture_baseline else 'after',
                      'releaseHashes': sorted(set(row['releaseHash'] for row in checks)), 'realCharges': 0}))


if __name__ == '__main__':
    main()
