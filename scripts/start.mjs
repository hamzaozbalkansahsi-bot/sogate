/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/start.mjs
 * Açıklama   : Standalone derlemeyi gerekli varlıklarla yerel veya yapılandırılmış sunucuda başlatır.
 */
import {cp,access} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import path from 'node:path';
const root=process.cwd();const target=path.join(root,'.next','standalone');await access(path.join(target,'server.js'));
if(!['development','test','staging','production'].includes(process.env.APP_ENV??''))throw new Error('APP_ENV yapılandırılmalıdır; üretim sırları ortam yöneticisinden sağlanır.');
const option=process.argv.indexOf('--port');const port=Number(option>=0?process.argv[option+1]:process.env.PORT??3000);if(!Number.isInteger(port)||port<1024||port>65535)throw new Error('Geçerli uygulama portu gerekir.');
for(const [source,destination]of [['public','public'],['.next/static','.next/static'],['assets','assets']])await cp(path.join(root,source),path.join(target,destination),{recursive:true,force:true});
const host=process.env.APP_BIND_HOST??'127.0.0.1';
const environment={...process.env,NODE_ENV:'production',HOSTNAME:host,PORT:String(port)};
if(['development','test'].includes(process.env.APP_ENV)){
 environment.APP_URL=`http://127.0.0.1:${port}`;environment.BETTER_AUTH_URL=environment.APP_URL;
 environment.STORAGE_LOCAL_PATH=path.resolve(root,process.env.STORAGE_LOCAL_PATH??'.local/media');
}
const child=spawn(process.execPath,[path.join(target,'server.js')],{cwd:root,env:environment,stdio:'inherit',windowsHide:true});
child.on('error',()=>{console.error('Uygulama başlatılamadı.');process.exitCode=1;});
child.on('exit',code=>{process.exitCode=code??1;});
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>child.kill(signal));
