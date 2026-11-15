/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/variant-apply.mjs
 * Açıklama   : Seçenek doğrulamasını korunmuş çekirdeğin yalnız derleme kopyasına bağlar.
 */
import fs from 'node:fs';import path from 'node:path';import ts from 'typescript';import{fileURLToPath}from'node:url';import{execFileSync}from'node:child_process';
const root=path.dirname(fileURLToPath(import.meta.url)),bundle=path.resolve(process.argv[2]);if(!bundle.includes('native-stage-'))throw Error('VARIANT_BUILD_SCOPE');
execFileSync(path.resolve(root,'../../.local/php-runtime/php.exe'),[path.join(root,'variant-build.php'),path.join(bundle,'private')],{stdio:'inherit'});
for(const [a,b]of [['variants.php','private/sexogate-variants.php'],['variants.js','public/sexogate-variants.js'],['variant-ui.js','public/sexogate-variant-ui.js']])fs.copyFileSync(path.join(root,a),path.join(bundle,b));
fs.writeFileSync(path.join(bundle,'public/sexogate-variant-copy.js'),'export const variantCopy='+fs.readFileSync(path.join(root,'variant-copy.json'),'utf8')+';\n');
fs.appendFileSync(path.join(bundle,'public/sexogate-storefront.css'),'\n'+fs.readFileSync(path.join(root,'variant.css'),'utf8'));
function edit(file,from,to){const p=path.join(bundle,file),source=fs.readFileSync(p,'utf8');if(source.split(from).length!==2)throw Error('VARIANT_HOOK_CHANGED:'+file+':'+from.slice(0,50));fs.writeFileSync(p,source.replace(from,to));}
function prepend(file,name,code){const p=path.join(bundle,'public',file),source=fs.readFileSync(p,'utf8'),tree=ts.createSourceFile(file,source,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS),found=[];function walk(n){if(ts.isFunctionDeclaration(n)&&n.name?.text===name)found.push(n);ts.forEachChild(n,walk);}walk(tree);if(found.length!==1)throw Error('VARIANT_FUNCTION_CHANGED:'+name);const at=found[0].body.getStart(tree)+1;fs.writeFileSync(p,source.slice(0,at)+'\n'+code+'\n'+source.slice(at));}
function imports(file,code){const p=path.join(bundle,'public',file);fs.writeFileSync(p,code+'\n'+fs.readFileSync(p,'utf8'));}
edit('private/sexogate-catalog.php','declare(strict_types=1);',"declare(strict_types=1);\nrequire_once __DIR__.'/sexogate-variants.php';");
edit('private/sexogate-catalog.php','return $fields;',"$fields['orderSelections']=['label'=>'Sipariş için zorunlu seçenekler','type'=>'textarea','readonly'=>true];return $fields;");
edit('private/sexogate-catalog.php',"'sourceVariants'=>$json($work['sourceVariants'])", "'orderSelections'=>sexogateSelectionEditorText($product,$values,$work),'sourceVariants'=>$json($work['sourceVariants'])");
edit('private/sexogate-catalog.php',"$product['stockKnown']=false;", "$product['variantSelection']=sexogateSelectionProduct($product);$product['stockKnown']=false;");
edit('private/account.php','declare(strict_types=1);',"declare(strict_types=1);\nrequire_once __DIR__.'/sexogate-variants.php';");
edit('private/account.php',"$line=['id'=>$item['id'],'quantity'=>$item['quantity']];", "$line=['id'=>$item['id'],'quantity'=>$item['quantity']];if(sexogateSelectionRequired($known[$item['id']])){try{$line=sexogateSelectionAccountLine($known[$item['id']],$item,$strict);}catch(InvalidArgumentException $e){throw new NodenoAccountHttpError(422,'invalid_state');}}");
edit('private/social-auth.php',"$cart = [];$favorites = [];", "$cart = [];$favorites = [];$selectionProducts=array_column($catalog['products'],null,'id');");
edit('private/social-auth.php',"(isset($item['options'])?10000:99)","(in_array($selectionProducts[$item['id']]['productType']??'',['door','cabinet-front'],true)?10000:99)");
edit('private/door-commerce.php','declare(strict_types=1);',"declare(strict_types=1);\nrequire_once __DIR__.'/sexogate-variants.php';");
edit('private/door-commerce.php',"if($type==='door'){", "if(sexogateSelectionRequired($p)){$clean=sexogateSelectionLine($p,$item);$snapshot=sexogateSelectionSnapshot($p,$clean);$clean['selectionSnapshot']=$snapshot;$p['variantColor']=array_fill_keys(NODENO_STORE_LOCALES,$snapshot['summary']);$unit=$p['salePriceMinor']??null;if(!is_int($unit)||$unit<=0)$unit=null;$pricing=['unitPriceMinor'=>$unit,'knownUnitMinor'=>$unit,'reasons'=>[]];$total=$unit===null?null:$unit*$quantity;}elseif($type==='door'){");
// Existing order persistence stores this quote JSON verbatim; labels are never recalculated from tomorrow’s catalog.
edit('public/admin-payments.js',"${line.options?`<pre>","${line.selectionSnapshot?`<p><strong>${esc(line.selectionSnapshot.summary)}</strong>${line.selectionSnapshot.sourceSku?` · ${esc(line.selectionSnapshot.sourceSku)}`:''}</p>`:line.options?`<pre>");
edit('private/payment-documents.php',"$variant=$line['variant']??'';", "if(isset($line['selectionSnapshot']['summary']))return (string)$line['selectionSnapshot']['summary'];$variant=$line['variant']??'';");
imports('shop-core.js',"import {normalizeSelectionCart} from './sexogate-variants.js?v=variants';");
edit('public/shop-core.js','export function normalizeCart(value,products)', 'function legacyNormalizeCart(value,products)');
fs.appendFileSync(path.join(bundle,'public/shop-core.js'),'\nexport function normalizeCart(value,products){return normalizeSelectionCart(value,products,legacyNormalizeCart);}\n');
imports('app.js',"import {requiresSelection,selectionDescription,mergeSelectionLine} from './sexogate-variants.js?v=variants';\nimport {openSelection} from './sexogate-variant-ui.js?v=variants';\nimport {variantCopy} from './sexogate-variant-copy.js?v=variants';");
prepend('app.js','addCart',"if(requiresSelection(byId(id))){void chooseAdultVariant(id,quantity);return false;}");
prepend('app.js','buyProduct',"if(requiresSelection(byId(id))){void chooseAdultVariant(id,detailQuantity,null,true);return;}");
prepend('app.js','cartLineProduct',"if(requiresSelection(p))return {...p,variantColor:Object.fromEntries(Object.keys(variantCopy).map(lang=>[lang,selectionDescription(p,item,lang,variantCopy[lang])]))};");
const oldColor="${!isSupplierProduct(p)&&p.variantColor?`<p class=\"basket-color\">${esc(t('productColor'))}: ${esc(loc(p.variantColor))}</p>`:''}";
edit('public/app.js',oldColor,"${requiresSelection(p)?`<p class=\"sg-cart-selection ${item.pendingSelection?'sg-selection-pending':''}\">${esc(selectionDescription(p,item,locale,variantCopy[locale]))}</p><button type=\"button\" class=\"sg-selection-edit\" data-selection-edit=\"${esc(cartLineKey(item))}\">${esc(variantCopy[locale].edit)}</button>`:"+oldColor.slice(2,-1)+'}');
edit('public/app.js',"(!isSupplierProduct(p)?experience?.cartVariantButton(p):'')", "(!isSupplierProduct(p)&&!requiresSelection(p)?experience?.cartVariantButton(p):'')");
edit('public/app.js',"if(experience.handleClick(event,el))return;", "if(el.dataset.selectionEdit){const line=cart.find(row=>cartLineKey(row)===el.dataset.selectionEdit);if(line)void chooseAdultVariant(line.id,line.quantity,cartLineKey(line));return;}if(experience.handleClick(event,el))return;");
// Bulk additions must use the same picker. They cannot create an ambiguous size behind it.
prepend('shopping-ui.js','bulkAdd',"const configurable=ids.find(id=>ctx.byId(id)?.variantSelection?.required);if(configurable){if(allowed())addCart(configurable);return;}");
fs.appendFileSync(path.join(bundle,'public/app.js'),`\nasync function chooseAdultVariant(id,quantity,replaceKey=null,buy=false){
 if(selectionsBlocked()){toast(t('loading'));return;}const product=byId(id),old=replaceKey?cart.find(row=>cartLineKey(row)===replaceKey):null;if(!product)return;
 const line=await openSelection({product,quantity:clamp(quantity,product),locale,copy:variantCopy[locale],esc,image,name:productName(product),price:priceMarkup(product),current:old});if(!line||selectionsBlocked()||byId(id)!==product)return;
 try{cart=mergeSelectionLine(cart,line,replaceKey);if(replaceKey)selected.delete(replaceKey);selected.add(line.key);guestCheckout={details:guestCheckout.details,review:null};saveCheckoutDraft(guestCheckout,session.user?.id||'guest');selectionsChanged();insights?.event('cart',id);toast(t('added'));if(buy){selected=new Set([line.key]);navigate(href('checkout'));}}catch{toast(variantCopy[locale].limit);}
}\n`);
console.log(JSON.stringify({requiredProductSelection:true,serverValidation:true,orderSnapshot:true,consentBrandStates:true,sourceSnapshotChanged:false}));
