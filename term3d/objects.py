import math
from .vec3lib import Vec3
from .mat4lib import Mat4
from typing import Optional, Callable, List
import uuid

class DirectionalLight:
    """Represents a directional light source with color and intensity."""
    def __init__(self, direction, color, intensity):
        self.direction = direction.norm()
        self.color = color
        self.intensity = intensity

class SpotLight:
    """Represents a spotlight (cone light) with position, direction, and cutoff angles."""
    def __init__(self, position, direction, color, intensity=1.0, inner_angle=15.0, outer_angle=20.0):
        self.position = position          # Vec3
        self.direction = direction.norm() # Vec3
        self.color = color                # (r,g,b)
        self.intensity = intensity
        self.inner_angle = math.radians(inner_angle)
        self.outer_angle = math.radians(outer_angle)

    def cone_factor(self, frag_pos):
        """Return factor 0..1 depending on if frag_pos is inside the cone."""
        L = (frag_pos - self.position).norm()
        cos_theta = self.direction.dot(-L)

        cos_inner = math.cos(self.inner_angle)
        cos_outer = math.cos(self.outer_angle)

        if cos_theta < cos_outer:
            return 0.0
        if cos_theta > cos_inner:
            return 1.0
        # Smooth falloff
        return (cos_theta - cos_outer) / (cos_inner - cos_outer)

    def attenuation(self, frag_pos):
        """Simple distance-based falloff (inverse-square)."""
        dist = (frag_pos - self.position).length()
        # Avoid division by zero
        return 1.0 / (1.0 + 0.1 * dist + 0.02 * (dist * dist))

class PointLight:
    """Represents a point light with position, color, and intensity."""
    def __init__(self, position, color, intensity=1.0):
        self.position = position  # Vec3
        self.color = color        # (r,g,b)
        self.intensity = intensity

    def attenuation(self, frag_pos):
        """Simple distance-based falloff (inverse-square)."""
        dist = (frag_pos - self.position).length()
        # Avoid division by zero
        return 1.0 / (1.0 + 0.1 * dist + 0.02 * (dist * dist))

# Mesh and Scene classes
class Mesh:
    def __init__(self, verts, faces, colors, material='flat'):
        self.verts = verts
        self.faces = faces
        self.vcols = colors
        self.material = material  # 'flat', 'phong', 'wireframe'
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
        self.id = uuid.uuid4()  # Unique ID for each node
        self.name = name
        self.transform = Transform()
        self.mesh = None
        self.light = None
        self.camera = None
        self.children: List['SceneNode'] = []
        self.parent: Optional['SceneNode'] = None
        self.tags: set[str] = set() 
        self.is_visible = True

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
    
    # --- Tagging API ---
    def add_tag(self, *tags: str):
        """Adds one or more tags to the node."""
        for tag in tags:
            self.tags.add(tag)

    def remove_tag(self, *tags: str):
        """Removes one or more tags from the node."""
        for tag in tags:
            self.tags.discard(tag)

    def has_tag(self, tag: str) -> bool:
        """Checks if the node has a specific tag."""
        return tag in self.tags

    def has_any_tag(self, *tags: str) -> bool:
        """Checks if the node has at least one of the given tags."""
        return not self.tags.isdisjoint(tags)

    def has_all_tags(self, *tags: str) -> bool:
        """Checks if the node has all of the given tags."""
        return self.tags.issuperset(tags)



    def set_scale(self, x=1.0, y=1.0, z=1.0):
        self.transform.scale = Vec3(x,y,z)
        return self

    def set_pivot(self, x=0.0, y=0.0, z=0.0):
        """Set the pivot point for rotation and scaling."""
        self.transform.pivot = Vec3(x,y,z)
        return self
    
    def get_parent(self) -> Optional['SceneNode']:
        return self.parent

    def get_children(self) -> List['SceneNode']:
        return self.children

    def get_all_descendants(self) -> List['SceneNode']:
        result = []
        def collect(node):
            for child in node.children:
                result.append(child)
                collect(child)
        collect(self)
        return result

    def find_child_by_name(self, name: str) -> Optional['SceneNode']:
        for child in self.children:
            if child.name == name:
                return child
        return None

    def find_child_by_pattern(self, pattern: str) -> List['SceneNode']:
        import fnmatch
        return [c for c in self.children if fnmatch.fnmatch(c.name, pattern)]
