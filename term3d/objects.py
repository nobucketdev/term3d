import math
import uuid
from typing import Callable, List, Optional

from .math3d import Mat4, Vec3


class DirectionalLight:
    """Represents a directional light source with color and intensity."""

    def __init__(self, direction, color, intensity):
        self.direction = direction.norm()
        self.color = color
        self.intensity = intensity


class SpotLight:
    """Represents a spotlight (cone light) with position, direction, and cutoff angles."""

    def __init__(
        self,
        position,
        direction,
        color,
        intensity=1.0,
        inner_angle=15.0,
        outer_angle=20.0,
    ):
        self.position = position  # Vec3
        self.direction = direction.norm()  # Vec3
        self.color = color  # (r,g,b)
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
        self.color = color  # (r,g,b)
        self.intensity = intensity

    def attenuation(self, frag_pos):
        """Simple distance-based falloff (inverse-square)."""
        dist = (frag_pos - self.position).length()
        # Avoid division by zero
        return 1.0 / (1.0 + 0.1 * dist + 0.02 * (dist * dist))


# Mesh and Scene classes
class Mesh:

    def __init__(self, verts, faces, colors, material="flat"):
        self.verts = verts
        self.faces = faces
        self.vcols = colors
        self.material = material  # 'flat', 'phong', 'wireframe'
        self.pos = Vec3(0, 0, 0)
        self.rot = Vec3(0, 0, 0)
        self.scale = Vec3(1, 1, 1)
        # Optional attributes, but should be included for slots if they might be set.
        self.min_v = None
        self.max_v = None

    def move(self, x=0, y=0, z=0):
        self.pos.x += x
        self.pos.y += y
        self.pos.z += z

    def rotate(self, x=0, y=0, z=0):
        self.rot.x += x
        self.rot.y += y
        self.rot.z += z

    def calculate_bounds(self):
        """
        Calculates the axis-aligned bounding box (AABB) for the mesh.
        ✅ Optimized
        """
        if not self.verts:
            return

        first = self.verts[0]
        min_x = max_x = first.x
        min_y = max_y = first.y
        min_z = max_z = first.z

        for v in self.verts[1:]:
            x, y, z = v.x, v.y, v.z
            if x < min_x:
                min_x = x
            elif x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            elif y > max_y:
                max_y = y
            if z < min_z:
                min_z = z
            elif z > max_z:
                max_z = z

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
        self.rot = Vec3(0, 0, 0)  # Pitch, Yaw, Roll


class Transform:
    def __init__(
        self,
        pos: Optional[Vec3] = None,
        rot: Optional[Vec3] = None,
        scale: Optional[Vec3] = None,
        pivot: Optional[Vec3] = None,
    ):
        self.pos = pos if pos else Vec3(0, 0, 0)
        self.rot = rot if rot else Vec3(0, 0, 0)
        self.scale = scale if scale else Vec3(1, 1, 1)
        self.pivot = pivot if pivot else Vec3(0, 0, 0)

    def to_matrix(self) -> Mat4:
        sx, sy, sz = self.scale.x, self.scale.y, self.scale.z
        px, py, pz = self.pivot.x, self.pivot.y, self.pivot.z
        tx, ty, tz = self.pos.x, self.pos.y, self.pos.z
        rx, ry, rz = self.rot.x, self.rot.y, self.rot.z

        # Precompute sine/cosine for rotation
        cx, sx_ = math.cos(rx), math.sin(rx)
        cy, sy_ = math.cos(ry), math.sin(ry)
        cz, sz_ = math.cos(rz), math.sin(rz)

        # Combined rotation * scale
        m = Mat4()
        m.m[0] = (cy * cz) * sx
        m.m[1] = (cy * sz_) * sx
        m.m[2] = -sy_ * sx
        m.m[3] = 0.0

        m.m[4] = (sx_ * sy_ * cz - cx * sz_) * sy
        m.m[5] = (sx_ * sy_ * sz_ + cx * cz) * sy
        m.m[6] = (sx_ * cy) * sy
        m.m[7] = 0.0

        m.m[8] = (cx * sy_ * cz + sx_ * sz_) * sz
        m.m[9] = (cx * sy_ * sz_ - sx_ * cz) * sz
        m.m[10] = (cx * cy) * sz
        m.m[11] = 0.0

        # Translation including pivot
        m.m[12] = tx + px - (m.m[0]*px + m.m[4]*py + m.m[8]*pz)
        m.m[13] = ty + py - (m.m[1]*px + m.m[5]*py + m.m[9]*pz)
        m.m[14] = tz + pz - (m.m[2]*px + m.m[6]*py + m.m[10]*pz)
        m.m[15] = 1.0

        return m

class SceneNode:

    def __init__(self, name: str = "node"):
        self.id = uuid.uuid4()  # Unique ID for each node
        self.name = name
        self.transform = Transform()
        self.mesh = None
        self.light = None
        self.camera = None
        self.children: List["SceneNode"] = []
        self.parent: Optional["SceneNode"] = None
        self.tags: set[str] = set()
        self.is_visible = True

    # --- Hierarchy ---
    def add(self, child: "SceneNode") -> "SceneNode":
        if child.parent is not None:
            child.parent.remove(child)
        child.parent = self
        self.children.append(child)
        return child

    def remove(self, child: "SceneNode") -> None:
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
    def traverse(self, fn: Callable[["SceneNode"], None]) -> None:
        fn(self)
        for c in self.children:
            c.traverse(fn)

    # --- Convenience ---
    def set_pos(self, x=0.0, y=0.0, z=0.0):
        self.transform.pos = Vec3(x, y, z)
        return self

    def set_rot(self, x=0.0, y=0.0, z=0.0):
        self.transform.rot = Vec3(x, y, z)
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
        self.transform.scale = Vec3(x, y, z)
        return self

    def set_pivot(self, x=0.0, y=0.0, z=0.0):
        """Set the pivot point for rotation and scaling."""
        self.transform.pivot = Vec3(x, y, z)
        return self

    def get_parent(self) -> Optional["SceneNode"]:
        return self.parent

    def get_children(self) -> List["SceneNode"]:
        return self.children

    def get_all_descendants(self) -> List["SceneNode"]:
        result = []

        def collect(node):
            for child in node.children:
                result.append(child)
                collect(child)

        collect(self)
        return result

    def find_child_by_name(self, name: str) -> Optional["SceneNode"]:
        for child in self.children:
            if child.name == name:
                return child
        return None

    def find_child_by_pattern(self, pattern: str) -> List["SceneNode"]:
        import fnmatch

        return [c for c in self.children if fnmatch.fnmatch(c.name, pattern)]
