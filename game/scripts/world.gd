extends Node3D

var player_spawn := Vector3(0, 1.0, 0)

func _ready() -> void:
    _setup_environment()
    _load_springfield_map()
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
    if FileAccess.file_exists(manifest_path):
        var parsed = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
        if parsed is Dictionary:
            var map_stats = parsed.get("springfield_map_stats", {})
            if map_stats is Dictionary:
                var spawn_data = map_stats.get("spawn_position", [0.0, 2.0, 0.0])
                if spawn_data is Array and spawn_data.size() == 3:
                    player_spawn = Vector3(float(spawn_data[0]), float(spawn_data[1]), float(spawn_data[2]))
            var scene_path := str(parsed.get("map_scene", ""))
            if scene_path != "" and ResourceLoader.exists(scene_path):
                var packed := load(scene_path) as PackedScene
                if packed:
                    var map_node := packed.instantiate()
                    map_node.name = "SpringfieldMap"
                    add_child(map_node)
                    return
            var mesh_path := str(parsed.get("map_mesh", ""))
            if mesh_path != "" and ResourceLoader.exists(mesh_path):
                var map_mesh = load(mesh_path)
                if map_mesh is Mesh:
                    var map_root := Node3D.new()
                    map_root.name = "SpringfieldMap"
                    var instance := MeshInstance3D.new()
                    instance.mesh = map_mesh
                    instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
                    map_root.add_child(instance)
                    add_child(map_root)
                    instance.create_trimesh_collision()
                    return
    push_warning("Springfield geometry not available. Using a temporary ground for input testing.")
    _create_stylized_test_ground()

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
    hud.set_script(load("res://scripts/touch_hud.gd"))
    layer.add_child(hud)
