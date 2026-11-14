<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/RuleViolation.php
 * Açıklama   : Müşteriye güvenle dönebilen iş kuralı ve HTTP hata sınırı.
 */
declare(strict_types=1);
namespace Sexogate;
final class RuleViolation extends \RuntimeException
{
    public function __construct(public readonly string $rule,string $message,public readonly int $status=409){parent::__construct($message);}
    public static function ensure(mixed $condition,string $code,string $message,int $status=409):void
    {if(!$condition)throw new self($code,$message,$status);}
}
