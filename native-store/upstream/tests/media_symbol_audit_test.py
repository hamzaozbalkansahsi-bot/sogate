import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('symbol_audit',ROOT/'scripts/media-symbol-audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


class SymbolAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.matcher=audit.SymbolMatcher()

    def test_real_standalone_flame_detected_without_any_adore_word(self):
        for filename in ['adore-gaming-flame-frame14.png','adore-gaming-flame-gray-frame10.png']:
            reference=np.array(Image.open(audit.REFERENCE_FOLDER/filename).convert('RGB'))
            for turns in [0,1]:
                symbol=np.ascontiguousarray(np.rot90(reference,turns))
                image=np.full((130,180,3),235,np.uint8)
                image[45:45+symbol.shape[0],80:80+symbol.shape[1]]=symbol
                hits=self.matcher.detect(image,targeted=True)
                self.assertTrue(any(h['confidence']>.98 for h in hits),(filename,turns,hits))

    def test_uniform_white_image_has_no_false_symbol(self):
        self.assertEqual(self.matcher.detect(np.full((130,180,3),255,np.uint8),targeted=True),[])

    def test_every_animation_frame_is_hash_bound_and_source_remains_unchanged(self):
        reference=np.array(Image.open(audit.REFERENCE_FOLDER/'adore-gaming-flame-frame14.png').convert('RGB'))
        frames=[]
        for x in [30,65]:
            rgb=np.full((100,150,3),230,np.uint8)
            rgb[40:40+reference.shape[0],x:x+reference.shape[1]]=reference
            frames.append(Image.fromarray(rgb))
        with tempfile.TemporaryDirectory(dir=ROOT/'artifacts') as folder:
            self.assertTrue(Path(folder).resolve().is_relative_to(ROOT.resolve()))
            path=Path(folder)/'reference.gif';frames[0].save(path,save_all=True,append_images=frames[1:],duration=[100,200],loop=0)
            source_sha=audit.media.sha(path.read_bytes())
            report=audit.scan_file((source_sha,path,True,[{'role':'test'}]))
            self.assertEqual(report['frameCount'],2)
            self.assertEqual(report['compositesScanned'],2)
            self.assertEqual({h['frame'] for h in report['hits']},{0,1})
            self.assertTrue(all(frame['rgbSha256'] for frame in report['frames']))
            self.assertEqual(audit.media.sha(path.read_bytes()),source_sha)


if __name__=='__main__':unittest.main()
