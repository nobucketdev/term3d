#!/usr/bin/env python3

import math
import os
from term3d.core import term3d, Vec3, PointLight
from term3d.shpbuild import build_cube, build_uv_sphere, build_cylinder, build_torus
from term3d.utils import set_mat
try:
    cols, rows = os.get_terminal_size(0)
except Exception:
    try:
        cols, rows = os.get_terminal_size(1)
    except Exception:
        cols, rows = (80, 30)
WIDTH_CHARS = max(40, min(140, cols))
HEIGHT_CHARS = max(12, min(60, rows - 2))
print("Welcome to the orbit.py test of term3d engine")
print(f"Terminal size: {WIDTH_CHARS}x{HEIGHT_CHARS}")
print("This test shows a big wireframe cube in the middle of the scene")
print("There is a flat shader(material) sphere and cylinder, and a Phong shader Donut orbiting around the cube")

q = 3 

class OrbitScene:
    def __init__(self):
        self.engine = term3d(WIDTH_CHARS, HEIGHT_CHARS)
        self.frame_count = 0
        try:
            current_cols, current_rows = os.get_terminal_size()
            self.last_terminal_size = (current_cols, current_rows - 2)
        except Exception:
            self.last_terminal_size = (WIDTH_CHARS, HEIGHT_CHARS)

        # Create a large central cube
        self.main_cube = build_cube(size=2.5)
        self.engine.add_mesh(self.main_cube)

        self.orbiting_sphere = build_uv_sphere(radius=0.5)
        self.engine.add_mesh(self.orbiting_sphere)

        self.orbiting_cylinder = build_cylinder(radius=0.4, height=1.5)
        self.engine.add_mesh(self.orbiting_cylinder)

        self.orbiting_torus = build_torus(R=1.0, r=0.5, segments_R=30, segments_r=10)
        self.engine.add_mesh(self.orbiting_torus)

        # Set materials for objects
        set_mat(self.main_cube, 'wireframe')  # Set the main cube to wireframe material
        set_mat(self.orbiting_torus, 'phong')  # Set the orbiting donut to Phong material

        self.engine.reset_camera(stepback=-10)
        
        self.engine.set_render_quality(q)

        self.engine.set_clear_color(20,30,40) 
        self.engine.add_light(Vec3(0.5, 0.7, -1.0), (255, 255, 255), 0.4)       # Make it low for now

        # Add a point light, focus on the circle orbiting, if it become dark near siting between the cube and camera and lit(color toward orange) siting opposite the camera, the PointLight work!
        point_light_pos = Vec3(0, 0, 0)   # I add a point light in center for testing
        point_light_color = (255, 210, 150)
        point_light_intensity = 1.0
        new_point_light = PointLight(point_light_pos, point_light_color, point_light_intensity)
        self.engine.lights.append(new_point_light)

        self.engine.set_ambient_light(60,60,60)    

        self.orbit_angle_sphere = 0.0
        self.orbit_angle_cylinder = math.pi / 2  
        self.orbit_angle_torus = math.pi  
        
        self.orbit_radius_sphere = 5.0
        self.orbit_radius_cylinder = 6.5
        self.orbit_radius_torus = 8.0

        self.engine._update = self._update_scene
        
        self._bind_camera_keys()

    def _update_scene(self, dt):
        for mesh in self.engine.meshes:
            mesh.rot.x += 0.5 * dt
            mesh.rot.y += 0.8 * dt

        self.orbit_angle_sphere += 1.22 * dt
        x_s = self.orbit_radius_sphere * math.cos(self.orbit_angle_sphere)
        z_s = self.orbit_radius_sphere * math.sin(self.orbit_angle_sphere)
        self.orbiting_sphere.pos = Vec3(x_s, 0, z_s)
        

        self.orbit_angle_cylinder += 0.85 * dt
        x_c = self.orbit_radius_cylinder * math.cos(self.orbit_angle_cylinder)
        y_c = self.orbit_radius_cylinder * math.sin(self.orbit_angle_cylinder)
        self.orbiting_cylinder.pos = Vec3(x_c, y_c, 0)
        self.orbiting_cylinder.rot.z += 1.8 * dt 
        
        self.orbit_angle_torus += 0.4 * dt
        x_t = self.orbit_radius_torus * math.cos(self.orbit_angle_torus)
        z_t = self.orbit_radius_torus * math.sin(self.orbit_angle_torus)
        self.orbiting_torus.pos = Vec3(x_t, 2, z_t) 
        self.orbiting_torus.rot.x += 1.2 * dt
        self.orbiting_torus.rot.y += 0.7 * dt

        self.frame_count += 1
        if self.frame_count % 30 == 0:
            try:
                current_size = os.get_terminal_size()
                current_width = max(40, min(140, current_size.columns))
                current_height = max(12, min(60, current_size.lines - 2))
                
                if (current_width, current_height) != self.last_terminal_size:
                    print(f"Resizing to {current_width}x{current_height}")
                    self.engine.resize_engine(current_width, current_height)
                    self.last_terminal_size = (current_width, current_height)
            except Exception:
                pass
        
    def _bind_camera_keys(self):
        key_up = 'i'
        key_down = 'k'
        key_left = 'j'
        key_right = 'l'

        def move_camera_relative(dx=0, dy=0, dz=0):
            pitch = self.engine.camera.rot.x
            yaw = self.engine.camera.rot.y

            forward = Vec3(
                math.cos(pitch) * math.sin(yaw),
                math.sin(pitch),
                math.cos(pitch) * math.cos(yaw)
            )

            right = Vec3(
                math.sin(yaw - math.pi / 2),
                0,
                math.cos(yaw - math.pi / 2)
            )

            up = Vec3(0,1,0)

            move_vec = Vec3(
                forward.x * dz + right.x * dx + up.x * dy,
                forward.y * dz + right.y * dx + up.y * dy,
                forward.z * dz + right.z * dx + up.z * dy
            )

            self.engine.move_camera(
                x=move_vec.x,
                y=move_vec.y,
                z=move_vec.z
            )

        self.engine.set_key_binding('w', lambda: move_camera_relative(dz=0.5))  
        self.engine.set_key_binding('s', lambda: move_camera_relative(dz=-0.5)) 
        self.engine.set_key_binding('a', lambda: move_camera_relative(dx=-0.5))
        self.engine.set_key_binding('d', lambda: move_camera_relative(dx=0.5)) 
        self.engine.set_key_binding('q', lambda: move_camera_relative(dy=0.5))
        self.engine.set_key_binding('e', lambda: move_camera_relative(dy=-0.5))
        
        self.engine.set_key_binding('r', lambda: self.engine.reset_camera(stepback=-10))

        self.engine.set_key_binding(key_up, lambda: self.engine.rotate_camera(x=-0.1))
        self.engine.set_key_binding(key_down, lambda: self.engine.rotate_camera(x=0.1))
        self.engine.set_key_binding(key_left, lambda: self.engine.rotate_camera(y=0.1))
        self.engine.set_key_binding(key_right, lambda: self.engine.rotate_camera(y=-0.1))

        self.engine.set_key_binding('+', lambda: self.engine.zoom_camera(0.25))
        self.engine.set_key_binding('-', lambda: self.engine.zoom_camera(-0.25))

    def run(self):
        self.engine.run()

if __name__ == '__main__':
    scene = OrbitScene()
    scene.run()


