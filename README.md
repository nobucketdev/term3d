# Term3D: Terminal-based 3D Graphics Engine

Term3D is a lightweight 3D graphics engine written from scratch in pure Python with minimal external libraries. It is designed to render 3D scenes directly to the terminal, utilizing Unicode half-block characters as pixels and ANSI escape codes for color. This project serves as a demonstration of a software rendering pipeline, including matrix transformations, lighting, and rasterization, all without relying on external libraries.

<p align="center">
  <a href="https://github.com/nobucketdev/term3d"><img src="https://img.shields.io/badge/term3d-009955?style=for-the-badge&logo=gnometerminal&logoColor=white" /></a>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <a href="LICENSE.md"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" />
  <img src="https://img.shields.io/badge/macOS-333333?style=for-the-badge&logo=apple&logoColor=white" />
</p>

## Features

* **Software Rendering:** Renders 3D geometry to a 2D terminal buffer without hardware acceleration.
* **Scene Graph:** Manages objects, lights, and cameras in a hierarchical structure.
* **Built-in Primitives:** Includes a shape builder for generating basic meshes like cubes, UV spheres, and planes.
* **Lighting Models:** Supports directional, spotlight, and point lights to add realism to scenes.
* **Matrix Algebra:** Custom vector (`Vec3`) and matrix (`Mat4`) libraries for 3D transformations.
* **Cross-platform Keyboard Input:** Handles non-blocking key presses on both Windows and Unix-like systems.

## Installation

This project has no external dependencies. To use it, simply download all the Python files (`.py`) and place them in the same directory.

## Usage

You can run a demo scene by executing one of the example scripts from your command line.

**Note:** If you didn't install the term3d into python yet, you can move all the test file from tests to outside to run
```bash
git clone https://github.com/nobucketdev/term3d.git
cd term3d
```

For the parent-child orbit example:

```bash
mv tests/spheresystem.py spheresystem.py
python3 spheresystem.py
```

For the spotlight scene:

```bash
mv tests/spotlight.py spotlight.py
python3 spotlight.py
```
If you want a quick test:
```bash
python3 quicktest.py
```

You can control the camera and view the scene using the keyboard controls defined in the `core.py` and example files.

## File Structure & Components

* **`core.py`**: The central engine class, `term3d`. It manages the rendering loop, scene graph, user input, and camera.
* **`renderer.py`**: Contains the `Renderer` class, which handles the core rendering pipeline. It performs view transformations and rasterization.
* **`shpbuild.py`**: Defines the `Mesh` class and provides helper functions (`build_cube`, `build_uv_sphere`, etc.) to create geometric primitives.
* **`objects.py`**: Defines the different types of light sources (`DirectionalLight`, `SpotLight`, `PointLight`) and the `SceneNode` class for the scene graph.
* **`vec3lib.py`**: A custom class for 3D vector math, including common operations like addition, subtraction, dot products, and normalization.
* **`mat4lib.py`**: A custom class for 4x4 matrix operations, used for all 3D transformations.
* **`utils.py`**: A collection of utility functions, including ANSI color code helpers for terminal output.
* **`tests/`**: Contain various test program.

## Suggest interpreter
As running a big scene, you might found the FPS is low. So I suggest using PyPy interpreter for a better performance
```bash
pypy3 quicktest.py
```
