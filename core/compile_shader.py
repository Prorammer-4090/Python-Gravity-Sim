from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from core.utils import Utils

class CompileShader:
    
    def __init__(self, shader_list):
        self.program_id = glCreateProgram()
        if self.program_id == 0:
            raise RuntimeError("Could not create shader program")
        
        utils = Utils()
        self.shader_list = []
        
        # Assuming shader_list contains tuples of (file_path, shader_type)
        for shader_path, shader_type in shader_list:
            shader_source = utils.readFiles(shader_path)
            self.shader_list.append((shader_source, shader_type))
            
        self.link_program()
    
    def init_shader(self, shader_source, shader_type):
        shader_id = glCreateShader(shader_type)
        if shader_id == 0:
            raise RuntimeError("Could not create shader object")
        
        glShaderSource(shader_id, shader_source)
        glCompileShader(shader_id)
        
        success = glGetShaderiv(shader_id, GL_COMPILE_STATUS)
        if not success:
            error_log = glGetShaderInfoLog(shader_id).decode('utf-8')
            glDeleteShader(shader_id)
            raise RuntimeError(f"There was an error compiling the shader:\n{error_log}")
        
        return shader_id
    
    def link_program(self):
        shader_ids = []

        for shader_source, shader_type in self.shader_list:
            if shader_type == "vertex shader":
                shader_id = self.init_shader(shader_source, GL_VERTEX_SHADER)
            elif shader_type == "fragment shader":
                shader_id = self.init_shader(shader_source, GL_FRAGMENT_SHADER)
            else:
                raise ValueError(f"Unknown shader type: {shader_type}")
            
            glAttachShader(self.program_id, shader_id)
            shader_ids.append(shader_id)

        glLinkProgram(self.program_id)

        success = glGetProgramiv(self.program_id, GL_LINK_STATUS)
        if not success:
            error_log = glGetProgramInfoLog(self.program_id).decode('utf-8')
            glDeleteProgram(self.program_id)
            raise RuntimeError(f"There was an error linking the program:\n{error_log}")
        
        # Optionally detach and delete shaders now that they're linked
        for shader_id in shader_ids:
            glDetachShader(self.program_id, shader_id)
            glDeleteShader(shader_id)

    def get_program_id(self):
        return self.program_id