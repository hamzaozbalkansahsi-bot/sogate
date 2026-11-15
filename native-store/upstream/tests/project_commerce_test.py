from pathlib import Path
import json,subprocess,unittest,tempfile
R=Path(__file__).resolve().parents[1];PHP=R/'artifacts/runtime-php/php.exe'
class ProjectCommerceTest(unittest.TestCase):
 def test_measured_door_rows_keep_exact_dimensions_and_server_owned_frame_and_glazing_fees(self):
  r=self.php('''$p=['id'=>'door-a','modelId'=>'model-a','code'=>'ND1','name'=>['tr'=>'Door'],'productType'=>'door','salePriceMinor'=>696500,'door'=>['glassAvailable'=>true,'charges'=>['depth'=>[17=>18000,19=>30000,21=>45500],'glazing'=>99000]]];$glass=['id'=>'door-glass-a','modelId'=>'model-a','productType'=>'door','door'=>['kind'=>'glazed']];$catalog=['products'=>[$p,$glass]];$o=['heightMm'=>2070,'leafWidthMm'=>770,'frameWidthMm'=>115];$out=[];
   foreach([95,115,145,165,185,215]as $width)$out[]=nodenoDoorPrice($p,array_replace($o,['frameWidthMm'=>$width]));
   $items=[['id'=>'door-a','quantity'=>2,'options'=>$o],['id'=>'door-a','quantity'=>2,'options'=>array_replace($o,['leafWidthMm'=>870,'frameWidthMm'=>145])],['id'=>'door-a','quantity'=>1,'options'=>array_replace($o,['leafWidthMm'=>870,'glazed'=>true,'glassModelId'=>'door-glass-a'])]];
   $out[]=nodenoCommerceQuote($catalog,$items,'TR');echo json_encode($out);''')
  self.assertEqual([x['unitPriceMinor']for x in r[:6]],[696500]*4+[726500,742000]);q=r[6];self.assertEqual(q['subtotalTryMinor'],696500*5+99000);self.assertTrue(q['minimumEligible']);self.assertEqual(len({x['key']for x in q['lines']}),3);self.assertEqual(q['lines'][0]['options']['frameWidthMm'],115)
 def test_measured_door_rejects_forged_glass_models_nonstandard_widths_and_conflicting_legacy_dimensions(self):
  r=self.php('''$p=['id'=>'door-a','modelId'=>'model-a','code'=>'ND1','name'=>['tr'=>'Door'],'productType'=>'door','salePriceMinor'=>696500,'door'=>['glassAvailable'=>true,'charges'=>['glazing'=>99000]]];$other=['id'=>'door-glass-b','modelId'=>'other-model','productType'=>'door','door'=>['kind'=>'glazed']];$o=['heightMm'=>2070,'leafWidthMm'=>770,'frameWidthMm'=>115];$out=[];
   foreach([['leafWidthMm'=>900],['frameWidthMm'=>110],['heightMm'=>2070.5],['height'=>220],['frameDepth'=>21],['glazed'=>true,'glassModelId'=>'door-glass-b'],['glazed'=>true,'glassModelId'=>'missing'],['glazed'=>true]]as $bad){try{nodenoCommerceQuote(['products'=>[$p,$other]],[['id'=>'door-a','quantity'=>5,'options'=>array_replace($o,$bad)]],'TR');$out[]=false;}catch(InvalidArgumentException $e){$out[]=true;}}echo json_encode($out);''')
  self.assertEqual(r,[True]*8)
 def php(self,body):
  result=subprocess.run([str(PHP),'-r',"require 'hosting/control-http.php';require_once 'hosting/wholesale.php';require 'hosting/door-commerce.php';"+body],cwd=R,capture_output=True,text=True,encoding='utf8')
  self.assertEqual(result.returncode,0,result.stderr+result.stdout);return json.loads(result.stdout)
 def test_area_and_door_minimums_are_independent_and_prices_are_server_owned(self):
  r=self.php('''$front=['id'=>'front-a','code'=>'ND 1','name'=>['tr'=>'Kapak'],'productType'=>'cabinet-front','salePriceMinor'=>273500,'front'=>['minimumApplies'=>true]];
   $door=['id'=>'door-a','code'=>'ND683','name'=>['tr'=>'Kapı'],'productType'=>'door','salePriceMinor'=>586000,'door'=>['charges'=>[]]];
   $catalog=['products'=>[$front,$door],'meta'=>['controlRevision'=>7]];
   $line=['id'=>'front-a','quantity'=>10,'options'=>['widthMm'=>500,'heightMm'=>1000,'application'=>'solid']];$out=[];
   foreach(['TR','DE']as $country)$out[]=nodenoCommerceQuote($catalog,[$line],$country);
   $out[]=nodenoCommerceQuote($catalog,[$line,['id'=>'door-a','quantity'=>4]],'TR');
   $out[]=nodenoCommerceQuote($catalog,[$line,['id'=>'door-a','quantity'=>5]],'TR');
   $line['quantity']=1;$line['options']=['widthMm'=>4999,'heightMm'=>1000,'application'=>'solid'];$out[]=nodenoCommerceQuote($catalog,[$line],'TR');
   foreach([['unitPriceMinor'=>1],['options'=>['widthMm'=>500,'heightMm'=>1000,'application'=>'solid','price'=>1]]]as $bad){try{nodenoCommerceQuote($catalog,[array_replace($line,$bad)],'TR');$out[]=false;}catch(InvalidArgumentException $e){$out[]=true;}}
   echo json_encode($out);''')
  self.assertEqual(r[0]['subtotalTryMinor'],1367500);self.assertTrue(r[0]['minimumEligible']);self.assertFalse(r[0]['checkoutEnabled'])
  self.assertFalse(r[1]['minimumEligible']);self.assertEqual(r[1]['missingFrontAreaMm2'],5000000)
  self.assertFalse(r[2]['minimumEligible']);self.assertEqual(r[2]['missingDoorSets'],1);self.assertTrue(r[3]['minimumEligible'])
  self.assertFalse(r[4]['minimumEligible']);self.assertEqual(r[4]['missingFrontAreaMm2'],1000);self.assertEqual(r[5:],[True,True])
 def test_whole_line_rounding_distinct_measurements_and_quote_only_options(self):
  r=self.php('''$p=['id'=>'front-a','code'=>'ND1','name'=>['tr'=>'Kapak'],'productType'=>'cabinet-front','salePriceMinor'=>273500,'front'=>['minimumApplies'=>true]];$a=['widthMm'=>333,'heightMm'=>777,'application'=>'solid'];$b=['widthMm'=>334,'heightMm'=>777,'application'=>'solid'];$line=['id'=>$p['id'],'quantity'=>10,'options'=>$a];$q=nodenoCommerceQuote(['products'=>[$p]],[$line,array_replace($line,['options'=>$b])],'TR');$p['salePriceMinor']=null;echo json_encode([$q,nodenoFrontPrice($p,$a,2),nodenoFrontPrice(array_replace($p,['salePriceMinor'=>273500]),array_replace($a,['application'=>'glazed']),2)]);''')
  self.assertNotEqual(r[0]['lines'][0]['key'],r[0]['lines'][1]['key'])
  self.assertEqual(r[0]['lines'][0]['lineTotalMinor'],(273500*333*777*10+500000)//1000000)
  self.assertIsNone(r[1]['lineTotalMinor']);self.assertTrue(r[2]['requiresQuote'])
 def test_configurations_survive_account_storage_and_social_merge(self):
  r=self.php('''require_once 'hosting/account.php';require_once 'hosting/social-auth.php';
   $front=['id'=>'front-a','productType'=>'cabinet-front'];$door=['id'=>'door-a','productType'=>'door','door'=>[]];$catalog=['products'=>[$front,$door]];
   $items=[['id'=>'front-a','quantity'=>500,'options'=>['widthMm'=>500,'heightMm'=>1000,'application'=>'solid']],['id'=>'front-a','quantity'=>2,'options'=>['widthMm'=>600,'heightMm'=>1000,'application'=>'solid']],['id'=>'door-a','quantity'=>5,'options'=>['frameDepth'=>19]]];
   echo json_encode(nodenoAccountState(['cart'=>$items,'favorites'=>[]],$catalog));''')
  self.assertEqual(len(r['cart']),3);self.assertEqual(r['cart'][0]['quantity'],500);self.assertEqual(r['cart'][2]['options']['frameDepth'],19)
 def test_one_square_millimetre_below_minimum_is_rejected(self):
  r=self.php('''$p=['id'=>'front-a','code'=>'ND1','name'=>['tr'=>'Kapak'],'productType'=>'cabinet-front','salePriceMinor'=>273500,'front'=>['minimumApplies'=>true]];
   $items=[['id'=>'front-a','quantity'=>1,'options'=>['widthMm'=>4990,'heightMm'=>1000,'application'=>'solid']],['id'=>'front-a','quantity'=>1,'options'=>['widthMm'=>99,'heightMm'=>101,'application'=>'solid']]];echo json_encode(nodenoCommerceQuote(['products'=>[$p]],$items,'TR'));''')
  self.assertEqual(r['frontAreaMm2'],4999999);self.assertEqual(r['missingFrontAreaMm2'],1);self.assertFalse(r['minimumEligible'])
 def test_account_merge_preserves_measured_lines_and_combines_only_identical_choices(self):
  with tempfile.TemporaryDirectory(prefix='nodeno-front-merge-')as temp:
   r=self.php('$root='+json.dumps(Path(temp).as_posix())+''';$db=nodenoAccountDatabase($root);
    foreach(['a','b']as $id)$db->prepare('INSERT INTO users(id,email,name,password_hash,created_at,updated_at)VALUES(?,?,?,?,?,?)')->execute([$id,$id.'@example.test','QA','not-a-usable-password',time(),time()]);
    $catalog=['products'=>[['id'=>'front-a','productType'=>'cabinet-front']]];$o=['widthMm'=>500,'heightMm'=>1000,'application'=>'solid'];$other=array_replace($o,['widthMm'=>600]);
    $states=['a'=>[['id'=>'front-a','quantity'=>10,'options'=>$o],['id'=>'front-a','quantity'=>2,'options'=>$other]],'b'=>[['id'=>'front-a','quantity'=>3,'options'=>$o]]];
    foreach($states as $id=>$items){$clean=nodenoAccountState(['cart'=>$items,'favorites'=>[]],$catalog);$db->prepare('INSERT INTO account_state(user_id,cart_json,favorites_json,updated_at)VALUES(?,?,?,?)')->execute([$id,json_encode($clean['cart']),'[]',time()]);}
    $target=$db->query("SELECT * FROM users WHERE id='a'")->fetch();$source=$db->query("SELECT * FROM users WHERE id='b'")->fetch();nodenoSocialMerge($db,$target,$source,$catalog);$stored=$db->query("SELECT cart_json FROM account_state WHERE user_id='a'")->fetchColumn();echo $stored;''')
   self.assertEqual(len(r),2);self.assertEqual([i['quantity']for i in r],[13,2]);self.assertEqual({i['options']['widthMm']for i in r},{500,600});self.assertEqual(len({i['key']for i in r}),2)
if __name__=='__main__':unittest.main()
