#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/collect-native-marketplaces.py
# Açıklama   : İzinli kamu kataloğunu duraklatılabilir SQLite kuyruğuna alır; erişim engelinde kaynağı durdurur.
import argparse,hashlib,json,sqlite3,time,sys
from pathlib import Path
from urllib.parse import quote,parse_qs,urlsplit,urlencode,urlunsplit
from native_marketplaces import fetch,search_page,detail_page
sys.stdout.reconfigure(encoding='utf-8');ROOT=Path(__file__).resolve().parent.parent;HOME=Path('D:/sexogate-local-artifacts-20261114/private-installs/marketplace-catalog-20261116');HOME.mkdir(exist_ok=True);db=sqlite3.connect(HOME/'research.sqlite',timeout=30);db.row_factory=sqlite3.Row;db.execute('PRAGMA journal_mode=WAL')
db.executescript('''CREATE TABLE IF NOT EXISTS searches(id INTEGER PRIMARY KEY,url TEXT UNIQUE,page INTEGER DEFAULT 1,status TEXT DEFAULT 'pending',reported_total INTEGER,observed INTEGER DEFAULT 0,last_hash TEXT,error TEXT);CREATE TABLE IF NOT EXISTS products(platform TEXT,id TEXT,url TEXT,category TEXT,listing_json TEXT,detail_json TEXT,status TEXT DEFAULT 'pending',attempts INTEGER DEFAULT 0,error TEXT,updated_at INTEGER,PRIMARY KEY(platform,id));CREATE TABLE IF NOT EXISTS pages(search_id INTEGER,page INTEGER,sha256 TEXT,products INTEGER,at INTEGER,PRIMARY KEY(search_id,page));''')
seeds=['https://www.trendyol.com/fantezi-giyim-x-c109067']+['https://www.trendyol.com/sr?q='+quote(q)for q in ['seks oyuncağı','fantezi kostüm','fantezi zar','erotik oyun kartları','vibratör','mastürbatör','anal oyuncak','çiftlere özel oyun','kayganlaştırıcı','fantezi aksesuar','prezervatif']]
for url in seeds:db.execute('INSERT OR IGNORE INTO searches(url)VALUES(?)',(url,))
db.commit();p=argparse.ArgumentParser();p.add_argument('--search-pages',type=int,default=120);p.add_argument('--details',type=int,default=500);p.add_argument('--individual',action='store_true',help='Yalnız bilinen ürün detaylarını sırayla okur; engellenmiş arama uçlarını yeniden çağırmaz.');a=p.parse_args();source_blocked=bool(db.execute("SELECT 1 FROM searches WHERE status='access_blocked' LIMIT 1").fetchone())
if a.individual:
 a.search_pages=0
 source_blocked=bool(db.execute("SELECT 1 FROM products WHERE status='access_blocked' LIMIT 1").fetchone())
def report():
 result={'at':int(time.time()),'rightsBasis':'user_declared_20261116','database':str(HOME/'research.sqlite'),'source':'public_web','trendyol':{'searches':[dict(r)for r in db.execute('SELECT * FROM searches')],'discovered':db.execute('SELECT COUNT(*)FROM products').fetchone()[0],'details':db.execute("SELECT COUNT(*)FROM products WHERE status='ready'").fetchone()[0],'pending':db.execute("SELECT COUNT(*)FROM products WHERE status='pending'").fetchone()[0],'allProductsTransferred':False},'hepsiburada':{'status':'access_blocked','observedHttpStatus':403,'bypassAttempted':False},'published':0,'fulfilmentAcceptance':False}
 (ROOT/'.local/native-marketplace-collection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8');print(json.dumps({'discovered':result['trendyol']['discovered'],'details':result['trendyol']['details'],'pending':result['trendyol']['pending'],'allTransferred':False}),flush=True)
for step in range(0 if source_blocked else max(0,a.search_pages)):
 row=db.execute("SELECT * FROM searches WHERE status='pending' ORDER BY page,id LIMIT 1").fetchone()
 if not row:break
 parsed=urlsplit(row['url']);query=parse_qs(parsed.query);query['pi']=[str(row['page'])];url=urlunsplit((parsed.scheme,parsed.netloc,parsed.path,urlencode(query,doseq=True),''))
 try:
  raw=fetch(url);data=search_page(raw);digest=hashlib.sha256(json.dumps(data['rawIds']).encode()).hexdigest()
  if row['last_hash']==digest and data['rawIds']:db.execute("UPDATE searches SET status='result_limit',error='REPEATED_PAGE' WHERE id=?",(row['id'],));db.commit();continue
  for product in data['products']:db.execute('INSERT OR IGNORE INTO products(platform,id,url,category,listing_json,updated_at)VALUES(?,?,?,?,?,?)',('trendyol',product['id'],product['url'],json.dumps(product['category'],ensure_ascii=False),json.dumps(product,ensure_ascii=False),int(time.time())))
  db.execute('INSERT OR REPLACE INTO pages VALUES(?,?,?,?,?)',(row['id'],row['page'],hashlib.sha256(raw).hexdigest(),len(data['products']),int(time.time())));db.execute('UPDATE searches SET page=page+1,reported_total=?,observed=observed+?,last_hash=?,status=? WHERE id=?',(data['reportedTotal'],len(data['products']),digest,'pending'if data['rawIds']else'exhausted',row['id']));db.commit()
 except PermissionError as e:
  db.execute("UPDATE searches SET status='access_blocked',error=? WHERE status='pending'",(str(e),));db.commit();source_blocked=True;report();break
 except Exception as e:db.execute("UPDATE searches SET status='needs_review',error=? WHERE id=?",(type(e).__name__,row['id']));db.commit()
 if step%12==11:report()
 time.sleep(1)
if not source_blocked:
 for step in range(max(0,a.details)):
  row=db.execute("SELECT * FROM products WHERE status='pending' AND attempts<3 ORDER BY attempts,updated_at,rowid LIMIT 1").fetchone()
  if not row:break
  try:
   raw=fetch(row['url']);(HOME/'raw').mkdir(exist_ok=True);(HOME/'raw'/(row['id']+'.html')).write_bytes(raw);detail=detail_page(raw,row['url']);assert detail['sourceId']==row['id'];db.execute("UPDATE products SET detail_json=?,status='ready',attempts=attempts+1,updated_at=?,error=NULL WHERE platform=?AND id=?",(json.dumps(detail,ensure_ascii=False),int(time.time()),row['platform'],row['id']));db.commit()
  except PermissionError as e:
   db.execute("UPDATE products SET status='access_blocked',error=?,attempts=attempts+1,updated_at=?WHERE platform=?AND id=?",(str(e),int(time.time()),row['platform'],row['id']));db.commit();source_blocked=True;report();break
  except Exception as e:db.execute("UPDATE products SET status=CASE WHEN attempts>=2 THEN 'needs_review' ELSE 'pending' END,attempts=attempts+1,error=? WHERE platform=? AND id=?",(type(e).__name__,row['platform'],row['id']));db.commit()
  if step%25==24:report()
  time.sleep(1)
report();db.close()
