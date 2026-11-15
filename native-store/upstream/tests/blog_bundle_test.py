import unittest,copy
from lib.blog_bundle import pack_bundle,unpack_bundle,merge_bundles
class BlogBundleTests(unittest.TestCase):
 def test_first_deployed_index_without_mime_is_verified_and_migrated(self):
  old_index,old=pack_bundle({'/assets/blog/old.svg':{'bytes':b'published','mime':'image/svg+xml'}});del old_index['files']['/assets/blog/old.svg']['mime']
  new_index,new=pack_bundle({'/assets/blog/new.svg':{'bytes':b'new','mime':'image/svg+xml'}});index,blob=merge_bundles(old_index,old,new_index,new);self.assertEqual(unpack_bundle(index,blob)['/assets/blog/old.svg']['bytes'],b'published')
  with self.assertRaisesRegex(ValueError,'hash'):merge_bundles(old_index,b'corrupted',new_index,new)
 def test_a_new_release_keeps_previous_published_image_bytes(self):
  old_index,old=pack_bundle({'/assets/blog/old.svg':{'bytes':b'approved old illustration','mime':'image/svg+xml'}});new_index,new=pack_bundle({'/assets/blog/new.svg':{'bytes':b'new approved illustration','mime':'image/svg+xml'}});index,blob=merge_bundles(old_index,old,new_index,new);images=unpack_bundle(index,blob);self.assertEqual(images['/assets/blog/old.svg']['bytes'],b'approved old illustration');self.assertEqual(images['/assets/blog/new.svg']['bytes'],b'new approved illustration')
 def test_an_immutable_url_cannot_silently_change(self):
  a,x=pack_bundle({'/assets/blog/a.svg':{'bytes':b'old','mime':'image/svg+xml'}});b,y=pack_bundle({'/assets/blog/a.svg':{'bytes':b'new','mime':'image/svg+xml'}})
  with self.assertRaisesRegex(ValueError,'immutable'):merge_bundles(a,x,b,y)
 def test_corruption_and_unindexed_bytes_are_rejected(self):
  index,blob=pack_bundle({'/assets/blog/a.svg':{'bytes':b'approved','mime':'image/svg+xml'}})
  with self.assertRaisesRegex(ValueError,'hash'):unpack_bundle(index,b'changed!')
  with self.assertRaisesRegex(ValueError,'hidden'):unpack_bundle(index,blob+b'not-an-editorial-image')
if __name__=='__main__':unittest.main()
