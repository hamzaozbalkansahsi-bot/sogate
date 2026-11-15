export function openCheckoutTerms(title,text,opener){
 let dialog=document.getElementById('checkout-terms-dialog');
 if(!dialog){dialog=document.createElement('dialog');dialog.id='checkout-terms-dialog';dialog.className='checkout-terms-dialog';document.body.append(dialog);dialog.addEventListener('close',()=>dialog._opener?.isConnected&&dialog._opener.focus({preventScroll:true}));dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});}
 dialog.replaceChildren();dialog._opener=opener;
 const header=document.createElement('header'),heading=document.createElement('h2'),close=document.createElement('button'),body=document.createElement('article');
 heading.id='checkout-terms-heading';heading.textContent=title;dialog.setAttribute('aria-labelledby',heading.id);close.type='button';close.setAttribute('aria-label',({tr:'Kapat',en:'Close',ru:'Закрыть',ar:'إغلاق'})[document.documentElement.lang]||'Close');close.textContent='×';close.onclick=()=>dialog.close();header.append(heading,close);
 for(const paragraph of text.split(/\n\s*\n/)){const p=document.createElement('p');p.textContent=paragraph;body.append(p);}
 dialog.append(header,body);dialog.showModal();close.focus();
}
