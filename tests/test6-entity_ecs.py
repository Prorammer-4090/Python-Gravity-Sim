from core.ecs.entity import Entity
from helpers.transform import Transform
import numpy as np

# Helper to print matrix nicely
def print_matrix(name, matrix):
    print(f"{name} World Matrix:")
    print(np.array_str(matrix, precision=2, suppress_small=True))
    print()

# Helper to print position from matrix
def print_position(name, matrix):
    pos = matrix[0:3, 3]  # Extract translation component from the matrix
    print(f"{name} World Position: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")

# Default transform component generator
def make_transform(pos, rot=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)):
    return {
        "position": list(pos),
        "rotation": list(rot),
        "scale": list(scale)
    }

# Create entities without parent links first
scene = Entity("Scene Root")
sun = Entity("Sun")
planet = Entity("Planet")
moon = Entity("Moon")

# Configure transforms
scene.add_component("Transform", make_transform(pos=(0.0, 0.0, 0.0)))
sun.add_component("Transform", make_transform(pos=(10.0, 0.0, 0.0)))
planet.add_component("Transform", make_transform(pos=(5.0, 0.0, 0.0), rot=(0, 10, 0)))
moon.add_component("Transform", make_transform(pos=(2.0, 0.0, 0.0)))

# Set up parent-child relationships
scene.add_child(sun)
sun.add_child(planet)
planet.add_child(moon)

# First approach: update each entity's local transform explicitly
print("=== Approach 1: Explicit local and world transform updates ===")
# Update local transforms for all entities
scene.update_local_transform()
sun.update_local_transform()
planet.update_local_transform()
moon.update_local_transform()

# Then update world transforms starting from the root
scene.update_world_transform()

# Print matrices
print_matrix(scene.name, scene.world_matrix)
print_matrix(sun.name, sun.world_matrix)
print_matrix(planet.name, planet.world_matrix)
print_matrix(moon.name, moon.world_matrix)

# Print world positions
print("\nWorld Positions:")
print_position(scene.name, scene.world_matrix)
print_position(sun.name, sun.world_matrix)
print_position(planet.name, planet.world_matrix)
print_position(moon.name, moon.world_matrix)

# Second approach: use the combined update_transform method
print("\n=== Approach 2: Combined update_transform method ===")

# Change some transforms to verify updates work
sun.add_component("Transform", make_transform(pos=(15.0, 0.0, 0.0)))
planet.add_component("Transform", make_transform(pos=(7.0, 0.0, 0.0), rot=(0, 20, 0)))

# Update using the combined method - just call on the root
scene.update_transform()

# Print updated world matrices
print_matrix(scene.name, scene.world_matrix)
print_matrix(sun.name, sun.world_matrix)
print_matrix(planet.name, planet.world_matrix)
print_matrix(moon.name, moon.world_matrix)

# Print updated positions
print("\nUpdated World Positions:")
print_position(scene.name, scene.world_matrix)
print_position(sun.name, sun.world_matrix)
print_position(planet.name, planet.world_matrix)
print_position(moon.name, moon.world_matrix)

# Third approach: direct matrix manipulation to verify it works as expected
print("\n=== Approach 3: Manual matrix verification ===")

# Create test matrices
root_matrix = np.identity(4, dtype=np.float32)
root_matrix[0:3, 3] = [0.0, 0.0, 0.0]  # Set translation component

sun_local = np.identity(4, dtype=np.float32)
sun_local[0:3, 3] = [15.0, 0.0, 0.0]   # Set translation component

planet_local = np.identity(4, dtype=np.float32)
planet_local[0:3, 3] = [7.0, 0.0, 0.0]  # Set translation component
# Apply rotation around Y axis (20 degrees)
angle = np.radians(20)
planet_local[0, 0] = np.cos(angle)
planet_local[0, 2] = np.sin(angle)
planet_local[2, 0] = -np.sin(angle)
planet_local[2, 2] = np.cos(angle)

moon_local = np.identity(4, dtype=np.float32)
moon_local[0:3, 3] = [2.0, 0.0, 0.0]   # Set translation component

# Calculate world matrices manually for verification
sun_world = np.matmul(root_matrix, sun_local)
planet_world = np.matmul(sun_world, planet_local)
moon_world = np.matmul(planet_world, moon_local)

print("Manually calculated world matrices:")
print_matrix("Root (manual)", root_matrix)
print_matrix("Sun (manual)", sun_world)
print_matrix("Planet (manual)", planet_world)
print_matrix("Moon (manual)", moon_world)

print("\nManually calculated world positions:")
print_position("Root (manual)", root_matrix)
print_position("Sun (manual)", sun_world)
print_position("Planet (manual)", planet_world)
print_position("Moon (manual)", moon_world)