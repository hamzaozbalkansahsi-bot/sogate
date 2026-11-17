# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_marketplace_acceptance.py
# Açıklama   : Katalog değişiminde eski ürünlere bağlı kabuller yerine yeni gerçek kaynak ve iade kanıtlarını zorunlu tutar.
import hashlib,json,sqlite3
from contextlib import closing
from pathlib import Path

DISCOVERY_KEYS=('productFirstLayout','compactHeader','compactCampaignCards','balancedSelection','alignedCards','realCategoryTabs','tabsPreserveScrollAndFocus','tabDeepLink','keyboardRail','variantSelectionRequired','blogRoute','serverClientParity','mountedServerLinks','categoryImages','hierarchy','backRestoresSelection','sizeFilter','brandFilter','colorFilter','validCombinedFacets','sortPreservesFilters','invalidPriceRejected','keyboardDrawer','facetNoindex','facetCanonical','search','rtl','singleStore','serverCategoryLayout')
SOURCE_TESTS={'data':'scripts/test-native-marketplace-data.py','payload':'scripts/test-native-marketplace-payload.php','installer':'scripts/test-native-installer.php','seo':'scripts/test-native-marketplace-seo.php','returnsCore':'scripts/test-native-returns-php.php','returnsCoreSource':'scripts/test-native-returns-php.php','returnOrdering':'scripts/test-native-return-ordering.php','returnOrderingSource':'scripts/test-native-return-ordering.php'}

def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def files_sha(paths,base):
 digest=hashlib.sha256()
 for path in sorted(set(Path(p)for p in paths)):
  digest.update(path.relative_to(base).as_posix().encode('utf8')+b'\0'+file_sha(path).encode('ascii')+b'\0')
 return digest.hexdigest()

def marketplace_source_fingerprint(root):
 """Kaynak denetiminin gerçekten okuduğu veri ve paket baytlarını bağlar; sır dosyası okumaz."""
 root=Path(root);package_path=root/'.local/native-stage-package.json';selection_path=root/'.local/native-marketplace-selection.json'
 package=json.loads(package_path.read_text('utf-8-sig'));selection=json.loads(selection_path.read_text('utf-8-sig'))
 prepared=Path(selection['path']);bundle=Path(package['bundle']);private=bundle/'private'
 data_path=prepared/'catalog-data.json';data=json.loads(data_path.read_text('utf-8-sig'));catalog_path=private/'catalog.json';catalog=json.loads(catalog_path.read_text('utf-8-sig'))
 manifest_path=bundle/'deployment-manifest.json';manifest=json.loads(manifest_path.read_text('utf-8-sig'))
 if package.get('release')!=manifest.get('release')or package.get('dataset')!=selection.get('dataset')or data.get('dataset')!=selection.get('dataset')or catalog.get('dataset')!=selection.get('dataset')or catalog.get('catalogOrigin')!='sexogate-catalog-v2'or catalog.get('products')!=data.get('products')or file_sha(data_path)!=selection.get('sha256')or len(data['products'])!=2194+selection['newProducts']:raise ValueError('MARKETPLACE_SOURCE_INPUT_MISMATCH')
 source_home=prepared.parent;legacy=source_home.parent/'native-catalog-20261115/prepared/catalog-data.json'
 work_paths=list((prepared/'catalog-workbench').glob('*.json'));work={key:value for path in work_paths for key,value in json.loads(path.read_text('utf-8-sig')).items()}
 media=[]
 for product in data['products'][2194:]:
  for item in work[product['id']]['media']:
   path=(source_home/'media'/item['file']).resolve()
   if not path.is_relative_to((source_home/'media').resolve()):raise ValueError('MARKETPLACE_SOURCE_MEDIA_SCOPE')
   media.append(path)
 database=source_home/'research.sqlite'
 with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True))as db:
  db.execute('PRAGMA query_only=ON');source_rows=sorted(row[0]for row in db.execute("SELECT detail_json FROM products WHERE status='ready'"))
 if len(source_rows)!=selection['sourceProducts']:raise ValueError('MARKETPLACE_SOURCE_INPUT_MISMATCH')
 source_returns={}
 for source,target in [('core.php','sg-returns-core.php'),('jobs.php','sg-returns-jobs.php'),('sg-returns-001.sql','sg-returns-001.sql')]:
  source_hash=file_sha(root/'native-store/returns'/source);packaged_hash=file_sha(private/target)
  if source_hash!=packaged_hash:raise ValueError('MARKETPLACE_RETURN_SOURCE_PACKAGE_MISMATCH')
  source_returns[source]=source_hash
 return {'release':package['release'],'dataset':selection['dataset'],'sourceDetails':selection['sourceProducts'],'loadedNew':selection['newProducts'],'packageMetadataSha256':file_sha(package_path),'packageManifestSha256':file_sha(manifest_path),'packageArchiveSha256':package['sha256'],'selectionSha256':file_sha(selection_path),'catalogDataSha256':file_sha(data_path),'bundleCatalogSha256':file_sha(catalog_path),'legacyCatalogSha256':file_sha(legacy),'catalogSourcesSha256':file_sha(prepared/'catalog-sources.json'),'bundleCatalogSourcesSha256':file_sha(private/'catalog-sources.json'),'coverReviewSha256':file_sha(source_home/'cover-review.json'),'workbenchSha256':files_sha(work_paths,prepared),'reviewedMediaSha256':files_sha(media,(source_home/'media').resolve()),'sourceReadyRowsSha256':hashlib.sha256(json.dumps(source_rows,ensure_ascii=False,separators=(',',':')).encode('utf8')).hexdigest(),'sourceTestSha256':{name:file_sha(root/path)for name,path in SOURCE_TESTS.items()},'returnSourcesSha256':source_returns,'installerSha256':file_sha(root/'native-store/deploy/install.php'),'runnerSha256':file_sha(root/'scripts/test-native-marketplace-source-proof.py'),'acceptanceHelperSha256':file_sha(root/'scripts/native_marketplace_acceptance.py')}

