import {mountDateTime} from './date-time.js?v=20261113-r2';
import './blog-surface.js?v=20261113-r2';
function number(value,min,max){const n=Number(value);if(!Number.isFinite(n)||n<min||n>max)throw new RangeError('invalid_measurement');return n;}
const rounded=n=>Math.round((n+Number.EPSILON)*100)/100;
export function paintEstimate({length,width,height,openings,coats,coverage,basis,waste}){
 const l=number(length,.01,1000),w=number(width,.01,1000),h=number(height,.01,100),o=number(openings,0,100000);
 const c=number(coats,1,10),r=number(coverage,.01,1000),p=number(waste,0,100);
 if(!Number.isInteger(c)||!['coat','system'].includes(basis))throw new RangeError('invalid_coverage');
 const gross=(l+w)*2*h;if(o>=gross)throw new RangeError('openings_exceed_surface');
 const area=gross-o;return {area:rounded(area),litres:rounded(area/r*(basis==='coat'?c:1)*(1+p/100))};
}
export function spaceEstimate({room,furniture,opposite}){
 const r=number(room,1,100000),f=number(furniture,0,100000),o=number(opposite,0,100000),remaining=rounded(r-f-o);
 return {remaining,fits:remaining>=0};
}
export function paletteFrom(value){
 if(typeof value!=='string'||!/^#[a-f\d]{6}$/i.test(value))throw new RangeError('invalid_colour');
 const c=[1,3,5].map(i=>parseInt(value.slice(i,i+2),16));
 const hex=x=>'#'+x.map(v=>Math.round(v).toString(16).padStart(2,'0')).join('').toUpperCase();
 return [value.toUpperCase(),hex(c.map(v=>v*.3+255*.7)),hex(c.map(v=>v*.5)),hex(c.map(v=>255-v))];
}

function bindTools(){
 const digits=new Intl.NumberFormat(document.documentElement.lang,{maximumFractionDigits:2});
 for(const form of document.querySelectorAll('[data-blog-tool]')){
  const output=form.querySelector('output');
  const update=()=>{
   try{
    const data=Object.fromEntries(new FormData(form)),kind=form.dataset.blogTool;
    if(kind==='paint'){
     const result=paintEstimate(data);output.textContent=digits.format(result.area)+' m² · '+digits.format(result.litres)+' L';
    }else if(kind==='space'){
     const result=spaceEstimate(data);output.textContent=digits.format(result.remaining)+' cm · '+(result.fits?form.dataset.fits:form.dataset.noFit);
     const chart=form.querySelector('[data-space-chart]'),r=Number(data.room),f=Number(data.furniture),o=Number(data.opposite);
     if(chart){chart.querySelector('[data-furniture]').setAttribute('width',Math.min(560,f/r*560));chart.querySelector('[data-opposite]').setAttribute('width',Math.min(560,o/r*560));chart.querySelector('[data-opposite]').setAttribute('x',30+Math.max(0,560-o/r*560));chart.querySelector('[data-gap]').textContent=digits.format(result.remaining)+' cm';}
    }else{
     const colors=paletteFrom(data.color);output.replaceChildren(...colors.map(color=>{const node=document.createElement('span');node.className='blog-swatch';const chip=document.createElement('span');chip.className='blog-swatch-color';chip.style.backgroundColor=color;node.append(chip,document.createTextNode(color));return node;}));
    }
    output.removeAttribute('data-error');
   }catch{output.textContent=form.dataset.error;output.setAttribute('data-error','true');}
  };
  form.addEventListener('input',update);form.addEventListener('submit',event=>{event.preventDefault();update();});update();
 }
}
if(typeof document!=='undefined'){bindTools();mountDateTime();}
