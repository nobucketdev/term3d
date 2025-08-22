from __future__ import annotations
from typing import List, Optional, Callable
from .vec3lib import Vec3
from .mat4lib import Mat4
import sys
import time
import os
import math
from .shpbuild import *
from .vec3lib import Vec3
from .renderer import Renderer
from .__init__ import __version__
from .utils import *
from .objects import *
from typing import List, Optional, Callable

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


class Transform:
    def __init__(self, pos: Optional[Vec3]=None, rot: Optional[Vec3]=None, scale: Optional[Vec3]=None, pivot: Optional[Vec3]=None):
        self.pos = pos if pos is not None else Vec3(0,0,0)
        self.rot = rot if rot is not None else Vec3(0,0,0)  # pitch, yaw, roll
        self.scale = scale if scale is not None else Vec3(1,1,1)
        # NEW: The point around which rotation and scaling occurs.
        self.pivot = pivot if pivot is not None else Vec3(0,0,0)

    def to_matrix(self) -> Mat4:
        # T_pos * T_pivot * R_rot * S_scale * T_neg_pivot
        # This order applies transformations around the pivot point.
        return (Mat4.translate(self.pos.x, self.pos.y, self.pos.z) *
                Mat4.translate(self.pivot.x, self.pivot.y, self.pivot.z) *
                Mat4.rotate_y(self.rot.y) *
                Mat4.rotate_x(self.rot.x) *
                Mat4.rotate_z(self.rot.z) *
                Mat4.scale(self.scale.x, self.scale.y, self.scale.z) *
                Mat4.translate(-self.pivot.x, -self.pivot.y, -self.pivot.z))

