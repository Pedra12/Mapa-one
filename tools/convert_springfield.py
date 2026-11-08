#!/usr/bin/env python3
"""Blender background script: normalize and merge the Springfield OBJ into one GLB."""
from pathlib import Path
import bpy, sys, re, difflib, unicodedata

args = sys.argv[sys.argv.index("--") + 1:]
if len(args) != 2:
    raise SystemExit("Usage: blender --background --python convert_springfield.py -- INPUT.obj OUTPUT.glb")
obj_path = Path(args[0]).resolve()
out_path = Path(args[1]).resolve()
mtl_path = obj_path.with_suffix(".mtl")
image_exts = {".png", ".jpg", ".jpeg", ".tga", ".bmp", ".webp"}
images = [p for p in obj_path.parent.rglob("*") if p.is_file() and p.suffix.lower() in image_exts]

def normalize(value):
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()

if not obj_path.is_file() or not mtl_path.is_file():
    raise SystemExit(f"Springfield OBJ/MTL missing: {obj_path}")

# The original MTL is Windows-1252 and contains a bump-map option after a filename.
# Normalize it to UTF-8 and point every map to the exact extracted image filename.
raw_mtl = mtl_path.read_bytes()
try:
    mtl_text = raw_mtl.decode("utf-8")
except UnicodeDecodeError:
    mtl_text = raw_mtl.decode("cp1252")
rewritten = []
missing = []
for line in mtl_text.splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        rewritten.append(line)
        continue
    match = re.match(r"^(map_Kd|map_Ka|map_Ks|map_d|map_Bump|bump|norm)\s+(.*)$", stripped, re.IGNORECASE)
    if not match:
        rewritten.append(line)
        continue
    key, rest = match.group(1), match.group(2).strip()
    # Ignore trailing MTL options after a texture name (e.g. "-bm 1").
    rest_clean = re.sub(r"\s+-bm\s+[-+0-9.eE]+\s*$", "", rest, flags=re.IGNORECASE)
    exact = [p for p in images if p.name.lower() in rest_clean.lower()]
    if not exact:
        target = normalize(Path(rest_clean).name)
        ranked = sorted(images, key=lambda p: difflib.SequenceMatcher(None, target, normalize(p.name)).ratio(), reverse=True)
        if ranked and difflib.SequenceMatcher(None, target, normalize(ranked[0].name)).ratio() >= 0.72:
            exact = [ranked[0]]
    if not exact:
        missing.append(rest)
        rewritten.append(line)
    else:
        rewritten.append(f"{key} {exact[0].name}")
if missing:
    raise SystemExit("Unresolved Springfield textures: " + "; ".join(missing))
mtl_path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")

# OBJ text may also contain Windows-1252 object/material labels.
raw_obj = obj_path.read_bytes()
try:
    raw_obj.decode("utf-8")
except UnicodeDecodeError:
    obj_path.write_text(raw_obj.decode("cp1252"), encoding="utf-8")

# Reset Blender and import all source objects.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.wm.obj_import(filepath=str(obj_path), forward_axis="NEGATIVE_Z", up_axis="Y",
                      use_split_objects=True, use_split_groups=True, validate_meshes=True)
mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not mesh_objects:
    raise SystemExit("Blender imported no mesh objects from Springfield OBJ")

# Join all imported pieces. Blender keeps material slots, reducing thousands of
# OBJ groups to a single render mesh with one surface per material.
bpy.ops.object.select_all(action="DESELECT")
for obj in mesh_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = mesh_objects[0]
bpy.ops.object.join()
merged = bpy.context.view_layer.objects.active
merged.name = "Springfield_Map"
merged.data.name = "Springfield_Map_Mesh"
merged.data.validate(verbose=True)
merged.data.update()
material_count = len(merged.data.materials)
if material_count > 256:
    raise SystemExit(f"Springfield has {material_count} materials, exceeding Godot's 256 surface limit")
out_path.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(out_path), export_format="GLB",
                          export_materials="EXPORT", export_image_format="AUTO",
                          export_apply=True, export_yup=True, export_texcoords=True,
                          export_normals=True, export_cameras=False, export_lights=False)
if not out_path.is_file() or out_path.stat().st_size == 0:
    raise SystemExit("Blender did not produce the Springfield GLB")
print(f"SPRINGFIELD_GL B={out_path} bytes={out_path.stat().st_size} vertices={len(merged.data.vertices)} faces={len(merged.data.polygons)} materials={material_count}")
