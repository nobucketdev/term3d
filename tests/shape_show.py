import sys
from term3d.core import term3d, Vec3, SceneNode
from term3d.shpbuild import(
    build_cube, build_uv_sphere, build_torus, build_plane,
    build_cylinder, build_cone, build_pyramid, build_icosphere,
    build_mobius_strip, build_klein_bottle, build_heart,
    build_dinis_surface, build_conical_helix, build_catenoid,
    build_capsule
)
from term3d.utils import set_mat

print("Welcome to the shape_show.py test of term3d engine\nPlease maximize terminal size and enter 0 - 7 quality setting\n0-1: Very Low, 2: Low, 3: Normal, 4-5: High, 6: Very High, 7: Extreme")
valid_qualities = {0, 1, 2, 3, 4, 5, 6, 7}
while True:
    try:
        q = int(input("Quality: "))
        if q in valid_qualities:
            break
        print("Please type a number from 0-7.")
    except ValueError:
        print("Please type a number from 0-7.")

print("\nChoose a color scheme for the shapes:")
print("1: Rainbow (default colors)")
print("2: Custom RGB color")
color_choice = input("Enter your choice (1 or 2): ")

selected_color = None
if color_choice == '2':
    try:
        r = int(input("Enter R value (0-255): "))
        g = int(input("Enter G value (0-255): "))
        b = int(input("Enter B value (0-255): "))
        selected_color = (r, g, b)
    except ValueError:
        print("Invalid color input, using default Rainbow colors.")
        selected_color = None
else:
    print("Using default Rainbow colors.")

material = "phong"
print("Select a material (0: flat, 1: phong, 2: wireframe)")
valid_mat = {0, 1, 2}
while True:
    try:
        m = int(input("Quality: "))
        if m in valid_mat:
            break
        print("Please type a number from 0-2")
    except ValueError:
        print("Please type a number from 0-2")

if m == 0:
    material = "flat"
elif m == 1:
    material = "phong"
elif m == 2:
    material = "wireframe"

