from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "Rufy · Mesh texturizzata"
FACE_NAME = "Rufy · Volto scolpito"
HAIR_NAME = "Rufy · Ciocche sulla fronte"
# Keep the color maps sharp in close-up; normal and material maps can remain
# smaller for the web.
MAX_COLOR_TEXTURE_SIZE = 4096
MAX_DATA_TEXTURE_SIZE = 2048

model = bpy.data.objects.get(MODEL_NAME)
if model is None or model.type != "MESH":
    raise RuntimeError(f"Expected a mesh object named {MODEL_NAME!r} in the Blender file.")

# The face and fringe are editable meshes parented to the original sculpture.
# Export every mesh descendant so they remain part of the downloadable GLB.
def descendants(parent):
    yield parent
    for child in parent.children:
        yield from descendants(child)


sculpture = [obj for obj in descendants(model) if obj.type == "MESH"]
names = {obj.name for obj in sculpture}
missing = {FACE_NAME, HAIR_NAME} - names
if missing:
    raise RuntimeError(f"Missing sculpture parts in the Blender file: {sorted(missing)!r}")

for image in bpy.data.images:
    if image.source != "FILE":
        continue

    width, height = image.size
    if not width or not height:
        raise RuntimeError(f"Image {image.name!r} has no pixels.")

    max_size = (
        MAX_COLOR_TEXTURE_SIZE
        if image.colorspace_settings.name == "sRGB"
        else MAX_DATA_TEXTURE_SIZE
    )
    scale = min(max_size / width, max_size / height, 1)
    if scale < 1:
        image.scale(round(width * scale), round(height * scale))

decimate = model.modifiers.new(name="Web detail", type="DECIMATE")
decimate.ratio = 0.5

bpy.ops.object.select_all(action="DESELECT")
for part in sculpture:
    part.select_set(True)
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
    # Explicit tangents keep normal-map shading consistent across glTF viewers.
    export_tangents=True,
    export_image_format="AUTO",
    export_image_quality=98,
)

if "FINISHED" not in result:
    raise RuntimeError(f"Blender could not export the web model: {result!r}")

print(f"Exported {destination} ({destination.stat().st_size / 1024 / 1024:.1f} MB)")