def validate_marketplace_source_proof(root,proof,suffix,release,base,selection,visible_new):
 expected=marketplace_source_fingerprint(root)
 if proof.get('schema')!=1 or proof.get('profile')!='marketplace-source-v1'or proof.get('scope')!=suffix or proof.get('targetBase')!=base or proof.get('release')!=release or proof.get('dataset')!=selection['dataset']or proof.get('sourceDetails')!=selection['sourceProducts']or proof.get('loadedNew')!=selection['newProducts']or proof.get('runnerSha256')!=file_sha(root/'scripts/test-native-marketplace-source-proof.py')or proof.get('fingerprint')!=expected or expected.get('release')!=release or expected.get('dataset')!=selection['dataset']or proof.get('executionEnvironment')!='local-isolated-cli'or any(proof.get(key)is not False for key in ['allMarketplaceProductsTransferred','publishedToRemote','realPaymentOrFiscalApiCalled']):raise ValueError('MARKETPLACE_SOURCE_EXECUTION_REQUIRED')
 executions=proof.get('executions',{})
 if set(executions)!=set(SOURCE_TESTS)or any(not isinstance(result,dict)or result.get('exitCode')!=0 or result.get('scriptSha256')!=file_sha(root/SOURCE_TESTS[name])for name,result in executions.items()):raise ValueError('MARKETPLACE_SOURCE_EXECUTION_REQUIRED')
 data=executions['data'];payload=executions['payload']
 if data.get('passed')!=6 or payload.get('passed')!=3*selection['newProducts']+10 or payload.get('newProducts')!=selection['newProducts']or payload.get('publishCandidates')!=visible_new or payload.get('isolatedDatabase')is not True or payload.get('publishedToRemote')is not False:raise ValueError('MARKETPLACE_SOURCE_EXECUTION_REQUIRED')
 installer=executions['installer']
 if installer.get('release')!=release or installer.get('products')!=selection['products']or not isinstance(installer.get('passed'),int)or installer['passed']<30 or len(installer.get('checks',[]))!=installer['passed']or not isinstance(installer.get('archiveFiles'),int)or not 2000<installer['archiveFiles']<=5000 or installer.get('pureValidationOnly')is not True or installer.get('networkCalled')is not False or installer.get('installed')is not False:raise ValueError('MARKETPLACE_SOURCE_EXECUTION_REQUIRED')
 seo=executions['seo']
 if seo.get('release')!=release or seo.get('dataset')!=selection['dataset']or seo.get('publicProducts')!=visible_new or seo.get('pages')!=11*visible_new or seo.get('locales')!=11 or not isinstance(seo.get('passed'),int)or seo['passed']<seo['pages']or seo.get('testSha256')!=file_sha(root/SOURCE_TESTS['seo'])or seo.get('warningsAsErrors')is not True or seo.get('networkCalled')is not False or seo.get('realPayments')is not False:raise ValueError('MARKETPLACE_SOURCE_EXECUTION_REQUIRED')
 for name,required in [('returnsCore',53),('returnsCoreSource',53),('returnOrdering',17),('returnOrderingSource',17)]:
  result=executions[name]
  if result.get('passed')!=required or len(result.get('checks',[]))!=required or result.get('testSha256')!=file_sha(root/SOURCE_TESTS[name])or result.get('isolatedDatabase')is not True or result.get('realPaymentOrFiscalApiCalled')is not False:raise ValueError('MARKETPLACE_SOURCE_EXECUTION_REQUIRED')

