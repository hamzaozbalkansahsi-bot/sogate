import {welcomeMapData} from './welcome-map-data.js?v=storefront-recovery-20261112-r1';
import {localizedValue} from './locale-runtime.js?v=storefront-recovery-20261112-r1';

const NS='http://www.w3.org/2000/svg';
export function createWelcomeCountryMap({doc,win,locale,countries,text,onSelect=()=>{},onActivate=()=>{}}){
 const container=doc.createElement('div');container.className='welcome-poster-map';
 const node=(name,attributes={})=>{const el=doc.createElementNS(NS,name);for(const [key,value]of Object.entries(attributes))el.setAttribute(key,String(value));return el;};
 const label=region=>countries.find(c=>c.code===region.code)?.[locale]||localizedValue(region.names,locale);
 const known=new Set(countries.map(c=>c.code));
 const regions=[...welcomeMapData.regions].sort((a,b)=>label(a).localeCompare(label(b),locale));
 const svg=node('svg',{viewBox:welcomeMapData.viewBox,role:'listbox',tabindex:'0','aria-label':text.mapLabel,'aria-describedby':'welcome-map-help',class:'welcome-country-map',preserveAspectRatio:'xMidYMid meet'});
 const defs=node('defs'),clip=node('clipPath',{id:'welcome-map-clip'});clip.append(node('rect',{x:-18,y:-10,width:780,height:430}));defs.append(clip);svg.append(defs);
 const drawing=node('g',{'clip-path':'url(#welcome-map-clip)'}),land=node('g',{class:'welcome-map-land'}),paths=new Map();
 for(const region of regions){
  const path=node('path',{d:region.path,id:'welcome-region-'+region.id,'data-map-region':region.id,'data-map-code':region.code,role:'option','aria-label':label(region),'aria-selected':'false','fill-rule':'evenodd',class:known.has(region.code)?'welcome-map-region is-destination':region.code==='TR'?'welcome-map-region is-origin':'welcome-map-region'});
  land.append(path);paths.set(region.id,path);
 }
 const routes=node('g',{class:'welcome-map-routes','aria-hidden':'true'});for(const d of welcomeMapData.routes)routes.append(node('path',{d}));
 const emphasis=node('g',{class:'welcome-map-emphasis','aria-hidden':'true'}),origin=node('g',{class:'welcome-map-origin','aria-hidden':'true'}),home=welcomeMapData.home;
 origin.append(node('circle',{cx:home.x,cy:home.y,r:11,class:'welcome-map-origin-halo'}),node('circle',{cx:home.x,cy:home.y,r:4,class:'welcome-map-origin-pin'}));
 drawing.append(land,routes,emphasis,origin);svg.append(drawing);
 const tooltip=doc.createElement('div');tooltip.className='welcome-map-tooltip';tooltip.hidden=true;tooltip.setAttribute('role','status');tooltip.setAttribute('aria-live','polite');
 const name=doc.createElement('strong'),status=doc.createElement('span');tooltip.append(name,status);
 const help=doc.createElement('span');help.id='welcome-map-help';help.className='sr-only';help.textContent=text.mapHelp;
 const caption=doc.createElement('span');caption.className='welcome-poster-regions';caption.textContent=text.regions;
 container.append(svg,caption,tooltip,help);
 let selected=null,frame=0,lastPoint=null;
 function position(point){
  if(!selected)return;
  const box=container.getBoundingClientRect(),shape=paths.get(selected.id).getBoundingClientRect();
  const anchor=point||{x:Math.max(box.left+16,Math.min(box.right-16,shape.left+shape.width/2)),y:Math.max(box.top+16,Math.min(box.bottom-16,shape.top))};
  const maxX=Math.max(12,box.width-tooltip.offsetWidth-12),maxY=Math.max(12,box.height-tooltip.offsetHeight-12);
  tooltip.style.left=Math.max(12,Math.min(maxX,anchor.x-box.left+16))+'px';
  tooltip.style.top=Math.max(12,Math.min(maxY,anchor.y-box.top-tooltip.offsetHeight-14))+'px';
 }
 function select(region,point){
  if(!region)return;
  if(selected?.id!==region.id){
   if(selected)paths.get(selected.id).setAttribute('aria-selected','false');
   selected=region;paths.get(region.id).setAttribute('aria-selected','true');
   svg.setAttribute('aria-activedescendant','welcome-region-'+region.id);
   const raised=node('path',{d:region.path,'fill-rule':'evenodd'});emphasis.replaceChildren(raised);
   name.textContent=label(region);status.textContent=known.has(region.code)?text.accepting:region.code==='TR'?text.turkeyStore:text.otherCountry;
   container.classList.add('has-country');container.dataset.activeCountry=region.code;tooltip.hidden=false;onSelect(region.code);
  }
  position(point);
 }
 function clear(){
  win.cancelAnimationFrame(frame);frame=0;
  if(selected)paths.get(selected.id).setAttribute('aria-selected','false');selected=null;
  svg.removeAttribute('aria-activedescendant');emphasis.replaceChildren();container.classList.remove('has-country');delete container.dataset.activeCountry;tooltip.hidden=true;onSelect(null);
 }
 function selectCode(code){select(regions.find(region=>region.code===code));}
 function move(event){
  if(event.pointerType==='touch')return;
  const path=event.target.closest?.('[data-map-region]');
  if(!path){if(doc.activeElement!==svg)clear();return;}
  lastPoint={x:event.clientX,y:event.clientY,regionId:path.dataset.mapRegion};
  if(frame)return;
  frame=win.requestAnimationFrame(()=>{frame=0;select(regions.find(region=>region.id===lastPoint.regionId),lastPoint);});
 }
 function leave(){if(doc.activeElement!==svg)clear();}
 function click(event){const id=event.target.closest?.('[data-map-region]')?.dataset.mapRegion;if(id){const region=regions.find(region=>region.id===id);select(region,{x:event.clientX,y:event.clientY});onActivate(region.code);}}
 function focus(){if(!selected)selectCode('TR');}
 function keys(event){
  if(['Enter',' '].includes(event.key)&&selected){event.preventDefault();event.stopPropagation();onActivate(selected.code);return;}
  if(!['ArrowRight','ArrowLeft','ArrowDown','ArrowUp','Home','End'].includes(event.key))return;
  event.preventDefault();event.stopPropagation();
  let index=regions.findIndex(region=>region.id===selected?.id);
  index=event.key==='Home'?0:event.key==='End'?regions.length-1:(index+(['ArrowRight','ArrowDown'].includes(event.key)?1:-1)+regions.length)%regions.length;
  select(regions[index]);
 }
 svg.addEventListener('pointermove',move,{passive:true});svg.addEventListener('click',click);svg.addEventListener('focus',focus);svg.addEventListener('keydown',keys);container.addEventListener('pointerleave',leave);
 return {element:container,select:selectCode,clear,destroy(){clear();svg.removeEventListener('pointermove',move);svg.removeEventListener('click',click);svg.removeEventListener('focus',focus);svg.removeEventListener('keydown',keys);container.removeEventListener('pointerleave',leave);}};
}
