from .vec3lib import Vec3

class Mesh:
    """Represents a 3D object with vertices, faces, and vertex colors."""
    def __init__(self, verts, faces, colors, material='flat'):
        self.verts = verts
        self.faces = faces
        self.vcols = colors
        self.material = material  # 'flat', 'phong', 'wireframe'
        self.pos = Vec3(0, 0, 0)
        self.rot = Vec3(0, 0, 0)
        self.scale = Vec3(1, 1, 1)
        self.min_v = Vec3(0, 0, 0)
        self.max_v = Vec3(0, 0, 0)
        self.calculate_bounds()

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
        
# New Light class to hold light properties
class Light:
    """Represents a directional light source with color and intensity."""
    def __init__(self, direction, color, intensity):
        self.direction = direction.norm()
        self.color = color
        self.intensity = intensity

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
