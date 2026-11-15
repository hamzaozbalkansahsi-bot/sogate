#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-browser-ready.py
# Açıklama   : Gerçek HTTP ile kritik veri ve yükleme ekranı engellerini, isteğe bağlı kur isteğinden bağımsız sınar.
import json,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright,TimeoutError
from native_browser_ready import NativePageReadiness

release=threading.Event();catalog_ready=threading.Event()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path in ['/api/exchange-rates','/api/critical']:release.wait(10);body=b'{}';mime='application/json'
  elif self.path=='/api/catalog':catalog_ready.wait(3);body=b'{}';mime='application/json'
  else:body=b'''<main><div class="loading-state">Loading</div></main><script>fetch('/api/exchange-rates');fetch('/api/catalog').then(r=>r.json()).then(()=>document.querySelector('main').innerHTML='<p id="ready">Ready</p>');</script>''';mime='text/html'
  try:self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  except (BrokenPipeError,ConnectionResetError):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True;threading.Thread(target=server.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(server.server_port)
try:
 with sync_playwright()as p:
  for engine in ['chromium','webkit']:
   browser=getattr(p,engine).launch();context=browser.new_context();page=context.new_page();readiness=NativePageReadiness(page,base,timeout=1000);catalog_ready.clear();page.goto(base);started=time.monotonic();threading.Timer(.25,catalog_ready.set).start();readiness.wait();assert time.monotonic()-started>=.2 and page.locator('#ready').count()==1 and readiness.optional_observed
   assert any(request.url.endswith('/api/exchange-rates')for request in readiness.pending),'OPTIONAL_FIXTURE_NOT_PENDING'
   page.evaluate("void fetch('/api/critical')");page.wait_for_timeout(50)
   try:readiness.wait();raise AssertionError('CRITICAL_REQUEST_WAS_IGNORED')
   except TimeoutError as error:assert '/api/critical'in str(error)
   release.set();readiness.wait();page.evaluate("document.querySelector('main').innerHTML='<div class=loading-state>Loading</div>'")
   try:readiness.wait();raise AssertionError('LOADING_UI_WAS_IGNORED')
   except TimeoutError:pass
   context.close();browser.close();release.clear();print(json.dumps({'engine':engine,'criticalDataWaited':True,'criticalRequestTimeoutEnforced':True,'loadingUiTimeoutEnforced':True,'optionalFxDoesNotBlockUi':True}),flush=True)
finally:release.set();server.shutdown();server.server_close()
