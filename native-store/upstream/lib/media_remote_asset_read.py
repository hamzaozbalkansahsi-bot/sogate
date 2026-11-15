"""Raw TLS cPanel download for explicitly scoped public/admin backup files."""
import base64,http.client,ssl,urllib.parse
ADMIN_ASSETS=frozenset(['admin.html','admin.js','admin.css','admin-password-visibility.js','admin-campaigns.js'])
def read_admin_bytes(backend,deployer,directory,name,*,maximum=1000000):
 if name not in ADMIN_ASSETS:raise ValueError('admin asset read outside approved file set')
 if directory!=deployer.PUBLIC and not directory.startswith(deployer.HOME+'/nodeno-backups/'):raise ValueError('admin asset read outside public or protected backup')
 deployer.remote_path(directory,private=directory!=deployer.PUBLIC);user,password=backend.probe.credentials();auth=base64.b64encode((user+':'+password).encode()).decode('ascii');connection=http.client.HTTPSConnection(deployer.HOST,deployer.PORT,timeout=60,context=ssl.create_default_context())
 try:
  connection.request('GET','/download?file='+urllib.parse.quote(directory+'/'+name,safe=''),headers={'Authorization':'Basic '+auth,'Accept-Encoding':'identity'});response=connection.getresponse()
  if response.status!=200:raise RuntimeError('raw scoped admin asset read rejected')
  body=response.read(maximum+1)
  if len(body)>maximum or response.getheader('Content-Encoding','identity')!='identity' or int(response.getheader('Content-Length',len(body)))!=len(body):raise RuntimeError('raw scoped admin asset read size/encoding differs')
  return body
 finally:connection.close()
