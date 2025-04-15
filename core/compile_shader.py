from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from core.utils import Utils
from core.logger import logger

class CompileShader:
    
    def __init__(self, shader_list):
        self.program_id = glCreateProgram()
        if self.program_id == 0:
            error_msg = "Could not create shader program"
            logger.log_error(RuntimeError(error_msg), f"Shader list: {shader_list}")
            raise RuntimeError(error_msg)
        
        utils = Utils()
        self.shader_list = []
        
        # Assuming shader_list contains tuples of (file_path, shader_type)
        for shader_path, shader_type in shader_list:
            try:
                shader_source = utils.readFiles(shader_path)
                self.shader_list.append((shader_source, shader_type))
            except Exception as e:
                logger.log_error(e, f"Failed to read shader file: {shader_path}")
                raise
            
        self.link_program()
    
    def init_shader(self, shader_source, shader_type):
        shader_id = glCreateShader(shader_type)
        if shader_id == 0:
            error_msg = "Could not create shader object"
            logger.log_error(RuntimeError(error_msg), f"Shader type: {shader_type}")
            raise RuntimeError(error_msg)
        
        glShaderSource(shader_id, shader_source)
        glCompileShader(shader_id)
        
        success = glGetShaderiv(shader_id, GL_COMPILE_STATUS)
        if not success:
            error_log = glGetShaderInfoLog(shader_id).decode('utf-8')
            glDeleteShader(shader_id)
            error = RuntimeError(f"There was an error compiling the shader:\n{error_log}")
            
            # Log the shader compilation error with the shader source
            context = f"Shader type: {shader_type}\nShader source:\n{shader_source[:500]}..." \
                      if len(shader_source) > 500 else shader_source
            logger.log_error(error, context)
            
            raise error
        
        return shader_id
    
    def link_program(self):
        shader_ids = []

        for shader_source, shader_type in self.shader_list:
            try:
                if shader_type == "vertex shader":
                    shader_id = self.init_shader(shader_source, GL_VERTEX_SHADER)
                elif shader_type == "fragment shader":
                    shader_id = self.init_shader(shader_source, GL_FRAGMENT_SHADER)
                else:
                    error = ValueError(f"Unknown shader type: {shader_type}")
                    logger.log_error(error)
                    raise error
                
                glAttachShader(self.program_id, shader_id)
                shader_ids.append(shader_id)
            except Exception as e:
                # Log any errors during shader initialization
                if not isinstance(e, (RuntimeError, ValueError)):
                    logger.log_error(e, f"Error initializing shader: {shader_type}")
                raise

        glLinkProgram(self.program_id)

        success = glGetProgramiv(self.program_id, GL_LINK_STATUS)
        if not success:
            error_log = glGetProgramInfoLog(self.program_id).decode('utf-8')
            glDeleteProgram(self.program_id)
            error = RuntimeError(f"There was an error linking the program:\n{error_log}")
            logger.log_error(error, f"Shader count: {len(shader_ids)}")
            raise error
        
        # Optionally detach and delete shaders now that they're linked
        for shader_id in shader_ids:
            glDetachShader(self.program_id, shader_id)
            glDeleteShader(shader_id)

    def get_program_id(self):
        return self.program_id