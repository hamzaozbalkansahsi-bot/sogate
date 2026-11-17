/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/product-feedback-apply.mjs
 * Açıklama   : Geri bildirim API, yönetim ve kalıcı temizlik işini yalnız yayın kopyasına bağlar.
 */
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const source=path.dirname(fileURLToPath(import.meta.url)),bundle=path.resolve(process.argv[2]||'');
if(!bundle.includes('native-stage-')||!fs.statSync(path.join(bundle,'private')).isDirectory())throw Error('PRODUCT_FEEDBACK_APPLY_SCOPE');
execFileSync(process.execPath,[path.join(source,'product-feedback-build.mjs'),bundle],{stdio:'inherit'});
function edit(name,from,to){const file=path.join(bundle,name),text=fs.readFileSync(file,'utf8');if(text.split(from).length!==2)throw Error('PRODUCT_FEEDBACK_HOOK_CHANGED:'+name);fs.writeFileSync(file,text.replace(from,to));}
edit('private/control-http.php',"require_once __DIR__.'/sg-returns-http.php';","require_once __DIR__.'/sg-returns-http.php';\nrequire_once __DIR__.'/sg-product-feedback.php';");
edit('private/control-http.php','if($result===null)$result=sgReturnAdmin($ctx,$route,$method,$body);','if($result===null)$result=sgProductFeedbackAdmin($ctx,$route,$method,$body);if($result===null)$result=sgReturnAdmin($ctx,$route,$method,$body);');
edit('deploy/dispatcher.php',"if($relative==='/api/notifications')",`if($relative==='/api/product-feedback'){require_once $private.'/sg-product-feedback.php';sgProductFeedbackHandle($private,$_SERVER['REQUEST_METHOD']);exit;}
if($relative==='/yonetim/urun-geri-bildirimleri'&&in_array($_SERVER['REQUEST_METHOD'],['GET','HEAD'],true)){require_once $private.'/sg-product-feedback.php';sgProductFeedbackAdminPage($mount,$assetRevision);}
if($relative==='/api/notifications')`);
edit('deploy/worker.php',"$health=['returns'=>$returns", "require_once $release.'/private/sg-product-feedback.php';$feedbackDb=nodenoControlDatabase($home.'/state');sgProductFeedbackSchema($feedbackDb);$feedbackCleanup=sgProductFeedbackCleanup($feedbackDb,time());$health=['productFeedback'=>$feedbackCleanup,'returns'=>$returns");
for(const name of ['public/index.html','private/index.html','public/admin.html'])if(fs.existsSync(path.join(bundle,name)))edit(name,'</head>','<link rel="stylesheet" href="/sg-product-feedback.css?v=storefront"><script type="module" src="/sg-product-feedback.js?v=storefront"></script></head>');
console.log(JSON.stringify({productFeedbackPublicApi:true,adminMfa:true,scheduledRetention:true,sourceSnapshotChanged:false}));
