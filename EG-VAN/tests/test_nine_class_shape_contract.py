"""Data-free nine-output contract for the existing EG-VAN architecture.

This is not a dataset or paper-reproduction test. It performs no training,
checkpoint loading, image inference, or network download.
"""

import sys
import unittest
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from models.egvan import EGVAN  # noqa: E402


class NineClassShapeContract(unittest.TestCase):
    def test_fresh_model_logits_and_probabilities(self):
        torch.set_num_threads(2)
        model = EGVAN(num_classes=9, pretrained_efficient=False,
                      pretrained_resnet=False).eval()
        with torch.no_grad():
            logits = model(torch.zeros(2, 3, 64, 64))
            probabilities = logits.softmax(dim=1)
        self.assertEqual(tuple(logits.shape), (2, 9))
        self.assertTrue(bool(torch.isfinite(logits).all()))
        self.assertTrue(bool(torch.isfinite(probabilities).all()))
        self.assertTrue(bool((probabilities >= 0).all()))
        self.assertTrue(bool(torch.allclose(probabilities.sum(dim=1),
                                            torch.ones(2), atol=1e-6)))


if __name__ == "__main__":
    unittest.main()
