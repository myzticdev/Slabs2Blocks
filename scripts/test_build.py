"""Inspect the installed recipe view at version and overlay boundaries."""
import hashlib
import io
import json
import unittest
import zipfile

import build


def installed(archive, version):
    with zipfile.ZipFile(io.BytesIO(archive)) as pack:
        meta = json.loads(pack.read("pack.mcmeta"))
        prefixes = [""]
        for entry in meta.get("overlays", {}).get("entries", []):
            if tuple(entry["min_format"]) <= version <= tuple(entry["max_format"]):
                prefixes.append(entry["directory"] + "/")
        folder = "recipe" if version[0] >= 48 else "recipes"
        active = {}
        for prefix in prefixes:
            root = prefix + f"data/slabs2blocks/{folder}/"
            for path in pack.namelist():
                if path.startswith(root):
                    active[path[len(root):-5]] = json.loads(pack.read(path))
        return active


class Packages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = build.release_files()

    def test_version_boundaries(self):
        cases = [(name, (fmt, 0), base) for name, fmt, base in build.LEGACY]
        for fmt, base in [
            (18, "1.20"), (41, "1.20"), (48, "1.21"), (57, "1.21"),
            (61, "1.21.4"), (81, "1.21.4"), (94, "1.21.4"), (101, "1.21.4"),
            (107, "26.2"), (121, "26.3"),
        ]:
            cases.append((build.STABLE, (fmt, 1 if fmt in (94, 101, 107) else 0), base))
        for fmt, base in [
            ((122, 0), "26.3"), ((124, 0), "26.3"), ((125, 0), "26.4-snapshot-5"),
            ((125, 1), "26.4-snapshot-6"), ((126, 0), "26.4-snapshot-7"),
            ((128, 1), "26.4-snapshot-7"),
        ]:
            cases.append((build.PREVIEW, fmt, base))
        for name, fmt, base in cases:
            with self.subTest(pack=name, format=fmt):
                recipes = installed(self.files[f"Slabs2Blocks-{name}.zip"], fmt)
                expected = build.catalogs()[base]
                self.assertEqual(recipes.keys(), expected.keys())
                for slab, recipe in recipes.items():
                    self.assertEqual(recipe["type"], "minecraft:crafting_shaped")
                    self.assertEqual(recipe["pattern"], ["SS"])
                    item = "minecraft:" + slab
                    self.assertEqual(recipe["key"], {"S": item if fmt[0] >= 57 else {"item": item}})
                    field = "id" if fmt[0] >= 41 else "item"
                    self.assertEqual(recipe["result"], {field: "minecraft:" + expected[slab], "count": 1})

    def test_distinct_materials(self):
        slabs = build.catalogs()["26.4-snapshot-7"]
        self.assertEqual(len(slabs), 105)
        self.assertEqual(slabs["bamboo_mosaic_slab"], "bamboo_mosaic")
        self.assertEqual(slabs["waxed_weathered_cut_copper_slab"], "waxed_weathered_cut_copper")
        self.assertEqual(slabs["blue_wool_slab"], "blue_wool")
        self.assertEqual(slabs["blue_concrete_slab"], "blue_concrete")
        self.assertNotIn("petrified_oak_slab", slabs)

    def test_release_bundle(self):
        self.assertEqual(self.files, build.release_files())
        with zipfile.ZipFile(io.BytesIO(self.files[build.MASTER])) as bundle:
            self.assertIsNone(bundle.testzip())
            checks = bundle.read("SHA256SUMS.txt").decode().splitlines()
            self.assertEqual(len(checks), 13)
            self.assertEqual(set(bundle.namelist()), set(self.files) - {build.MASTER})
            for line in checks:
                checksum, name = line.split("  ")
                payload = bundle.read(name)
                self.assertEqual(checksum, hashlib.sha256(payload).hexdigest())
                self.assertEqual(payload, self.files[name])
                with zipfile.ZipFile(io.BytesIO(payload)) as pack:
                    self.assertIsNone(pack.testzip())
                    self.assertIn("pack.mcmeta", pack.namelist())
                    self.assertTrue(pack.read("pack.png").startswith(b"\x89PNG"))
