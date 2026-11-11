/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/commerce/jobs.ts
 * Açıklama   : Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.
 */
import { query, transaction } from "../db";
import { expireReservations } from "./orders";

export type JobHandlers=Record<string,(payload:Record<string,unknown>)=>Promise<void>>;
export async function processJobsOnce(handlers:JobHandlers={}):Promise<number> {
 const jobs=await transaction(async connection=>query(`WITH claim AS(
  SELECT id FROM jobs WHERE(status='pending' AND available_at<=now())OR(status='running' AND lease_until<now())
  ORDER BY available_at,id FOR UPDATE SKIP LOCKED LIMIT 10)
  UPDATE jobs j SET status='running',attempts=j.attempts+1,lease_until=now()+interval '5 minutes'
  FROM claim WHERE j.id=claim.id RETURNING j.*`,[],connection));
 for(const job of jobs) {
  try {
   if(job.type==="reservation.expire")await expireReservations();
   else if(handlers[job.type])await handlers[job.type](job.payload);
   else throw Object.assign(new Error("Job handler not configured"),{code:"HANDLER_NOT_CONFIGURED"});
   await query("UPDATE jobs SET status='completed',completed_at=now(),lease_until=null,last_error=null WHERE id=$1 AND status='running' AND attempts=$2",[job.id,job.attempts]);
  } catch(error) {
   // Error codes only: provider errors may contain addresses, messages or secrets.
   const raw=(error as {code?:string}).code??"JOB_FAILED";
   const code=/^[A-Z_0-9]{1,80}$/.test(raw)?raw:"JOB_FAILED";
   await query("UPDATE jobs SET status=CASE WHEN attempts>=max_attempts THEN 'failed' ELSE 'pending' END,available_at=now()+make_interval(secs=>least(3600,30*power(2,attempts)::int)),lease_until=null,last_error=$2 WHERE id=$1 AND attempts=$3",[job.id,code,job.attempts]);
  }
 }
 return jobs.length;
}
