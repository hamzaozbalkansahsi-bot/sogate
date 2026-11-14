<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Config.php
 * Açıklama   : Git dışı yapılandırma, ortam ve test/gerçek ödeme sınırları.
 */
declare(strict_types=1);
namespace Sexogate;
final class Config
{
    public function __construct(private readonly array $values)
    {
        RuleViolation::ensure(PHP_INT_SIZE===8,'PHP_64_BIT_REQUIRED','Sunucu yapılandırması uygun değil.',503);
        RuleViolation::ensure(in_array($this->get('env'),['development','test','production'],true),'ENV_REQUIRED','Ortam yapılandırması eksik.',503);
        RuleViolation::ensure(strlen($this->get('secret'))>=32,'SECRET_REQUIRED','Güvenli uygulama ayarları eksik.',503);
        RuleViolation::ensure(in_array($this->get('base_path'),['','/test'],true),'BASE_PATH_INVALID','Uygulama yolu geçersiz.',503);
        $url=parse_url($this->get('app_url'));RuleViolation::ensure(is_array($url)&&isset($url['host'])&&in_array($url['scheme']??'', ['http','https'],true)&&!isset($url['user'])&&!isset($url['pass']),'APP_URL_INVALID','Uygulama adresi geçersiz.',503);
        if($this->local()&&!in_array($url['host'],['127.0.0.1','localhost','::1'],true))RuleViolation::ensure($url['scheme']==='https'&&$this->flag('stage_access')&&strlen($this->get('stage_password_sha256'))===64&&$this->get('stage_user')!=='','STAGE_ACCESS_REQUIRED','Özel test erişimi yapılandırılmadı.',503);
        if(!$this->local())RuleViolation::ensure($this->get('payment_provider')!=='test','TEST_PROVIDER_DISABLED','Test ödemesi üretimde kullanılamaz.',503);
    }
    public static function load(string $file):self
    {if(!is_file($file))throw new RuleViolation('CONFIG_REQUIRED','Uygulama kurulumu tamamlanmadı.',503);$values=str_ends_with($file,'.json')?json_decode(file_get_contents($file),true,64,JSON_THROW_ON_ERROR):require $file;if(!is_array($values))throw new \RuntimeException('CONFIG_INVALID');return new self($values);}
    public function get(string $key,string $fallback=''):string{return isset($this->values[$key])?(string)$this->values[$key]:$fallback;}
    public function flag(string $key):bool{return ($this->values[$key]??false)===true;}
    public function local():bool{return in_array($this->get('env'),['development','test'],true);}
    public function url(string $path='/'):string
    {RuleViolation::ensure(str_starts_with($path,'/')&&!str_starts_with($path,'//'),'INVALID_PATH','Bağlantı geçersiz.',400);return rtrim($this->get('app_url'),'/').$path;}
    public function path(string $path='/'):string{return $this->get('base_path').$path;}
    public function json(array $data):string{return json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);}
}
