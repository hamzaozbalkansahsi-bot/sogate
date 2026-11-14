#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/build-php-stacked-logo.py
# Açıklama   : Onaylı simge ve yazı geometrisini bozmadan simgeyi yazının üzerine ortalar.
import copy,json,xml.etree.ElementTree as ET
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent.parent;source=root/'hosting/php/public/assets/brand';target=root/'public/brand/app';target.mkdir(exist_ok=True);ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True);page=browser.new_page()
 try:
  for suffix,color in [('', '#5A0A20'),('-light','#FBF4EF')]:
   horizontal=ET.fromstring((source/('logo-horizontal-light.svg' if suffix else 'logo-horizontal.svg')).read_text('utf8'));word=copy.deepcopy([e for e in horizontal if e.tag==f'{{{ns}}}g'][-1]);word.attrib={'id':'wordmark','fill':color};symbol=ET.fromstring((source/('symbol-light.svg' if suffix else 'symbol-dark.svg')).read_text('utf8'));mark=ET.Element(f'{{{ns}}}g',{'id':'monogram'})
   for child in symbol:
    if child.tag not in [f'{{{ns}}}title',f'{{{ns}}}defs']:mark.append(copy.deepcopy(child))
   logo=ET.Element(f'{{{ns}}}svg',{'width':'690','height':'310','viewBox':'0 0 690 310','role':'img','aria-label':'SEXOGATE'});logo.extend([mark,word]);page.set_content(ET.tostring(logo,encoding='unicode'));bounds=page.evaluate("()=>Object.fromEntries(['monogram','wordmark'].map(id=>{const b=document.getElementById(id).getBBox();return[id,{x:b.x,y:b.y,w:b.width,h:b.height}]}))")
   m=bounds['monogram'];w=bounds['wordmark'];scale=.64;mark.set('transform',f'translate({345-scale*(m["x"]+m["w"]/2)} {18-scale*m["y"]}) scale({scale})');word.set('transform',f'translate({345-(w["x"]+w["w"]/2)} {202-w["y"]})');logo.set('height',str(round(202+w['h']+25,3)));logo.set('viewBox',f'0 0 690 {202+w["h"]+25:.3f}');
   page.set_content(ET.tostring(logo,encoding='unicode'));box=page.evaluate("()=>{const b=document.querySelector('svg').getBBox();return{x:b.x,y:b.y,w:b.width,h:b.height}}")
   padding=12;logo.set('viewBox',f'{box["x"]-padding:.3f} {box["y"]-padding:.3f} {box["w"]+2*padding:.3f} {box["h"]+2*padding:.3f}');logo.set('width',f'{box["w"]+2*padding:.3f}');logo.set('height',f'{box["h"]+2*padding:.3f}')
   name='logo-stacked'+suffix+'.svg';data='<!-- Proje: SEXOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN | Dosya: public/brand/app/'+name+' | Açıklama: Simge üstte, yazı altta merkezli onaylı geometri. -->\n'+ET.tostring(logo,encoding='unicode');(target/name).write_text(data,encoding='utf8');(source/'app'/name).write_text(data,encoding='utf8');page.set_content(data);metrics=page.evaluate("()=>{const a=document.getElementById('monogram').getBoundingClientRect(),b=document.getElementById('wordmark').getBoundingClientRect();return {centerDifference:Math.abs(a.x+a.width/2-b.x-b.width/2),symbolBottom:a.bottom,wordTop:b.top}}")
   assert metrics['centerDifference']<.01 and metrics['symbolBottom']<metrics['wordTop'],metrics;print(name,json.dumps(metrics))
 finally:browser.close()
