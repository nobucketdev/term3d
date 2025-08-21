from .mat4lib import Mat4
from .vec3lib import Vec3
from .utils import *
from typing import List, Tuple
from .objects import DirectionalLight, SpotLight, PointLight

# A constant for color normalization, making the code's intent clearer.
COLOR_SCALE = 1.0 / 255.0

def edge_coeffs(x0: float, y0: float, x1: float, y1: float) -> Tuple[float, float, float]:
    """
    Calculates the coefficients A, B, and C for a 2D line equation (Ax + By + C = 0)
    that passes through two given points (x0, y0) and (x1, y1).
    These coefficients are used for the barycentric coordinate calculation in rasterization.
    """
    A = y0 - y1
    B = x1 - x0
    C = x0 * y1 - y0 * x1
    return A, B, C

class Renderer:
    """
    Handles all 3D rendering and 2D rasterization logic for a terminal-based renderer.
    """
    def __init__(self, width_chars: int, height_chars: int):
        self.base_width_chars = width_chars
        self.base_height_chars = height_chars
        self.clear_color = (12, 12, 20)
        
        # Set initial resolution, which also initializes the buffers.
        self.set_resolution_factor(1.0)
        
    def _is_mesh_visible(self, mesh, camera, view_proj_matrix, model_matrix=None) -> bool:
        """
        Checks if the mesh's bounding box is within the camera's view frustum,
        with a margin to prevent early disappearance.
        """
        MARGIN = 0.2  # Adjust this value as needed (larger = more room before disappearing)

        # Get the 8 corners of the bounding box
        corners = [
            Vec3(mesh.min_v.x, mesh.min_v.y, mesh.min_v.z),
            Vec3(mesh.max_v.x, mesh.min_v.y, mesh.min_v.z),
            Vec3(mesh.min_v.x, mesh.max_v.y, mesh.min_v.z),
            Vec3(mesh.max_v.x, mesh.max_v.y, mesh.min_v.z),
            Vec3(mesh.min_v.x, mesh.min_v.y, mesh.max_v.z),
            Vec3(mesh.max_v.x, mesh.min_v.y, mesh.max_v.z),
            Vec3(mesh.min_v.x, mesh.max_v.y, mesh.max_v.z),
            Vec3(mesh.max_v.x, mesh.max_v.y, mesh.max_v.z),
        ]
    
        # Transform bounding box to world space
        model_matrix = (model_matrix if model_matrix is not None else
                        (Mat4.translate(mesh.pos.x, mesh.pos.y, mesh.pos.z) *
                         Mat4.rotate_y(mesh.rot.y) *
                         Mat4.rotate_x(mesh.rot.x) *
                         Mat4.rotate_z(mesh.rot.z) *
                         Mat4.scale(mesh.scale.x, mesh.scale.y, mesh.scale.z)))
                    
        world_corners = [model_matrix * c for c in corners]
    
        # Project world-space corners to clip space
        projected_corners = [view_proj_matrix * c for c in world_corners]
    
        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')

        for v_proj in projected_corners:
            min_x = min(min_x, v_proj.x)
            min_y = min(min_y, v_proj.y)
            min_z = min(min_z, v_proj.z)
            max_x = max(max_x, v_proj.x)
            max_y = max(max_y, v_proj.y)
            max_z = max(max_z, v_proj.z)

        # Frustum culling with margin
        if max_x < -1.0 - MARGIN or min_x > 1.0 + MARGIN or \
           max_y < -1.0 - MARGIN or min_y > 1.0 + MARGIN or \
           max_z < camera.znear - MARGIN or min_z > camera.zfar + MARGIN:
            return False

        return True


    # --- Buffer & Resolution Management ---
    def set_resolution_factor(self, factor: float):
        """
        Adjusts the rendering resolution and resizes the color and depth buffers.
        A factor > 1 creates a higher-resolution buffer that is downsampled for display.
        """
        self.res_factor = factor
        self.pixel_width = int(self.base_width_chars * factor)
        self.pixel_height = int(self.base_height_chars * factor) * 2
        
        num_pixels = self.pixel_width * self.pixel_height

        # Use flat lists for buffers to improve data locality and cache performance.
        self.color_buffer = [(0, 0, 0, 0)] * num_pixels
        self.depth_buffer = [float('inf')] * num_pixels

    def _get_buffer_index(self, x: int, y: int) -> int:
        """Calculates the 1D index from 2D coordinates."""
        return y * self.pixel_width + x

    def clear_buffers(self):
        """Resets the color and depth buffers to their default clear values."""
        num_pixels = self.pixel_width * self.pixel_height
        bg = self.clear_color
        clear_pixel = (bg[0], bg[1], bg[2], 0)
        
        # Efficiently fill the lists in-place.
        self.color_buffer[:] = [clear_pixel] * num_pixels
        self.depth_buffer[:] = [float('inf')] * num_pixels

    # --- Frame Rendering Pipeline ---
    def render_mesh(self, mesh, camera, lights, model_matrix=None):
        """
        Performs the full rendering pipeline for a single mesh,
        including transformations, projection, and rasterization.
        """
        # Create the view and projection matrices
        aspect_ratio = self.pixel_width / self.pixel_height
        view_matrix = (Mat4.rotate_x(-camera.rot.x) *
                       Mat4.rotate_y(-camera.rot.y) *
                       Mat4.rotate_z(-camera.rot.z) *
                       Mat4.translate(-camera.pos.x, -camera.pos.y, -camera.pos.z))
        proj_matrix = Mat4.perspective(camera.fov, aspect_ratio, camera.znear, camera.zfar)
        
        view_proj_matrix = proj_matrix * view_matrix
        
        # Frustum culling check: skip rendering if the bounding box is not visible.
        if not self._is_mesh_visible(mesh, camera, view_proj_matrix, model_matrix=model_matrix):
            return

        # Pre-calculate scaled light values for efficiency.
        ambient_scaled = (self.engine_ref.ambient_light[0] * COLOR_SCALE,
                          self.engine_ref.ambient_light[1] * COLOR_SCALE,
                          self.engine_ref.ambient_light[2] * COLOR_SCALE)
                          
        lights_scaled = []
        for light in lights:
            if isinstance(light, DirectionalLight):
                # Directional light
                lights_scaled.append(("directional", light.direction,
                    (light.color[0] * COLOR_SCALE, light.color[1] * COLOR_SCALE, light.color[2] * COLOR_SCALE),
                    light.intensity))
            elif isinstance(light, SpotLight):
                # Spotlight
                lights_scaled.append(("spot", light,
                    (light.color[0] * COLOR_SCALE, light.color[1] * COLOR_SCALE, light.color[2] * COLOR_SCALE),
                    light.intensity))
            elif isinstance(light, PointLight):
                # Point light
                lights_scaled.append(("point", light,
                    (light.color[0] * COLOR_SCALE, light.color[1] * COLOR_SCALE, light.color[2] * COLOR_SCALE),
                    light.intensity))

        # Apply transformations and project vertices
        transformed_verts = self._transform_mesh_vertices(mesh, model_matrix=model_matrix)
        projected_verts = self._project_vertices(transformed_verts, camera)
        
        # Rasterize and shade the triangles.
        self._rasterize_triangles(mesh, transformed_verts, projected_verts, lights_scaled, ambient_scaled)

    def _transform_mesh_vertices(self, mesh, model_matrix=None) -> List[Vec3]:
        """Applies model transformations (scale, rotate, translate) to a mesh's vertices."""
        # It's more efficient to chain multiplications from right to left,
        # so the final matrix applies scale, then rotation, then translation.
        model_matrix = (model_matrix if model_matrix is not None else
                        (Mat4.translate(mesh.pos.x, mesh.pos.y, mesh.pos.z) *
                         Mat4.rotate_y(mesh.rot.y) *
                         Mat4.rotate_x(mesh.rot.x) *
                         Mat4.rotate_z(mesh.rot.z) *
                         Mat4.scale(mesh.scale.x, mesh.scale.y, mesh.scale.z)))

        return [model_matrix * v for v in mesh.verts]

    def _project_vertices(self, world_verts: List[Vec3], camera) -> List[Tuple[int, int, float]]:
        """Projects world-space vertices into screen space, handling perspective."""
        projected = []
        aspect_ratio = self.pixel_width / self.pixel_height

        # Create the view matrix from the camera's inverse transform.
        view_matrix = (Mat4.rotate_x(-camera.rot.x) *
                       Mat4.rotate_y(-camera.rot.y) *
                       Mat4.rotate_z(-camera.rot.z) *
                       Mat4.translate(-camera.pos.x, -camera.pos.y, -camera.pos.z))
                       
        # Create the projection matrix.
        proj_matrix = Mat4.perspective(camera.fov, aspect_ratio, camera.znear, camera.zfar)

        for v_world in world_verts:
            v_view = view_matrix * v_world
            z_proj = v_view.z + camera.zoom

            if z_proj <= camera.znear:
                projected.append((0, 0, float('inf')))
                continue

            v_proj = proj_matrix * Vec3(v_view.x, v_view.y, z_proj)
            
            # Map normalized device coordinates (-1 to 1) to pixel coordinates (0 to W/H).
            px = int((v_proj.x * 0.5 + 0.5) * (self.pixel_width - 1))
            py = int((-v_proj.y * 0.5 + 0.5) * (self.pixel_height - 1))
            projected.append((px, py, z_proj))
        return projected

    # --- Shading and Rasterization ---
    def _calculate_flat_color(
        self,
        base_color: Tuple[int, int, int],
        normal: Vec3,
        frag_pos: Vec3,
        lights: List,
        ambient_light: Tuple[float, float, float]
    ) -> Tuple[int, int, int]:
        """Flat shading: ambient + diffuse, supporting directional and spot lights."""
        br, bg, bb = base_color
        ar, ag, ab = ambient_light
        nx, ny, nz = normal.x, normal.y, normal.z

        # Start with ambient contribution
        total_r = br * ar
        total_g = bg * ag
        total_b = bb * ab

        for ltype, ldata, lcolor, lintensity in lights:
            if ltype == "directional":
                light_dir = -ldata
                intensity = max(nx * light_dir.x + ny * light_dir.y + nz * light_dir.z, 0.0) * lintensity
                spot_factor = 1.0
                dist_factor = 1.0
            elif ltype == "spot":
                spotlight = ldata
                L = (spotlight.position - frag_pos).norm()
                diff = max(normal.dot(L), 0.0)
                spot_factor = spotlight.cone_factor(frag_pos)
                dist_factor = spotlight.attenuation(frag_pos)
                intensity = diff * lintensity * spot_factor * dist_factor
            elif ltype == "point":
                pointlight = ldata
                light_vec = (pointlight.position - frag_pos).norm()
                diff = max(normal.dot(light_vec), 0.0)
                dist_factor = pointlight.attenuation(frag_pos)
                intensity = diff * lintensity * dist_factor
                spot_factor = 1.0 # Point lights have no cone factor
            else:
                continue

            lr, lg, lb = lcolor
            total_r += br * lr * intensity
            total_g += bg * lg * intensity
            total_b += bb * lb * intensity

        final_r = clamp(int(total_r), 0, 255)
        final_g = clamp(int(total_g), 0, 255)
        final_b = clamp(int(total_b), 0, 255)
        return final_r, final_g, final_b
    
    def _calculate_phong_color(
        self,
        base_color: Tuple[int, int, int],
        normal: Vec3,
        view_dir: Vec3,
        lights: List,
        ambient_light: Tuple[float, float, float],
        frag_pos: Vec3
    ) -> Tuple[int, int, int]:
        """Phong shading: ambient + diffuse + specular, supporting directional and spot lights."""
        br, bg, bb = base_color
        ar, ag, ab = ambient_light
    
        # Phong parameters
        specular_strength = 0.5
        shininess = 32

        # Start with ambient
        total_r = br * ar
        total_g = bg * ag
        total_b = bb * ab

        for ltype, ldata, lcolor, lintensity in lights:
            if ltype == "directional":
                light_vec = -ldata.norm()
                diff = max(normal.dot(light_vec), 0.0)
                spot_factor = 1.0
                dist_factor = 1.0
            elif ltype == "spot":
                spotlight = ldata
                L = (spotlight.position - frag_pos).norm()
                light_vec = L
                diff = max(normal.dot(L), 0.0)
                spot_factor = spotlight.cone_factor(frag_pos)
                dist_factor = spotlight.attenuation(frag_pos)
            elif ltype == "point":
                pointlight = ldata
                light_vec = (pointlight.position - frag_pos).norm()
                diff = max(normal.dot(light_vec), 0.0)
                dist_factor = pointlight.attenuation(frag_pos)
                intensity = diff * lintensity * dist_factor
                spot_factor = 1.0 # Point lights have no cone factor
            else:
                continue

            lr, lg, lb = lcolor
            # Diffuse
            total_r += br * lr * diff * lintensity * spot_factor * dist_factor
            total_g += bg * lg * diff * lintensity * spot_factor * dist_factor
            total_b += bb * lb * diff * lintensity * spot_factor * dist_factor

            # Specular
            reflect_dir = (normal * 2 * normal.dot(light_vec) - light_vec).norm()
            spec = max(view_dir.dot(reflect_dir), 0.0) ** shininess
            total_r += 255 * lr * specular_strength * spec * lintensity * spot_factor * dist_factor
            total_g += 255 * lg * specular_strength * spec * lintensity * spot_factor * dist_factor
            total_b += 255 * lb * specular_strength * spec * lintensity * spot_factor * dist_factor

        final_r = clamp(int(total_r), 0, 255)
        final_g = clamp(int(total_g), 0, 255)
        final_b = clamp(int(total_b), 0, 255)
        return final_r, final_g, final_b


    def _draw_wireframe(self, mesh, projected_verts, color=(255,255,255)):
        """Draws triangle edges as lines (Bresenham) with depth check."""
        pixel_width, pixel_height = self.pixel_width, self.pixel_height
        color_buffer = self.color_buffer
        depth_buffer = self.depth_buffer
        for i0, i1, i2 in mesh.faces:
            for a, b in [(i0, i1), (i1, i2), (i2, i0)]:
                x0, y0, z0 = projected_verts[a]
                x1, y1, z1 = projected_verts[b]
                # Bresenham's line algorithm with depth interpolation
                dx = abs(x1 - x0)
                dy = abs(y1 - y0)
                sx = 1 if x0 < x1 else -1
                sy = 1 if y0 < y1 else -1
                err = dx - dy
                x, y = x0, y0
                steps = max(dx, dy) if max(dx, dy) > 0 else 1
                for i in range(steps + 1):
                    t = i / steps if steps > 0 else 0
                    z = z0 * (1 - t) + z1 * t
                    if 0 <= x < pixel_width and 0 <= y < pixel_height:
                        idx = y * pixel_width + x
                        if z < depth_buffer[idx]:
                            depth_buffer[idx] = z
                            color_buffer[idx] = (color[0], color[1], color[2], 1)
                    if x == x1 and y == y1:
                        break
                    e2 = 2 * err
                    if e2 > -dy:
                        err -= dy
                        x += sx
                    if e2 < dx:
                        err += dx
                        y += sy

    def _rasterize_triangles(self, mesh, transformed_verts, projected_verts, lights, ambient):
        """
        Rasterizes each triangle of the mesh using incremental barycentric coordinates.
        This method fills the color and depth buffers.
        """
        if mesh.material == 'wireframe':
            self._draw_wireframe(mesh, projected_verts)
            return

        pixel_width, pixel_height = self.pixel_width, self.pixel_height
        depth_buffer = self.depth_buffer
        color_buffer = self.color_buffer

        for i0, i1, i2 in mesh.faces:
            x0, y0, z0 = projected_verts[i0]
            x1, y1, z1 = projected_verts[i1]
            x2, y2, z2 = projected_verts[i2]
            
            # Skip triangles that are too close to the camera (or are clipped).
            if z0 == float('inf') or z1 == float('inf') or z2 == float('inf'):
                continue
                
            # Backface culling: Check if the triangle is facing away from the camera.
            # Use the sign of the cross product for the area.
            cross_product_area = (x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0)
            
            # Handle the case of zero-area triangles.
            if cross_product_area == 0:
                continue

            # This line was missing! It calculates the inverse area.
            inv_area = 1.0 / cross_product_area
            
            # Find the bounding box for the triangle.
            min_x = max(0, min(x0, x1, x2))
            max_x = min(pixel_width - 1, max(x0, x1, x2))
            min_y = max(0, min(y0, y1, y2))
            max_y = min(pixel_height - 1, max(y0, y1, y2))
            
            if min_x > max_x or min_y > max_y:
                continue

            # Calculate the face normal.
            v0_world, v1_world, v2_world = transformed_verts[i0], transformed_verts[i1], transformed_verts[i2]
            face_normal = (v1_world - v0_world).cross(v2_world - v0_world).norm()
            
            # The average color for the triangle.
            avg_color = ((mesh.vcols[i0][0] + mesh.vcols[i1][0] + mesh.vcols[i2][0]) / 3,
                         (mesh.vcols[i0][1] + mesh.vcols[i1][1] + mesh.vcols[i2][1]) / 3,
                         (mesh.vcols[i0][2] + mesh.vcols[i1][2] + mesh.vcols[i2][2]) / 3)
            
            # Determine if the front or back face is visible based on the cross product.
            is_front_face = cross_product_area > 0

            # Calculate the final color based on the visible side.
            tri_center = (v0_world + v1_world + v2_world) * (1/3)

            if mesh.material == 'phong':
                view_dir = (Vec3(0,0,0) - tri_center).norm()
                if is_front_face:
                    final_color = self._calculate_phong_color(avg_color, face_normal, view_dir, lights, ambient, tri_center)
                else:
                    final_color = self._calculate_phong_color(avg_color, -face_normal, view_dir, lights, ambient, tri_center)
            else:  # 'flat' shading
                if is_front_face:
                    final_color = self._calculate_flat_color(avg_color, face_normal, tri_center, lights, ambient)
                else:
                    final_color = self._calculate_flat_color(avg_color, -face_normal, tri_center, lights, ambient)


            # The alpha value is 1 for any pixel that gets rendered.
            rgba = (final_color[0], final_color[1], final_color[2], 1)

            # Pre-calculate edge coefficients for incremental rasterization.
            A0, B0, C0 = edge_coeffs(x1, y1, x2, y2)
            A1, B1, C1 = edge_coeffs(x2, y2, x0, y0)
            A2, B2, C2 = edge_coeffs(x0, y0, x1, y1)

            # Initial barycentric weights for the top-left corner of the bounding box.
            w0_row = A0 * min_x + B0 * min_y + C0
            w1_row = A1 * min_x + B1 * min_y + C1
            w2_row = A2 * min_x + B2 * min_y + C2

            # Delta values for incremental updates.
            dw0dx, dw1dx, dw2dx = A0, A1, A2
            dw0dy, dw1dy, dw2dy = B0, B1, B2

            for py in range(min_y, max_y + 1):
                w0, w1, w2 = w0_row, w1_row, w2_row
                base_index = py * pixel_width + min_x
                
                for px in range(min_x, max_x + 1):
                    # Check if the pixel is inside the triangle.
                    if (w0 >= 0 and w1 >= 0 and w2 >= 0) or \
                       (w0 <= 0 and w1 <= 0 and w2 <= 0):
                        
                        # Calculate barycentric coordinates.
                        bw0 = w0 * inv_area
                        bw1 = w1 * inv_area
                        bw2 = w2 * inv_area
                        
                        # Interpolate depth (z-value).
                        z = bw0 * z0 + bw1 * z1 + bw2 * z2
                        
                        if z < depth_buffer[base_index]:
                            depth_buffer[base_index] = z
                            color_buffer[base_index] = rgba
                            
                    # Increment weights for the next pixel.
                    w0 += dw0dx
                    w1 += dw1dx
                    w2 += dw2dx
                    base_index += 1

                # Increment weights for the next row.
                w0_row += dw0dy
                w1_row += dw1dy
                w2_row += dw2dy

    # --- Output Composition ---
    def compose_to_chars(self) -> List[str]:
        """
        Composes the pixel buffers into a list of terminal characters.
        This uses half-block rendering, where each character represents a
        top and bottom pixel, effectively doubling the vertical resolution.
        """
        output_lines = []
        char_width, char_height = self.base_width_chars, self.base_height_chars
        res_factor = self.res_factor
        pixel_width, pixel_height = self.pixel_width, self.pixel_height
        color_buffer = self.color_buffer

        # The number of sub-pixels per character cell depends on the resolution factor.
        sub_pixels_per_char = int(res_factor * res_factor)
        
        for cy in range(char_height):
            row_chars = []
            
            # Determine the pixel rows corresponding to the top and bottom of the character.
            top_y_base = int(cy * 2 * res_factor)
            bot_y_base = int((cy * 2 + 1) * res_factor)
            
            for cx in range(char_width):
                col_base = int(cx * res_factor)
                
                # Initialize sums for averaging top and bottom sub-pixel colors.
                tr_sum, tg_sum, tb_sum = 0, 0, 0
                br_sum, bg_sum, bb_sum = 0, 0, 0
                
                for sy in range(int(res_factor)):
                    ty = min(top_y_base + sy, pixel_height - 1)
                    by = min(bot_y_base + sy, pixel_height - 1)
                    
                    row_offset_t = ty * pixel_width
                    row_offset_b = by * pixel_width
                    
                    for sx in range(int(res_factor)):
                        px = min(col_base + sx, pixel_width - 1)
                        
                        # Get pixel colors from the buffer.
                        top_pixel_color = color_buffer[row_offset_t + px]
                        bot_pixel_color = color_buffer[row_offset_b + px]
                        
                        # Accumulate color sums for averaging.
                        tr_sum += top_pixel_color[0]
                        tg_sum += top_pixel_color[1]
                        tb_sum += top_pixel_color[2]
                        
                        br_sum += bot_pixel_color[0]
                        bg_sum += bot_pixel_color[1]
                        bb_sum += bot_pixel_color[2]

                # Calculate the average color for the top and bottom halves.
                top_rgb = (tr_sum // sub_pixels_per_char, tg_sum // sub_pixels_per_char, tb_sum // sub_pixels_per_char)
                bot_rgb = (br_sum // sub_pixels_per_char, bg_sum // sub_pixels_per_char, bb_sum // sub_pixels_per_char)
                
                # Use ANSI escape codes to set the foreground and background colors.
                # The '▀' character (upper half block) is then colored with these.
                row_chars.append(fg_rgb(*top_rgb) + bg_rgb(*bot_rgb) + '▀' + RESET)
                
            output_lines.append(''.join(row_chars))
        
        return output_lines
