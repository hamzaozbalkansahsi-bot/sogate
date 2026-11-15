"""Apply the verified detail-recovery delta using the established rollback publisher."""
from pathlib import Path
import importlib.util, json, sys

R = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_recovery_publisher', R/'scripts/publish-native-locales-release.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)
publisher.E = R/'artifacts/storefront-followup-20261112'
publisher.REQUIRED_CHANGED = {'private/index.html','public/app.js','public/styles.css','public/locale-runtime.js'}
original_verify = publisher.verify_local_inputs

def verify(d):
    proof, base, release, source, public, counts = original_verify(d)
    publisher.require(proof['baseReleaseHash'] == 'af4206253f7b99b51084f2c71d195186cfe2bfbae6850729cbd6311518a0a821', 'unexpected_recovery_base')
    core = {'public/app.js','public/styles.css'}
    old_version = b'target-locales-20261111-r1'
    new_version = b'storefront-recovery-20261112-r1'
    new_sources = {'Loading product details…','The product details could not be loaded.'}
    reviewed = json.loads((R/'data/localization/reviewed-overrides.json').read_bytes())
    corrected_labels = {'Architrave profile','Search','Diameter','Model','Length','Width'}
    for name in proof['changedFiles']:
        before, after = base['all_bytes'][name], release['all_bytes'][name]
        if name in core:
            continue
        if name.startswith('public/locales/') or name.startswith('private/locale.'):
            a, b = json.loads(before), json.loads(after)
            publisher.require(set(b['translations'])-set(a['translations']) <= new_sources, 'unexpected_new_translation_'+name)
            publisher.require(all(b['translations'].get(k) == v or (k in corrected_labels and b['translations'].get(k) == reviewed[k][publisher.NATIVE.index(b['locale'])]) for k,v in a['translations'].items()), 'existing_translation_changed_'+name)
            a.pop('sourceInventorySha256', None); b.pop('sourceInventorySha256', None)
            a.pop('translations'); b.pop('translations')
            publisher.require(a == b, 'dictionary_metadata_changed_'+name)
        else:
            publisher.require(after == before.replace(old_version, new_version), 'non_version_dependency_change_'+name)
    acceptance = json.loads((publisher.E/'browser-local.json').read_bytes())
    publisher.require(all(row.get(key) is True for row in acceptance['checks'] for key in ['http503Retry','invalidResponseRetry','noAutomaticRetry','quantityPreserved']), 'recovery_browser_acceptance_incomplete')
    review = json.loads((publisher.E/'code-review.json').read_bytes())
    publisher.require(review.get('passed') is True and review.get('releaseHash') == proof['releaseHash'], 'recovery_code_review_missing')
    return proof, base, release, source, public, counts

publisher.verify_local_inputs = verify
if __name__ == '__main__':
    publisher.main()
