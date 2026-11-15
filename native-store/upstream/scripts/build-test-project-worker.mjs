// Isolated regression fixture: reviewed live furniture data, current source UI.
// The cPanel test packager marks this fixture testOnly; it cannot be deployed.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {packWebAssets} from '../lib/assets.mjs';
import {fileURLToPath} from 'node:url';
const root=new URL('../',import.meta.url),base=new URL('artifacts/cpanel-release-welcome-v2-20261103/private/',root);
let externalAssets={};try{const approved=JSON.parse(await readFile(new URL('data/supplier-media-approved.json',root)));externalAssets=Object.fromEntries(Object.entries(approved.images).map(([url,row])=>[url,row.outputSha256]));}catch(e){if(e.code!=='ENOENT')throw e;}
const catalog=JSON.parse(await readFile(new URL('catalog.json',base))),media=JSON.parse(await readFile(new URL('media.json',base))),brand=JSON.parse(await readFile(new URL('data/brand.json',root))),assets=await packWebAssets(fileURLToPath(new URL('web/',root)),{externalAssets});
catalog.meta.testOnly=true;
const seo=(await readFile(new URL('web/seo-core.js',root),'utf8')).replace(/^export /gm,''),server=(await readFile(new URL('lib/server.mjs',root),'utf8')).replace(/^import .*from '\.\/seo\.mjs';\r?\n/m,'').replace(/^export /gm,'');
await mkdir(new URL('dist/server/',root),{recursive:true});
await writeFile(new URL('dist/server/index.js',root),seo+'\n'+server+'\nexport default createApplication('+[catalog,assets,media,{},null,brand,{}].map((v,i)=>i===4?'fetch':JSON.stringify(v)).join(',')+');\n');
console.log('Isolated test fixture refreshed; not a production build.');
