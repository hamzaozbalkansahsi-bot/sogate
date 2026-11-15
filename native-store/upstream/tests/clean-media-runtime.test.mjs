import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtemp,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath} from 'node:url';

const root=fileURLToPath(new URL('../',import.meta.url));
const php=process.env.PHP_BINARY||'php';
const missing=spawnSync(php,['--version']).status!==0?'PHP unavailable; clean-media execution unverified':false;
test('PHP serves only exact approved hashes, ignores baseline caches and never falls back from cleaned files',{skip:missing},async()=>{
 const temporary=await mkdtemp(path.join(os.tmpdir(),'nodeno-clean-media-'));
 try {
  const script=`<?php
define('NODENO_RUNTIME_LIBRARY', true);
require 'hosting/index.php';
function check($value,$message) { if(!$value) throw new RuntimeException($message); }
function rejects($call,$message) { $failed=false; try{$call();}catch(Throwable $error){$failed=true;} check($failed,$message); }
$root=${JSON.stringify(temporary.replaceAll('\\','/'))};
mkdir($root.'/cache'); mkdir($root.'/vault'); mkdir($root.'/private');
$root=realpath($root);
$png=base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=');
$sha=hash('sha256',$png); $url='https://witcdn.adoremobilya.com/test.png'; $key=hash('sha256',$url);
$entry=['state'=>'approved_unmodified','sourceSha'=>$sha,'outputSha'=>$sha,'mime'=>'image/png','bytes'=>strlen($png),'width'=>1,'height'=>1,'file'=>null];
file_put_contents($root.'/cache/'.$key.'.bin',$png);
$calls=0;
$transport=function($url,$file) use($png,&$calls) { $calls++;file_put_contents($file,$png);return ['status'=>200,'headers'=>['content-type'=>'image/png']]; };
$image=nodenoFetchImage($url,$root.'/cache',$transport,$entry);
check($calls===1,'Unsafe baseline URL cache was reused');
check(basename($image['file'])==='approved-'.$sha.'.bin','Approval cache namespace missing');
check(hash_file('sha256',$image['file'])===$sha,'Approved source bytes changed');
nodenoFetchImage($url,$root.'/cache',function(){throw new RuntimeException('Fresh approved cache missed');},$entry);
file_put_contents($image['file'],$png.'tampered');
rejects(function() use($url,$root,$entry,$png) { nodenoFetchImage($url,$root.'/cache',function($url,$file) use($png){file_put_contents($file,$png.'changed-source');return ['status'=>200,'headers'=>['content-type'=>'image/png']];},$entry); },'Changed supplier bytes were accepted');
$clean=$entry; $clean['state']='approved_cleaned'; $clean['file']=$sha.'.png';
file_put_contents($root.'/vault/'.$clean['file'],$png);
$verified=nodenoApprovedVaultImage($root.'/vault',$clean);check($verified['sha256']===$sha,'Vault hash mismatch');
$original=nodenoApprovedVaultImage($root.'/vault',$entry);check($original['sha256']===$sha,'Unmodified approved file must also use local vault');
$set=['images'=>[$key=>$entry]];$releaseHash=str_repeat('b',64);$mediaVersion=str_repeat('c',64);
nodenoVerifyMediaVault($root.'/vault',$set,$releaseHash,$mediaVersion);
nodenoVerifyMediaVault($root.'/vault',$set,$releaseHash,$mediaVersion);
check(count(glob($root.'/vault/.nodeno-verified-*.json'))===1,'Private verification receipt missing');
file_put_contents($root.'/vault/'.$clean['file'],$png.'changed');
rejects(function() use($root,$clean){nodenoApprovedVaultImage($root.'/vault',$clean);},'Tampered cleaned image accepted');
rejects(function() use($root,$set,$releaseHash,$mediaVersion){nodenoVerifyMediaVault($root.'/vault',$set,$releaseHash,$mediaVersion);},'Cached health receipt accepted a changed hosted file');
unlink($root.'/vault/'.$clean['file']);
rejects(function() use($root,$clean){nodenoApprovedVaultImage($root.'/vault',$clean);},'Missing cleaned image accepted');
rejects(function() use($root,$entry){nodenoApprovedVaultImage($root.'/vault',$entry);},'Missing unmodified local file accepted');
$traversal=$clean;$traversal['file']='../../secret';rejects(function()use($traversal){nodenoValidateMediaApproval($traversal);},'Path traversal accepted');
$review=$entry;$review['state']='review_required';rejects(function()use($review){nodenoValidateMediaApproval($review);},'Quarantine approval accepted');
$manifest=['schema'=>1,'policy'=>'approved-only-v1','referenceCount'=>1,'uniqueCount'=>1,'counts'=>['approved_unmodified'=>1,'approved_cleaned'=>0],'references'=>['7:0'=>$key],'images'=>[$key=>$entry]];
$write=function($manifest)use($root){$body=json_encode($manifest);file_put_contents($root.'/private/media-approved.json',$body);file_put_contents($root.'/private/release.json',json_encode(['mediaVersion'=>hash('sha256',$body)]));};
$write($manifest);check(nodenoApprovedMediaManifest($root.'/private',['7'=>[$url]])['referenceCount']===1,'Complete approval rejected');
$manifest['references']=[];$write($manifest);rejects(function()use($root,$url){nodenoApprovedMediaManifest($root.'/private',['7'=>[$url]]);},'Missing reference accepted');
echo json_encode(['status'=>'passed','baselineNetworkCalls'=>$calls]);
`;
  const result=spawnSync(php,[],{cwd:root,input:script,encoding:'utf8'});
  assert.equal(result.status,0,result.stderr||result.stdout);
  assert.equal(JSON.parse(result.stdout).status,'passed');
 } finally {
  if(path.dirname(temporary)!==path.resolve(os.tmpdir())||!path.basename(temporary).startsWith('nodeno-clean-media-')) throw new Error('Unsafe fixture cleanup');
  await rm(temporary,{recursive:true,force:true});
 }
});
