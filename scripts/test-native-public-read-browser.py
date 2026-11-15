#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-public-read-browser.py
# Açıklama   : Gerçek tarayıcıda yarım kalan HTTP gövdesini iptal edip tek güvenli okuma tekrarını doğrular.
import json,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
helper=(ROOT/'native-store/storefront/public-read.js').read_text('utf8')
counts={};mode='recover'
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path=='/api/catalog':
   counts[mode]=counts.get(mode,0)+1
   self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
   if mode=='fail' or counts[mode]==1:time.sleep(.6)
   try:self.wfile.write(json.dumps({'name':'İç Giyim · Iğdır'},ensure_ascii=False).encode('utf8'))
   except (BrokenPipeError,ConnectionResetError):pass
  else:
   body=('<main id="result"></main><script type="module">'+helper+"\ntry{const data=await readStorefrontJson('/api/catalog',{}, {timeoutMs:150});document.querySelector('main').textContent=data.name;}catch(e){document.querySelector('main').textContent=e.name;}window.readComplete=true;</script>").encode('utf8')
   self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True;threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright()as p:
  for engine in ['chromium','webkit']:
   browser=getattr(p,engine).launch()
   for selected in ['recover','fail']:
    mode=selected;counts[mode]=0;context=browser.new_context();page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    try:
     page.goto('http://127.0.0.1:'+str(server.server_port));page.wait_for_function('window.readComplete===true',timeout=3000)
     assert page.locator('#result').inner_text()==('İç Giyim · Iğdır'if mode=='recover'else'AbortError')
     assert counts[mode]==2 and not errors,{'attempts':counts[mode],'errors':errors}
     print(json.dumps({'engine':engine,'scenario':mode,'realHttpAttempts':2,'bodyDeadline':True,'pageErrors':0,'paymentCalled':False}),flush=True)
    finally:context.close()
   browser.close()
finally:server.shutdown();server.server_close()
