from geometry.geometry import Geometry
import numpy as np


class ParametricGeometry(Geometry):
    """
    A class for creating parametric geometries based on a surface function.
    It extends the Geometry class to generate vertices, colors, UV coordinates,
    and both face and vertex normal vectors from a parametric surface function.
    """

    def __init__(self, u_min, u_max, u_segments, v_min, v_max, v_segments, surface_fn):
        """
        Initializes a parametric geometry by sampling a surface function.

        Params:
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

        # Build triangles
        for u_idx in range(u_segments):
            for v_idx in range(v_segments):
                # Get vertices for current quad
                p1 = vertices[u_idx][v_idx]
                p2 = vertices[u_idx + 1][v_idx]
                p3 = vertices[u_idx + 1][v_idx + 1]
                p4 = vertices[u_idx][v_idx + 1]

                # Get corresponding vertex normals
                n1 = vertex_normal_grid[u_idx][v_idx]
                n2 = vertex_normal_grid[u_idx + 1][v_idx]
                n3 = vertex_normal_grid[u_idx + 1][v_idx + 1]
                n4 = vertex_normal_grid[u_idx][v_idx + 1]

                # Calculate face normals for both triangles
                fn1 = calculate_face_normal(p1, p2, p3)
                fn2 = calculate_face_normal(p1, p3, p4)

                # Get UV coordinates
                uv1 = uv_coords[u_idx][v_idx]
                uv2 = uv_coords[u_idx + 1][v_idx]
                uv3 = uv_coords[u_idx + 1][v_idx + 1]
                uv4 = uv_coords[u_idx][v_idx + 1]

                # Add data for first triangle (p1, p2, p3)
                vertex_positions.extend([p1, p2, p3])
                vertex_colors.extend([colors[0], colors[1], colors[2]])
                vertex_uvs.extend([uv1, uv2, uv3])
                vertex_normals.extend([n1, n2, n3])
                face_normals.extend([fn1, fn1, fn1])

                # Add data for second triangle (p1, p3, p4)
                vertex_positions.extend([p1, p3, p4])
                vertex_colors.extend([colors[3], colors[4], colors[5]])
                vertex_uvs.extend([uv1, uv3, uv4])
                vertex_normals.extend([n1, n3, n4])
                face_normals.extend([fn2, fn2, fn2])

        # Add attributes to geometry
        self.addAttribute("vec2", "vertexUV", vertex_uvs)
        self.addAttribute("vec3", "vertexPosition", vertex_positions)
        self.addAttribute("vec3", "vertexColor", vertex_colors)
        self.addAttribute("vec3", "vertexNormal", vertex_normals)
        self.addAttribute("vec3", "faceNormal", face_normals)

        self.countVertices()