import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dateTimeSettings} from '../web/date-time.js';
const root=fileURLToPath(new URL('../',import.meta.url));
const source=await readFile(new URL('../web/visitor-market.js',import.meta.url),'utf8');
const codes=source.match(/countries=new Set\(\('([^']+)'\)/)?.[1].split(' ');
if(!codes?.includes('TR'))throw new Error('Country registry unavailable');
const regions={};
for(const code of codes){
 const s=dateTimeSettings(code,{deviceTimeZone:'Not/A-Country-Zone'}),date=new Intl.DateTimeFormat(s.locale,{day:'2-digit',month:'2-digit',year:'numeric',calendar:'gregory',numberingSystem:'latn',timeZone:'UTC'});
 const pattern=code==='TR'?'d/m/Y':date.formatToParts(new Date('2026-11-12T12:00:00Z')).map(p=>({day:'d',month:'m',year:'Y'}[p.type]??p.value.replace(/[A-Za-z]/g,c=>'\\'+c))).join('');
 const time=new Intl.DateTimeFormat(s.locale,{hour:'2-digit',minute:'2-digit',timeZone:'UTC',...(code==='TR'?{hourCycle:'h23'}:{})});
 const numbers=new Intl.NumberFormat(s.locale,{useGrouping:false});
 const dayPeriod=hour=>time.formatToParts(new Date(`2026-11-12T${hour}:05:00Z`)).find(p=>p.type==='dayPeriod')?.value||'';
 regions[code]={locale:s.locale,timeZone:s.timeZone,datePattern:pattern,hour12:time.resolvedOptions().hour12,hourCycle:time.resolvedOptions().hourCycle,timeParts:time.formatToParts(new Date('2026-11-12T21:05:00Z')).map(p=>p.type==='literal'?{type:'literal',value:p.value}:{type:p.type}),dayPeriods:{am:dayPeriod('09'),pm:dayPeriod('21')},digits:Array.from({length:10},(_,n)=>numbers.format(n))};
}
const helper=await readFile(new URL('../web/date-time.js',import.meta.url));
const body=JSON.stringify({schema:1,calendar:'gregory',sourceHelperSha256:createHash('sha256').update(helper).digest('hex'),icuVersion:process.versions.icu,regions},null,2)+'\n';
await writeFile(root+'data/date-time-regions.json',body);
