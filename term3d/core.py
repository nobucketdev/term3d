from __future__ import annotations

import fnmatch
import math
import os
import shutil
import sys
import time
from typing import Callable, List, Optional

from .__init__ import __version__
from .objects import *
from .renderer import Renderer
from .shpbuild import *
from .utils import *
from .math3d import Vec3

print(f"Term3D by baod[nobucketdev] - Version {__version__}")

# Cross-platform keyboard handling
if os.name == "nt":
    import msvcrt

    def get_key_nonblocking():
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch in (b"\x00", b"\xe0"):
                ch2 = msvcrt.getch()
                return (ch + ch2).decode(errors="ignore")
            try:
                return ch.decode()
            except Exception:
                return ""
        return None

else:
    import select
    import termios
    import tty

    def get_key_nonblocking():
        """Reads a keypress from Unix without blocking."""
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            return sys.stdin.read(1)
        return None


class term3d:
    """
    ## Term3D Engine

    Terminal-based 3D graphics engine for Python. This class is the central
    component for managing the 3D scene, rendering loop, and user interaction.
    It utilizes a scene graph to organize meshes, lights, and other objects.

    ### Attributes
    - `renderer`: The `Renderer` instance responsible for handling the
      drawing buffers and outputting characters to the terminal.
    - `camera`: The `Camera` object that defines the viewer's position,
      rotation, zoom, and field of view within the scene.
    - `root`: The root `SceneNode` of the scene graph. All other nodes
      are children of this node, either directly or indirectly.
    - `nodes`: A dictionary for quick lookup of any `SceneNode` by its
      unique name.
    - `ambient_light`: The base light color applied to all objects in
      the scene, represented as an RGB tuple `(r, g, b)`.
    - `running`: A boolean flag that controls the main rendering loop.
      The loop continues as long as this is `True`.
    - `fps`: The current frames per second being rendered.
    - `quality`: The current render quality level (0-7), which determines
      the resolution scaling factor.
    - `tar_fps`: The target frames per second for the engine loop.
    - `show_status_text`: A boolean that toggles the display of the
      FPS/camera information overlay.
    - `title_text`: The string displayed as the terminal window's title.
    - `key_bindings`: A dictionary mapping key characters (e.g., 'w', 's')
      to their corresponding action functions.
    - `rotating_nodes`: A list of `SceneNode` objects that are
      automatically rotated each frame for a demo effect.
    - `last_frame_time`: The timestamp of the previous frame's update.
    - `last_terminal_size`: The terminal dimensions at the last check,
      used to detect resize events.

    ### Methods

    #### Scene Graph API
    - `create_node(name='node', parent=None, tags=None)`: Creates a new `SceneNode` and adds it to the scene graph.
    - `get_node(name)`: Retrieves a `SceneNode` by its name.
    - `add_mesh_node(mesh, name='mesh', parent=None)`: Creates a new `SceneNode` with a mesh component.
    - `add_light_node(light, name='light', parent=None)`: Creates a new `SceneNode` with a light component.
    - `register_for_rotation(node)`: Adds a node to a list for automatic rotation.
    - `remove_node(node)`: Removes a node and its descendants from the scene graph.

    #### Camera Controls
    - `set_camera_zoom(zoom)`: Sets the camera's zoom level.
    - `set_camera_fov(fov)`: Sets the camera's field of view in degrees.
    - `set_camera_position(x, y, z)`: Sets the camera's position.
    - `set_camera_rotation(x, y, z)`: Sets the camera's rotation in radians.
    - `set_camera_transform(pos, rot)`: Sets position and rotation using `Vec3` objects.
    - `move_camera(x=0, y=0, z=0)`: Moves the camera by a relative amount.
    - `rotate_camera(x=0, y=0, z=0)`: Rotates the camera by a relative amount.
    - `zoom_camera(delta)`: Zooms the camera by a relative amount.
    - `change_fov(delta)`: Changes the camera's FOV by a relative amount.
    - `reset_camera(stepback)`: Resets the camera to a default position.
    - `look_at(target)`: Orients the camera to face a specific world coordinate.

    #### Node Transform Helpers
    - `set_node_position(node, x, y, z)`: Sets the position of a specific scene node.
    - `set_node_rotation(node, x, y, z)`: Sets the rotation of a specific scene node.
    - `set_node_scale(node, x, y, z)`: Sets the scale of a specific scene node.
    - `set_node_pivot(node, x, y, z)`: Sets the pivot point for a node.

    #### Node Search and Retrieval
    - `get_node_position(name)`: Retrieves the position of a node by name.
    - `get_node_world_rotation(name)`: Retrieves the world rotation of a node.
    - `get_node_rotation(name)`: Retrieves the local rotation of a node.
    - `get_node_id(name)`: Retrieves a node's unique ID by name.
    - `find_by_id(node_id)`: Finds a node by its unique ID.
    - `find_by_name(pattern)`: Finds all nodes whose names match a wildcard pattern.
    - `find_all(condition)`: Finds nodes that satisfy a custom lambda condition.
    - `find_with_mesh()`: Finds all nodes with a mesh component.
    - `find_with_light()`: Finds all nodes with a light component.
    - `get_parent(node)`: Returns the parent of a given node.
    - `list_children(node)`: Returns a list of the immediate children of a node.
    - `list_all_descendants(node)`: Returns a flat list of all descendant nodes.

    #### Advanced Tagging and Search APIs
    - `find_nodes_by_tag(tag)`: Finds all nodes with a specific tag.
    - `find_nodes_with_any_tag(*tags)`: Finds all nodes with at least one of the specified tags.
    - `find_nodes_with_all_tags(*tags)`: Finds all nodes with all of the specified tags.
    - `find_nodes_by_name_and_tag(pattern, tag)`: Finds nodes that match a name pattern and have a specific tag.

    #### Engine Configuration and Control
    - `__init__(width_chars, height_chars)`: Initializes the engine.
    - `set_key_binding(key_code, action_function)`: Binds a keypress to a function.
    - `set_on_update(update_function)`: Sets a custom function to run on every frame.
    - `set_render_quality(quality_level)`: Adjusts the resolution scaling.
    - `set_manual_quality(quality)`: Sets a custom resolution factor.
    - `set_ambient_light(r, g, b)`: Sets the ambient light color.
    - `set_clear_color(r, g, b)`: Sets the terminal background color.
    - `set_fps(fps)`: Sets the target frames per second.
    - `resize_engine(width_chars, height_chars)`: Resizes the engine's buffers.
    - `set_title(title)`: Sets the terminal window's title.
    - `debug(enable)`: Toggles the debug status overlay.
    - `run()`: Starts the main engine loop.
    - `test()`: Runs a simple demo scene.
    - `duplicate_node(node, parent=None)`: Creates a deep copy of a node and its descendants.

    #### Deprecated Methods (Backwards Compatibility)
    - `add_light(direction, color, intensity=1.0)`: Use `add_light_node()` with a `DirectionalLight` instead.
    - `add_spotlight(position, direction, color, ...)`: Use `add_light_node()` with a `SpotLight` instead.
    - `add_pointlight(position, color, intensity=1.0)`: Use `add_light_node()` with a `PointLight` instead.
    - `add_mesh(mesh)`: Use `add_mesh_node()` instead.
    - `remove_mesh(mesh)`: Use `remove_node(node)` instead.
    - `set_light_properties(light_index, ...)`: Modify the light's node component directly.

    #### Internal Methods (Not for general use)
    - `_render_scene()`: Traverses the scene graph and renders visible meshes.
    - `_draw_frame()`: Writes the final frame to the terminal.
    - `_update(dt)`: The main update step of the engine loop.
    - `_handle_input()`: Checks for keyboard input and terminal resizes.
    """

    def __init__(self, width_chars, height_chars):
        self.renderer = Renderer(width_chars, height_chars)
        self.renderer.engine_ref = self
        self.camera = Camera(zoom=1.0)

        # New scene graph core
        self.root = SceneNode("root")
        self.nodes = {"root": self.root}
        self.ambient_light = (50, 50, 60)
        self.rotating_nodes = []  # Tracks nodes for automatic rotation

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
        self.last_terminal_size = shutil.get_terminal_size(fallback=(80, 24))

    # --- Scene Graph API ---
    def create_node(
        self,
        name: str = "node",
        parent: SceneNode = None,
        tags: Optional[List[str]] = None,
    ) -> SceneNode:
        if name in self.nodes:
            i = 1
            while f"{name}_{i}" in self.nodes:
                i += 1
            name = f"{name}_{i}"

        parent = parent or self.root
        node = SceneNode(name)
        parent.add(node)
        self.nodes[name] = node
        if tags:
            node.add_tag(*tags)  # Add tags during creation
        return node

    def get_node(self, name: str) -> Optional[SceneNode]:
        return self.nodes.get(name)

    def add_mesh_node(
        self, mesh, name: str = "mesh", parent: SceneNode = None
    ) -> SceneNode:
        node = self.create_node(name, parent)
        node.mesh = mesh
        return node

    def add_light_node(
        self, light, name: str = "light", parent: SceneNode = None
    ) -> SceneNode:
        node = self.create_node(name, parent)
        node.light = light
        return node

    # --- Backwards compatibility for old API methods ---
    def add_light(self, direction, color, intensity=1.0):
        light = DirectionalLight(direction, color, intensity)
        self.add_light_node(light, name="dir_light")

    def add_spotlight(
        self,
        position,
        direction,
        color,
        intensity=1.0,
        inner_angle=15.0,
        outer_angle=20.0,
    ):
        light = SpotLight(
            position, direction, color, intensity, inner_angle, outer_angle
        )
        self.add_light_node(light, name="spotlight")

    def add_pointlight(self, position, color, intensity=1.0):
        light = PointLight(position, color, intensity)
        self.add_light_node(light, name="pointlight")

    def add_mesh(self, mesh):
        self.add_mesh_node(mesh, name="legacy_mesh")

    def register_for_rotation(self, node: SceneNode):
        if node.mesh is not None:
            self.rotating_nodes.append(node)

    def remove_mesh(self, mesh):
        # Find the node that holds this mesh and remove it
        node_to_remove = None
        for name, node in self.nodes.items():
            if node.mesh is mesh:
                node_to_remove = node
                break
        if node_to_remove:
            self.remove_node(node_to_remove)

    # --- End of back-compat changes ---

    def set_key_binding(self, key_code, action_function):
        self.key_bindings[key_code] = action_function

    def set_on_update(self, update_function: Callable[[float], None]):
        """Sets a function to be called on every frame update with the delta time (dt)."""
        self._update_function = update_function

    def set_render_quality(self, quality_level):
        quality_map = {0: 1 / 2, 1: 2 / 3, 2: 3 / 4, 3: 1, 4: 3 / 2, 5: 2, 6: 3, 7: 5}

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

    def set_light_properties(
        self, light_index, direction=None, color=None, intensity=None
    ):
        # This function is now deprecated due to scene graph.
        # It's better to get the light node and change its properties directly.
        pass

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
        self.set_camera_rotation(0, 0, 0)

    # --- Node transform helpers ---
    def set_node_position(self, node: SceneNode, x, y, z):
        node.set_pos(x, y, z)

    def set_node_rotation(self, node: SceneNode, x, y, z):
        node.set_rot(x, y, z)

    def set_node_scale(self, node: SceneNode, x, y, z):
        node.set_scale(x, y, z)

    def set_node_pivot(self, node: SceneNode, x, y, z):
        node.set_pivot(x, y, z)

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

    def get_node_id(self, name: str) -> Optional[str]:
        """Retrieves a node's unique ID by its name."""
        node = self.get_node(name)
        if node:
            return str(node.id)
        return None

    def find_by_id(self, node_id) -> Optional[SceneNode]:
        return next((n for n in self.nodes.values() if str(n.id) == str(node_id)), None)

    def find_by_name(self, pattern: str) -> List[SceneNode]:
        """Wildcard name search (e.g., 'cube*' or '*light')."""
        return [n for n in self.nodes.values() if fnmatch.fnmatch(n.name, pattern)]

    def find_all(self, condition) -> List[SceneNode]:
        """Find nodes using a custom lambda condition."""
        # Find all nodes by traversing the scene graph
        all_nodes = self.list_all_descendants(self.root)
        # Filter the nodes based on the condition
        return [n for n in all_nodes if condition(n)]

    def find_with_mesh(self) -> List[SceneNode]:
        # Uses the improved find_all method
        return self.find_all(lambda n: n.mesh is not None)

    def find_with_light(self) -> List[SceneNode]:
        # Uses the improved find_all method
        return self.find_all(lambda n: n.light is not None)

    def get_parent(self, node: SceneNode) -> Optional[SceneNode]:
        return node.get_parent()

    def list_children(self, node: SceneNode) -> List[SceneNode]:
        return node.get_children()

    def list_all_descendants(self, node: SceneNode) -> List[SceneNode]:
        result = []

        def collect(n):
            for child in n.children:
                result.append(child)
                collect(child)

        collect(node)
        return result

    # --- Advanced Tagging and Search APIs ---
    def find_nodes_by_tag(self, tag: str) -> List[SceneNode]:
        """Finds all nodes that have a specific tag."""
        return self.find_all(lambda n: n.has_tag(tag))

    def find_nodes_with_any_tag(self, *tags: str) -> List[SceneNode]:
        """Finds all nodes that have at least one of the specified tags."""
        return self.find_all(lambda n: n.has_any_tag(*tags))

    def find_nodes_with_all_tags(self, *tags: str) -> List[SceneNode]:
        """Finds all nodes that have all of the specified tags."""
        return self.find_all(lambda n: n.has_all_tags(*tags))

    def find_nodes_by_name_and_tag(self, pattern: str, tag: str) -> List[SceneNode]:
        """Finds nodes that match a name pattern and have a specific tag."""
        return self.find_all(
            lambda n: fnmatch.fnmatch(n.name, pattern) and n.has_tag(tag)
        )

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

        # Create a new node and recursively duplicate its children
        new_node = self.create_node(
            name=node.name + "_copy", parent=parent or node.parent
        )
        new_node.transform = copy.deepcopy(node.transform)

        if node.mesh:
            new_node.mesh = copy.deepcopy(node.mesh)

        if node.light:
            new_node.light = copy.deepcopy(node.light)

        for child in node.children:
            self.duplicate_node(child, new_node)

        return new_node

    def remove_node(self, node: SceneNode):
        # Recursively remove children first
        for child in list(node.children):
            self.remove_node(child)

        # Remove the node from the master dictionary
        if node.name in self.nodes:
            del self.nodes[node.name]

        # Remove the node from its parent
        if node.parent:
            node.parent.remove(node)

        if node in self.rotating_nodes:
            self.rotating_nodes.remove(node)

    def hide(self):
        self.is_visible = False

    def show(self):
        self.is_visible = True

    def toggle_visibility(self):
        self.is_visible = not self.is_visible

    def set_clear_color(self, r, g, b):
        self.renderer.clear_color = (
            clamp(r, 0, 255),
            clamp(g, 0, 255),
            clamp(b, 0, 255),
        )

    def set_fps(self, fps):
        self.tar_fps = fps

    def resize_engine(self, width_chars, height_chars):
        # Ensure minimum size to prevent errors
        width_chars = max(30, width_chars)
        height_chars = max(12, height_chars)

        self.renderer.base_width_c = width_chars
        self.renderer.base_height_c = height_chars
        self.renderer.set_resolution_factor(
            self.renderer.res_factor
        )  # Re-initializes buffers
        sys.stdout.write(CLEAR_SCREEN)  # Clear the screen after resizing

    def set_title(self, title):
        """Sets the terminal window title."""
        self.title_text = str(title)

    def debug(self, enable):
        """Disables the display of the FPS and camera status text."""
        self.show_status_text = enable

    def run(self):
        try:
            # Check if sys.stdin is a tty before attempting to get terminal settings
            if os.name != "nt" and sys.stdin.isatty():
                self.old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
                self.has_tty = True
            else:
                self.has_tty = False

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
            sys.stdout.write("\n")
            sys.stdout.write(SET_TITLE.format(title=""))  # Clear title on exit
            sys.stdout.flush()
            # Only restore settings if they were successfully saved
            if os.name != "nt" and self.has_tty:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    def _render_scene(self):
        self.renderer.clear_buffers()

        meshes_to_render = []
        lights_in_scene = []

        # Collect all meshes and lights from the scene graph
        def collect_objects(node: SceneNode):
            # NEW: Check for visibility before adding to render list
            if not node.is_visible:
                return

            if node.mesh is not None:
                meshes_to_render.append(node)
            if node.light is not None:
                lights_in_scene.append(node)

            # Recursively check children's visibility
            for child in node.children:
                collect_objects(child)

        collect_objects(self.root)

        # Render each mesh
        for node in meshes_to_render:
            self.renderer.render_mesh(
                node.mesh,
                self.camera,
                [l.light for l in lights_in_scene],
                model_matrix=node.world_matrix(),
            )

    def _draw_frame(self):
        lines = self.renderer.compose_to_chars()

        # Position cursor at top-left
        sys.stdout.write(CSI + "H")

        # Write the rendered scene
        sys.stdout.write("\n".join(lines))

        # Optionally write status text
        if self.show_status_text:

            total_verts = 0
            total_tris = 0
            num_meshes = 0
            lights_in_scene = []

            def collect_stats(node: SceneNode):
                nonlocal total_verts, total_tris, num_meshes
                if node.mesh:
                    total_verts += len(node.mesh.verts)
                    total_tris += len(node.mesh.faces)
                    num_meshes += 1
                if node.light:
                    lights_in_scene.append(node.light)

            self.root.traverse(collect_stats)

            lights_info = ""
            if lights_in_scene:
                lights_info += "\nLights:\n"
                for i, light in enumerate(lights_in_scene):
                    light_type = "Unknown"
                    props = []

                    if isinstance(light, DirectionalLight):
                        light_type = "Directional"
                        props.append(
                            f"Direction:   ({light.direction.x:.1f}, {light.direction.y:.1f}, {light.direction.z:.1f})"
                        )
                        props.append(
                            f"Color:       RGB({light.color[0]}, {light.color[1]}, {light.color[2]})"
                        )
                        props.append(f"Intensity:   {light.intensity:.1f}")
                    elif isinstance(light, SpotLight):
                        light_type = "Spotlight"
                        props.append(
                            f"Position:    ({light.position.x:.1f}, {light.position.y:.1f}, {light.position.z:.1f})"
                        )
                        props.append(
                            f"Direction:   ({light.direction.x:.1f}, {light.direction.y:.1f}, {light.direction.z:.1f})"
                        )
                        props.append(
                            f"Color:       RGB({light.color[0]}, {light.color[1]}, {light.color[2]})"
                        )
                        props.append(f"Intensity:   {light.intensity:.1f}")
                        props.append(
                            f"Inner Angle: {math.degrees(light.inner_angle):.1f}°"
                        )
                        props.append(
                            f"Outer Angle: {math.degrees(light.outer_angle):.1f}°"
                        )
                    elif isinstance(light, PointLight):
                        light_type = "Point"
                        props.append(
                            f"Position:    ({light.position.x:.1f}, {light.position.y:.1f}, {light.position.z:.1f})"
                        )
                        props.append(
                            f"Color:       RGB({light.color[0]}, {light.color[1]}, {light.color[2]})"
                        )
                        props.append(f"Intensity:   {light.intensity:.1f}")

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
            sys.stdout.write(CSI + "H" + status)

        sys.stdout.flush()

    def _update(self, dt):
        if self._update_function:
            self._update_function(dt)
        for node in self.rotating_nodes:
            node.transform.rot.x = math.fmod(node.transform.rot.x, 2 * math.pi)
            node.transform.rot.y = math.fmod(node.transform.rot.y, 2 * math.pi)
            node.transform.rot.z = math.fmod(node.transform.rot.z, 2 * math.pi)

    def _handle_input(self):
        key = get_key_nonblocking()
        if key:
            if key in ("\x1b", "\x03"):
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
                status_lines = 6  # number of lines in the status text
                if not self.show_status_text:
                    status_lines = 0
                self.resize_engine(
                    current_size.columns, current_size.lines - status_lines
                )
                self.last_terminal_size = current_size
        except Exception:
            pass  # Ignore errors if terminal size can't be retrieved

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
        # Add the cube as a node to the scene graph
        cube_node = self.add_mesh_node(cube_mesh, name="cube")
        self.register_for_rotation(cube_node)

        # Add a directional light
        self.add_light(Vec3(0.5, 0.5, -1), (255, 255, 255), intensity=1.0)

        # Set camera properties
        self.set_camera_position(0, 0, 1.5)
        self.set_camera_fov(60)

        # Set up basic keyboard controls
        self.set_key_binding("w", lambda: self.move_camera(z=0.5))
        self.set_key_binding("s", lambda: self.move_camera(z=-0.5))
        self.set_key_binding("a", lambda: self.rotate_camera(y=0.1))
        self.set_key_binding("d", lambda: self.rotate_camera(y=-0.1))
        self.set_key_binding("q", lambda: self.zoom_camera(-0.5))
        self.set_key_binding("e", lambda: self.zoom_camera(0.5))

        # Run the main loop
        self.run()
