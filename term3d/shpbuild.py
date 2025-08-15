import math
from .vec3lib import Vec3

# Clamp helper
def clamp(v, a, b): return a if v < a else (b if v > b else v)

class Mesh:
    """Represents a 3D object with vertices, faces, and vertex colors."""
    def __init__(self, verts, faces, colors):
        self.verts = verts
        self.faces = faces
        self.vcols = colors
        self.pos = Vec3(0, 0, 0)
        self.rot = Vec3(0, 0, 0)
        self.scale = Vec3(1, 1, 1)
        self.min_v = Vec3(0, 0, 0)
        self.max_v = Vec3(0, 0, 0)
        self.calculate_bounds()

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
        
        


# Simple mesh (cube) generator for example
def build_cube(size=1.0, color=None):
    """Generates a cube mesh. Accepts an optional custom color."""
    s = size/2.0
    verts = [
        Vec3(-s,-s,-s), Vec3(s,-s,-s), Vec3(s,s,-s), Vec3(-s,s,-s),
        Vec3(-s,-s,s),  Vec3(s,-s,s),  Vec3(s,s,s),  Vec3(-s,s,s)
    ]
    # Faces as triangles (v0,v1,v2)
    faces = [
        (0,1,2),(0,2,3), # back
        (4,6,5),(4,7,6), # front
        (0,4,5),(0,5,1), # bottom
        (3,2,6),(3,6,7), # top
        (1,5,6),(1,6,2), # right
        (0,3,7),(0,7,4)  # left
    ]
    
    # Assign vertex colors based on whether a custom color is provided
    if color:
        vcols = [color] * len(verts)
    else:
        vcols = [
            (255, 179, 186), (255, 223, 186), (255, 255, 186), (186, 255, 201),
            (186, 225, 255), (223, 186, 255), (255, 186, 255), (186, 255, 255)
        ]
        
    return Mesh(verts, faces, vcols)

def build_uv_sphere(radius=1.0, segments_x=20, segments_y=10, color=None):
    """Generates a sphere mesh with a given radius and subdivisions. Accepts an optional custom color."""
    verts = []
    faces = []
    vcols = []

    # Generate vertices
    for y in range(segments_y + 1):
        phi = y * math.pi / segments_y
        for x in range(segments_x + 1):
            theta = x * 2 * math.pi / segments_x
            sx = math.cos(theta) * math.sin(phi)
            sy = math.sin(theta) * math.sin(phi)
            sz = math.cos(phi)
            verts.append(Vec3(radius * sx, radius * sy, radius * sz))
            # Set vertex colors
            if not color:
                vcols.append((
                    int(255 * (sx + 1) / 2),
                    int(255 * (sy + 1) / 2),
                    int(255 * (sz + 1) / 2)
                ))

    # Generate faces
    for y in range(segments_y):
        for x in range(segments_x):
            i0 = y * (segments_x + 1) + x
            i1 = i0 + 1
            i2 = (y + 1) * (segments_x + 1) + x
            i3 = i2 + 1
            
            # Quads are split into two triangles
            faces.append((i0, i2, i1))
            faces.append((i1, i2, i3))

    if color:
        vcols = [color] * len(verts)

    return Mesh(verts, faces, vcols)

