<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Crypto.php
 * Açıklama   : MFA ve mahrem bildirim verisini kapsam ayrımlı AES256-GCM zarfında saklar.
 */
declare(strict_types=1);
namespace Sexogate;
final class Crypto
{
    public function __construct(private Config $config){}
    public function seal(array $data,string $scope):string
    {$iv=random_bytes(12);$tag='';$key=hash('sha256',$scope."\0".$this->config->get('secret'),true);$cipher=openssl_encrypt($this->config->json($data),'aes-256-gcm',$key,OPENSSL_RAW_DATA,$iv,$tag,$scope);if($cipher===false)throw new \RuntimeException('ENCRYPTION_FAILED');return $this->config->json(['v'=>1,'iv'=>base64_encode($iv),'tag'=>base64_encode($tag),'data'=>base64_encode($cipher)]);}
    public function open(string $envelope,string $scope):array
    {$e=json_decode($envelope,true,32,JSON_THROW_ON_ERROR);$key=hash('sha256',$scope."\0".$this->config->get('secret'),true);$plain=openssl_decrypt(base64_decode($e['data'],true),'aes-256-gcm',$key,OPENSSL_RAW_DATA,base64_decode($e['iv'],true),base64_decode($e['tag'],true),$scope);if($plain===false)throw new \RuntimeException('ENCRYPTED_DATA_INVALID');return json_decode($plain,true,32,JSON_THROW_ON_ERROR);}
}
