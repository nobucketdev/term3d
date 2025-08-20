#!/usr/bin/env python3
"""
This script demonstrates a scene with a simulated spotlight shining down
on a single sphere using the term3d engine.
"""

from term3d.core import term3d
from term3d.shpbuild import build_uv_sphere, build_plane
from term3d.vec3lib import Vec3
from term3d.utils import set_mat

def main():
    """
    Sets up and runs the main scene with a spotlight.
    """
    # Initialize the term3d engine with a terminal size of 120x36 characters
    engine = term3d(120, 36)
    engine.set_title("Spotlight Scene")
    engine.set_render_quality(5)

    # --- Light Setup ---
    # Create a spotlight positioned high up, shining straight down.
    # The 'position' is where the light source is.
    # The 'direction' is the vector the light is pointing in.
    # The inner and outer angles control the cone of the spotlight.
    engine.add_spotlight(
            position=Vec3(0, -6, 0),        # 6 units above the scene
            direction=Vec3(0, -1, 0),       # aiming straight down (–Y)
            color=(255, 200, 150),          # warm orange/yellow light
            intensity=5.0,                  # strong brightness
            inner_angle=40,                 # wide bright inner cone
            outer_angle=60                  # soft fade at edges
        )

    # Add a subtle ambient light to illuminate the dark areas
    engine.set_ambient_light(60, 60, 70)
   # --- Object Creation ---
    # Create a single UV sphere and position it in the center
    central_sphere = build_uv_sphere(radius=1.5, segments_x=32, segments_y=16, color=(200, 100, 100))
    engine.add_mesh(central_sphere)
    engine.set_mesh_position(central_sphere, 0, -1.5, 0)
    
    # --- Create the plane using the build_plane helper function ---
    plane_mesh = build_plane(width=20, depth=20, segments_x=25, segments_z=25, color=(200,200,200))
    engine.add_mesh(plane_mesh)

    # Register the sphere for automatic rotation, but not the plane
    engine.register_for_rotation(central_sphere)


    # --- Camera and Controls ---
    # Set the initial camera position and field of view
    engine.set_camera_position(0, -5, -8)
    engine.set_camera_fov(60)
    engine.rotate_camera(x=-0.6)

    # Set up basic keyboard controls for camera movement
    engine.set_key_binding('w', lambda: engine.move_camera(z=0.5))
    engine.set_key_binding('s', lambda: engine.move_camera(z=-0.5))
    engine.set_key_binding('a', lambda: engine.rotate_camera(y=-0.1))
    engine.set_key_binding('d', lambda: engine.rotate_camera(y=0.1))
    engine.set_key_binding('q', lambda: engine.rotate_camera(x=0.1))
    engine.set_key_binding('e', lambda: engine.rotate_camera(x=-0.1))
    
    # Run the main engine loop
    engine.run()

if __name__ == "__main__":
    main()
