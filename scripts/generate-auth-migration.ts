/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/generate-auth-migration.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import { getMigrations } from 'better-auth/db/migration';
import { writeFile, access } from 'node:fs/promises';
import { authOptions } from '../src/server/auth';
import { pool } from '../src/server/db';
try {
  try { await access('migrations/002_auth.sql');throw new Error('Migration zaten var; üzerine yazma yasak.'); }catch(error){if((error as NodeJS.ErrnoException).code!=='ENOENT')throw error;}
  const plan=await getMigrations(authOptions());
  await writeFile('migrations/002_auth.sql','-- SEXSOGATE Better Auth 1.7.20 resmi şeması; üretilmiş migration.\n'+await plan.compileMigrations());
  console.log('Better Auth migration üretildi.');
}finally{await pool.end();}
