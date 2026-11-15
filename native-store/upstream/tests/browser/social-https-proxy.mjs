import https from 'node:https';
import http from 'node:http';
import {readFile,realpath} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import assert from 'node:assert/strict';
const config=JSON.parse(await readFile('artifacts/social-auth/preview.json','utf8'));
assert.equal(config.testOnly,true);
const temporary=await realpath(config.temporaryRoot),parent=await realpath(os.tmpdir());
assert.equal(path.dirname(temporary).toLowerCase(),parent.toLowerCase());assert.ok(path.basename(temporary).startsWith('nodeno-auth-browser-'));
for(const filename of [config.key,config.cert])assert.equal(path.dirname(await realpath(filename)).toLowerCase(),temporary.toLowerCase());
https.createServer({key:await readFile(config.key),cert:await readFile(config.cert)},(req,res)=>{
 const upstream=http.request({hostname:'127.0.0.1',port:4190,path:req.url,method:req.method,agent:false,headers:{...req.headers,connection:'close'}},response=>{res.writeHead(response.statusCode,response.headers);response.pipe(res);});
 upstream.on('error',()=>{res.writeHead(502);res.end('Isolated preview unavailable');});req.pipe(upstream);
}).listen(4189,'127.0.0.1',()=>console.log('Test-only HTTPS account UI: https://127.0.0.1:4189'));
