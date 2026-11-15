from pathlib import Path
from datetime import datetime,date
import importlib.util,json,subprocess,unittest
from unittest.mock import MagicMock,patch
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('fx_refresh',R/'hosting/fx-refresh.py');fx=importlib.util.module_from_spec(s);s.loader.exec_module(fx)
def xml(day,usd):return ('<Tarih_Date Tarih="'+day.strftime('%d.%m.%Y')+'"><Currency CurrencyCode="USD"><Unit>1</Unit><ForexSelling>'+usd+'</ForexSelling></Currency><Currency CurrencyCode="EUR"><Unit>1</Unit><ForexSelling>60.0000</ForexSelling></Currency><Currency CurrencyCode="JPY"><Unit>100</Unit><ForexSelling>25.0000</ForexSelling></Currency></Tarih_Date>').encode()
class FxRefreshTest(unittest.TestCase):
 def test_temporary_transport_failure_retries_the_official_tls_source(self):
  day=date(2026,11,9);response=MagicMock();response.__enter__.return_value=response;response.status=200;response.geturl.return_value=fx.url(day);response.read.return_value=xml(day,'55')
  opener=MagicMock();opener.open.side_effect=[fx.urllib.error.URLError('TLS handshake timed out'),response]
  with patch.object(fx.urllib.request,'build_opener',return_value=opener):
   result=fx.fetch(day)
  self.assertEqual(result['rates']['USD']['rateMicros'],55000000);self.assertEqual(opener.open.call_count,2)
  self.assertTrue(all(call.kwargs['timeout']==20 for call in opener.open.call_args_list))
 def test_failed_transport_has_a_bounded_retry_and_unpublished_day_is_not_retried(self):
  day=date(2026,11,10);opener=MagicMock();opener.open.side_effect=fx.urllib.error.URLError('timed out')
  with patch.object(fx.urllib.request,'build_opener',return_value=opener):
   with self.assertRaises(ValueError):fx.fetch(day)
  self.assertEqual(opener.open.call_count,3)
  opener.open.reset_mock();opener.open.side_effect=fx.urllib.error.HTTPError(fx.url(day),404,'Not Found',{},None)
  with patch.object(fx.urllib.request,'build_opener',return_value=opener):self.assertIsNone(fx.fetch(day))
  self.assertEqual(opener.open.call_count,1)
 def test_weekly_highest_and_monday_reset(self):
  values={date(2026,11,9):'55.0000',date(2026,11,10):'52.0000',date(2026,11,11):'50.0000',date(2026,11,16):'40.0000'}
  fetch=lambda day:fx.parse(xml(day,values[day]),day)if day in values else None
  a=fx.build(datetime(2026,11,11,18,tzinfo=fx.IST),fetch);b=fx.build(datetime(2026,11,16,18,tzinfo=fx.IST),fetch)
  self.assertEqual(a['rates']['USD']['rateMicros'],55000000);self.assertEqual(a['rates']['USD']['date'],'2026-11-09');self.assertEqual(b['rates']['USD']['rateMicros'],40000000);self.assertEqual(a['rates']['JPY']['unit'],100)
 def test_revision_and_all_rates_match_the_php_producer(self):
  day=date(2026,11,9);body=xml(day,'55.0000');now=datetime(2026,11,9,18,tzinfo=fx.IST);expected=fx.build(now,lambda d:fx.parse(body,d)if d==day else None)
  code="require 'hosting/exchange-rates.php';$body="+json.dumps(body.decode())+";$r=nodenoFxBuild(new DateTimeImmutable('2026-11-09 18:00:00',new DateTimeZone('Europe/Istanbul')),static function($dates)use($body){$r=[];foreach($dates as $d)$r[$d]=['status'=>200,'body'=>$body];return $r;});echo json_encode($r);"
  result=subprocess.run([str(R/'artifacts/runtime-php/php.exe'),'-r',code],cwd=R,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stdout);self.assertEqual(json.loads(result.stdout),expected)
 def test_weekend_carry_and_malformed_sources(self):
  friday=date(2026,11,6);a=fx.build(datetime(2026,11,9,9,tzinfo=fx.IST),lambda day:fx.parse(xml(day,'55'),day)if day==friday else None);self.assertTrue(a['carriedForward']);self.assertEqual(a['weekStart'],'2026-11-09')
  for body in [b'<!DOCTYPE x [<!ENTITY x "x">]><x/>',xml(friday,'1.23e4'),xml(friday,'0'),xml(friday,'55').replace(b'06.11.2026',b'07.11.2026')]:
   with self.assertRaises((ValueError,Exception)):fx.parse(body,friday)
if __name__=='__main__':unittest.main()
