"""Controlli senza dipendenze esterne per il modello e il visualizzatore."""

import json
from pathlib import Path
import re
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
GLB = ROOT / "assets" / "rufy.glb"


class ModelAssetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with GLB.open("rb") as model:
            magic, version, total_length = struct.unpack("<4sII", model.read(12))
            assert magic == b"glTF" and version == 2
            assert total_length == GLB.stat().st_size
            json_length, json_type = struct.unpack("<I4s", model.read(8))
            assert json_type == b"JSON"
            cls.gltf = json.loads(model.read(json_length))
            cls.binary_length, binary_type = struct.unpack("<I4s", model.read(8))
            assert binary_type == b"BIN\x00"
            cls.binary_offset = model.tell()
            assert cls.binary_offset + cls.binary_length == total_length

    def image_size(self, texture_index):
        texture = self.gltf["textures"][texture_index]
        image = self.gltf["images"][texture["source"]]
        self.assertNotIn("uri", image, "Le texture devono essere incorporate nel GLB")
        view = self.gltf["bufferViews"][image["bufferView"]]
        offset = view.get("byteOffset", 0)
        self.assertLessEqual(offset + view["byteLength"], self.binary_length)
        with GLB.open("rb") as model:
            model.seek(self.binary_offset + offset)
            data = model.read(view["byteLength"])
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            self.assertEqual(data[12:16], b"IHDR")
            return struct.unpack(">II", data[16:24])
        self.assertTrue(data.startswith(b"\xff\xd8"), "Formato immagine inatteso")
        position = 2
        # JPEG dimensions are in a Start of Frame segment, not a fixed offset.
        while position + 4 < len(data):
            self.assertEqual(data[position], 0xFF)
            while position < len(data) and data[position] == 0xFF:
                position += 1
            marker = data[position]
            position += 1
            if marker in (0x01, 0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                continue
            segment_length = struct.unpack_from(">H", data, position)[0]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                height, width = struct.unpack_from(">HH", data, position + 3)
                return width, height
            position += segment_length
        self.fail("Dimensioni JPEG non trovate")

    def node_and_primitive(self, name):
        nodes = self.gltf["nodes"]
        matches = [(index, node) for index, node in enumerate(nodes) if node.get("name") == name]
        self.assertEqual(len(matches), 1, f"Oggetto mancante o duplicato: {name}")
        index, node = matches[0]
        self.assertIn("mesh", node)
        primitive = self.gltf["meshes"][node["mesh"]]["primitives"][0]
        return index, node, primitive

    def test_mesh_and_embedded_textures(self):
        _, _, primitive = self.node_and_primitive("Rufy · Mesh texturizzata")
        for attribute in ("POSITION", "NORMAL", "TANGENT", "TEXCOORD_0"):
            self.assertIn(attribute, primitive["attributes"])
        self.assertGreater(self.gltf["accessors"][primitive["indices"]]["count"], 0)

        material = self.gltf["materials"][primitive["material"]]
        pbr = material["pbrMetallicRoughness"]
        self.assertEqual(self.image_size(pbr["baseColorTexture"]["index"]), (4096, 4096))
        self.assertEqual(self.image_size(material["normalTexture"]["index"]), (2048, 2048))
        self.assertEqual(self.image_size(pbr["metallicRoughnessTexture"]["index"]), (2048, 2048))
        self.assertLess(material["normalTexture"].get("scale", 1), 1)

    def test_sculpted_face_and_fringe_are_exported(self):
        _, model, _ = self.node_and_primitive("Rufy · Mesh texturizzata")
        face_index, _, face = self.node_and_primitive("Rufy · Volto scolpito")
        hair_index, _, hair = self.node_and_primitive("Rufy · Ciocche sulla fronte")
        self.assertIn(face_index, model.get("children", []))
        self.assertIn(hair_index, model.get("children", []))

        for attribute in ("POSITION", "NORMAL", "TANGENT", "TEXCOORD_0"):
            self.assertIn(attribute, face["attributes"])
        positions = self.gltf["accessors"][face["attributes"]["POSITION"]]
        self.assertGreater(positions["count"], 10_000)
        # The new surface has real depth, rather than a flat image facing the camera.
        self.assertGreater(positions["max"][0] - positions["min"][0], 0.02)
        self.assertGreater(self.gltf["accessors"][face["indices"]]["count"], 0)
        self.assertIn("NORMAL", hair["attributes"])
        self.assertGreater(self.gltf["accessors"][hair["indices"]]["count"], 0)

        material = self.gltf["materials"][face["material"]]
        pbr = material["pbrMetallicRoughness"]
        self.assertGreaterEqual(pbr.get("roughnessFactor", 1), 0.65)
        self.assertEqual(material.get("alphaMode", "OPAQUE"), "OPAQUE")
        self.assertFalse(material.get("doubleSided", False))
        self.assertEqual(self.image_size(pbr["baseColorTexture"]["index"]), (1600, 1018))

    def test_viewer_imports_are_local(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        match = re.search(r'<script type="importmap">\s*(.*?)\s*</script>', html, re.S)
        self.assertIsNotNone(match)
        imports = json.loads(match.group(1))["imports"]
        self.assertTrue(imports["three"].startswith("./"))
        self.assertTrue((ROOT / imports["three"]).is_file())
        self.assertTrue(imports["three/addons/"].startswith("./"))
        addons = ROOT / imports["three/addons/"]
        for module in ("controls/OrbitControls.js", "loaders/GLTFLoader.js", "utils/BufferGeometryUtils.js"):
            self.assertTrue((addons / module).is_file(), module)
        self.assertTrue((ROOT / "vendor/three/LICENSE").is_file())


if __name__ == "__main__":
    unittest.main()
