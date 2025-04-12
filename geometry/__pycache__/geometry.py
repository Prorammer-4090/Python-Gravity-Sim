# Resource Used: Developing Graphics Frameworks with Python and OpenGL -- Lee Stemkoski, Michael Pascale
# I added functionality for selection

from core.attribute import Attribute
import math
import numpy

class Geometry(object):
    """
    A class representing geometric data, including vertex attributes, transformations, 
    and operations like merging and subdivision.
    """

    def __init__(self):
        """
        Initializes a Geometry object with no attributes and an undefined vertex count.
        """
        self.attributes = {}  # Dictionary to store vertex attributes (e.g., positions, colors).
        self.vertexCount = None  # Number of vertices, to be calculated later.

    def addAttribute(self, dataType, variableName, data):
        """
        Adds an attribute (e.g., vertex position, color) to the geometry.

        Params:
            dataType (str): The data type of the attribute (e.g., "vec3").
            variableName (str): The name of the attribute (e.g., "vertexPosition").
            data (list): The data for the attribute.
        """
        self.attributes[variableName] = Attribute(dataType, data)

    def countVertices(self):
        """
        Counts the number of vertices in the geometry based on the first attribute.
        Assumes all attributes have the same number of vertices.
        """
        attrib = list(self.attributes.values())[0]  # Get the first attribute.
        self.vertexCount = len(attrib.data)  # Set vertex count based on attribute data.

    def applyMatrix(self, matrix, variableName="vertexPosition"):
        """
        Applies a transformation matrix to the specified attribute.

        Params:
            matrix (numpy.ndarray): The 4x4 transformation matrix.
            variableName (str): The attribute name to apply the matrix to (default is "vertexPosition").
        """
        oldPositionData = self.attributes[variableName].data  # Get current vertex positions.
        newPositionData = []

        for oldPos in oldPositionData:
            newPos = oldPos.copy()
            newPos.append(1)  # Add homogeneous coordinate for matrix multiplication.
            newPos = matrix @ newPos  # Apply the transformation matrix.
            newPos = list(newPos[:3])  # Convert back to 3D coordinates.
            newPositionData.append(newPos)

        self.attributes[variableName].data = newPositionData  # Update the attribute data.
        # extract the rotation submatrix
        rotationMatrix = numpy.array([matrix[0][0:3],
                                      matrix[1][0:3],
                                      matrix[2][0:3]])
        oldVertexNormalData = self.attributes["vertexNormal"].data
        newVertexNormalData = []
        for oldNormal in oldVertexNormalData:
            newNormal = oldNormal.copy()
            newNormal = rotationMatrix @ newNormal
            newVertexNormalData.append(newNormal)

        self.attributes["vertexNormal"].data = newVertexNormalData
        oldFaceNormalData = self.attributes["faceNormal"].data
        newFaceNormalData = []

        for oldNormal in oldFaceNormalData:
            newNormal = oldNormal.copy()
            newNormal = rotationMatrix @ newNormal
            newFaceNormalData.append(newNormal)

        self.attributes["faceNormal"].data = newFaceNormalData
        self.attributes[variableName].uploadData()  # Upload updated data to the GPU.

    def merge(self, otherGeometry):
        """
        Merges another Geometry object into this one by appending its attributes.

        Params:
            otherGeometry (Geometry): The Geometry object to merge with.
        """
        for variableName, attributeObject in self.attributes.items():
            attributeObject.data += otherGeometry.attributes[variableName].data  # Append data.
            attributeObject.uploadData()  # Upload updated data to the GPU.
        self.countVertices()  # Recalculate the vertex count.

    def get_triangles(self):
        """
        Retrieves triangles from the vertex data by grouping consecutive vertices.

        Returns:
            list: A list of triangles, where each triangle is a tuple of three vertices.
        """
        vertex_positions = self.attributes["vertexPosition"].data
        triangles = []

        # Group every 3 vertices to form triangles.
        for i in range(0, len(vertex_positions), 3):
            v0 = vertex_positions[i]
            v1 = vertex_positions[i + 1]
            v2 = vertex_positions[i + 2]
            triangles.append((v0, v1, v2))

        return triangles

    def normalize(self, vector):
        """
        Normalizes a 3D vector to have a length of 1.

        Params:
            vector (list): The vector to normalize.

        Returns:
            list: The normalized vector.
        """
        length = math.sqrt(sum(coord * coord for coord in vector))  # Compute the vector's length.
        if length == 0:
            return vector  # Return the original vector if its length is zero.
        return [coord / length for coord in vector]  # Scale each component by the length.

    def midpoint(self, v1, v2):
        """
        Computes the midpoint between two vectors.

        Params:
            v1 (list): The first vector.
            v2 (list): The second vector.

        Returns:
            list: The midpoint vector.
        """
        return [(a + b) / 2 for a, b in zip(v1, v2)]  # Compute the average of each component.

    def subdivide(self, subdivisions=1, normalize_vertices=True):
        """
        Subdivides the geometry into smaller triangles by adding midpoints to edges.

        Params:
            subdivisions (int): The number of subdivision steps to perform.
            normalize_vertices (bool): Whether to normalize vertex positions (default is True).

        Returns:
            Geometry: The subdivided geometry.
        """
        for _ in range(subdivisions):
            vertices = self.attributes["vertexPosition"].data
            triangles = self.get_triangles()

            new_vertices = vertices.copy()  # Copy existing vertices.
            new_triangles = []  # List to store new triangles.
            midpoint_cache = {}  # Cache for midpoint indices to avoid duplication.

            def get_midpoint_index(v1_idx, v2_idx):
                """
                Retrieves or creates the index of the midpoint between two vertices.

                Params:
                    v1_idx (int): Index of the first vertex.
                    v2_idx (int): Index of the second vertex.

                Returns:
                    int: Index of the midpoint vertex.
                """
                key = tuple(sorted([v1_idx, v2_idx]))  # Create a unique key for the edge.

                if key in midpoint_cache:
                    return midpoint_cache[key]  # Return cached index if available.

                # Compute the midpoint and normalize if needed.
                v1 = vertices[v1_idx]
                v2 = vertices[v2_idx]
                midpoint = self.midpoint(v1, v2)
                if normalize_vertices:
                    midpoint = self.normalize(midpoint)

                new_idx = len(new_vertices)  # Assign a new index for the midpoint.
                new_vertices.append(midpoint)  # Add the midpoint to the vertex list.
                midpoint_cache[key] = new_idx  # Cache the midpoint index.

                return new_idx

            # Subdivide each triangle into 4 smaller triangles.
            for v1, v2, v3 in triangles:
                v1_idx = vertices.index(v1)
                v2_idx = vertices.index(v2)
                v3_idx = vertices.index(v3)

                a = get_midpoint_index(v1_idx, v2_idx)
                b = get_midpoint_index(v2_idx, v3_idx)
                c = get_midpoint_index(v3_idx, v1_idx)

                new_triangles.extend([
                    [v1_idx, a, c],
                    [v2_idx, b, a],
                    [v3_idx, c, b],
                    [a, b, c]
                ])

            # Update vertex position data for the new triangles.
            position_data = [new_vertices[idx] for triangle in new_triangles for idx in triangle]

            # Handle vertex colors, if present.
            if "vertexColor" in self.attributes:
                old_colors = self.attributes["vertexColor"].data
                new_colors = []
                for i in range(0, len(position_data), 3):
                    color_index = (i // 9) % (len(old_colors) // 3)
                    new_colors.extend(old_colors[color_index * 3:(color_index + 1) * 3])
                self.attributes["vertexColor"].data = new_colors
                self.attributes["vertexColor"].uploadData()

            # Update vertex positions and upload to the GPU.
            self.attributes["vertexPosition"].data = position_data
            self.attributes["vertexPosition"].uploadData()
            self.countVertices()  # Recalculate the vertex count.

        return self