def build_icosphere(radius=1.0, subdivisions=2, color=None):
    """
    Generates an icosphere mesh.
    Starts with a base icosahedron and refines it by subdividing each triangle. Accepts an optional custom color.
    """
    verts = []
    faces = []
    
    # Golden ratio
    t = (1.0 + math.sqrt(5.0)) / 2.0
    
    # Vertices of a base icosahedron
    verts.append(Vec3(-1,  t,  0).norm())
    verts.append(Vec3( 1,  t,  0).norm())
    verts.append(Vec3(-1, -t,  0).norm())
    verts.append(Vec3( 1, -t,  0).norm())

    verts.append(Vec3( 0, -1,  t).norm())
    verts.append(Vec3( 0,  1,  t).norm())
    verts.append(Vec3( 0, -1, -t).norm())
    verts.append(Vec3( 0,  1, -t).norm())

    verts.append(Vec3( t,  0, -1).norm())
    verts.append(Vec3( t,  0,  1).norm())
    verts.append(Vec3(-t,  0, -1).norm())
    verts.append(Vec3(-t,  0,  1).norm())

    
    # 20 faces of the icosahedron
    faces_base = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
    ]
    
    faces = list(faces_base)
    
    # Subdivision loop
    midpoint_cache = {}
    
    def get_midpoint(p1_idx, p2_idx):
        nonlocal midpoint_cache, verts
        
        # Ensure consistent key order for the cache
        key = tuple(sorted((p1_idx, p2_idx)))
        if key in midpoint_cache:
            return midpoint_cache[key]
        
        p1 = verts[p1_idx]
        p2 = verts[p2_idx]
        mid = (p1 + p2).norm()
        verts.append(mid)
        mid_idx = len(verts) - 1
        midpoint_cache[key] = mid_idx
        return mid_idx
    
    for i in range(subdivisions):
        new_faces = []
        for f in faces:
            v1, v2, v3 = f
            
            a = get_midpoint(v1, v2)
            b = get_midpoint(v2, v3)
            c = get_midpoint(v3, v1)
            
            new_faces.append((v1, a, c))
            new_faces.append((v2, b, a))
            new_faces.append((v3, c, b))
            new_faces.append((a, b, c))
        faces = new_faces
        
    # Apply radius and color
    vcols = []
    for v in verts:
        verts[verts.index(v)] = Vec3(v.x * radius, v.y * radius, v.z * radius)
        if color:
            vcols.append(color)
        else:
            vcols.append((
                int(255 * (v.x + 1) / 2),
                int(255 * (v.y + 1) / 2),
                int(255 * (v.z + 1) / 2)
            ))

    return Mesh(verts, faces, vcols)

def build_torus(R=2.0, r=0.7, segments_R=40, segments_r=20, color=None):
    """Generates a torus mesh (donut) with major radius R and minor radius r. Accepts an optional custom color."""
    verts, faces, vcols = [], [], []
    for i in range(segments_R):
        theta = 2 * math.pi * i / segments_R
        cos_theta, sin_theta = math.cos(theta), math.sin(theta)
        for j in range(segments_r):
            phi = 2 * math.pi * j / segments_r
            cos_phi, sin_phi = math.cos(phi), math.sin(phi)
            x = (R + r * cos_phi) * cos_theta
            y = (R + r * cos_phi) * sin_theta
            z = r * sin_phi
            verts.append(Vec3(x, y, z))
            if not color:
                vcols.append((
                    int(127 + 127 * cos_phi),
                    int(127 + 127 * sin_theta),
                    int(127 + 127 * sin_phi)
                ))
    if color:
        vcols = [color] * len(verts)

    for i in range(segments_R):
        for j in range(segments_r):
            i0 = i * segments_r + j
            i1 = i * segments_r + (j + 1) % segments_r
            i2 = ((i + 1) % segments_R) * segments_r + j
            i3 = ((i + 1) % segments_R) * segments_r + (j + 1) % segments_r
            faces.append((i0, i2, i1))
            faces.append((i1, i2, i3))
    return Mesh(verts, faces, vcols)

def build_plane(width=1.0, depth=1.0, segments_x=1, segments_z=1, color=None):
    """Generates a flat grid plane along XZ axis. Accepts an optional custom color."""
    verts, faces, vcols = [], [], []
    for z in range(segments_z + 1):
        for x in range(segments_x + 1):
            px = (x / segments_x - 0.5) * width
            pz = (z / segments_z - 0.5) * depth
            verts.append(Vec3(px, 0, pz))
            if not color:
                vcols.append((200, 200, 200))

    if color:
        vcols = [color] * len(verts)

    for z in range(segments_z):
        for x in range(segments_x):
            i0 = z * (segments_x + 1) + x
            i1 = i0 + 1
            i2 = i0 + (segments_x + 1)
            i3 = i2 + 1
            faces.append((i0, i2, i1))
            faces.append((i1, i2, i3))
    return Mesh(verts, faces, vcols)

