/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/mega-menu-build.mjs
 * Açıklama   : Görselli mega menüyü yalnız türetilmiş native paketinin renderMega işlevine bağlar.
 */
import fs from'node:fs';import path from'node:path';import ts from'typescript';import{fileURLToPath}from'node:url';
const sourceRoot=path.dirname(fileURLToPath(import.meta.url)),bundle=path.resolve(process.argv[2]||''),appFile=path.join(bundle,'public/app.js'),cssFile=path.join(bundle,'public/sexogate-storefront.css');
const scoped=path.basename(bundle).startsWith('native-stage-')||(path.basename(bundle)==='bundle'&&path.basename(path.dirname(bundle)).startsWith('native-stage-'));if(!scoped||!fs.existsSync(appFile)||!fs.existsSync(cssFile))throw Error('MEGA_MENU_BUILD_SCOPE');
let app=fs.readFileSync(appFile,'utf8');if(app.includes('renderMegaMenu as renderSexogateMegaMenu'))throw Error('MEGA_MENU_ALREADY_APPLIED');const tree=ts.createSourceFile('app.js',app,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS),matches=[];function visit(node){if(ts.isFunctionDeclaration(node)&&node.name?.text==='renderMega')matches.push(node);ts.forEachChild(node,visit);}visit(tree);if(matches.length!==1)throw Error('MEGA_MENU_RENDER_HOOK_CHANGED');
const replacement=`function renderMega(){const roots=rootCategories().filter(c=>categoryCount(c.id)>0),active=roots.find(c=>c.id===megaActive)||roots[0],target=$('#mega-menu');target.classList.add('sg-mega-menu');if(!active){megaActive='';target.innerHTML='';target.hidden=true;$('#category-trigger')?.setAttribute('aria-expanded','false');return;}megaActive=active.id;target.innerHTML=renderSexogateMegaMenu({catalog,active,roots,locale,esc,loc,href,image,categoryCount,categoryPhoto,t,count,icon});}`;
app=app.slice(0,matches[0].getStart(tree))+replacement+app.slice(matches[0].end);app="import {renderMegaMenu as renderSexogateMegaMenu} from './sexogate-mega-menu-renderers.js?v=storefront';\n"+app;
const escape="if(event.key==='Escape'){closePanels();return;}";
if(app.split(escape).length!==2)throw Error('MEGA_MENU_ESCAPE_HOOK_CHANGED');
app=app.replace(escape,"if(event.key==='Escape'){const megaWasOpen=$('#mega-menu')&&!$('#mega-menu').hidden;closePanels();if(megaWasOpen)$('#category-trigger')?.focus({preventScroll:true});return;}");
const renderer=fs.readFileSync(path.join(sourceRoot,'mega-menu-renderers.js'),'utf8');if(renderer.split("'./mega-menu-core.js'").length!==2)throw Error('MEGA_MENU_CORE_IMPORT_CHANGED');
fs.copyFileSync(path.join(sourceRoot,'mega-menu-core.js'),path.join(bundle,'public/sexogate-mega-menu-core.js'));fs.writeFileSync(path.join(bundle,'public/sexogate-mega-menu-renderers.js'),renderer.replace("'./mega-menu-core.js'","'./sexogate-mega-menu-core.js?v=storefront'"));fs.writeFileSync(appFile,app);fs.appendFileSync(cssFile,'\n'+fs.readFileSync(path.join(sourceRoot,'mega-menu.css'),'utf8'));
console.log(JSON.stringify({megaMenuImages:true,emptyCategoriesHidden:true,keyboardHooksPreserved:true,sourceSnapshotChanged:false}));
