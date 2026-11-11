/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/migrate.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import pg from "pg";
import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

export async function migrate(databaseUrl=process.env.DATABASE_URL) {
 if(!databaseUrl) throw new Error("DATABASE_URL is required");
 const client=new pg.Client({connectionString:databaseUrl});
 await client.connect();
 try {
  await client.query("SELECT pg_advisory_lock(8401102026)");
  await client.query("CREATE TABLE IF NOT EXISTS schema_migrations(name text PRIMARY KEY,checksum text NOT NULL,applied_at timestamptz NOT NULL DEFAULT now())");
  const files=(await readdir(resolve("migrations"))).filter(f=>f.endsWith(".sql")).sort();
  for(const name of files) {
   const sql=await readFile(resolve("migrations",name),"utf8");
   const checksum=createHash("sha256").update(sql).digest("hex");
   const existing=await client.query("SELECT checksum FROM schema_migrations WHERE name=$1",[name]);
   if(existing.rows.length) {
    if(existing.rows[0].checksum!==checksum) throw new Error(`Migration checksum mismatch: ${name}`);
    continue;
   }
   await client.query("BEGIN");
   try { await client.query(sql); await client.query("INSERT INTO schema_migrations(name,checksum) VALUES($1,$2)",[name,checksum]); await client.query("COMMIT"); }
   catch(error) { await client.query("ROLLBACK");throw error; }
   console.log(`Applied ${name}`);
  }
 } finally { await client.query("SELECT pg_advisory_unlock(8401102026)"); await client.end(); }
}
if(process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href) {
 migrate().catch(()=>{console.error("Migration failed; inspect database configuration and migration checksums.");process.exitCode=1;});
}
