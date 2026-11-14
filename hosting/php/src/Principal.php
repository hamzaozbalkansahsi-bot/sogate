<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Principal.php
 * Açıklama   : Sunucu oturumundan oluşturulan kimliğin rol ve MFA erişim sınırı.
 */
declare(strict_types=1);
namespace Sexogate;
final readonly class Principal
{
    public function __construct(public string $id,public string $role,public bool $mfa){}
    public function require(string $resource,bool $write=false):void
    {
        RuleViolation::ensure($this->id!==''&&$this->mfa,'MFA_REQUIRED','Bu işlem için doğrulanmış yönetim oturumu gerekir.',403);
        $roles=['catalog'=>['catalog'],'inventory'=>['warehouse'],'purchases'=>['catalog','warehouse','finance'],'orders'=>['warehouse','support','finance'],'shipping'=>['warehouse'],'returns'=>['support','warehouse','finance'],'finance'=>['finance'],'content'=>['marketing'],'customers'=>['support'],'settings'=>[]];
        RuleViolation::ensure($this->role==='admin'||in_array($this->role,$roles[$resource]??[],true),'FORBIDDEN','Bu işlem için yetkiniz yok.',403);
        if($write&&in_array($resource,['orders','finance'],true))RuleViolation::ensure(in_array($this->role,['admin','finance','support'],true),'FORBIDDEN','Bu işlem için yetkiniz yok.',403);
    }
    public function costs():bool{return $this->mfa&&in_array($this->role,['admin','finance','catalog'],true);}
}
