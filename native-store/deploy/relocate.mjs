/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/deploy/relocate.mjs
 * Açıklama   : Özgün kaynakları değiştirmeden yayın kopyasının marka ve URL kökünü taşır.
 */
import fs from 'node:fs';
import path from 'node:path';
import ts from 'typescript';
export const MOUNT='/__SEXOGATE_MOUNT__';
export function brandText(source){return source.replace(/https:\/\/(?:www\.)?nodenohome\.com(?:\.tr)?/g,'https://sexogate.com'+MOUNT).replace(/(?:www\.)?nodenohome\.com(?:\.tr)?/g,'sexogate.com').replace(/\bNODENO\b/g,'SEXOGATE');}
export function relocateText(source){return brandText(source).replace(/((?:href|src|action|poster)=["'])\/(?!\/|__SEXOGATE_MOUNT__)/gi,'$1'+MOUNT+'/').replace(/(url\(\s*["']?)\/(?!\/|__SEXOGATE_MOUNT__)/gi,'$1'+MOUNT+'/');}
export function relocateJs(source,name='module.js'){
 const text=relocateText(source),file=ts.createSourceFile(name,text,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS),edits=[],relativeHelpers=new Set();
 // fetch('/api/account'+path) gibi sarmalayıcılara verilen /state kök URL değildir.
 function helpers(node){if(ts.isFunctionDeclaration(node)&&node.name&&node.parameters[0]&&ts.isIdentifier(node.parameters[0].name)){const parameter=node.parameters[0].name.text;function scan(value){if(ts.isCallExpression(value)&&ts.isIdentifier(value.expression)&&value.expression.text==='fetch'){const arg=value.arguments[0];if(arg&&ts.isBinaryExpression(arg)&&arg.operatorToken.kind===ts.SyntaxKind.PlusToken&&ts.isStringLiteralLike(arg.left)&&/^\/api(?:\/|$)/.test(arg.left.text.startsWith(MOUNT)?arg.left.text.slice(MOUNT.length):arg.left.text)&&arg.right.getText(file).includes(parameter))relativeHelpers.add(node.name.text);}ts.forEachChild(value,scan);}if(node.body)scan(node.body);}ts.forEachChild(node,helpers);}helpers(file);
 function helperSuffix(node){let argument=node;while(argument.parent&&(ts.isBinaryExpression(argument.parent)||ts.isParenthesizedExpression(argument.parent)||ts.isConditionalExpression(argument.parent)||ts.isTemplateExpression(argument.parent)))argument=argument.parent;const call=argument.parent;return ts.isCallExpression(call)&&call.arguments[0]===argument&&ts.isIdentifier(call.expression)&&relativeHelpers.has(call.expression.text);}
 function childPath(node){for(let current=node,parent=node.parent;parent;current=parent,parent=parent.parent){if(ts.isBinaryExpression(parent)&&parent.operatorToken.kind===ts.SyntaxKind.PlusToken){if(parent.right===current)return true;}else if(!ts.isParenthesizedExpression(parent)&&!ts.isConditionalExpression(parent))break;}return false;}
 function walk(node){
  if((ts.isStringLiteralLike(node)||ts.isTemplateHead(node))&&node.text.startsWith('/')&&!node.text.startsWith('//')&&!node.text.startsWith(MOUNT)){
   const rootUrl=node.text!=='/'||(ts.isNewExpression(node.parent)&&node.parent.expression.getText(file)==='URL');
   if(rootUrl&&!childPath(node)&&!helperSuffix(node))edits.push(node.getStart(file)+1);
  }
  ts.forEachChild(node,walk);
 }
 walk(file);let result=text;for(const position of edits.sort((a,b)=>b-a))result=result.slice(0,position)+MOUNT+result.slice(position);
 return result.replaceAll('/^\\/media\\/','/^\\/__SEXOGATE_MOUNT__\\/media\\/');
}
if(process.argv[2]){
 const root=path.resolve(process.argv[2]);let count=0;
 function visit(folder){for(const item of fs.readdirSync(folder,{withFileTypes:true})){const name=path.join(folder,item.name);if(item.isDirectory())visit(name);else if(item.isFile()&&name.endsWith('.js')){fs.writeFileSync(name,relocateJs(fs.readFileSync(name,'utf8'),name));count++;}}}
 visit(root);console.log(JSON.stringify({relocatedJavaScriptModules:count}));
}
