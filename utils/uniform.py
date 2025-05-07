from core.logger import logger
from typing import Any, Dict, Optional, Tuple
from OpenGL.GL import *

class Uniform:
    """
    A class representing a uniform variable in an OpenGL shader program.

    Uniform variables are used to pass data (such as integers, floats, vectors, 
    matrices, or textures) from the CPU to the GPU for use in shaders.

    Instance Variables:
        data_type (str): The type of data being passed to the uniform 
                        (e.g., "int", "float", "vec2", "vec3", "vec4", "mat4", "sampler2D").
        data (varied): The actual data to be sent to the uniform variable.
        variable_ref (int): The location reference of the uniform variable in the shader program.
    """

    def __init__(self, data_type: str, data: Any) -> None:
        """
        Initialize a Uniform object.

        Params:
            data_type (str): The type of the uniform variable (e.g., "int", "float", "vec3").
            data (varied): The data to be passed to the uniform (type depends on data_type).

        Variables:
            - `data_type`: Specifies the type of the uniform (e.g., vector, matrix, or sampler).
            - `data`: Contains the uniform data that will be uploaded to the GPU.
            - `variable_ref`: Initially `None`, this will store the uniform's location in the shader program.
        """
        self.data_type: str = data_type
        self.data: Tuple[int, int] | Any = data
        self.variable_ref: Optional[Any] = None

    def locate_variable(self, program_ref: int, variable_name: str) -> None:
        """
        Locate the uniform variable in the shader program.

        Params:
            program_ref (int): The reference ID of the shader program.
            variable_name (str): The name of the uniform variable in the shader.

        This function retrieves and stores the location of the uniform variable. 
        If the variable is not found in the shader program, it logs a warning.
        """
        match self.data_type:
            case "Light":
                refs: Dict[str, int] = {}
                refs["lightType"]   = glGetUniformLocation(program_ref, variable_name + ".lightType")
                refs["color"]       = glGetUniformLocation(program_ref, variable_name + ".color")
                refs["direction"]   = glGetUniformLocation(program_ref, variable_name + ".direction")
                refs["position"]    = glGetUniformLocation(program_ref, variable_name + ".position")
                refs["attenuation"] = glGetUniformLocation(program_ref, variable_name + ".attenuation")
                self.variable_ref = refs

            case "Shadow":
                refs = {}
                refs["lightDirection"]  = glGetUniformLocation(program_ref, variable_name + ".lightDirection")
                refs["projectionMatrix"] = glGetUniformLocation(program_ref, variable_name + ".projectionMatrix")
                refs["viewMatrix"]      = glGetUniformLocation(program_ref, variable_name + ".viewMatrix")
                refs["depthTexture"]    = glGetUniformLocation(program_ref, variable_name + ".depthTexture")
                refs["strength"]        = glGetUniformLocation(program_ref, variable_name + ".strength")
                refs["bias"]            = glGetUniformLocation(program_ref, variable_name + ".bias")
                self.variable_ref = refs

            case _:
                loc = glGetUniformLocation(program_ref, variable_name)
                if loc == -1:
                    logger.log_message(f"Uniform '{variable_name}' not found in program {program_ref}",
                                       level="WARNING")
                self.variable_ref = loc

    def _bind_texture(self, tex_ref: int, unit: int) -> None:
        """
        Bind a texture to a specified texture unit.

        Params:
            tex_ref (int): The reference ID of the texture object.
            unit (int): The texture unit to bind the texture to.
        """
        # unit=0 → GL_TEXTURE0, unit=1 → GL_TEXTURE1, etc.
        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, tex_ref)

    def upload_data(self) -> None:
        """
        Upload the uniform data to the GPU.

        This method handles data types by calling the appropriate 
        OpenGL function to pass the data to the uniform variable in the shader.

        Supported Data Types:
            - "int", "bool": Uses `glUniform1i` to upload integer data.
            - "float": Uses `glUniform1f` to upload float data.
            - "vec2", "vec3", "vec4": Uploads 2D, 3D, or 4D vectors using `glUniform*`.
            - "mat4": Uploads a 4x4 matrix using `glUniformMatrix4fv`.
            - "sampler2D": Handles texture samplers and binds textures to texture units.
        """
        if self.variable_ref in (None, -1):
            return

        try:
            # Check if data is None which could cause errors
            if self.data is None:
                logger.log_message(f"Cannot upload None data for uniform of type {self.data_type}", level="WARNING")
                return
                
            # Get OpenGL error state before upload
            pre_error = glGetError()
            if pre_error != GL_NO_ERROR:
                logger.log_message(f"OpenGL error before uniform upload: {pre_error}", level="WARNING")

            match self.data_type:
                case "int" | "bool":
                    glUniform1i(self.variable_ref, int(self.data))

                case "float":
                    glUniform1f(self.variable_ref, float(self.data))

                case "vec2":
                    glUniform2f(self.variable_ref, *self.data)

                case "vec3":
                    glUniform3f(self.variable_ref, *self.data)

                case "vec4":
                    glUniform4f(self.variable_ref, *self.data)

                case "mat4":
                                        glUniformMatrix4fv(self.variable_ref, 1, GL_TRUE, self.data)

                case "sampler2D":
                    tex_ref, unit = self.data
                    # Check if texture reference is valid
                    if tex_ref is None or tex_ref == 0:
                        logger.log_message(f"Invalid texture reference: {tex_ref}", level="WARNING")
                        return
                        
                    logger.log_message(f"Binding texture ID {tex_ref} to unit {unit} for uniform at location {self.variable_ref}", level="DEBUG")
                    self._bind_texture(tex_ref, unit)
                    glUniform1i(self.variable_ref, unit)

                case "Light":
                    refs = self.variable_ref  # type: Dict[str, int]
                    L = self.data
                    glUniform1i(refs["lightType"], L.lightType)
                    glUniform3f(refs["color"], *L.color)
                    glUniform3f(refs["direction"], *L.getDirection())
                    glUniform3f(refs["position"], *L.getPosition())
                    glUniform3f(refs["attenuation"], *L.attenuation)

                case "Shadow":
                    refs = self.variable_ref
                    S = self.data
                    glUniform3f(refs["lightDirection"], *S.lightSource.getDirection())
                    glUniformMatrix4fv(refs["projectionMatrix"], 1, GL_TRUE, S.camera.projectionMatrix)
                    glUniformMatrix4fv(refs["viewMatrix"], 1, GL_TRUE, S.camera.viewMatrix)
                    # bind depth texture to a fixed unit (e.g. 15)
                    self._bind_texture(S.renderTarget.texture.textureRef, 15)
                    glUniform1i(refs["depthTexture"], 15)
                    glUniform1f(refs["strength"], S.strength)
                    glUniform1f(refs["bias"], S.bias)

                case _:
                    logger.log_message(f"Unsupported uniform type {self.data_type}", level="ERROR")
                    return
                    
            # Check for errors after upload
            post_error = glGetError()
            if post_error != GL_NO_ERROR:
                logger.log_message(f"OpenGL error after uploading uniform of type {self.data_type}: {post_error}", level="ERROR")
                
        except Exception as e:
            logger.log_error(e, context=f"Error uploading uniform data of type {self.data_type}")