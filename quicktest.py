#!/usr/bin/env python3
import math, os
from term3d.core import term3d, Vec3
from term3d.shpbuild import build_cube, build_uv_sphere, build_cylinder, build_torus
from term3d.utils import set_mat
from term3d.objects import DirectionalLight, PointLight
import shutil

try:
    cols, rows = os.get_terminal_size(0)
except Exception:
    try:
        cols, rows = os.get_terminal_size(1)
    except Exception:
        cols, rows = (80, 30)

WIDTH_CHARS = max(40, min(140, cols))
HEIGHT_CHARS = max(12, min(60, rows - 2))

print("Welcome to the quicktest of term3d engine (scene graph edition)")
print(f"Terminal size: {WIDTH_CHARS}x{HEIGHT_CHARS}")

q = 5

class OrbitScene:
    def __init__(self):
        self.engine = term3d(WIDTH_CHARS, HEIGHT_CHARS)
        self.frame_count = 0
        
        size = shutil.get_terminal_size(fallback=(80, 24))
        self.last_terminal_size = (size.columns, size.lines - 2)

        # --- Scene graph nodes ---
        # The cube is the central parent node
        self.node_cube   = self.engine.add_mesh_node(build_cube(size=2.5), "cube")
        
        # The orbiting shapes are all children of the cube
        self.node_sphere = self.engine.add_mesh_node(build_uv_sphere(radius=0.5), "sphere", parent=self.node_cube)
        self.node_cyl    = self.engine.add_mesh_node(build_cylinder(radius=0.4, height=1.5), "cylinder", parent=self.node_cube)
        self.node_torus  = self.engine.add_mesh_node(build_torus(R=1.0, r=0.5, segments_R=30, segments_r=10), "torus", parent=self.node_cube)

        # Set the initial positions of the children relative to their parents
        self.node_sphere.set_pos(5.0, 0, 0)
        self.node_cyl.set_pos(0, 0, 6.5)
        self.node_torus.set_pos(0, 2, 8.0)

        # Materials
        set_mat(self.node_cube.mesh, 'wireframe')
        set_mat(self.node_torus.mesh, 'phong')

        # Camera & lighting
        self.engine.reset_camera(stepback=-15)
        self.engine.set_render_quality(q)
        self.engine.set_clear_color(20, 30, 40)
        self.engine.add_light_node(
            DirectionalLight(Vec3(0.5, 0.7, -1.0), (255,255,255), 0.4),
            "sun"
        )
        self.engine.add_pointlight(Vec3(0.0, -3.5, 0.0), (255,255,255), intensity=3.0)
        self.engine.set_ambient_light(60,60,60)

        # Orbit state
        self.orbit_angle_parent = 0.0

        # Hook update
        self.engine._update = self._update_scene
        self._bind_camera_keys()

    def _update_scene(self, dt):
        # Apply independent self-spin to each node
        self.node_cube.transform.rot.x += 0.5 * dt
        self.node_cube.transform.rot.y += 0.8 * dt

        self.node_sphere.transform.rot.y += 0.6 * dt
        self.node_cyl.transform.rot.z    += 1.8 * dt
        self.node_torus.transform.rot.x  += 1.2 * dt
        self.node_torus.transform.rot.y  += 0.7 * dt

        # All orbiting children are driven by the parent cube's rotation
        self.orbit_angle_parent += 0.5 * dt
        self.node_cube.set_rot(0, self.orbit_angle_parent, 0)

        # check terminal resize
        self.frame_count += 1
        if self.frame_count % 30 == 0:
            try:
                current_size = os.get_terminal_size()
                new_w = max(40, min(140, current_size.columns))
                new_h = max(12, min(60, current_size.lines - 2))
                if (new_w, new_h) != self.last_terminal_size:
                    print(f"Resizing to {new_w}x{new_h}")
                    self.engine.resize_engine(new_w, new_h)
                    self.last_terminal_size = (new_w, new_h)
            except Exception:
                pass

    def _bind_camera_keys(self):
        # same as before
        self.engine.set_key_binding('w', lambda: self.engine.move_camera(z=0.5))
        self.engine.set_key_binding('s', lambda: self.engine.move_camera(z=-0.5))
        self.engine.set_key_binding('a', lambda: self.engine.move_camera(x=-0.5))
        self.engine.set_key_binding('d', lambda: self.engine.move_camera(x=0.5))
        self.engine.set_key_binding('q', lambda: self.engine.move_camera(y=0.5))
        self.engine.set_key_binding('e', lambda: self.engine.move_camera(y=-0.5))
        self.engine.set_key_binding('r', lambda: self.engine.reset_camera(stepback=-10))
        self.engine.set_key_binding('i', lambda: self.engine.rotate_camera(x=-0.1))
        self.engine.set_key_binding('k', lambda: self.engine.rotate_camera(x=0.1))
        self.engine.set_key_binding('j', lambda: self.engine.rotate_camera(y=0.1))
        self.engine.set_key_binding('l', lambda: self.engine.rotate_camera(y=-0.1))
        self.engine.set_key_binding('+', lambda: self.engine.zoom_camera(0.25))
        self.engine.set_key_binding('-', lambda: self.engine.zoom_camera(-0.25))

    def run(self):
        self.engine.run()

if __name__ == '__main__':
    OrbitScene().run()