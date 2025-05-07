from utils.utils import Utils
from utils.uniform import Uniform
from core.compile_shader import CompileShader
from core.texture_cache import TextureCache
from OpenGL.GL import *
import pyrr
import numpy as np
from core.logger import logger  # Add logger import

DEFAULT_COLOR = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)

class Material:
    def __init__(self, shader_list):
        logger.log_message(f"Initializing Material with {len(shader_list)} shaders", level="INFO")
        try:
            # compile shaders and store the GL program ID
            self.compile_shader = CompileShader(shader_list)
            self.program_id = self.compile_shader.get_program_id()
            
            if self.program_id is None or self.program_id == 0:
                logger.log_message("Failed to create shader program", level="ERROR")
            else:
                logger.log_message(f"Shader program created with ID: {self.program_id}", level="DEBUG")
                
                # built-in uniforms
                self.uniforms = {
                    "model": Uniform("mat4", None),
                    "view": Uniform("mat4", None),
                    "projection": Uniform("mat4", None)
                }
                
                # CRITICAL: Locate all uniforms right after compilation
                self.locate_uniforms()
                logger.log_message("Uniforms located in shader program", level="DEBUG")
        except Exception as e:
            logger.log_error(e, context="Error during shader compilation")
            self.program_id = None  # Set to None to indicate failure
            self.uniforms = {}

        # render settings
        self.settings = {
            "drawStyle": GL_TRIANGLES
        }

        # simple material data
        self._diffuse_color = DEFAULT_COLOR
        self._meshes = []
        self._texture = None

    @property
    def diffuse_color(self):
        """RGBA diffuse color."""
        return self._diffuse_color

    @diffuse_color.setter
    def diffuse_color(self, value):
        self._diffuse_color = value

    @property
    def meshes(self):
        """List of meshes using this material."""
        return self._meshes

    @property
    def texture(self):
        return self._texture

    def set_texture(self, path):
        logger.log_message(f"Setting texture: {path}", level="DEBUG")
        try:
            self._texture = TextureCache().get_texture(path)
            if self._texture is None or self._texture.texture_id is None:
                logger.log_message(f"Failed to load texture: {path}", level="ERROR")
            else:
                logger.log_message(f"Texture loaded with ID: {self._texture.texture_id}", level="DEBUG")
                
                # Add texture uniform automatically when setting a texture
                # Use texture unit 0 for the primary texture
                # Older approach - uncomment if you want to auto-add uniform:
                # self.add_uniform("sampler2D", "texture1", (self._texture.texture_id, 0))
        except Exception as e:
            logger.log_error(e, context=f"Error loading texture: {path}")
            self._texture = None

    # --- shader uniform management ---
    def add_uniform(self, data_type: str, name: str, data):
        """Register a new uniform on this material *and* immediately locate it."""
        logger.log_message(f"Adding uniform: {name} of type {data_type}", level="DEBUG")
        try:
            u = Uniform(data_type, data)
            u.locate_variable(self.program_id, name)
            if u.variable_ref == -1:
                logger.log_message(f"Uniform location not found: {name}", level="WARNING")
            self.uniforms[name] = u
        except Exception as e:
            logger.log_error(e, context=f"Error adding uniform: {name}")

    def locate_uniforms(self):
        """Query and store uniform locations in the shader."""
        logger.log_message("Locating uniforms in shader", level="DEBUG")
        
        # Activate the program while locating uniforms
        current_program = glGetIntegerv(GL_CURRENT_PROGRAM)
        glUseProgram(self.program_id)
        
        for name, uni in self.uniforms.items():
            try:
                # use program_id and the correct method name
                uni.locate_variable(self.program_id, name)
                logger.log_message(f"Uniform '{name}' location: {uni.variable_ref}", level="DEBUG")
                
                if uni.variable_ref == -1:
                    logger.log_message(f"Uniform location not found: {name}", level="WARNING")
            except Exception as e:
                logger.log_error(e, context=f"Error locating uniform: {name}")
                
        # Restore previous program
        glUseProgram(current_program)

    def update_render_settings(self):
        """Override in subclasses to apply GL state (e.g., blending)."""
        try:
            gl_error = glGetError()
            if gl_error != GL_NO_ERROR:
                logger.log_message(f"OpenGL error before updating render settings: {gl_error}", level="WARNING")
                
            # Check if we have a texture and ensure it's bound properly
            if self._texture and self._texture.texture_id:
                logger.log_message(f"Binding texture ID {self._texture.texture_id} for rendering", level="DEBUG")
                # Make sure texture is bound to unit 0
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(GL_TEXTURE_2D, self._texture.texture_id)
                
            
            gl_error = glGetError()
            if gl_error != GL_NO_ERROR:
                logger.log_message(f"OpenGL error after updating render settings: {gl_error}", level="WARNING")
        except Exception as e:
            logger.log_error(e, context="Error updating render settings")

    def set_properties(self, properties: dict):
        """Batch‐update uniforms or settings by key."""
        for name, value in properties.items():
            if name in self.uniforms:
                self.uniforms[name].data = value
            elif name in self.settings:
                self.settings[name] = value
            else:
                raise KeyError(f"No material property named '{name}'")
