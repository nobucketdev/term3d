#!/usr/bin/env python3
"""
This script demonstrates a scene with a simulated point light and two spheres
using the term3d engine.
"""

from term3d.core import PointLight, Vec3, term3d
from term3d.shpbuild import build_plane, build_uv_sphere


def main():
    """
    Sets up and runs the main scene.
    """
    # Initialize the term3d engine with a terminal size of 120x36 characters
    engine = term3d(120, 36)
    engine.set_title("Point Light Scene")
    engine.set_render_quality(5)

    # --- Light Setup ---
    # Create the point light as a node
    light = PointLight(
        position=Vec3(0.0, -3.5, 0.0), color=(255, 255, 255), intensity=3.0
    )
    engine.add_light_node(
        light
    )  # Use add_light_node instead of the deprecated add_pointlight

    # Add a subtle ambient light to illuminate the dark areas
    engine.set_ambient_light(60, 60, 70)

    # --- Object Creation ---
    # Create the first UV sphere and position it to the left
    sphere_left_mesh = build_uv_sphere(
        radius=1.0, segments_x=32, segments_y=16, color=(200, 100, 100)
    )
    # Add the sphere as a node and set its position
    sphere_left_node = engine.add_mesh_node(sphere_left_mesh)  # Use add_mesh_node
    engine.set_node_position(
        sphere_left_node, -2.5, 0, 0
    )  # Use set_node_position on the node

    # Create the second UV sphere and position it to the right
    sphere_right_mesh = build_uv_sphere(
        radius=1.0, segments_x=32, segments_y=16, color=(100, 100, 200)
    )
    # Add the sphere as a node and set its position
    sphere_right_node = engine.add_mesh_node(sphere_right_mesh)  # Use add_mesh_node
    engine.set_node_position(
        sphere_right_node, 2.5, 0, 0
    )  # Use set_node_position on the node

    plane_mesh = build_plane(
        width=20, depth=20, segments_x=30, segments_z=30, color=(200, 200, 200)
    )
    # Add the plane mesh as a node
    plane_node = engine.add_mesh_node(plane_mesh)  # Use add_mesh_node

    # --- Camera and Controls ---
    # Set the initial camera position and field of view
    engine.set_camera_position(0, -5, -5.5)
    engine.set_camera_fov(60)
    engine.rotate_camera(x=-0.9)

    # Set up basic keyboard controls for camera movement
    engine.set_key_binding("w", lambda: engine.move_camera(z=0.5))
    engine.set_key_binding("s", lambda: engine.move_camera(z=-0.5))
    engine.set_key_binding("a", lambda: engine.rotate_camera(y=-0.1))
    engine.set_key_binding("d", lambda: engine.rotate_camera(y=0.1))
    engine.set_key_binding("q", lambda: engine.rotate_camera(x=0.1))
    engine.set_key_binding("e", lambda: engine.rotate_camera(x=-0.1))

    # --- Run the Engine ---
    # Start the main rendering loop
    engine.run()


if __name__ == "__main__":
    main()
