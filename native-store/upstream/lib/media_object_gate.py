"""Hash-bound whole-object acceptance, independent of legacy ink detectors."""
import hashlib,json
def validate_object_evidence(manifest,policy,receipt):
 if policy.get('version')!='whole-object-v1' or receipt.get('version')!=policy['version']:raise ValueError('Missing whole object evidence version')
 digest=lambda value:hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()
 if policy.get('sourceSetSha256') and digest(sorted([k,r['sourceSha']]for k,r in manifest['images'].items()))!=policy['sourceSetSha256']:raise ValueError('Complete whole object source set changed')
 if policy.get('referenceSetSha256') and digest(sorted(manifest.get('references',{}).items()))!=policy['referenceSetSha256']:raise ValueError('Complete whole object reference set changed')
 if any(row.get('state')=='approved_cleaned'and key not in policy['required']for key,row in manifest['images'].items()):raise ValueError('uncovered whole object cleaned image')
 rejected=set(policy['rejectedOutputSha256'])
 for row in manifest['images'].values():
  if row.get('outputSha') in rejected:raise ValueError('Known retained physical sticker output cannot publish')
 required=policy['required'];reviews=receipt.get('images',{})
 for key,requirement in required.items():
  current=manifest['images'].get(key);review=reviews.get(key)
  if not current or not review:raise ValueError('Missing whole object source coverage')
  if requirement['sourceSha256']!=current['sourceSha'] or review.get('sourceSha256')!=current['sourceSha'] or review.get('outputSha256')!=current['outputSha']:raise ValueError('Whole object source/output hash mismatch')
  if requirement.get('acceptedOutputSha256',current['outputSha'])!=current['outputSha']:raise ValueError('Output differs from actually accepted whole object bytes')
  for name in ['outputRgbaSha256','maskPath','maskSha256','timeline']:
   if name in requirement and review.get(name)!=requirement[name]:raise ValueError('Whole object decoded pixels, mask or frame timeline differ')
  if review.get('width')!=current['width'] or review.get('height')!=current['height']:raise ValueError('Whole object dimensions mismatch')
  if not isinstance(review.get('reviewer'),str) or not review['reviewer'].strip():raise ValueError('Missing whole object visual reviewer')
  fields=review.get('fields',[]);expected=requirement['fields']
  if sorted(f.get('id',-1)for f in fields)!=sorted(f['id']for f in expected):raise ValueError('Whole object field coverage mismatch')
  by_id={f['id']:f for f in fields}
  for field in expected:
   proof=by_id[field['id']]
   for name in ['sourceFrame','durationMs','outputRgbaSha256','maskPath','maskSha256']:
    if name in field and proof.get(name)!=field[name]:raise ValueError('Whole object decoded frame, pixel or mask binding differs')
   if proof.get('visualReview')is not True:raise ValueError('Incomplete whole object visual acceptance')
   if field['kind']=='already_removed_print':
    if proof.get('noPhysicalObjectRemains')is not True:raise ValueError('Incomplete whole object print acceptance')
    continue
   if any(proof.get(flag)is not True for flag in ['wholeObjectRemoved','rimAndShadowRemoved','surfaceContinuous','edgesContinuous']):raise ValueError('Incomplete whole object surface and edge acceptance')
   box=proof.get('maskBox',[]);x0,y0,x1,y1=field['box'];w=current['width'];h=current['height']
   if len(box)!=4 or any(type(v)is not int for v in box)or not(0<=box[0]<box[2]<=w and 0<=box[1]<box[3]<=h)or box[0]>max(0,x0-2)or box[1]>max(0,y0-2)or box[2]<min(w,x1+2)or box[3]<min(h,y1+2):raise ValueError('Ink-only or invalid physical object footprint')
 return True
