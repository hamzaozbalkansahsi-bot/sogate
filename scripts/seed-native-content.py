#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/seed-native-content.py
# Açıklama   : Yalnız mevcut SEXOGATE rehberlerini özgün NODENO içerik motorunun yerel deposuna bağlar.
import hashlib,html,json,subprocess,textwrap
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent;build=json.loads((ROOT/'.local/native-store-build.json').read_text('utf8'));private=Path(build['private']);public=Path(build['public']);storage=Path(build['storage']);php=ROOT/'.local/php-runtime/php.exe'
assert build['localOnly'] and build['checkoutEnabled'] is False
code=r"require 'hosting/php/vendor/autoload.php';$c=Sexogate\Config::load('hosting/php/config.local.json');$d=new Sexogate\Database($c);$e=new Sexogate\Editorial($d,$c);$out=[];foreach($e->listing('tr')['rows'] as $r)$out[]=$e->article($r['slug'],'tr');echo json_encode($out,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);"
result=subprocess.run([str(php),'-r',code],cwd=ROOT,capture_output=True)
if result.returncode:raise RuntimeError('SEXOGATE_GUIDES_READ_FAILED')
guides=json.loads(result.stdout);articles=[]
for guide in guides:
 headings=[s['title'] or guide['title'] for s in guide['sections']][:3];parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800"><rect width="1200" height="800" fill="#FBF4EF"/><text x="80" y="110" font-family="Georgia,serif" font-size="40" fill="#5A0A20">SEXOGATE</text><path d="M80 150H1120" stroke="#E7B4BD" stroke-width="2"/>']
 for i,heading in enumerate(headings):
  x=80+i*360;parts.append(f'<rect x="{x}" y="270" width="320" height="310" rx="130" fill="#F3E6E8"/><text x="{x+160}" y="355" text-anchor="middle" font-family="Georgia,serif" font-size="32" fill="#5A0A20">{i+1}</text>')
  for n,line in enumerate(textwrap.wrap(heading,20)[:4]):parts.append(f'<text x="{x+160}" y="{415+n*38}" text-anchor="middle" font-family="Georgia,serif" font-size="26" fill="#24191D">{html.escape(line)}</text>')
 parts.append('</svg>');raw=''.join(parts).encode('utf8');url='/assets/blog/sexogate-'+guide['slug']+'.svg';dest=public/url.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 articles.append({'id':'sexogate-'+guide['slug'],'slug':guide['slug'],'category':'care' if 'bakim' in guide['slug'] else 'planning','title':guide['title'],'description':guide['summary'],'keywords':[],'intro':guide['summary'],'sections':[{'heading':s['title'] or guide['title'],'paragraphs':s['paragraphs']} for s in guide['sections']],'checklist':[],'tool':'','related':[],'sources':[],'image':{'url':url,'alt':guide['title']+' · Bölüm akışı','width':1200,'height':800,'kind':'original-diagram','sha256':hashlib.sha256(raw).hexdigest()}})
assert articles,'EXISTING_SEXOGATE_GUIDES_REQUIRED'
bank={'schemaVersion':1,'timezone':'Europe/Istanbul','dailySlots':['09:30','18:30'],'launchImmediately':True,'articles':articles}
(private/'blog-bank.json').write_text(json.dumps(bank,ensure_ascii=False),encoding='utf8')
for locale,title,paragraphs in [
 ('tr','Üyelik koşulları taslağı',['Hesabınız, adresleriniz ve siparişlerinize güvenli erişim sağlamak için kullanılır. Pazarlama izni üyelikten ve satın almadan ayrıdır.','Hukuki satıcı, veri sorumlusu ve işletme bilgileri doğrulanmadan bu taslak yürürlüğe girmez. Gerçek tahsilat kapalıdır.']),
 ('en','Draft membership terms',['Your account provides secure access to your addresses and orders. Marketing permission is separate from membership and purchase.','These draft terms cannot take effect until the legal seller, data controller and business details are verified. Live charging is disabled.'])]:
 corpus={'locale':locale,'version':'sexogate-local-draft-20261115','status':'draft','documents':[{'id':'membership','title':title,'status':'draft','sections':[{'heading':title,'paragraphs':paragraphs}]}]}
 (private/('site-documents.'+locale+'.json')).write_text(json.dumps(corpus,ensure_ascii=False),encoding='utf8')
code="require $argv[1].'/blog-worker.php';echo json_encode(nodenoBlogTick($argv[2],$argv[1],$argv[3],time()));"
result=subprocess.run([str(php),'-d','extension=pdo_sqlite','-d','extension=sqlite3','-r',code,str(private),str(storage),str(public)],capture_output=True)
if result.returncode:raise RuntimeError('ORIGINAL_BLOG_WORKER_FAILED: '+result.stderr.decode('utf8','replace')[:500])
print(json.dumps({'source':'existing SEXOGATE local CMS','guides':len(articles),'donorArticlesCopied':False,'worker':json.loads(result.stdout)}))
