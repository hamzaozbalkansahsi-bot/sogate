"""Build the decorative welcome SVG from public-domain Natural Earth geometry."""
from pathlib import Path
import hashlib,json,math,urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/welcome-poster';OUT.mkdir(exist_ok=True)
URL='https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson'
source=OUT/'natural-earth-countries.geojson'
if not source.exists():
 with urllib.request.urlopen(URL,timeout=30) as response: source.write_bytes(response.read())
data=json.loads(source.read_bytes())
targets={'DE','GB','AZ','KZ','TM','UZ','KG','IQ','IR','SY'}
def project(point):return ((point[0]+16)*7,(65-point[1])*9.2)
def shape(geometry):
 polygons=[geometry['coordinates']] if geometry['type']=='Polygon' else geometry['coordinates']
 result=[]
 for polygon in polygons:
  ring=polygon[0]
  if max(p[0] for p in ring)<-16 or min(p[0] for p in ring)>87 or max(p[1] for p in ring)<21 or min(p[1] for p in ring)>65:continue
  for ring in polygon:
   points=[project(p) for p in ring]
   result.append('M'+'L'.join(f'{x:.1f},{y:.1f}' for x,y in points)+'Z')
 return ''.join(result)

svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 400" fill="none">',
 '<defs><clipPath id="map"><path d="M0 0h720v400H0z"/></clipPath></defs>',
 '<path fill="#172D38" d="M0 0h720v400H0z"/>',
 '<g clip-path="url(#map)" stroke="#172D38" stroke-width=".9" stroke-linejoin="round">']
features=[]
for feature in data['features']:
 props=feature['properties'];code=props.get('ISO_A2_EH') or props.get('ISO_A2');d=shape(feature['geometry'])
 if not d:continue
 fill='#D8EC81' if code in targets else '#F5F2E9' if code=='TR' else '#2D4650'
 svg.append(f'<path data-country="{code}" d="{d}" fill="{fill}" fill-rule="evenodd"/>')
 if code in targets:features.append((code,props))
assert {code for code,_ in features}==targets
svg.append('</g>')
home=project((27.1428,38.4237))
svg.append('<g clip-path="url(#map)" stroke="#F5F2E9" stroke-width="1" stroke-opacity=".35">')
for code,props in features:
 x,y=project((props['LABEL_X'],props['LABEL_Y']));hx,hy=home
 midx=(hx+x)/2;midy=min(y,hy)-35
 svg.append(f'<path d="M{hx:.1f},{hy:.1f}Q{midx:.1f},{midy:.1f} {x:.1f},{y:.1f}"/>')
svg.append('</g>')
svg.append(f'<circle cx="{home[0]:.1f}" cy="{home[1]:.1f}" r="12" stroke="#F5F2E9" stroke-opacity=".45"/>')
svg.append(f'<circle cx="{home[0]:.1f}" cy="{home[1]:.1f}" r="4.5" fill="#172D38" stroke="#F5F2E9" stroke-width="2"/>')
svg.append('</svg>')
target=ROOT/'web/assets/brand/international-map.svg';target.write_text('\n'.join(svg)+'\n',encoding='utf-8')
(OUT/'map-source.json').write_text(json.dumps({'source':URL,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'license':'Public domain','licenseUrl':'https://www.naturalearthdata.com/about/terms-of-use/','highlightedCountries':sorted(targets),'svgSha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2)+'\n')
print(json.dumps({'built':True,'bytes':target.stat().st_size,'countries':len(targets)}))

# Interactive regions use the same frozen geometry, with no HTML from the source.
regions=[]
for feature in data['features']:
 props=feature['properties'];d=shape(feature['geometry'])
 if not d:continue
 code=props.get('ISO_A2_EH') or props.get('ISO_A2')
 names={lang:props.get('NAME_'+lang.upper()) or props['NAME_EN']for lang in ['tr','en','ru','ar']}
 regions.append({'id':props['ADM0_A3'],'code':code,'path':d,'names':names})
assert len({v['id']for v in regions})==len(regions)
payload={'viewBox':'-18 -10 780 430','regions':regions,'home':{'x':round(home[0],2),'y':round(home[1],2)},'routes':[]}
for code,props in features:
 x,y=project((props['LABEL_X'],props['LABEL_Y']));hx,hy=home
 payload['routes'].append(f'M{hx:.1f},{hy:.1f}Q{(hx+x)/2:.1f},{min(y,hy)-35:.1f} {x:.1f},{y:.1f}')
encoded=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('\u2028','\\u2028').replace('\u2029','\\u2029')
interactive=ROOT/'web/welcome-map-data.js';interactive.write_text('export const welcomeMapData=Object.freeze('+encoded+');\n',encoding='utf8')
evidence=ROOT/'artifacts/welcome-poster-v2';evidence.mkdir(exist_ok=True)
(evidence/'map-source.json').write_text(json.dumps({'source':URL,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'license':'Public domain','regions':len(regions),'confirmedDestinations':sorted(targets),'moduleSha256':hashlib.sha256(interactive.read_bytes()).hexdigest()},indent=2)+'\n')
print(json.dumps({'interactive':True,'regions':len(regions),'bytes':interactive.stat().st_size}))
