/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/variant-ui.js
 * Açıklama   : Varsayılan beden seçmeden erişilebilir ürün seçimi penceresi sunar.
 */
import {selectionLine} from './sexogate-variants.js?v=variants';
let active=null;
export function openSelection({product,quantity,locale,copy,esc,image,name,price,current}){
 active?.close();const trigger=document.activeElement,dialog=document.createElement('dialog');dialog.className='sg-variant-dialog';dialog.setAttribute('aria-labelledby','sg-variant-title');dialog.dir=['ar','fa'].includes(locale)?'rtl':'ltr';
 const schema=product.variantSelection,selection={...(current?.options?.selection||{})};
 dialog.innerHTML=`<header><div><p>SEXOGATE</p><h2 id="sg-variant-title">${esc(copy.title)}</h2></div><button class="sg-variant-close" type="button" aria-label="${esc(copy.close)}">×</button></header><div class="sg-variant-product"><div>${image(product)}</div><div><h3>${esc(name)}</h3><p>${price}</p></div></div><form><div class="sg-variant-options">${schema.axes.map(axis=>`<fieldset data-axis="${esc(axis.id)}"><legend>${esc(copy[axis.id]||axis.label)} <small>${esc(copy.required)}</small></legend><div>${axis.values.map(value=>`<button type="button" data-choice="${esc(value.id)}" aria-pressed="${selection[axis.id]===value.id}">${esc(value.label)}</button>`).join('')}</div></fieldset>`).join('')}</div><p class="sg-variant-message" role="status" aria-live="polite"></p><button class="button sg-variant-add" type="submit" disabled>${esc(copy.add)}</button><button type="button" class="sg-variant-cancel">${esc(copy.cancel)}</button></form>`;
 document.body.append(dialog);active=dialog;
 return new Promise(resolve=>{
  let result=null,done=false;
  const validate=()=>{let line=null;try{line=selectionLine(product,{id:product.id,quantity,options:{selection}});}catch{}const complete=schema.axes.length&&schema.axes.every(a=>selection[a.id]);dialog.querySelector('.sg-variant-add').disabled=!line;dialog.querySelector('.sg-variant-message').textContent=schema.blocked?copy.blocked:complete&&!line?copy.unavailable:'';return line;};
  for(const field of dialog.querySelectorAll('fieldset'))for(const button of field.querySelectorAll('[data-choice]'))button.onclick=()=>{selection[field.dataset.axis]=button.dataset.choice;for(const sibling of field.querySelectorAll('[data-choice]'))sibling.setAttribute('aria-pressed',String(sibling===button));validate();};
  dialog.querySelector('form').onsubmit=event=>{event.preventDefault();const line=validate();if(line){result=line;dialog.close();}};
  for(const button of dialog.querySelectorAll('.sg-variant-close,.sg-variant-cancel'))button.onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{if(done)return;done=true;dialog.remove();if(active===dialog)active=null;trigger?.isConnected&&trigger.focus({preventScroll:true});resolve(result);},{once:true});
  dialog.showModal();validate();dialog.querySelector('.sg-variant-close').focus({preventScroll:true});
 });
}
