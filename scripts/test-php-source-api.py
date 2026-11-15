#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-php-source-api.py
# Açıklama   : Gerçek API yanıtlarını yalnız rastgele yerel test DB'sinde tekrar işler.
import argparse, json, os, subprocess
from pathlib import Path

root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser();parser.add_argument('--capture-root',type=Path,required=True);args=parser.parse_args()
folder=args.capture_root.resolve()/'xshopum';report=json.loads((folder/'report.json').read_text('utf8'))
assert report['complete'] and report['errors']==0 and report['allMetadataParsed']
env=os.environ.copy()
for line in (root/'.local/mysql/mysql.env').read_text('utf8').splitlines():
 if line.startswith('MYSQL_TEST_ADMIN_URL='):
  value=line.split('=',1)[1];env['MYSQL_TEST_ADMIN_URL']=json.loads(value) if value.startswith('"') else value
env['SG_API_REPLAY_CACHE']=str(folder/'cache');env['SG_API_REPLAY_PRODUCTS']=str(report['productUrls']);env['SG_API_REPLAY_CATEGORIES']=str(report['categoryUrls'])
code=r'''<?php
declare(strict_types=1);
require 'vendor/autoload.php';require 'tests/TestDatabase.php';
$f=new TestDatabase();$actor=new Sexogate\Principal('recorded-api-test','admin',true);$cache=getenv('SG_API_REPLAY_CACHE');
$totals=['products'=>(int)getenv('SG_API_REPLAY_PRODUCTS'),'categories'=>(int)getenv('SG_API_REPLAY_CATEGORIES')];
$source=new Sexogate\SourceApi($f->db,$f->config,function($resource,$page)use($cache,$totals){$url=Sexogate\SupplierApiHttp::endpoint($resource,$page);$path=$cache.'/'.hash('sha256',$url).'.body';if(!is_file($path))throw new RuntimeException('RECORDED_RESPONSE_MISSING');return ['status'=>200,'total'=>$totals[$resource],'body'=>file_get_contents($path)];});
$r=$source->start('xshopum','recorded-real-api-replay',$actor);
for($n=0;$n<202;$n++){$run=$source->run($r['id'],$actor);if($run['status']!=='running')break;$source->process($r['id'],$run['resource'],(int)$run['page'],1);}
$run=$source->run($r['id'],$actor);$batch=(new Sexogate\SourceCatalog($f->db,$f->config))->listing($actor)[0]??null;
if($run['status']!=='complete'||!$batch||(int)$batch['product_count']!==$totals['products']||(int)$batch['category_count']!==$totals['categories'])throw new RuntimeException('RECORDED_CATALOG_MISMATCH');
foreach(['products','inventory_balance','supplier_offers'] as $table)if((int)$f->db->one('SELECT COUNT(*) n FROM '.$table)['n']!==0)throw new RuntimeException('UNEXPECTED_LIVE_WRITE');
foreach($f->db->all('SELECT payload FROM source_catalog_records') as $row){$payload=json_decode($row['payload'],true,32,JSON_THROW_ON_ERROR);if($payload['supplierQuantity']!==null)throw new RuntimeException('UNVERIFIED_QUANTITY');}
echo json_encode(['mode'=>'recorded-real-api-response-replay','isolatedLocalDatabase'=>true,'products'=>$totals['products'],'categories'=>$totals['categories'],'pages'=>(int)$f->db->one('SELECT COUNT(*) n FROM source_api_pages')['n'],'warehouseWrites'=>0,'publishedProducts'=>0,'serverNetworkAccessProved'=>false],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);
'''
result=subprocess.run([str(root/'.local/php-runtime/php.exe')],input=code.encode('utf8'),cwd=root/'hosting/php',env=env,capture_output=True)
if result.returncode:
 print('RECORDED_API_REPLAY_FAILED',result.stdout.decode('utf8','replace')[:1200],result.stderr.decode('utf8','replace')[:1200]);raise SystemExit(1)
evidence=json.loads(result.stdout);(root/'.local/php-source-api-replay.json').write_text(json.dumps(evidence,indent=2),encoding='utf8');print(json.dumps(evidence))
