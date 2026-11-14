<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Providers/PaymentProvider.php
 * Açıklama   : Kart verisi almayan ödeme sağlayıcı sınırı.
 */
declare(strict_types=1);
namespace Sexogate\Providers;
interface PaymentProvider
{
    public function createSession(array $order,string $successUrl,string $cancelUrl,string $key):array;
    public function query(string $reference):array;
    public function refund(string $paymentIntent,int $amount,string $key):array;
    public function cancel(string $reference,string $key):array;
    public function verify(string $raw,string $signature):array;
}
