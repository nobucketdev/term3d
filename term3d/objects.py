import math
from .vec3lib import Vec3
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
