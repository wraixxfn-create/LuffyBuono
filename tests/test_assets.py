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

    def test_mesh_and_embedded_textures(self):
        primitive = self.gltf["meshes"][0]["primitives"][0]
        self.assertIn("POSITION", primitive["attributes"])
        self.assertIn("NORMAL", primitive["attributes"])
        self.assertIn("TANGENT", primitive["attributes"])
        self.assertIn("TEXCOORD_0", primitive["attributes"])
        self.assertGreater(self.gltf["accessors"][primitive["indices"]]["count"], 0)

        material = self.gltf["materials"][primitive["material"]]
        pbr = material["pbrMetallicRoughness"]
        self.assertEqual(self.image_size(pbr["baseColorTexture"]["index"]), (4096, 4096))
        self.assertEqual(self.image_size(material["normalTexture"]["index"]), (2048, 2048))
        self.assertEqual(self.image_size(pbr["metallicRoughnessTexture"]["index"]), (2048, 2048))

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
