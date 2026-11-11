/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/auth.ts
 * Açıklama   : Güvenli oturum, rol ve oturuma bağlı iki adımlı doğrulama.
 */
import { betterAuth } from 'better-auth';
import { twoFactor } from 'better-auth/plugins';
import {createAuthMiddleware} from 'better-auth/api';
import { pool } from './db';
import { createCipheriv, createHash, randomBytes, randomUUID } from 'node:crypto';
import { HttpError } from './security';
import type { Principal, Role } from '../shared/contracts';

export function authOptions() {
  const secret=process.env.BETTER_AUTH_SECRET;
  if(!secret||secret.length<32)throw new HttpError(503,'Oturum ayarları henüz tamamlanmadı.');
  return {
    appName:'SEXSOGATE', database:pool, secret,
    baseURL:process.env.BETTER_AUTH_URL,
    trustedOrigins:[process.env.APP_URL ?? 'http://127.0.0.1:3000'],
    emailAndPassword:{ enabled:true, minPasswordLength:12, maxPasswordLength:128,
      requireEmailVerification:process.env.APP_ENV==='production',
      revokeSessionsOnPasswordReset:true,
      sendResetPassword:async({user,url}:{user:{email:string};url:string})=>enqueueAuthEmail(user.email,'password-reset',url)
    },
    emailVerification:{sendVerificationEmail:async({user,url}:{user:{email:string};url:string})=>enqueueAuthEmail(user.email,'verify-email',url)},
    user:{additionalFields:{role:{type:'string' as const,defaultValue:'customer',input:false}}},
    session:{expiresIn:60*60*24,updateAge:60*30,freshAge:60*15,cookieCache:{enabled:false}},
    rateLimit:{enabled:true,storage:'database' as const,window:60,max:60,customRules:{'/sign-in/email':{window:60,max:5},'/sign-up/email':{window:60,max:5},'/request-password-reset':{window:60,max:3}}},
    advanced:{useSecureCookies:process.env.APP_ENV==='production',defaultCookieAttributes:{httpOnly:true,sameSite:'lax' as const,path:'/'}},
    plugins:[twoFactor({issuer:'SEXSOGATE',totpOptions:{period:30,digits:6}})],
    hooks:{after:createAuthMiddleware(async ctx=>{
      if(!['/two-factor/verify-totp','/two-factor/verify-backup-code'].includes(ctx.path??''))return;
      const result=ctx.context.returned;
      if(!result||typeof result!=='object'||!('token' in result)||typeof result.token!=='string')return;
      const verified=ctx.context.newSession?.session??ctx.context.session?.session;
      if(!verified)return;
      const row=(await pool.query('SELECT s.id,s."userId",u."twoFactorEnabled" FROM session s JOIN "user" u ON u.id=s."userId" WHERE s.id=$1',[verified.id])).rows[0];
      if(!row?.twoFactorEnabled)return;
      await pool.query('INSERT INTO session_mfa(session_id,user_id) VALUES($1,$2) ON CONFLICT(session_id) DO UPDATE SET verified_at=now()',[row.id,row.userId]);
      // Password-only sessions created before enrollment must never gain MFA authority.
      await pool.query('DELETE FROM session WHERE "userId"=$1 AND id<>$2 AND NOT EXISTS(SELECT 1 FROM session_mfa WHERE session_id=session.id)',[row.userId,row.id]);
    })},
  };
}
let instance:ReturnType<typeof betterAuth<ReturnType<typeof authOptions>>>|undefined;
export function getAuth(){return instance??=betterAuth(authOptions());}
export async function getPrincipal(headers:Headers):Promise<Principal|null>{
  const session=await getAuth().api.getSession({headers});
  if(!session)return null;
  // Role is loaded from the database on every request, never from a client claim.
  const result=await pool.query<{role:Role;twoFactorEnabled:boolean;mfa_verified:boolean}>('SELECT u.role,u."twoFactorEnabled",EXISTS(SELECT 1 FROM session_mfa m WHERE m.user_id=u.id AND m.session_id=$2 AND m.verified_at>now()-interval \'4 hours\') mfa_verified FROM "user" u WHERE u.id=$1',[session.user.id,session.session.id]);
  const row=result.rows[0];if(!row)return null;
  return {id:session.user.id,role:row.role,mfa:row.twoFactorEnabled===true&&row.mfa_verified===true,mfaEnabled:row.twoFactorEnabled===true};
}
export async function requirePrincipal(headers:Headers,admin=false){
  const principal=await getPrincipal(headers);if(!principal)throw new HttpError(401,'Devam etmek için giriş yapın.');
  if(admin){if(principal.role==='customer')throw new HttpError(403,'Bu işlem için yetkiniz yok.');if(!principal.mfa)throw new HttpError(403,'Yönetim erişimi için iki adımlı doğrulamayı etkinleştirin.','MFA_REQUIRED');}
  return principal;
}
async function enqueueAuthEmail(email:string,kind:string,url:string){
  const iv=randomBytes(12);const key=createHash('sha256').update(process.env.BETTER_AUTH_SECRET!).digest();
  const cipher=createCipheriv('aes-256-gcm',key,iv);const data=Buffer.concat([cipher.update(JSON.stringify({email,kind,url}),'utf8'),cipher.final()]);
  const payload={iv:iv.toString('hex'),tag:cipher.getAuthTag().toString('hex'),data:data.toString('hex')};
  await pool.query("INSERT INTO jobs(type,payload,dedupe_key) VALUES('email.auth',$1,$2)",[payload,`auth:${randomUUID()}`]);
}
