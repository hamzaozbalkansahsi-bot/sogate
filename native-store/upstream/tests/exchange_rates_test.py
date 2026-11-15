from pathlib import Path
import json,subprocess,unittest

ROOT=Path(__file__).resolve().parents[1]
PHP=ROOT/'artifacts/runtime-php/php.exe'
class ExchangeRatesTest(unittest.TestCase):
 def run_php(self,body):
  result=subprocess.run([str(PHP),'-r',"require 'hosting/exchange-rates.php';"+body],cwd=ROOT,capture_output=True,text=True,encoding='utf8')
  self.assertEqual(result.returncode,0,result.stderr);return json.loads(result.stdout)
 def test_weekly_highest_and_week_reset(self):
  result=self.run_php('''
  $xml=static fn($date,$usd)=>'<Tarih_Date Tarih="'.date('d.m.Y',strtotime($date)).'"><Currency CurrencyCode="USD"><Unit>1</Unit><ForexSelling>'.$usd.'</ForexSelling></Currency><Currency CurrencyCode="EUR"><Unit>1</Unit><ForexSelling>60.0000</ForexSelling></Currency></Tarih_Date>';
  $rates=['2026-11-09'=>'55.0000','2026-11-10'=>'52.0000','2026-11-11'=>'50.0000','2026-11-16'=>'40.0000'];
  $fetch=static function($dates)use($rates,$xml){$out=[];foreach($dates as $date)$out[$date]=isset($rates[$date])?['status'=>200,'body'=>$xml($date,$rates[$date])]:['status'=>404];return $out;};
  $a=nodenoFxBuild(new DateTimeImmutable('2026-11-11 18:00:00',new DateTimeZone('Europe/Istanbul')),$fetch);
  $b=nodenoFxBuild(new DateTimeImmutable('2026-11-16 18:00:00',new DateTimeZone('Europe/Istanbul')),$fetch);
  echo json_encode([$a,$b]);''')
  self.assertEqual(result[0]['rates']['USD']['rateMicros'],55000000)
  self.assertEqual(result[0]['rates']['USD']['date'],'2026-11-09')
  self.assertEqual(result[0]['weekStart'],'2026-11-09')
  self.assertEqual(result[1]['rates']['USD']['rateMicros'],40000000)
  self.assertEqual(result[1]['weekStart'],'2026-11-16')
 def test_exact_minor_units(self):
  result=self.run_php("echo json_encode([nodenoFxConvert(550000,['rateMicros'=>55000000,'unit'=>1]),nodenoFxConvert(50000,['rateMicros'=>25000000,'unit'=>100],0),nodenoFxConvert(1,['rateMicros'=>2000000,'unit'=>1]),nodenoFxConvert(1000000000000,['rateMicros'=>50178000,'unit'=>1])]);")
  self.assertEqual(result[:3],[10000,2000,1])
  self.assertEqual(result[3],(1000000000000*1000000+50178000//2)//50178000)
 def test_invalid_source_and_transport_failure_are_rejected(self):
  result=self.run_php('''$out=[];foreach(['<!DOCTYPE x [<!ENTITY y SYSTEM "file:///etc/passwd">]><x/>','<Tarih_Date Tarih="31.02.2026"/>','<Tarih_Date Tarih="10.11.2026"/>']as $xml){try{nodenoFxParse($xml);$out[]=false;}catch(Throwable $e){$out[]=true;}}try{nodenoFxBuild(new DateTimeImmutable('2026-11-11'),static fn($dates)=>array_fill_keys($dates,['status'=>500]));$out[]=false;}catch(Throwable $e){$out[]=true;}echo json_encode($out);''')
  self.assertEqual(result,[True]*4)
if __name__=='__main__':unittest.main()
