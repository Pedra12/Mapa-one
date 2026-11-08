#!/usr/bin/env python3
"""Select verified assets from the extracted packs and stage them for Godot."""
from pathlib import Path
import json, shutil, difflib, unicodedata

root = Path("asset-audit")
game = Path("game")
assets = game / "assets"
if assets.exists():
    shutil.rmtree(assets)
assets.mkdir(parents=True)

def copy_tree(src: Path, dst: Path):
    if src.exists():
        shutil.copytree(src, dst, dirs_exist_ok=True)

# KayKit medium rig: mannequin and matching animation clips are kept together.
kay = root / "extracted/KayKit_Character_Animations_1.1/KayKit_Character_Animations_1.1"
copy_tree(kay / "Mannequin Character/characters", assets / "characters")
copy_tree(kay / "Mannequin Character/Textures", assets / "characters/Textures")
copy_tree(kay / "Animations/gltf/Rig_Medium", assets / "animations/KayKit_Rig_Medium")

# Stage a curated, mobile-sized subset. The full original libraries remain in
# the complete audit artifact, while the APK receives only assets used by the scene.
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
copy_tree(nature / "Textures", assets / "nature/Textures")

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

# The Springfield archive contains a RAR with the actual OBJ geometry.
map_nested = root / "nested/mapa-springfield/source/mapa-final-simpson"
map_rar = root / "rar-extracted/mapa-springfield/source/mapa-final-simpson/source/FINAL OBJ"
copy_tree(map_nested / "textures", assets / "springfield/textures")
copy_tree(map_rar, assets / "springfield/geometry")

models = []
for ext in (".glb", ".gltf", ".fbx", ".obj"):
    models.extend(p for p in (assets / "springfield/geometry").rglob("*") if p.is_file() and p.suffix.lower() == ext)
models.sort(key=lambda p: (p.suffix.lower() != ".obj", -p.stat().st_size, str(p)))
map_scene = ""
map_mesh = ""
if models:
    chosen = models[0]
    rel = chosen.relative_to(game)
    if chosen.suffix.lower() == ".obj":
        map_mesh = "res://" + rel.as_posix()
    else:
        map_scene = "res://" + rel.as_posix()

map_stats = {"vertices": 0, "faces": 0, "objects": 0, "material_libraries": [], "textures_missing": [], "bounds": {}, "spawn_position": [0.0, 2.0, 0.0]}
if map_mesh:
    obj_file = game / map_mesh.replace("res://", "")
    obj_lines = obj_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    vertex_rows = []
    for line in obj_lines:
        if line.startswith("v "):
            parts = line.split()
            if len(parts) >= 4:
                try:
                    vertex_rows.append((float(parts[1]), float(parts[2]), float(parts[3])))
                except ValueError:
                    pass
    map_stats["vertices"] = len(vertex_rows)
    map_stats["faces"] = sum(1 for line in obj_lines if line.startswith("f "))
    map_stats["objects"] = sum(1 for line in obj_lines if line.startswith("o ") or line.startswith("g "))
    if vertex_rows:
        mins = [min(v[i] for v in vertex_rows) for i in range(3)]
        maxs = [max(v[i] for v in vertex_rows) for i in range(3)]
        map_stats["bounds"] = {"min": mins, "max": maxs}
        map_stats["spawn_position"] = [(mins[0] + maxs[0]) * 0.5, mins[1] + 2.0, (mins[2] + maxs[2]) * 0.5]
    mtl_names = [line[7:].strip() for line in obj_lines if line.startswith("mtllib ")]
    map_stats["material_libraries"] = mtl_names
    texture_keys = ("map_Kd ", "map_Ka ", "map_Ks ", "map_d ", "map_Bump ", "bump ", "norm ")
    image_files = [p for p in (assets / "springfield").rglob("*") if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".tga", ".bmp", ".webp")]
    def normalize_name(value):
        return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    for mtl_name in mtl_names:
        mtl_path = obj_file.parent / mtl_name
        if not mtl_path.exists():
            map_stats["textures_missing"].append(mtl_name)
            continue
        for line in mtl_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith(texture_keys):
                rest = line.split(" ", 1)[1].strip()
                reference = rest
                for option in (" -bm ", " -s ", " -o ", " -clamp "):
                    if option in reference:
                        reference = reference.split(option, 1)[0].strip()
                reference = reference.strip('"')
                if any(p.name.lower() in line.lower() for p in image_files):
                    continue
                target_name = Path(reference).name
                normalized_target = normalize_name(target_name)
                ranked = sorted(image_files, key=lambda p: difflib.SequenceMatcher(None, normalized_target, normalize_name(p.name)).ratio(), reverse=True)
                if ranked and difflib.SequenceMatcher(None, normalized_target, normalize_name(ranked[0].name)).ratio() >= 0.72:
                    alias = mtl_path.parent / target_name
                    if not alias.exists():
                        shutil.copy2(ranked[0], alias)
                else:
                    map_stats["textures_missing"].append(reference)

manifest = {
    "map_scene": map_scene,
    "map_mesh": map_mesh,
    "map_model_count": len(models),
    "map_models": ["res://" + p.relative_to(game).as_posix() for p in models],
    "character_model": "res://assets/characters/Mannequin_Medium.glb",
    "animation_files": sorted("res://" + p.relative_to(game).as_posix() for p in (assets / "animations").rglob("*.glb")),
    "ruin_models": sum(1 for p in (assets / "ruins").rglob("*.glb")),
    "nature_models": sum(1 for p in (assets / "nature").rglob("*.gltf")),
    "nature_model_names": nature_models,
    "ruin_model_names": [f"{folder}/{name}.glb" for folder, names in ruins_selection.items() for name in names],
    "springfield_geometry_files": len(models),
    "springfield_map_stats": map_stats
}
(assets / "asset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
if not map_scene and not map_mesh:
    raise SystemExit("Springfield geometry was not found. Refusing to build a fake map.")
if map_mesh and map_stats["textures_missing"]:
    raise SystemExit("Springfield OBJ has unresolved material or texture references: " + ", ".join(map_stats["textures_missing"]))
if not (assets / "characters/Mannequin_Medium.glb").is_file():
    raise SystemExit("KayKit medium character model missing.")
