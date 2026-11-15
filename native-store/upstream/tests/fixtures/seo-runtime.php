<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require dirname(__DIR__, 2) . '/hosting/seo.php';
$input=json_decode(stream_get_contents(STDIN),true,512,JSON_THROW_ON_ERROR);
parse_str(ltrim($input['query'],'?'),$query);
echo json_encode(nodenoSeoPage($input['catalog'],$input['config'],$query),JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);
