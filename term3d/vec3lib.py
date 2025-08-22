import math


class Vec3:
    """3D vector with full vector algebra support, optimized for pure Python."""

    __slots__ = ("x", "y", "z")
    EPS = 1e-9

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    # --- Arithmetic operators ---
    def __add__(self, o):
        if not isinstance(o, Vec3):
            return NotImplemented
        return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o):
        if not isinstance(o, Vec3):
            return NotImplemented
        return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)

    def __mul__(self, s):
        if isinstance(s, Vec3):
            return Vec3(self.x * s.x, self.y * s.y, self.z * s.z)
        elif isinstance(s, (int, float)):
            return Vec3(self.x * s, self.y * s, self.z * s)
        return NotImplemented

    __rmul__ = __mul__

    def __truediv__(self, s):
        eps = self.EPS
        if isinstance(s, Vec3):
            return Vec3(
                self.x / (s.x if abs(s.x) > eps else eps),
                self.y / (s.y if abs(s.y) > eps else eps),
                self.z / (s.z if abs(s.z) > eps else eps),
            )
        elif isinstance(s, (int, float)):
            s = s if abs(s) > eps else eps
            return Vec3(self.x / s, self.y / s, self.z / s)
        return NotImplemented

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def __eq__(self, o):
        if not isinstance(o, Vec3):
            return False
        tol = 1e-9
        dx = self.x - o.x
        dy = self.y - o.y
        dz = self.z - o.z
        return abs(dx) <= tol and abs(dy) <= tol and abs(dz) <= tol

    def __hash__(self):
        return hash((round(self.x, 9), round(self.y, 9), round(self.z, 9)))

    # --- Vector algebra ---
    def dot(self, o):
        return self.x * o.x + self.y * o.y + self.z * o.z

    def cross(self, o):
        x = self.y * o.z - self.z * o.y
        y = self.z * o.x - self.x * o.z
        z = self.x * o.y - self.y * o.x
        return Vec3(x, y, z)

    def hadamard(self, o):
        return Vec3(self.x * o.x, self.y * o.y, self.z * o.z)

    # --- Magnitude & normalization ---
    def length_sq(self):
        x, y, z = self.x, self.y, self.z
        return x * x + y * y + z * z

    def length(self):
        return math.sqrt(self.length_sq()) or self.EPS

    def norm(self):
        l_sq = self.x * self.x + self.y * self.y + self.z * self.z
        if l_sq < 1e-9:
            return Vec3(0.0, 0.0, 0.0)
        inv = 1.0 / math.sqrt(l_sq)
        return Vec3(self.x * inv, self.y * inv, self.z * inv)

    # --- Distance & angles ---
    def distance(self, o):
        dx = self.x - o.x
        dy = self.y - o.y
        dz = self.z - o.z
        return math.sqrt(dx * dx + dy * dy + dz * dz) or self.EPS

    def angle_with(self, o):
        lx = self.length()
        lo = o.length()
        denom = lx * lo
        if denom < self.EPS:
            return 0.0
        val = self.dot(o) / denom
        return math.acos(max(-1.0, min(1.0, val)))

    # --- Projection & reflection ---
    def project_on(self, o):
        o_len_sq = o.length_sq()
        if o_len_sq < self.EPS:
            return Vec3(0, 0, 0)
        scale = self.dot(o) / o_len_sq
        return Vec3(o.x * scale, o.y * scale, o.z * scale)

    def reject_from(self, o):
        return self - self.project_on(o)

    def reflect(self, normal):
        d = 2 * self.dot(normal)
        return Vec3(self.x - normal.x * d, self.y - normal.y * d, self.z - normal.z * d)

    # --- Triple products ---
    def scalar_triple(self, b, c):
        return self.dot(b.cross(c))

    def vector_triple(self, b, c):
        db = self.dot(b)
        dc = self.dot(c)
        return Vec3(b.x * dc - c.x * db, b.y * dc - c.y * db, b.z * dc - c.z * db)

    # --- Interpolation ---
    def lerp(self, o, t):
        return Vec3(
            self.x + (o.x - self.x) * t,
            self.y + (o.y - self.y) * t,
            self.z + (o.z - self.z) * t,
        )

    # --- Conversion ---
    def to_tuple(self):
        return (self.x, self.y, self.z)

    def to_list(self):
        return [self.x, self.y, self.z]

    # --- Representation ---
    def __repr__(self):
        return f"Vec3({self.x:.6f}, {self.y:.6f}, {self.z:.6f})"

    def __str__(self):
        return f"({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"

    # --- In-place operators for tight loops ---
    def iadd(self, o):
        self.x += o.x
        self.y += o.y
        self.z += o.z
        return self

    def isub(self, o):
        self.x -= o.x
        self.y -= o.y
        self.z -= o.z
        return self

    def imul(self, s):
        if isinstance(s, Vec3):
            self.x *= s.x
            self.y *= s.y
            self.z *= s.z
        else:
            self.x *= s
            self.y *= s
            self.z *= s
        return self

    def idiv(self, s):
        eps = self.EPS
        if isinstance(s, Vec3):
            self.x /= s.x if abs(s.x) > eps else eps
            self.y /= s.y if abs(s.y) > eps else eps
            self.z /= s.z if abs(s.z) > eps else eps
        else:
            s = s if abs(s) > eps else eps
            self.x /= s
            self.y /= s
            self.z /= s
        return self
