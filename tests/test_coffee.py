import csv
import json
from pathlib import Path
import sys
import unittest
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from coffee import next_month
from coffee_dataset import export_coffee


class CoffeeEditionTests(unittest.TestCase):
    def test_contiguous_months_and_conversion(self):
        data = json.loads((ROOT / "web/data/coffee.json").read_text())
        previous = None
        for row in data["rows"]:
            if previous:
                self.assertEqual(row["month"], next_month(previous))
            if row["usd"] is None or row["fx"] is None:
                self.assertIsNone(row["cad"])
            else:
                self.assertAlmostEqual(row["cad"], row["usd"] * row["fx"], places=7)
            previous = row["month"]
        self.assertEqual(previous, data["end"])
        self.assertEqual(data["start"], data["rows"][0]["month"])
        self.assertGreaterEqual(len(data["rows"]), 117)

    def test_machine_readable_dataset_and_csv_agree(self):
        with TemporaryDirectory() as tmp:
            stage = Path(tmp)
            (stage / "data").mkdir()
            (stage / "data/coffee.json").write_bytes((ROOT / "web/data/coffee.json").read_bytes())
            schema = json.loads(export_coffee(stage))
            with (stage / "data/coffee.csv").open() as raw:
                rows = list(csv.DictReader(raw))
            self.assertEqual(schema["temporalCoverage"], rows[0]["month"] + "/" + rows[-1]["month"])
            self.assertTrue(schema["distribution"]["contentUrl"].endswith("/data/coffee.csv"))
            self.assertEqual(len(schema["isBasedOn"]), 3)
