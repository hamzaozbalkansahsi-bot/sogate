#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-source-catalog.py
# Açıklama   : Kaynak katalog ayrıştırma, Türkçe metin ve güvenli URL sınırlarını sınar.
import importlib.util,unittest
from pathlib import Path
path=Path(__file__).with_name('source-catalog.py')
class SourceCatalogTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(path.exists(),'Source catalog collector is not implemented.')
        spec=importlib.util.spec_from_file_location('source_catalog',path);self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
    def test_sitemap_does_not_count_images_as_products(self):
        raw=b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"><url><loc>https://www.liona.com.tr/test.html</loc><image:image><image:loc>https://www.liona.com.tr/a.jpg</image:loc><image:title>Test Image</image:title></image:image></url></urlset>'
        rows=self.m.sitemap_rows(raw);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['title'],'Test');self.assertEqual(len(rows[0]['images']),1)
    def test_dtd_and_private_or_unknown_urls_are_rejected(self):
        with self.assertRaises(ValueError):self.m.sitemap_rows(b'<!DOCTYPE x SYSTEM "file:///etc/passwd"><x/>')
        for url in ['http://127.0.0.1/a','https://www.liona.com.tr@127.0.0.1/x','https://unknown.example/x','https://www.liona.com.tr:444/a']:
            with self.assertRaises(ValueError):self.m.canonical(url,'liona')
    def test_product_keeps_turkish_and_never_invents_stock_quantity(self):
        raw='''<html><h1>İç Giyim · Ölçü</h1><script type="application/ld+json">{"@type":"Product","name":"İç Giyim · Ölçü","sku":"GERÇEK-01","offers":{"price":"199.90","priceCurrency":"TRY","availability":"https://schema.org/InStock"}}</script></html>'''.encode()
        p=self.m.product_data(raw,'https://www.liona.com.tr/olcu.html');self.assertEqual(p['title'],'İç Giyim · Ölçü');self.assertEqual(p['quotedRetailMinor'],19990);self.assertIsNone(p['supplierQuantity']);self.assertTrue(p['publicInStock'])
    def test_category_ignores_product_carousel_and_encodes_turkish_url(self):
        raw='<h1>İç Giyim</h1><script type="application/ld+json">{"@type":"Product","name":"Önerilen Ürün","sku":"SKU-1","offers":{"price":"99.00","priceCurrency":"TRY"}}</script>'.encode()
        r=self.m.product_data(raw,'https://www.liona.com.tr/ödeme','category')
        self.assertEqual(r['title'],'İç Giyim');self.assertIsNone(r['sku']);self.assertIsNone(r['quotedRetailMinor'])
        self.assertEqual(self.m.canonical('https://www.liona.com.tr/ödeme?ad=İç','liona'),'https://www.liona.com.tr/%C3%B6deme?ad=%C4%B0%C3%A7')
    def test_api_query_includes_unavailable_products(self):
        self.assertTrue(hasattr(self.m,'api_url'),'Documented full-catalog API query is missing.')
        u=self.m.urllib.parse.urlsplit(self.m.api_url('products',2));q=self.m.urllib.parse.parse_qs(u.query)
        self.assertEqual(q['stock_status'],['instock,outofstock,onbackorder']);self.assertEqual(q['page'],['2']);self.assertEqual(u.hostname,'www.xshopum.com')
        categories=self.m.urllib.parse.parse_qs(self.m.urllib.parse.urlsplit(self.m.api_url('products/categories',1)).query);self.assertNotEqual(categories.get('orderby'),['id'])
        with self.assertRaises(ValueError):self.m.api_url('http://127.0.0.1/',1)
if __name__=='__main__':unittest.main()
