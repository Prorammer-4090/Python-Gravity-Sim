from meshes.mesh_data import MeshData
from math import sin, cos, pi
from OpenGL.GL import *

class PolygonGeometry(MeshData):
    """
    A flat polygon geometry with the specified number of sides.
    """

    def __init__(self, sides=3, radius=1):
        """
        Initialize a regular polygon geometry.
        
        Args:
            sides (int): Number of sides in the polygon
            radius (float): Radius of the polygon
        """
        super().__init__()

        # Calculate angle increment between vertices
        angle = 2 * pi / sides
        
        # Initialize data arrays
        position_data = []
        color_data = []
        uv_data = []
        normal_data = []
        indices = []
        
        # Normal vector for the entire polygon (facing +Z direction)
        normal_vector = [0, 0, 1]
        uv_center = [0.5, 0.5]  # Center point for UV mapping

        # Add center vertex first (shared by all triangles)
        position_data.append([0, 0, 0])  # Center point
        color_data.append([1, 1, 1])     # White for center
        uv_data.append(uv_center)        # Center UV
        normal_data.append(normal_vector)

        # Add vertices around the circumference
        for i in range(sides):
            # Calculate vertex position
            x = radius * cos(i * angle)
            y = radius * sin(i * angle)
            
            # Add vertex data
            position_data.append([x, y, 0])
            
            # Alternate colors for visual distinction
            color = [1, 0, 0] if i % 2 == 0 else [0, 0, 1]
            color_data.append(color)
            
            # Calculate UV coordinates (transform from [-1,1] to [0,1] range)
            uv_data.append([cos(i * angle) * 0.5 + 0.5, sin(i * angle) * 0.5 + 0.5])
            
            # Add normal vector (all facing in +Z direction)
            normal_data.append(normal_vector)
            
            # Create triangle from center to current vertex and next vertex
            current = i + 1
            next_vertex = (i + 1) % sides + 1  # +1 because index 0 is center
            
            indices.extend([0, current, next_vertex])

        # Add attribute data to geometry
        self.add_attr("vec2", "v_uv", uv_data)
        self.add_attr("vec3", "v_pos", position_data)
        self.add_attr("vec3", "color", color_data)
        self.add_attr("vec3", "v_norm", normal_data)
        self.add_attr("vec3", "f_norm", normal_data)  # Same as vertex normals for flat surface
        self.add_attr("uint", "indices", indices)

        self.count_vert()