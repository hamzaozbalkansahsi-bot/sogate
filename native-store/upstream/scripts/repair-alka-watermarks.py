"""Learn the measured repeating overlay from matching images; produce review candidates."""
from pathlib import Path
import hashlib,importlib.util,json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion';OUT=O/'watermark-candidates';OUT.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('supplier_wm',R/'lib/supplier_watermarks.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=json.loads((O/'alka-multiroi-probe.json').read_bytes());selected=[p for p in rows if p['matches']>=2]
white=np.zeros((1254,1254,3),np.uint8)
for row in selected:white=np.maximum(white,np.asarray(Image.open(row['path']).convert('RGB')))
grey=white.mean(2);mask=(white.min(2)>210)&(white.max(2).astype(int)-white.min(2)<18)&(grey<253)
# Exclude large uniform photographic shadow footprints; keep letter-sized components.
import cv2
count,labels,stats,_=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
keep=np.zeros(count,bool)
for i in range(1,count):
 x,y,w,h,area=stats[i];keep[i]=4<=area<=18000 and w<320 and h<240
mask=keep[labels];transmission=white.astype(np.float32)/255;footprint=cv2.dilate(mask.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
Image.fromarray(white).save(OUT/'measured-background.png');Image.fromarray(mask.astype(np.uint8)*255).save(OUT/'measured-mask.png')
Image.fromarray(footprint.astype(np.uint8)*255).save(OUT/'candidate-footprint.png')
results=[]
for row in selected:
 source=np.asarray(Image.open(row['path']).convert('RGB'));output=m.reverse_multiply(source,transmission,mask);output=m.clear_background_residual(output,footprint);assert np.array_equal(source[~footprint],output[~footprint]);file=OUT/(row['id']+'.png');Image.fromarray(output).save(file)
 results.append({'productId':row['id'],'sourcePath':row['path'],'sourceSha256':hashlib.sha256(Path(row['path']).read_bytes()).hexdigest(),'outputPath':file.relative_to(R).as_posix(),'outputSha256':hashlib.sha256(file.read_bytes()).hexdigest(),'width':1254,'height':1254,'outsidePixelsUnchanged':True,'geometryGenerated':False,'reviewRequired':True,'publicationReady':False})
report={'method':'measured_multiply_overlay_inverse','candidateCount':len(results),'maskPixels':int(mask.sum()),'maskFraction':float(mask.mean()),'products':results,'publicationReady':False}
(OUT/'receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in report.items()if k!='products'}))
