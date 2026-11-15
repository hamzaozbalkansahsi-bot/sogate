import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {readFileSync} from 'node:fs';
import {formatDate,formatDateTime,dateTimeSettings} from '../web/date-time.js';
test('server-rendered dates use Istanbul by default and selected country on subsequent requests',()=>{
 const code=`require ${JSON.stringify(path.resolve('hosting/date-time.php').replaceAll('\\','/'))};echo json_encode([nodenoHumanDate('2026-11-12','TR'),nodenoHumanDateTime('2026-11-12T21:05:00Z','TR'),nodenoHumanDate('2026-11-12','US'),nodenoHumanDate('2026-11-12','DE'),nodenoHumanDateTime('2026-11-12T21:05:00Z','BR'),nodenoDateRegion('BR')['locale']]);`;
 const r=spawnSync(path.resolve('artifacts/runtime-php/php.exe'),['-r',code],{encoding:'utf8'});assert.equal(r.status,0,r.stdout+r.stderr);assert.deepEqual(JSON.parse(r.stdout),['12/11/2026','13/11/2026 00:05','11/12/2026','12.11.2026','12/11/2026 18:05','pt-BR']);
});
test('all selectable countries share server and browser formats and default zone names',()=>{
 const regions=JSON.parse(readFileSync('data/date-time-regions.json','utf8')).regions,stamps=['2026-11-12T21:05:00Z','2026-07-12T00:05:00Z'];
 const rows=Object.keys(regions).flatMap(country=>stamps.map(stamp=>({country,stamp})));
 // Compare the same local wall time: PHP and Node can ship different IANA releases.
 const code=`require ${JSON.stringify(path.resolve('hosting/date-time.php').replaceAll('\\','/'))};$rows=json_decode(stream_get_contents(STDIN),true);$out=[];foreach($rows as $row){$zone=nodenoDateRegion($row['country'])['timeZone'];$local=new DateTimeImmutable(substr($row['stamp'],0,19),new DateTimeZone($zone));$out[]=['date'=>nodenoHumanDate('2026-11-12',$row['country']),'time'=>nodenoHumanDateTime($local,$row['country']),'zone'=>$zone];}echo json_encode($out);`;
 const r=spawnSync(path.resolve('artifacts/runtime-php/php.exe'),['-r',code],{input:JSON.stringify(rows),encoding:'utf8'});assert.equal(r.status,0,r.stdout+r.stderr);
 const actual=JSON.parse(r.stdout),spaces=value=>value.replace(/[\u00a0\u202f]/g,' ');for(const [i,row]of rows.entries()){const options={country:row.country,deviceTimeZone:'Not/A-Country-Zone'};assert.deepEqual({...actual[i],date:spaces(actual[i].date),time:spaces(actual[i].time)},{date:spaces(formatDate('2026-11-12',options)),time:spaces(formatDateTime(row.stamp,{...options,timeZone:'UTC'})),zone:dateTimeSettings(row.country,options).timeZone},row.country+' '+row.stamp);}
});
