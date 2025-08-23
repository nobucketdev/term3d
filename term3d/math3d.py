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


class Mat4:
    """
    A class for a 4x4 matrix, optimized for performance using a flat 1D list.
    The matrix is stored in column-major order, which is common in graphics APIs
    like OpenGL and is efficient for vector-matrix multiplication.
    """

    def __init__(self):
        # Using a flat list for a 4x4 matrix, totaling 16 elements.
        # Initialized to an identity matrix for convenience.
        self.m = [0.0] * 16
        self.m[0] = self.m[5] = self.m[10] = self.m[15] = 1.0

    @classmethod
    def identity(cls):
        """Creates a 4x4 identity matrix."""
        return cls()

    @classmethod
    def scale(cls, x, y, z):
        """Creates a scale matrix."""
        m = cls()
        m.m[0] = x
        m.m[5] = y
        m.m[10] = z
        return m

    @classmethod
    def translate(cls, x, y, z):
        """Creates a translation matrix."""
        m = cls()
        m.m[12] = x
        m.m[13] = y
        m.m[14] = z
        return m

    @classmethod
    def rotate_x(cls, angle):
        """Creates a rotation matrix around the X-axis."""
        m = cls()
        c, s = math.cos(angle), math.sin(angle)
        m.m[5] = c
        m.m[6] = s
        m.m[9] = -s
        m.m[10] = c
        return m

    @classmethod
    def rotate_y(cls, angle):
        """Creates a rotation matrix around the Y-axis."""
        m = cls()
        c, s = math.cos(angle), math.sin(angle)
        m.m[0] = c
        m.m[2] = -s
        m.m[8] = s
        m.m[10] = c
        return m

    @classmethod
    def rotate_z(cls, angle):
        """Creates a rotation matrix around the Z-axis."""
        m = cls()
        c, s = math.cos(angle), math.sin(angle)
        m.m[0] = c
        m.m[1] = s
        m.m[4] = -s
        m.m[5] = c
        return m

    @classmethod
    def perspective(cls, fov, aspect, znear, zfar):
        """Creates a perspective projection matrix."""
        m = cls()
        f = 1.0 / math.tan(math.radians(fov) / 2.0)
        m.m[0] = f / aspect
        m.m[5] = f
        m.m[10] = (zfar + znear) / (znear - zfar)
        m.m[11] = -1.0
        m.m[14] = (2.0 * zfar * znear) / (znear - zfar)
        m.m[15] = 0.0
        return m

    def __mul__(self, other):
        """Performs matrix-matrix or matrix-vector multiplication."""
        if isinstance(other, Mat4):
            a = self.m
            b = other.m
            c = [0.0] * 16

            # Row 0
            c[0]  = a[0]*b[0]  + a[4]*b[1]  + a[8]*b[2]  + a[12]*b[3]
            c[1]  = a[1]*b[0]  + a[5]*b[1]  + a[9]*b[2]  + a[13]*b[3]
            c[2]  = a[2]*b[0]  + a[6]*b[1]  + a[10]*b[2] + a[14]*b[3]
            c[3]  = a[3]*b[0]  + a[7]*b[1]  + a[11]*b[2] + a[15]*b[3]

            # Row 1
            c[4]  = a[0]*b[4]  + a[4]*b[5]  + a[8]*b[6]  + a[12]*b[7]
            c[5]  = a[1]*b[4]  + a[5]*b[5]  + a[9]*b[6]  + a[13]*b[7]
            c[6]  = a[2]*b[4]  + a[6]*b[5]  + a[10]*b[6] + a[14]*b[7]
            c[7]  = a[3]*b[4]  + a[7]*b[5]  + a[11]*b[6] + a[15]*b[7]

            # Row 2
            c[8]  = a[0]*b[8]  + a[4]*b[9]  + a[8]*b[10] + a[12]*b[11]
            c[9]  = a[1]*b[8]  + a[5]*b[9]  + a[9]*b[10] + a[13]*b[11]
            c[10] = a[2]*b[8]  + a[6]*b[9]  + a[10]*b[10]+ a[14]*b[11]
            c[11] = a[3]*b[8]  + a[7]*b[9]  + a[11]*b[10]+ a[15]*b[11]

            # Row 3
            c[12] = a[0]*b[12] + a[4]*b[13] + a[8]*b[14] + a[12]*b[15]
            c[13] = a[1]*b[12] + a[5]*b[13] + a[9]*b[14] + a[13]*b[15]
            c[14] = a[2]*b[12] + a[6]*b[13] + a[10]*b[14]+ a[14]*b[15]
            c[15] = a[3]*b[12] + a[7]*b[13] + a[11]*b[14]+ a[15]*b[15]

            res = Mat4()
            res.m = c
            return res

        elif isinstance(other, Vec3):
            # Optimized matrix-vector multiplication (assuming column-major)
            x, y, z = other.x, other.y, other.z
            w = 1.0

            # Transform the vector
            vx = x * self.m[0] + y * self.m[4] + z * self.m[8] + w * self.m[12]
            vy = x * self.m[1] + y * self.m[5] + z * self.m[9] + w * self.m[13]
            vz = x * self.m[2] + y * self.m[6] + z * self.m[10] + w * self.m[14]
            vw = x * self.m[3] + y * self.m[7] + z * self.m[11] + w * self.m[15]

            if vw != 0.0:
                return Vec3(vx / vw, vy / vw, vz / vw)
            return Vec3(vx, vy, vz)
