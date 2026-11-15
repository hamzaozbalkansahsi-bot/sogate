import http from 'node:http';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {stat} from 'node:fs/promises';
const worker=fileURLToPath(new URL('../dist/server/index.js',import.meta.url));
let module,modified=0;
const server=http.createServer(async(req,res)=>{
 try {
  const stamp=(await stat(worker)).mtimeMs;
  if(stamp!==modified){module=await import(pathToFileURL(worker).href+'?v='+stamp);modified=stamp;}
  const response=await module.default.fetch(new Request('http://127.0.0.1:4173'+req.url,{method:req.method,headers:req.headers}),{},{});
  res.writeHead(response.status,Object.fromEntries(response.headers));
  if(response.body) for await(const chunk of response.body) res.write(chunk);
  res.end();
 }catch{res.writeHead(500,{'content-type':'text/plain'});res.end('Preview is unavailable');}
});
server.listen(4173,'127.0.0.1',()=>console.log('Local: http://127.0.0.1:4173'));
