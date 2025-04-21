from meshes.mesh_data import MeshData
import math
from OpenGL.GL import *


class PolyhedronGeometry(MeshData):
    """
    A class for creating regular polyhedron geometries (tetrahedron, octahedron, etc.).

    Can create base polyhedra and optionally subdivide faces for smoother shapes.
    """

    def __init__(self, radius=1.0, polyhedron_type="tetrahedron", subdivisions=0):
        """
        Initialize a polyhedron geometry.

        Args:
            radius (float): Radius of the circumscribed sphere
            polyhedron_type (str): Type of polyhedron ('tetrahedron', 'octahedron', 'cube',
                                   'icosahedron', or 'dodecahedron')
            subdivisions (int): Number of times to subdivide faces (0 = no subdivision)
        """
        super().__init__()

        # Get base polyhedron vertices and faces
        vertices, faces = self.get_base_polyhedron(polyhedron_type)

        # Normalize vertices to unit length
        vertices = [self.normalize(v) for v in vertices]

        # Perform requested subdivisions
        for _ in range(subdivisions):
            vertices, faces = self.subdivide_faces(vertices, faces)

        # Scale vertices by radius
        vertices = [[radius * coord for coord in vertex] for vertex in vertices]

        # Calculate vertex normals for smooth shading
        vertex_normals = self.calculate_vertex_normals(vertices, faces)

        # Calculate UV coordinates for each vertex
        uv_coords = [self.calculate_uv(self.normalize(v)) for v in vertices]

        # Calculate face normals and build face attributes
        face_normals = []
        for face in faces:
            v0, v1, v2 = [vertices[i] for i in face]
            e1 = [v1[i] - v0[i] for i in range(3)]
            e2 = [v2[i] - v0[i] for i in range(3)]
            normal = self.normalize(self.cross_product(e1, e2))
            
            # Ensure normal points outward
            center = [(v0[i] + v1[i] + v2[i]) / 3 for i in range(3)]
            if self.dot_product(center, normal) < 0:
                normal = [-n for n in normal]
                
            face_normals.append(normal)

        # Define a simple color scheme based on faces
        C1, C2, C3 = [1, 0, 0], [0, 1, 0], [0, 0, 1]
        C4, C5, C6 = [0, 1, 1], [1, 0, 1], [1, 1, 0]
        default_colors = [C1, C2, C3, C4, C5, C6]
        
        # Assign a color to each vertex based on its face
        vertex_colors = []
        for i in range(len(vertices)):
            # Find a face containing this vertex and use its color
            for f_idx, face in enumerate(faces):
                if i in face:
                    color_idx = f_idx % len(default_colors)
                    vertex_colors.append(default_colors[color_idx])
                    break
            else:
                # Fallback if vertex isn't in any face
                vertex_colors.append([0.7, 0.7, 0.7])
                
        # Create face normal array matching vertex count
        expanded_face_normals = []
        for face_idx, face in enumerate(faces):
            for _ in face:
                expanded_face_normals.append(face_normals[face_idx])

        # Add attribute data to geometry with proper types
        self.add_attr("vec3", "v_pos", vertices)
        self.add_attr("vec3", "color", vertex_colors)
        self.add_attr("vec2", "v_uv", uv_coords)
        self.add_attr("vec3", "v_norm", vertex_normals)
        self.add_attr("vec3", "f_norm", vertex_normals)  # Using vertex normals for smooth shading
        
        # Flatten faces into a single index array
        indices = []
        for face in faces:
            indices.extend(face)
            
        self.add_attr("uint", "indices", indices)
        
        self.count_vert()

    def calculate_uv(self, normalized_vertex):
        """
        Calculate UV coordinates using spherical projection.
        
        Args:
            normalized_vertex (list): Normalized vertex coordinates [x, y, z]
            
        Returns:
            list: UV coordinates [u, v]
        """
        x, y, z = normalized_vertex

        # Calculate spherical coordinates
        u = 0.5 + (math.atan2(x, z) / (2 * math.pi))
        v = 0.5 + (math.asin(y) / math.pi)

        return [u, v]

    def calculate_vertex_normals(self, vertices, faces):
        """
        Calculate smooth vertex normals by averaging face normals.
        
        Args:
            vertices (list): List of vertex positions
            faces (list): List of face indices
            
        Returns:
            list: List of normal vectors for each vertex
        """
        # Initialize normal accumulation arrays
        vertex_normals = [[0, 0, 0] for _ in vertices]
        vertex_counts = [0] * len(vertices)

        # Accumulate face normals for each vertex
        for face in faces:
            v0 = vertices[face[0]]
            v1 = vertices[face[1]]
            v2 = vertices[face[2]]

            # Calculate face normal
            e1 = [v1[i] - v0[i] for i in range(3)]
            e2 = [v2[i] - v0[i] for i in range(3)]
            face_normal = self.normalize(self.cross_product(e1, e2))
            
            # Ensure normal points outward (away from origin)
            # Calculate face center
            center = [(v0[i] + v1[i] + v2[i]) / 3 for i in range(3)]
            
            # If dot product is negative, the normal points inward, so flip it
            if self.dot_product(center, face_normal) < 0:
                face_normal = [-n for n in face_normal]

            # Add face normal to each vertex's accumulated normal
            for vertex_index in face:
                vertex_normals[vertex_index] = [
                    vertex_normals[vertex_index][i] + face_normal[i]
                    for i in range(3)
                ]
                vertex_counts[vertex_index] += 1

        # Average and normalize the accumulated normals
        for i in range(len(vertices)):
            if vertex_counts[i] > 0:
                vertex_normals[i] = self.normalize([
                    coord / vertex_counts[i] for coord in vertex_normals[i]
                ])
            else:
                # If a vertex isn't used in any face, use its position as normal
                vertex_normals[i] = self.normalize(vertices[i])

        return vertex_normals

    def get_base_polyhedron(self, polyhedron_type):
        """
        Get the base vertices and faces for the specified polyhedron type.
        
        Args:
            polyhedron_type (str): Type of polyhedron
            
        Returns:
            tuple: (vertices, faces) lists
        """
        if polyhedron_type == "tetrahedron":
            t = (1.0 + math.sqrt(2.0)) / 2.0
            vertices = [
                [-1, -t, 0], [1, -t, 0], [0, 1, t], [0, 1, -t]
            ]
            faces = [
                [2, 1, 0], [2, 3, 1], [0, 3, 2], [1, 3, 0]
            ]

        elif polyhedron_type == "octahedron":
            vertices = [
                [1, 0, 0], [-1, 0, 0], [0, 1, 0],
                [0, -1, 0], [0, 0, 1], [0, 0, -1]
            ]
            faces = [
                [4, 0, 2], [4, 2, 1], [4, 1, 3], [4, 3, 0],
                [5, 2, 0], [5, 1, 2], [5, 3, 1], [5, 0, 3]
            ]

        elif polyhedron_type == "cube":
            vertices = [
                [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
            ]
            faces = [
                [0, 2, 1], [0, 3, 2],  # front
                [4, 5, 7], [5, 6, 7],  # back
                [0, 4, 7], [0, 7, 3],  # left
                [1, 2, 6], [1, 6, 5],  # right
                [3, 7, 6], [3, 6, 2],  # top
                [0, 1, 5], [0, 5, 4]  # bottom
            ]

        elif polyhedron_type == "icosahedron":
            t = (1.0 + math.sqrt(5.0)) / 2.0
            vertices = [
                [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
                [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
                [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]
            ]
            faces = [
                [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
                [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
                [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
                [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
            ]

        elif polyhedron_type == "dodecahedron":
            phi = (1 + math.sqrt(5)) / 2
            vertices = [
                [0, 0, 1.070466], [.7136442, 0, .7978784], [-.3568221, .618034, .7978784],
                [-.3568221, -.618034, .7978784], [.7978784, .618034, .3568221],
                [.7978784, -.618034, .3568221], [-.9341724, .381966, .3568221],
                [.1362939, 1, .3568221], [.1362939, -1, .3568221],
                [-.9341724, -.381966, .3568221], [.9341724, .381966, -.3568221],
                [.9341724, -.381966, -.3568221], [-.7978784, .618034, -.3568221],
                [-.1362939, 1, -.3568221], [-.1362939, -1, -.3568221],
                [-.7978784, -.618034, -.3568221], [.3568221, .618034, -.7978784],
                [.3568221, -.618034, -.7978784], [-.7136442, 0, -.7978784],
                [0, 0, -1.070466]
            ]

            # Convert pentagonal faces to triangles
            pentagon_faces = [
                [0, 1, 4, 7, 2], [0, 2, 6, 9, 3], [0, 3, 8, 5, 1],
                [1, 5, 11, 10, 4], [2, 7, 13, 12, 6], [3, 9, 15, 14, 8],
                [4, 10, 16, 13, 7], [5, 8, 14, 17, 11], [6, 12, 18, 15, 9],
                [10, 11, 17, 19, 16], [12, 13, 16, 19, 18], [14, 15, 18, 19, 17]
            ]

            # Convert pentagons to triangles
            faces = []
            for pentagon in pentagon_faces:
                faces.extend([
                    [pentagon[0], pentagon[1], pentagon[2]],
                    [pentagon[0], pentagon[2], pentagon[3]],
                    [pentagon[0], pentagon[3], pentagon[4]]
                ])
        else:
            raise ValueError(
                "Polyhedron type must be 'tetrahedron', 'octahedron', 'cube', 'icosahedron', or 'dodecahedron'")

        return vertices, faces

    def normalize(self, vector):
        """
        Normalize a vector to unit length.
        
        Args:
            vector (list): Vector to normalize
            
        Returns:
            list: Normalized vector
        """
        length = math.sqrt(sum(coord * coord for coord in vector))
        if length < 1e-8:
            return vector
        return [coord / length for coord in vector]

    def cross_product(self, a, b):
        """
        Calculate the cross product of two vectors.
        
        Args:
            a (list): First vector
            b (list): Second vector
            
        Returns:
            list: Cross product of a and b
        """
        return [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        ]

    def dot_product(self, a, b):
        """
        Calculate the dot product of two vectors.
        
        Args:
            a (list): First vector
            b (list): Second vector
            
        Returns:
            float: Dot product of a and b
        """
        return sum(a[i] * b[i] for i in range(3))

    def midpoint(self, v1, v2):
        """
        Calculate the midpoint between two vectors.
        
        Args:
            v1 (list): First vector
            v2 (list): Second vector
            
        Returns:
            list: Midpoint between v1 and v2
        """
        return [(a + b) / 2 for a, b in zip(v1, v2)]

    def subdivide_faces(self, vertices, faces):
        """
        Subdivide each face into four smaller faces.
        
        Args:
            vertices (list): List of vertex positions
            faces (list): List of face indices
            
        Returns:
            tuple: (new_vertices, new_faces) lists
        """
        new_vertices = vertices.copy()
        new_faces = []
        midpoint_cache = {}

        def get_midpoint_index(v1_idx, v2_idx):
            """Get or create the index of the midpoint between two vertices."""
            smaller, larger = sorted((v1_idx, v2_idx))
            key = (smaller, larger)

            if key in midpoint_cache:
                return midpoint_cache[key]

            v1 = vertices[v1_idx]
            v2 = vertices[v2_idx]
            midpoint = self.normalize(self.midpoint(v1, v2))
            new_vertices.append(midpoint)
            midpoint_index = len(new_vertices) - 1
            midpoint_cache[key] = midpoint_index

            return midpoint_index

        for face in faces:
            v1, v2, v3 = face

            # Get midpoints
            a = get_midpoint_index(v1, v2)
            b = get_midpoint_index(v2, v3)
            c = get_midpoint_index(v3, v1)

            # Create four new triangles with consistent winding order
            new_faces.extend([
                [v1, a, c],  # Corner triangle 1
                [v2, b, a],  # Corner triangle 2
                [v3, c, b],  # Corner triangle 3
                [a, b, c]  # Center triangle
            ])

        return new_vertices, new_faces