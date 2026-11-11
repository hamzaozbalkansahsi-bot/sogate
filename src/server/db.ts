/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/db.ts
 * Açıklama   : PostgreSQL bağlantısı, parametreli sorgu ve işlem tekrarları.
 */
import pg, { type PoolClient, type QueryResultRow } from "pg";
import { Kysely, PostgresDialect } from "kysely";

// Domain amounts are bounded below Number.MAX_SAFE_INTEGER by SQL constraints.
pg.types.setTypeParser(20, (value: string) => Number(value));
const globalDb = globalThis as unknown as {sexsogatePool?: pg.Pool};
export const pool = globalDb.sexsogatePool ?? new pg.Pool({
  connectionString: process.env.DATABASE_URL,
  max: 12, connectionTimeoutMillis: 5000, idleTimeoutMillis: 30000,
  application_name: "sexsogate",
});
if (process.env.NODE_ENV !== "production") globalDb.sexsogatePool = pool;
export const db = new Kysely<Record<string, never>>({dialect: new PostgresDialect({pool})});
export type Connection = Pick<PoolClient,"query">;
export async function query<T extends QueryResultRow=QueryResultRow>(text:string, values:unknown[]=[], connection:Connection=pool):Promise<T[]> {
  return (await connection.query<T>(text, values)).rows;
}
export async function transaction<T>(work:(client:PoolClient)=>Promise<T>, retries=3):Promise<T> {
  for(let attempt=0;;attempt++) {
    const client=await pool.connect();
    try {
      await client.query("BEGIN");
      const result=await work(client);
      await client.query("COMMIT");
      return result;
    } catch(error) {
      await client.query("ROLLBACK");
      const code=(error as {code?:string}).code;
      if(attempt>=retries || !["40001","40P01"].includes(code??"")) throw error;
    } finally { client.release(); }
    await new Promise(resolve=>setTimeout(resolve,20+Math.random()*50));
  }
}
