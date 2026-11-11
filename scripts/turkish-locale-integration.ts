/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/turkish-locale-integration.ts
 * Açıklama   : Yalıtılmış yerel veritabanında Türkçe metin, arama ve dil sıralaması doğrulaması.
 */
import assert from "node:assert/strict";
import { randomBytes } from "node:crypto";
import pg from "pg";
import { migrate } from "./migrate";

// PostgreSQL ICU locale collations and COLLATE expression semantics:
// https://www.postgresql.org/docs/18/collation.html#COLLATION-MANAGING-ICU
const original = new URL(process.env.TEST_DATABASE_URL ?? process.env.DATABASE_URL ?? "");
assert(["127.0.0.1", "localhost", "[::1]"].includes(original.hostname), "Yalnız yerel test veritabanı kullanılabilir.");
const databaseName = `sexsogate_${randomBytes(6).toString("hex")}_locale_test`;
assert(/^sexsogate_[a-f0-9]{12}_locale_test$/.test(databaseName), "Test veritabanı adı güvenli değil.");
const controlUrl = new URL(original);
controlUrl.pathname = "/postgres";
const control = new pg.Client({ connectionString: controlUrl.href });
await control.connect();
let created = false;
let pool: pg.Pool | undefined;
try {
  // Deliberately use C as the database default: ordering must come from the request locale.
  await control.query(`CREATE DATABASE "${databaseName}" TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C'`);
  created = true;
  original.pathname = `/${databaseName}`;
  process.env.DATABASE_URL = original.href;
  process.env.APP_ENV = "test";
  await migrate(original.href);
  const database = await import("../src/server/db");
  pool = database.pool;
  const { listProducts } = await import("../src/server/commerce/catalog");
  const collations = await pool.query<{ collname: string }>("SELECT collname FROM pg_collation WHERE collname=ANY($1::text[])", [["tr-x-icu", "en-x-icu"]]);
  assert.deepEqual(collations.rows.map(row => row.collname).sort(), ["en-x-icu", "tr-x-icu"], "PostgreSQL Türkçe ve İngilizce ICU desteği gereklidir.");
  const names = ["Çeşme", "Iğdır", "İstanbul", "İzmir", "Şişli"];
  const sentence = "Hamza ÖZBALKAN İstanbul İzmir Iğdır Şişli Çeşme İç Giyim Ölçü ve Özellikler Güvenli Alışveriş";
  const searches = ["cesme", "igdir", "istanbul", "izmir", "sisli"];
  await pool.query("INSERT INTO categories(slug,name,name_en) VALUES('locale-test','Dil doğrulaması','Locale verification')");
  for (const [index, name] of names.entries()) {
    const product = await pool.query<{ id: string }>("INSERT INTO products(slug,name,name_en,description,description_en,category,image,status,care,fixture) VALUES($1,$2,$3,$4,$5,'locale-test','/media/atelier-01.svg','published',$6,true) RETURNING id", [`locale-${index}`, name, `${name} test collection`, "Yalnız yalıtılmış dil testi.", "Isolated locale test only.", sentence]);
    const variant = await pool.query<{ id: string }>("INSERT INTO variants(product_id,sku,name,name_en,price_minor,currency) VALUES($1,$2,'Standart','Standard',10000,'TRY') RETURNING id", [product.rows[0].id, `LOCALE-${index}`]);
    await pool.query("INSERT INTO variant_prices(variant_id,currency,amount_minor) VALUES($1,'TRY',10000)", [variant.rows[0].id]);
  }
  const stored = await pool.query<{ name: string; care: string; care_utf8: string }>("SELECT name,care,encode(convert_to(care,'UTF8'),'hex') care_utf8 FROM products ORDER BY slug");
  assert.deepEqual(stored.rows.map(row => row.name), names);
  for (const row of stored.rows) {
    assert.equal(row.care, sentence);
    assert.equal(row.care_utf8, Buffer.from(sentence, "utf8").toString("hex"));
  }
  console.log("PASS: exact Turkish names and complete accented sentence persist as UTF-8");
  for (const [index, q] of searches.entries()) {
    const found = await listProducts({ q, locale: "tr", currency: "TRY" });
    assert.deepEqual(found.map(product => product.name), [names[index]], `Türkçe arama: ${q}`);
  }
  const afterSearch = await pool.query<{ name: string }>("SELECT name FROM products ORDER BY slug");
  assert.deepEqual(afterSearch.rows.map(row => row.name), names);
  console.log("PASS: five ASCII search queries find Turkish names without changing stored text");
  const turkish = await listProducts({ sort: "name", locale: "tr", currency: "TRY" });
  assert.deepEqual(turkish.map(product => product.name), [...names].sort(new Intl.Collator("tr-TR").compare), "Katalog ad sıralaması Türkçe alfabesini izlemeli.");
  console.log("PASS: Turkish catalog ordering matches Intl.Collator(tr-TR) with database default C");
  const english = await listProducts({ sort: "name", locale: "en", currency: "TRY" });
  const englishNames = names.map(name => `${name} test collection`);
  assert.deepEqual(english.map(product => product.nameEn), englishNames.sort(new Intl.Collator("en").compare));
  console.log("PASS: English catalog ordering uses the English locale");
  await assert.rejects(()=>listProducts({ sort: 'name COLLATE "C"; DROP TABLE products;--', locale: "tr", currency: "TRY" }),{code:'INVALID_CATALOG_FILTER'});
  assert.equal((await pool.query("SELECT count(*)::int n FROM products")).rows[0].n, names.length);
  console.log("PASS: unrecognized sort input cannot become a SQL collation or statement");
  console.log("Turkish locale integration: 5 checks passed.");
} finally {
  await pool?.end();
  if (created) await control.query(`DROP DATABASE "${databaseName}"`);
  await control.end();
}
