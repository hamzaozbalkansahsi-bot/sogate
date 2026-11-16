#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/run-native-stage-local.py
# Açıklama   : Sunucu alt yolu paketini yalnız loopback üzerinde gerçek TLS ile çalıştırır.
import datetime,http.client,http.server,ipaddress,json,os,ssl,subprocess
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
ROOT=Path(__file__).resolve().parent.parent;b=json.loads((ROOT/'.local/native-stage-local.json').read_text('utf8'));base=Path(b['base']);key=base/'tls.key';cert=base/'tls.pem'
if not cert.exists():
 secret=rsa.generate_private_key(public_exponent=65537,key_size=2048);subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'SEXOGATE mount acceptance')]);now=datetime.datetime.now(datetime.timezone.utc);c=x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(secret.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=2)).not_valid_after(now+datetime.timedelta(days=7)).add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False).sign(secret,hashes.SHA256());cert.write_bytes(c.public_bytes(serialization.Encoding.PEM));key.write_bytes(secret.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
class Proxy(http.server.BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1'
 def log_message(self,*args):pass
 def serve(self):
  if self.headers.get('Host')!='127.0.0.1:3188':self.send_error(403);return
  size=int(self.headers.get('Content-Length','0'))
  if size<0 or size>2000000 or self.headers.get('Transfer-Encoding'):self.send_error(413);return
  c=http.client.HTTPConnection('127.0.0.1',3187,timeout=40)
  try:
   c.request(self.command,self.path,body=self.rfile.read(size) if size else None,headers={k:v for k,v in self.headers.items() if k.lower() not in {'connection','transfer-encoding'}});r=c.getresponse();body=r.read();self.send_response(r.status)
   for k,v in r.getheaders():
    if k.lower() not in {'connection','transfer-encoding','content-length','server','date'}:self.send_header(k,v)
   self.send_header('Content-Length',str(len(body)));self.end_headers()
   if self.command!='HEAD':self.wfile.write(body)
  finally:c.close()
 do_GET=do_HEAD=do_POST=do_PUT=do_PATCH=do_DELETE=do_OPTIONS=serve
env=os.environ.copy();env['SEXOGATE_NATIVE_LOCAL_TLS']='loopback-only'
if os.name=='nt':env.setdefault('OPENSSL_CONF',str(ROOT/'.local/php-runtime/extras/ssl/openssl.cnf'))
log=(base/'php.log').open('wb');php=subprocess.Popen([str(ROOT/'.local/php-runtime/php.exe'),'-d','extension=pdo_sqlite','-d','extension=sqlite3','-S','127.0.0.1:3187','-t',b['web'],b['router']],env=env,stdout=log,stderr=log)
http.server.ThreadingHTTPServer.request_queue_size=128
server=http.server.ThreadingHTTPServer(('127.0.0.1',3188),Proxy);context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key);server.socket=context.wrap_socket(server.socket,server_side=True)
try:print(b['url'],flush=True);server.serve_forever()
finally:server.server_close();php.terminate();php.wait(timeout=10);log.close()