def marketplace_package(root,package):
 catalog=json.loads((Path(package['bundle'])/'private/catalog.json').read_text('utf8'))
 return catalog.get('catalogOrigin')=='sexogate-catalog-v2'

def marketplace_acceptance(root,suffix,release,base,minimum_time):
 def read(name):
  p=root/name
  if not p.is_file()or p.stat().st_mtime<minimum_time:raise ValueError('MARKETPLACE_PROOF_MISSING_OR_STALE')
  return json.loads(p.read_text('utf-8-sig'))
 def rows(name,keys=(),script=None):
  data=read(name);data=data['results']if isinstance(data,dict)and'results'in data else data
  if not isinstance(data,list)or len(data)!=2 or {r.get('engine')for r in data}!={'chromium','webkit'}:raise ValueError('MARKETPLACE_TWO_ENGINE_PROOF_REQUIRED')
  checksum=hashlib.sha256((root/script).read_bytes()).hexdigest()if script else None
  if any(r.get('base')!=base or r.get('release')!=release or r.get('pageErrors',0)or not all(r.get(k)is True for k in keys)or(checksum and r.get('scriptSha256')!=checksum)for r in data):raise ValueError('MARKETPLACE_PROOF_FAILED')
  return data
 root=Path(root);selection=json.loads((root/'.local/native-marketplace-selection.json').read_text('utf-8-sig'));imported=read('.local/native-marketplace-import-'+suffix+'.json')
 if imported.get('base')!=base or imported.get('release')!=release or imported.get('dataset')!=selection['dataset']or imported.get('loadedNew')!=selection['newProducts']or not imported.get('idempotent')or imported.get('oldSupplierProductsVisible')is not False or imported.get('genericBrandsNotInvented')is not True:raise ValueError('MARKETPLACE_IMPORT_ACCEPTANCE_REQUIRED')
 copy_proof=read('.local/native-marketplace-copy-'+suffix+'.json')
 if type(copy_proof.get('schema'))is not int or copy_proof['schema']!=1 or copy_proof.get('base')!=base or copy_proof.get('release')!=release or copy_proof.get('dataset')!=selection['dataset']or type(copy_proof.get('visible'))is not int or copy_proof['visible']!=imported['visibleNew']or copy_proof.get('scriptSha256')!=file_sha(root/'scripts/clean-native-marketplace-copy.py')or copy_proof.get('helperSha256')!=file_sha(root/'scripts/native_marketplace_copy.py')or type(copy_proof.get('remainingCTAs'))is not int or copy_proof['remainingCTAs']!=0 or copy_proof.get('realPayments')is not False or any(copy_proof.get(key)is not True for key in ['protectedFieldsNoChange','sourcePreserved','idempotent','verifiedAfterReload','expectedSetMatch','actualRequests']):raise ValueError('MARKETPLACE_CUSTOMER_COPY_REQUIRED')
 validate_marketplace_source_proof(root,read('docs/native-marketplace-source-'+suffix+'-results.json'),suffix,release,base,selection,imported['visibleNew'])
 discovery=rows('docs/native-marketplace-discovery-'+suffix+'-results.json',DISCOVERY_KEYS,'scripts/test-native-marketplace-discovery.py')
 if any(r.get('publicProducts')!=imported['visibleNew']or r.get('occupiedRoots',0)<1 or r.get('pageErrors')!=0 or r.get('realPayments')is not False or r.get('adminAccessed')is not False for r in discovery):raise ValueError('MARKETPLACE_DISCOVERY_REQUIRED')
 nav=rows('.local/native-browser-marketplace-mount-'+suffix+'.json')
 if any(r.get('adminRoutes',0)<33 or r.get('publicRoutes',0)<9 or r.get('externalRequests')or not r.get('mfa')for r in nav):raise ValueError('MARKETPLACE_NAVIGATION_ACCEPTANCE_REQUIRED')
 language=read('.local/native-languages-marketplace-mount-'+suffix+'.json')
 if language.get('base')!=base or language.get('release')!=release or not language.get('finalized')or language.get('pageErrors')or language.get('scriptSha256')!=hashlib.sha256((root/'scripts/test-native-languages.py').read_bytes()).hexdigest()or len(language.get('locales',[]))!=11 or len(language.get('clientSwitches',[]))!=3 or any(not all(v.get(k)for k in ['selected','clientMetadata','catalogUiReady'])for v in language['clientSwitches'])or any(v.get('status')!=200 or not all(v.get(k)for k in ['selected','adultMetadata','clientAdultMetadata','catalogUiReady'])for v in language['locales']):raise ValueError('MARKETPLACE_LANGUAGES_REQUIRED')
 age=rows('.local/native-adult-marketplace-adult-'+suffix+'.json',['ageGate','guestBrowsing','keyboardFocus','escapeBypassBlocked'])
 if any(r.get('worldMap')is not False or r.get('furnitureCopy')is not False or r.get('iconOnlySocialLinks')!=4 for r in age):raise ValueError('MARKETPLACE_BRAND_ACCEPTANCE_REQUIRED')
 polish=rows('.local/native-marketplace-polish-'+suffix+'.json',['realImagesLoaded','alignedCards','footerPrivacyEntry','readableFeatures','horizontalRelatedRail','horizontalRecentRail','consentRevocation','accountHelperMountedOnce','productImageBounds'])
 if any(r.get('furnitureCopy')is not False or r.get('stickyOverlap')is not False or r.get('underlinedLinks')is not False or r.get('compactImageCampaignCards')!=4 or r.get('curtainDurationSeconds',0)<4.8 for r in polish):raise ValueError('MARKETPLACE_LAYOUT_REQUIRED')
 paint=rows('.local/native-marketplace-paint-'+suffix+'.json',['javascriptDisabled','realImages'])
 if any(r.get('serverHtmlCompactCards')!=4 or r.get('serverLocales')!=11 or r.get('legacyHero')is not False for r in paint):raise ValueError('MARKETPLACE_FIRST_PAINT_REQUIRED')
 variant=rows('docs/native-marketplace-variants-'+suffix+'-results.json',['selectionRequired','sizeColorCartLines','editMergeReload','legacyCartRepair','sourceMatrix','bulkAllItems','bulkCancellation','rtl'])
 variant_hash=hashlib.sha256((root/'scripts/test-native-marketplace-variants.py').read_bytes()+(root/'scripts/native_variant_cases.py').read_bytes()).hexdigest()
 if any(r.get('scriptSha256')!=variant_hash or r.get('realPayment')is not False or r.get('consentNormalHoverFocus')!='brand-burgundy/wine'or len(r.get('isolatedCases',[]))!=7 for r in variant):raise ValueError('MARKETPLACE_VARIANTS_REQUIRED')
 actions=rows('.local/native-marketplace-actions-'+suffix+'.json',['primarySingleLine','touchTargets','quantityButtons','favoriteAndCompare','variantRequired','shareDialog','rtl'])
 if any(r.get('cssPreview')for r in actions):raise ValueError('MARKETPLACE_UNBUILT_CSS_NOT_ACCEPTED')
 basket=rows('.local/native-marketplace-cart-notifications-'+suffix+'.json',['cartSelectionTotals','quantityUpdates','variantLabels','moveToFavoritesAndRemove','summaryDialog','permissionNotRequestedAutomatically'])
 if any(r.get('stickyOverlap')is not False or r.get('notificationApi',{}).get('externalPushSent')is not False for r in basket):raise ValueError('MARKETPLACE_CART_NOTIFICATION_REQUIRED')
 catalog=rows('docs/native-marketplace-'+suffix+'-results.json',['sourceCodesKept','finalMarkup15','noFakeInventory','noLegacyProducts','realImageHashes','draftMediaPrivate','categorySizeFilter','priceSort','facetNoindex','singleStore','adminMfa','adminFieldsAndSeo','adminGoToProductAfterReload','checkoutClosed'],'scripts/test-native-marketplace-browser.py')
 if any(r.get('dataset')!=selection['dataset']or r.get('loadedNew')!=selection['newProducts']or r.get('visibleNew')!=imported['visibleNew']or r.get('allMarketplaceProductsTransferred')is not False for r in catalog):raise ValueError('MARKETPLACE_SOURCE_SET_REQUIRED')
 http=read('.local/native-marketplace-http-'+suffix+'.json')
 if http.get('base')!=base or http.get('release')!=release or http.get('scriptSha256')!=hashlib.sha256((root/'scripts/test-native-marketplace-http.py').read_bytes()).hexdigest()or not all(http.get(k)is True for k in ['privatePathsBlocked','guestOrderOwnership','returnCsrfAndOrigin','returnsNoStoreNoindex','adminProtected','checkoutClosed'])or http.get('realPayments')is not False:raise ValueError('MARKETPLACE_HTTP_SECURITY_REQUIRED')
 rows('.local/native-returns-public-'+suffix+'.json',['guestLookupProtected','noOrderDataLeaked','trAndEn','rtlLanguageChoice','noStoreNoindex'],'scripts/test-native-returns-public.py')
 if suffix=='local':
  returns=rows('.local/native-returns-local.json',['partialReturn','serverQuote','idempotency','cancelAndHistory','csrfAndOrigin','sessionAndOrderOwnership','warehouseFinancialBoundary','adminMfa','quarantineNoRestock','fiscalConfirmationSeparate','testExcludedFromLiveReport','trAndEn','rtlLanguageChoice','firstHtmlAndNoindex'],'scripts/test-native-returns-browser.py')
  if any(r.get('realPaymentsCalled')is not False or r.get('fiscalApiCalled')is not False or not r.get('localPaidFixturesOnly')for r in returns):raise ValueError('RETURN_ISOLATED_ACCEPTANCE_REQUIRED')
 return {'profile':'marketplace-returns-v1','groups':15 if suffix=='local'else 14,'sourceDetails':selection['sourceProducts'],'loadedNew':selection['newProducts'],'visibleNew':imported['visibleNew'],'independentSourceProof':True,'discoveryProof':True,'customerCopyProof':True,'allTransferred':False}
