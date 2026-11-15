"""Exercise reviewed clean-feed creatives and localized discovery metadata without network calls."""
from pathlib import Path
import base64,json,subprocess
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];E=R/'artifacts/social-keywords-20261113';proof=json.loads((E/'release.json').read_bytes());C=R/proof['release'];Q=E/'isolated-social';Q.mkdir(exist_ok=True)
q=lambda x:"'"+str(x).replace('\\','/').replace("'","\\'")+"'"
program="require "+q(C/'private/social-worker.php')+"; $root=$argv[1];$db=nodenoControlDatabase($root);nodenoStudioSchema($db);$cat=json_decode(file_get_contents($argv[2].'/catalog.json'),true);$out=[];foreach(nodenoStudioCreativeProfiles()as $id=>$profile){try{$p=nodenoStudioProduct($cat,(string)$id);}catch(Throwable $e){continue;}if(!nodenoStudioCreativeProfile($p))continue;$post=['platform'=>'instagram','format'=>'carousel','locale'=>'tr','payload_json'=>json_encode(nodenoStudioCaption($p,'tr','instagram'))];$assets=nodenoStudioRenderImage($db,$root,$post,$p,$argv[2],$argv[3],$argv[4]);$copy=[];foreach(['tr','en','ru','ar']as $lang){$v=nodenoStudioCaption($p,$lang,'instagram');if(empty($v['keywords'])||count($v['hashtags'])<1)exit(8);$copy[$lang]=$v['caption'];}$out[]=['id'=>(string)$id,'name'=>nodenoStudioName($p,'tr'),'assets'=>$assets,'copy'=>$copy];}echo json_encode($out,JSON_UNESCAPED_UNICODE);"
r=subprocess.run([str(R/'artifacts/runtime-php/php.exe'),'-d','extension=gd','-d','display_errors=0','-r',program,str(Q),str(C/'private'),str(R/'artifacts/social-engine-20261112/preview/media'),str(C/'public')],capture_output=True,text=True,encoding='utf8');assert r.returncode==0,r.stderr[:700];items=json.loads(r.stdout);assert len(items)>=10
def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
cards=[]
for item in items:
 for i,h in enumerate(item['assets']):cards.append('<article><img src="'+uri(Q/'social-media'/(h+'.png'))+'"><p>'+item['id']+' · '+str(i+1)+'</p></article>')
with sync_playwright()as p:
 b=p.chromium.launch(executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium-1254/chrome-win64/chrome.exe'),headless=True)
 for batch in range(0,len(cards),20):
  group=cards[batch:batch+20];page=b.new_page(viewport={'width':1200,'height':int((len(group)+4)//5*330)})
  page.set_content('<style>body{margin:0;background:#eee;font:14px sans-serif}main{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;padding:10px}article{margin:0}img{width:224px;height:280px;object-fit:contain}p{margin:5px}</style><main>'+''.join(group)+'</main>');page.wait_for_function('()=>Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)');page.screenshot(path=str(E/f'creative-review-{batch//20+1}.png'));page.close()
 b.close()
(E/'local-social.json').write_text(json.dumps({'passed':True,'testOnly':True,'releaseHash':proof['releaseHash'],'reviewedProducts':len(items),'renderedFrames':len(cards),'locales':['tr','en','ru','ar'],'externalPostsCreated':0,'paidCalls':0,'items':items},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'reviewedProducts':len(items),'frames':len(cards)}))
