/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/privacy.ts
 * Açıklama   : Veri sorumlusu kimliğini ve kanıtlı ilgili kişi başvuru iş akışını yönetir.
 */
import {createCipheriv,createHash,randomBytes} from 'node:crypto';
import {z} from 'zod';
import {query,transaction,type Connection,pool} from './db';
import {HttpError} from './security';
import type {Principal} from '../shared/contracts';
const kinds=['access','correction','erasure','objection','portability','consent_withdrawal','other'] as const;
const local=()=>['development','test'].includes(process.env.APP_ENV??'');
const hash=(value:string)=>createHash('sha256').update(value).digest('hex');
function parse<T>(schema:z.ZodType<T>,value:unknown):T{const result=schema.safeParse(value);if(!result.success)throw new HttpError(400,'Başvuru alanlarını ve biçimlerini kontrol edin.','PRIVACY_VALIDATION');return result.data;}
function authorized(principal:Principal,configuration=false){if(!principal.mfa||!(configuration?['admin']:['admin','support']).includes(principal.role))throw new HttpError(403,'Bu gizlilik işlemi için yetkiniz yok.');}
async function audit(principal:Principal,action:string,id:string,details:Record<string,unknown>,connection:Connection){await query("INSERT INTO audit_log(actor_id,action,resource,resource_id,details) VALUES($1,$2,'privacy',$3,$4)",[principal.id,action,id,JSON.stringify(details)],connection);}
async function policyFor(country:string|null,connection:Connection=pool){if(!country)return null;const [row]=await query("SELECT p.id FROM privacy_policies p JOIN privacy_controllers c ON c.id=p.controller_id WHERE p.country=$1 AND p.approved=true AND c.status='approved' AND($2=true OR(p.fixture=false AND c.fixture=false))",[country,local()],connection);return row??null;}
async function queueNotice(input:{email:string;reference:string;url:string;locale:string},key:string,connection:Connection){
 const secret=process.env.BETTER_AUTH_SECRET;if(!secret||secret.length<32)throw new HttpError(503,'Güvenli bildirim yapılandırması eksik.');
 const iv=randomBytes(12),cipher=createCipheriv('aes-256-gcm',createHash('sha256').update(secret).digest(),iv),data=Buffer.concat([cipher.update(JSON.stringify(input),'utf8'),cipher.final()]);
 await query("INSERT INTO jobs(type,payload,dedupe_key) VALUES('email.privacy',$1,$2) ON CONFLICT(dedupe_key) DO NOTHING",[{iv:iv.toString('hex'),tag:cipher.getAuthTag().toString('hex'),data:data.toString('hex')},key],connection);
}
export async function createPrivacyRequest(input:unknown,principal:Principal|null){
 const value=parse(z.object({email:z.email().max(254),type:z.enum(kinds),summary:z.string().trim().min(10).max(4000),country:z.string().regex(/^[A-Z]{2}$/).optional(),locale:z.enum(['tr','en'])}).strict(),input);
 if(principal){const [user]=await query('SELECT email FROM "user" WHERE id=$1',[principal.id]);if(!user||user.email.toLowerCase()!==value.email.toLowerCase())throw new HttpError(400,'Hesabınıza bağlı e-posta adresini kullanın.');}
 const token=randomBytes(32).toString('base64url');
 const row=await transaction(async connection=>{
  await query("SELECT pg_advisory_xact_lock_shared(hashtext('privacy-controller'))",[],connection);
  if(value.country)await query("SELECT pg_advisory_xact_lock(hashtext('privacy-policy:'||$1))",[value.country],connection);
  const policy=await policyFor(value.country??null,connection);
  const [created]=await query("INSERT INTO privacy_requests(customer_id,email,type,summary,country,locale,tracking_hash,policy_id,due_at) VALUES($1,$2,$3,$4,$5,$6,$7,$8,sg_privacy_deadline(now(),$8)) RETURNING id,reference",[principal?.id??null,value.email,value.type,value.summary,value.country??null,value.locale,hash(token),policy?.id??null],connection);
  const url=new URL(`${value.locale==='en'?'/en':''}/veri-basvurusu`,process.env.APP_URL??'http://127.0.0.1:3000');url.searchParams.set('case',created.id);url.searchParams.set('token',token);
  await queueNotice({email:value.email,reference:created.reference,url:url.href,locale:value.locale},`privacy-received:${created.id}`,connection);return created;
 });
 return {id:String(row.id),reference:String(row.reference),token};
}
export async function getPrivacyRequest(id:string,token:string|null,principal:Principal|null){
 if(id.length>100||token&&(!/^[A-Za-z0-9_-]{43}$/.test(token)))throw new HttpError(404,'Başvuru bulunamadı.');
 const [row]=await query('SELECT id,reference,customer_id,status,identity_status,received_at,due_at,type,summary,email,country FROM privacy_requests WHERE id=$1 AND((customer_id=$2 AND $2::text IS NOT NULL) OR(tracking_hash=$3 AND $3::text IS NOT NULL))',[id,principal?.id??null,token?hash(token):null]);
 if(!row)throw new HttpError(404,'Başvuru bulunamadı.');
 const result={id:row.id,reference:row.reference,status:row.status,receivedAt:row.received_at.toISOString(),dueAt:row.due_at?.toISOString()??null};
 if(!principal||row.customer_id!==principal.id)return result;
 return {...result,type:row.type,summary:row.summary,identityStatus:row.identity_status,responses:await query('SELECT body,outcome,created_at FROM privacy_responses WHERE request_id=$1',[id])};
}
export async function myPrivacyRequests(principal:Principal){return query('SELECT id,reference,type,status,received_at,due_at FROM privacy_requests WHERE customer_id=$1 ORDER BY received_at DESC LIMIT 100',[principal.id]);}
export async function saveController(input:unknown,principal:Principal){
 authorized(principal,true);const value=parse(z.object({action:z.literal('controller'),legalName:z.string().trim().min(2).max(300),address:z.string().trim().min(5).max(1000),email:z.email().max(254),evidence:z.string().trim().min(10).max(2000),approve:z.boolean()}).strict(),input);
 return transaction(async connection=>{
  await query("SELECT pg_advisory_xact_lock(hashtext('privacy-controller'))",[],connection);
  if(value.approve){
   await query("UPDATE privacy_policies SET approved=false WHERE controller_id IN(SELECT id FROM privacy_controllers WHERE status='approved')",[],connection);
   await query("UPDATE privacy_controllers SET status='archived' WHERE status='approved'",[],connection);
  }
  const [row]=await query("INSERT INTO privacy_controllers(version,legal_name,address,email,evidence,status,fixture,created_by) SELECT coalesce(max(version),0)+1,$1,$2,$3,$4,$5,$6,$7 FROM privacy_controllers RETURNING id,version",[value.legalName,value.address,value.email,value.evidence,value.approve?'approved':'draft',local(),principal.id],connection);
  await audit(principal,value.approve?'controller_approved':'controller_draft_saved',row.id,{version:row.version},connection);return row;
 });
}
export async function savePrivacyPolicy(input:unknown,principal:Principal){
 authorized(principal,true);const value=parse(z.object({action:z.literal('policy'),country:z.string().regex(/^[A-Z]{2}$/),unit:z.enum(['days','months']),count:z.number().int().min(1).max(366),timeZone:z.string().min(1).max(100),source:z.url().max(1000).refine(url=>new URL(url).protocol==='https:'),evidence:z.string().trim().min(10).max(2000),retentionNote:z.string().trim().min(20).max(4000),approve:z.boolean()}).strict(),input);
 if(value.unit==='months'&&value.count>12)throw new HttpError(400,'Takvim ayı sınırını kontrol edin.');
 return transaction(async connection=>{
  await query("SELECT pg_advisory_xact_lock_shared(hashtext('privacy-controller'))",[],connection);
  await query("SELECT pg_advisory_xact_lock(hashtext('privacy-policy:'||$1))",[value.country],connection);
  const [zone]=await query('SELECT name FROM pg_timezone_names WHERE name=$1',[value.timeZone],connection);if(!zone)throw new HttpError(400,'Geçerli bir saat dilimi seçin.');
  const [controller]=await query("SELECT id FROM privacy_controllers WHERE status='approved' AND($1=true OR fixture=false)",[local()],connection);
  if(value.approve&&!controller)throw new HttpError(409,'Önce ayrı veri sorumlusu kimliğini doğrulayın.');
  if(value.approve)await query('UPDATE privacy_policies SET approved=false WHERE country=$1 AND approved=true',[value.country],connection);
  const [row]=await query('INSERT INTO privacy_policies(controller_id,country,version,unit,period_count,time_zone,source,evidence,retention_note,approved,fixture,approved_by) SELECT $1,$2,coalesce(max(version),0)+1,$3,$4,$5,$6,$7,$8,$9,$10,$11 FROM privacy_policies WHERE country=$2 RETURNING id,version',[controller?.id??null,value.country,value.unit,value.count,value.timeZone,value.source,value.evidence,value.retentionNote,value.approve,local(),value.approve?principal.id:null],connection);
  if(value.approve)await query("UPDATE privacy_requests SET policy_id=$1,due_at=CASE WHEN due_at IS NULL THEN sg_privacy_deadline(received_at,$1) ELSE least(due_at,sg_privacy_deadline(received_at,$1)) END,updated_at=now() WHERE policy_id IS NULL AND country=$2 AND status IN('received','in_review')",[row.id,value.country],connection);
  await audit(principal,value.approve?'privacy_policy_approved':'privacy_policy_draft',row.id,{country:value.country,version:row.version},connection);return row;
 });
}
const requestId=z.string().min(1).max(100),reference=z.string().trim().min(10).max(2000);
export async function privacyAction(input:unknown,principal:Principal){
 authorized(principal);const data=parse(z.discriminatedUnion('action',[
  z.object({action:z.literal('verify'),id:requestId,method:z.enum(['authenticated_account','secure_channel']),reference}).strict(),
  z.object({action:z.literal('start'),id:requestId}).strict(),
  z.object({action:z.literal('route'),id:requestId,country:z.string().regex(/^[A-Z]{2}$/),reference}).strict(),
  z.object({action:z.literal('respond'),id:requestId,response:z.string().trim().min(20).max(4000),reference,outcome:z.enum(['fulfilled','partially_fulfilled','rejected'])}).strict(),
  z.object({action:z.literal('identity_rejection'),id:requestId,response:z.string().trim().min(20).max(4000),reference}).strict(),
 ]),input);
 return transaction(async connection=>{
  await query("SELECT pg_advisory_xact_lock_shared(hashtext('privacy-controller'))",[],connection);
  if(data.action==='route')await query("SELECT pg_advisory_xact_lock(hashtext('privacy-policy:'||$1))",[data.country],connection);
  const [row]=await query('SELECT * FROM privacy_requests WHERE id=$1 FOR UPDATE',[data.id],connection);if(!row)throw new HttpError(404,'Başvuru bulunamadı.');if(['responded','rejected'].includes(row.status))throw new HttpError(409,'Yanıtlanmış başvuru değiştirilemez.');
  if(data.action==='verify'){
   if(data.method==='authenticated_account'){
    const [account]=await query('SELECT email,"emailVerified" FROM "user" WHERE id=$1',[row.customer_id],connection);
    if(!account?.emailVerified||account.email.toLowerCase()!==row.email.toLowerCase())throw new HttpError(409,'Doğrulanmış hesap eşleşmesi bulunamadı; güvenli kanal incelemesi gerekir.');
   }
   await query("UPDATE privacy_requests SET identity_status='verified',assigned_to=$2,updated_at=now() WHERE id=$1",[row.id,principal.id],connection);
  }else if(data.action==='route'){
   const policy=await policyFor(data.country,connection);await query('UPDATE privacy_requests SET country=$2,policy_id=$3,due_at=CASE WHEN due_at IS NULL THEN sg_privacy_deadline(received_at,$3) WHEN $3::text IS NULL THEN due_at ELSE least(due_at,sg_privacy_deadline(received_at,$3)) END,updated_at=now() WHERE id=$1',[row.id,data.country,policy?.id??null],connection);
  }else{
   if(data.action!=='identity_rejection'&&row.identity_status!=='verified')throw new HttpError(409,'Önce başvuranın kimliğini güvenli kanaldan doğrulayın.');
   if(data.action==='identity_rejection'&&row.identity_status!=='pending')throw new HttpError(409,'Kimliği doğrulanmış başvuruda bu ret gerekçesi kullanılamaz.');
   const policy=row.policy_id?{id:row.policy_id}:await policyFor(row.country,connection);if(!policy)throw new HttpError(409,'Onaylı yanıt süresi ve saklama kuralı gerekiyor.');
   const [usable]=await query('SELECT id FROM privacy_policies WHERE id=$1 AND approved_by IS NOT NULL AND($2=true OR fixture=false)',[policy.id,local()],connection);if(!usable)throw new HttpError(409,'Bu ortamda kullanılabilir onaylı başvuru kuralı bulunamadı.');
   if(data.action==='start')await query("UPDATE privacy_requests SET status='in_review',assigned_to=$2,policy_id=$3,due_at=coalesce(due_at,sg_privacy_deadline(received_at,$3)),updated_at=now() WHERE id=$1",[row.id,principal.id,policy.id],connection);
   else{
    if(data.action==='respond'&&row.status!=='in_review')throw new HttpError(409,'Başvuruyu önce değerlendirmeye alın.');
    const outcome=data.action==='identity_rejection'?'rejected':data.outcome;
    await query('INSERT INTO privacy_responses(request_id,actor_id,body,outcome,external_reference) VALUES($1,$2,$3,$4,$5)',[row.id,principal.id,data.response,outcome,data.reference],connection);
    await query("UPDATE privacy_requests SET status=$2,updated_at=now() WHERE id=$1",[row.id,outcome==='rejected'?'rejected':'responded'],connection);
    const url=row.customer_id?new URL(`${row.locale==='en'?'/en':''}/veri-basvurusu?case=${encodeURIComponent(row.id)}`,process.env.APP_URL!).href:'';
    await queueNotice({email:row.email,reference:row.reference,url,locale:row.locale},`privacy-response:${row.id}`,connection);
   }
  }
  await query('INSERT INTO privacy_request_events(request_id,actor_id,type,reference) VALUES($1,$2,$3,$4)',[row.id,principal.id,data.action,'reference' in data?data.reference:''],connection);
  await audit(principal,`privacy_${data.action}`,row.id,{...('method' in data?{method:data.method}:{}),...('outcome' in data?{outcome:data.outcome}:{}),...('reference' in data?{referenceHash:hash(data.reference)}:{})},connection);return {id:row.id};
 });
}
export async function privacyAdmin(principal:Principal,filter:{page?:number;q?:string;id?:string;status?:string}){
 authorized(principal);const page=filter.page??1;if(!Number.isSafeInteger(page)||page<1||page>100000)throw new HttpError(400,'Sayfa numarası geçersiz.');
 const search=`%${(filter.q??'').slice(0,100).replace(/[\\%_]/g,'\\$&')}%`;
 const rows=await query("SELECT id,reference,email,type,summary,country,locale,status,identity_status,received_at,due_at,assigned_to,policy_id,(due_at<now() AND status IN('received','in_review')) overdue,count(*) OVER() total FROM privacy_requests WHERE(reference ILIKE $1 OR email ILIKE $1) AND($4::text IS NULL OR id=$4) AND($5::text IS NULL OR status=$5) ORDER BY CASE WHEN status IN('received','in_review') THEN 0 ELSE 1 END,due_at NULLS FIRST,received_at LIMIT $2 OFFSET $3",[search,25,(page-1)*25,filter.id??null,filter.status??null]);
 const total=rows[0]?.total??(await query("SELECT count(*) total FROM privacy_requests WHERE(reference ILIKE $1 OR email ILIKE $1) AND($2::text IS NULL OR id=$2) AND($3::text IS NULL OR status=$3)",[search,filter.id??null,filter.status??null]))[0].total;
 const controllers=await query('SELECT id,version,legal_name,address,email,status,fixture,created_at FROM privacy_controllers ORDER BY version DESC LIMIT 10');
 const policies=await query('SELECT id,country,version,unit,period_count,time_zone,source,retention_note,approved,fixture,created_at FROM privacy_policies ORDER BY country,version DESC LIMIT 100');
 const details=filter.id&&rows.length?{events:await query('SELECT type,reference,actor_id,created_at FROM privacy_request_events WHERE request_id=$1 ORDER BY created_at',[filter.id]),responses:await query('SELECT body,outcome,external_reference,created_at FROM privacy_responses WHERE request_id=$1',[filter.id])}:undefined;
 return {rows,total:Number(total),page,controllers,policies,details};
}
export async function assertPrivacyLaunchReady(connection:Connection=pool){
 const [controller]=await query("SELECT id FROM privacy_controllers WHERE status='approved' AND fixture=false",[],connection);
 if(!controller)throw new HttpError(503,'Canlı satış için veri sorumlusu kimliği doğrulanmalıdır.');
 const gaps=await query("SELECT c.code FROM country_rules c WHERE c.enabled=true AND c.fixture=false AND NOT EXISTS(SELECT 1 FROM privacy_policies p WHERE p.country=c.code AND p.controller_id=$1 AND p.approved=true AND p.approved_by IS NOT NULL AND p.fixture=false)",[controller.id],connection);
 if(gaps.length)throw new HttpError(503,'Satış ülkeleri için onaylı başvuru süresi ve saklama kuralları eksik.');
}
