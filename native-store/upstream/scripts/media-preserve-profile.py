"""Restore source ICC metadata on reviewed lossless rasters without changing pixels."""
from __future__ import annotations
import argparse,copy,hashlib,io,json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
FROZEN='37fbdbdb594cb9d366fec3cb7f2662a694d4497ea7545607d471d23c3a9ecbd9'
DEST=ROOT/'artifacts/media-profile-preservation'
def sha(body):return hashlib.sha256(body).hexdigest()
def safe(relative):
    path=ROOT/relative;actual=path.resolve()
    if path.is_symlink() or not actual.is_relative_to(ROOT/'artifacts'):raise ValueError('Unsafe artifact path')
    return actual
def immutable(path,body):
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        with path.open('xb') as stream:stream.write(body)
    except FileExistsError:
        if path.read_bytes()!=body:raise ValueError('Immutable output collision')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    raw=(ROOT/'artifacts/media-cleanup.json').read_bytes();manifest=json.loads(raw)
    if manifest['pipelineVersion']!=FROZEN:raise ValueError('Unexpected base pipeline')
    records=[];selections={};needed=[]
    for key,row in manifest['images'].items():
        if row['state']!='approved_cleaned':continue
        source_path=safe(row['sourcePath']);old_path=safe(row['path'])
        if sha(source_path.read_bytes())!=row['sourceSha'] or sha(old_path.read_bytes())!=row['outputSha']:raise ValueError('Reviewed image bytes changed')
        with Image.open(source_path) as source,Image.open(old_path) as old:
            profile=source.info.get('icc_profile') or b''
            if profile==(old.info.get('icc_profile') or b''):continue
            if getattr(old,'n_frames',1)!=1:raise ValueError('Animated profile change requires framewise review')
            if source.getexif().get(274,1) not in (0,1) or old.getexif().get(274,1) not in (0,1):raise ValueError('Orientation change requires explicit review')
            needed.append(key)
            if not args.apply:continue
            pixels=old.convert('RGBA').tobytes();size=old.size;format=old.format
            if format not in {'WEBP','PNG'}:raise ValueError('Reviewed output must be lossless PNG/WebP')
            options={'icc_profile':profile}
            if format=='WEBP':options.update(lossless=True,quality=100,method=6)
            old.load();out=io.BytesIO();old.save(out,format=format,**options);body=out.getvalue()
        with Image.open(io.BytesIO(body)) as decoded:
            if decoded.size!=size or decoded.convert('RGBA').tobytes()!=pixels or decoded.info.get('icc_profile',b'')!=profile:raise ValueError('Profile remux changed pixels or profile')
        digest=sha(body);extension='webp' if format=='WEBP' else 'png';path=DEST/'outputs'/(digest+'.'+extension);immutable(path,body)
        candidate=copy.deepcopy(row['finalReview']['candidate'])
        candidate.update(urlSha=key,sourceSha=row['sourceSha'],sourcePath=row['sourcePath'],pipelineVersion=FROZEN,path=path.relative_to(ROOT).as_posix(),outputSha=digest,bytes=len(body),width=size[0],height=size[1],mime='image/'+extension)
        candidate['profilePreservation']={'previousReviewedOutputSha':row['outputSha'],'sourceIccSha256':sha(profile),'decodedRgbaSha256':sha(pixels),'allDecodedPixelsUnchanged':True,'iccMatchesSource':True,'previousVisualSelection':row['finalReview']['selection']}
        records.append(candidate)
        selections[key]={'candidateSha':digest,'reviewer':'Codex root profile restoration and decoded-pixel equivalence review 2026-10-31','notes':'Previously visually accepted retouch. Original ICC profile restored; every decoded RGBA byte is identical to the reviewed output. Product geometry, masks, source and post-scan evidence remain unchanged. Source ICC SHA256 '+sha(profile),'structureReview':True}
    receipt={'schemaVersion':1,'pipelineVersion':FROZEN,'sourceManifestSha256':sha(raw),'publicationReady':False,'images':records}
    if args.apply:
        DEST.mkdir(parents=True,exist_ok=True)
        (DEST/'candidates.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
        (DEST/'selections.json').write_text(json.dumps({'schemaVersion':1,'basePipelineVersion':FROZEN,'selections':selections},ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'mode':'apply' if args.apply else 'plan','reviewedCleanedImages':sum(r['state']=='approved_cleaned' for r in manifest['images'].values()),'profileFixesNeeded':len(needed),'writtenCandidates':len(records),'mainManifestModified':False,'publicationReady':False}))

if __name__=='__main__':main()
