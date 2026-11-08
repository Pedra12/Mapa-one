#!/usr/bin/env python3
"""Select mobile-sized original assets and the converted Springfield GLB for Godot."""
from pathlib import Path
import json, shutil

root = Path("asset-audit")
game = Path("game")
assets = game / "assets"
if assets.exists():
    shutil.rmtree(assets)
assets.mkdir(parents=True)

def copy_tree(src: Path, dst: Path):
    if src.exists():
        shutil.copytree(src, dst, dirs_exist_ok=True)

# KayKit medium rig: mannequin and matching animation clips.
kay = root / "extracted/KayKit_Character_Animations_1.1/KayKit_Character_Animations_1.1"
copy_tree(kay / "Mannequin Character/characters", assets / "characters")
copy_tree(kay / "Mannequin Character/Textures", assets / "characters/Textures")
copy_tree(kay / "Animations/gltf/Rig_Medium", assets / "animations/KayKit_Rig_Medium")

# Curated nature models. Keep the source atlas files beside the glTF files because
# the original glTF image URIs are relative to this directory.
nature = root / "extracted/Stylized.Nature.MegaKit.Standard"
nature_src = nature / "glTF"
nature_dst = assets / "nature/glTF"
nature_dst.mkdir(parents=True, exist_ok=True)
nature_models = [
    "Bush_Common", "Bush_Common_Flowers",
    "CommonTree_1", "CommonTree_2", "CommonTree_3", "CommonTree_4", "CommonTree_5",
    "Pine_1", "Pine_2", "Pine_3", "Pine_4", "Pine_5",
    "TwistedTree_1", "TwistedTree_2",
    "Rock_Medium_1", "Rock_Medium_2", "Rock_Medium_3",
    "Grass_Common_Short", "Grass_Common_Tall", "Grass_Wispy_Short", "Grass_Wispy_Tall",
    "Fern_1", "Mushroom_Common", "Mushroom_Laetiporus",
    "Flower_3_Group", "Flower_4_Group", "Plant_1", "Plant_7"
]
for model_name in nature_models:
    for suffix in (".gltf", ".bin"):
        src = nature_src / (model_name + suffix)
        if src.is_file():
            shutil.copy2(src, nature_dst / src.name)
copy_tree(nature / "Textures", nature_dst)

# Curated ruins props and architectural pieces.
ruins_src = root / "extracted/RuinsGLB/RuinsGLB"
ruins_selection = {
    "Accessories": ["Altar", "AncientCoinAmethyst", "AncientCoinEmerald", "AncientCoinRuby", "ChestBaseGold", "ChestCover", "WallLight"],
    "Blocks": ["BlockMossMD", "BlockNormalMD", "BlockCrackMD"],
    "Moss": ["GroundMossMD"],
    "Pillars": ["PillarRound"],
    "Stairs": ["StairsMD"],
    "Walls": ["Gate", "WallBrokenMD", "WallNormalMD"],
    "Skely": ["Skely", "SkelyDraugr", "SkelyPoison"]
}
for folder, names in ruins_selection.items():
    for model_name in names:
        src = ruins_src / folder / (model_name + ".glb")
        if src.is_file():
            dest = assets / "ruins" / folder
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / src.name)

# Use the Blender-converted map. The original OBJ and all source files remain in
# the complete audit artifact; the GLB has its materials/textures embedded.
source_obj = root / "rar-extracted/mapa-springfield/source/mapa-final-simpson/source/FINAL OBJ/FINAL OBJ/Mapa Simpson.obj"
converted_map = root / "converted/MapaSpringfield.glb"
if not source_obj.is_file():
    raise SystemExit(f"Original Springfield OBJ not found: {source_obj}")
if not converted_map.is_file():
    raise SystemExit("Converted Springfield GLB missing. Blender conversion must run before staging.")
map_dst = assets / "springfield/geometry/MapaSpringfield.glb"
map_dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(converted_map, map_dst)

# Read original geometry statistics and compute a spawn point from its real bounds.
raw_obj = source_obj.read_bytes()
try:
    obj_text = raw_obj.decode("utf-8")
except UnicodeDecodeError:
    obj_text = raw_obj.decode("cp1252")
obj_lines = obj_text.splitlines()
vertex_rows = []
for line in obj_lines:
    if line.startswith("v "):
        parts = line.split()
        if len(parts) >= 4:
            try:
                vertex_rows.append((float(parts[1]), float(parts[2]), float(parts[3])))
            except ValueError:
                pass
map_stats = {
    "vertices": len(vertex_rows),
    "faces": sum(1 for line in obj_lines if line.startswith("f ")),
    "objects": sum(1 for line in obj_lines if line.startswith("o ") or line.startswith("g ")),
    "material_libraries": [line[7:].strip() for line in obj_lines if line.startswith("mtllib ")],
    "textures_missing": [],
    "bounds": {},
    "spawn_position": [0.0, 2.0, 0.0]
}
if vertex_rows:
    mins = [min(v[i] for v in vertex_rows) for i in range(3)]
    maxs = [max(v[i] for v in vertex_rows) for i in range(3)]
    map_stats["bounds"] = {"min": mins, "max": maxs}
    map_stats["spawn_position"] = [(mins[0] + maxs[0]) * 0.5, mins[1] + 2.0, (mins[2] + maxs[2]) * 0.5]

map_scene = "res://assets/springfield/geometry/MapaSpringfield.glb"
manifest = {
    "map_scene": map_scene,
    "map_mesh": "",
    "map_model_count": 1,
    "map_models": [map_scene],
    "character_model": "res://assets/characters/Mannequin_Medium.glb",
    "animation_files": sorted("res://" + p.relative_to(game).as_posix() for p in (assets / "animations").rglob("*.glb")),
    "ruin_models": sum(1 for p in (assets / "ruins").rglob("*.glb")),
    "nature_models": sum(1 for p in (assets / "nature").rglob("*.gltf")),
    "nature_model_names": nature_models,
    "ruin_model_names": [f"{folder}/{name}.glb" for folder, names in ruins_selection.items() for name in names],
    "springfield_geometry_files": 1,
    "springfield_map_stats": map_stats
}
(assets / "asset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
if not (assets / "characters/Mannequin_Medium.glb").is_file():
    raise SystemExit("KayKit medium character model missing.")
if map_stats["vertices"] == 0 or map_stats["faces"] == 0:
    raise SystemExit("Springfield source geometry is empty.")
