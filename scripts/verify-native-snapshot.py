#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/verify-native-snapshot.py
# Açıklama   : Kaynak NODENO klasörü olmadan da Git'teki doğrudan kopyanın bütünlüğünü doğrular.
import hashlib,json,re
from pathlib import Path,PurePosixPath
from native_fixture_safety import FILES

ROOT=Path(__file__).resolve().parent.parent;folder=ROOT/'native-store/upstream';manifest=json.loads((ROOT/'native-store/source-manifest.json').read_text('utf8'))
assert len(manifest['files'])>=400
exceptions=manifest.get('fixtureSanitizations',{})
assert set(exceptions)<=FILES
for name,proof in exceptions.items():
 assert proof['safeSha256']==manifest['files'][name] and re.fullmatch('[a-f0-9]{64}',proof['sourceSha256']) and proof['sourceSha256']!=proof['safeSha256'],name
assert {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}==set(manifest['files']),'SOURCE_FILE_INVENTORY_CHANGED'
for name,expected in manifest['files'].items():
 rel=PurePosixPath(name);path=folder/name
 assert not rel.is_absolute() and '..' not in rel.parts and path.resolve().is_relative_to(folder.resolve()) and not path.is_symlink(),name
 assert re.fullmatch('[a-f0-9]{64}',expected) and hashlib.sha256(path.read_bytes()).hexdigest()==expected,name
 assert not any(p.startswith(('.env','client_secret')) or p.endswith('.local') for p in rel.parts),name
 assert path.suffix.lower() not in {'.sqlite','.db','.bin'},name
assets=ROOT/'native-store/theme/assets';proof=json.loads((assets/'sources.json').read_text('utf8'))
assert {p.relative_to(assets).as_posix() for p in assets.rglob('*') if p.is_file()}==set(proof['files'])|{'sources.json'},'THEME_FILE_INVENTORY_CHANGED'
for name,expected in proof['files'].items():
 path=assets/name;assert path.resolve().is_relative_to(assets.resolve()) and not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==expected,name
print(json.dumps({'sourceFiles':len(manifest['files']),'hashesVerified':True,'byteIdenticalFiles':len(manifest['files'])-len(exceptions),'syntheticFixtureExceptions':len(exceptions),'themeAssetsVerified':len(proof['files']),'donorSecretsOrDatabaseCopied':False}))