def build_cylinder(radius=1.0, height=2.0, segments=20, color=None):
    """Generates a vertical cylinder mesh. Accepts an optional custom color."""
    verts, faces, vcols = [], [], []
    half_h = height / 2.0

    # Side vertices
    for y in (-half_h, half_h):
        for i in range(segments):
            theta = 2 * math.pi * i / segments
            x, z = radius * math.cos(theta), radius * math.sin(theta)
            verts.append(Vec3(x, y, z))
            if not color:
                vcols.append((int(127 + 127 * math.cos(theta)),
                              int(127 + 127 * math.sin(theta)), 200))

    # Top/bottom center vertices
    top_center = len(verts)
    verts.append(Vec3(0, half_h, 0))
    if not color:
        vcols.append((255, 255, 255))
    
    bottom_center = len(verts)
    verts.append(Vec3(0, -half_h, 0))
    if not color:
        vcols.append((200, 200, 200))

    if color:
        vcols = [color] * len(verts)

    # Side faces
    for i in range(segments):
        i0 = i
        i1 = (i + 1) % segments
        i2 = segments + i
        i3 = segments + ((i + 1) % segments)
        faces.append((i0, i2, i1))
        faces.append((i1, i2, i3))

    # Top faces
    for i in range(segments):
        i0 = segments + i
        i1 = segments + ((i + 1) % segments)
        faces.append((top_center, i0, i1))

    # Bottom faces
    for i in range(segments):
        i0 = (i + 1) % segments
        i1 = i
        faces.append((bottom_center, i0, i1))

    return Mesh(verts, faces, vcols)

def build_cone(radius=1.0, height=2.0, segments=20, color=None):
    """Generates a vertical cone mesh. Accepts an optional custom color."""
    verts, faces, vcols = [], [], []
    half_h = height / 2.0

    # Base vertices
    for i in range(segments):
        theta = 2 * math.pi * i / segments
        x, z = radius * math.cos(theta), radius * math.sin(theta)
        verts.append(Vec3(x, -half_h, z))
        if not color:
            vcols.append((int(127 + 127 * math.cos(theta)),
                          int(127 + 127 * math.sin(theta)), 200))

    # Apex vertex
    apex = len(verts)
    verts.append(Vec3(0, half_h, 0))
    if not color:
        vcols.append((255, 255, 255))

    # Base center
    base_center = len(verts)
    verts.append(Vec3(0, -half_h, 0))
    if not color:
        vcols.append((200, 200, 200))

    if color:
        vcols = [color] * len(verts)

    # Side faces
    for i in range(segments):
        i0 = i
        i1 = (i + 1) % segments
        faces.append((i0, apex, i1))

    # Base faces
    for i in range(segments):
        i0 = (i + 1) % segments
        i1 = i
        faces.append((base_center, i0, i1))

    return Mesh(verts, faces, vcols)

def build_pyramid(base=1.0, height=1.0, color=None):
    """Generates a square pyramid. Accepts an optional custom color."""
    s = base / 2.0
    verts = [
        Vec3(-s, 0, -s), Vec3(s, 0, -s),
        Vec3(s, 0, s), Vec3(-s, 0, s),
        Vec3(0, height, 0)
    ]
    if color:
        vcols = [color] * len(verts)
    else:
        vcols = [(200, 200, 200), (200, 200, 200), (200, 200, 200), (200, 200, 200), (255, 255, 255)]

    faces = [
        (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4),  # sides
        (0, 3, 2), (0, 2, 1)  # base
    ]
    return Mesh(verts, faces, vcols)


def build_mobius_strip(radius=1.0, width=0.3, segments=100, color=None):
    """Generates a mobius strip. Accepts an optional custom color."""
    verts, faces, vcols = [], [], []
    for i in range(segments + 1):
        t = 2 * math.pi * i / segments
        for j in [-width/2, width/2]:
            # Möbius parametric coords
            x = (radius + j * math.cos(t / 2)) * math.cos(t)
            y = (radius + j * math.cos(t / 2)) * math.sin(t)
            z = j * math.sin(t / 2)
            verts.append(Vec3(x, y, z))
            # Color gradient based on position
            if not color:
                vcols.append((int(127 + 128 * math.cos(t)), int(127 + 128 * math.sin(t)), int(255 * (j + width/2)/width)))

    if color:
        vcols = [color] * len(verts)

    for i in range(segments):
        idx = i * 2
        faces.append((idx, idx + 1, idx + 3))
        faces.append((idx, idx + 3, idx + 2))
    return Mesh(verts, faces, vcols)

