import numpy as np
from OpenGL.GL import *

class MeshData(object):

    def __init__(self):
        
        self.attributes = {}  # Dictionary to store vertex attributes (e.g., positions, colors).
        self.num_vertices = None  # Number of vertices, to be calculated later.
        self.vao_id = None
        self.vbo_id_list = []     

    def add_attr(self, dataType, variableName, data):
    
        self.attributes[variableName] = (dataType, data)

    def count_vert(self):
        # Check if indices attribute exists
        if "indices" in self.attributes:
            self.num_vertices = len(self.attributes["indices"][1])
        else:
            # Fallback to another attribute if available
            if self.attributes:
                some_attr = next(iter(self.attributes.values()))
                self.num_vertices = len(some_attr[1])

    def apply_mat(self, matrix, variable_name="v_pos"):
        # Get data with proper accessing
        pos_data = self.attributes[variable_name][1]
        
        # Transform positions
        ones = np.ones((len(pos_data), 1))
        homo = np.hstack((np.array(pos_data), ones))
        transformed = (matrix @ homo.T).T[:, :3]
        self.attributes[variable_name] = (self.attributes[variable_name][0], transformed.tolist())

        # Extract rotation matrix
        rot_matrix = np.array(matrix)[:3, :3]

        # Transform normals if they exist
        if "v_norm" in self.attributes:
            v_norm_data = self.attributes["v_norm"][1]
            transformed_v_norm = (rot_matrix @ np.array(v_norm_data).T).T.tolist()
            self.attributes["v_norm"] = (self.attributes["v_norm"][0], transformed_v_norm)
        
        if "f_norm" in self.attributes:
            f_norm_data = self.attributes["f_norm"][1]
            transformed_f_norm = (rot_matrix @ np.array(f_norm_data).T).T.tolist()
            self.attributes["f_norm"] = (self.attributes["f_norm"][0], transformed_f_norm)

    def merge(self, otherGeometry):

        for variableName, attributeObject in self.attributes.items():
            attributeObject.data += otherGeometry.attributes[variableName].data  # Append data.
            attributeObject.uploadData()
        self.count_vert()
        
    def gpu_load(self):
        # Create vertex array object
        self.vao_id = glGenVertexArrays(1)
        glBindVertexArray(self.vao_id)
        
        # Check if required attributes exist
        if "v_pos" not in self.attributes or "color" not in self.attributes or "indices" not in self.attributes:
            print("Error: Required attributes missing")
            return
        
        # Position buffer
        vbo_id = glGenBuffers(1)
        self.vbo_id_list.append(vbo_id)
        position_data = np.array(self.attributes["v_pos"][1], dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
        glBufferData(GL_ARRAY_BUFFER, position_data, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, None)
        
        # Color buffer
        vbo_id = glGenBuffers(1)
        self.vbo_id_list.append(vbo_id)
        color_data = np.array(self.attributes["color"][1], dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
        glBufferData(GL_ARRAY_BUFFER, color_data, GL_STATIC_DRAW)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, False, 0, None)
        
        # Vertex Normal buffer
        vbo_id = glGenBuffers(1)
        self.vbo_id_list.append(vbo_id)
        vertex_norm = np.array(self.attributes["v_norm"][1], dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
        glBufferData(GL_ARRAY_BUFFER, vertex_norm, GL_STATIC_DRAW)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, False, 0, None)
        
        # Face Normal buffer
        vbo_id = glGenBuffers(1)
        self.vbo_id_list.append(vbo_id)
        face_norm = np.array(self.attributes["f_norm"][1], dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
        glBufferData(GL_ARRAY_BUFFER, face_norm, GL_STATIC_DRAW)
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 3, GL_FLOAT, False, 0, None)
        
        # Vertex UV buffer
        vbo_id = glGenBuffers(1)
        self.vbo_id_list.append(vbo_id)
        vertex_norm = np.array(self.attributes["v_norm"][1], dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
        glBufferData(GL_ARRAY_BUFFER, vertex_norm, GL_STATIC_DRAW)
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(4, 2, GL_FLOAT, False, 0, None)
        
        # Indices buffer
        vbo_id = glGenBuffers(1)
        self.vbo_id_list.append(vbo_id)
        indices_data = np.array(self.attributes["indices"][1], dtype=np.int32)  # Fixed spelling
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo_id)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices_data, GL_STATIC_DRAW)  # Corrected buffer type
        
        
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        
    def del_buffers(self):
        # Only delete if buffers exist
        if self.vbo_id_list:
            for buffer in self.vbo_id_list:
                glDeleteBuffers(1, [buffer])
            self.vbo_id_list = []
        
        if self.vao_id is not None:
            glDeleteVertexArrays(1, [self.vao_id])
            self.vao_id = None

