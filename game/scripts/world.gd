extends Node3D

const DEFAULT_MAP_PATH := "res://assets/springfield/geometry/MapaSpringfield.glb"
var player_spawn := Vector3(0.0, 3.0, 0.0)
var map_loaded := false

func _ready() -> void:
    _setup_environment()
    await _load_springfield_map()
    _create_player()
    _create_touch_hud()

func _setup_environment() -> void:
    var world_env := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_SKY
    var sky := Sky.new()
    var sky_mat := ProceduralSkyMaterial.new()
    sky_mat.sky_top_color = Color(0.12, 0.28, 0.43)
    sky_mat.sky_horizon_color = Color(0.67, 0.76, 0.78)
    sky_mat.ground_bottom_color = Color(0.13, 0.17, 0.14)
    sky_mat.ground_horizon_color = Color(0.49, 0.53, 0.42)
    sky.sky_material = sky_mat
    env.sky = sky
    env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
    env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
    env.tonemap_exposure = 1.0
    world_env.environment = env
    add_child(world_env)

    var sun := DirectionalLight3D.new()
    sun.rotation_degrees = Vector3(-48, -32, 0)
    sun.light_energy = 1.25
    sun.shadow_enabled = true
    add_child(sun)

func _load_springfield_map() -> void:
    var manifest_path := "res://assets/asset_manifest.json"
    var scene_path := DEFAULT_MAP_PATH
    var manifest: Dictionary = {}

    if FileAccess.file_exists(manifest_path):
        var parsed = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
        if parsed is Dictionary:
            manifest = parsed
            var configured_path := str(manifest.get("map_scene", ""))
            if not configured_path.is_empty():
                scene_path = configured_path
            var stats = manifest.get("springfield_map_stats", {})
            if stats is Dictionary:
                var spawn_data = stats.get("spawn_position", [])
                if spawn_data is Array and spawn_data.size() == 3:
                    player_spawn = Vector3(float(spawn_data[0]), float(spawn_data[1]), float(spawn_data[2]))

    if not ResourceLoader.exists(scene_path):
        push_error("MAPA AUSENTE: arquivo não encontrado em " + scene_path)
        _create_stylized_test_ground()
        return

    var map_resource = load(scene_path)
    if not (map_resource is PackedScene):
        push_error("MAPA INVÁLIDO: não foi possível importar " + scene_path)
        _create_stylized_test_ground()
        return

    var map_node := (map_resource as PackedScene).instantiate()
    map_node.name = "SpringfieldMap"
    add_child(map_node)
    _add_map_collisions(map_node)
    await get_tree().physics_frame

    var stats = manifest.get("springfield_map_stats", {})
    if stats is Dictionary:
        player_spawn = _find_walkable_spawn(stats)
    map_loaded = true
    print("SPRINGFIELD MAP LOADED: ", scene_path, " | spawn=", player_spawn)

func _find_walkable_spawn(stats: Dictionary) -> Vector3:
    var bounds = stats.get("bounds", {})
    if not (bounds is Dictionary):
        return player_spawn
    var mins = bounds.get("min", [])
    var maxs = bounds.get("max", [])
    if not (mins is Array and maxs is Array and mins.size() >= 3 and maxs.size() >= 3):
        return player_spawn

    var min_x := float(mins[0])
    var min_y := float(mins[1])
    var min_z := float(mins[2])
    var max_x := float(maxs[0])
    var max_y := float(maxs[1])
    var max_z := float(maxs[2])
    var state := get_world_3d().direct_space_state

    for row in range(5):
        for col in range(5):
            var tx := 0.2 + float(col) * 0.15
            var tz := 0.2 + float(row) * 0.15
            var x := lerp(min_x, max_x, tx)
            var z := lerp(min_z, max_z, tz)
            var origin := Vector3(x, max_y + 100.0, z)
            var finish := Vector3(x, min_y - 100.0, z)
            var query := PhysicsRayQueryParameters3D.create(origin, finish)
            var hit := state.intersect_ray(query)
            if not hit.is_empty():
                var normal: Vector3 = hit.get("normal", Vector3.UP)
                if normal.y > 0.45:
                    return hit.position + Vector3.UP * 1.15

    return Vector3((min_x + max_x) * 0.5, min_y + 8.0, (min_z + max_z) * 0.5)

func _add_map_collisions(map_root: Node) -> void:
    var meshes := map_root.find_children("*", "MeshInstance3D", true, false)
    if map_root is MeshInstance3D:
        meshes.push_front(map_root)
    for mesh_node in meshes:
        if mesh_node is MeshInstance3D and mesh_node.mesh:
            mesh_node.create_trimesh_collision()

func _create_stylized_test_ground() -> void:
    var ground := MeshInstance3D.new()
    var plane := PlaneMesh.new()
    plane.size = Vector2(180, 180)
    ground.mesh = plane
    var material := StandardMaterial3D.new()
    material.albedo_color = Color(0.19, 0.28, 0.17)
    material.roughness = 1.0
    ground.material_override = material
    ground.position.y = -0.08
    add_child(ground)
    var body := StaticBody3D.new()
    var collision := CollisionShape3D.new()
    var shape := BoxShape3D.new()
    shape.size = Vector3(180, 0.2, 180)
    collision.shape = shape
    collision.position.y = -0.1
    body.add_child(collision)
    add_child(body)

func _create_player() -> void:
    var player := CharacterBody3D.new()
    player.set_script(load("res://scripts/player.gd"))
    player.name = "Player"
    player.position = player_spawn
    add_child(player)

func _create_touch_hud() -> void:
    var layer := CanvasLayer.new()
    layer.name = "TouchLayer"
    add_child(layer)
    var hud := Control.new()
    hud.name = "TouchHUD"
    hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
    hud.set_script(load("res://scripts/touch_hud.gd"))
    layer.add_child(hud)
