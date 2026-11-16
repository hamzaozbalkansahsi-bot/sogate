#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-acceptance.py
# Açıklama   : Pazaryeri yayın kapısının eski, eksik ve değiştirilmiş kanıtları geçici örneklerle reddettiğini sınar.
import hashlib,json,os,sqlite3,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import native_marketplace_acceptance as gate

RELEASE='1'*24
DATASET='2'*32
BASES={'local':'https://127.0.0.1:3188/test','preview':'https://sexogate.com/test/native-preview-'+'3'*16}
DISCOVERY_KEYS=['productFirstLayout','compactHeader','compactCampaignCards','balancedSelection','alignedCards','realCategoryTabs','tabsPreserveScrollAndFocus','tabDeepLink','keyboardRail','variantSelectionRequired','blogRoute','serverClientParity','mountedServerLinks','categoryImages','hierarchy','backRestoresSelection','sizeFilter','brandFilter','colorFilter','validCombinedFacets','sortPreservesFilters','invalidPriceRejected','keyboardDrawer','facetNoindex','facetCanonical','search','rtl','singleStore','serverCategoryLayout']

class MarketplaceAcceptanceTest(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='sexogate-gate-test-');self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name);self.minimum=time.time()-5
  self.fingerprint_function=gate.marketplace_source_fingerprint
  self.fingerprint={'release':RELEASE,'dataset':DATASET,'selectionSha256':'a'*64,'catalogSha256':'b'*64,'packageSha256':'c'*64,'sourceDatabaseSha256':'d'*64}
  fingerprint_patch=patch.object(gate,'marketplace_source_fingerprint',return_value=self.fingerprint);self.fingerprint_mock=fingerprint_patch.start();self.addCleanup(fingerprint_patch.stop)
  self.selection={'dataset':DATASET,'newProducts':131,'sourceProducts':138,'products':2325,'path':str(self.root/'prepared'),'sha256':'4'*64}
  self.write('.local/native-marketplace-selection.json',self.selection)
  scripts=['test-native-languages.py','test-native-marketplace-variants.py','native_variant_cases.py','test-native-marketplace-browser.py','test-native-marketplace-http.py','test-native-returns-public.py','test-native-returns-browser.py','test-native-returns-php.php','test-native-return-ordering.php','test-native-marketplace-discovery.py','test-native-marketplace-source-proof.py','test-native-marketplace-data.py','test-native-marketplace-payload.php']
  for name in scripts:self.bytes('scripts/'+name,('temporary fixture '+name).encode())
  for scope in BASES:self.baseline(scope)
  # Her olumsuz örnekten önce aynı geçici temel gerçekten kabul edilmelidir.
  for scope in BASES:self.accept(scope)

 def bytes(self,name,value):
  path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value);return path

 def write(self,name,value):return self.bytes(name,json.dumps(value,ensure_ascii=False).encode('utf8'))

 def read(self,name):return json.loads((self.root/name).read_text('utf8'))

 def checksum(self,name):return hashlib.sha256((self.root/name).read_bytes()).hexdigest()

 def rows(self,scope,keys=(),extra=None,script=None):
  common={'base':BASES[scope],'release':RELEASE,'pageErrors':0,**{k:True for k in keys},**(extra or {})}
  if script:common['scriptSha256']=self.checksum('scripts/'+script)
  return [{'engine':engine,**common}for engine in ['chromium','webkit']]

 def baseline(self,scope):
  self.write('.local/native-marketplace-import-'+scope+'.json',{'base':BASES[scope],'release':RELEASE,'dataset':DATASET,'loadedNew':131,'visibleNew':82,'idempotent':True,'oldSupplierProductsVisible':False,'genericBrandsNotInvented':True})
  self.write('.local/native-browser-marketplace-mount-'+scope+'.json',self.rows(scope,extra={'adminRoutes':33,'publicRoutes':9,'externalRequests':0,'mfa':True}))
  self.write('.local/native-languages-marketplace-mount-'+scope+'.json',{'base':BASES[scope],'release':RELEASE,'finalized':True,'pageErrors':0,'scriptSha256':self.checksum('scripts/test-native-languages.py'),'locales':[{'status':200,'selected':True,'adultMetadata':True,'clientAdultMetadata':True,'catalogUiReady':True}for _ in range(11)],'clientSwitches':[{'selected':True,'clientMetadata':True,'catalogUiReady':True}for _ in range(3)]})
  self.write('.local/native-adult-marketplace-adult-'+scope+'.json',self.rows(scope,['ageGate','guestBrowsing','keyboardFocus','escapeBypassBlocked'],{'worldMap':False,'furnitureCopy':False,'iconOnlySocialLinks':4}))
  self.write('.local/native-marketplace-polish-'+scope+'.json',self.rows(scope,['realImagesLoaded','alignedCards','footerPrivacyEntry','readableFeatures','horizontalRelatedRail','horizontalRecentRail','consentRevocation','accountHelperMountedOnce','productImageBounds'],{'furnitureCopy':False,'stickyOverlap':False,'underlinedLinks':False,'compactImageCampaignCards':4,'curtainDurationSeconds':4.8}))
  self.write('.local/native-marketplace-paint-'+scope+'.json',self.rows(scope,['javascriptDisabled','realImages'],{'serverHtmlCompactCards':4,'serverLocales':11,'legacyHero':False}))
  variant_hash=hashlib.sha256((self.root/'scripts/test-native-marketplace-variants.py').read_bytes()+(self.root/'scripts/native_variant_cases.py').read_bytes()).hexdigest()
  self.write('docs/native-marketplace-variants-'+scope+'-results.json',self.rows(scope,['selectionRequired','sizeColorCartLines','editMergeReload','legacyCartRepair','sourceMatrix','bulkAllItems','bulkCancellation','rtl'],{'scriptSha256':variant_hash,'realPayment':False,'consentNormalHoverFocus':'brand-burgundy/wine','isolatedCases':list(range(7))}))
  self.write('.local/native-marketplace-actions-'+scope+'.json',self.rows(scope,['primarySingleLine','touchTargets','quantityButtons','favoriteAndCompare','variantRequired','shareDialog','rtl'],{'cssPreview':False}))
  self.write('.local/native-marketplace-cart-notifications-'+scope+'.json',self.rows(scope,['cartSelectionTotals','quantityUpdates','variantLabels','moveToFavoritesAndRemove','summaryDialog','permissionNotRequestedAutomatically'],{'stickyOverlap':False,'notificationApi':{'externalPushSent':False}}))
  self.write('docs/native-marketplace-'+scope+'-results.json',self.rows(scope,['sourceCodesKept','finalMarkup15','noFakeInventory','noLegacyProducts','realImageHashes','draftMediaPrivate','categorySizeFilter','priceSort','facetNoindex','singleStore','adminMfa','adminFieldsAndSeo','adminGoToProductAfterReload','checkoutClosed'],{'dataset':DATASET,'loadedNew':131,'visibleNew':82,'allMarketplaceProductsTransferred':False},'test-native-marketplace-browser.py'))
  self.write('.local/native-marketplace-http-'+scope+'.json',{'base':BASES[scope],'release':RELEASE,'scriptSha256':self.checksum('scripts/test-native-marketplace-http.py'),'privatePathsBlocked':True,'guestOrderOwnership':True,'returnCsrfAndOrigin':True,'returnsNoStoreNoindex':True,'adminProtected':True,'checkoutClosed':True,'realPayments':False})
  self.write('.local/native-returns-public-'+scope+'.json',self.rows(scope,['guestLookupProtected','noOrderDataLeaked','trAndEn','rtlLanguageChoice','noStoreNoindex'],script='test-native-returns-public.py'))
  self.write('.local/native-returns-local.json',self.rows('local',['partialReturn','serverQuote','idempotency','cancelAndHistory','csrfAndOrigin','sessionAndOrderOwnership','warehouseFinancialBoundary','adminMfa','quarantineNoRestock','fiscalConfirmationSeparate','testExcludedFromLiveReport','trAndEn','rtlLanguageChoice','firstHtmlAndNoindex'],{'realPaymentsCalled':False,'fiscalApiCalled':False,'localPaidFixturesOnly':True},'test-native-returns-browser.py'))
  self.write('.local/returns-unit-source-final.json',{'passed':53,'realPaymentOrFiscalApiCalled':False,'testSha256':self.checksum('scripts/test-native-returns-php.php')})
  self.write('docs/native-marketplace-discovery-'+scope+'-results.json',{'base':BASES[scope],'results':self.rows(scope,DISCOVERY_KEYS,{'publicProducts':82,'occupiedRoots':6,'realPayments':False,'adminAccessed':False},'test-native-marketplace-discovery.py')})
  def isolated_execution(name,count):return {'exitCode':0,'passed':count,'checks':['fixture_check_'+str(n)for n in range(count)],'scriptSha256':self.checksum('scripts/'+name),'testSha256':self.checksum('scripts/'+name),'isolatedDatabase':True,'realPaymentOrFiscalApiCalled':False}
  source={'schema':1,'profile':'marketplace-source-v1','scope':scope,'targetBase':BASES[scope],'release':RELEASE,'dataset':DATASET,'sourceDetails':138,'loadedNew':131,'runnerSha256':self.checksum('scripts/test-native-marketplace-source-proof.py'),'fingerprint':self.fingerprint,'allMarketplaceProductsTransferred':False,'publishedToRemote':False,'realPaymentOrFiscalApiCalled':False,'executionEnvironment':'local-isolated-cli','executions':{'data':{'exitCode':0,'passed':6,'scriptSha256':self.checksum('scripts/test-native-marketplace-data.py')},'payload':{'exitCode':0,'passed':403,'newProducts':131,'publishCandidates':82,'isolatedDatabase':True,'publishedToRemote':False,'scriptSha256':self.checksum('scripts/test-native-marketplace-payload.php')},'returnsCore':isolated_execution('test-native-returns-php.php',53),'returnsCoreSource':isolated_execution('test-native-returns-php.php',53),'returnOrdering':isolated_execution('test-native-return-ordering.php',17),'returnOrderingSource':isolated_execution('test-native-return-ordering.php',17)}}
  self.write('docs/native-marketplace-source-'+scope+'-results.json',source)

 def accept(self,scope='local'):
  return gate.marketplace_acceptance(self.root,scope,RELEASE,BASES[scope],self.minimum)

 def assert_rejected(self,scope='local'):
  with self.assertRaises((ValueError,KeyError,FileNotFoundError)):self.accept(scope)

 def mutate_row(self,name,field,value):
  data=self.read(name);rows=data['results']if isinstance(data,dict)else data;rows[0][field]=value;self.write(name,data)

 def test_valid_profiles_do_not_claim_full_catalogue(self):
  for scope in BASES:
   with self.subTest(scope=scope):
    result=self.accept(scope);self.assertFalse(result['allTransferred']);self.assertEqual(result['sourceDetails'],138);self.assertEqual(result['loadedNew'],131);self.assertEqual(result['visibleNew'],82)

 def test_existing_import_and_browser_proof_cannot_replace_discovery(self):
  (self.root/'docs/native-marketplace-discovery-local-results.json').unlink();self.assert_rejected()

 def test_discovery_rejects_stale_report(self):
  path=self.root/'docs/native-marketplace-discovery-local-results.json';os.utime(path,(self.minimum-1,self.minimum-1));self.assert_rejected()

 def test_discovery_rejects_wrong_context_or_script(self):
  name='docs/native-marketplace-discovery-local-results.json';original=self.read(name)
  for field,value in [('engine','firefox'),('base',BASES['preview']),('release','9'*24),('scriptSha256','0'*64),('publicProducts',0),('occupiedRoots',0),('realPayments',True),('adminAccessed',True),('pageErrors',1)]:
   with self.subTest(field=field):
    self.write(name,original);self.mutate_row(name,field,value);self.assert_rejected()

 def test_discovery_rejects_each_missing_behavior(self):
  name='docs/native-marketplace-discovery-local-results.json';original=self.read(name)
  for key in DISCOVERY_KEYS:
   with self.subTest(behavior=key):
    self.write(name,original);self.mutate_row(name,key,False);self.assert_rejected()

 def test_source_proof_is_required_for_local_and_preview(self):
  for scope in BASES:
   with self.subTest(scope=scope):
    path=self.root/('docs/native-marketplace-source-'+scope+'-results.json');raw=path.read_bytes();path.unlink();self.assert_rejected(scope);path.write_bytes(raw)

 def test_source_proof_rejects_stale_report(self):
  path=self.root/'docs/native-marketplace-source-local-results.json';os.utime(path,(self.minimum-1,self.minimum-1));self.assert_rejected()

 def test_source_rejects_wrong_scope_release_dataset_or_hash(self):
  name='docs/native-marketplace-source-local-results.json';original=self.read(name)
  fields=[('schema',0),('profile','legacy-source'),('scope','preview'),('targetBase',BASES['preview']),('release','9'*24),('dataset','9'*32),('sourceDetails',139),('loadedNew',132),('runnerSha256','0'*64),('fingerprint',{'catalogSha256':'0'*64}),('executionEnvironment','remote-cli')]
  for field,value in fields:
   with self.subTest(field=field):
    data=json.loads(json.dumps(original));data[field]=value;self.write(name,data);self.assert_rejected()

 def test_source_rejects_full_catalogue_or_remote_execution_claims(self):
  name='docs/native-marketplace-source-local-results.json';original=self.read(name)
  for field in ['allMarketplaceProductsTransferred','publishedToRemote','realPaymentOrFiscalApiCalled']:
   with self.subTest(field=field):
    data=json.loads(json.dumps(original));data[field]=True;self.write(name,data);self.assert_rejected()

 def test_source_requires_every_real_cli_execution(self):
  name='docs/native-marketplace-source-local-results.json';original=self.read(name)
  for execution in original['executions']:
   for failure in ['missing','nonzero_exit','wrong_script_hash']:
    with self.subTest(execution=execution,failure=failure):
     data=json.loads(json.dumps(original))
     if failure=='missing':del data['executions'][execution]
     elif failure=='nonzero_exit':data['executions'][execution]['exitCode']=1
     else:data['executions'][execution]['scriptSha256']='0'*64
     self.write(name,data);self.assert_rejected()

 def test_source_rejects_old_or_incomplete_check_counts(self):
  name='docs/native-marketplace-source-local-results.json';original=self.read(name)
  for execution,count in [('data',5),('payload',402),('returnsCore',49),('returnsCoreSource',49),('returnOrdering',16),('returnOrderingSource',16)]:
   with self.subTest(execution=execution):
    data=json.loads(json.dumps(original));data['executions'][execution]['passed']=count;self.write(name,data);self.assert_rejected()

 def test_source_payload_must_match_loaded_and_visible_products(self):
  name='docs/native-marketplace-source-local-results.json';original=self.read(name)
  for field,value in [('newProducts',130),('publishCandidates',81),('isolatedDatabase',False),('publishedToRemote',True)]:
   with self.subTest(field=field):
    data=json.loads(json.dumps(original));data['executions']['payload'][field]=value;self.write(name,data);self.assert_rejected()

 def test_return_executions_require_current_test_hash_and_isolation(self):
  name='docs/native-marketplace-source-local-results.json';original=self.read(name)
  for execution in ['returnsCore','returnsCoreSource','returnOrdering','returnOrderingSource']:
   for field,value in [('testSha256','0'*64),('checks',[]),('isolatedDatabase',False),('realPaymentOrFiscalApiCalled',True)]:
    with self.subTest(execution=execution,field=field):
     data=json.loads(json.dumps(original));data['executions'][execution][field]=value;self.write(name,data);self.assert_rejected()

 def test_changed_inputs_invalidate_completed_source_proof(self):
  self.fingerprint_mock.return_value={**self.fingerprint,'catalogSha256':'9'*64};self.assert_rejected()

 def test_changed_runner_invalidates_completed_source_proof(self):
  self.bytes('scripts/test-native-marketplace-source-proof.py',b'changed fixture runner');self.assert_rejected()

 def test_changed_return_test_invalidates_completed_source_proof(self):
  self.bytes('scripts/test-native-return-ordering.php',b'changed fixture ordering test');self.assert_rejected()

 def test_fingerprint_recomputes_real_temporary_input_hashes(self):
  isolated=self.root/'fingerprint-case';home=isolated/'marketplace-catalog-20261116';prepared=home/'prepared';bundle=isolated/'bundle';private=bundle/'private'
  def raw(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)
  def write(path,value):raw(path,json.dumps(value,ensure_ascii=False).encode('utf8'))
  products=[{'id':'archived-'+str(i)}for i in range(2194)]+[{'id':'sg_ty_'+'a'*16}]
  data={'dataset':DATASET,'catalogOrigin':'sexogate-catalog-v2','products':products}
  write(prepared/'catalog-data.json',data);write(private/'catalog.json',data)
  selection={'path':str(prepared),'dataset':DATASET,'newProducts':1,'sourceProducts':1,'sha256':hashlib.sha256((prepared/'catalog-data.json').read_bytes()).hexdigest()}
  write(isolated/'.local/native-marketplace-selection.json',selection)
  write(isolated/'.local/native-stage-package.json',{'bundle':str(bundle),'release':RELEASE,'dataset':DATASET,'sha256':'e'*64})
  write(bundle/'deployment-manifest.json',{'release':RELEASE});write(isolated/'native-catalog-20261115/prepared/catalog-data.json',{'products':products[:2194]})
  write(prepared/'catalog-sources.json',{'dataset':DATASET});write(private/'catalog-sources.json',{'dataset':DATASET});write(home/'cover-review.json',[{'id':products[-1]['id'],'coverApproved':True}])
  write(prepared/'catalog-workbench/aa.json',{products[-1]['id']:{'media':[{'file':'reviewed.jpg'}]}});raw(home/'media/reviewed.jpg',b'isolated image fixture')
  db=sqlite3.connect(home/'research.sqlite')
  try:
   db.execute('CREATE TABLE products(status TEXT,detail_json TEXT)');db.execute('INSERT INTO products VALUES(?,?)',('ready','{"sourceCode":"SOURCE-001"}'));db.commit()
  finally:db.close()
  for script in set(gate.SOURCE_TESTS.values())|{'scripts/test-native-marketplace-source-proof.py','scripts/native_marketplace_acceptance.py'}:raw(isolated/script,('isolated '+script).encode())
  for source,target in [('core.php','sg-returns-core.php'),('jobs.php','sg-returns-jobs.php'),('sg-returns-001.sql','sg-returns-001.sql')]:
   value=('isolated '+source).encode();raw(isolated/'native-store/returns'/source,value);raw(private/target,value)
  raw(isolated/'native-store/deploy/install.php',b'isolated installer fixture')
  first=self.fingerprint_function(isolated)
  self.assertEqual(first['catalogDataSha256'],selection['sha256']);self.assertEqual(first['selectionSha256'],hashlib.sha256((isolated/'.local/native-marketplace-selection.json').read_bytes()).hexdigest());self.assertEqual(first['release'],RELEASE)
  raw(home/'media/reviewed.jpg',b'changed isolated image fixture');second=self.fingerprint_function(isolated)
  self.assertNotEqual(first['reviewedMediaSha256'],second['reviewedMediaSha256']);self.assertEqual(first['catalogDataSha256'],second['catalogDataSha256'])
  raw(private/'sg-returns-jobs.php',b'mismatched isolated jobs fixture')
  with self.assertRaisesRegex(ValueError,'MARKETPLACE_RETURN_SOURCE_PACKAGE_MISMATCH'):self.fingerprint_function(isolated)

if __name__=='__main__':unittest.main(verbosity=2)
