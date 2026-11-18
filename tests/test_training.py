import json
import unittest
from pathlib import Path

import pandas as pd

from train import fit_reference


class TrainingPipelineTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(Path("config.json").read_text())
        cls.data = pd.read_csv("dataset/train.csv")

    def test_dataset_has_enough_rows(self):
        self.assertGreaterEqual(len(self.data), 100)

    def test_dataset_has_two_classes(self):
        self.assertEqual(self.data["label"].nunique(), 2)

    def test_required_features_exist(self):
        required = self.config["features"] + ["label"]
        self.assertTrue(set(required).issubset(self.data.columns))

    def test_model_training(self):
        model, accuracy = fit_reference(self.data, self.config)

        self.assertIsNotNone(model)
        self.assertGreaterEqual(accuracy, 0.0)
        self.assertLessEqual(accuracy, 1.0)

    def test_training_artifacts_exist(self):
        self.assertTrue(Path("artifacts/model.joblib").exists())
        self.assertTrue(Path("artifacts/metrics.json").exists())

        metrics = json.loads(Path("artifacts/metrics.json").read_text())

        self.assertEqual(metrics["student_id"], "FA23-BDS-021")
        self.assertEqual(metrics["training_rows"], len(self.data))
        self.assertIn("accuracy", metrics)
        self.assertIn("model_version", metrics)
        self.assertIn("git_sha", metrics)


if __name__ == "__main__":
    unittest.main()
