#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/collect-native-marketplaces-next.py
# Açıklama   : İlk yayın adayını değiştirmeden sonraki ürün sayfalarını ayrı, kalıcı ve tek istekli kuyruğa toplar.
import hashlib,json,math,sqlite3,time
from pathlib import Path
from native_marketplaces import fetch,search_page,detail_page
ROOT=Path(__file__).resolve().parent.parent;BASE=Path('D:/sexogate-local-artifacts-20261114/private-installs');OLD=BASE/'marketplace-catalog-20261116';HOME=BASE/'marketplace-catalog-20261116-next';HOME.mkdir(exist_ok=True);(HOME/'raw').mkdir(exist_ok=True)
file=HOME/'research.sqlite'
if not file.exists():
 with sqlite3.connect(OLD/'research.sqlite')as source,sqlite3.connect(file)as target:source.backup(target)
 for p in(OLD/'raw').glob('*.html'):
  import os
  if not(HOME/'raw'/p.name).exists():os.link(p,HOME/'raw'/p.name)
db=sqlite3.connect(file);db.row_factory=sqlite3.Row;db.executescript("CREATE TABLE IF NOT EXISTS next_pages(page INTEGER PRIMARY KEY,reported_total INTEGER,raw_ids_json TEXT,status TEXT,sha256 TEXT,at INTEGER);CREATE TABLE IF NOT EXISTS next_state(key TEXT PRIMARY KEY,value TEXT);")
def report(state):
 counts=dict(db.execute('SELECT status,COUNT(*)FROM products GROUP BY status').fetchall());r={'state':state,'database':str(file),'source':'trendyol_individual_pages','sourceCategory':'seks-oyuncaklari-y-s8150','pages':db.execute('SELECT COUNT(*)FROM next_pages').fetchone()[0],'products':counts,'firstReleaseDatasetChanged':False,'published':0,'allCategoriesTransferred':False,'at':int(time.time())};(ROOT/'.local/native-marketplace-next-collection.json').write_text(json.dumps(r,indent=2),'utf8');print(json.dumps({'state':state,'products':counts,'pages':r['pages']}),flush=True)
blocked=db.execute("SELECT value FROM next_state WHERE key='blocked'").fetchone()
if blocked:report('access_blocked');raise SystemExit(2)
seen=set();page=1;maximum=30
while page<=maximum:
 prior=db.execute('SELECT *FROM next_pages WHERE page=?',(page,)).fetchone()
 if prior:raw_ids=json.loads(prior['raw_ids_json']);maximum=min(30,math.ceil(prior['reported_total']/36));seen.update(raw_ids);page+=1;continue
 try:
  raw=fetch('https://www.trendyol.com/seks-oyuncaklari-y-s8150?pi='+str(page));data=search_page(raw)
  if data['page']!=page:raise ValueError('SOURCE_PAGINATION_MISMATCH')
  if set(data['rawIds'])<=seen:report('result_limit');break
  seen.update(data['rawIds']);maximum=min(30,math.ceil(data['reportedTotal']/36))
  for p in data['products']:db.execute('INSERT OR IGNORE INTO products(platform,id,url,category,listing_json,updated_at)VALUES(?,?,?,?,?,?)',('trendyol',p['id'],p['url'],json.dumps(p['category'],ensure_ascii=False),json.dumps(p,ensure_ascii=False),int(time.time())))
  db.execute('INSERT INTO next_pages VALUES(?,?,?,?,?,?)',(page,data['reportedTotal'],json.dumps(data['rawIds']),'observed',hashlib.sha256(raw).hexdigest(),int(time.time())));db.commit();report('discovering');page+=1;time.sleep(1)
 except PermissionError as e:db.execute("INSERT OR REPLACE INTO next_state VALUES('blocked',?)",(str(e),));db.commit();report('access_blocked');raise SystemExit(2)
for row in db.execute("SELECT *FROM products WHERE status='pending'AND attempts<3 ORDER BY id LIMIT 1000").fetchall():
 try:
  raw=fetch(row['url']);(HOME/'raw'/(row['id']+'.html')).write_bytes(raw);d=detail_page(raw,row['url']);assert d['sourceId']==row['id'];db.execute("UPDATE products SET detail_json=?,status='ready',attempts=attempts+1,updated_at=?WHERE platform=?AND id=?",(json.dumps(d,ensure_ascii=False),int(time.time()),row['platform'],row['id']));db.commit()
 except PermissionError as e:db.execute("INSERT OR REPLACE INTO next_state VALUES('blocked',?)",(str(e),));db.commit();report('access_blocked');raise SystemExit(2)
 except Exception as e:db.execute("UPDATE products SET status='needs_review',error=?,attempts=attempts+1 WHERE platform=?AND id=?",(type(e).__name__,row['platform'],row['id']));db.commit()
 report('reading_individual_products');time.sleep(1)
report('collection_pass_finished');db.close()
