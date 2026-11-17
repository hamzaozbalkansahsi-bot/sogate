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
MODULE_TESTS={'productExperienceJs':'test-native-product-experience.mjs','megaMenuJs':'test-native-mega-menu.mjs','galleryExperienceJs':'test-native-gallery-experience.mjs','productExperiencePhp':'test-native-product-experience.php','editorialPhp':'test-native-product-editorial.php','feedbackSourcePhp':'test-native-product-feedback.php','feedbackPackagePhp':'test-native-product-feedback.php','gallerySourcePhp':'test-native-product-gallery.php','galleryPackagePhp':'test-native-product-gallery.php','runtimeCatalogPhp':'test-native-runtime-catalog.php'}
MEMORY_MODULES=('public/index.php','deploy/worker.php','private/control-http.php','private/control-catalog.php','private/control-store.php','private/sexogate-catalog.php','private/sexogate-runtime-catalog.php','private/catalog.json','private/catalog-active.json.gz','private/catalog-active.meta.json','private/sexogate-storefront-content.php','private/sexogate-product-editorial.php','private/sexogate-product-editorial-data.json','private/sexogate-product-gallery.php','private/sexogate-product-gallery-data.json','private/sexogate-notifications.php')

class MarketplaceAcceptanceTest(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='sexogate-gate-test-');self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name);self.minimum=time.time()-5
  self.fingerprint_function=gate.marketplace_source_fingerprint
  self.fingerprint={'release':RELEASE,'dataset':DATASET,'selectionSha256':'a'*64,'catalogSha256':'b'*64,'packageSha256':'c'*64,'sourceDatabaseSha256':'d'*64}
  fingerprint_patch=patch.object(gate,'marketplace_source_fingerprint',return_value=self.fingerprint);self.fingerprint_mock=fingerprint_patch.start();self.addCleanup(fingerprint_patch.stop)
  self.module_fingerprint={'release':RELEASE,'dataset':DATASET,'sourceSha256':'7'*64,'manifestSha256':'8'*64}
  self.module_fingerprint_function=gate.product_module_fingerprint
  module_patch=patch.object(gate,'product_module_fingerprint',return_value=self.module_fingerprint,create=True);self.module_fingerprint_mock=module_patch.start();self.addCleanup(module_patch.stop)
  self.selection={'dataset':DATASET,'newProducts':958,'sourceProducts':1002,'products':3152,'path':str(self.root/'prepared'),'sha256':'4'*64}
  self.write('.local/native-marketplace-selection.json',self.selection)
  self.write('native-store/storefront/product-gallery-data.json',{'schema':1,'sourceDataset':DATASET,'products':{'isolated_fixture':{}}})
  scripts=['test-native-languages.py','test-native-marketplace-variants.py','native_variant_cases.py','test-native-marketplace-browser.py','test-native-marketplace-http.py','test-native-returns-public.py','test-native-returns-browser.py','test-native-returns-php.php','test-native-return-ordering.php','test-native-marketplace-discovery.py','test-native-marketplace-source-proof.py','test-native-marketplace-data.py','test-native-marketplace-payload.php','test-native-installer.php','test-native-marketplace-seo.php']
  scripts+=['clean-native-marketplace-copy.py','native_marketplace_copy.py','test-native-product-experience-browser.py']
  scripts+=list(set(MODULE_TESTS.values()))+['test-native-product-modules.py','test-native-product-runtime-memory.py']
  for name in scripts:self.bytes('scripts/'+name,('temporary fixture '+name).encode())
  self.product_proofs()
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

 def product_proofs(self):
  bundle=self.root/'bundle';archive=self.bytes('package.zip',b'isolated acceptance archive')
  files={name:self.checksum(str(self.bytes('bundle/'+name,('fixture '+name).encode()).relative_to(self.root)))for name in MEMORY_MODULES}
  self.write('bundle/deployment-manifest.json',{'release':RELEASE,'dataset':DATASET,'files':files})
  self.write('.local/native-stage-package.json',{'release':RELEASE,'dataset':DATASET,'bundle':str(bundle),'archive':str(archive),'sha256':self.checksum('package.zip')})
  self.write('.local/native-product-module-results.json',{'schema':1,'profile':'native-product-modules-v1','passed':True,'release':RELEASE,'dataset':DATASET,'runnerSha256':self.checksum('scripts/test-native-product-modules.py'),'sourceSha256':self.module_fingerprint['sourceSha256'],'fingerprint':self.module_fingerprint,'executionEnvironment':'local-isolated-cli','fullPackageVerifiedBeforeAndAfter':True,'fullPackageVerificationPasses':2,'publishedToRemote':False,'realProviderCalled':False,'executions':{name:{'passed':1,'exitCode':0,'scriptSha256':self.checksum('scripts/'+script)}for name,script in MODULE_TESTS.items()}})
  cases={name:{'case':name,'release':RELEASE,'exitCode':0,'ok':True,'memoryLimit':'128M','peakBytes':122*1024*1024,'fatal':False,'realProviderCalled':False}for name in ['worker','customer','adminSchema','adminProducts']}
  cases['worker'].update(healthOk=True,notificationsSent=0)
  cases['customer'].update(sourceProducts=958,publicProducts=803,stories=803)
  cases['adminSchema'].update(sourceProducts=3152,publicProducts=803,schemaProducts=3152,schemaVisibleProducts=803,unusedCatalogReleased=True)
  cases['adminProducts'].update(sourceProducts=958,publicProducts=803,rows=958,publishedRows=803,reviewRows=155,unusedCatalogReleased=True)
  self.write('.local/native-product-runtime-memory.json',{'schema':1,'passed':True,'executionEnvironment':'local-isolated-php-128M','actualExecutions':4,'packageUnchanged':True,'realProviderCalled':False,'release':RELEASE,'dataset':DATASET,'scriptSha256':self.checksum('scripts/test-native-product-runtime-memory.py'),'packageArchiveSha256':self.checksum('package.zip'),'moduleHashes':files,'cases':cases})

 def baseline(self,scope):
  self.write('.local/native-marketplace-import-'+scope+'.json',{'base':BASES[scope],'release':RELEASE,'dataset':DATASET,'loadedNew':958,'visibleNew':803,'idempotent':True,'oldSupplierProductsVisible':False,'genericBrandsNotInvented':True})
  self.write('.local/native-marketplace-copy-'+scope+'.json',{'schema':1,'base':BASES[scope],'release':RELEASE,'dataset':DATASET,'visible':803,'scriptSha256':self.checksum('scripts/clean-native-marketplace-copy.py'),'helperSha256':self.checksum('scripts/native_marketplace_copy.py'),'remainingCTAs':0,'realPayments':False,**{key:True for key in ['protectedFieldsNoChange','sourcePreserved','idempotent','verifiedAfterReload','expectedSetMatch','actualRequests']}})
  self.write('.local/native-browser-marketplace-mount-'+scope+'.json',self.rows(scope,extra={'adminRoutes':33,'publicRoutes':9,'externalRequests':0,'mfa':True}))
  self.write('.local/native-languages-marketplace-mount-'+scope+'.json',{'base':BASES[scope],'release':RELEASE,'finalized':True,'pageErrors':0,'scriptSha256':self.checksum('scripts/test-native-languages.py'),'locales':[{'status':200,'selected':True,'adultMetadata':True,'clientAdultMetadata':True,'catalogUiReady':True}for _ in range(11)],'clientSwitches':[{'selected':True,'clientMetadata':True,'catalogUiReady':True}for _ in range(3)]})
  self.write('.local/native-adult-marketplace-adult-'+scope+'.json',self.rows(scope,['ageGate','guestBrowsing','keyboardFocus','escapeBypassBlocked'],{'worldMap':False,'furnitureCopy':False,'iconOnlySocialLinks':4}))
  self.write('.local/native-marketplace-polish-'+scope+'.json',self.rows(scope,['realImagesLoaded','alignedCards','footerPrivacyEntry','readableFeatures','horizontalRelatedRail','horizontalRecentRail','consentRevocation','accountHelperMountedOnce','productImageBounds'],{'furnitureCopy':False,'stickyOverlap':False,'underlinedLinks':False,'compactImageCampaignCards':4,'curtainDurationSeconds':4.8}))
  self.write('.local/native-marketplace-paint-'+scope+'.json',self.rows(scope,['javascriptDisabled','realImages'],{'serverHtmlCompactCards':4,'serverLocales':11,'legacyHero':False}))
  variant_hash=hashlib.sha256((self.root/'scripts/test-native-marketplace-variants.py').read_bytes()+(self.root/'scripts/native_variant_cases.py').read_bytes()).hexdigest()
  self.write('docs/native-marketplace-variants-'+scope+'-results.json',self.rows(scope,['selectionRequired','sizeColorCartLines','editMergeReload','legacyCartRepair','sourceMatrix','bulkAllItems','bulkCancellation','rtl'],{'scriptSha256':variant_hash,'realPayment':False,'consentNormalHoverFocus':'brand-burgundy/wine','isolatedCases':list(range(7))}))
  self.write('.local/native-marketplace-actions-'+scope+'.json',self.rows(scope,['primarySingleLine','touchTargets','quantityButtons','favoriteAndCompare','variantRequired','shareDialog','rtl'],{'cssPreview':False}))
  self.write('.local/native-marketplace-cart-notifications-'+scope+'.json',self.rows(scope,['cartSelectionTotals','quantityUpdates','variantLabels','moveToFavoritesAndRemove','summaryDialog','permissionNotRequestedAutomatically'],{'stickyOverlap':False,'notificationApi':{'externalPushSent':False}}))
  self.write('docs/native-marketplace-'+scope+'-results.json',self.rows(scope,['sourceCodesKept','finalMarkup15','noFakeInventory','noLegacyProducts','realImageHashes','draftMediaPrivate','categorySizeFilter','priceSort','facetNoindex','singleStore','adminMfa','adminFieldsAndSeo','adminGoToProductAfterReload','checkoutClosed'],{'dataset':DATASET,'loadedNew':958,'visibleNew':803,'allMarketplaceProductsTransferred':False},'test-native-marketplace-browser.py'))
  self.write('.local/native-product-experience-'+scope+'.json',self.rows(scope,gate.PRODUCT_EXPERIENCE_KEYS,{'scope':scope,'dataset':DATASET,'visibleNew':803,'widths':[360,390,430,768,1440],'samples':5,'galleryImageCount':2,'feedbackReference':'SGF-261117-ABCDEF123456','feedbackReviewedVersion':2,'qaFeedbackClearlyLabelled':True,'realPayments':False,'ordersCreated':False,'realRefunds':False,'sourceSnapshotChanged':False},'test-native-product-experience-browser.py'))
  self.write('.local/native-marketplace-http-'+scope+'.json',{'base':BASES[scope],'release':RELEASE,'scriptSha256':self.checksum('scripts/test-native-marketplace-http.py'),'privatePathsBlocked':True,'guestOrderOwnership':True,'returnCsrfAndOrigin':True,'returnsNoStoreNoindex':True,'adminProtected':True,'checkoutClosed':True,'realPayments':False,**{k:True for k in ['reviewedGallery','galleryCommercialFieldsUnchanged','galleryAllAssociationsChecked','galleryPrivateNoStore','galleryOwnershipChecked']},'galleryRegistrySha256':self.checksum('native-store/storefront/product-gallery-data.json'),'galleryOriginalSamples':2,'galleryProductsExtended':3,'galleryApprovedAssets':4})
  self.write('.local/native-returns-public-'+scope+'.json',self.rows(scope,['guestLookupProtected','noOrderDataLeaked','trAndEn','rtlLanguageChoice','noStoreNoindex'],script='test-native-returns-public.py'))
  self.write('.local/native-returns-local.json',self.rows('local',['partialReturn','serverQuote','idempotency','cancelAndHistory','csrfAndOrigin','sessionAndOrderOwnership','warehouseFinancialBoundary','adminMfa','quarantineNoRestock','fiscalConfirmationSeparate','testExcludedFromLiveReport','trAndEn','rtlLanguageChoice','firstHtmlAndNoindex'],{'realPaymentsCalled':False,'fiscalApiCalled':False,'localPaidFixturesOnly':True},'test-native-returns-browser.py'))
  self.write('.local/returns-unit-source-final.json',{'passed':53,'realPaymentOrFiscalApiCalled':False,'testSha256':self.checksum('scripts/test-native-returns-php.php')})
  self.write('docs/native-marketplace-discovery-'+scope+'-results.json',{'base':BASES[scope],'results':self.rows(scope,DISCOVERY_KEYS,{'publicProducts':803,'occupiedRoots':6,'realPayments':False,'adminAccessed':False},'test-native-marketplace-discovery.py')})
  def isolated_execution(name,count):return {'exitCode':0,'passed':count,'checks':['fixture_check_'+str(n)for n in range(count)],'scriptSha256':self.checksum('scripts/'+name),'testSha256':self.checksum('scripts/'+name),'isolatedDatabase':True,'realPaymentOrFiscalApiCalled':False}
  source={'schema':1,'profile':'marketplace-source-v1','scope':scope,'targetBase':BASES[scope],'release':RELEASE,'dataset':DATASET,'sourceDetails':1002,'loadedNew':958,'runnerSha256':self.checksum('scripts/test-native-marketplace-source-proof.py'),'fingerprint':self.fingerprint,'allMarketplaceProductsTransferred':False,'publishedToRemote':False,'realPaymentOrFiscalApiCalled':False,'executionEnvironment':'local-isolated-cli','executions':{'data':{'exitCode':0,'passed':6,'scriptSha256':self.checksum('scripts/test-native-marketplace-data.py')},'payload':{'exitCode':0,'passed':2884,'newProducts':958,'publishCandidates':803,'isolatedDatabase':True,'publishedToRemote':False,'scriptSha256':self.checksum('scripts/test-native-marketplace-payload.php')},'returnsCore':isolated_execution('test-native-returns-php.php',53),'returnsCoreSource':isolated_execution('test-native-returns-php.php',53),'returnOrdering':isolated_execution('test-native-return-ordering.php',17),'returnOrderingSource':isolated_execution('test-native-return-ordering.php',17)}}
  source['executions']['installer']={'exitCode':0,'scriptSha256':self.checksum('scripts/test-native-installer.php'),'passed':30,'checks':['fixture_installer_check_'+str(n)for n in range(30)],'release':RELEASE,'products':3152,'archiveFiles':2500,'pureValidationOnly':True,'networkCalled':False,'installed':False}
  source['executions']['seo']={'exitCode':0,'scriptSha256':self.checksum('scripts/test-native-marketplace-seo.php'),'testSha256':self.checksum('scripts/test-native-marketplace-seo.php'),'passed':8833,'pages':8833,'publicProducts':803,'locales':11,'release':RELEASE,'dataset':DATASET,'warningsAsErrors':True,'networkCalled':False,'realPayments':False}
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
    result=self.accept(scope);self.assertFalse(result['allTransferred']);self.assertEqual(result['sourceDetails'],1002);self.assertEqual(result['loadedNew'],958);self.assertEqual(result['visibleNew'],803);self.assertEqual(result['groups'],16 if scope=='local'else 15);self.assertTrue(result['productExperienceProof']);self.assertTrue(result['productModuleProof']);self.assertTrue(result['productRuntimeMemoryProof'])

 def test_module_and_memory_proofs_are_required_and_fresh_in_both_profiles(self):
  for name in ['.local/native-product-module-results.json','.local/native-product-runtime-memory.json']:
   original=self.read(name)
   for scope in BASES:
    with self.subTest(name=name,scope=scope):
     path=self.root/name;path.unlink();self.assert_rejected(scope);self.write(name,original);os.utime(path,(self.minimum-1,self.minimum-1));self.assert_rejected(scope);self.write(name,original)

 def test_module_proof_context_and_flags_are_strict(self):
  name='.local/native-product-module-results.json';original=self.read(name)
  failures=[('schema',True),('schema',0),('profile','old'),('passed',1),('release','9'*24),('dataset','9'*32),('runnerSha256','0'*64),('sourceSha256','0'*64),('fingerprint',{}),('executionEnvironment','remote'),('fullPackageVerifiedBeforeAndAfter',False),('fullPackageVerificationPasses',1),('fullPackageVerificationPasses',2.0),('publishedToRemote',True),('realProviderCalled',True)]
  for key,value in failures:
   with self.subTest(key=key,value=value):self.write(name,{**original,key:value});self.assert_rejected()

 def test_module_proof_requires_exactly_ten_successful_current_executions(self):
  name='.local/native-product-module-results.json';original=self.read(name)
  for execution in MODULE_TESTS:
   for key,value in [('exitCode',1),('exitCode',False),('passed',0),('passed',True),('passed',1.0),('scriptSha256','0'*64),('missing',None)]:
    with self.subTest(execution=execution,key=key):
     data=json.loads(json.dumps(original))
     if key=='missing':del data['executions'][execution]
     else:data['executions'][execution][key]=value
     self.write(name,data);self.assert_rejected()
  data=json.loads(json.dumps(original));data['executions']['unexpected']={};self.write(name,data);self.assert_rejected()

 def test_module_fingerprint_or_current_runner_change_invalidates_proof(self):
  self.module_fingerprint_mock.return_value={**self.module_fingerprint,'sourceSha256':'0'*64};self.assert_rejected();self.module_fingerprint_mock.return_value=self.module_fingerprint
  self.bytes('scripts/test-native-product-modules.py',b'changed runner');self.assert_rejected()

 def test_product_module_fingerprint_imports_current_helper_without_main(self):
  self.bytes('scripts/test-native-product-modules.py',b"def fingerprint(full=True):\n return {'full':full,'root':str(ROOT),'metadata':str(METADATA),'selection':str(SELECTION),'source':str(SOURCE)}\nif __name__=='__main__':\n raise RuntimeError('MAIN_MUST_NOT_RUN')\n")
  result=self.module_fingerprint_function(self.root)
  self.assertIs(result['full'],False);self.assertEqual(result['root'],str(self.root));self.assertEqual(result['metadata'],str(self.root/'.local/native-stage-package.json'));self.assertEqual(result['selection'],str(self.root/'.local/native-marketplace-selection.json'));self.assertEqual(result['source'],str(self.root/'native-store/storefront'))

 def test_memory_proof_context_and_flags_are_strict(self):
  name='.local/native-product-runtime-memory.json';original=self.read(name)
  failures=[('schema',True),('passed',False),('executionEnvironment','local-php'),('actualExecutions',3),('actualExecutions',4.0),('packageUnchanged',1),('realProviderCalled',True),('release','9'*24),('dataset','9'*32),('scriptSha256','0'*64),('packageArchiveSha256','0'*64),('moduleHashes',{})]
  for key,value in failures:
   with self.subTest(key=key,value=value):self.write(name,{**original,key:value});self.assert_rejected()

 def test_memory_requires_all_four_real_cases_with_exact_limit_and_no_fatal(self):
  name='.local/native-product-runtime-memory.json';original=self.read(name)
  for case in original['cases']:
   for key,value in [('exitCode',1),('exitCode',False),('ok',1),('case','other'),('release','9'*24),('memoryLimit','256M'),('peakBytes',0),('peakBytes',True),('peakBytes',134217729),('peakBytes',122.5),('fatal',True),('fatal',None),('realProviderCalled',True),('missing',None)]:
    with self.subTest(case=case,key=key):
     data=json.loads(json.dumps(original))
     if key=='missing':del data['cases'][case]
     else:data['cases'][case][key]=value
     self.write(name,data);self.assert_rejected()
  data=json.loads(json.dumps(original));data['cases']['unexpected']={};self.write(name,data);self.assert_rejected()

 def test_memory_case_product_counts_and_worker_health_are_required(self):
  name='.local/native-product-runtime-memory.json';original=self.read(name)
  counts={'customer':{'sourceProducts':958,'publicProducts':803,'stories':803},'adminSchema':{'sourceProducts':3152,'publicProducts':803,'schemaProducts':3152,'schemaVisibleProducts':803},'adminProducts':{'sourceProducts':958,'publicProducts':803,'rows':958,'publishedRows':803,'reviewRows':155},'worker':{'notificationsSent':0}}
  for case,fields in counts.items():
   for key,value in fields.items():
    for invalid in [value+1,float(value),True]:
     with self.subTest(case=case,key=key,value=invalid):
      data=json.loads(json.dumps(original));data['cases'][case][key]=invalid;self.write(name,data);self.assert_rejected()
  for case,key in [('worker','healthOk'),('adminSchema','unusedCatalogReleased'),('adminProducts','unusedCatalogReleased')]:
   for invalid in [False,1,None]:
    with self.subTest(case=case,key=key):
     data=json.loads(json.dumps(original));data['cases'][case][key]=invalid;self.write(name,data);self.assert_rejected()

 def test_memory_hashes_bind_to_actual_archive_manifest_and_modules(self):
  name='.local/native-product-runtime-memory.json';original=self.read(name)
  for module in MEMORY_MODULES:
   with self.subTest(module=module):
    data=json.loads(json.dumps(original));data['moduleHashes'][module]='0'*64;self.write(name,data);self.assert_rejected()
  self.write(name,original);self.bytes('package.zip',b'changed archive');self.assert_rejected()

 def test_changed_memory_script_or_packaged_module_invalidates_proof(self):
  self.bytes('scripts/test-native-product-runtime-memory.py',b'changed memory helper');self.assert_rejected()
  self.bytes('scripts/test-native-product-runtime-memory.py',b'temporary fixture test-native-product-runtime-memory.py');self.bytes('bundle/private/control-http.php',b'changed package module');self.assert_rejected()

 def test_gallery_proof_rejects_missing_flags_and_originals(self):
  name='.local/native-marketplace-http-local.json';original=self.read(name)
  for key,value in [(key,False)for key in ['reviewedGallery','galleryCommercialFieldsUnchanged','galleryAllAssociationsChecked','galleryPrivateNoStore','galleryOwnershipChecked']]+[('galleryRegistrySha256','f'*64),('galleryOriginalSamples',0),('galleryApprovedAssets',0),('galleryProductsExtended',804)]:
   with self.subTest(key=key):
    altered={**original,key:value};self.write(name,altered);self.assert_rejected();self.write(name,original)

 def test_gallery_registry_change_requires_new_http_proof(self):
  self.write('native-store/storefront/product-gallery-data.json',{'changed':True});self.assert_rejected()

 def test_existing_import_and_browser_proof_cannot_replace_discovery(self):
  (self.root/'docs/native-marketplace-discovery-local-results.json').unlink();self.assert_rejected()

 def test_product_experience_required_in_both_profiles_and_current_time(self):
  for scope in BASES:
   with self.subTest(scope=scope):
    name='.local/native-product-experience-'+scope+'.json';original=self.read(name);path=self.root/name
    path.unlink();self.assert_rejected(scope);self.write(name,original)
    os.utime(path,(self.minimum-1,self.minimum-1));self.assert_rejected(scope);self.write(name,original)

 def test_product_experience_requires_exactly_two_distinct_engines(self):
  name='.local/native-product-experience-local.json';original=self.read(name)
  for rows in [[],original[:1],[original[0],original[0]],original+[original[0]],[{**original[0],'engine':'firefox'},original[1]]]:
   with self.subTest(engines=[row.get('engine')for row in rows]):
    self.write(name,rows);self.assert_rejected()

 def test_product_experience_every_behavior_must_be_boolean_true(self):
  self.assertEqual(len(gate.PRODUCT_EXPERIENCE_KEYS),21)
  name='.local/native-product-experience-local.json';original=self.read(name)
  for key in gate.PRODUCT_EXPERIENCE_KEYS:
   for value in [False,None,1,'true']:
    with self.subTest(behavior=key,value=value):
     self.write(name,original);self.mutate_row(name,key,value);self.assert_rejected()
   data=json.loads(json.dumps(original));del data[1][key];self.write(name,data);self.assert_rejected()

 def test_product_experience_rejects_wrong_context_coverage_or_fixture_claims(self):
  name='.local/native-product-experience-local.json';original=self.read(name)
  fields=[('base',BASES['preview']),('release','9'*24),('scope','preview'),('dataset','9'*32),('scriptSha256','0'*64),('visibleNew',802),('visibleNew',True),('visibleNew',803.0),('pageErrors',1),('pageErrors',False),('pageErrors',None),('widths',[390,430,768,1440]),('widths',[360.0,390,430,768,1440]),('widths',[1440,768,430,390,360]),('samples',4),('samples',5.0),('galleryImageCount',1),('galleryImageCount',True),('feedbackReviewedVersion',1),('feedbackReviewedVersion',2.0),('feedbackReference','SGF-123456-NOT-REAL'),('feedbackReference',None),('qaFeedbackClearlyLabelled',False)]+[(key,value)for key in ['realPayments','ordersCreated','realRefunds','sourceSnapshotChanged']for value in [True,None,0]]
  for field,value in fields:
   with self.subTest(field=field,value=value):
    self.write(name,original);self.mutate_row(name,field,value);self.assert_rejected()

 def test_product_experience_script_change_invalidates_completed_proof(self):
  self.bytes('scripts/test-native-product-experience-browser.py',b'changed isolated product browser test');self.assert_rejected()

 def test_customer_copy_requires_fresh_complete_source_bound_http_proof(self):
  name='.local/native-marketplace-copy-local.json';original=self.read(name);path=self.root/name;path.unlink();self.assert_rejected();self.write(name,original)
  os.utime(path,(self.minimum-1,self.minimum-1));self.assert_rejected();self.write(name,original)
  for field,value in [('base',BASES['preview']),('release','9'*24),('dataset','9'*32),('visible',81),('visible',True),('schema',0),('schema',True),('scriptSha256','0'*64),('helperSha256','0'*64),('remainingCTAs',1),('remainingCTAs',False),('realPayments',True)]+[(key,False)for key in ['protectedFieldsNoChange','sourcePreserved','idempotent','verifiedAfterReload','expectedSetMatch','actualRequests']]:
   with self.subTest(field=field):
    self.write(name,{**original,field:value});self.assert_rejected()

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

 def test_installer_requires_package_context_complete_checks_and_no_install(self):
  name='docs/native-marketplace-source-local-results.json';original=self.read(name)
  fields=[('passed',29),('release','9'*24),('products',2324),('archiveFiles',2000),('archiveFiles',5001),('archiveFiles',2500.0),('checks',[]),('pureValidationOnly',False),('networkCalled',True),('installed',True)]
  for field,value in fields:
   with self.subTest(field=field,value=value):
    data=json.loads(json.dumps(original));data['executions']['installer'][field]=value;self.write(name,data);self.assert_rejected()

 def test_seo_requires_every_public_product_locale_context_and_safe_execution(self):
  name='docs/native-marketplace-source-local-results.json';original=self.read(name)
  fields=[('passed',901),('pages',901),('publicProducts',81),('locales',10),('release','9'*24),('dataset','9'*32),('testSha256','0'*64),('warningsAsErrors',False),('networkCalled',True),('realPayments',True)]
  for field,value in fields:
   with self.subTest(field=field):
    data=json.loads(json.dumps(original));data['executions']['seo'][field]=value;self.write(name,data);self.assert_rejected()

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
