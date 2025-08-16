
# Term3D: A 3D Rendering Engine for Your Terminal

Term3D is a lightweight 3D graphics engine written in Python, designed to render 3D scenes directly in your terminal. It's built to be a simple, accessible library for creating and visualizing 3D content in a text-based environment.

## Features

- **Unicode Half-Block Rendering:** Utilizes the Unicode half-block character (`▀`) to achieve a higher vertical resolution, packing two "pixels" into each character space.

- **Truecolor ANSI Support:** Provides smooth, rich color depth using ANSI truecolor for both foreground and background.

- **Mesh Rendering:** Supports rendering of 3D meshes with triangle rasterization and a Z-buffer for correct depth occlusion.

- **Lighting:** Includes support for multiple directional lights with adjustable color and intensity.

- **Shading Option:** Support Flat, Phone and wireframe material.

- **Cross-Platform Keyboard Controls:** A non-blocking input system allows for interactive camera and scene control across different operating systems.

- **Adjustable Quality:** Control the rendering resolution and target frames per second (FPS).

- **Per-Object Movement & Rotation API** Make it easy animate an object without suffer FPS drop due to object creation and deletion.

- **Status Overlay:** An optional overlay displays real-time FPS, camera position, and other scene information for debugging.
