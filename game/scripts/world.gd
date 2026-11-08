extends Node3D

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
            var map_path := str(parsed.get("map_scene", ""))
            if map_path != "" and ResourceLoader.exists(map_path):
                var packed := load(map_path) as PackedScene
                if packed:
                    var map_node := packed.instantiate()
                    map_node.name = "SpringfieldMap"
                    add_child(map_node)
                    return
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
    var player_script = load("res://scripts/player.gd")
    var player := CharacterBody3D.new()
    player.set_script(player_script)
    player.name = "Player"
    player.position = Vector3(0, 1.0, 0)
    add_child(player)

func _create_touch_hud() -> void:
    var hud := CanvasLayer.new()
    hud.name = "TouchHUD"
    hud.set_script(load("res://scripts/touch_hud.gd"))
    add_child(hud)