class SceneNode:
    def __init__(self, name: str = "node"):
        self.name = name
        self.transform = Transform()
        self.mesh = None       # Optional[Mesh]
        self.light = None      # Optional[Light]
        self.camera = None     # Optional[Camera] (not used yet, but handy)
        self.children: List[SceneNode] = []
        self.parent: Optional[SceneNode] = None

    # --- Hierarchy ---
    def add(self, child:'SceneNode') -> 'SceneNode':
        if child.parent is not None:
            child.parent.remove(child)
        child.parent = self
        self.children.append(child)
        return child

    def remove(self, child:'SceneNode') -> None:
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    # --- World transform ---
    def world_matrix(self) -> Mat4:
        m = self.transform.to_matrix()
        p = self.parent
        while p is not None:
            m = p.transform.to_matrix() * m
            p = p.parent
        return m

    # --- Traversal ---
    def traverse(self, fn: Callable[['SceneNode'], None]) -> None:
        fn(self)
        for c in self.children:
            c.traverse(fn)

    # --- Convenience ---
    def set_pos(self, x=0.0, y=0.0, z=0.0):
        self.transform.pos = Vec3(x,y,z)
        return self

    def set_rot(self, x=0.0, y=0.0, z=0.0):
        self.transform.rot = Vec3(x,y,z)
        return self

    def get_rot(self) -> Vec3:
        """Return local rotation (Euler angles)."""
        return self.transform.rot

    def get_world_rot(self) -> Vec3:
        """Return cumulative/world rotation (adds parent rotations)."""
        r = self.transform.rot
        p = self.parent
        while p is not None:
            r = r + p.transform.rot
            p = p.parent
        return r

    def set_scale(self, x=1.0, y=1.0, z=1.0):
        self.transform.scale = Vec3(x,y,z)
        return self

    def set_pivot(self, x=0.0, y=0.0, z=0.0):
        """Set the pivot point for rotation and scaling."""
        self.transform.pivot = Vec3(x,y,z)
        return self

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
        self.meshes = []  # DEPRECATED: legacy flat list
        self.root = SceneNode('root')
        self._legacy_group = self.root.add(SceneNode('legacy_meshes'))
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
        self._update_function = None

        self.key_bindings = {}
        self.set_render_quality(self.quality)
        self.last_terminal_size = os.get_terminal_size()

    def add_light(self, direction, color, intensity=1.0):
        self.lights.append(DirectionalLight(direction, color, intensity))

    def add_spotlight(self, position, direction, color, intensity=1.0, inner_angle=15.0, outer_angle=20.0):
        self.lights.append(SpotLight(position, direction, color, intensity, inner_angle, outer_angle))

    def add_pointlight(self, position, color, intensity=1.0):
        self.lights.append(PointLight(position, color, intensity))
        
    def set_key_binding(self, key_code, action_function):
        self.key_bindings[key_code] = action_function

    def set_on_update(self, update_function: Callable[[float], None]):
        """Sets a function to be called on every frame update with the delta time (dt)."""
        self._update_function = update_function

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


    # --- Scene Graph API ---
    def create_node(self, name: str='node', parent: SceneNode=None) -> SceneNode:
        parent = parent or self.root
        return parent.add(SceneNode(name))

    def add_mesh_node(self, mesh, name: str='mesh', parent: SceneNode=None) -> SceneNode:
        node = self.create_node(name, parent)
        node.mesh = mesh
        # Keep legacy list updated for stats / backwards compatibility.
        self.meshes.append(mesh)
        return node

    def add_light_node(self, light, name: str='light', parent: SceneNode=None) -> SceneNode:
        node = self.create_node(name, parent)
        node.light = light
        self.lights.append(light)
        return node

    def add_mesh(self, mesh):            # Deprecated
        # Back-compat: keep flat list AND attach to scene graph under legacy group
        self.meshes.append(mesh)
        node = SceneNode('mesh')
        node.mesh = mesh
        self._legacy_group.add(node)

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



    # --- Node transform helpers ---
    def set_node_position(self, node: SceneNode, x, y, z):
        node.set_pos(x,y,z)

    def set_node_rotation(self, node: SceneNode, x, y, z):
        node.set_rot(x,y,z)

    def set_node_scale(self, node: SceneNode, x, y, z):
        node.set_scale(x,y,z)
    
    def set_node_pivot(self, node: SceneNode, x, y, z):
        node.set_pivot(x,y,z)
        
    def get_node_position(self, name: str) -> Optional[Vec3]:
        node = self.get_node(name)
        if node:
            return node.transform.pos
        return None
    
    def get_node_world_rotation(self, name: str) -> Optional[Vec3]:
        node = self.get_node(name)
        if node:
            return node.get_world_rot()
        return None
        
    def get_node_rotation(self, node_id):
        node = self.nodes.get(node_id)
        if node:
            return node.get_rot()
        return None

    def get_node_world_rotation(self, node_id):
        node = self.nodes.get(node_id)
        if node:
            return node.get_world_rot()
        return None        

    def get_node(self, name: str) -> Optional[SceneNode]:
        return self.nodes.get(name)
    
    def look_at(self, target: Vec3):
        # Calculate the direction vector from the camera to the target
        direction = target - self.camera.pos
        
        # Calculate yaw (rotation around the Y-axis)
        yaw = math.atan2(direction.x, direction.z)
        
        # Calculate pitch (rotation around the X-axis)
        # Use a temporary vector to project the direction onto the XZ plane
        pitch_vector = Vec3(direction.x, 0, direction.z)
        pitch = -math.atan2(direction.y, pitch_vector.length())
        
        # Update camera rotation
        self.camera.rot.x = pitch
        self.camera.rot.y = yaw
        self.camera.rot.z = 0.0

    def duplicate_node(self, node: SceneNode, parent: SceneNode = None) -> SceneNode:
        import copy
        
        new_node = SceneNode(node.name + "_copy", parent=parent or node.parent)
        new_node.local_transform = copy.deepcopy(node.local_transform)
        
        if node.mesh:
            new_mesh = copy.deepcopy(node.mesh)
            new_node.mesh = new_mesh
            self.meshes.append(new_mesh)
        
        if node.light:
            new_light = copy.deepcopy(node.light)
            new_node.light = new_light
            self.lights.append(new_light)
        
        # Recursively duplicate child nodes
        for child in node.children:
            self.duplicate_node(child, new_node)
            
        return new_node
        
    def remove_node(self, node: SceneNode):
        # Recursively remove children first
        for child in list(node.children):
            self.remove_node(child)

        # Remove the mesh from the engine's lists if it exists
        if node.mesh and node.mesh in self.meshes:
            self.meshes.remove(node.mesh)
            if node.mesh in self.rotating_meshes:
                self.rotating_meshes.remove(node.mesh)
        
        # Remove the light from the engine's list if it exists
        if node.light and node.light in self.lights:
            self.lights.remove(node.light)
            
        # Remove the node from its parent
        if node.parent:
            node.parent.children.remove(node)
            
            

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

        def draw(node: SceneNode):
            if node.mesh is not None:
                self.renderer.render_mesh(node.mesh, self.camera, self.lights, model_matrix=node.world_matrix())
        self.root.traverse(draw)

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
                    light_type = "Unknown"
                    props = []
                    
                    # Check the type of the light and get its properties
                    if isinstance(light, DirectionalLight):
                        light_type = "Directional"
                        props.append(f"Direction:   ({light.direction.x:.1f}, {light.direction.y:.1f}, {light.direction.z:.1f})")
                        props.append(f"Color:       RGB({light.color[0]}, {light.color[1]}, {light.color[2]})")
                        props.append(f"Intensity:   {light.intensity:.1f}")
                    elif isinstance(light, SpotLight):
                        light_type = "Spotlight"
                        props.append(f"Position:    ({light.position.x:.1f}, {light.position.y:.1f}, {light.position.z:.1f})")
                        props.append(f"Direction:   ({light.direction.x:.1f}, {light.direction.y:.1f}, {light.direction.z:.1f})")
                        props.append(f"Color:       RGB({light.color[0]}, {light.color[1]}, {light.color[2]})")
                        props.append(f"Intensity:   {light.intensity:.1f}")
                        props.append(f"Inner Angle: {math.degrees(light.inner_angle):.1f}°")
                        props.append(f"Outer Angle: {math.degrees(light.outer_angle):.1f}°")
                    elif isinstance(light, PointLight):
                        light_type = "Point"
                        props.append(f"Position:    ({light.position.x:.1f}, {light.position.y:.1f}, {light.position.z:.1f})")
                        props.append(f"Color:       RGB({light.color[0]}, {light.color[1]}, {light.color[2]})")
                        props.append(f"Intensity:   {light.intensity:.1f}")

                    # Format the output string
                    props_str = "\n  ".join(props)
                    lights_info += f" {i}: {light_type}\n  {props_str}\n"
            else:
                lights_info = "No lights in scene."


            status = f"""
FPS:     {self.fps:<6.1f}    Quality: {self.quality}
Cam Pos: ({self.camera.pos.x:>6.2f}, {self.camera.pos.y:>6.2f}, {self.camera.pos.z:>6.2f})
Cam Rot: ({self.camera.rot.x:>6.2f}, {self.camera.rot.y:>6.2f}, {self.camera.rot.z:>6.2f})
Zoom:    {self.camera.zoom:<6.2f}    FOV: {self.camera.fov:.1f}°
Scene:   {num_meshes} meshes, {total_verts} verts, {total_tris} tris
{lights_info}
            """

            
            # Position the cursor at the top-left and overwrite with the new status text
            sys.stdout.write(CSI + 'H' + status)

        sys.stdout.flush()

    def _update(self, dt):
        if self._update_function:
            self._update_function(dt)
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