def build_klein_bottle(segments_u=50, segments_v=20, scale=1.0, color=None):
    """Generates a Klein bottle mesh. Accepts an optional custom color."""
    verts, faces, vcols = [], [], []
    for i in range(segments_u + 1):
        u = 2 * math.pi * i / segments_u
        for j in range(segments_v + 1):
            v = 2 * math.pi * j / segments_v
            # Parametric equations for Klein bottle
            if u < math.pi:
                x = 3 * math.cos(u) * (1 + math.sin(u)) + scale * (2 * (1 - math.cos(u) / 2)) * math.cos(v)
                y = 8 * math.sin(u) + scale * (2 * (1 - math.cos(u) / 2)) * math.sin(v)
            else:
                x = 3 * math.cos(u) * (1 + math.sin(u)) + scale * math.cos(v + math.pi)
                y = 8 * math.sin(u)
            z = scale * math.sin(u) + 2 * (1 - math.cos(u) / 2) * math.sin(v) if u < math.pi else scale * math.sin(v)
            verts.append(Vec3(x * 0.1, y * 0.1, z * 0.1))
            # Simple coloring
            if not color:
                c = int(255 * i / segments_u)
                vcols.append((c, 128, 255 - c))

    if color:
        vcols = [color] * len(verts)

    for i in range(segments_u):
        for j in range(segments_v):
            i0 = i * (segments_v + 1) + j
            i1 = i0 + 1
            i2 = (i + 1) * (segments_v + 1) + j
            i3 = i2 + 1
            faces.append((i0, i2, i1))
            faces.append((i1, i2, i3))
    return Mesh(verts, faces, vcols)

def build_heart(scale=1.0, segments=50, color=None):
    """Generates a heart shape mesh. Accepts an optional custom color."""
    verts, faces, vcols = [], [], []
    for i in range(segments + 1):
        t = math.pi * i / segments
        for j in range(segments + 1):
            p = 2 * math.pi * j / segments
            x = scale * 16 * (math.sin(t) ** 3) * math.cos(p)
            y = scale * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            z = scale * 16 * (math.sin(t) ** 3) * math.sin(p)
            verts.append(Vec3(x * 0.02, y * 0.02, z * 0.02))
            if not color:
                vcols.append((255, int(100 + 155 * i / segments), int(100 + 155 * j / segments)))

    if color:
        vcols = [color] * len(verts)

    for i in range(segments):
        for j in range(segments):
            i0 = i * (segments + 1) + j
            i1 = i0 + 1
            i2 = (i + 1) * (segments + 1) + j
            i3 = i2 + 1
            faces.append((i0, i2, i1))
            faces.append((i1, i2, i3))
    return Mesh(verts, faces, vcols)

def build_dinis_surface(a=1.0, b=0.2, segments=50, color=None):
    """Generates a Dini's surface mesh. Accepts an optional custom color."""
    verts, faces, vcols = [], [], []
    scale = 0.5
    for i in range(segments + 1):
        u = 2 * math.pi * i / segments
        for j in range(segments + 1):
            # Restrict v to a positive tangent domain, e.g., from a small epsilon to pi
            v = 0.01 + (math.pi - 0.02) * j / segments  
            # Parametric equations for Dini's surface
            x = scale * a * math.cos(u) * math.sin(v)
            y = scale * a * math.sin(u) * math.sin(v)
            z = scale * (a * (math.cos(v) + math.log(math.tan(v / 2))) + b * u)
            
            verts.append(Vec3(x, y, z))
            if not color:
                vcols.append((int(255 * i / segments), 150, int(255 * j / segments)))

    if color:
        vcols = [color] * len(verts)

    for i in range(segments):
        for j in range(segments):
            i0 = i * (segments + 1) + j
            i1 = i0 + 1
            i2 = (i + 1) * (segments + 1) + j
            i3 = i2 + 1
            faces.append((i0, i2, i1))
            faces.append((i1, i2, i3))
            
    return Mesh(verts, faces, vcols)

