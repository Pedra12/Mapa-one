extends Control
class_name TouchHUD

var player: AdventurePlayer
var screen_size := Vector2.ZERO
var joystick_center := Vector2.ZERO
var joystick_vector := Vector2.ZERO
var active_move_touch := -1
var active_look_touch := -1
var last_look_position := Vector2.ZERO
var jump_pressed := false
var fire_pressed := false
var sprint_pressed := false

func _ready() -> void:
    player = get_parent().get_parent().get_node("Player") as AdventurePlayer
    screen_size = get_viewport_rect().size
    set_process_input(true)
    queue_redraw()

func _process(_delta: float) -> void:
    screen_size = get_viewport().get_visible_rect().size
    queue_redraw()

func _input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        var p: Vector2 = event.position
        if event.pressed:
            if _inside_jump(p):
                player.request_jump()
            elif _inside_fire(p):
                fire_pressed = true
                player.set_fire(true)
            elif _inside_sprint(p):
                sprint_pressed = true
                player.set_sprint(true)
            elif p.x < screen_size.x * 0.43 and p.y > screen_size.y * 0.48:
                active_move_touch = event.index
                joystick_center = Vector2(screen_size.x * 0.17, screen_size.y * 0.79)
                _update_joystick(p)
            elif p.x > screen_size.x * 0.43:
                active_look_touch = event.index
                last_look_position = p
        else:
            if event.index == active_move_touch:
                active_move_touch = -1
                joystick_vector = Vector2.ZERO
                player.set_move_input(Vector2.ZERO)
            if event.index == active_look_touch:
                active_look_touch = -1
            if _inside_fire(p):
                fire_pressed = false
                player.set_fire(false)
            if _inside_sprint(p):
                sprint_pressed = false
                player.set_sprint(false)
        queue_redraw()
    elif event is InputEventScreenDrag:
        if event.index == active_move_touch:
            _update_joystick(event.position)
        elif event.index == active_look_touch:
            player.add_look_delta(event.relative)
    elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
        if event.pressed and event.position.x > screen_size.x * 0.43:
            active_look_touch = 999
            last_look_position = event.position
        elif not event.pressed:
            active_look_touch = -1
    elif event is InputEventMouseMotion and active_look_touch == 999:
        player.add_look_delta(event.relative)

func _update_joystick(p: Vector2) -> void:
    var delta := (p - joystick_center) / 76.0
    joystick_vector = delta.limit_length(1.0)
    player.set_move_input(joystick_vector)

func _inside_jump(p: Vector2) -> bool:
    return p.distance_to(Vector2(screen_size.x * 0.89, screen_size.y * 0.78)) < 54.0

func _inside_fire(p: Vector2) -> bool:
    return p.distance_to(Vector2(screen_size.x * 0.89, screen_size.y * 0.57)) < 54.0

func _inside_sprint(p: Vector2) -> bool:
    return p.distance_to(Vector2(screen_size.x * 0.72, screen_size.y * 0.86)) < 48.0

func _draw() -> void:
    var s := get_viewport().get_visible_rect().size
    if active_move_touch != -1:
        draw_circle(joystick_center, 78.0, Color(0.05, 0.08, 0.1, 0.34))
        draw_arc(joystick_center, 78.0, 0, TAU, 48, Color(0.8, 0.9, 1, 0.55), 2.0)
        draw_circle(joystick_center + joystick_vector * 48.0, 31.0, Color(0.82, 0.9, 1, 0.65))
    else:
        var c := Vector2(s.x * 0.17, s.y * 0.79)
        draw_circle(c, 70.0, Color(0.05, 0.08, 0.1, 0.23))
        draw_arc(c, 70.0, 0, TAU, 48, Color(0.8, 0.9, 1, 0.35), 2.0)
        draw_circle(c, 27.0, Color(0.82, 0.9, 1, 0.35))
    _draw_button(Vector2(s.x * 0.89, s.y * 0.78), "PULAR", Color(0.2, 0.65, 0.95, 0.72))
    _draw_button(Vector2(s.x * 0.89, s.y * 0.57), "ATIRAR", Color(0.85, 0.22, 0.16, 0.76))
    _draw_button(Vector2(s.x * 0.72, s.y * 0.86), "CORRER", Color(0.15, 0.55, 0.32, 0.7))
    draw_string(ThemeDB.fallback_font, Vector2(24, 38), "MUNDO PERDIDO  •  EXPLORAÇÃO", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(1, 1, 1, 0.9))
    draw_string(ThemeDB.fallback_font, Vector2(24, 62), "Arraste à direita para girar a câmera", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(1, 1, 1, 0.72))

func _draw_button(c: Vector2, label: String, color: Color) -> void:
    draw_circle(c, 48.0, Color(0.02, 0.04, 0.06, 0.35))
    draw_circle(c, 42.0, color)
    draw_arc(c, 42.0, 0, TAU, 48, Color(1, 1, 1, 0.72), 2.0)
    draw_string(ThemeDB.fallback_font, c + Vector2(-33, 5), label, HORIZONTAL_ALIGNMENT_CENTER, 66, 11, Color.WHITE)
