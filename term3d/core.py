#!/usr/bin/env python3
"""
This is a 3D rendering engine for the terminal.
It is designed to be used as a library, with a simple API for building
and rendering scenes from an external file.

Features:
 - Unicode half-block rendering (▀) to pack 2 vertical pixels per character
 - Truecolor ANSI foreground/background for smooth color
 - Mesh rendering with triangle rasterization and z-buffer
 - Multiple directional lights with color and intensity (Lambert)
 - Keyboard controls (cross-platform)
 - Per-object rotation toggle via the API
 - FPS display, adjustable resolution
 - Improved SSAA blending with clear color at object edges

The main term3d class acts as the user's entry point,
exposing a simple API to set up the scene and run the loop.

"""

import sys
import time
import os
import math
from .shpbuild import *
from .vec3lib import Vec3
from .renderer import Renderer
from .__init__ import __version__
from .utils import *

print(f"Term3D by baod[nobucketdev] - Version {__version__}")

# Cross-platform keyboard handling
if os.name == 'nt':
    import msvcrt

    def get_key_nonblocking():
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch in (b"\x00", b"\xe0"):
                ch2 = msvcrt.getch()
                return (ch + ch2).decode(errors='ignore')
            try:
                return ch.decode()
            except Exception:
                return ''
        return None
else:
    import tty
    import termios
    import select

    def get_key_nonblocking():
        """Reads a keypress from Unix without blocking."""
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            return sys.stdin.read(1)
        return None


# New Light class to hold light properties
class Light:
    """Represents a directional light source with color and intensity."""
    def __init__(self, direction, color, intensity):
        self.direction = direction.norm()
        self.color = color
        self.intensity = intensity


# Mesh and Scene classes
class Mesh:
    def __init__(self, verts, faces, colors):
        self.verts = verts
        self.faces = faces
        self.vcols = colors
        self.pos = Vec3(0, 0, 0)
        self.rot = Vec3(0, 0, 0)
        self.scale = Vec3(1, 1, 1)

    def move(self, x=0, y=0, z=0):
        self.pos.x += x
        self.pos.y += y
        self.pos.z += z

    def rotate(self, x=0, y=0, z=0):
        self.rot.x += x
        self.rot.y += y
        self.rot.z += z
        
    def calculate_bounds(self):
        """Calculates the axis-aligned bounding box (AABB) for the mesh."""
        if not self.verts:
            return

        min_x = min(v.x for v in self.verts)
        min_y = min(v.y for v in self.verts)
        min_z = min(v.z for v in self.verts)

        max_x = max(v.x for v in self.verts)
        max_y = max(v.y for v in self.verts)
        max_z = max(v.z for v in self.verts)

        self.min_v = Vec3(min_x, min_y, min_z)
        self.max_v = Vec3(max_x, max_y, max_z)
        

class Camera:
    """
    Represents the camera, handling projection settings, position, and rotation.
    """
    def __init__(self, fov=60.0, znear=0.1, zfar=100.0, zoom=3.0):
        self.fov = fov
        self.znear = znear
        self.zfar = zfar
        self.zoom = zoom
        self.pos = Vec3(0, 0, 0)
        self.rot = Vec3(0, 0, 0) # Pitch, Yaw, Roll

