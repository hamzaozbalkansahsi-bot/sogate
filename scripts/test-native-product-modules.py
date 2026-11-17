#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-product-modules.py
# Açıklama   : Gerçek kaynak ve arşiv eşitliğini bağlayarak izole ürün modülü testlerinin sürüme bağlı kanıtını üretir.
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / '.local/native-product-module-results.json'
METADATA = ROOT / '.local/native-stage-package.json'
SELECTION = ROOT / '.local/native-marketplace-selection.json'
SOURCE = ROOT / 'native-store/storefront'
COPIES = {
    'content.php': 'private/sexogate-storefront-content.php',
    'copy.json': 'private/sexogate-storefront-copy.json',
    'editorial.php': 'private/sexogate-product-editorial.php',
    'product-editorial-data.json': 'private/sexogate-product-editorial-data.json',
    'product-experience.php': 'private/sexogate-product-experience.php',
    'product-experience-copy.json': 'private/sexogate-product-experience-copy.json',
    'product-return-policy.json': 'private/sexogate-product-return-policy.json',
    'product-feedback.php': 'private/sg-product-feedback.php',
    'product-feedback-001.sql': 'private/product-feedback-001.sql',
    'product-gallery.php': 'private/sexogate-product-gallery.php',
    'product-gallery-data.json': 'private/sexogate-product-gallery-data.json',
    'runtime-catalog.php': 'private/sexogate-runtime-catalog.php',
}
EXTRA_SOURCE = (
    'apply.mjs', 'renderers.js', 'ui.js', 'storefront.css', 'home.css',
    'product-experience-core.js', 'product-experience-renderers.js',
    'product-experience-ui.js', 'product-experience.css', 'product-experience-build.mjs',
    'product-feedback.js', 'product-feedback.css', 'product-feedback-apply.mjs',
    'product-feedback-build.mjs', 'product-gallery-apply.mjs',
    'mega-menu-core.js', 'mega-menu-renderers.js', 'mega-menu-build.mjs', 'mega-menu.css',
    'gallery-experience-core.js', 'gallery-experience-build.mjs',
    'runtime-catalog-build.mjs',
)
TESTS = (
    ('productExperienceJs', 'node-json', 'test-native-product-experience.mjs', ()),
    ('megaMenuJs', 'node-tap', 'test-native-mega-menu.mjs', ()),
    ('galleryExperienceJs', 'node-tap', 'test-native-gallery-experience.mjs', ()),
    ('productExperiencePhp', 'php-json', 'test-native-product-experience.php', ()),
    ('editorialPhp', 'php-json', 'test-native-product-editorial.php', ()),
    ('feedbackSourcePhp', 'php-json', 'test-native-product-feedback.php', ()),
    ('feedbackPackagePhp', 'php-json', 'test-native-product-feedback.php', ('--package',)),
    ('gallerySourcePhp', 'php-json', 'test-native-product-gallery.php', ()),
    ('galleryPackagePhp', 'php-json', 'test-native-product-gallery.php', ('--package',)),
    ('runtimeCatalogPhp', 'php-json', 'test-native-runtime-catalog.php', ()),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(condition, code):
    if not condition:
        raise ValueError(code)


def fingerprint(full=True):
    package = json.loads(METADATA.read_text('utf-8-sig'))
    selection = json.loads(SELECTION.read_text('utf-8-sig'))
    release, dataset = package.get('release'), package.get('dataset')
    require(isinstance(release, str) and re.fullmatch('[a-f0-9]{24}', release), 'PRODUCT_MODULE_RELEASE_INVALID')
    require(isinstance(dataset, str) and re.fullmatch('[a-f0-9]{32}', dataset) and dataset == selection.get('dataset'), 'PRODUCT_MODULE_DATASET_INVALID')
    bundle, archive_path = Path(package['bundle']).resolve(), Path(package['archive']).resolve()
    require(bundle.name == 'bundle' and bundle.parent.name.startswith('native-stage-') and archive_path.parent == bundle.parent and archive_path.name == release + '.zip', 'PRODUCT_MODULE_PACKAGE_SCOPE_INVALID')
    require(archive_path.is_file(), 'PRODUCT_MODULE_ARCHIVE_MISSING')
    archive_sha = file_sha(archive_path)
    require(archive_sha == package.get('sha256') and archive_path.stat().st_size == package.get('bytes'), 'PRODUCT_MODULE_ARCHIVE_CHANGED')
    manifest_path = bundle / 'deployment-manifest.json'
    manifest = json.loads(manifest_path.read_text('utf-8-sig'))
    require(manifest.get('release') == release and manifest.get('dataset') == dataset and manifest.get('previewOnly') is True and manifest.get('checkoutEnabled') is False, 'PRODUCT_MODULE_MANIFEST_CONTEXT_INVALID')
    require(package.get('previewOnly') is True and package.get('checkoutEnabled') is False, 'PRODUCT_MODULE_PAYMENT_GUARD_REQUIRED')
    files = manifest.get('files')
    require(isinstance(files, dict) and files and package.get('files') == len(files), 'PRODUCT_MODULE_MANIFEST_FILES_INVALID')
    if full:
        with zipfile.ZipFile(archive_path) as archive:
            names = archive.namelist()
            require(len(names) == len(set(names)) and set(names) == set(files) | {'deployment-manifest.json'}, 'PRODUCT_MODULE_ARCHIVE_SET_INVALID')
            require(archive.read('deployment-manifest.json') == manifest_path.read_bytes(), 'PRODUCT_MODULE_ARCHIVE_MANIFEST_CHANGED')
            for relative, checksum in files.items():
                target = (bundle / relative).resolve()
                require(target.is_relative_to(bundle) and target.is_file() and isinstance(checksum, str) and re.fullmatch('[a-f0-9]{64}', checksum), 'PRODUCT_MODULE_MANIFEST_PATH_INVALID')
                require(file_sha(target) == checksum and digest(archive.read(relative)) == checksum, 'PRODUCT_MODULE_PACKAGE_FILE_CHANGED')
    catalog = json.loads((bundle / 'private/catalog.json').read_text('utf-8-sig'))
    require(catalog.get('dataset') == dataset and catalog.get('catalogOrigin') == 'sexogate-catalog-v2', 'PRODUCT_MODULE_CATALOG_CONTEXT_INVALID')
    source_files = {}
    copies = {}
    for source_name, relative in COPIES.items():
        checksum = file_sha(SOURCE / source_name)
        require(files.get(relative) == checksum and file_sha(bundle / relative) == checksum, 'PRODUCT_MODULE_SOURCE_PACKAGE_MISMATCH')
        source_files['native-store/storefront/' + source_name] = checksum
        copies[source_name] = {'packageFile': relative, 'sourceSha256': checksum, 'packageSha256': checksum}
    for name in EXTRA_SOURCE:
        source_files['native-store/storefront/' + name] = file_sha(SOURCE / name)
    for _, _, name, _ in TESTS:
        source_files['scripts/' + name] = file_sha(ROOT / 'scripts' / name)
    feedback_test = (ROOT / 'scripts/test-native-product-feedback.php').read_text('utf-8-sig')
    require(all(token in feedback_test for token in ("in_array('--package',$argv,true)", "['bundle'].'/private'", "require $private.'/control-indexnow.php'", "require $repo.'/native-store/storefront/product-feedback.php'")), 'PRODUCT_MODULE_FEEDBACK_PACKAGE_CONTRACT_CHANGED')
    gallery_test = (ROOT / 'scripts/test-native-product-gallery.php').read_text('utf-8-sig')
    require(all(token in gallery_test for token in ("in_array('--package',$argv,true)", "['bundle'].'/private/sexogate-product-gallery.php'", 'require $file;')), 'PRODUCT_MODULE_GALLERY_PACKAGE_CONTRACT_CHANGED')
    source_files['scripts/test-native-product-modules.py'] = file_sha(Path(__file__))
    source_files['native-store/upstream/web/app.js'] = file_sha(ROOT / 'native-store/upstream/web/app.js')
    source_files['native-store/upstream/hosting/control-indexnow.php'] = file_sha(ROOT / 'native-store/upstream/hosting/control-indexnow.php')
    prepared_catalog = Path(selection['path']) / 'catalog-data.json'
    prepared_sha = file_sha(prepared_catalog)
    require(prepared_sha == selection.get('sha256'), 'PRODUCT_MODULE_FROZEN_SOURCE_CHANGED')
    return {
        'release': release, 'dataset': dataset,
        'packageMetadataSha256': file_sha(METADATA),
        'selectionSha256': file_sha(SELECTION), 'frozenCatalogSha256': prepared_sha,
        'manifestSha256': file_sha(manifest_path), 'archiveSha256': archive_sha,
        'manifestFileCount': len(files), 'verifiedCopyPairs': copies,
        'sourceFiles': source_files,
        'sourceSha256': digest(json.dumps(source_files, sort_keys=True, separators=(',', ':')).encode('utf8')),
    }


def parse_result(kind, stdout):
    if kind == 'node-tap':
        counts = {}
        for label in ('tests', 'pass', 'fail', 'cancelled', 'skipped', 'todo'):
            matches = re.findall(r'^#\s+' + label + r'\s+(\d+)\s*$', stdout, re.M)
            require(len(matches) == 1, 'PRODUCT_MODULE_TAP_OUTPUT_INVALID')
            counts[label] = int(matches[0])
        require(counts['pass'] > 0 and counts['tests'] == counts['pass'] and all(counts[label] == 0 for label in ('fail', 'cancelled', 'skipped', 'todo')), 'PRODUCT_MODULE_TAP_CHECKS_INCOMPLETE')
        return {'passed': counts['pass'], 'tap': counts}
    result = json.loads(stdout)
    require(isinstance(result, dict) and type(result.get('passed')) is int and result['passed'] > 0, 'PRODUCT_MODULE_JSON_OUTPUT_INVALID')
    if 'checks' in result:
        require(isinstance(result['checks'], list) and len(result['checks']) == result['passed'], 'PRODUCT_MODULE_CHECK_COUNT_INVALID')
    for key in ('realProviderCalled', 'realApiCalled', 'externalNetworkCalled', 'externalCalls', 'sourceChanged', 'sourceSnapshotChanged'):
        require(key not in result or result[key] is False, 'PRODUCT_MODULE_EXTERNAL_OR_SOURCE_MUTATION')
    if result.get('networkCalled') is True:
        require(result.get('loopbackHttpCalled') is True and result.get('externalNetworkCalled') is False, 'PRODUCT_MODULE_EXTERNAL_NETWORK_FORBIDDEN')
    require('sourcePreserved' not in result or result['sourcePreserved'] is True, 'PRODUCT_MODULE_SOURCE_NOT_PRESERVED')
    # Uzun ürün metni veya mutlak yerel yollar yerine yalnız test kanıtı alanları tutulur.
    fields = ('passed', 'checks', 'products', 'titlesCleaned', 'minimumTrDescriptionBytes', 'testSha256', 'scriptSha256', 'moduleSha256', 'isolatedDatabase', 'sourcePreserved', 'realProviderCalled', 'realApiCalled', 'networkCalled', 'externalNetworkCalled', 'loopbackHttpCalled', 'externalCalls', 'sourceChanged', 'sourceSnapshotChanged')
    return {key: result[key] for key in fields if key in result}


def execute(test, before, node, php):
    name, kind, filename, arguments = test
    script = ROOT / 'scripts' / filename
    command = ([node, '--test', '--test-reporter=tap'] if kind == 'node-tap' else [node] if kind == 'node-json' else [str(php), '-d', 'extension=pdo_sqlite', '-d', 'extension=sqlite3']) + [str(script), *arguments]
    started = datetime.datetime.now(datetime.timezone.utc)
    completed = subprocess.run(command, cwd=ROOT, env=os.environ.copy(), capture_output=True, timeout=300)
    logs = ROOT / '.local/native-product-module-logs'
    logs.mkdir(parents=True, exist_ok=True)
    (logs / (name + '.stdout')).write_bytes(completed.stdout)
    (logs / (name + '.stderr')).write_bytes(completed.stderr)
    require(completed.returncode == 0, 'PRODUCT_MODULE_TEST_FAILED_' + name)
    result = parse_result(kind, completed.stdout.decode('utf-8-sig'))
    checksum = before['sourceFiles']['scripts/' + filename]
    for key in ('testSha256', 'scriptSha256'):
        require(key not in result or result[key] == checksum, 'PRODUCT_MODULE_TEST_SCRIPT_CHANGED')
    if name.startswith('gallery') and kind == 'php-json':
        module_hash = before['verifiedCopyPairs']['product-gallery.php']['sourceSha256']
        require(result.get('moduleSha256') == module_hash, 'PRODUCT_MODULE_WRONG_GALLERY_MODULE')
    if name.startswith('feedback'):
        # --package gerçek paket kontrol bağımlılığını, bayt eşitliği doğrulanmış kaynak feedback modülünü kullanır.
        require(result.get('isolatedDatabase') is True and result.get('externalCalls') is False, 'PRODUCT_MODULE_FEEDBACK_ISOLATION_REQUIRED')
        result['packageContract'] = 'packaged-control-dependency-with-byte-identical-feedback-source' if arguments else 'source-control-and-feedback'
    result.update(exitCode=completed.returncode, scriptSha256=checksum,
                  sourceSha256=before['sourceSha256'], arguments=list(arguments),
                  stdoutSha256=digest(completed.stdout), stderrSha256=digest(completed.stderr),
                  durationSeconds=round((datetime.datetime.now(datetime.timezone.utc) - started).total_seconds(), 3))
    print(json.dumps({'execution': name, 'passed': result['passed'], 'exitCode': completed.returncode}), flush=True)
    return result


def main():
    OUTPUT.unlink(missing_ok=True)
    node = shutil.which('node')
    php = ROOT / '.local/php-runtime/php.exe'
    require(bool(node) and php.is_file(), 'PRODUCT_MODULE_LOCAL_RUNTIME_MISSING')
    before = fingerprint(full=True)
    executions = {}
    for test in TESTS:
        require(fingerprint(full=False) == before, 'PRODUCT_MODULE_INPUT_CHANGED_DURING_TEST')
        executions[test[0]] = execute(test, before, node, php)
        require(fingerprint(full=False) == before, 'PRODUCT_MODULE_INPUT_CHANGED_DURING_TEST')
    require(set(executions) == {test[0] for test in TESTS}, 'PRODUCT_MODULE_EXECUTION_SET_INCOMPLETE')
    require(fingerprint(full=True) == before, 'PRODUCT_MODULE_INPUT_CHANGED_DURING_TEST')
    proof = {
        'schema': 1, 'profile': 'native-product-modules-v1', 'passed': True,
        'release': before['release'], 'dataset': before['dataset'],
        'runnerSha256': file_sha(Path(__file__)), 'sourceSha256': before['sourceSha256'],
        'fingerprint': before, 'executions': executions, 'executionEnvironment': 'local-isolated-cli',
        'fullPackageVerifiedBeforeAndAfter': True, 'fullPackageVerificationPasses': 2,
        'publishedToRemote': False, 'realProviderCalled': False,
        'completedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    temporary = OUTPUT.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n', 'utf8')
    require(fingerprint(full=False) == before, 'PRODUCT_MODULE_INPUT_CHANGED_DURING_TEST')
    temporary.replace(OUTPUT)
    print(json.dumps({'moduleProofCreated': True, 'release': before['release'], 'executions': len(executions), 'verifiedCopyPairs': len(COPIES), 'passed': {name: value['passed'] for name, value in executions.items()}, 'publishedToRemote': False, 'realProviderCalled': False}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        OUTPUT.unlink(missing_ok=True)
        code = str(error) if isinstance(error, ValueError) and re.fullmatch('[A-Za-z_0-9]+', str(error)) else type(error).__name__
        print(json.dumps({'moduleProofCreated': False, 'code': code}), file=sys.stderr)
        raise SystemExit(1)
