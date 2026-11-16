<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/returns/pages.php
 * Açıklama   : İade merkezinin ilk HTML’sini ve veri içermeyen yönetim kabuğunu oluşturur.
 */
declare(strict_types=1);
function sgReturnPage(array $config,array $query):array{
 $locale=is_string($query['lang']??null)&&in_array($query['lang'],NODENO_SEO_LOCALES,true)?$query['lang']:'tr';$all=json_decode((string)file_get_contents(__DIR__.'/sg-returns-copy.json'),true,64,JSON_THROW_ON_ERROR);$copy=$all[$locale]??null;$e='nodenoSeoEscape';
 $gate=['tr'=>'İade dilini seç','en'=>'Choose your return language','ru'=>'Выберите язык возврата','ar'=>'اختر لغة الإرجاع','de'=>'Sprache für die Rückgabe wählen','az'=>'Qaytarma dilini seçin','kk'=>'Қайтару тілін таңдаңыз','tk'=>'Yzyna gaýtarmagyň dilini saýlaň','uz'=>'Qaytarish tilini tanlang','ky'=>'Кайтаруу тилин тандаңыз','fa'=>'زبان مرجوعی را انتخاب کنید'];
 if($copy){$title=$copy['title'];$description=$copy['intro'];$body='<section class="wrap sg-returns" lang="'.$locale.'"><header><p class="sg-return-brand">SEXOGATE</p><h1 tabindex="-1">'.$e($title).'</h1><p>'.$e($description).'</p></header><div data-return-content role="region" aria-label="'.$e($title).'"><p role="status">'.$e($copy['loading']).'</p></div><noscript><a href="mailto:info@sexogate.com">'.$e($copy['email']).'</a></noscript></section>';}
 else{$title=$gate[$locale];$description=$title;$body='<section class="wrap sg-returns sg-return-language"><h1 tabindex="-1">'.$e($title).'</h1><a class="button" href="'. $e(nodenoSeoLink('return-center','tr')).'" data-nav>Türkçe</a><a class="button secondary" href="'.$e(nodenoSeoLink('return-center','en')).'" data-nav>English</a></section>';}
 return ['verification'=>$config['seo']??[],'status'=>200,'title'=>$title.' | SEXOGATE','description'=>$description,'canonical'=>null,'alternates'=>[],'indexable'=>false,'jsonld'=>[],'body'=>$body,'locale'=>$locale,'kind'=>'return-center','image'=>''];
}
function sgReturnAdminPage(string $mount,string $version):never{
 foreach(nodenoSecurityHeaders()as $key=>$value)header($key.': '.$value);header('Cache-Control: private, no-store');header('X-Robots-Tag: noindex, nofollow');header('Content-Type: text/html; charset=utf-8');
 $e=static fn($v)=>htmlspecialchars($v,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');echo '<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>İade merkezi | SEXOGATE</title><link rel="stylesheet" href="'.$e($mount.'/admin.css?v='.$version).'"><link rel="stylesheet" href="'.$e($mount.'/sexogate.css?v='.$version).'"><link rel="stylesheet" href="'.$e($mount.'/sg-returns.css?v='.$version).'"><script type="module" src="'.$e($mount.'/sg-returns-admin.js?v='.$version).'"></script></head><body class="sg-return-admin-page"><header class="sg-return-admin-header"><a href="'.$e($mount.'/yonetim').'"><img src="'.$e($mount.'/assets/brand/logo-horizontal.svg').'" width="130" height="80" alt="SEXOGATE"></a><a href="'.$e($mount.'/yonetim').'">Yönetime dön</a></header><main id="sg-return-admin" class="sg-returns"><p role="status">Yönetim oturumu kontrol ediliyor.</p></main></body></html>';exit;
}
function sgReturnWorker(string $private,string $storage):array{
 require_once $private.'/control-http.php';require_once $private.'/sg-returns-http.php';$db=nodenoControlDatabase($storage);sgReturnSchema($db);
 // Bu /test yayını tahsilat yapmaz; anahtar bulunması gerçek iadeyi açmaz.
 return sgReturnRunJobs($db,null,time(),10)+['realProviderEnabled'=>false];
}