class term3d:
    """
    ## Term3D Engine

    Terminal-based 3D graphics engine for Python.  
    Manages meshes, lights, camera, input, terminal title, status display, and the rendering loop.

    ## Attributes
    - `renderer` : Renderer handling buffers and terminal drawing.
    - `camera` : Camera object with position, rotation, zoom, FOV.
    - `meshes` : List of all scene meshes.
    - `rotating_meshes` : Meshes that rotate automatically.
    - `lights` : List of scene lights.
    - `ambient_light` : RGB tuple for ambient light.
    - `running` : True while the engine loop is active.
    - `fps` : Current frames per second.
    - `quality` : Render quality (1=low, 5=high).
    - `tar_fps` : Target frames per second.
    - `show_status_text` : Toggle FPS/camera overlay.
    - `title_text` : Terminal window title.
    - `key_bindings` : Key-action mapping.
    - `last_terminal_size` : Stores terminal size for auto-resize.

    ## Methods
    - `add_mesh(mesh)` : Add a mesh.
    - `register_for_rotation(mesh)` : Register mesh for rotation.
    - `remove_mesh(mesh)` : Remove mesh.
    - `set_mesh_position(mesh, x, y, z)` : Set mesh position.
    - `set_mesh_rotation(mesh, x, y, z)` : Set mesh rotation.
    - `get_mesh(index)` : Get mesh by index.
    - `add_light(direction, color, intensity=1.0)` : Add a light.
    - `set_light_properties(index, ...)` : Modify light properties.
    - `set_ambient_light(r, g, b)` : Set ambient light.
    - `set_camera_position(x, y, z)` : Move camera.
    - `set_camera_rotation(x, y, z)` : Rotate camera.
    - `set_camera_transform(pos, rot)` : Set position & rotation.
    - `move_camera(x, y, z)` : Move relative.
    - `rotate_camera(x, y, z)` : Rotate relative.
    - `set_camera_zoom(zoom)` : Set zoom.
    - `zoom_camera(delta)` : Adjust zoom.
    - `set_camera_fov(fov)` : Set field of view.
    - `change_fov(delta)` : Adjust FOV.
    - `set_clear_color(r, g, b)` : Set background color.
    - `set_render_quality(level)` : Adjust resolution scaling.
    - `resize_engine(width, height)` : Resize terminal buffers.
    - `set_fps(fps)` : Set target FPS.
    - `set_title(title)` : Set terminal title.
    - `debug(enable)` : Toggle status text display.
    - `run()` : Start main engine loop.

    ## Example
    ```python
    engine = term3d(80, 24)
    engine.add_mesh(my_mesh)
    engine.add_light(Vec3(1, -1, 0), (255, 255, 255))
    engine.set_key_binding('w', lambda: engine.move_camera(z=1))
    engine.set_title("My Demo")
    engine.run()
    ```
    """
    def __init__(self, width_chars, height_chars):
        self.renderer = Renderer(width_chars, height_chars)
        self.renderer.engine_ref = self
        self.camera = Camera(zoom=1.0)
        self.meshes = []
        self.rotating_meshes = []
        self.lights = []
        self.ambient_light = (50, 50, 60)
        self.running = True
        self.last_frame_time = time.time()
        self.fps = 0.0
        self.quality = 3
        self.tar_fps = 30
        self.show_status_text = True
        self.title_text = ""

        self.key_bindings = {}
        self.set_render_quality(self.quality)
        self.last_terminal_size = os.get_terminal_size()

    def add_light(self, direction, color, intensity=1.0):
        self.lights.append(Light(direction, color, intensity))

    def set_key_binding(self, key_code, action_function):
        self.key_bindings[key_code] = action_function

    def set_render_quality(self, quality_level):
        quality_map = {
            0: 1/2,  1: 2/3,  2: 3/4,  3: 1,   
            4: 3/2,  5: 2,    6: 3,    7: 5
        }
        
        self.quality = quality_level
        resolution_factor = quality_map.get(quality_level)
        
        if resolution_factor is not None:
            self.renderer.set_resolution_factor(resolution_factor)
        else:
            print("Invalid quality level. Setting to Medium.")
            self.set_render_quality(2)
            
    def set_manual_quality(self, quality):
        try:
            self.renderer.set_resolution_factor(quality)
        except ValueError:
            print("Invalid quality value. Setting to 1")
            self.renderer.set_resolution_factor(1)

    def add_mesh(self, mesh):
        self.meshes.append(mesh)

    def register_for_rotation(self, mesh):
        self.rotating_meshes.append(mesh)

    def get_mesh(self, index):
        if 0 <= index < len(self.meshes):
            return self.meshes[index]
        return None

    def set_mesh_position(self, mesh, x, y, z):
        if mesh in self.meshes:
            mesh.pos = Vec3(x, y, z)

    def set_mesh_rotation(self, mesh, x, y, z):
        if mesh in self.meshes:
            mesh.rot = Vec3(x, y, z)

    def remove_mesh(self, mesh):
        if mesh in self.meshes:
            self.meshes.remove(mesh)
        if mesh in self.rotating_meshes:
            self.rotating_meshes.remove(mesh)

    def set_camera_zoom(self, zoom):
        self.camera.zoom = zoom

    def set_camera_fov(self, fov):
        self.camera.fov = clamp(fov, 10.0, 160.0)

    def set_camera_position(self, x, y, z):
        self.camera.pos = Vec3(x, y, z)

    def set_camera_rotation(self, x, y, z):
        self.camera.rot = Vec3(x, y, z)

    def set_camera_transform(self, pos, rot):
        self.camera.pos = pos
        self.camera.rot = rot

    def set_light_properties(self, light_index, direction=None, color=None, intensity=None):
        if 0 <= light_index < len(self.lights):
            light = self.lights[light_index]
            if direction:
                light.direction = direction.norm()
            if color:
                light.color = color
            if intensity is not None:
                light.intensity = intensity

    def set_ambient_light(self, r, g, b):
        self.ambient_light = (clamp(r, 0, 255), clamp(g, 0, 255), clamp(b, 0, 255))

    def move_camera(self, x=0, y=0, z=0):
        self.camera.pos.x += x
        self.camera.pos.y += y
        self.camera.pos.z += z

    def rotate_camera(self, x=0, y=0, z=0):
        self.camera.rot.x += x
        self.camera.rot.y += y
        self.camera.rot.z += z

    def zoom_camera(self, delta):
        self.camera.zoom += delta

    def change_fov(self, delta):
        self.set_camera_fov(self.camera.fov + delta)
        
    def reset_camera(self, stepback):
        self.set_camera_position(0, 0, stepback)
        self.set_camera_zoom(1.0)
        self.set_camera_fov(60.0)
        self.set_camera_rotation(0,0,0)

    def set_clear_color(self, r, g, b):
        self.renderer.clear_color = (clamp(r, 0, 255), clamp(g, 0, 255), clamp(b, 0, 255))

    def set_fps(self, fps):
        self.tar_fps = fps

    def resize_engine(self, width_chars, height_chars):
        # Ensure minimum size to prevent errors
        width_chars = max(30, width_chars)
        height_chars = max(12, height_chars)

        self.renderer.base_width_c = width_chars
        self.renderer.base_height_c = height_chars
        self.renderer.set_resolution_factor(self.renderer.res_factor) # Re-initializes buffers
        sys.stdout.write(CLEAR_SCREEN) # Clear the screen after resizing

    def set_title(self, title):
        """Sets the terminal window title."""
        self.title_text = str(title)

    def debug(self, enable):
        """Disables the display of the FPS and camera status text."""
        self.show_status_text = enable


    def run(self):
        try:
            if os.name != 'nt':
                self.old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
            sys.stdout.write(HIDE_CURSOR)
            sys.stdout.write(CLEAR_SCREEN)
            sys.stdout.write(SET_TITLE.format(title=self.title_text))
            sys.stdout.flush()

            while self.running:
                now = time.time()
                dt = now - self.last_frame_time
                self.last_frame_time = now

                self._handle_input()
                self._update(dt)
                self._render_scene()
                self._draw_frame()

                self.fps = 1.0 / max(1e-9, dt)
                time.sleep(max(0.0, 1.0 / self.tar_fps - (time.time() - now)))

        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            sys.stdout.write(RESET)
            sys.stdout.write(SHOW_CURSOR)
            sys.stdout.write('\n')
            sys.stdout.write(SET_TITLE.format(title="")) # Clear title on exit
            sys.stdout.flush()
            if os.name != 'nt':
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    def _render_scene(self):
        self.renderer.clear_buffers()
        for mesh in self.meshes:
            self.renderer.render_mesh(mesh, self.camera, self.lights)

    def _draw_frame(self):
        lines = self.renderer.compose_to_chars()

        # Position cursor at top-left
        sys.stdout.write(CSI + 'H')

        # Write the rendered scene
        sys.stdout.write('\n'.join(lines))

        # Optionally write status text
        if self.show_status_text:
            total_verts = sum(len(m.verts) for m in self.meshes)
            total_tris = sum(len(m.faces) for m in self.meshes)
            num_meshes = len(self.meshes)
            
            lights_info = ""
            if self.lights:
                lights_info += "\nLights:\n"
                for i, light in enumerate(self.lights):
                    dir_str = f"({light.direction.x:.1f}, {light.direction.y:.1f}, {light.direction.z:.1f})"
                    col_str = f"RGB({light.color[0]}, {light.color[1]}, {light.color[2]})"
                    lights_info += f" {i}:\n  Direction: {dir_str}\n  Color: {col_str}\n  Intensity: {light.intensity:.1f}\n"
            else:
                lights_info = "No lights in scene."

            status = (
                f"\nFPS: {self.fps:.1f} | Quality: {self.quality}\n"
                f"Cam Pos: ({self.camera.pos.x:.2f}, {self.camera.pos.y:.2f}, {self.camera.pos.z:.2f})\n"
                f"Cam Rot: ({self.camera.rot.x:.2f}, {self.camera.rot.y:.2f}, {self.camera.rot.z:.2f})\n"
                f"Zoom: {self.camera.zoom:.2f} | FOV: {self.camera.fov:.1f}°\n"
                f"Scene: {num_meshes} meshes, {total_verts} verts, {total_tris} tris\n"
                f"{lights_info}"
            )
            
            # Position the cursor at the top-left and overwrite with the new status text
            sys.stdout.write(CSI + 'H' + status)

        sys.stdout.flush()

    def _update(self, dt):
        for mesh in self.meshes:
            mesh.rot.x = math.fmod(mesh.rot.x, 2 * math.pi)
            mesh.rot.y = math.fmod(mesh.rot.y, 2 * math.pi)
            mesh.rot.z = math.fmod(mesh.rot.z, 2 * math.pi)

    def _handle_input(self):
        key = get_key_nonblocking()
        if key:
            if key in ('\x1b', '\x03'):
                self.running = False
                return

            action = self.key_bindings.get(key.lower())
            if action:
                action()

        # Check for terminal resize
        try:
            current_size = os.get_terminal_size()
            if current_size != self.last_terminal_size:
                # Adjust height to account for status text
                status_lines = 6 # number of lines in the status text
                if not self.show_status_text:
                    status_lines = 0
                self.resize_engine(current_size.columns, current_size.lines - status_lines)
                self.last_terminal_size = current_size
        except Exception:
            pass # Ignore errors if terminal size can't be retrieved

    def test(self):
        """
        Runs a simple demo scene to test the engine's functionality.
        This includes a rotating cube, a light, and basic camera controls.
        """
        print("Starting Term3D Test Scene. Press 'ESC' or 'Ctrl+C' to exit.")

        # Set up the demo scene
        self.set_title("Term3D Test Scene")
        
        # Build a cube mesh using the helper function from shape_builder
        cube_mesh = build_cube(2.0)
        self.add_mesh(cube_mesh)
        self.register_for_rotation(cube_mesh)
        
        # Add a directional light
        self.add_light(Vec3(0.5, 0.5, -1), (255, 255, 255), intensity=1.0)
        
        # Set camera properties
        self.set_camera_position(0, 0, 1.5)
        self.set_camera_fov(60)
        
        # Set up basic keyboard controls
        self.set_key_binding('w', lambda: self.move_camera(z=0.5))
        self.set_key_binding('s', lambda: self.move_camera(z=-0.5))
        self.set_key_binding('a', lambda: self.rotate_camera(y=0.1))
        self.set_key_binding('d', lambda: self.rotate_camera(y=-0.1))
        self.set_key_binding('q', lambda: self.zoom_camera(-0.5))
        self.set_key_binding('e', lambda: self.zoom_camera(0.5))

        # Run the main loop
        self.run()