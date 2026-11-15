#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/run-native-store.py
# Açıklama   : Özgün güvenli yönetim çerezlerini koruyan, yalnız yerel TLS/PHP önizlemesi.
import datetime,http.client,http.server,ipaddress,json,os,ssl,subprocess
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT=Path(__file__).resolve().parent.parent
build=json.loads((ROOT/'.local/native-store-build.json').read_text('utf8'));folder=Path(build['buildRoot']);cert=folder/'local-cert.pem';key=folder/'local-key.pem'
if not cert.exists():
 secret=rsa.generate_private_key(public_exponent=65537,key_size=2048);subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'SEXOGATE local preview')]);now=datetime.datetime.now(datetime.timezone.utc)
 certificate=x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(secret.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=2)).not_valid_after(now+datetime.timedelta(days=7)).add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False).sign(secret,hashes.SHA256())
 cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM));key.write_bytes(secret.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
class Proxy(http.server.BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1'
 def log_message(self,*args):pass
 def serve(self):
  if self.headers.get('Host')!='127.0.0.1:3186':self.send_error(403);return
  length=int(self.headers.get('Content-Length','0'))
  if length>2000000 or self.headers.get('Transfer-Encoding'):self.send_error(413);return
  headers={k:v for k,v in self.headers.items() if k.lower() not in {'connection','transfer-encoding'}};headers['Connection']='close';connection=http.client.HTTPConnection('127.0.0.1',3185,timeout=40)
  try:
   connection.request(self.command,self.path,body=self.rfile.read(length) if length else None,headers=headers);response=connection.getresponse();body=response.read()
   if 'text/html' in (response.getheader('Content-Type') or ''):
    import re
    text=re.sub(r'\bNODENO\b','SEXOGATE',body.decode('utf8'))
    if '/sexogate.css' not in text:text=text.replace('</head>','<link rel="stylesheet" href="/sexogate.css"><script defer src="/sexogate-branding.js"></script></head>')
    body=text.encode('utf8')
   self.send_response(response.status)
   for k,v in response.getheaders():
    if k.lower() not in {'connection','transfer-encoding','content-length','server','date','x-robots-tag'}:self.send_header(k,v)
   self.send_header('Content-Length',str(len(body)));self.send_header('X-Robots-Tag','noindex,nofollow');self.end_headers()
   if self.command!='HEAD':self.wfile.write(body)
  except (OSError,ssl.SSLError):self.close_connection=True
  finally:connection.close()
 do_GET=do_HEAD=do_POST=do_PUT=do_PATCH=do_DELETE=do_OPTIONS=serve

environment=os.environ.copy();environment.update(NODENO_TEST_PUBLIC=build['public'],NODENO_TEST_HTTPS='loopback-tls-only')
log=(folder/'php-local.log').open('wb');php=subprocess.Popen([str(ROOT/'.local/php-runtime/php.exe'),'-d','extension=pdo_sqlite','-d','extension=sqlite3','-S','127.0.0.1:3185','-t',build['public'],str(Path(build['private'])/'dev-router.php')],env=environment,stdout=log,stderr=log)
server=http.server.ThreadingHTTPServer(('127.0.0.1',3186),Proxy);context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key);server.socket=context.wrap_socket(server.socket,server_side=True)
try:print('SEXOGATE direct application: https://127.0.0.1:3186 (local TLS)',flush=True);server.serve_forever()
finally:server.server_close();php.terminate();php.wait(timeout=10);log.close()
