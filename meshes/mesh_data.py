import numpy as np
from OpenGL.GL import *
from typing import Dict, Tuple, List, Union, Optional, Any
from core.logger import logger  # Import the custom project logger

class MeshData:
    """
    Manages 3D mesh data for OpenGL rendering.
    
    Handles storage of vertex attributes (positions, colors, normals, etc.),
    transformations, and GPU buffer management.
    """

    def __init__(self):
        """Initialize an empty mesh data container."""
        self.attributes: Dict[str, Tuple[int, List]] = {}  # Dictionary to store vertex attributes
        self.num_vertices: Optional[int] = None  # Number of vertices
        self.vao_id: Optional[int] = None  # Vertex Array Object ID
        self.vbo_id_list: List[int] = []  # List of Vertex Buffer Object IDs
        # Map attribute names to their shader locations
        self.attr_locations = {
            "v_pos": 0,
            "color": 1,
            "v_norm": 2,
            "f_norm": 3,
            "v_uv": 2 
        }

    def add_attr(self, data_type: Union[int, str], variable_name: str, data: List) -> None:
        """
        Add a vertex attribute to the mesh.
        
        Args:
            data_type: Data type ("vec2", "vec3", "uint") or OpenGL constant (GL_FLOAT, etc.)
            variable_name: Name of the attribute (e.g., "v_pos", "color")
            data: List of attribute data
        """
        # Convert string types to OpenGL constants if needed
        gl_type = data_type
        if isinstance(data_type, str):
            if data_type in ["vec2", "vec3", "float"]:
                gl_type = GL_FLOAT
            elif data_type in ["uint", "int"]:
                gl_type = GL_UNSIGNED_INT
        
        self.attributes[variable_name] = (gl_type, data)
        
    def count_vert(self) -> None:
        """Calculate the number of vertices in the mesh."""
        if "indices" in self.attributes:
            self.num_vertices = len(self.attributes["indices"][1])
        else:
            # Fallback to another attribute if available
            if self.attributes:
                some_attr = next(iter(self.attributes.values()))
                self.num_vertices = len(some_attr[1])
            else:
                self.num_vertices = 0
                
    def get_triangles(self):
        """
        Retrieves triangles from the vertex data by grouping consecutive vertices.

        Returns:
            list: A list of triangles, where each triangle is a tuple of three vertices.
        """
        vertex_positions = self.attributes["v_pos"].data
        triangles = []

        # Group every 3 vertices to form triangles.
        for i in range(0, len(vertex_positions), 3):
            v0 = vertex_positions[i]
            v1 = vertex_positions[i + 1]
            v2 = vertex_positions[i + 2]
            triangles.append((v0, v1, v2))

        return triangles
                
    def apply_mat(self, matrix: np.ndarray, variable_name: str = "v_pos") -> None:
        """
        Apply a transformation matrix to mesh vertices and normals.
        Handles normals correctly using the inverse transpose for non-uniform scaling.
        
        Args:
            matrix: 4x4 transformation matrix (Column-Major)
            variable_name: Name of the position attribute (default: "v_pos")
        """
        if variable_name not in self.attributes:
            logger.log_message(f"Cannot apply matrix, {variable_name} attribute not found", level="WARNING")
            return
            
        # Get position data
        pos_data = self.attributes[variable_name][1]
        
        # Transform positions (Correct for Column-Major)
        pos_array = np.array(pos_data)
        ones = np.ones((len(pos_array), 1))
        homo = np.hstack((pos_array, ones)) # Nx4
        # matrix (4x4) @ homo.T (4xN) -> 4xN -> .T -> Nx4 -> [:,:3] -> Nx3
        transformed = (matrix @ homo.T).T[:, :3]
        self.attributes[variable_name] = (self.attributes[variable_name][0], transformed.tolist())

        # --- Correct Normal Transformation ---
        # Extract upper-left 3x3 matrix
        mat33 = matrix[:3, :3]
        try:
            # Calculate inverse transpose for normal transformation
            inv_transpose_mat33 = np.linalg.inv(mat33).T
            
            # Transform vertex normals if they exist
            if "v_norm" in self.attributes:
                v_norm_data = self.attributes["v_norm"][1]
                v_norm_array = np.array(v_norm_data) # Nx3
                # inv_transpose_mat33 (3x3) @ v_norm_array.T (3xN) -> 3xN -> .T -> Nx3
                transformed_v_norm = (inv_transpose_mat33 @ v_norm_array.T).T
                # Renormalize normals after transformation
                norms = np.linalg.norm(transformed_v_norm, axis=1, keepdims=True)
                # Avoid division by zero for zero-length normals
                valid_norms = norms > 1e-8 
                transformed_v_norm[valid_norms] /= norms[valid_norms]
                self.attributes["v_norm"] = (self.attributes["v_norm"][0], transformed_v_norm.tolist())
            
            # Transform face normals if they exist
            if "f_norm" in self.attributes:
                f_norm_data = self.attributes["f_norm"][1]
                f_norm_array = np.array(f_norm_data) # Nx3
                # inv_transpose_mat33 (3x3) @ f_norm_array.T (3xN) -> 3xN -> .T -> Nx3
                transformed_f_norm = (inv_transpose_mat33 @ f_norm_array.T).T
                # Renormalize normals
                norms = np.linalg.norm(transformed_f_norm, axis=1, keepdims=True)
                valid_norms = norms > 1e-8
                transformed_f_norm[valid_norms] /= norms[valid_norms]
                self.attributes["f_norm"] = (self.attributes["f_norm"][0], transformed_f_norm.tolist())

        except np.linalg.LinAlgError:
            logger.log_message("Matrix has no inverse, cannot transform normals correctly.", level="WARNING")
            # Optionally skip normal transformation or use the original matrix as a fallback
            # Fallback (less accurate for non-uniform scale):
            # rot_matrix = mat33
            # ... apply rot_matrix as before ...

    def merge(self, other_geometry) -> None:
        """
        Merge another MeshData object into this one.
        
        Args:
            other_geometry: Another MeshData object to merge with this one
        """
        # First, validate both meshes have the same attributes
        for var_name in self.attributes:
            if var_name not in other_geometry.attributes:
                logger.log_message(f"Cannot merge, attribute {var_name} missing from other geometry", level="ERROR")
                return
                
        # Merge each attribute
        for var_name, (data_type, data) in self.attributes.items():
            other_data_type, other_data = other_geometry.attributes[var_name]
            
            if data_type != other_data_type:
                logger.log_message(f"Data type mismatch for {var_name}, using original type", level="WARNING")
                
            # Special handling for indices when merging
            if var_name == "indices" and "v_pos" in self.attributes:
                # Offset indices by the number of vertices in the first mesh
                vertex_count = len(self.attributes["v_pos"][1])
                adjusted_indices = [idx + vertex_count for idx in other_data]
                merged_data = data + adjusted_indices
            else:
                merged_data = data + other_data
                
            self.attributes[var_name] = (data_type, merged_data)
            
        self.count_vert()
        
        # If already loaded to GPU, reload with new data
        if self.vao_id is not None:
            self.del_buffers()
            self.gpu_load()
        
    def gpu_load(self) -> bool:
        """
        Upload mesh data to the GPU.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check for required attributes
            required_attrs = ["v_pos", "indices"]
            for attr in required_attrs:
                if attr not in self.attributes:
                    logger.log_message(f"Required attribute '{attr}' missing", level="ERROR")
                    return False
            
            # Create vertex array object
            self.vao_id = glGenVertexArrays(1)
            glBindVertexArray(self.vao_id)
            
            # Process position data (required)
            self._load_attribute_buffer("v_pos", 3)
            
            # Process optional attributes
            optional_attrs = {
                "color": 3,
                "v_norm": 3,
                "f_norm": 3,
                "v_uv": 2
            }
            
            for attr_name, components in optional_attrs.items():
                if attr_name in self.attributes:
                    self._load_attribute_buffer(attr_name, components)
            
            # Process indices (required)
            vbo_id = glGenBuffers(1)
            self.vbo_id_list.append(vbo_id)
            indices_data = np.array(self.attributes["indices"][1], dtype=np.uint32)  
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo_id)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices_data, GL_STATIC_DRAW)
            
            # Unbind
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindVertexArray(0)
            
            logger.log_message(f"Mesh loaded to GPU with {self.num_vertices} vertices", level="INFO")
            return True
            
        except Exception as e:
            logger.log_error(e, context="Error during GPU loading of mesh data")
            self.del_buffers()  # Clean up any partial resources
            return False
    
    def _load_attribute_buffer(self, attr_name: str, components: int) -> None:
        """
        Helper method to load a specific attribute buffer.
        
        Args:
            attr_name: Name of the attribute
            components: Number of components per vertex (e.g., 3 for positions/normals, 2 for UVs)
        """
        if attr_name not in self.attributes:
            return
            
        data_type, data = self.attributes[attr_name]
        location = self.attr_locations.get(attr_name, -1)
        
        if location < 0:
            logger.log_message(f"No shader location defined for attribute '{attr_name}'", level="WARNING")
            return
            
        vbo_id = glGenBuffers(1)
        self.vbo_id_list.append(vbo_id)
        
        attribute_data = np.array(data, dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
        glBufferData(GL_ARRAY_BUFFER, attribute_data, GL_STATIC_DRAW)
        glEnableVertexAttribArray(location)
        glVertexAttribPointer(location, components, GL_FLOAT, False, 0, None)
        
    def del_buffers(self) -> None:
        """Delete OpenGL buffers safely if they exist."""
        try:
            # Check if OpenGL functions are available before calling them
            if bool(glDeleteBuffers) and hasattr(self, 'vbo_id_list') and self.vbo_id_list:
                glDeleteBuffers(len(self.vbo_id_list), self.vbo_id_list)
                self.vbo_id_list = []
                
            if bool(glDeleteVertexArrays) and hasattr(self, 'vao_id') and self.vao_id:
                glDeleteVertexArrays(1, [self.vao_id])
                self.vao_id = None
        except Exception as e:
            print(f"Warning: Error during buffer cleanup: {e}")

