<?php
declare(strict_types=1);

const NODENO_STORE_LOCALES=['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa'];
const NODENO_NATIVE_LOCALES=['de','az','kk','tk','uz','ky','fa'];
function nodenoLocaleValid(mixed $locale):bool {return is_string($locale)&&in_array($locale,NODENO_STORE_LOCALES,true);}
function nodenoLocaleRtl(string $locale):bool {return in_array($locale,['ar','fa'],true);}
function nodenoLocaleDictionary(string $locale,bool $catalogue=false):array {
 static $cache=[];
 if(!in_array($locale,NODENO_NATIVE_LOCALES,true))throw new InvalidArgumentException('invalid_locale');
 $key=$locale.($catalogue?'.catalogue':'');
 if(isset($cache[$key]))return $cache[$key];
 $file=__DIR__.'/locale.'.$key.'.json';
 if(!is_file($file)&&basename(__DIR__)==='hosting'&&is_file(dirname(__DIR__).'/AGENTS.md'))$file=dirname(__DIR__).'/web/locales/'.$key.'.json';
 if(!is_file($file)||is_link($file))throw new RuntimeException('locale_dictionary_unavailable');
 $value=json_decode((string)file_get_contents($file),true,64,JSON_THROW_ON_ERROR);
 if(($value['schema']??null)!==1||($value['locale']??null)!==$locale||!is_array($value['translations']??null))throw new RuntimeException('invalid_locale_dictionary');
 return $cache[$key]=$value['translations'];
}
function nodenoNativeText(string $source,string $locale):string {
 if(!in_array($locale,NODENO_NATIVE_LOCALES,true)||$source===''||!preg_match('/[A-Za-z]{2}/',$source)||preg_match('~^(?:https?://|/|[\w.+-]+@[\w.-]+\.[A-Za-z]+$)~',$source))return $source;
 $dictionary=nodenoLocaleDictionary($locale);
 if(!array_key_exists($source,$dictionary))$dictionary=nodenoLocaleDictionary($locale,true);
 if(!array_key_exists($source,$dictionary))throw new RuntimeException('locale_translation_missing:'.$locale);
 return $dictionary[$source];
}
function nodenoLocaleTree(mixed $value,string $locale):mixed {
 if(is_string($value))return nodenoNativeText($value,$locale);
 if(is_array($value)){foreach($value as $key=>$item)$value[$key]=nodenoLocaleTree($item,$locale);}
 return $value;
}
function nodenoLocaleCopy(array $copy,string $locale):mixed {
 if(array_key_exists($locale,$copy))return $copy[$locale];
 if(in_array($locale,NODENO_NATIVE_LOCALES,true)&&array_key_exists('en',$copy))return nodenoLocaleTree($copy['en'],$locale);
 return $copy['tr']??$copy['en']??[];
}
function nodenoLocaleLocal(mixed $value,string $locale):string {
 if(is_string($value)||is_int($value)||is_float($value))return (string)$value;
 if(!is_array($value))return '';
 if(isset($value[$locale]))return (string)$value[$locale];
 if(in_array($locale,NODENO_NATIVE_LOCALES,true)){
  $source=$value['en']??'';if(!is_string($source))return '';
  if(($value['tr']??null)===$source&&($value['ru']??null)===$source&&($value['ar']??null)===$source)return $source;
  return nodenoNativeText($source,$locale);
 }
 return (string)($value['tr']??$value['en']??'');
}
function nodenoLocaleDocument(array $versions,string $locale):string {
 if(isset($versions[$locale]))return $versions[$locale];
 if(!in_array($locale,NODENO_NATIVE_LOCALES,true))return '';
 return implode("\n\n",array_map(static fn($p)=>nodenoNativeText($p,$locale),explode("\n\n",$versions['en']??'')));
}