def build_conical_helix(radius=1.0, height=3.0, turns=5, segments=100, color=None):
    """Generates a conical helix mesh. Accepts an optional custom color."""
    verts, faces, vcols = [], [], []
    scale = 0.5
    for i in range(segments + 1):
        t = 2 * math.pi * turns * i / segments
        r = scale * radius * (1 - i / segments) 
        
        x = r * math.cos(t)
        y = r * math.sin(t)
        z = scale * height * (i / segments)
        
        verts.append(Vec3(x, y, z))
        if not color:
            vcols.append((255, int(255 * i / segments), 0))
    
    verts_b, faces_b = [], []
    for i in range(segments + 1):
        t = 2 * math.pi * turns * i / segments
        r = scale * radius * (1 - i / segments)
        
        x = r * math.cos(t)
        y = r * math.sin(t)
        z = scale * height * (i / segments)
        
        offset_x = 0.1 * math.cos(t + math.pi / 2)
        offset_y = 0.1 * math.sin(t + math.pi / 2)
        
        verts_b.append(Vec3(x + offset_x, y + offset_y, z))
        
    for i in range(segments):
        i0 = i
        i1 = i + 1
        i2 = i + segments + 1
        i3 = i2 + 1
        faces.append((i0, i2, i1))
        faces.append((i1, i2, i3))

    all_verts = verts + verts_b
    if color:
        all_vcols = [color] * len(all_verts)
    else:
        all_vcols = vcols + [(255, int(255 * i / segments), 0) for i in range(segments + 1)]
    
    final_faces = []
    for i in range(segments):
        final_faces.append((i, i + segments + 1, i + 1))
        final_faces.append((i + 1, i + segments + 1, i + segments + 2))
    
    return Mesh(all_verts, final_faces, all_vcols)

def build_catenoid(u_range=(-1, 1), v_range=(-math.pi, math.pi), segments_u=20, segments_v=50, color=None):
    """Generates a catenoid mesh. Accepts an optional custom color."""
    verts, faces, vcols = [], [], []
    scale = 2.0
    for i in range(segments_u + 1):
        u = u_range[0] + (u_range[1] - u_range[0]) * i / segments_u
        for j in range(segments_v + 1):
            v = v_range[0] + (v_range[1] - v_range[0]) * j / segments_v
            x = scale * math.cosh(u) * math.cos(v)
            y = scale * math.cosh(u) * math.sin(v)
            z = scale * u
            
            verts.append(Vec3(x * 0.5, y * 0.5, z * 0.5))
            if not color:
                vcols.append((int(127 + 128 * math.cos(v)), int(127 + 128 * math.sin(v)), 255))

    if color:
        vcols = [color] * len(verts)

    for i in range(segments_u):
        for j in range(segments_v):
            i0 = i * (segments_v + 1) + j
            i1 = i0 + 1
            i2 = (i + 1) * (segments_v + 1) + j
            i3 = i2 + 1
            faces.append((i0, i2, i1))
            faces.append((i1, i2, i3))

    return Mesh(verts, faces, vcols)


