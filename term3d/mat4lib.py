import math
from .vec3lib import Vec3

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
            # Optimized matrix-matrix multiplication
            res = Mat4()
            a = self.m
            b = other.m
            c = res.m
            for i in range(4):  # Rows of resulting matrix
                for j in range(4):  # Columns of resulting matrix
                    c[j * 4 + i] = (a[i] * b[j * 4] +
                                    a[i + 4] * b[j * 4 + 1] +
                                    a[i + 8] * b[j * 4 + 2] +
                                    a[i + 12] * b[j * 4 + 3])
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