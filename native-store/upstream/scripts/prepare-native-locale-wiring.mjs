// Syntax-aware, repeatable source transform. Does not modify catalogue records.
import {readFile,readdir,writeFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
const require=createRequire('C:/Users/Hamza ÖZBALKAN/AppData/Local/npm-cache/_npx/bbbefcae0b32ac69/node_modules/acorn/package.json'),{parse}=require('acorn');
const only=process.argv.slice(2),changed=[];
for(const file of await readdir('web')){
 if(!file.endsWith('.js')||['locale-runtime.js','locale-registry.js','welcome-map-data.js'].includes(file)||file.startsWith('admin')||only.length&&!only.includes(file))continue;
 const name='web/'+file,original=await readFile(name,'utf8');if(original.includes('/* native-locale-copy */'))continue;
 let s=original;const edits=[];
 function visit(node){if(!node||typeof node!=='object')return;
  if(node.type==='ObjectExpression'){
   const keys=node.properties.filter(p=>p.type==='Property'&&!p.computed).map(p=>p.key.name??p.key.value);
   if(['tr','en','ru','ar'].every(k=>keys.includes(k))){edits.push({start:node.start,end:node.end});return;}
  }
  for(const [key,value]of Object.entries(node))if(value&&typeof value==='object'&&key!=='loc'){if(Array.isArray(value))value.forEach(visit);else visit(value);}
 }
 visit(parse(s,{ecmaVersion:'latest',sourceType:'module'}));
 for(const edit of edits.sort((a,b)=>b.start-a.start))s=s.slice(0,edit.start)+'localeCopy('+s.slice(edit.start,edit.end)+')'+s.slice(edit.end);
 if(edits.length){s="/* native-locale-copy */\nimport {localeCopy} from './locale-runtime.js?v=target-locales-20261111-r1';\n"+s;await writeFile(name,s);changed.push({file,objects:edits.length});}
}
console.log(JSON.stringify({changed}));
