import {readdir,readFile,writeFile} from 'node:fs/promises';
const version='storefront-recovery-20261112-r1';let changed=0;
for(const file of await readdir('web')){
 if(!file.endsWith('.js')||file.startsWith('admin'))continue;
 const name='web/'+file,source=await readFile(name,'utf8');
 const result=source.replace(/(from\s*['"])(\.\/[^'"?]+\.js)(?:\?[^'"]*)?(['"])/g,(_,prefix,url,quote)=>prefix+url+'?v='+version+quote);
 if(result!==source){await writeFile(name,result);changed++;}
}
for(const file of ['web/index.html','hosting/legal.php']){
 const source=await readFile(file,'utf8'),result=source.replace(/\/(app\.js|styles\.css|legal\.js|legal\.css)\?v=[^'"\s<>]+/g,(_,name)=>'/'+name+'?v='+version);
 if(result!==source)await writeFile(file,result);
}
console.log(JSON.stringify({version,modulesChanged:changed}));
