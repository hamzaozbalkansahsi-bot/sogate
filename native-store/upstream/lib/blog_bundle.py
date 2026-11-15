"""Validate and merge immutable editorial images without exposing draft files publicly."""
import hashlib,re
def unpack_bundle(index,blob):
 if not isinstance(index,dict)or index.get('schema')!=1 or not isinstance(index.get('files'),dict):raise ValueError('blog_bundle_schema_invalid')
 result={};segments=[]
 for url,row in index['files'].items():
  if not re.fullmatch(r'/assets/blog/[a-z0-9][a-z0-9-]*\.(svg|png|webp|jpg)',url)or not isinstance(row,dict):raise ValueError('blog_bundle_url_invalid')
  offset=row.get('offset');length=row.get('length');sha=row.get('sha256')
  if type(offset)is not int or type(length)is not int or offset<0 or not 0<length<=2000000 or offset+length>len(blob)or not isinstance(sha,str)or not re.fullmatch('[a-f0-9]{64}',sha):raise ValueError('blog_bundle_range_invalid')
  data=blob[offset:offset+length]
  if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('blog_bundle_hash_mismatch')
  expected={'.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.jpg':'image/jpeg'}[url[url.rfind('.'):]]
  if row.get('mime')!=expected:raise ValueError('blog_bundle_mime_invalid')
  result[url]={'bytes':data,'mime':expected};segments.append((offset,length))
 cursor=0
 for offset,length in sorted(segments):
  if offset!=cursor:raise ValueError('blog_bundle_hidden_or_overlapping_bytes')
  cursor+=length
 if cursor!=len(blob):raise ValueError('blog_bundle_hidden_or_overlapping_bytes')
 return result
def pack_bundle(images):
 index={'schema':1,'files':{}};parts=[];offset=0
 for url,row in sorted(images.items()):
  body=row['bytes'];index['files'][url]={'offset':offset,'length':len(body),'sha256':hashlib.sha256(body).hexdigest(),'mime':row['mime']};parts.append(body);offset+=len(body)
 blob=b''.join(parts);unpack_bundle(index,blob);return index,blob
def upgrade_legacy_index(index):
 """Add MIME to the first deployed schema-1 index; hashes and ranges stay strict."""
 if not isinstance(index,dict)or not isinstance(index.get('files'),dict):return index
 rows={}
 for url,row in index['files'].items():
  row=dict(row)if isinstance(row,dict)else row
  if isinstance(row,dict)and 'mime'not in row:
   row['mime']={'.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.jpg':'image/jpeg'}.get(url[url.rfind('.'):],'')
  rows[url]=row
 return {**index,'files':rows}

def merge_bundles(old_index,old_blob,new_index,new_blob):
 old=unpack_bundle(upgrade_legacy_index(old_index),old_blob)if old_index is not None else{};new=unpack_bundle(new_index,new_blob)
 for url,row in new.items():
  if url in old and old[url]!=row:raise ValueError('immutable_blog_image_url_changed')
 return pack_bundle({**old,**new})
