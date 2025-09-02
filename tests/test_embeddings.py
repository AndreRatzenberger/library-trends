import unittest
import numpy as np

from scout.embeddings import embed_text, to_blob, from_blob


class TestEmbeddings(unittest.TestCase):
    def test_embed_text_shapes_and_roundtrip(self):
        v0 = embed_text("")
        self.assertIsInstance(v0, np.ndarray)
        self.assertEqual(v0.shape[0], 768)

        v1 = embed_text("hello world")
        self.assertEqual(v1.shape, (768,))
        self.assertTrue(np.isfinite(v1).all())

        blob = to_blob(v1)
        v2 = from_blob(blob, 768)
        self.assertTrue(np.allclose(v1, v2))
