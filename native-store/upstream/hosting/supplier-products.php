<?php
declare(strict_types=1);

/** Read one hash-bound public description without loading every supplier description into memory. */
function nodenoSupplierDetails(string $private,string $id,array $catalog):?array {
    if(!preg_match('/^[A-Za-z0-9_-]{1,80}$/D',$id))return null;
    $product=null;
    foreach($catalog['products']??[]as $p)if(($p['id']??'')===$id){$product=$p;break;}
    if(!$product||($product['productType']??'')!=='supplier-item'||($product['hidden']??false)||($product['published']??true)===false||empty($product['supplierDetailsHash']))return null;
    $indexFile=$private.'/supplier-details.json';$dataFile=$private.'/supplier-details.bin';
    if(!is_file($indexFile)||!is_file($dataFile)||is_link($indexFile)||is_link($dataFile))throw new RuntimeException('Supplier details unavailable');
    $index=json_decode((string)file_get_contents($indexFile),true,64,JSON_THROW_ON_ERROR);$entry=$index['products'][$id]??null;
    if(!is_array($entry)||!is_int($entry['offset']??null)||!is_int($entry['bytes']??null)||$entry['offset']<0||$entry['bytes']<1||$entry['bytes']>262144||!hash_equals((string)$product['supplierDetailsHash'],(string)($entry['sha256']??'')))throw new RuntimeException('Supplier details index mismatch');
    $handle=fopen($dataFile,'rb');if(!$handle)throw new RuntimeException('Supplier details unavailable');
    try {
        $stat=fstat($handle);
        if($entry['offset']+$entry['bytes']>$stat['size']||fseek($handle,$entry['offset'])!==0)throw new RuntimeException('Supplier details range mismatch');
        $body='';while(strlen($body)<$entry['bytes']&&!feof($handle)){$chunk=fread($handle,$entry['bytes']-strlen($body));if($chunk===false)throw new RuntimeException('Supplier details read failed');$body.=$chunk;}
    }finally{fclose($handle);}
    if(!hash_equals($entry['sha256'],hash('sha256',$body)))throw new RuntimeException('Supplier details hash mismatch');
    $value=json_decode($body,true,64,JSON_THROW_ON_ERROR);
    if(($value['id']??'')!==$id||!is_array($value['description']??null))throw new RuntimeException('Supplier details identity mismatch');
    foreach(['tr','en','ru','ar']as $locale)if(!is_string($value['description'][$locale]??null)||$value['description'][$locale]==='')throw new RuntimeException('Supplier translation missing');
    return ['id'=>$id,'description'=>array_intersect_key($value['description'],array_flip(defined('NODENO_STORE_LOCALES')?NODENO_STORE_LOCALES:['tr','en','ru','ar'])),'sha256'=>$entry['sha256']];
}

function nodenoSupplierSeoDetails(string $private,array $catalog,array $query):array {
    $id=$query['product']??null;
    if(!is_string($id))return $catalog;
    $details=nodenoSupplierDetails($private,$id,$catalog);if(!$details)return $catalog;
    foreach($catalog['products']as &$product)if($product['id']===$id){$product['description']=$details['description'];break;}
    unset($product);return $catalog;
}

/** The release health check has already hashed every listed public file. Bind those hashes to review decisions. */
function nodenoSupplierMediaHealth(string $private,array $catalog,array $files):array {
    $products=array_values(array_filter($catalog['products']??[],static fn($p)=>($p['productType']??'')==='supplier-item'));
    if(!$products)return ['supplierProducts'=>0,'supplierMediaApproved'=>0];
    $file=$private.'/supplier-media-approved.json';
    if(!is_file($file)||is_link($file))throw new RuntimeException('Supplier image review required');
    $approved=json_decode((string)file_get_contents($file),true,512,JSON_THROW_ON_ERROR);
    if(($approved['schema']??null)!==1||($approved['publicationReady']??false)!==true||($approved['testOnly']??false)!==false)throw new RuntimeException('Supplier image review required');
    $references=[];$seen=[];
    foreach($products as $product)foreach($product['images']as $index=>$path){
        if(!preg_match('~^/assets/suppliers/([a-f0-9]{64})\.(jpg|png|webp)$~D',$path,$match))throw new RuntimeException('Invalid supplier image path');
        $row=$approved['images'][$path]??null;
        if(!is_array($row)||($row['visualReview']??false)!==true||($row['outputSha256']??'')!==$match[1]||!preg_match('/^[a-f0-9]{64}$/D',$row['sourceSha256']??'')||($files['public'.$path]??'')!==$match[1])throw new RuntimeException('Supplier image approval mismatch');
        $references[$product['id'].':'.$index]=$path;$seen[$path]=true;
    }
    if(count($seen)!==count($approved['images']??[])||$references!==($approved['references']??null))throw new RuntimeException('Supplier image references mismatch');
    return ['supplierProducts'=>count($products),'supplierMediaApproved'=>count($seen)];
}
