from pathlib import Path
import copy,hashlib,importlib.util,json,unittest
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('gate',R/'lib/media_object_gate.py');gate=importlib.util.module_from_spec(s);s.loader.exec_module(gate)
H=lambda v:hashlib.sha256(v).hexdigest()
class WholeObjectAcceptanceTest(unittest.TestCase):
 def test_new_cleaned_image_needs_its_own_whole_object_review(self):
  self.manifest['images']['unreviewed']={**self.manifest['images']['mira'],'sourceSha':'d'*64,'outputSha':'e'*64}
  with self.assertRaisesRegex(ValueError,'uncovered'):gate.validate_object_evidence(self.manifest,self.policy,self.record)
 def test_complete_source_and_reference_sets_are_pinned(self):
  self.policy['sourceSetSha256']=H(json.dumps(sorted([k,r['sourceSha']]for k,r in self.manifest['images'].items()),separators=(',',':')).encode());self.manifest['references']={'4929:3':'mira'};self.policy['referenceSetSha256']=H(json.dumps(sorted(self.manifest['references'].items()),separators=(',',':')).encode());gate.validate_object_evidence(self.manifest,self.policy,self.record)
  bad=copy.deepcopy(self.manifest);bad['images']['extra']={'state':'approved_unmodified','sourceSha':'d'*64}
  with self.assertRaisesRegex(ValueError,'source set'):gate.validate_object_evidence(bad,self.policy,self.record)
  bad=copy.deepcopy(self.manifest);bad['references']['4929:4']='mira'
  with self.assertRaisesRegex(ValueError,'reference set'):gate.validate_object_evidence(bad,self.policy,self.record)
 def setUp(self):
  self.policy={'version':'whole-object-v1','required':{'mira':{'sourceSha256':'a'*64,'fields':[{'id':260,'box':[654,450,676,457],'kind':'physical_object'}]}},'rejectedOutputSha256':['9c99dc0d11b34aa52eeb555c4026f184ead06d51b0b1bd965d3177725ab4456d']}
  self.manifest={'images':{'mira':{'sourceSha':'a'*64,'outputSha':'b'*64,'state':'approved_cleaned','width':880,'height':880}}}
  self.record={'version':'whole-object-v1','images':{'mira':{'sourceSha256':'a'*64,'outputSha256':'b'*64,'width':880,'height':880,'reviewer':'actual native and full product review','fields':[{'id':260,'maskBox':[645,444,680,463],'wholeObjectRemoved':True,'rimAndShadowRemoved':True,'surfaceContinuous':True,'edgesContinuous':True,'visualReview':True}]}}}
 def test_word_erased_live_mira_cannot_publish(self):
  self.manifest['images']['mira']['outputSha']=self.policy['rejectedOutputSha256'][0]
  with self.assertRaisesRegex(ValueError,'retained'):gate.validate_object_evidence(self.manifest,self.policy,self.record)
 def test_complete_review_accepts_only_its_current_source_output(self):
  gate.validate_object_evidence(self.manifest,self.policy,self.record)
  self.manifest['images']['mira']['outputSha']='c'*64
  with self.assertRaisesRegex(ValueError,'hash'):gate.validate_object_evidence(self.manifest,self.policy,self.record)
 def test_missing_or_partial_body_review_fails(self):
  for field in ['wholeObjectRemoved','rimAndShadowRemoved','surfaceContinuous','edgesContinuous','visualReview']:
   record=copy.deepcopy(self.record);record['images']['mira']['fields'][0][field]=False
   with self.subTest(field=field),self.assertRaisesRegex(ValueError,'whole object'):gate.validate_object_evidence(self.manifest,self.policy,record)
  with self.assertRaises(ValueError):gate.validate_object_evidence(self.manifest,self.policy,{'version':'whole-object-v1','images':{}})
 def test_ink_only_mask_and_wrong_dimensions_fail(self):
  self.record['images']['mira']['fields'][0]['maskBox']=[654,450,676,457]
  with self.assertRaisesRegex(ValueError,'footprint'):gate.validate_object_evidence(self.manifest,self.policy,self.record)
  self.record['images']['mira']['fields'][0]['maskBox']=[645,444,680,463];self.record['images']['mira']['width']=881
  with self.assertRaisesRegex(ValueError,'dimensions'):gate.validate_object_evidence(self.manifest,self.policy,self.record)
 def test_unexpected_omitted_or_duplicate_fields_fail(self):
  for fields in [[],self.record['images']['mira']['fields']*2,[{**self.record['images']['mira']['fields'][0],'id':261}]]:
   with self.subTest(fields=fields),self.assertRaisesRegex(ValueError,'coverage'):gate.validate_object_evidence(self.manifest,self.policy,{**self.record,'images':{'mira':{**self.record['images']['mira'],'fields':fields}}})
 def test_reencoded_output_cannot_self_approve_with_a_new_receipt(self):
  self.policy['required']['mira']['acceptedOutputSha256']='b'*64;self.manifest['images']['mira']['outputSha']='c'*64;self.record['images']['mira']['outputSha256']='c'*64
  with self.assertRaisesRegex(ValueError,'accepted'):gate.validate_object_evidence(self.manifest,self.policy,self.record)
 def test_actual_decoded_frame_mask_and_timing_are_bound(self):
  f=self.policy['required']['mira']['fields'][0];f.update(sourceFrame=10,durationMs=80,maskSha256='d'*64,outputRgbaSha256='e'*64);p=self.record['images']['mira']['fields'][0];p.update(sourceFrame=10,durationMs=80,maskSha256='d'*64,outputRgbaSha256='e'*64);gate.validate_object_evidence(self.manifest,self.policy,self.record)
  for key,value in [('sourceFrame',9),('durationMs',81),('maskSha256','f'*64),('outputRgbaSha256','f'*64)]:
   bad=copy.deepcopy(self.record);bad['images']['mira']['fields'][0][key]=value
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'frame|mask|pixel'):gate.validate_object_evidence(self.manifest,self.policy,bad)
if __name__=='__main__':unittest.main()