def build_capsule(radius=0.5, height=2.0, segments=30, color=None):
    """
    Generates a capsule mesh by combining a cylinder and two hemispheres.
    This corrected version builds a single, seamless mesh.
    Accepts an optional custom color.
    """
    verts, faces, vcols = [], [], []

    half_height = height / 2.0
    num_verts_per_ring = segments
    num_lat = segments // 2

    # Step 1: Create vertices for the cylindrical body
    # This also forms the base rings for the hemispheres
    for i in range(num_verts_per_ring):
        angle = 2 * math.pi * i / num_verts_per_ring
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        # Bottom ring
        verts.append(Vec3(x, y, -half_height))
        # Top ring
        verts.append(Vec3(x, y, half_height))

    # Step 2: Create vertices for the bottom hemisphere's pole and rings
    v_offset_bottom = len(verts)
    verts.append(Vec3(0, 0, -half_height - radius))  # Bottom pole
    for i in range(1, num_lat + 1):
        lat = (math.pi / 2.0) * i / num_lat
        for j in range(num_verts_per_ring):
            lon = 2 * math.pi * j / num_verts_per_ring
            x = radius * math.sin(lat) * math.cos(lon)
            y = radius * math.sin(lat) * math.sin(lon)
            z = radius * math.cos(lat)
            verts.append(Vec3(x, y, -half_height - z))
            
    # Step 3: Create vertices for the top hemisphere's pole and rings
    v_offset_top = len(verts)
    verts.append(Vec3(0, 0, half_height + radius))  # Top pole
    for i in range(1, num_lat + 1):
        lat = (math.pi / 2.0) * i / num_lat
        for j in range(num_verts_per_ring):
            lon = 2 * math.pi * j / num_verts_per_ring
            x = radius * math.sin(lat) * math.cos(lon)
            y = radius * math.sin(lat) * math.sin(lon)
            z = radius * math.cos(lat)
            verts.append(Vec3(x, y, half_height + z))
            
    # Step 4: Generate faces for all parts
    # Faces for the cylindrical part
    for i in range(num_verts_per_ring):
        i0 = i * 2
        i1 = ((i + 1) % num_verts_per_ring) * 2
        i2 = i * 2 + 1
        i3 = ((i + 1) % num_verts_per_ring) * 2 + 1
        faces.append((i0, i1, i3))
        faces.append((i0, i3, i2))
    
    # Faces for the bottom hemisphere
    pole_idx_bottom = v_offset_bottom
    ring_start_idx_bottom = pole_idx_bottom + 1
    
    # Connect cylinder's bottom ring to the hemisphere's first ring
    for j in range(num_verts_per_ring):
        i0 = j * 2
        i1 = ((j + 1) % num_verts_per_ring) * 2
        i2 = ring_start_idx_bottom + j
        i3 = ring_start_idx_bottom + ((j + 1) % num_verts_per_ring)
        faces.append((i0, i1, i3))
        faces.append((i0, i3, i2))

    # Connect the remaining rings of the bottom hemisphere
    for i in range(num_lat - 1):
        for j in range(num_verts_per_ring):
            i0 = ring_start_idx_bottom + i * num_verts_per_ring + j
            i1 = ring_start_idx_bottom + i * num_verts_per_ring + ((j + 1) % num_verts_per_ring)
            i2 = ring_start_idx_bottom + (i + 1) * num_verts_per_ring + j
            i3 = ring_start_idx_bottom + (i + 1) * num_verts_per_ring + ((j + 1) % num_verts_per_ring)
            faces.append((i0, i1, i3))
            faces.append((i0, i3, i2))

    # Connect the final ring to the bottom pole
    final_ring_start_bottom = ring_start_idx_bottom + (num_lat - 1) * num_verts_per_ring
    for j in range(num_verts_per_ring):
        i0 = final_ring_start_bottom + j
        i1 = final_ring_start_bottom + ((j + 1) % num_verts_per_ring)
        faces.append((pole_idx_bottom, i1, i0))  # Reverse winding

    # Faces for the top hemisphere
    pole_idx_top = v_offset_top
    ring_start_idx_top = pole_idx_top + 1

    # Connect cylinder's top ring to the hemisphere's first ring
    for j in range(num_verts_per_ring):
        i0 = j * 2 + 1
        i1 = ((j + 1) % num_verts_per_ring) * 2 + 1
        i2 = ring_start_idx_top + j
        i3 = ring_start_idx_top + ((j + 1) % num_verts_per_ring)
        faces.append((i0, i2, i1))
        faces.append((i1, i2, i3))

    # Connect the remaining rings of the top hemisphere
    for i in range(num_lat - 1):
        for j in range(num_verts_per_ring):
            i0 = ring_start_idx_top + i * num_verts_per_ring + j
            i1 = ring_start_idx_top + i * num_verts_per_ring + ((j + 1) % num_verts_per_ring)
            i2 = ring_start_idx_top + (i + 1) * num_verts_per_ring + j
            i3 = ring_start_idx_top + (i + 1) * num_verts_per_ring + ((j + 1) % num_verts_per_ring)
            faces.append((i0, i2, i1))
            faces.append((i1, i2, i3))
    
    # Connect the final ring to the top pole
    final_ring_start_top = ring_start_idx_top + (num_lat - 1) * num_verts_per_ring
    for j in range(num_verts_per_ring):
        i0 = final_ring_start_top + j
        i1 = final_ring_start_top + ((j + 1) % num_verts_per_ring)
        faces.append((pole_idx_top, i0, i1))

    # Step 5: Assign colors
    if color:
        vcols = [color] * len(verts)
    else:
        # Generate default colors based on position
        for i in range(len(verts)):
            vcols.append((int(127 + 127 * (verts[i].x / radius)),
                          int(127 + 127 * (verts[i].y / radius)),
                          int(127 + 127 * (verts[i].z / (half_height + radius)))))
            
    return Mesh(verts, faces, vcols)