#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native-catalog-review.py
# Açıklama   : İlk vitrin adaylarının değiştirilmemiş fotoğraflarını görsel inceleme sayfalarında gösterir.
import html,json
from pathlib import Path
from playwright.sync_api import sync_playwright
HOME=Path('D:/sexogate-local-artifacts-20261114/private-installs/native-catalog-20261115');source=json.loads((HOME/'catalog-source.json').read_text('utf8'));images=json.loads((HOME/'images.json').read_text('utf8'));work={w['id']:w for w in source['workbench']};candidates=[]
def eligible(p):
 w=work[p['id']];return not p['eligibilityHold']and p['salePriceMinor']is not None and w['source']['publicInStock']is True and w['sourceImages']and'file'in images.get(w['sourceImages'][0],{})
for vendor in ['liona','sistina']:
 rows=[p for p in source['products']if work[p['id']]['source']['vendor']==vendor and eligible(p)];rows.sort(key=lambda p:('gecelik'not in p['name']['tr'].lower(),p['id']));candidates.extend(rows[:10 if vendor=='liona'else 5])
for group in ['toys','couples','accessories','care','gifts']:candidates.extend([p for p in source['products']if p['categoryIds']==['sg_'+group]and eligible(p)][:4])
folder=HOME/'review';folder.mkdir(exist_ok=True);report=[]
with sync_playwright()as pw:
 browser=pw.chromium.launch();page=browser.new_page(viewport={'width':1700,'height':1150},device_scale_factor=1)
 for offset in range(0,len(candidates),10):
  batch=candidates[offset:offset+10];cards=[]
  for p in batch:
   w=work[p['id']];image=images[w['sourceImages'][0]];cards.append('<article><img src="'+(HOME/'media'/image['file']).as_uri()+'"><strong>'+html.escape(p['name']['tr'])+'</strong><small>'+p['id']+'</small></article>');report.append({'id':p['id'],'sourceUrl':w['sourceImages'][0],'sha256':image['sha256'],'file':image['file'],'sheet':offset//10})
  file=folder/(str(offset//10)+'.html');file.write_text('<!doctype html><meta charset="utf-8"><style>body{margin:18px;background:#eee;font:13px Arial}.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}article{padding:10px;background:white}img{width:100%;height:420px;object-fit:contain}strong,small{display:block;margin:8px 0}</style><div class="grid">'+''.join(cards)+'</div>',encoding='utf8');page.goto(file.as_uri());page.locator('img').evaluate_all('(nodes)=>Promise.all(nodes.map(n=>n.decode()))');page.screenshot(path=str(folder/(str(offset//10)+'.png')),full_page=True)
 browser.close()
(folder/'candidates.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'candidates':len(candidates),'sheets':(len(candidates)+9)//10,'reviewed':False}))
