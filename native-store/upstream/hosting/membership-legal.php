<?php
declare(strict_types=1);
require_once __DIR__.'/localization.php';

function nodenoMembershipSchema(PDO $db):void {
 $db->exec('CREATE TABLE IF NOT EXISTS membership_acceptances(user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,version TEXT NOT NULL,locale TEXT NOT NULL,document_hash TEXT NOT NULL,document_json TEXT NOT NULL,accepted_at INTEGER NOT NULL)');
}
function nodenoMembershipTerms($locale):array {
 if(!is_string($locale)||!in_array($locale,NODENO_STORE_LOCALES,true))throw new NodenoAccountHttpError(422,'membership_locale_invalid');
 $file=__DIR__.'/site-documents.'.$locale.'.json';
 // Only this repository's source layout has a development fallback. Releases must package their own corpus.
 if(!is_file($file)&&basename(__DIR__)==='hosting'&&is_file(dirname(__DIR__).'/AGENTS.md'))$file=dirname(__DIR__).'/data/legal/site-documents.'.$locale.'.json';
 if(!is_file($file)||is_link($file))throw new RuntimeException('Membership terms unavailable');
 $corpus=json_decode((string)file_get_contents($file),true,64,JSON_THROW_ON_ERROR);$document=null;
 if(($corpus['locale']??null)!==$locale||!is_string($corpus['version']??null))throw new RuntimeException('Membership corpus invalid');
 foreach($corpus['documents']??[]as $item)if(($item['id']??'')==='membership')$document=$item;
 if(!is_array($document)||!is_array($document['sections']??null))throw new RuntimeException('Membership document unavailable');
 $version=$document['version']??$corpus['version'];$json=json_encode(['version'=>$version,'locale'=>$locale,'document'=>$document],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
 return ['version'=>$version,'hash'=>hash('sha256',$json),'locale'=>$locale,'url'=>'/legal/membership?lang='.$locale,'documentJson'=>$json];
}
function nodenoMembershipValidate(array $body):array {
 if(($body['acceptMembership']??null)!==true||!is_string($body['membershipVersion']??null)||!is_string($body['membershipHash']??null)||!is_string($body['membershipLocale']??null))throw new NodenoAccountHttpError(422,'membership_acceptance_required');
 $terms=nodenoMembershipTerms($body['membershipLocale']);
 if(!hash_equals($terms['version'],$body['membershipVersion'])||!hash_equals($terms['hash'],$body['membershipHash']))throw new NodenoAccountHttpError(409,'membership_terms_changed');
 return $terms;
}
function nodenoMembershipRecord(PDO $db,string $userId,array $terms,int $acceptedAt):void {
 $db->prepare('INSERT INTO membership_acceptances(user_id,version,locale,document_hash,document_json,accepted_at) VALUES(?,?,?,?,?,?)')->execute([$userId,$terms['version'],$terms['locale'],$terms['hash'],$terms['documentJson'],$acceptedAt]);
}
