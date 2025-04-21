import numpy as np
from OpenGL.GL import *
from meshes.mesh_data import MeshData
from core.logger import logger

class GridGeometry(MeshData):
    """Generates vertices and indices for a grid on the XZ plane."""
    def __init__(self, size=20, divisions=20):
        super().__init__()
        self.draw_mode = GL_LINES # Set draw mode to lines

        vertices_list = []
        indices_list = []
        index_count = 0
        step = size / divisions
        half_size = size / 2

        for i in range(divisions + 1):
            # Lines parallel to Z-axis
            x = -half_size + i * step
            vertices_list.extend([x, 0, -half_size]) # Start point
            vertices_list.extend([x, 0,  half_size]) # End point
            indices_list.extend([index_count, index_count + 1])
            index_count += 2

            # Lines parallel to X-axis
            z = -half_size + i * step
            vertices_list.extend([-half_size, 0, z]) # Start point
            vertices_list.extend([ half_size, 0, z]) # End point
            indices_list.extend([index_count, index_count + 1])
            index_count += 2

        # Use add_attr to store data correctly
        self.add_attr("vec3", "v_pos", vertices_list)
        self.add_attr("uint", "indices", indices_list) # Use "uint" or GL_UNSIGNED_INT

        # Call count_vert after attributes are added
        self.count_vert()
        # self.num_vertices should now be correctly set by count_vert

        # Now call gpu_load
        if not self.gpu_load():
             # Log the error, but avoid raising another exception here if logger handles it
             logger.log_error(None, "Failed to load grid geometry to GPU") # Keep logging

    # gpu_load is inherited
