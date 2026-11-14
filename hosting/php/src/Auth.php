<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Auth.php
 * Açıklama   : Argon2id, DB hız sınırı, iptal edilebilir oturum ve gerçek TOTP MFA.
 */
declare(strict_types=1);
namespace Sexogate;
use Symfony\Component\HttpFoundation\Session\SessionInterface;
use Symfony\Component\PasswordHasher\Hasher\NativePasswordHasher;
use OTPHP\TOTP;
final class Auth
{
    private NativePasswordHasher $hasher;private Crypto $crypto;
    public function __construct(private Database $db,private Config $config){$this->hasher=new NativePasswordHasher(algorithm:PASSWORD_ARGON2ID);$this->crypto=new Crypto($config);}
    private function email(string $email):string
    {$email=mb_strtolower(trim($email),'UTF-8');RuleViolation::ensure(strlen($email)<=254&&filter_var($email,FILTER_VALIDATE_EMAIL),'INVALID_EMAIL','E-posta adresini kontrol edin.',400);return $email;}
    private function password(string $password):void{RuleViolation::ensure(mb_strlen($password)>=12&&mb_strlen($password)<=128,'INVALID_PASSWORD','Parola 12 ile 128 karakter arasında olmalıdır.',400);}
    private function limit(string $action,string $email,string $ip):void
    {
        $binary=@inet_pton($ip);$network=$binary===false?'unknown':(strlen($binary)===4?bin2hex($binary):(substr($binary,0,12)===str_repeat("\0",10)."\xff\xff"?bin2hex(substr($binary,12)):bin2hex(substr($binary,0,8))));
        $keys=[hash_hmac('sha256',$action.':account:'.$email,$this->config->get('secret')),hash_hmac('sha256',$action.':network:'.$network,$this->config->get('secret'))];sort($keys,SORT_STRING);
        $this->db->transaction(function()use($keys){foreach($keys as $key){$this->db->execute('INSERT INTO php_login_limits(id,attempts,expires_at) VALUES(?,0,DATE_ADD(CURRENT_TIMESTAMP(3),INTERVAL 1 MINUTE)) ON DUPLICATE KEY UPDATE id=id',[$key]);$row=$this->db->one('SELECT attempts,expires_at FROM php_login_limits WHERE id=? FOR UPDATE',[$key]);$expired=strtotime($row['expires_at'].' UTC')<=time();RuleViolation::ensure($expired||(int)$row['attempts']<5,'RATE_LIMITED','Çok fazla deneme yaptınız. Bir dakika bekleyip yeniden deneyin.',429);$this->db->execute('UPDATE php_login_limits SET attempts=?,expires_at=IF(?,DATE_ADD(CURRENT_TIMESTAMP(3),INTERVAL 1 MINUTE),expires_at) WHERE id=?',[$expired?1:(int)$row['attempts']+1,$expired?1:0,$key]);}});
    }
    public function register(string $name,string $email,string $password,SessionInterface $session,string $ip):array
    {
        $email=$this->email($email);$this->password($password);$name=trim($name);RuleViolation::ensure(mb_strlen($name)>=2&&mb_strlen($name)<=120&&!preg_match('/[\x00-\x1f\x7f]/u',$name),'INVALID_NAME','Ad soyad alanını kontrol edin.',400);$this->limit('signup',$email,$ip);
        RuleViolation::ensure(!$this->db->one('SELECT id FROM `user` WHERE email=?',[$email]),'ACCOUNT_EXISTS','Bu adresle işlem yapılamıyor. Giriş veya parola yenileme adımını kullanın.');$id=Database::id();$hash=$this->hasher->hash($password);$this->db->transaction(function()use($id,$name,$email,$hash){$this->db->execute('INSERT INTO `user`(id,name,email,emailVerified,role,password_hash) VALUES(?,?,?,?,?,?)',[$id,$name,$email,$this->config->local()?1:0,'customer',$hash]);if(!$this->config->local())$this->sendAccountToken($id,$email,'verify-email');});
        if(!$this->config->local())return ['verificationRequired'=>true];$this->complete($session,$id,false);return $this->user($session);
    }
    public function login(string $email,string $password,SessionInterface $session,string $ip):array
    {
        $email=$this->email($email);$this->limit('login',$email,$ip);$user=$this->db->one('SELECT id,password_hash,emailVerified,php_totp_secret FROM `user` WHERE email=?',[$email]);$valid=$user&&is_string($user['password_hash'])&&$this->hasher->verify($user['password_hash'],$password);
        RuleViolation::ensure($valid,'INVALID_CREDENTIALS','E-posta veya parola hatalı.',401);RuleViolation::ensure($this->config->local()||(bool)$user['emailVerified'],'EMAIL_NOT_VERIFIED','E-posta doğrulaması gerekir.',403);
        $session->migrate(true);$session->clear();if($user['php_totp_secret']!==null){$session->set('pending_user',$user['id']);$session->set('pending_until',time()+300);return ['mfaRequired'=>true];}$this->complete($session,$user['id'],false);return $this->user($session);
    }
    private function complete(SessionInterface $session,string $id,bool $mfa):void
    {$row=$this->db->one('SELECT php_session_version FROM `user` WHERE id=?',[$id]);$session->migrate(true);$session->set('user_id',$id);$session->set('epoch',(int)$row['php_session_version']);$session->set('mfa',$mfa);$session->set('auth_at',time());$session->set('last_seen',time());$session->remove('pending_user');$session->remove('pending_until');}
    public function principal(SessionInterface $session):?Principal
    {
        $id=$session->get('user_id');if(!is_string($id))return null;$r=$this->db->one('SELECT id,role,twoFactorEnabled,php_session_version FROM `user` WHERE id=?',[$id]);$ttl=($r['role']??'customer')==='customer'?86400:1800;
        if(!$r||(int)$r['php_session_version']!==$session->get('epoch')||time()-(int)$session->get('last_seen',0)>$ttl){$session->invalidate();return null;}$session->set('last_seen',time());return new Principal($id,$r['role'],(bool)$r['twoFactorEnabled']&&$session->get('mfa')===true);
    }
    public function user(SessionInterface $session):array
    {$p=$this->principal($session);if(!$p)return ['user'=>null,'mfaRequired'=>$session->has('pending_user')];$r=$this->db->one('SELECT id,name,email,twoFactorEnabled FROM `user` WHERE id=?',[$p->id]);return ['user'=>['id'=>$r['id'],'name'=>$r['name'],'email'=>$r['email'],'role'=>$p->role,'mfa'=>$p->mfa,'mfaEnabled'=>(bool)$r['twoFactorEnabled']]];}
    public function logout(SessionInterface $session):void{$session->invalidate();}
    public function beginMfa(SessionInterface $session,string $password):array
    {
        $p=$this->principal($session);RuleViolation::ensure($p,'AUTH_REQUIRED','Giriş yapın.',401);$r=$this->db->one('SELECT email,password_hash,php_totp_secret FROM `user` WHERE id=?',[$p->id]);RuleViolation::ensure($this->hasher->verify($r['password_hash'],$password),'REAUTH_REQUIRED','Parolanızı doğrulayın.',401);RuleViolation::ensure($r['php_totp_secret']===null,'MFA_ALREADY_ENABLED','İki adımlı doğrulama zaten açık.');$otp=TOTP::generate();$otp->setIssuer('SEXOGATE');$otp->setLabel($r['email']);$session->set('mfa_setup',$this->crypto->seal(['secret'=>$otp->getSecret(),'user'=>$p->id,'expires'=>time()+300],'mfa-setup'));return ['secret'=>$otp->getSecret(),'uri'=>$otp->getProvisioningUri()];
    }
    public function confirmMfa(SessionInterface $session,string $code):array
    {
        $p=$this->principal($session);RuleViolation::ensure($p&&$session->has('mfa_setup'),'MFA_SETUP_REQUIRED','Doğrulama kurulumunu yeniden başlatın.');$pending=$this->crypto->open($session->get('mfa_setup'),'mfa-setup');RuleViolation::ensure($pending['user']===$p->id&&$pending['expires']>time()&&TOTP::createFromSecret($pending['secret'])->verify($code),'MFA_INVALID','Doğrulama kodu geçersiz.',401);
        $codes=[];for($i=0;$i<8;$i++)$codes[]=strtoupper(bin2hex(random_bytes(12)));$this->db->execute('UPDATE `user` SET php_totp_secret=?,php_recovery_hashes=?,twoFactorEnabled=true,php_session_version=php_session_version+1 WHERE id=?',[$this->crypto->seal(['secret'=>$pending['secret']],'mfa'),$this->config->json(array_map(fn($c)=>hash('sha256',$c),$codes)),$p->id]);$session->remove('mfa_setup');$this->complete($session,$p->id,true);return ['recoveryCodes'=>$codes];
    }
    public function verifyLoginMfa(SessionInterface $session,string $code,string $ip):array
    {
        $id=$session->get('pending_user');RuleViolation::ensure(is_string($id)&&(int)$session->get('pending_until')>time(),'MFA_CHALLENGE_REQUIRED','Yeniden giriş yapın.',401);$this->limit('mfa',$id,$ip);
        $this->db->transaction(function()use($id,$code){
            $r=$this->db->one('SELECT php_totp_secret,php_recovery_hashes,php_totp_last_step FROM `user` WHERE id=? FOR UPDATE',[$id]);RuleViolation::ensure($r&&$r['php_totp_secret'],'MFA_INVALID','Doğrulama geçersiz.',401);$secret=$this->crypto->open($r['php_totp_secret'],'mfa')['secret'];$otp=TOTP::createFromSecret($secret);$step=intdiv(time(),30);
            foreach([$step-1,$step,$step+1] as $candidate)if($candidate>(int)$r['php_totp_last_step']&&hash_equals($otp->at($candidate*30),$code)){$this->db->execute('UPDATE `user` SET php_totp_last_step=? WHERE id=?',[$candidate,$id]);return;}
            $hashes=json_decode($r['php_recovery_hashes']??'[]',true);$found=array_search(hash('sha256',strtoupper(trim($code))),$hashes,true);RuleViolation::ensure($found!==false,'MFA_INVALID','Doğrulama kodu geçersiz.',401);unset($hashes[$found]);$this->db->execute('UPDATE `user` SET php_recovery_hashes=? WHERE id=?',[$this->config->json(array_values($hashes)),$id]);
        });$this->complete($session,$id,true);return $this->user($session);
    }
    public function setupAdmin(string $name,string $email,string $password):string
    {
        $this->password($password);$email=$this->email($email);return $this->db->transaction(function()use($name,$email,$password){$this->db->one("SELECT name FROM commerce_definition_locks WHERE name='php-admin-setup' FOR UPDATE");RuleViolation::ensure(!$this->db->one("SELECT id FROM `user` WHERE role='admin' FOR UPDATE"),'ADMIN_ALREADY_EXISTS','Yönetici kurulumu daha önce tamamlandı.');$id=Database::id();$this->db->execute("INSERT INTO `user`(id,name,email,emailVerified,role,password_hash) VALUES(?,?,?,true,'admin',?)",[$id,$name,$email,$this->hasher->hash($password)]);return $id;});
    }
    private function sendAccountToken(string $id,string $email,string $kind):void
    {
        $token=bin2hex(random_bytes(32));$this->db->execute('INSERT INTO php_account_tokens(user_id,kind,token_hash,expires_at) VALUES(?,?,?,DATE_ADD(CURRENT_TIMESTAMP(3),INTERVAL 30 MINUTE))',[$id,$kind,hash('sha256',$token)]);
        $path=$kind==='password-reset'?'/hesap/parola-yenile':'/hesap/dogrula';$envelope=$this->crypto->seal(['email'=>$email,'kind'=>$kind,'url'=>$this->config->url($path).'#token='.$token],'email.auth');(new Commerce($this->db,$this->config))->enqueue('email.auth',['envelope'=>$envelope],'account-mail:'.Database::id());
    }
    public function requestReset(string $email,string $ip):array
    {$email=$this->email($email);$this->limit('reset',$email,$ip);$row=$this->db->one('SELECT id FROM `user` WHERE email=?',[$email]);if($row)$this->db->transaction(fn()=> $this->sendAccountToken($row['id'],$email,'password-reset'));return ['recorded'=>true];}
    public function reset(string $token,string $password):void
    {
        $this->password($password);$hash=$this->hasher->hash($password);$this->db->transaction(function()use($token,$hash){$r=$this->db->one("SELECT id,user_id FROM php_account_tokens WHERE token_hash=? AND kind='password-reset' AND consumed_at IS NULL AND expires_at>CURRENT_TIMESTAMP(3) FOR UPDATE",[hash('sha256',$token)]);RuleViolation::ensure($r,'RESET_TOKEN_INVALID','Bağlantı geçersiz veya süresi dolmuş.',400);$this->db->execute('UPDATE `user` SET password_hash=?,php_session_version=php_session_version+1 WHERE id=?',[$hash,$r['user_id']]);$this->db->execute("UPDATE php_account_tokens SET consumed_at=CURRENT_TIMESTAMP(3) WHERE user_id=? AND kind='password-reset' AND consumed_at IS NULL",[$r['user_id']]);});
    }
    public function verifyEmail(string $token):void
    {$this->db->transaction(function()use($token){$r=$this->db->one("SELECT id,user_id FROM php_account_tokens WHERE token_hash=? AND kind='verify-email' AND consumed_at IS NULL AND expires_at>CURRENT_TIMESTAMP(3) FOR UPDATE",[hash('sha256',$token)]);RuleViolation::ensure($r,'VERIFY_TOKEN_INVALID','Bağlantı geçersiz veya süresi dolmuş.',400);$this->db->execute('UPDATE `user` SET emailVerified=true WHERE id=?',[$r['user_id']]);$this->db->execute('UPDATE php_account_tokens SET consumed_at=CURRENT_TIMESTAMP(3) WHERE id=?',[$r['id']]);});}
}
