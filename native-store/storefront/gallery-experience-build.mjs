/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/gallery-experience-build.mjs
 * Açıklama   : Galeri döngüsü ve etkin fotoğraf kontrollerini yalnız türetilmiş uygulamaya bağlar.
 */
import fs from'node:fs';import path from'node:path';import ts from'typescript';import{fileURLToPath}from'node:url';
const root=path.dirname(fileURLToPath(import.meta.url)),bundle=path.resolve(process.argv[2]||''),appFile=path.join(bundle,'public/app.js');
const scoped=path.basename(bundle).startsWith('native-stage-')||(path.basename(bundle)==='bundle'&&path.basename(path.dirname(bundle)).startsWith('native-stage-'));if(!scoped||!fs.existsSync(appFile))throw Error('GALLERY_EXPERIENCE_BUILD_SCOPE');
let app=fs.readFileSync(appFile,'utf8');if(app.includes('wrapGalleryIndex as sgWrapGalleryIndex'))throw Error('GALLERY_EXPERIENCE_ALREADY_APPLIED');
const replacements={
 selectPhoto:"function selectPhoto(index){const p=byId(currentRoute().product),viewport=$('#photo-viewport');if(!p||!viewport)return;gallery=sgWrapGalleryIndex(index,p.images?.length||0);viewport.scrollTo({left:gallery*viewport.clientWidth,behavior:'instant'});updatePhotoControls();}",
 setGallery:"function setGallery(index){const p=byId(currentRoute().product),viewport=$('#gallery-viewport');if(!p||!viewport)return;gallery=sgWrapGalleryIndex(index,p.images?.length||0);viewport.scrollTo({left:gallery*viewport.clientWidth,behavior:'instant'});updateGalleryControls();}",
 updatePhotoControls:"function updatePhotoControls(){const p=byId(currentRoute().product);if(!p)return;const total=p.images?.length||0,counter=$('#photo-counter');if(counter)counter.textContent=count(total?gallery+1:0)+' / '+count(total);document.querySelectorAll('[data-photo-step]').forEach(button=>{button.disabled=total<2;button.hidden=total<2;});}",
 updateGalleryControls:'function updateGalleryControls(){const p=byId(currentRoute().product);if(!p)return;const total=p.images?.length||0,counter=$(\'#gallery-counter\');if(counter)counter.textContent=count(total?gallery+1:0)+\' / \'+count(total);document.querySelectorAll(\'[data-gallery],[data-gallery-point]\').forEach(button=>button.setAttribute(\'aria-pressed\',String(Number(button.dataset.gallery??button.dataset.galleryPoint)===gallery)));const point=$(`[data-gallery-point="${gallery}"]`),points=point?.parentElement;if(point&&points)points.scrollLeft=point.offsetLeft-points.offsetLeft-(points.clientWidth-point.clientWidth)/2;document.querySelectorAll(\'[data-gallery-step]\').forEach(button=>{button.disabled=total<2;button.hidden=true;});}'
};
const tree=ts.createSourceFile('app.js',app,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS),found=new Map(Object.keys(replacements).map(name=>[name,[]]));function visit(node){if(ts.isFunctionDeclaration(node)&&found.has(node.name?.text))found.get(node.name.text).push(node);ts.forEachChild(node,visit);}visit(tree);for(const[name,nodes]of found)if(nodes.length!==1)throw Error('GALLERY_EXPERIENCE_HOOK_CHANGED:'+name);
const edits=[...found].map(([name,nodes])=>({node:nodes[0],replacement:replacements[name]})).sort((a,b)=>b.node.getStart(tree)-a.node.getStart(tree));for(const {node,replacement}of edits)app=app.slice(0,node.getStart(tree))+replacement+app.slice(node.end);
app="import {wrapGalleryIndex as sgWrapGalleryIndex} from './sexogate-gallery-experience-core.js?v=storefront';\n"+app;fs.copyFileSync(path.join(root,'gallery-experience-core.js'),path.join(bundle,'public/sexogate-gallery-experience-core.js'));fs.writeFileSync(appFile,app);
console.log(JSON.stringify({cyclicExpandedGallery:true,smallGalleryThumbsOnly:true,keyboardAndSwipePreserved:true,sourceSnapshotChanged:false}));
