// Selection keys are shared with nodenoBlogSurfaceForm; no product approval is inferred.
const choices=Object.freeze({
 material:['wood','mdf','veneer','metal','plastic','ceramic','unknown'],
 finish:['bare','coated','unknown'],
 exposure:['dry-interior','water','exterior','unknown'],
 condition:['sound','peeling','damp','unknown']
});
const materialSteps={wood:'wood-system',mdf:'mdf-edges',veneer:'thin-veneer',metal:'metal-system',plastic:'plastic-system',ceramic:'ceramic-system',unknown:'identify-material'};
const finishSteps={bare:'bare-finish',coated:'existing-finish',unknown:'identify-finish'};
const exposureSteps={'dry-interior':'dry-interior',water:'water-system',exterior:'exterior-system',unknown:'identify-exposure'};

/** Return a preparation-check plan, never a diagnosis or a paint recommendation. */
export function assessSurface(input){
 if(!input||typeof input!=='object'||Array.isArray(input)||Object.entries(choices).some(([key,values])=>!values.includes(input[key])))throw new RangeError('invalid_surface_selection');
 const {material,finish,exposure,condition}=input;
 let status='verification-required';const steps=[];
 if(condition==='damp'){status='moisture-first';steps.push('moisture-source','check-stability');}
 else if(condition==='peeling'){status='stability-first';steps.push('loose-finish','check-stability');}
 else steps.push(condition==='unknown'?'inspect-condition':'inspect-sound');
 if(status==='verification-required'&&Object.keys(choices).some(key=>input[key]==='unknown'))status='identify-first';
 steps.push(materialSteps[material],finishSteps[finish],exposureSteps[exposure],'verify-product','representative-sample');
 return {status,steps,verificationRequired:true};
}

const mounted=new WeakSet();
const ownText=(object,key)=>object&&Object.hasOwn(object,key)&&typeof object[key]==='string'?object[key]:null;
/** Bind only [data-blog-surface]; safe to call again after page integration. */
export function mountSurfaceTools(root=globalThis.document){
 if(!root||typeof root.querySelectorAll!=='function')return 0;
 let count=0;
 for(const form of root.querySelectorAll('[data-blog-surface]')){
  if(mounted.has(form))continue;
  const output=form.querySelector('[data-surface-status]'),list=form.querySelector('[data-surface-steps]');
  let copy;try{copy=JSON.parse(form.dataset.surfaceCopy);}catch{continue;}
  if(!output||!list||!ownText(copy,'invalidSelection')||!copy.statuses||!copy.steps)continue;
  const update=()=>{
   const input={};
   for(const [name,values]of Object.entries(choices)){
    const field=form.elements.namedItem(name);input[name]=field?.value;
    if(values.includes(input[name]))field?.removeAttribute('aria-invalid');
    else field?.setAttribute('aria-invalid','true');
   }
   try{
    const plan=assessSurface(input),status=ownText(copy.statuses,plan.status),texts=plan.steps.map(key=>ownText(copy.steps,key));
    if(!status||texts.some(text=>!text))throw new RangeError('surface_copy_missing');
    const nodes=texts.map(text=>{const item=form.ownerDocument.createElement('li');item.textContent=text;return item;});
    output.textContent=status;output.dataset.surfaceState=plan.status;list.replaceChildren(...nodes);
   }catch{
    output.textContent=copy.invalidSelection;output.dataset.surfaceState='invalid';list.replaceChildren();
   }
  };
  form.addEventListener('change',update);
  form.addEventListener('submit',event=>{event.preventDefault();update();});
  form.addEventListener('reset',()=>queueMicrotask(update));
  const button=form.querySelector('[data-surface-submit]');if(button)button.disabled=false;
  mounted.add(form);count++;update();
 }
 return count;
}
if(typeof document!=='undefined')mountSurfaceTools();
