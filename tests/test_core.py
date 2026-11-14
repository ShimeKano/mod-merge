import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from modmerge.core import inspect_mod, build_java_bundle, merge_bedrock_packs


class ModMergeTests(unittest.TestCase):
    def test_detect_fabric(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "demo.jar"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("fabric.mod.json", json.dumps({"id": "demo", "name": "Demo"}))
            info = inspect_mod(p)
            self.assertEqual(info.kind, "Java mod")
            self.assertIn("Fabric", info.loaders)

    def test_java_bundle_keeps_jars_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "demo.jar"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("fabric.mod.json", '{"id":"demo","name":"Demo"}')
            out = Path(tmp) / "bundle.zip"
            build_java_bundle([str(p)], str(out), "Fabric")
            with zipfile.ZipFile(out) as z:
                self.assertIn("mods/demo.jar", z.namelist())
                self.assertIn("modmerge-report.json", z.namelist())

    def test_merge_bedrock_resource_packs(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs = []
            for idx in range(2):
                p = Path(tmp) / f"p{idx}.mcpack"
                manifest = {
                    "format_version": 2,
                    "header": {"name": f"Pack {idx}", "uuid": f"00000000-0000-0000-0000-00000000000{idx}", "version": [1, 0, 0]},
                    "modules": [{"type": "resources", "uuid": f"10000000-0000-0000-0000-00000000000{idx}", "version": [1, 0, 0]}]
                }
                with zipfile.ZipFile(p, "w") as z:
                    z.writestr("manifest.json", json.dumps(manifest))
                    z.writestr(f"textures/item/item{idx}.png", bytes([idx]))
                inputs.append(str(p))
            out = Path(tmp) / "merged.mcpack"
            result = merge_bedrock_packs(inputs, str(out))
            self.assertEqual(result["type"], "resource")
            with zipfile.ZipFile(out) as z:
                self.assertIn("textures/item/item0.png", z.namelist())
                self.assertIn("textures/item/item1.png", z.namelist())


if __name__ == "__main__":
    unittest.main()
