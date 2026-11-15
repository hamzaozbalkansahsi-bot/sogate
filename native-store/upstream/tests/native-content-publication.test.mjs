import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
test('native content can be edited and untranslated English changes cannot replace live content',()=>{
 const code=`require 'hosting/control-http.php';$fields=nodenoControlDefinitions()['products']['fields'];$data=['title_en'=>'A previously unseen catalogue title 20261111'];$error='';try{nodenoControlNativePublication('products',$data);}catch(NodenoControlHttpError $e){$error=$e->errorCode;}foreach(NODENO_NATIVE_LOCALES as $locale)$data['title_'.$locale]='Native title '.$locale;nodenoControlNativePublication('products',$data);nodenoControlNativePublication('products',['priceMinor'=>12000]);echo json_encode([isset($fields['title_kk'],$fields['description_fa'],$fields['seoTitle_az']),$error,nodenoControlDefinitions()['markets']['fields']['language']['options']]);`;
 const r=spawnSync('artifacts/runtime-php/php.exe',['-r',code],{encoding:'utf8'});assert.equal(r.status,0,r.stderr||r.stdout);
 const [fields,error,languages]=JSON.parse(r.stdout);assert.equal(fields,true);assert.equal(error,'native_translation_required');assert.equal(languages.length,11);
});
