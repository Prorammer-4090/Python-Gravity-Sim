from meshes.mesh_data import MeshData
import numpy as np


class ParametricGeometry(MeshData):
    """
    A class for creating parametric geometries based on a surface function.
    It extends the MeshData class to generate vertices, colors, UV coordinates,
    and both face and vertex normal vectors from a parametric surface function.
    """

    def __init__(self, u_min, u_max, u_segments, v_min, v_max, v_segments, surface_fn):
        """
        Initializes a parametric geometry by sampling a surface function.

        Args:
            u_min (float): Minimum value of the u parameter
            u_max (float): Maximum value of the u parameter
            u_segments (int): Number of subdivisions along the u direction
            v_min (float): Minimum value of the v parameter
            v_max (float): Maximum value of the v parameter
            v_segments (int): Number of subdivisions along the v direction
            surface_fn (function): A function that takes (u, v) and returns a 3D point [x, y, z]
        """
        super().__init__()

        # Calculate step sizes
        u_step = (u_max - u_min) / u_segments
        v_step = (v_max - v_min) / v_segments

        # Generate vertices grid
        vertices = [[surface_fn(u_min + i * u_step, v_min + j * v_step)
                     for j in range(v_segments + 1)]
                    for i in range(u_segments + 1)]

        # Generate UV coordinates
        uv_coords = [[[i / u_segments, j / v_segments]
                      for j in range(v_segments + 1)]
                     for i in range(u_segments + 1)]

        # Initialize arrays for final data
        vertex_positions = []
        vertex_colors = []
        vertex_uvs = []
        vertex_normals = []
        face_normals = []
        indices = []

        # Default color palette
        colors = [[1, 0, 0], [0, 1, 0], [0, 0, 1],
                  [1, 1, 0], [0, 1, 1], [1, 0, 1]]

        def calculate_surface_normal(u, v, h):
            """Calculate surface normal using partial derivatives."""
            # Calculate partial derivatives using central differences
            du = h * u_step
            dv = h * v_step

            # Points for partial derivatives
            p_center = np.array(surface_fn(u, v))
            p_du_plus = np.array(surface_fn(u + du, v))
            p_du_minus = np.array(surface_fn(u - du, v))
            p_dv_plus = np.array(surface_fn(u, v + dv))
            p_dv_minus = np.array(surface_fn(u, v - dv))

            # Compute partial derivatives using central differences
            du_vector = (p_du_plus - p_du_minus) / (2 * du)
            dv_vector = (p_dv_plus - p_dv_minus) / (2 * dv)

            # Calculate normal through cross product
            normal = np.cross(du_vector, dv_vector)
            norm = np.linalg.norm(normal)

            # Handle degenerate cases
            if norm < 1e-8:
                # Fall back to normalized position vector if surface normal is degenerate
                return p_center / np.linalg.norm(p_center) if np.linalg.norm(p_center) > 1e-8 else np.array([0, 1, 0])

            return normal / norm

        def calculate_face_normal(p1, p2, p3):
            """Calculate face normal from three vertices."""
            v1 = np.array(p2) - np.array(p1)
            v2 = np.array(p3) - np.array(p1)
            normal = np.cross(v1, v2)
            norm = np.linalg.norm(normal)

            if norm < 1e-8:
                # If the face normal is degenerate, return a default normal
                return np.array([0, 1, 0])

            return normal / norm

        # Pre-calculate vertex normals
        vertex_normal_grid = []
        for u_idx in range(u_segments + 1):
            normal_row = []
            u = u_min + u_idx * u_step
            for v_idx in range(v_segments + 1):
                v = v_min + v_idx * v_step
                normal = calculate_surface_normal(u, v, 0.01)  # Adaptive step size
                normal_row.append(normal)
            vertex_normal_grid.append(normal_row)

        # Create indexed geometry data
        # First, add all vertices to arrays - we'll reference them by indices
        for u_idx in range(u_segments + 1):
            for v_idx in range(v_segments + 1):
                # Get vertex data
                position = vertices[u_idx][v_idx]
                uv = uv_coords[u_idx][v_idx]
                normal = vertex_normal_grid[u_idx][v_idx]
                
                # Add data to arrays
                vertex_positions.append(position)
                vertex_uvs.append(uv)
                vertex_normals.append(normal)
                
                # Alternate colors for visual distinction
                color_idx = (u_idx + v_idx) % len(colors)
                vertex_colors.append(colors[color_idx])

        # Calculate face normals for the quads
        quad_face_normals = []
        for u_idx in range(u_segments):
            row_normals = []
            for v_idx in range(v_segments):
                # Get vertices for current quad
                p1 = vertices[u_idx][v_idx]
                p2 = vertices[u_idx + 1][v_idx]
                p3 = vertices[u_idx + 1][v_idx + 1]
                
                # Calculate face normal
                face_normal = calculate_face_normal(p1, p2, p3)
                row_normals.append(face_normal)
            quad_face_normals.append(row_normals)

        # Generate face data with proper indices
        for u_idx in range(u_segments):
            for v_idx in range(v_segments):
                # Calculate the indices of the four corners of each grid cell
                i0 = u_idx * (v_segments + 1) + v_idx
                i1 = (u_idx + 1) * (v_segments + 1) + v_idx
                i2 = (u_idx + 1) * (v_segments + 1) + (v_idx + 1)
                i3 = u_idx * (v_segments + 1) + (v_idx + 1)
                
                # Get the face normal for this quad
                face_normal = quad_face_normals[u_idx][v_idx]
                
                # First triangle (i0, i1, i2)
                indices.extend([i0, i1, i2])
                face_normals.extend([face_normal, face_normal, face_normal])
                
                # Second triangle (i0, i2, i3)
                indices.extend([i0, i2, i3])
                face_normals.extend([face_normal, face_normal, face_normal])

        # Add attributes to geometry using the original string type names
        self.add_attr("vec2", "v_uv", vertex_uvs)
        self.add_attr("vec3", "v_pos", vertex_positions)
        self.add_attr("vec3", "color", vertex_colors)
        self.add_attr("vec3", "v_norm", vertex_normals)
        self.add_attr("vec3", "f_norm", face_normals)
        self.add_attr("uint", "indices", indices)

        self.count_vert()