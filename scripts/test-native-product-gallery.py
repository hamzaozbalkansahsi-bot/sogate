#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-product-gallery.py
# Açıklama   : Galeri indiriminde erişim engeli, gerçek dosya imzası ve inceleme ayrımını sınar.
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

spec = importlib.util.spec_from_file_location('gallery', Path(__file__).with_name('collect-native-product-gallery.py'))
gallery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gallery)


class Response:
    def __init__(self, status=200, content=b'', mime='image/jpeg', redirected=False):
        self.status_code = status
        self.content = content
        self.is_redirect = redirected
        self.headers = {'Content-Type': mime, 'Content-Length': str(len(content))}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_content(self, chunk_size):
        yield self.content


class Session:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url, **kwargs):
        self.calls += 1
        if kwargs.get('allow_redirects') is not False:
            raise AssertionError('redirects enabled')
        return self.response


class GalleryTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('D:/CodexScratch/gallery-tests')
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.target = Path(self.temp.name).resolve()
        self.assertTrue(self.target.is_relative_to(scratch.resolve()))
        (self.target / 'media').mkdir()
        (self.target / 'review-sheets').mkdir()
        self.target_patch = patch.object(gallery, 'TARGET', self.target)
        self.target_patch.start()

    def tearDown(self):
        self.target_patch.stop()
        self.temp.cleanup()

    def image(self):
        path = self.target / 'original.jpg'
        Image.new('RGB', (80, 90), '#5a0a20').save(path, format='JPEG')
        return path

    def download(self, response):
        collector = gallery.Collector()
        session = Session(response)
        with patch.object(gallery, 'safe_url', lambda url: url), patch.object(gallery.requests, 'Session', lambda: session):
            result = collector.download('https://cdn.dsmcdn.com/source.jpg')[1]
        return result, collector, session

    def test_access_block_stops_all_future_requests(self):
        for status in (401, 403, 429):
            with self.subTest(status=status):
                result, collector, session = self.download(Response(status=status))
                self.assertEqual(result, {'state': 'access_blocked', 'httpStatus': status})
                self.assertTrue(collector.stop.is_set())
                self.assertEqual(collector.access_block, status)
                collector.download('https://cdn.dsmcdn.com/next.jpg')
                self.assertEqual(session.calls, 1)

    def test_bytes_are_preserved_and_probe_is_real(self):
        path = self.image()
        expected = path.read_bytes()
        result, _, _ = self.download(Response(content=expected))
        self.assertEqual(result['state'], 'ready')
        self.assertEqual((self.target / 'media' / result['file']).read_bytes(), expected)
        self.assertEqual((result['width'], result['height']), (80, 90))
        self.assertFalse(result['originalBytesChanged'])

    def test_wrong_image_signature_is_rejected(self):
        result, _, _ = self.download(Response(content=b'<html>login</html>'))
        self.assertEqual(result['state'], 'failed')
        self.assertFalse(list((self.target / 'media').glob('*.part')))

    def test_mime_mismatch_is_rejected(self):
        result, _, _ = self.download(Response(content=self.image().read_bytes(), mime='image/png'))
        self.assertEqual(result['reason'], 'GALLERY_IMAGE_MIME_MISMATCH')

    def test_redirect_is_not_followed(self):
        result, _, session = self.download(Response(status=302, redirected=True))
        self.assertEqual(result['reason'], 'GALLERY_REDIRECT_REJECTED')
        self.assertEqual(session.calls, 1)

    def test_size_limit_prevents_read(self):
        response = Response(content=b'')
        response.headers['Content-Length'] = str(gallery.MAX_BYTES + 1)
        result, _, _ = self.download(response)
        self.assertEqual(result['reason'], 'GALLERY_IMAGE_SIZE_REJECTED')

    def test_pixel_limit_is_enforced(self):
        path = self.image()
        with patch.object(gallery, 'MAX_PIXELS', 500):
            with self.assertRaisesRegex(ValueError, 'GALLERY_IMAGE_SIGNATURE_REJECTED'):
                gallery.probe(path)

    def test_private_dns_is_rejected(self):
        with patch.object(gallery.socket, 'getaddrinfo', return_value=[(2, 1, 6, '', ('127.0.0.1', 443))]):
            with self.assertRaisesRegex(ValueError, 'GALLERY_PRIVATE_ADDRESS_REJECTED'):
                gallery.safe_url('https://cdn.dsmcdn.com/source.jpg')

    def test_pending_dedup_keeps_late_source_associations(self):
        original = self.image()
        asset = gallery.probe(original)
        asset.update(file=asset['sha256'] + '.jpg', state='ready')
        (self.target / 'media' / asset['file']).write_bytes(original.read_bytes())
        manifest = {
            'products': {'one': {'baseHashes': {}}, 'two': {'baseHashes': {}}},
            'assets': {'a': asset, 'b': {'state': 'pending'}}, 'sheets': [],
            'slots': [{'productId': pid, 'code': 'seo-' + pid, 'sourceIndex': 1,
                       'sourceSha256': 'a' * 64, 'sourceUrl': url, 'review': 'pending_human_review'}
                      for pid, url in [('one', 'a'), ('two', 'b')]],
        }
        gallery.make_sheets(manifest, final=True)
        self.assertEqual(len(manifest['sheets']), 1)
        first_sha = gallery.digest(self.target / 'review-sheets/gallery-review-0001.jpg')
        manifest['assets']['b'] = dict(asset)
        gallery.make_sheets(manifest, final=True)
        self.assertEqual(len(manifest['sheets']), 1)
        self.assertEqual(len(manifest['reviewAssociations'][asset['sha256']]), 2)
        self.assertEqual(gallery.digest(self.target / 'review-sheets/gallery-review-0001.jpg'), first_sha)

    def test_existing_rejected_hash_is_never_reviewed_as_new(self):
        original = self.image()
        asset = gallery.probe(original)
        asset.update(file=asset['sha256'] + '.jpg', state='ready')
        manifest = {
            'products': {'one': {'baseHashes': {'0': asset['sha256']}}},
            'assets': {'a': asset}, 'sheets': [],
            'slots': [{'productId': 'one', 'code': 'seo-one', 'sourceIndex': 2,
                       'sourceSha256': 'a' * 64, 'sourceUrl': 'a', 'review': 'pending_human_review'}],
        }
        gallery.make_sheets(manifest, final=True)
        self.assertEqual(manifest['sheets'], [])
        self.assertEqual(manifest['reviewAssociations'], {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
