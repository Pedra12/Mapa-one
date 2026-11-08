extends CharacterBody3D
class_name AdventurePlayer

@export var walk_speed := 4.8
@export var sprint_speed := 7.2
@export var jump_velocity := 5.2
@export var turn_speed := 11.0
@export var look_sensitivity := 0.0035

var move_input := Vector2.ZERO
var look_delta := Vector2.ZERO
var wants_sprint := false
var wants_jump := false
var wants_fire := false
var camera_yaw := 0.0
var camera_pitch := -0.18
var gravity := 9.8
var visual_root: Node3D
var spring_arm: SpringArm3D
var camera: Camera3D

func _ready() -> void:
    gravity = float(ProjectSettings.get_setting("physics/3d/default_gravity", 9.8))
    var capsule := CapsuleShape3D.new()
    capsule.radius = 0.34
    capsule.height = 1.75
    var collider := CollisionShape3D.new()
    collider.shape = capsule
    collider.position.y = 0.88
    add_child(collider)

    visual_root = Node3D.new()
    visual_root.name = "CharacterVisual"
    add_child(visual_root)
    var model_path := "res://assets/characters/Mannequin_Medium.glb"
    if ResourceLoader.exists(model_path):
        var model_scene := load(model_path) as PackedScene
        if model_scene:
            var model := model_scene.instantiate()
            visual_root.add_child(model)
            model.position.y = -0.88
            model.scale = Vector3.ONE * 1.0
    else:
        _create_fallback_visual()

    var pivot := Node3D.new()
    pivot.name = "CameraPivot"
    pivot.position.y = 1.48
    add_child(pivot)
    spring_arm = SpringArm3D.new()
    spring_arm.spring_length = 4.2
    spring_arm.margin = 0.18
    pivot.add_child(spring_arm)
    camera = Camera3D.new()
    camera.current = true
    camera.fov = 70.0
    spring_arm.add_child(camera)
    _apply_camera_rotation()

func _create_fallback_visual() -> void:
    var mesh := CapsuleMesh.new()
    mesh.radius = 0.32
    mesh.height = 1.65
    var body := MeshInstance3D.new()
    body.mesh = mesh
    body.position.y = 0.82
    var mat := StandardMaterial3D.new()
    mat.albedo_color = Color(0.18, 0.31, 0.42)
    body.material_override = mat
    visual_root.add_child(body)

func _physics_process(delta: float) -> void:
    camera_yaw -= look_delta.x * look_sensitivity
    camera_pitch = clamp(camera_pitch - look_delta.y * look_sensitivity, -0.78, 0.22)
    look_delta = Vector2.ZERO
    _apply_camera_rotation()

    var camera_basis := Basis(Vector3.UP, camera_yaw)
    var forward := -camera_basis.z
    var right := camera_basis.x
    var direction := (right * move_input.x + forward * -move_input.y)
    direction.y = 0.0
    if direction.length_squared() > 1.0:
        direction = direction.normalized()

    var speed := sprint_speed if wants_sprint else walk_speed
    velocity.x = direction.x * speed
    velocity.z = direction.z * speed

    if not is_on_floor():
        velocity.y -= gravity * delta
    elif wants_jump:
        velocity.y = jump_velocity
    wants_jump = false

    if direction.length_squared() > 0.01:
        var target_yaw := atan2(direction.x, direction.z)
        visual_root.rotation.y = lerp_angle(visual_root.rotation.y, target_yaw, turn_speed * delta)

    move_and_slide()

func _apply_camera_rotation() -> void:
    if is_instance_valid(spring_arm):
        spring_arm.rotation.y = camera_yaw
        spring_arm.rotation.x = camera_pitch

func set_move_input(value: Vector2) -> void:
    move_input = value.limit_length(1.0)

func add_look_delta(value: Vector2) -> void:
    look_delta += value

func request_jump() -> void:
    wants_jump = true

func set_sprint(value: bool) -> void:
    wants_sprint = value

func set_fire(value: bool) -> void:
    wants_fire = value
