"""Offline production blog gates; no catalogue audit or hosting access is needed."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest

from lib.blog_bundle import pack_bundle

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DEPLOY = load('blog_gate_deployment', 'scripts/deploy-cpanel.py')


def production_files():
    images = {
        '/assets/blog/' + code + '.svg': {
            'bytes': ('<svg xmlns="http://www.w3.org/2000/svg"><title>' + code + '</title></svg>').encode(),
            'mime': 'image/svg+xml',
        }
        for code in ['tr', 'en', 'ru', 'ar', 'historic']
    }
    index, blob = pack_bundle(images)

    def content(locale):
        url = '/assets/blog/' + locale + '.svg'
        return {
            'title': 'Reviewed guide ' + locale,
            'description': 'A complete editorial description.',
            'intro': 'A practical original introduction.',
            'keywords': ['measurement', 'planning', 'surface'],
            'sections': [{'heading': 'Step ' + str(i), 'paragraphs': ['A practical action.']} for i in range(4)],
            'checklist': ['Measure.', 'Check.', 'Record.'],
            'image': {'url': url, 'storage': 'private-bundle', 'kind': 'original-diagram',
                      'sha256': index['files'][url]['sha256'], 'alt': 'Original guide diagram', 'width': 1200, 'height': 800},
        }

    articles = []
    for i in range(250):
        article = content('tr')
        article.update(id='guide-' + str(i), slug='guide-' + str(i), locales={code: content(code) for code in ['en', 'ru', 'ar']})
        articles.append(article)
    bank = {'schemaVersion': 1, 'publicationReady': True, 'timezone': 'Europe/Istanbul',
            'dailySlots': ['09:30', '18:30'], 'articles': articles}
    return {'private/blog-bank.json': json.dumps(bank).encode(),
            'private/blog-images.json': json.dumps(index).encode(), 'private/blog-images.bin': blob}


def change_bank(files, mutation):
    bank = json.loads(files['private/blog-bank.json'])
    mutation(bank)
    files['private/blog-bank.json'] = json.dumps(bank).encode()


class BlogPublicationGateTests(unittest.TestCase):
    def validate(self, files):
        return load('blog_gate_validator', 'lib/blog_publication.py').validate_blog_publication(files)

    def test_ready_four_language_bank_accepts_valid_historic_private_media(self):
        result = self.validate(production_files())
        self.assertEqual(result['articles'], 250)
        self.assertEqual(result['locales'], ['tr', 'en', 'ru', 'ar'])
        self.assertEqual(result['bundledImages'], 5)

    def test_unready_short_and_duplicate_banks_fail_closed(self):
        mutations = [lambda b: b.update(publicationReady=False),
                     lambda b: b.update(schemaVersion=True),
                     lambda b: b['articles'].pop(),
                     lambda b: b['articles'][1].update(id=b['articles'][0]['id']),
                     lambda b: b['articles'][1].update(slug=b['articles'][0]['slug'])]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                files = production_files()
                change_bank(files, mutation)
                with self.assertRaises(ValueError):
                    self.validate(files)

    def test_locale_keys_without_actual_article_bodies_are_not_approved(self):
        mutations = [lambda b: b['articles'][0]['locales'].pop('ru'),
                     lambda b: b['articles'][0]['locales'].update(en={}),
                     lambda b: b['articles'][0]['locales']['ar'].update(sections=[]),
                     lambda b: b['articles'][0]['locales']['ru']['sections'][0].update(paragraphs=[' ']),
                     lambda b: b['articles'][0].update(intro='')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                files = production_files()
                change_bank(files, mutation)
                with self.assertRaisesRegex(ValueError, 'blog_'):
                    self.validate(files)

    def test_every_current_reference_must_match_the_private_bundle(self):
        mutations = [lambda b: b['articles'][0]['image'].update(storage='public'),
                     lambda b: b['articles'][0]['locales']['ru']['image'].update(sha256='0' * 64),
                     lambda b: b['articles'][0]['locales']['en']['image'].update(url='/assets/blog/missing.svg')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                files = production_files()
                change_bank(files, mutation)
                with self.assertRaisesRegex(ValueError, 'blog_'):
                    self.validate(files)

    def test_test_only_bank_article_translation_image_and_bundle_are_rejected(self):
        mutations = [lambda b: b.update(testOnly=True),
                     lambda b: b['articles'][0].update(testOnly=True),
                     lambda b: b['articles'][0]['locales']['ru'].update(testOnly=True),
                     lambda b: b['articles'][0]['image'].update(testOnly=True)]
        for mutation in mutations:
            files = production_files()
            change_bank(files, mutation)
            with self.assertRaisesRegex(ValueError, 'test_only'):
                self.validate(files)
        files = production_files()
        index = json.loads(files['private/blog-images.json'])
        index['testOnly'] = True
        files['private/blog-images.json'] = json.dumps(index).encode()
        with self.assertRaisesRegex(ValueError, 'test_only'):
            self.validate(files)

        files = production_files()
        index = json.loads(files['private/blog-images.json'])
        index['files']['/assets/blog/tr.svg']['testOnly'] = True
        files['private/blog-images.json'] = json.dumps(index).encode()
        with self.assertRaisesRegex(ValueError, 'test_only'):
            self.validate(files)

    def test_corruption_hidden_bytes_and_static_editorial_files_are_rejected(self):
        for mutation in [lambda f: f.update({'private/blog-images.bin': b'X' + f['private/blog-images.bin'][1:]}),
                         lambda f: f.update({'private/blog-images.bin': f['private/blog-images.bin'] + b'hidden'}),
                         lambda f: f.update({'public/assets/blog/draft.svg': b'<svg/>'})]:
            files = production_files()
            mutation(files)
            with self.assertRaises(ValueError):
                self.validate(files)
        with self.assertRaisesRegex(ValueError, 'public_editorial_image'):
            self.validate({'public/assets/blog/draft.svg': b'<svg/>'})

    def test_new_package_requires_mime_even_when_legacy_migration_is_supported(self):
        files = production_files()
        index = json.loads(files['private/blog-images.json'])
        index['files']['/assets/blog/historic.svg'].pop('mime')
        files['private/blog-images.json'] = json.dumps(index).encode()
        with self.assertRaisesRegex(ValueError, 'mime'):
            self.validate(files)

    def test_package_reader_rejects_static_namespace_regardless_of_case(self):
        gate = load('blog_gate_reader', 'lib/blog_publication.py')
        with tempfile.TemporaryDirectory(prefix='nodeno-blog-reader-gate-') as directory:
            for name, body in production_files().items():
                path = Path(directory) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
            leaked = Path(directory) / 'public/ASSETS/BLOG/draft.svg'
            leaked.parent.mkdir(parents=True)
            leaked.write_bytes(b'<svg/>')
            with self.assertRaisesRegex(ValueError, 'public_editorial_image'):
                gate.validate_blog_publication(gate.read_blog_files(directory))

    def test_generic_deployment_rejects_bad_blog_before_other_audits(self):
        files = production_files()
        change_bank(files, lambda b: b.update(publicationReady=False))
        with self.assertRaisesRegex(DEPLOY.DeployError, 'blog_publication_not_ready'):
            DEPLOY.validate_media_publication(ROOT, {'manifest': {}, 'all_bytes': files})

        with self.assertRaisesRegex(DEPLOY.DeployError, 'test_only'):
            DEPLOY.validate_media_publication(ROOT, {'manifest': {'testOnly': True}, 'all_bytes': production_files()})

    def test_surface_private_module_is_allowed_but_static_blog_media_is_not(self):
        self.assertIn('blog-surface.php', DEPLOY.PAYMENT_PRIVATE_FILES)
        files = {'private/' + name: b'{}' for name in DEPLOY.PRIVATE_FILES if name != 'release.json'}
        files.update({'public/index.php': b'<?php', 'public/.htaccess': b'DirectoryIndex index.php',
                      'private/catalog.json': b'{"products":[{"id":"fixture"}]}',
                      'private/config.json': b'{"checkoutEnabled":false,"mode":"catalogue"}',
                      'private/blog-surface.php': b'<?php // isolated surface module'})
        hashes = {name: hashlib.sha256(body).hexdigest() for name, body in sorted(files.items())}
        fingerprint = hashlib.sha256()
        for name, digest in hashes.items():
            fingerprint.update((name + '\0' + digest + '\0').encode())
        manifest = {'runtime': 'php', 'checkoutEnabled': False, 'products': 1,
                    'releaseHash': fingerprint.hexdigest(), 'files': hashes}
        with tempfile.TemporaryDirectory(prefix='nodeno-blog-allowlist-') as directory:
            for name, body in files.items():
                target = Path(directory) / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
            (Path(directory) / 'private/release.json').write_text(json.dumps(manifest))
            self.assertIn('private/blog-surface.php', DEPLOY.load_release(directory)['all_bytes'])


class BlogBuildGateTests(unittest.TestCase):
    def fixture(self, directory):
        root = Path(directory)

        def write(name, body):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body.encode() if isinstance(body, str) else body)

        for name in ['scripts/build-cpanel.mjs', 'lib/blog_publication.py', 'lib/blog_bundle.py']:
            write(name, (ROOT / name).read_bytes())
        write('package.json', '{"type":"module"}')
        write('scripts/build-date-time-regions.mjs', '// Country generation is outside this isolated gate test.\n')
        write('lib/native-locales.mjs', 'export async function loadNativeDictionaries(){return {dictionaries:{}};}')
        write('lib/supplier-catalog.mjs', 'export async function loadSupplierCatalog(){throw Error("Unexpected supplier load");}')
        write('lib/seo.mjs', 'export function seoPage(){return {};}export function seoDocument(html){return html;}')
        write('lib/server.mjs', 'export function safeMediaUrl(){return false;}')
        write('lib/media-approvals.mjs', 'export async function loadMediaApprovals(){return {testOnly:true,mediaVersion:"fixture",manifest:{referenceCount:0,counts:{}}};}')
        write('dist/server/index.js', '''
import {readFileSync,writeFileSync} from 'node:fs';
writeFileSync(new URL('../../worker-imported',import.meta.url),'imported');
export default {async fetch(request){
 const pathname=new URL(request.url).pathname;
 if(pathname==='/api/catalog'){
  if(process.env.NODENO_GATE_MUTATE_SOURCE){const file=new URL('../../data/blog-bank.json',import.meta.url);const bank=JSON.parse(readFileSync(file,'utf8'));bank.publicationReady=false;writeFileSync(file,JSON.stringify(bank));}
  return new Response(JSON.stringify({products:[{id:'1',images:[]}],categories:[],meta:{releaseHash:'a'.repeat(64)}}));
 }
 if(pathname==='/api/config')return new Response(JSON.stringify({checkoutEnabled:false,mode:'catalogue'}));
 if(pathname==='/')return new Response(readFileSync(new URL('../../web/index.html',import.meta.url)));
 throw Error('Unexpected Worker asset: '+pathname);
}};
''')
        write('data/catalog-source.json', '{"products":[{"id":"1","images":[]}]}')
        write('data/supplier-catalog.json', '{}')
        write('data/date-time-regions.json', '{}')
        for locale in ['tr', 'en', 'ru', 'ar']:
            write('data/legal/site-documents.' + locale + '.json', '{}')
        geo = {'files': {}}
        for name in ['geo-v4.bin', 'geo-v6.bin']:
            write('data/geo/' + name, b'')
            geo['files'][name] = {'sha256': hashlib.sha256(b'').hexdigest(), 'bytes': 0, 'records': 0}
        write('data/geo/geo-license.json', json.dumps(geo))
        for entry in (ROOT / 'hosting').iterdir():
            if entry.is_file():
                write('hosting/' + entry.name, 'Isolated gate fixture: ' + entry.name)
        write('web/index.html', '<html><head></head><body>Isolated gate fixture</body></html>')
        write('web/assets/blog/future-draft.svg', '<svg xmlns="http://www.w3.org/2000/svg"/>')
        for name, body in production_files().items():
            write('data/' + Path(name).name, body)
        (root / 'artifacts').mkdir()
        return root

    def build(self, root, **env):
        return subprocess.run(['node', 'scripts/build-cpanel.mjs'], cwd=root,
                              env={**os.environ, 'NODENO_CPANEL_OUTPUT': str(root / 'artifacts/cpanel-release-gate-test'), **env},
                              capture_output=True, text=True)

    def test_real_builder_copies_surface_and_private_bundle_without_static_drafts(self):
        with tempfile.TemporaryDirectory(prefix='nodeno-blog-build-gate-') as directory:
            root = self.fixture(directory)
            result = self.build(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = root / 'artifacts/cpanel-release-gate-test'
            manifest = json.loads((output / 'private/release.json').read_bytes())
            self.assertTrue(manifest['testOnly'])
            self.assertIn('private/blog-surface.php', manifest['files'])
            self.assertEqual((output / 'private/blog-images.bin').read_bytes(), (root / 'data/blog-images.bin').read_bytes())
            self.assertFalse((output / 'public/assets/blog').exists())
            self.assertTrue((root / 'web/assets/blog/future-draft.svg').exists())

    def test_unready_source_stops_before_worker_import_and_package_output(self):
        with tempfile.TemporaryDirectory(prefix='nodeno-blog-build-gate-') as directory:
            root = self.fixture(directory)
            path = root / 'data/blog-bank.json'
            bank = json.loads(path.read_bytes())
            bank['publicationReady'] = False
            path.write_text(json.dumps(bank))
            result = self.build(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('blog_publication_not_ready', result.stderr)
            self.assertFalse((root / 'worker-imported').exists())
            self.assertFalse((root / 'artifacts/cpanel-release-gate-test').exists())

    def test_actual_staged_bytes_are_rechecked_before_replacing_a_previous_package(self):
        with tempfile.TemporaryDirectory(prefix='nodeno-blog-build-gate-') as directory:
            root = self.fixture(directory)
            previous = root / 'artifacts/cpanel-release-gate-test'
            previous.mkdir()
            (previous / 'previous-package').write_text('keep the previous package')
            result = self.build(root, NODENO_GATE_MUTATE_SOURCE='1')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('blog_publication_not_ready', result.stderr)
            self.assertTrue((root / 'worker-imported').exists())
            self.assertEqual((previous / 'previous-package').read_text(), 'keep the previous package')


if __name__ == '__main__':
    unittest.main()
