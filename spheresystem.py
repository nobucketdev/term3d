import math
import sys
import time

from term3d.core import SceneNode, Vec3, term3d
from term3d.shpbuild import build_uv_sphere


def main():
    """
    Main function to set up and run the example scene with node finding API.
    """
    try:
        # Create the 3D engine instance
        engine = term3d(120, 40)
        engine.set_title("Parent-Child-Grandchild Orbit Example with Node Query Demo")

        # Set up a directional light
        engine.add_light(Vec3(0.5, 0.5, -0.5), (255, 255, 255), intensity=1.0)

        # Set camera position to view the scene
        engine.set_camera_position(0, 0, -14)

        # Create the parent sphere node
        parent_mesh = build_uv_sphere(radius=2.0, color=(100, 100, 255))
        # Assign a 'parent' tag when creating the node
        parent_node = engine.add_mesh_node(parent_mesh, "Parent Sphere")
        parent_node.add_tag("parent", "celestial_body")
        parent_node.set_pivot(0, 0, 0)

        # Create the child sphere node and attach it to the parent
        child_mesh = build_uv_sphere(radius=1.0, color=(255, 100, 100))
        child_node = parent_node.add(SceneNode("Child Sphere"))
        child_node.mesh = child_mesh
        # Assign 'child' and 'celestial_body' tags
        child_node.add_tag("child", "celestial_body")
        child_node.set_pos(0, 0, 6)

        # Create the grandchild sphere node and attach it to the child
        grandchild_mesh = build_uv_sphere(radius=0.5, color=(255, 255, 0))
        grandchild_node = child_node.add(SceneNode("Grandchild Sphere"))
        grandchild_node.mesh = grandchild_mesh
        # Assign 'grandchild' and 'celestial_body' tags
        grandchild_node.add_tag("grandchild", "celestial_body")
        grandchild_node.set_pos(0, 0, 2.5)

        # === Demonstrate Node Query API ===
        print("\n--- Node Query Demo ---")
        # Find by name pattern
        sphere_nodes = engine.find_by_name("*Sphere")
        print(f"Nodes matching '*Sphere': {[n.name for n in sphere_nodes]}")

        # List children of parent_node
        print(
            f"Direct children of {parent_node.name}: {[c.name for c in parent_node.get_children()]}"
        )

        # List all descendants of parent_node
        print(
            f"All descendants of {parent_node.name}: {[c.name for c in parent_node.get_all_descendants()]}"
        )

        # Find parent of grandchild_node
        print(f"Parent of {grandchild_node.name}: {grandchild_node.get_parent().name}")

        # New: Print node names and their tags
        print("\nNode Tags:")
        for node_name, node in engine.nodes.items():
            # Skip the root node for this example
            if node_name != "root":
                print(f"  {node_name}: {list(node.tags)}")

        # === End of Query Demo ===

        # This variable will track the parent's rotation
        parent_rotation = 0.0

        # This variable will track the child's rotation
        child_rotation = 0.0

        # Get the start time for the oscillation calculation
        start_time = time.time()

        # Create a loop to continuously update the parent, child, and grandchild nodes
        def update_scene(dt):
            nonlocal parent_rotation
            nonlocal child_rotation

            # Get elapsed time for the sine wave
            elapsed_time = time.time() - start_time

            # Make the parent's x-position oscillate using a sine wave
            x_pos = math.sin(elapsed_time) * 5.0
            parent_node.set_pos(x_pos, 0, 0)

            # Rotate the parent around its own pivot point
            parent_rotation += math.pi * dt / 2  # Rotate 90 degrees per second
            parent_node.set_rot(0, parent_rotation, 0)

            # Rotate the child around its own pivot, which causes the grandchild to orbit it
            child_rotation += math.pi * dt  # Rotate 180 degrees per second
            child_node.set_rot(0, child_rotation, 0)

        # Hook the update function into the engine loop
        engine.set_on_update(update_scene)

        # Add keybindings for camera control
        engine.set_key_binding("w", lambda: engine.move_camera(z=1))
        engine.set_key_binding("s", lambda: engine.move_camera(z=-1))
        engine.set_key_binding("a", lambda: engine.move_camera(x=-1))
        engine.set_key_binding("d", lambda: engine.move_camera(x=1))
        engine.set_key_binding("q", lambda: engine.rotate_camera(y=-0.1))
        engine.set_key_binding("e", lambda: engine.rotate_camera(y=0.1))

        # Start the main rendering loop
        engine.run()

    except Exception as e:
        print(f"An error occurred: {e}")
        # Clean up the terminal in case of an error
        print("\x1b[?25h\x1b[0m")
        sys.exit(1)


if __name__ == "__main__":
    main()
