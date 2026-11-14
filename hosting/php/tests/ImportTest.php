<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/tests/ImportTest.php
 * Açıklama   : UTF-8 CSV/XLSX önizleme, formül reddi, tekil ve atomik taslak aktarımı.
 */
declare(strict_types=1);
require_once __DIR__.'/TestDatabase.php';
use PHPUnit\Framework\TestCase;
use Sexogate\{Import,Fixtures,Principal,RuleViolation};
use PhpOffice\PhpSpreadsheet\{Spreadsheet,Writer\Xlsx};
final class ImportTest extends TestCase
{
    private function row(string $sku='IMPORT-01',string $slug='ithal-bir'):array{return [$sku,'İç Giyim Ölçü ve Özellikler','Lingerie details',$slug,'ic-giyim','Bordo','149,50','50,00','Şişli Çeşme Iğdır ıİiIşŞğĞüÜöÖçÇ','Product details','/media/atelier-01.svg'];}
    private function headers():array{return ['sku','name','nameEn','slug','category','variantName','price','cost','description','descriptionEn','image'];}
    private function csv(array $rows):string{$file=tempnam(sys_get_temp_dir(),'sg-import-');$h=fopen($file,'wb');fwrite($h,"\xEF\xBB\xBF");fputcsv($h,$this->headers(),';','"','');foreach($rows as $row)fputcsv($h,$row,';','"','');fclose($h);return $file;}
    private function service(TestDatabase $f):Import{self::assertTrue(class_exists(Import::class),'PHP içe aktarma modülü eksik.');(new Fixtures($f->db,$f->config))->policies();return new Import($f->db,$f->config);}
    public function testCsvPreviewPreservesTurkishAndCommitCreatesDraftsOnlyOnce():void
    {$f=new TestDatabase();$service=$this->service($f);$a=new Principal('catalog','catalog',true);$file=$this->csv([$this->row()]);try{$batch=$service->preview($file,'ürün-listesi.csv',[],$a);self::assertSame(0,$batch['errorCount']);self::assertSame('İç Giyim Ölçü ve Özellikler',$batch['rows'][0]['data']['name']);self::assertSame(0,(int)$f->db->one('SELECT COUNT(*) n FROM products')['n']);$key=bin2hex(random_bytes(16));$r=$service->commit($batch['id'],$key,$a);self::assertEquals($r,$service->commit($batch['id'],$key,$a));self::assertSame(1,$r['created']);self::assertSame('draft',$f->db->one('SELECT status FROM products')['status']);self::assertSame(14950,(int)$f->db->one('SELECT price_minor FROM variants')['price_minor']);self::assertSame(0,(int)$f->db->one('SELECT on_hand FROM inventory_balance')['on_hand']);}finally{unlink($file);}}
    public function testDuplicateSkuAndFormulaAreVisibleErrorsAndBlockTheWholeBatch():void
    {$f=new TestDatabase();$service=$this->service($f);$a=new Principal('catalog','catalog',true);$bad=$this->row('=HYPERLINK("https://example.invalid")','ithal-uc');$file=$this->csv([$this->row(),$this->row('IMPORT-01','ithal-iki'),$bad]);try{$batch=$service->preview($file,'ürünler.csv',[],$a);self::assertGreaterThanOrEqual(2,$batch['errorCount']);$this->expectException(RuleViolation::class);$service->commit($batch['id'],bin2hex(random_bytes(16)),$a);}finally{unlink($file);}}
    public function testSkuCreatedAfterPreviewRollsBackEveryRow():void
    {$f=new TestDatabase();$service=$this->service($f);$a=new Principal('catalog','catalog',true);$file=$this->csv([$this->row(),$this->row('IMPORT-02','ithal-iki')]);try{$batch=$service->preview($file,'ürünler.csv',[],$a);$f->db->execute("INSERT INTO products(id,slug,name,name_en,category,image) VALUES('other','other','Diğer','Other','ic-giyim','/media/atelier-01.svg')");$f->db->execute("INSERT INTO variants(id,product_id,sku,name,name_en,price_minor) VALUES('other','other','IMPORT-02','Tek','One',100)");try{$service->commit($batch['id'],bin2hex(random_bytes(16)),$a);self::fail('Önizleme sonrası çakışma kabul edildi.');}catch(RuleViolation){}self::assertSame(1,(int)$f->db->one('SELECT COUNT(*) n FROM products')['n']);self::assertSame('preview',$f->db->one('SELECT status FROM import_batches')['status']);}finally{unlink($file);}}
    public function testXlsxReadsRawTextAndRejectsFormulaCellsWithoutCalculating():void
    {$f=new TestDatabase();$service=$this->service($f);$a=new Principal('catalog','catalog',true);$sheet=new Spreadsheet();$sheet->getActiveSheet()->fromArray([$this->headers(),$this->row(),$this->row('IMPORT-02','ithal-iki')]);$sheet->getActiveSheet()->setCellValue('B3','=SUM(1,2)');$file=tempnam(sys_get_temp_dir(),'sg-xlsx-');try{(new Xlsx($sheet))->save($file);$batch=$service->preview($file,'ürünler.xlsx',[],$a);self::assertSame('İç Giyim Ölçü ve Özellikler',$batch['rows'][0]['data']['name']);self::assertGreaterThan(0,$batch['errorCount']);self::assertStringContainsString('FORMULA',$batch['rows'][1]['errors'][0]);}finally{$sheet->disconnectWorksheets();unlink($file);}}
    public function testExternalRelationshipIsRejectedBeforeSpreadsheetReaderRuns():void
    {$f=new TestDatabase();$service=$this->service($f);$file=tempnam(sys_get_temp_dir(),'sg-xlsx-');$zip=new ZipArchive();$zip->open($file,ZipArchive::OVERWRITE);$zip->addFromString('xl/_rels/workbook.xml.rels','<Relationships><Relationship TargetMode="External" Target="http://127.0.0.1/private"/></Relationships>');$zip->close();try{$service->preview($file,'dosya.xlsx',[],new Principal('catalog','catalog',true));self::fail('Dış ilişki kabul edildi.');}catch(RuleViolation $e){self::assertSame('IMPORT_EXTERNAL_CONTENT',$e->rule);}finally{unlink($file);}}
    public function testCsvExportCannotStartAFormulaAndPreservesUtf8():void
    {$csv=Import::csv([['=1+1',' +SUM(1,2)','İstanbul Iğdır Hamza ÖZBALKAN']]);self::assertStringContainsString("'=1+1",$csv);self::assertStringContainsString("' +SUM(1,2)",$csv);self::assertStringContainsString('İstanbul Iğdır Hamza ÖZBALKAN',$csv);}
    public function testSharedStringsCannotExpandIntoAnUnboundedPreviewPayload():void
    {$f=new TestDatabase();$service=$this->service($f);$sheet=new Spreadsheet();$sheet->getActiveSheet()->fromArray([$this->headers()]);for($i=0;$i<200;$i++){$row=$this->row('LARGE-'.$i,'large-'.$i);$row[8]=str_repeat('x',9000);$row[9]=str_repeat('y',9000);$sheet->getActiveSheet()->fromArray([$row],null,'A'.($i+2));}$file=tempnam(sys_get_temp_dir(),'sg-xlsx-');try{(new Xlsx($sheet))->save($file);self::assertLessThan(2000000,filesize($file));$this->expectException(RuleViolation::class);$service->preview($file,'paylaşılan-metinler.xlsx',[],new Principal('catalog','catalog',true));}finally{$sheet->disconnectWorksheets();unlink($file);}}
}
