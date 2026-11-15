/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/theme/branding.js
 * Açıklama   : Özgün motoru değiştirmeden yalnız marka alanlarının görünür adını günceller.
 */
(()=>{'use strict';const scope='.sidebar-brand,.sidebar-foot,.topbar,.auth-brand,.auth-stage,.footer-brand,.store-footer,.site-footer,.logo,.eyebrow';
function brand(){for(const box of document.querySelectorAll(scope)){const walker=document.createTreeWalker(box,NodeFilter.SHOW_TEXT);let node;while(node=walker.nextNode())if(!node.parentElement.closest('script,style,code,pre,input,textarea')){const value=node.data.replace(/\bNODENO\b/g,'SEXOGATE').replace(/nodenohome\.com(?:\.tr)?/g,'sexogate.com').replace(/İyi tasarım\. Kolay yaşam\./g,'Tutkunu Keşfet.');if(value!==node.data)node.data=value;}for(const node of box.querySelectorAll('[alt],[aria-label]'))for(const attr of ['alt','aria-label']){const value=node.getAttribute(attr);if(value?.includes('NODENO'))node.setAttribute(attr,value.replace(/\bNODENO\b/g,'SEXOGATE'));}}}
brand();new MutationObserver(brand).observe(document.body,{childList:true,subtree:true});})();
