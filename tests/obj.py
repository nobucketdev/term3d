
"""
viewer.py - Simple OBJ viewer for Term3D

Usage:
    python viewer.py path/to/model.obj [options]

Examples:
    python viewer.py model.obj --fov 75 --material wireframe --no-autorotate
    python viewer.py pumpkin.obj --width 120 --height 50 --ambient 30 30 60
"""

import sys
import math
import argparse
from pathlib import Path
import shutil

# import your engine pieces
import term3d.core as core_mod
from term3d.objects import Mesh, Vec3


def load_obj(path: str):
    """Minimal OBJ loader (verts, normals, uvs, faces) with triangulation."""
    verts, normals, uvs, faces = [], [], [], []

    with open(path, "r", encoding="utf8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if parts[0] == "v" and len(parts) >= 4:
                x, y, z = map(float, parts[1:4])
                verts.append(Vec3(x, y, z))
            elif parts[0] == "vn" and len(parts) >= 4:
                nx, ny, nz = map(float, parts[1:4])
                normals.append(Vec3(nx, ny, nz))
            elif parts[0] == "vt" and len(parts) >= 3:
                u, v = map(float, parts[1:3])
                uvs.append((u, v))
            elif parts[0] == "f" and len(parts) >= 4:
                idxs = []
                for tok in parts[1:]:
                    vi = int(tok.split("/")[0]) if "/" in tok else int(tok)
                    if vi < 0:
                        vi = len(verts) + 1 + vi
                    idxs.append(vi - 1)
                for i in range(1, len(idxs) - 1):
                    faces.append((idxs[0], idxs[i], idxs[i + 1]))

    if not verts:
        raise ValueError("No vertices loaded from OBJ.")

    colors = [(150, 150, 150) for _ in verts]
    mesh = Mesh(verts=verts, faces=faces, colors=colors, material="flat")
    mesh.calculate_bounds()
    return mesh


def center_and_scale_mesh(mesh: Mesh, target_size=1.6):
    """Center mesh at origin and scale uniformly to target_size."""
    mesh.calculate_bounds()
    if mesh.min_v is None or mesh.max_v is None:
        return
    min_v, max_v = mesh.min_v, mesh.max_v
    center = Vec3((min_v.x + max_v.x) / 2, (min_v.y + max_v.y) / 2, (min_v.z + max_v.z) / 2)
    size_x, size_y, size_z = max_v.x - min_v.x, max_v.y - min_v.y, max_v.z - min_v.z
    max_dim = max(size_x, size_y, size_z)
    scale = target_size / max_dim if max_dim > 0 else 1.0

    for v in mesh.verts:
        v.x, v.y, v.z = (v.x - center.x) * scale, (v.y - center.y) * scale, (v.z - center.z) * scale

    mesh.calculate_bounds()

def parse_args():
    p = argparse.ArgumentParser(description="Simple OBJ viewer for Term3D")
    p.add_argument("objfile", nargs="?", default=None, help="Path to OBJ file (default: test/teapot.obj)")
    p.add_argument("--fov", type=float, default=60.0, help="Camera field of view in degrees")
    p.add_argument("--size", type=float, default=1.6, help="Target size for scaling model")
    p.add_argument("--width", type=int, help="Override terminal width")
    p.add_argument("--height", type=int, help="Override terminal height")
    p.add_argument("--material", choices=["flat", "wireframe", "phong"],
               default="flat", help="Initial material mode")
    p.add_argument("--no-autorotate", action="store_true", help="Disable auto-rotation at start")
    p.add_argument("--ambient", type=int, nargs=3, metavar=("R", "G", "B"), default=(60, 60, 50),
                   help="Ambient light RGB")
    p.add_argument("--light-dir", type=float, nargs=3, metavar=("X", "Y", "Z"),
                   default=(0.5, 0.7, 0), help="Directional light vector")
    p.add_argument("--light-color", type=int, nargs=3, metavar=("R", "G", "B"),
                   default=(255, 255, 255), help="Directional light color")
    p.add_argument("--zoom", type=float, default=-1.0, help="Initial camera z position")
    return p.parse_args()


def main():
    args = parse_args()
    objpath = Path(args.objfile) if args.objfile else Path("tests/teapot.obj")

    if not objpath.exists():
        print("File not found:", objpath)
        sys.exit(1)

    print("Loading:", objpath)
    mesh = load_obj(str(objpath))
    center_and_scale_mesh(mesh, target_size=args.size)
    mesh.material = args.material
    mesh = load_obj(str(objpath))
    center_and_scale_mesh(mesh, target_size=args.size)
    mesh.material = args.material

    try:
        cols, rows = shutil.get_terminal_size(fallback=(100, 40))
        rows = max(12, rows - 6)
    except Exception:
        cols, rows = 100, 40

    if args.width:
        cols = args.width
    if args.height:
        rows = args.height

    engine = core_mod.term3d(cols, rows)
    node = engine.add_mesh_node(mesh, name="model")
    engine.register_for_rotation(node)

    rotating = not args.no_autorotate
    if not rotating and node in engine.rotating_nodes:
        engine.rotating_nodes.remove(node)

    engine.set_camera_position(0, 0, args.zoom)
    engine.set_camera_fov(args.fov)
    engine.set_ambient_light(*args.ambient)
    engine.add_light(Vec3(*args.light_dir), tuple(args.light_color), intensity=1.2)

    def toggle_material():
        order = ["flat", "wireframe", "phong"]
        idx = order.index(mesh.material) if mesh.material in order else 0
        mesh.material = order[(idx + 1) % len(order)]
        print(f"Material switched to: {mesh.material}")

    def toggle_rotation():
        nonlocal rotating
        if node in engine.rotating_nodes:
            engine.rotating_nodes.remove(node)
            rotating = False
        else:
            engine.rotating_nodes.append(node)
            rotating = True

    engine.set_key_binding("m", toggle_material)
    engine.set_key_binding(" ", toggle_rotation)
    engine.set_key_binding("w", lambda: engine.move_camera(z=0.3))
    engine.set_key_binding("s", lambda: engine.move_camera(z=-0.3))
    engine.set_key_binding("a", lambda: engine.rotate_camera(y=0.1))
    engine.set_key_binding("d", lambda: engine.rotate_camera(y=-0.1))
    engine.set_key_binding("q", lambda: engine.zoom_camera(-0.3))
    engine.set_key_binding("e", lambda: engine.zoom_camera(0.3))
    engine.set_key_binding("r", lambda: (engine.set_camera_position(0, 0, args.zoom),
                                         engine.set_camera_rotation(0, 0, 0)))
    engine.set_key_binding("i", lambda: engine.rotate_camera(x=0.07))   # up
    engine.set_key_binding("k", lambda: engine.rotate_camera(x=-0.07))  # down
    engine.set_key_binding("j", lambda: engine.move_camera(x=-0.3))     # left
    engine.set_key_binding("l", lambda: engine.move_camera(x=0.3))      # right

    def on_update(dt):
        if rotating:
            node.transform.rot.y += dt * 0.4
            node.transform.rot.x += dt * 0.3

    engine.set_on_update(on_update)
    engine.set_title(f"OBJ Viewer - {objpath.name}")
    print("Controls: w/s/a/d q/e r m (toggle material) SPACE (toggle rotation), ESC to quit")
    engine.run()


if __name__ == "__main__":
    main()
