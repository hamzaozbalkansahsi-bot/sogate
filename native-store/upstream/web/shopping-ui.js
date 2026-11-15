import {cartLineKey} from './door-core.js?v=storefront-recovery-20261112-r1';
import {optionalPersonalizationAllowed} from './privacy-preferences.js?v=storefront-recovery-20261112-r1';
import {rankProductSearch,searchCategoryMatches,rememberSearch} from './catalog-search.js?v=storefront-recovery-20261112-r1';
import {distinctModels} from './shop-core.js?v=storefront-recovery-20261112-r1';
import {comparisonIds,comparisonRows,parseSpaceMeasure,fitAssessment,replaceCartVariant,favoritesToCart,validateCollections} from './shopping-core.js?v=storefront-recovery-20261112-r1';

// Public catalogue choices stay on this device. Private collections use owner-scoped,
// versioned requests; they never share the basket's background synchronisation queue.
export function createShoppingExperience(ctx){
 const {esc,e: t,loc,image,icon,href,productHref,productName,priceMarkup,byId,variantsOf,read,write,api,openDialog,toast,navigate,render,addCart}=ctx;
 const $=selector=>document.querySelector(selector),state=()=>ctx.state();
 const products=()=>state().catalog.products;
 const num=value=>new Intl.NumberFormat(state().locale,{maximumFractionDigits:2}).format(value);
 let comparison=[],comparisonReady=false,owner='',ownerEpoch=-1,ownerStatus='',lists=[],version=0,listStatus='idle',listError='',writing=false,request=0;
 let quickId='',quickQuantity=1,collectionProduct='',editingList='',collectionDraft='',collectionGeneration=0,fitRoute='',undo=null,undoTimer=null,searchIndex=-1;
 const own=()=>`${state().sessionEpoch}:${state().session.user?.id||'guest'}`;
 if(typeof window!=='undefined')window.addEventListener('nodeno:privacy-change',event=>{if(event.detail?.granted!==true){searchIndex=-1;const panel=$('#search-suggestions');if(panel){panel.replaceChildren();panel.hidden=true;}$('#search')?.setAttribute('aria-expanded','false');}});
 const cartFingerprint=()=>JSON.stringify({cart:state().cart,selected:[...state().selected].sort()});
 const allowed=()=>{if(state().sessionStatus!=='ready'){toast(t('loading'));return false;}return true;};
 const errorCopy=error=>t(error?.code==='collections_changed'?'collectionsConflict':String(error?.message||error?.code).includes('limit')?'collectionsLimit':'collectionsError');
 function selectionButton(p){return `<button type="button" class="card-compare" data-compare="${esc(p.id)}" aria-pressed="${comparison.includes(p.id)}">${icon('compare')}<span>${esc(t('compare'))}</span></button>`;}
 function cardTools(p){return `<div class="card-tools">${selectionButton(p)}<button type="button" class="icon-button" data-collect="${esc(p.id)}" aria-label="${esc(t('addCollection')+': '+productName(p))}">${icon('bookmark')}</button></div>`;}
 function quickButton(p){return `<button class="quick-open" type="button" data-quick="${esc(p.id)}">${esc(t('quickView'))}</button>`;}
 function productTools(p){return `<div class="product-shopping-tools">${selectionButton(p)}<button type="button" data-fit="${esc(p.id)}">${icon('measure')}${esc(t('fitTitle'))}</button><button type="button" data-collect="${esc(p.id)}">${icon('bookmark')}${esc(t('addCollection'))}</button></div>`;}
 function tabs(active){return `<nav class="shopping-tabs" aria-label="${esc(t('mySelection'))}">${[['favorites','favorites'],['collections','collections'],['recent','recent']].map(([page,key])=>`<a href="${esc(href(page))}" data-nav ${active===page?'aria-current="page"':''}>${esc(t(key))}</a>`).join('')}</nav>`;}
 function guide(){return `<section class="shopping-guide" aria-label="${esc(t('shoppingGuide'))}"><div><p class="eyebrow">NODENO</p><h2>${esc(t('chooseWithConfidence'))}</h2></div>${[['measure','spaceFind','spaceFindBody','catalog'],['compare','compare','compareBody','compare'],['bookmark','collections','collectionsBody','collections']].map(([ico,key,body,page])=>`<a href="${esc(href(page,page==='catalog'?{fit:'1'}:{}))}" data-nav><span class="guide-icon">${icon(ico)}</span><div><h3>${esc(t(key))}</h3><p>${esc(t(body))}</p></div></a>`).join('')}</section>`;}
 function syncOwner(){
  const next=state().session.user?.id||'guest',epoch=state().sessionEpoch;
  if(owner===next&&ownerEpoch===epoch&&ownerStatus===state().sessionStatus)return;
  owner=next;ownerEpoch=epoch;ownerStatus=state().sessionStatus;request++;collectionGeneration++;lists=[];version=0;writing=false;listStatus='idle';listError='';undo=null;
  for(const id of ['collection-dialog','variant-dialog'])$('#'+id)?.close();
  if(next==='guest'&&state().sessionStatus==='ready'){try{lists=validateCollections(read('nodeno.collections.guest.v1',[]),products());}catch{lists=[];}listStatus='ready';}
 }
 async function loadLists(){
  syncOwner();if(state().sessionStatus!=='ready'||listStatus==='loading'||listStatus==='ready')return;
  if(!state().session.user){listStatus='ready';return;}
  const expected=own(),token=++request;listStatus='loading';listError='';
  try{const data=await api('/collections');if(expected!==own()||token!==request)return;lists=validateCollections(data.collections,products());version=data.version;listStatus='ready';}
  catch(error){if(expected!==own()||token!==request)return;listStatus='error';listError=errorCopy(error);}
  if(expected!==own())return;if(state().route.page==='collections')render();if($('#collection-dialog')?.open)renderCollectionDialog();
 }
 async function saveLists(next,{merge=false}={}){
  if(writing||!allowed()||listStatus!=='ready')return false;
  const expected=own(),token=++request;let validated;
  try{validated=validateCollections(next,products());}catch(error){toast(errorCopy(error));return false;}
  writing=true;listError='';if($('#collection-name-form'))collectionDraft=$('#collection-name').value;refreshListsUI();
  try{
   if(state().session.user){const data=await api(merge?'/collections/merge':'/collections',merge?'POST':'PUT',{version,collections:validated});if(expected!==own()||token!==request)return false;lists=validateCollections(data.collections,products());version=data.version;}
   else{lists=validated;write('nodeno.collections.guest.v1',lists);}
   return true;
  }catch(error){if(expected!==own()||token!==request)return false;listError=errorCopy(error);if(error.code==='collections_changed')listStatus='error';return false;}
  finally{if(expected===own()&&token===request){writing=false;refreshListsUI();}}
 }
 function refreshListsUI(){if(state().route.page==='collections')render();if($('#collection-dialog')?.open)renderCollectionDialog();}
 function collectionNotice(){return listError?`<p class="error" role="alert">${esc(listError)}</p>${listStatus==='error'?`<button class="button" type="button" data-shopping="reload-lists">${esc(t('retry'))}</button>`:''}`:'';}
 function renderCollections(){
  syncOwner();const route=state().route,chosen=lists.find(row=>row.id===route.collection);
  if(listStatus==='idle')queueMicrotask(()=>void loadLists());
  const guest=read('nodeno.collections.guest.v1',[]),importReady=state().session.user&&Array.isArray(guest)&&guest.length;
  return `<div class="wrap shopping-page">${ctx.pageHeading('collections')}${tabs('collections')}<p class="subtle">${esc(t(state().session.user?'collectionsAccount':'collectionsGuest'))}</p>${collectionNotice()}${listStatus!=='ready'?`<p role="status">${esc(t(listStatus==='error'?'collectionsError':'loading'))}</p>`:`${importReady?`<div class="collection-import"><p>${esc(t('collectionsImportBody'))}</p><button class="button" data-shopping="import-lists" ${writing?'disabled':''}>${esc(t('collectionsImport'))}</button></div>`:''}<div class="collection-toolbar"><button class="button button-dark" data-shopping="new-list" ${writing?'disabled':''}>${icon('plus')}${esc(t('newCollection'))}</button></div><div class="collection-layout"><nav class="collection-list" aria-label="${esc(t('collections'))}">${lists.map(row=>`<a href="${esc(href('collections',{collection:row.id}))}" data-nav ${row.id===chosen?.id?'aria-current="page"':''}><span>${esc(row.name)}</span><b>${row.items.length}</b></a>`).join('')||`<p class="subtle">${esc(t('collectionsEmpty'))}</p>`}</nav><section class="collection-products">${chosen?`<div class="section-heading"><div><h2>${esc(chosen.name)}</h2><p class="subtle">${chosen.items.length} ${esc(t('items'))}</p></div><div class="collection-actions"><button class="link-button" data-list-rename="${chosen.id}" ${writing?'disabled':''}>${esc(t('renameCollection'))}</button><button class="link-button" data-list-delete="${chosen.id}" ${writing?'disabled':''}>${esc(t('deleteCollection'))}</button></div></div>${chosen.items.length?`<button class="button" data-list-cart="${chosen.id}">${esc(t('addSelectionToCart'))}</button><div class="product-grid">${chosen.items.map(id=>`<div class="collection-entry">${ctx.productCard(byId(id))}<button class="collection-remove-item link-button" data-list-remove="${chosen.id}" data-product="${esc(id)}" aria-label="${esc(t('removeCollectionItem')+': '+productName(byId(id)))}">${esc(t('removeCollectionItem'))}</button></div>`).join('')}</div>`:`<p>${esc(t('collectionEmpty'))}</p><a class="button" href="${esc(href('catalog'))}" data-nav>${esc(t('browse'))}</a>`}`:`<div class="collection-empty"><span>${icon('bookmark')}</span><h2>${esc(t('collectionsStart'))}</h2><p>${esc(t('collectionsBody'))}</p><a class="button" href="${esc(href('catalog'))}" data-nav>${esc(t('browse'))}</a></div>`}</section></div>`}</div>`;
 }
 function renderCollectionDialog(){
  const p=byId(collectionProduct),row=lists.find(list=>list.id===editingList),deleting=$('#collection-dialog').dataset.mode==='delete';
  $('#collection-content').innerHTML=`<div class="dialog-heading"><h2 id="collection-title">${esc(t(deleting?'deleteCollection':row?'renameCollection':p?'addCollection':'newCollection'))}</h2><button type="button" class="icon-button" data-close="collection-dialog" aria-label="${esc(t('close'))}">${icon('close')}</button></div>${p?`<div class="collection-product-preview">${image(p)}<strong>${esc(productName(p))}</strong></div>`:''}${collectionNotice()}${listStatus!=='ready'?`<p role="status">${esc(t('loading'))}</p>`:deleting?`<p>${esc(t('deleteCollectionConfirm'))}</p><p><strong>${esc(row?.name)}</strong></p><button type="button" class="button button-dark" data-list-delete-confirm="${row?.id||''}" ${writing?'disabled':''}>${esc(t('deleteCollection'))}</button>`:`${p&&lists.length?`<div class="collection-options">${lists.map(list=>`<button type="button" data-list-add="${list.id}" aria-pressed="${list.items.includes(p.id)}" ${writing?'disabled':''}><span>${esc(list.name)}</span><span>${esc(t(list.items.includes(p.id)?'inCollection':'addCollectionShort'))}</span></button>`).join('')}</div>`:''}<form id="collection-name-form"><label for="collection-name">${esc(t('collectionName'))}</label><input id="collection-name" name="name" maxlength="60" required value="${esc(collectionDraft)}" autocomplete="off" ${writing?'disabled':''}><button class="button button-dark" type="submit" ${writing?'disabled':''}>${esc(t(row?'save':'newCollection'))}</button></form>`}`;
 }
 async function openCollection(product='',edit='',mode=''){
  if(!allowed())return;syncOwner();collectionGeneration++;collectionProduct=product;editingList=edit;collectionDraft=lists.find(row=>row.id===edit)?.name||'';$('#collection-dialog').dataset.mode=mode;renderCollectionDialog();openDialog('collection-dialog');await loadLists();if($('#collection-dialog').open)renderCollectionDialog();
 }
 function renderRecent(){return `<div class="wrap shopping-page">${ctx.pageHeading('recent',`<button class="link-button" data-shopping="clear-recent">${esc(t('clear'))}</button>`)}${tabs('recent')}<p class="subtle">${esc(t('recentDevice'))}</p><div class="product-grid">${state().recent.map(byId).filter(Boolean).map(ctx.productCard).join('')||`<p>${esc(t('recentEmpty'))}</p>`}</div></div>`;}
 function renderCompare(){
  if(!comparisonReady){comparison=comparisonIds(read('nodeno.compare.v1',[]),products());comparisonReady=true;}
  const fromURL=new URLSearchParams(location.search).get('ids');if(fromURL!==null){comparison=comparisonIds(fromURL,products());write('nodeno.compare.v1',comparison);}
  const selected=comparison.map(byId).filter(Boolean);
  return `<div class="wrap shopping-page comparison-page">${ctx.pageHeading('compare')}<p class="subtle">${esc(t('compareBody'))}</p>${selected.length?`<div class="comparison-toolbar"><label><input type="checkbox" id="comparison-differences">${esc(t('differencesOnly'))}</label><button class="link-button" data-shopping="clear-compare">${esc(t('clear'))}</button></div><div class="comparison-scroll" role="region" tabindex="0" aria-label="${esc(t('compare'))}"><table class="comparison-table"><thead><tr><th scope="col">${esc(t('specifications'))}</th>${selected.map(p=>`<th scope="col"><button class="icon-button comparison-remove" data-compare="${esc(p.id)}" aria-label="${esc(t('remove')+': '+productName(p))}">${icon('close')}</button><a href="${esc(productHref(p.id))}" data-nav>${image(p)}<span>${esc(productName(p))}</span></a><button class="button button-dark" data-add="${esc(p.id)}">${esc(t('add'))}</button></th>`).join('')}</tr></thead><tbody>${comparisonRows(selected,state().locale).map(row=>`<tr data-different="${row.different}"><th scope="row">${esc(t(row.labelKey))}</th>${row.values.map(value=>`<td>${value?esc(value):`<span class="subtle">${esc(t('sourceNotSpecified'))}</span>`}</td>`).join('')}</tr>`).join('')}</tbody></table></div><a href="${esc(href('catalog'))}" data-nav class="button">${esc(t('compareAddMore'))}</a>`:`<div class="shopping-empty"><span>${icon('compare')}</span><h2>${esc(t('compareStart'))}</h2><a class="button button-dark" href="${esc(href('catalog'))}" data-nav>${esc(t('browse'))}</a></div>`}</div>`;
 }
 function refreshCompare(){
  write('nodeno.compare.v1',comparison);document.querySelectorAll('[data-compare]').forEach(button=>button.setAttribute('aria-pressed',String(comparison.includes(button.dataset.compare))));
  if(state().route.page==='compare'){const url=new URL(location.href);url.searchParams.set('ids',comparison.join(','));history.replaceState(history.state,'',url);render();}else syncChrome();
 }
 function syncChrome(){
  const container=$('#shopping-dock');if(!container)return;
  if(undo&&(undo.owner!==own()||undo.after!==cartFingerprint()))undo=null;
  container.innerHTML=`${undo?`<div class="cart-undo" role="status"><span>${esc(t('cartRemoved'))}</span><button class="link-button" data-shopping="undo-cart">${esc(t('undo'))}</button><button class="icon-button" data-shopping="dismiss-undo" aria-label="${esc(t('close'))}">${icon('close')}</button></div>`:''}${comparison.length&&state().route.page!=='compare'?`<div class="comparison-tray"><div class="comparison-miniatures">${comparison.map(byId).filter(Boolean).map(p=>`<button class="comparison-mini" data-compare="${esc(p.id)}" aria-label="${esc(t('remove')+': '+productName(p))}">${image(p,p.coverIndex||0,{alt:''})}${icon('close')}</button>`).join('')}</div><a class="button button-dark" href="${esc(href('compare',{ids:comparison.join(',')}))}" data-nav>${esc(t('compare'))} (${comparison.length}/4)</a><button class="icon-button" data-shopping="clear-compare" aria-label="${esc(t('clear'))}">${icon('close')}</button></div>`:''}`;
  container.hidden=!container.childElementCount;
  document.documentElement.dataset.shoppingDock=String(!container.hidden);
 }
 function cartRemoved(id){
  const before=state().cart.map(line=>({...line})),selection=[...state().selected];
  const next=id?before.filter(line=>cartLineKey(line)!==id):[],chosen=new Set(selection.filter(item=>id&&item!==id));
  if(!before.length)return;ctx.commitCart(next,chosen);undo={before,selection,after:cartFingerprint(),owner:own()};clearTimeout(undoTimer);undoTimer=setTimeout(()=>{undo=null;syncChrome();},8000);syncChrome();
 }
 function openQuick(id){quickId=id;quickQuantity=1;renderQuick();openDialog('quick-dialog');}
 function renderQuick(){const p=byId(quickId);if(!p)return;$('#quick-content').innerHTML=`<div class="dialog-heading"><h2 id="quick-title">${esc(t('quickView'))}</h2><button class="icon-button" data-close="quick-dialog" aria-label="${esc(t('close'))}">${icon('close')}</button></div><div class="quick-layout"><a href="${esc(productHref(p.id))}" data-nav>${image(p,p.coverIndex||0,{lazy:false})}</a><div><p class="eyebrow">NODENO</p><h3>${esc(productName(p))}</h3><bdi class="product-code" dir="ltr">${esc(p.code)}</bdi><p class="detail-price">${priceMarkup(p)}</p><p>${esc(t('productColor'))}: <strong>${esc(loc(p.variantColor)||t('sourceNotSpecified'))}</strong></p><div class="quick-colors">${variantsOf(p).map(v=>`<button class="quick-color" data-quick-variant="${esc(v.id)}" aria-pressed="${p.id===v.id}" aria-label="${esc(loc(v.variantColor)||v.code)}">${image(v,v.coverIndex||0,{alt:''})}<span>${esc(loc(v.variantColor))}</span></button>`).join('')}</div><label class="quick-quantity" for="quick-quantity">${esc(t('quantity'))}<input id="quick-quantity" name="quantity" autocomplete="off" type="number" min="1" max="99" value="${quickQuantity}" inputmode="numeric"></label><button type="button" class="button button-dark" data-quick-add="${esc(p.id)}">${icon('cart')}${esc(t('add'))}</button><a class="text-link quick-details" href="${esc(productHref(p.id))}" data-nav>${esc(t('viewProduct'))}</a><p class="subtle">${esc(t('productPaymentPending'))}</p></div></div>`;}
 function fitForm(id){const p=byId(id);$('#fit-content').innerHTML=`<div class="dialog-heading"><h2 id="fit-title">${esc(t('fitTitle'))}</h2><button class="icon-button" data-close="fit-dialog" aria-label="${esc(t('close'))}">${icon('close')}</button></div><p><strong>${esc(productName(p))}</strong></p><p class="subtle">${esc(t('fitHelp'))}</p><form id="fit-form" data-product="${esc(id)}"><div class="fit-inputs">${['width','height','depth'].map(axis=>`<label for="fit-${axis}">${esc(t('dimension'+axis[0].toUpperCase()+axis.slice(1)))}<input id="fit-${axis}" name="${axis}" type="text" inputmode="decimal" required pattern="[0-9]{1,5}([.,][0-9]{1,2})?" autocomplete="off"><span>cm</span></label>`).join('')}</div><button class="button button-dark" type="submit">${esc(t('checkFit'))}</button></form><div id="fit-result" role="status" aria-live="polite"></div><p class="subtle fit-note">${esc(t('fitNote'))}</p>`;openDialog('fit-dialog');}
 function cartVariantButton(p){return !['door','cabinet-front'].includes(p.productType)&&variantsOf(p).length>1?`<button class="link-button" data-cart-variant="${esc(p.id)}">${esc(t('changeColor'))}</button>`:'';}
 function openCartVariant(id){const p=byId(id);$('#variant-content').innerHTML=`<div class="dialog-heading"><h2 id="variant-title">${esc(t('changeColor'))}</h2><button class="icon-button" data-close="variant-dialog" aria-label="${esc(t('close'))}">${icon('close')}</button></div><h3>${esc(productName(p))}</h3><div class="cart-variant-options">${variantsOf(p).map(v=>`<button type="button" data-cart-replace="${esc(id)}" data-target="${esc(v.id)}" aria-pressed="${v.id===id}">${image(v)}<span>${esc(loc(v.variantColor))}</span><strong>${priceMarkup(v)}</strong></button>`).join('')}</div><p class="subtle">${esc(t('variantMergeNote'))}</p>`;openDialog('variant-dialog');}
 function bulkAdd(ids){const front=ids.find(id=>ctx.byId(id)?.productType==='cabinet-front');if(front){ctx.navigate(ctx.productHref(front));return;}try{if(!allowed())return;const next=favoritesToCart(state().cart,ids,products());ctx.commitCart(next,new Set([...state().selected,...ids]));toast(t('added'));}catch(error){toast(t('cartLimit'));}}
 function handleClick(event,el){
  if(!el)return false;let handled=true;
  if(el.dataset.compare){const id=el.dataset.compare;if(!byId(id))return true;if(comparison.includes(id))comparison=comparison.filter(value=>value!==id);else if(comparison.length<4)comparison.push(id);else{toast(t('compareLimit'));return true;}refreshCompare();}
  else if(el.dataset.quick)openQuick(el.dataset.quick);
  else if(el.dataset.quickVariant){quickId=el.dataset.quickVariant;renderQuick();}
  else if(el.dataset.quickAdd){if(allowed()&&$('#quick-quantity').reportValidity()){quickQuantity=Number($('#quick-quantity').value);addCart(el.dataset.quickAdd,quickQuantity);}}
  else if(el.dataset.fit)fitForm(el.dataset.fit);
  else if(el.dataset.collect)void openCollection(el.dataset.collect);
  else if(el.dataset.cartVariant){if(allowed())openCartVariant(el.dataset.cartVariant);}
  else if(el.dataset.cartReplace){if(allowed()){try{const result=replaceCartVariant(state().cart,el.dataset.cartReplace,el.dataset.target,products(),state().selected);ctx.commitCart(result.cart,result.selected);$('#variant-dialog').close();toast(t('colorChanged'));}catch{toast(t('quantityLimit'));}}}
  else if(el.dataset.listRename)void openCollection('',el.dataset.listRename);
  else if(el.dataset.listDelete)void openCollection('',el.dataset.listDelete,'delete');
  else if(el.dataset.listDeleteConfirm){const generation=collectionGeneration;void saveLists(lists.filter(row=>row.id!==el.dataset.listDeleteConfirm)).then(ok=>{if(ok&&generation===collectionGeneration){$('#collection-dialog').close();navigate(href('collections'));}});}
  else if(el.dataset.listAdd){const id=collectionProduct,next=lists.map(row=>row.id===el.dataset.listAdd?{...row,items:row.items.includes(id)?row.items.filter(item=>item!==id):[...row.items,id]}:row);void saveLists(next).then(ok=>{if(ok)toast(t('collectionSaved'));});}
  else if(el.dataset.listRemove){void saveLists(lists.map(row=>row.id===el.dataset.listRemove?{...row,items:row.items.filter(id=>id!==el.dataset.product)}:row));}
  else if(el.dataset.listCart)bulkAdd(lists.find(row=>row.id===el.dataset.listCart)?.items||[]);
  else if(el.dataset.searchTerm!==undefined){$('#search').value=el.dataset.searchTerm;submitSearch();}
  else if(el.dataset.remove){if(allowed())cartRemoved(el.dataset.remove);}
  else if(el.dataset.action==='clear-cart'){if(allowed())cartRemoved();}
  else switch(el.dataset.shopping){
   case'clear-compare':comparison=[];refreshCompare();break;
   case'undo-cart':if(undo&&undo.owner===own()&&undo.after===cartFingerprint()){const previous=undo;undo=null;ctx.commitCart(previous.before,new Set(previous.selection));}syncChrome();break;
   case'dismiss-undo':undo=null;syncChrome();break;
   case'new-list':void openCollection();break;
   case'reload-lists':listStatus='idle';void loadLists();refreshListsUI();break;
   case'import-lists':{void saveLists(read('nodeno.collections.guest.v1',[]),{merge:true}).then(ok=>{if(ok){try{localStorage.removeItem('nodeno.collections.guest.v1');}catch{}render();toast(t('collectionSaved'));}});break;}
   case'favorite-cart':bulkAdd([...state().saved]);break;
   case'clear-recent':ctx.clearRecent();render();break;
   case'clear-searches':if(optionalPersonalizationAllowed())write('nodeno.searches.v1',[]);showSuggestions();$('#search').focus();break;
   default:handled=false;
  }
  if(handled){event.preventDefault();return true;}
  if(el.dataset.searchAll&&optionalPersonalizationAllowed())write('nodeno.searches.v1',rememberSearch(read('nodeno.searches.v1',[]),el.dataset.searchAll));
  if(el.matches('a[data-nav],a[data-route]')&&!event.ctrlKey&&!event.metaKey&&!event.shiftKey&&!event.altKey&&event.button===0)document.querySelectorAll('#quick-dialog[open],#collection-dialog[open]').forEach(dialog=>dialog.close());
  return false;
 }
 function handleSubmit(event){
  const form=event.target;
  if(form.id==='collection-name-form'){
   event.preventDefault();const name=String(new FormData(form).get('name')||'').trim();if(!name){form.elements.name.setCustomValidity(t('collectionName'));form.reportValidity();return true;}
   const id=editingList||crypto.randomUUID().replaceAll('-',''),next=editingList?lists.map(row=>row.id===id?{...row,name}:row):[...lists,{id,name,items:collectionProduct?[collectionProduct]:[]}];
   const generation=collectionGeneration;void saveLists(next).then(ok=>{if(ok&&generation===collectionGeneration){$('#collection-dialog').close();toast(t('collectionSaved'));if(state().route.page==='collections')navigate(href('collections',{collection:id}));}});return true;
  }
  if(form.id==='fit-form'){
   event.preventDefault();const data=new FormData(form),space=Object.fromEntries(['width','height','depth'].map(axis=>[axis,parseSpaceMeasure(String(data.get(axis)||''))]));for(const axis of Object.keys(space))form.elements[axis].setCustomValidity(space[axis]===null?t('measureError'):'');if(!form.reportValidity())return true;
   const result=fitAssessment(byId(form.dataset.product),space);
   $('#fit-result').innerHTML=`<h3 class="fit-status" data-status="${result.status}">${esc(t('fit'+result.status[0].toUpperCase()+result.status.slice(1)))}</h3><dl>${result.axes.map(axis=>`<div><dt>${esc(t('dimension'+axis.axis[0].toUpperCase()+axis.axis.slice(1)))}</dt><dd>${axis.bounds?`${axis.bounds.min===axis.bounds.max?num(axis.bounds.max):num(axis.bounds.min)+'–'+num(axis.bounds.max)} cm` :esc(t('sourceNotSpecified'))}</dd><dd>${esc(t('spaceAvailable'))}: ${num(axis.available)} cm</dd></div>`).join('')}</dl>`;return true;
  }
  return false;
 }
 function handleInput(event){if(event.target.closest('#fit-form,#collection-name-form,.catalog-filter-form'))event.target.setCustomValidity('');}
 function handleChange(event){if(event.target.id==='comparison-differences'){$('.comparison-table').dataset.differences=String(event.target.checked);return true;}return false;}
 function showSuggestions(){
  const input=$('#search'),panel=$('#search-suggestions'),query=input.value.trim();searchIndex=-1;input.removeAttribute('aria-activedescendant');if(state().catalogStatus!=='ready')return;
  const matches=query?distinctModels(rankProductSearch(products(),query,state().locale)).slice(0,5):[],categories=query?searchCategoryMatches(state().catalog.categories,query,state().locale):[],history=optionalPersonalizationAllowed()?read('nodeno.searches.v1',[]):[];
  const options=query?`${categories.map(c=>`<a class="suggestion suggestion-category" href="${esc(href('catalog',{category:c.id}))}" data-nav>${icon('box')}<span>${esc(loc(c.name))}<small>${esc(t('categories'))}</small></span></a>`).join('')}${matches.map(p=>`<a class="suggestion" href="${esc(productHref(p.id))}" data-nav><span class="suggestion-photo">${image(p)}</span><span>${esc(productName(p))}<bdi dir="ltr">${esc(p.code)}</bdi></span><strong>${priceMarkup(p)}</strong></a>`).join('')}<a class="all-results" href="${esc(href('catalog',{q:query}))}" data-search-all="${esc(query)}" data-nav>${esc(t('showResults'))}</a>`:Array.isArray(history)?history.slice(0,6).map(term=>`<button type="button" class="suggestion search-history" data-search-term="${esc(term)}">${icon('search')}<span>${esc(term)}</span></button>`).join(''):'';
  panel.innerHTML=options?`<div class="suggestion-title"><span>${esc(t(query?'searchSuggestions':'recentSearches'))}</span>${!query?`<button type="button" class="link-button" data-shopping="clear-searches">${esc(t('clear'))}</button>`:''}</div><div id="search-options" role="listbox" aria-label="${esc(t('searchSuggestions'))}">${options}</div>`:'';
  panel.querySelectorAll('.suggestion,.all-results').forEach((item,i)=>{item.id='search-option-'+i;item.setAttribute('role','option');item.setAttribute('aria-selected','false');});
  panel.hidden=!options;input.setAttribute('role','combobox');input.setAttribute('aria-autocomplete','list');input.setAttribute('aria-controls','search-options');input.setAttribute('aria-expanded',String(!panel.hidden));
 }
 function submitSearch(){const input=$('#search'),query=input.value.trim();if(optionalPersonalizationAllowed())write('nodeno.searches.v1',rememberSearch(read('nodeno.searches.v1',[]),query));$('#search-suggestions').hidden=true;input.setAttribute('aria-expanded','false');navigate(href('catalog',{q:query}));input.blur();}
 function handleKeydown(event){
  if(event.target!==$('#search')||event.isComposing)return false;const panel=$('#search-suggestions'),options=[...panel.querySelectorAll('[role=option]')];
  if(event.key==='Escape'){panel.hidden=true;event.target.setAttribute('aria-expanded','false');event.target.removeAttribute('aria-activedescendant');return true;}
  if(!panel.hidden&&['ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();searchIndex=Math.max(0,Math.min(options.length-1,searchIndex+(event.key==='ArrowDown'?1:-1)));options.forEach((option,i)=>option.setAttribute('aria-selected',String(i===searchIndex)));if(options[searchIndex]){event.target.setAttribute('aria-activedescendant',options[searchIndex].id);options[searchIndex].scrollIntoView({block:'nearest'});}return true;}
  if(event.key==='Enter'&&!panel.hidden&&searchIndex>=0&&options[searchIndex]){event.preventDefault();options[searchIndex].click();return true;}return false;
 }
 function afterRender(){
  if(!comparisonReady&&state().catalogStatus==='ready'){comparison=comparisonIds(read('nodeno.compare.v1',[]),products());comparisonReady=true;}
  syncOwner();syncChrome();
  const fitRequested=state().route.page==='catalog'&&new URLSearchParams(location.search).get('fit')==='1';
  if(!fitRequested)fitRoute='';else if(fitRoute!==location.search){fitRoute=location.search;requestAnimationFrame(()=>{if(matchMedia('(max-width:700px)').matches){ctx.openFilters();}else{$('#desktop-space-filter')?.scrollIntoView({block:'center'});$('#desktop-max-Width')?.focus({preventScroll:true});}});}
 }
 return{cardTools,quickButton,productTools,tabs,guide,renderCollections,renderRecent,renderCompare,cartVariantButton,afterRender,syncChrome,showSuggestions,submitSearch,handleClick,handleSubmit,handleInput,handleChange,handleKeydown};
}
