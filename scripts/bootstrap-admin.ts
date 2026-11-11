/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/bootstrap-admin.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import {getAuth} from '../src/server/auth';
import {pool} from '../src/server/db';
if(!['development','test'].includes(process.env.APP_ENV??''))throw new Error('Yerel yönetici oluşturma yalnız izole geliştirme/test ortamında kullanılabilir.');
const email=process.env.ADMIN_SETUP_EMAIL;const password=process.env.ADMIN_SETUP_PASSWORD;
if(!email||!password)throw new Error('Yerel yönetici bilgileri yapılandırılmadı.');
try{const existing=await pool.query('SELECT id FROM "user" WHERE email=$1',[email]);if(!existing.rowCount){const result=await getAuth().api.signUpEmail({body:{email,password,name:'Yerel Yönetici'}});await pool.query('UPDATE "user" SET role=\'admin\',"emailVerified"=true WHERE id=$1',[result.user.id]);console.log('Yerel yönetici oluşturuldu. Yönetim erişiminden önce MFA kurulumu gerekir.');}else console.log('Mevcut yerel yönetici korunuyor.');}finally{await pool.end();}
