#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_browser_ready.py
# Açıklama   : Arayüz kabulünü isteğe bağlı kur isteğinden ayırır; kritik istekleri ve yükleme durumunu bekler.
import time
from urllib.parse import urlsplit
from playwright.sync_api import TimeoutError

class NativePageReadiness:
 def __init__(self,page,base,timeout=30000):
  self.page=page;self.timeout=timeout;self.optional_url=base.rstrip('/')+'/api/exchange-rates';self.pending=set();self.optional_observed=False
  page.on('request',self.started)
  page.on('requestfinished',self.finished)
  page.on('requestfailed',self.finished)
 def started(self,request):
  self.pending.add(request)
  if request.url.split('?',1)[0]==self.optional_url:self.optional_observed=True
 def finished(self,request):self.pending.discard(request)
 def critical(self):return [request for request in self.pending if request.url.split('?',1)[0]!=self.optional_url]
 def wait(self):
  deadline=time.monotonic()+self.timeout/1000
  self.page.wait_for_load_state('load',timeout=self.timeout)
  while True:
   while self.critical():
    if time.monotonic()>=deadline:raise TimeoutError('Critical requests unfinished: '+','.join(sorted({urlsplit(request.url).path for request in self.critical()})))
    self.page.wait_for_timeout(50)
   remaining=max(1,int((deadline-time.monotonic())*1000))
   self.page.wait_for_function('()=>document.readyState==="complete"&&!document.querySelector("main .loading,main .loading-state")&&(![...document.scripts].some(s=>s.src&&new URL(s.src).pathname.endsWith("/app.js"))||!!document.querySelector("#display-currency"))',timeout=remaining)
   self.page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
   if not self.critical():return
