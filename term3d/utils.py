CSI = '\x1b['
RESET = CSI + '0m'
HIDE_CURSOR = CSI + '?25l'
SHOW_CURSOR = CSI + '?25h'
CLEAR_SCREEN = CSI + '2J' + CSI + 'H'
SET_TITLE = '\x1b]2;{title}\x07'
def clamp(v, a, b): return a if v < a else (b if v > b else v)
def fg_rgb(r, g, b):
    return f"{CSI}38;2;{int(r)};{int(g)};{int(b)}m"
def bg_rgb(r, g, b):
    return f"{CSI}48;2;{int(r)};{int(g)};{int(b)}m"
def set_mat(mesh, material):
    if material in ('flat', 'phong', 'wireframe'):
        mesh.material = material
    else:
        raise ValueError("Material must be 'flat', 'phong', or 'wireframe'.")