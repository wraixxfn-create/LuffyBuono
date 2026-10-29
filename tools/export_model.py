from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "Rufy · Mesh texturizzata"
MAX_TEXTURE_SIZE = 2048

model = bpy.data.objects.get(MODEL_NAME)
if model is None or model.type != "MESH":
    raise RuntimeError(f"Expected a mesh object named {MODEL_NAME!r} in the Blender file.")

for image in bpy.data.images:
    if image.source != "FILE":
        continue

    width, height = image.size
    scale = min(MAX_TEXTURE_SIZE / width, MAX_TEXTURE_SIZE / height, 1)
    if scale < 1:
        image.scale(round(width * scale), round(height * scale))

decimate = model.modifiers.new(name="Web detail", type="DECIMATE")
decimate.ratio = 0.5

bpy.ops.object.select_all(action="DESELECT")
model.select_set(True)
bpy.context.view_layer.objects.active = model

destination = ROOT / "assets" / "rufy.glb"
destination.parent.mkdir(parents=True, exist_ok=True)

result = bpy.ops.export_scene.gltf(
    filepath=str(destination),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_cameras=False,
    export_lights=False,
    export_animations=False,
    export_skins=False,
    export_image_format="AUTO",
    export_image_quality=90,
)

if "FINISHED" not in result:
    raise RuntimeError(f"Blender could not export the web model: {result!r}")

print(f"Exported {destination} ({destination.stat().st_size / 1024 / 1024:.1f} MB)")
