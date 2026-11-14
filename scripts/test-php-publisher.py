#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-php-publisher.py
# Açıklama   : FTP yazımı sırasında etkin dosyanın yarım okunmamasını ağsız doğrular.
import hashlib,importlib.util,io,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
root=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('php_publisher',root/'scripts/publish-php-test.py')
publisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)

class MemoryFTP:
    def __init__(self):self.files={'/test/index.php':b'old'};self.partial=False
    def storbinary(self,command,stream):
        target=command.removeprefix('STOR ');self.files[target]=b'partial'
        self.partial=self.files['/test/index.php']!=b'old'
        self.files[target]=stream.read()
    def retrbinary(self,command,callback):callback(self.files[command.removeprefix('RETR ')])
    def rename(self,source,target):self.files[target]=self.files.pop(source)
    def delete(self,target):self.files.pop(target,None)

class AtomicPublisherTest(unittest.TestCase):
    def test_failed_metadata_activation_preserves_the_previous_file(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'state.json';target.write_text('{"retained":true}',encoding='utf8')
            with patch('os.replace',side_effect=OSError('DISK_FULL')):
                with self.assertRaises(OSError):publisher.persist(target,{'retained':False})
            self.assertEqual('{"retained":true}',target.read_text('utf8'))
            self.assertEqual([target],list(Path(folder).iterdir()))
    def test_explicit_package_root_accepts_only_the_named_release_and_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            release='a'*24;archive=Path(folder)/(release+'.zip');archive.write_bytes(b'archive')
            package={'release':release,'archive':str(archive),'sha256':hashlib.sha256(b'archive').hexdigest()}
            self.assertEqual(archive.resolve(),publisher.validate_archive(package,Path(folder)))
            with self.assertRaises(ValueError):publisher.validate_archive(package,Path(folder)/'other')
            archive.write_bytes(b'changed')
            with self.assertRaises(ValueError):publisher.validate_archive(package,Path(folder))
    def test_active_entry_changes_only_after_upload_finishes(self):
        ftp=MemoryFTP();publisher.store_atomic(ftp,'/test/index.php',b'new')
        self.assertFalse(ftp.partial);self.assertEqual({'/test/index.php':b'new'},ftp.files)
    def test_main_site_is_rejected_before_any_write(self):
        ftp=MemoryFTP()
        with self.assertRaises(ValueError):publisher.store_atomic(ftp,'/index.html',b'new')
        self.assertEqual({'/test/index.php':b'old'},ftp.files)

if __name__=='__main__':unittest.main()
