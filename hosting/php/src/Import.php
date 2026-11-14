<?php
/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/src/Import.php
 * Açıklama   : Sınırlı CSV/XLSX okuma, kolon eşleme, hata önizlemesi ve atomik taslak ürün aktarımı.
 */
declare(strict_types=1);
namespace Sexogate;
use PhpOffice\PhpSpreadsheet\Reader\Xlsx;
use PhpOffice\PhpSpreadsheet\Cell\DataType;
final class Import
{
    public const COLUMNS=['sku'=>'Stok kodu','name'=>'Ürün adı','nameEn'=>'İngilizce ürün adı','slug'=>'Ürün bağlantısı','category'=>'Kategori kodu','variantName'=>'Seçenek adı','price'=>'Satış fiyatı','cost'=>'Alış maliyeti','description'=>'Açıklama','descriptionEn'=>'İngilizce açıklama','image'=>'Görsel yolu','brand'=>'Marka','material'=>'Malzeme'];
    public function __construct(private Database $db,private Config $config){}
    private function read(string $file,string $format):array
    {
        RuleViolation::ensure(!str_contains($file,'://')&&is_file($file)&&!is_link($file)&&filesize($file)>0&&filesize($file)<=2000000,'IMPORT_FILE_INVALID','Dosya en fazla 2 MB boyutunda CSV veya XLSX olmalıdır.',400);
        if($format==='csv'){
            $raw=file_get_contents($file);RuleViolation::ensure(mb_check_encoding($raw,'UTF-8')&&!str_contains($raw,"\0"),'IMPORT_UTF8_REQUIRED','CSV dosyasını UTF-8 olarak kaydedin.',400);
            $stream=fopen('php://temp','w+b');fwrite($stream,preg_replace('/\A\xEF\xBB\xBF/','',$raw));rewind($stream);$first=fgets($stream);$separator=substr_count($first,';')>=substr_count($first,',')?';':',';rewind($stream);$rows=[];
            try{while(($row=fgetcsv($stream,32769,$separator,'"',''))!==false){RuleViolation::ensure(count($row)<=30&&count($rows)<501,'IMPORT_LIMIT','En fazla 500 veri satırı ve 30 sütun yüklenebilir.',400);if($row===[null])continue;$rows[]=$row;}}finally{fclose($stream);}return $rows;
        }
        $zip=new \ZipArchive();RuleViolation::ensure($zip->open($file,\ZipArchive::RDONLY)===true,'IMPORT_XLSX_INVALID','XLSX arşivi okunamadı.',400);
        try{$total=0;RuleViolation::ensure($zip->numFiles<=100,'IMPORT_LIMIT','XLSX içeriği sınırı aşıyor.',400);for($n=0;$n<$zip->numFiles;$n++){$entry=$zip->statIndex($n);$name=$entry['name'];$total+=$entry['size'];RuleViolation::ensure($entry['size']<=4000000&&$total<=8000000&&!preg_match('~(?:vbaProject|externalLinks|embeddings|drawings|\.\./|^/)~i',$name),'IMPORT_UNSAFE_ARCHIVE','Makro, dış kaynak veya gömülü nesne içeren dosya kabul edilmez.',400);if(preg_match('/\.(xml|rels)$/i',$name)){$xml=$zip->getFromIndex($n);RuleViolation::ensure(!preg_match('/<!\s*(?:DOCTYPE|ENTITY)|TargetMode\s*=\s*[\x22\x27]External/i',$xml),'IMPORT_EXTERNAL_CONTENT','Dış bağlantı veya XML varlığı içeren dosya kabul edilmez.',400);}}}finally{$zip->close();}
        $reader=new Xlsx();$info=$reader->listWorksheetInfo($file);RuleViolation::ensure(count($info)===1&&$info[0]['totalRows']<=501&&$info[0]['totalColumns']<=30,'IMPORT_LIMIT','Tek sayfa, en fazla 500 veri satırı ve 30 sütun yüklenebilir.',400);$reader->setReadDataOnly(true);$book=$reader->load($file);
        try{$sheet=$book->getActiveSheet();$rows=[];$expandedBytes=0;for($r=1;$r<=$info[0]['totalRows'];$r++){$row=[];for($c=1;$c<=$info[0]['totalColumns'];$c++){$cell=$sheet->getCell([$c,$r]);$v=$cell->getValue();$expandedBytes+=strlen(is_scalar($v)||(is_object($v)&&method_exists($v,'__toString'))?(string)$v:'');RuleViolation::ensure($expandedBytes<=2000000,'IMPORT_LIMIT','Açılmış hücre metinleri toplamı 2 MB sınırını aşamaz.',400);$row[]=$cell->getDataType()===DataType::TYPE_FORMULA?['formula'=>true]:(is_object($v)?(string)$v:$v);}$rows[]=$row;}return $rows;}finally{$book->disconnectWorksheets();}
    }
    public function preview(string $file,string $name,array $mapping,Principal $actor):array
    {
        $actor->require('catalog',true);$format=strtolower(pathinfo($name,PATHINFO_EXTENSION));RuleViolation::ensure(in_array($format,['csv','xlsx'],true)&&mb_strlen($name)<=255&&!str_contains($name,"\0"),'IMPORT_FORMAT','Yalnız CSV ve XLSX kabul edilir.',400);
        $raw=$this->read($file,$format);RuleViolation::ensure(count($raw)>=2,'IMPORT_EMPTY','Başlık ve en az bir veri satırı gerekir.',400);$header=array_shift($raw);foreach($header as &$v){RuleViolation::ensure(is_scalar($v),'IMPORT_HEADER','Sütun başlıkları metin olmalıdır.',400);$v=trim((string)$v);}unset($v);RuleViolation::ensure(count(array_unique($header))===count($header),'IMPORT_HEADER','Sütun başlıkları tekrarlanamaz.',400);
        $columns=[];foreach(self::COLUMNS as $field=>$label){$source=$mapping[$field]??(in_array($field,$header,true)?$field:$label);RuleViolation::ensure(is_string($source),'IMPORT_MAPPING','Sütun eşlemesini kontrol edin.',400);$position=array_search($source,$header,true);if(in_array($field,['sku','name','nameEn','slug','category','variantName','price','image'],true))RuleViolation::ensure($position!==false,'IMPORT_MAPPING','Gerekli sütun eksik: '.$label,400);$columns[$field]=$position;}
        $rows=[];$seenSku=[];$seenSlug=[];$errors=0;$catalog=new Catalog($this->db,$this->config);
        foreach($raw as $index=>$values){$data=[];$rowErrors=[];foreach($columns as $field=>$position){$v=$position===false?'':($values[$position]??'');if(is_array($v)||preg_match('/\A[=+@\-]/u',ltrim((string)$v))){$rowErrors[]='FORMULA_NOT_ALLOWED:'.self::COLUMNS[$field];$v='';}$data[$field]=trim((string)$v);if(!mb_check_encoding($data[$field],'UTF-8')||str_contains($data[$field],"\0")||mb_strlen($data[$field])>10000)$rowErrors[]='INVALID_TEXT:'.self::COLUMNS[$field];}
            try{$data['priceMinor']=Money::parseDecimal($data['price']);$data['costMinor']=Money::parseDecimal($data['cost']?:'0');$catalog->validateDraft($data);if(!$this->db->one('SELECT slug FROM categories WHERE slug=? AND active=true',[$data['category']]))$rowErrors[]='CATEGORY_NOT_FOUND';if(!is_file(dirname(__DIR__).'/public/assets'.$data['image']))$rowErrors[]='IMAGE_NOT_FOUND';}catch(RuleViolation $e){$rowErrors[]=$e->rule;}
            if(isset($seenSku[$data['sku']])||$this->db->one('SELECT id FROM variants WHERE sku=?',[$data['sku']]))$rowErrors[]='DUPLICATE_SKU';if(isset($seenSlug[$data['slug']])||$this->db->one('SELECT id FROM products WHERE slug=?',[$data['slug']]))$rowErrors[]='DUPLICATE_SLUG';$seenSku[$data['sku']]=true;$seenSlug[$data['slug']]=true;$rowErrors=array_values(array_unique($rowErrors));$errors+=count($rowErrors);$rows[]=['line'=>$index+2,'data'=>$data,'errors'=>$rowErrors];
        }
        $id=Database::id();$this->db->transaction(function()use($id,$actor,$name,$file,$format,$mapping,$rows,$errors){$this->db->execute("INSERT INTO import_batches(id,actor_id,file_name,file_sha256,format,column_mapping,payload,error_count,expires_at) VALUES(?,?,?,?,?,?,?,?,DATE_ADD(CURRENT_TIMESTAMP(3),INTERVAL 24 HOUR))",[$id,$actor->id,basename(str_replace('\\','/',$name)),hash_file('sha256',$file),$format,$this->config->json($mapping),$this->config->json($rows),$errors]);(new Audit($this->db))->record($actor,'preview','imports',$id,['rows'=>count($rows),'errors'=>$errors]);});return ['id'=>$id,'rows'=>$rows,'errorCount'=>$errors,'status'=>'preview'];
    }
    public function get(string $id,Principal $actor):array
    {$actor->require('catalog');$r=$this->db->one('SELECT * FROM import_batches WHERE id=?',[$id]);RuleViolation::ensure($r&&($actor->role==='admin'||$r['actor_id']===$actor->id),'IMPORT_NOT_FOUND','İçe aktarma kaydı bulunamadı.',404);$r['rows']=json_decode($r['payload'],true,32,JSON_THROW_ON_ERROR);unset($r['payload']);return $r;}
    public function commit(string $id,string $key,Principal $actor):array
    {
        $actor->require('catalog',true);$this->get($id,$actor);
        return (new Audit($this->db))->command($actor,$key,['import',$id],function()use($id,$actor){$batch=$this->db->one('SELECT * FROM import_batches WHERE id=? FOR UPDATE',[$id]);RuleViolation::ensure($batch['status']==='preview'&&(int)$batch['error_count']===0&&strtotime($batch['expires_at'].' UTC')>time(),'IMPORT_NOT_READY','Hatalı, süresi dolmuş veya işlenmiş önizleme aktarılamaz.');$rows=json_decode($batch['payload'],true,32,JSON_THROW_ON_ERROR);$catalog=new Catalog($this->db,$this->config);$created=[];
            foreach($rows as $row){$data=$row['data'];RuleViolation::ensure(!$this->db->one('SELECT id FROM variants WHERE sku=?',[$data['sku']])&&!$this->db->one('SELECT id FROM products WHERE slug=?',[$data['slug']]),'IMPORT_CHANGED','Önizlemeden sonra stok kodu veya bağlantı çakıştı. Dosyayı yeniden inceleyin.');$created[]=$catalog->insertDraft($data,$actor);}
            $this->db->execute("UPDATE import_batches SET status='committed',committed_at=CURRENT_TIMESTAMP(3) WHERE id=?",[$id]);(new Audit($this->db))->record($actor,'commit','imports',$id,['created'=>count($created)]);return ['id'=>$id,'created'=>count($created),'products'=>$created];});
    }
    public function listing(Principal $actor):array
    {$actor->require('catalog');return $this->db->all('SELECT id,file_name,status,error_count,created_at,expires_at FROM import_batches'.($actor->role==='admin'?'':' WHERE actor_id=?').' ORDER BY created_at DESC LIMIT 100',$actor->role==='admin'?[]:[$actor->id]);}
    public static function csv(array $rows):string
    {$stream=fopen('php://temp','w+b');fwrite($stream,"\xEF\xBB\xBF");foreach($rows as $row){$safe=array_map(fn($v)=>preg_match('/\A[=+@\-]/u',ltrim((string)$v))?"'".$v:(string)$v,$row);fputcsv($stream,$safe,';','"','');}rewind($stream);$value=stream_get_contents($stream);fclose($stream);return $value;}
    public static function errorLabel(string $code):string
    {$parts=explode(':',$code,2);$labels=['FORMULA_NOT_ALLOWED'=>'Formül içeren hücre kabul edilmez','INVALID_TEXT'=>'Metin biçimini veya uzunluğunu kontrol edin','CATEGORY_NOT_FOUND'=>'Etkin kategori bulunamadı','IMAGE_NOT_FOUND'=>'Kayıtlı görsel bulunamadı','DUPLICATE_SKU'=>'Stok kodu tekrarlanıyor veya daha önce kullanılmış','DUPLICATE_SLUG'=>'Ürün bağlantısı tekrarlanıyor veya daha önce kullanılmış','INVALID_PRODUCT'=>'Zorunlu ürün alanlarını kontrol edin','INVALID_SLUG'=>'Ürün bağlantısı küçük harf, rakam ve tire içermelidir','INVALID_MEDIA'=>'Kayıtlı katalog görseli seçilmelidir','INVALID_AMOUNT'=>'Tutar biçimini kontrol edin','INVALID_MONEY'=>'Tutar biçimini kontrol edin'];return ($labels[$parts[0]]??'Alan doğrulanamadı').(isset($parts[1])?' · '.$parts[1]:'');}
}
