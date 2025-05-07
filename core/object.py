from .entity import Entity
from OpenGL.GL import *
from core.logger import logger  # Add logger import

class Object(Entity):
    
    def __init__(self, mesh, material):
        super().__init__()
        logger.log_message("Initializing Object with mesh and material", level="DEBUG")
        
        try:
            self.material = material
            self.mesh = mesh
            self.visible = True

            # Validate mesh and material
            if mesh is None:
                logger.log_message("Warning: Object created with None mesh", level="WARNING")
            
            if material is None:
                logger.log_message("Warning: Object created with None material", level="WARNING")
            elif material.program_id is None:
                logger.log_message("Warning: Material has invalid program_id", level="WARNING")
            
            # assign the shader program to the mesh and let it load its VAO/VBOs
            if mesh is not None and material is not None and material.program_id is not None:
                self.mesh.program_id = material.program_id
                
                # Log before GPU load
                logger.log_message(f"Loading mesh to GPU with program_id: {material.program_id}", level="DEBUG")
                
                gpu_load_result = self.mesh.gpu_load()
                if not gpu_load_result:
                    logger.log_message("Failed to load mesh to GPU", level="ERROR")
                
                # now use the mesh's VAO
                self.vao_id = self.mesh.vao_id
                logger.log_message(f"Object initialized with VAO_ID: {self.vao_id}", level="DEBUG")
            else:
                logger.log_message("Cannot initialize mesh OpenGL data due to missing components", level="ERROR")
                self.vao_id = None
                
        except Exception as e:
            logger.log_error(e, context="Error during Object initialization")
            self.vao_id = None
            self.visible = False
    
    def get_triangles(self):
        """
        Retrieve the triangles that define the mesh's geometry.

        Returns:
            list: A list of triangles that compose the mesh.
        """
        try:
            return self.mesh.get_triangles()
        except Exception as e:
            logger.log_error(e, context="Error retrieving triangles from mesh")
            return []

    def is_visible(self):
        """
        Check if the mesh is currently marked as visible.

        Returns:
            bool: True if the mesh is visible and should be rendered, False if not.
        """
        return self.visible