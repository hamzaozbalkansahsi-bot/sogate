"""Narrow, idempotent date-format migration over a verified application snapshot.

This lets a release preserve concurrently edited product and marketing code byte for byte
outside the date call sites. The same transformation is available to the package builder.
"""
import re
VERSION='20261113-r2'
def rewrite(name,body):
 text=body.decode('utf8');before=text
 if name=='app.js':
  old="function orderDate(value){const date=new Date(value);return value&&Number.isFinite(date.getTime())?new Intl.DateTimeFormat(locale,{dateStyle:'medium'}).format(date):'';}"
  text=text.replace(old,"function orderDate(value){return formatDate(value);}")
  names=['formatDate','mountDateTime']
 elif name=='admin.js':
  text=text.replace("const date=n=>n?new Intl.DateTimeFormat('tr-TR',{dateStyle:'medium',timeStyle:'short'}).format(new Date(n*1000)):'Henüz yok';","const date=n=>n?formatDateTime(n):'Henüz yok';")
  text=text.replace('new Date(v*1000-new Date(v*1000).getTimezoneOffset()*60000).toISOString().slice(0,16)','dateTimeInput(v)')
  text=text.replace('Math.floor(new Date(el.value).getTime()/1000)','Math.floor(parseDateTimeInput(el.value).getTime()/1000)')
  text=text.replace('Saatler bu cihazın saat diliminde gösterilir','Saatler seçilen ülkenin saat diliminde gösterilir').replace('Intl.DateTimeFormat().resolvedOptions().timeZone','dateTimeSettings().timeZone')
  names=['formatDateTime','dateTimeInput','parseDateTimeInput','dateTimeSettings','mountDateTime']
 elif name=='admin-social.js':
  text=text.replace("const date=(n,options={dateStyle:'medium',timeStyle:'short'})=>n?new Intl.DateTimeFormat('tr-TR',{timeZone:'Europe/Istanbul',...options}).format(n*1000):'Henüz yok';","const date=(n,options={timeStyle:'short'})=>n?(options.timeStyle?formatDateTime(n):formatDate(n)):'Henüz yok';")
  text=text.replace('new Date((scheduled+10800)*1000).toISOString().slice(0,16)','dateTimeInput(scheduled)')
  text=text.replace("Math.floor(Date.parse(fd.get('scheduled')+'+03:00')/1000)","Math.floor(parseDateTimeInput(fd.get('scheduled')).getTime()/1000)")
  text=text.replace("Math.floor(Date.parse(fd.get('expires')+'T23:59:59+03:00')/1000)","Math.floor(parseDateTimeInput(fd.get('expires')+'T23:59').getTime()/1000)+59")
  text=text.replace('Yayın zamanı (İstanbul)','Yayın zamanı (${esc(dateTimeSettings().timeZone)})')
  names=['formatDate','formatDateTime','dateTimeInput','parseDateTimeInput','dateTimeSettings']
 elif name=='admin-suppliers.js':
  text=text.replace("const date=n=>n?new Date(n*1000).toLocaleDateString('tr-TR'):'Henüz alınmadı';","const date=n=>n?formatDate(n):'Henüz alınmadı';")
  text=text.replace("new Date(r.checkedAt).toLocaleString('tr-TR')",'formatDateTime(r.checkedAt)')
  text=text.replace("new Date().toLocaleDateString('en-CA')",'dateTimeInput(new Date()).slice(0,10)')
  for field in['purchasedAt','effectiveAt']:text=text.replace("new Date(f.get('"+field+"')+'T12:00:00').getTime()","parseDateTimeInput(f.get('"+field+"')+'T12:00').getTime()")
  names=['formatDate','formatDateTime','dateTimeInput','parseDateTimeInput']
 elif name=='admin-analytics.js':
  text=text.replace("new Intl.DateTimeFormat('tr-TR',{timeZone:'UTC'}).format(Number(day)*86400000)","formatDate(new Date(Number(day)*86400000).toISOString().slice(0,10))")
  names=['formatDate']
 else:return body
 # Merge an existing import instead of introducing duplicate bindings from another task.
 pattern=r"import\s*\{([^}]+)\}\s*from\s*['\"]\./date-time\.js[^'\"]*['\"];?(?:\r?\n)?"
 found=re.search(pattern,text)
 if found:names=sorted(set(names+[x.strip()for x in found[1].split(',')if x.strip()]));text=text[:found.start()]+text[found.end():]
 names=sorted(set(names));text="import {"+','.join(names)+"} from './date-time.js?v="+VERSION+"';\n"+text
 if 'mountDateTime'in names and 'mountDateTime();'not in text:text=text.replace("';\n","';\nmountDateTime();\n",1)
 # A changed parent module fetches current child formatters even after a long browser session.
 text=re.sub(r"(from\s*['\"]\./admin-(?:social|suppliers|analytics)\.js)(?:\?[^'\"]*)?(['\"])",r'\1?v=date-policy-'+VERSION+r'\2',text)
 return text.encode('utf8')
def html_revision(body,script):
 text=body.decode('utf8');return re.sub(r'(src=["\x27]/'+re.escape(script)+r')(?:\?[^"\x27]*)?(["\x27])',r'\1?v=date-policy-'+VERSION+r'\2',text).encode('utf8')