def main():
    width, height = 80, 40
    engine = term3d(width, height)

    # List of tuples: (shape name, shape mesh)
    shape_meshes = [
        ("Cube", build_cube(color=selected_color)),
        ("Sphere", build_uv_sphere(color=selected_color)),
        ("Icosphere", build_icosphere(color=selected_color)),
        ("Torus", build_torus(color=selected_color)),
        ("Plane", build_plane(color=selected_color)),
        ("Cylinder", build_cylinder(color=selected_color)),
        ("Cone", build_cone(color=selected_color)),
        ("Pyramid", build_pyramid(color=selected_color)),
        ("Möbius Strip", build_mobius_strip(color=selected_color)),
        ("Klein Bottle", build_klein_bottle(color=selected_color)),
        ("Heart", build_heart(color=selected_color)),
        ("Dini's Surface", build_dinis_surface(color=selected_color)),
        ("Conical Helix", build_conical_helix(color=selected_color)),
        ("Catenoid", build_catenoid(color=selected_color)),
        ("Capsule", build_capsule(color=selected_color)),
    ]

    # Create a list of SceneNodes, each with a mesh
    shapes_nodes = [engine.add_mesh_node(mesh, name) for name, mesh in shape_meshes]

    index = 0
    current_node = shapes_nodes[index]
    engine.register_for_rotation(current_node.mesh)
    set_mat(current_node.mesh, material)

    rotation_step = 0.1
    zoom = -5
    min_zoom = -10
    max_zoom = -2
    auto_rotate = True

    def rotate_x_pos():
        nonlocal auto_rotate
        auto_rotate = False
        current_node.set_rot(current_node.transform.rot.x + rotation_step, current_node.transform.rot.y, current_node.transform.rot.z)

    def rotate_x_neg():
        nonlocal auto_rotate
        auto_rotate = False
        current_node.set_rot(current_node.transform.rot.x - rotation_step, current_node.transform.rot.y, current_node.transform.rot.z)

    def rotate_y_pos():
        nonlocal auto_rotate
        auto_rotate = False
        current_node.set_rot(current_node.transform.rot.x, current_node.transform.rot.y + rotation_step, current_node.transform.rot.z)

    def rotate_y_neg():
        nonlocal auto_rotate
        auto_rotate = False
        current_node.set_rot(current_node.transform.rot.x, current_node.transform.rot.y - rotation_step, current_node.transform.rot.z)

    def rotate_z_pos():
        nonlocal auto_rotate
        auto_rotate = False
        current_node.set_rot(current_node.transform.rot.x, current_node.transform.rot.y, current_node.transform.rot.z + rotation_step)

    def rotate_z_neg():
        nonlocal auto_rotate
        auto_rotate = False
        current_node.set_rot(current_node.transform.rot.x, current_node.transform.rot.y, current_node.transform.rot.z - rotation_step)

    def next_shape():
        nonlocal index, current_node, auto_rotate
        auto_rotate = False
        engine.rotating_meshes.clear()
        engine.root.remove(current_node)
        index = (index + 1) % len(shapes_nodes)
        current_node = shapes_nodes[index]
        engine.root.add(current_node)
        engine.register_for_rotation(current_node.mesh)
        set_mat(current_node.mesh, material)

    def prev_shape():
        nonlocal index, current_node, auto_rotate
        auto_rotate = False
        engine.rotating_meshes.clear()
        engine.root.remove(current_node)
        index = (index - 1) % len(shapes_nodes)
        current_node = shapes_nodes[index]
        engine.root.add(current_node)
        engine.register_for_rotation(current_node.mesh)
        set_mat(current_node.mesh, material)

    def zoom_in():
        nonlocal zoom, auto_rotate
        auto_rotate = False
        zoom = max(min_zoom, zoom + 0.5)
        engine.set_camera_zoom(zoom)

    def zoom_out():
        nonlocal zoom, auto_rotate
        auto_rotate = False
        zoom = min(max_zoom, zoom - 0.5)
        engine.set_camera_zoom(zoom)

    def quit_app():
        engine.running = False

    def toggle_auto_rotate():
        nonlocal auto_rotate
        auto_rotate = not auto_rotate

    # Bind keys
    engine.set_key_binding('q', rotate_x_neg)
    engine.set_key_binding('e', rotate_x_pos)
    engine.set_key_binding('w', rotate_y_neg)
    engine.set_key_binding('s', rotate_y_pos)
    engine.set_key_binding('a', rotate_z_neg)
    engine.set_key_binding('d', rotate_z_pos)
    engine.set_key_binding('j', prev_shape)
    engine.set_key_binding('l', next_shape)
    engine.set_key_binding('z', zoom_in)
    engine.set_key_binding('x', zoom_out)
    engine.set_key_binding('\x1b', quit_app)
    engine.set_key_binding('\x03', quit_app)
    engine.set_key_binding('r', toggle_auto_rotate)

    engine.set_camera_position(0, 0, zoom)
    engine.set_camera_rotation(0, 0, 0)
    engine.set_ambient_light(150, 150, 150)
    engine.add_light(Vec3(1, 1, 1), (255, 255, 255), 0.8)
    engine.set_render_quality(q)

    original_draw_frame = engine._draw_frame
    def draw_frame_with_name():
        nonlocal auto_rotate
        if auto_rotate:
            current_node.transform.rot.y += 0.022
            current_node.transform.rot.z += 0.028
            current_node.transform.rot.x += 0.025

        original_draw_frame()
        rot = current_node.transform.rot

        status = "On" if auto_rotate else "Off"
        sys.stdout.write(f"\x1b[{height+1};1HShape: {current_node.name} | Rot: X={rot.x:.2f} Y={rot.y:.2f} Z={rot.z:.2f} Zoom: {-zoom:.1f} \nQWEASD rotate, R toggle auto-rotate, J/L switch shape, Z/X zoom, ESC quit")
        sys.stdout.flush()
    engine._draw_frame = draw_frame_with_name

    engine.run()


if __name__ == "__main__":
    main()