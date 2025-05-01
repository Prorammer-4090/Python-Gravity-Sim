import pygame as pg
from pygame.locals import *
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from core.window import Window
from core.ui import Button, Label
import ctypes
from helpers.camera import Camera
from helpers.cameraController import CameraController
from helpers.transform import Transform
from helpers.object3D import Object3D
from core.texture_cache import TextureCache
from core.logger import logger

# Vertex shader
VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color; 
layout(location = 2) in vec2 texCoords;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection; 

out vec3  fragColor;
out vec2  fragUV;

void main() {
    gl_Position   = projection * view * model * vec4(position, 1.0); 
    fragColor     = color;
    fragUV        = texCoords;
}
"""

# Fragment shader
FRAGMENT_SHADER = """
#version 330 core
in  vec3  fragColor; 
in  vec2  fragUV;
out vec4  outColor;

uniform sampler2D texture1;

void main() {
     vec4 tex = texture(texture1, fragUV);
     outColor = tex * vec4(fragColor, 1.0);
    
    //outColor = texture(texture1, fragUV);
}
"""


class Cubeapp(Window):
    def __init__(self):
        self.width = 800
        self.height = 600
        super().__init__([self.width, self.height])
        self.theta = 0
        self.rotation_speed = 60.0

        # Create the cube object
        self.cube = Object3D()

        # Initialize Camera and Controller
        self.camera_controller = CameraController(unitsPerSecond=2, degreesPerSecond=60)
        self.camera = Camera(aspectRatio=800 / 600)
        self.camera_controller.setPosition([0, 0, 5])
        self.camera_controller.add(self.camera)
        
        self.texture_cache = TextureCache()
        self.cube_texture = None

        # Add some UI elements
        self.fps_label = self.ui_manager.add_element(
            Label(10, 10, "FPS: 0", color=(255, 255, 0), font_family="fonts/Silkscreen-Regular.ttf")
        )
        
        self.scale_label = self.ui_manager.add_element(
            Label(600, 10, "Scale: 1", color=(255, 255, 0), font_family="fonts/Silkscreen-Regular.ttf")
        )
        
        self.pause_button = self.ui_manager.add_element(
            Button(10, 40, 100, 30, "Pause", self.toggle_pause, font_family="fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255))
        )
        
        self.reset_button = self.ui_manager.add_element(
            Button(120, 40, 100, 30, "Reset", self.reset_simulation, font_family="fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255))
        )
        
        self.paused = False
        self.reset = False
    
    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_button.text = "Resume" if self.paused else "Pause"
        print(f"Simulation {'paused' if self.paused else 'resumed'}")
    
    def reset_simulation(self):
        self.reset = True
        print("Simulation reset")
            
    def initialize(self):
        print("OpenGL version:", glGetString(GL_VERSION).decode())
        print("GLSL version:", glGetString(GL_SHADING_LANGUAGE_VERSION).decode())

        glEnable(GL_DEPTH_TEST)
        
        # Create shader
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.shader = compileProgram(
            compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
            compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        )
        glUseProgram(self.shader)
        
        texture_path = "textures/stone.png"
        self.cube_texture = self.texture_cache.get_texture(texture_path)
        
        if self.cube_texture is None or self.cube_texture.texture_id is None:
            logger.log_message(f"Failed to load primary texture '{texture_path}'. Check logs.", level="ERROR")
            self.cube_texture = self.texture_cache.get_texture(None)
            if self.cube_texture is None or self.cube_texture.texture_id is None:
                logger.log_message("Default texture also unavailable. Cannot proceed with texturing.", level="CRITICAL")
            else:
                logger.log_message("Using default texture as fallback.", level="WARNING")
        
        # Create cube
        vertices = np.array([
            # Back face (z = -1)
             1, -1, -1,  1,0,0,  1,0,
             1,  1, -1,  0,1,0,  1,1,
            -1,  1, -1,  0,0,1,  0,1,
            -1, -1, -1,  1,1,0,  0,0,
            # Front face (z = +1)
             1, -1,  1,  1,0,1,  1,0,
             1,  1,  1,  0,1,1,  1,1,
            -1,  1,  1,  1,1,1,  0,1,
            -1, -1,  1,  0,0,0,  0,0,
            # Left face (x = -1)
            -1, -1, -1,  1,1,0,  1,0,
            -1,  1, -1,  0,0,1,  1,1,
            -1,  1,  1,  0,0,0,  0,1,
            -1, -1,  1,  1,1,1,  0,0,
            # Right face (x = +1)
             1, -1, -1,  1,0,0,  1,0,
             1,  1, -1,  0,1,0,  1,1,
             1,  1,  1,  0,1,1,  0,1,
             1, -1,  1,  1,0,1,  0,0,
            # Top face (y = +1)
            -1,  1, -1,  0,0,1,  0,0,
             1,  1, -1,  0,1,0,  1,0,
             1,  1,  1,  0,1,1,  1,1,
            -1,  1,  1,  1,1,1,  0,1,
            # Bottom face (y = -1)
            -1, -1, -1,  1,1,0,  0,0,
             1, -1, -1,  1,0,0,  1,0,
             1, -1,  1,  1,0,1,  1,1,
            -1, -1,  1,  1,1,1,  0,1,
        ], dtype=np.float32)

        indices = np.array([
            0,1,2, 2,3,0,       # back
            4,5,6, 6,7,4,       # front
            8,9,10,10,11,8,     # left
            12,13,14,14,15,12,  # right
            16,17,18,18,19,16,  # top
            20,21,22,22,23,20,  # bottom
        ], dtype=np.uint32)


        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        
        stride = 8 * vertices.itemsize # 3 floats for position, 3 floats for color, 2 floats for UV = 8 floats total

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * vertices.itemsize))
        glEnableVertexAttribArray(1)
        
        # Texture coordinate attribute (location = 2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * vertices.itemsize)) # Offset by 6 floats
        glEnableVertexAttribArray(2)

        self.index_count = len(indices)
        glBindVertexArray(0) # Unbind VAO after configuration is complete
        glBindBuffer(GL_ARRAY_BUFFER, 0) # Unbind VBO
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0) # Unbind EBO (optional but good practice)

        # Set up projection matrix
        self.camera.setPerspective(aspectRatio=self.width / self.height)

        # Get uniform locations
        self.proj_loc = glGetUniformLocation(self.shader, "projection")
        self.view_loc = glGetUniformLocation(self.shader, "view")
        self.model_loc = glGetUniformLocation(self.shader, "model")
        self.tex_sampler_loc = glGetUniformLocation(self.shader, "texture1") # Location for the texture sampler

        # Verify uniform locations
        if -1 in [self.proj_loc, self.view_loc, self.model_loc, self.tex_sampler_loc]:
            logger.log_message("One or more uniform locations not found!", level="WARNING")

         # --- Initial Matrix/Uniform Setup ---
        glUseProgram(self.shader) # Bind shader to set uniforms
        glUniformMatrix4fv(self.proj_loc, 1, GL_TRUE, self.camera.projectionMatrix)
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, self.camera.viewMatrix)
        # Set the texture sampler uniform to use texture unit 1
        if self.tex_sampler_loc != -1:
             glUniform1i(self.tex_sampler_loc, 1) # 1 corresponds to GL_TEXTURE1
        glUseProgram(0) # Unbind shader

        self.camera.updateViewMatrix() # Ensure camera view matrix is calculated initially
        self.check_gl_error("After Initialization")
        logger.log_message("Initialization complete.", level="INFO")

        
    def update(self):
        super().update()
        
        # Update FPS display
        fps = self.clock.get_fps()
        self.fps_label.text = f"FPS: {fps:.1f}"
        
        cursor_scale = self.ui_manager.cursor_scale
        self.scale_label.text = f"Scale: {cursor_scale:.2f}"
        
        # Calculate delta time for updates
        delta_time = self.clock.get_time() / 1000.0  # Convert ms to seconds

        # Update camera controller based on input
        self.camera_controller.update(self.input, delta_time)

        # Skip physics updates when paused
        if hasattr(self, 'paused') and self.paused:
            return
        if self.reset:
            self.cube.transform = Transform.identity()
            self.theta = 0
            self.reset = False

        # Update rotation angle based on time
        if self.theta > 360:
            self.theta = 0
        self.theta = (self.theta + self.rotation_speed * delta_time)

        # Apply rotation around Y and X axes to the cube
        rot_x = Transform.rotation(0, self.theta, 0)
        rot_z = Transform.rotation(self.theta, 0, 0)
        self.cube.transform = rot_x @ rot_z

    def render_opengl(self):
        # Clear buffers and set viewport
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glViewport(0, 0, self.width, self.height)

        glUseProgram(self.shader)
        self.check_gl_error("After glUseProgram in render_opengl")
        
        # --- Bind Texture ---
        if self.cube_texture and self.cube_texture.texture_id is not None:
            # logger.log_message(f"Binding texture ID: {self.cube_texture.texture_id}", level="DEBUG")
            self.cube_texture.bind(texture_unit=1) # Bind to texture unit 1
        else:
            # For now, if no texture, it might render black or based on shader defaults
            logger.log_message("No valid texture to bind for rendering.", level="WARNING")

        self.camera.updateViewMatrix()

        # Apply matrices
        glUniformMatrix4fv(self.view_loc, 1, GL_TRUE, self.camera.viewMatrix)
        
        model_matrix = self.cube.getWorldMatrix()
        glUniformMatrix4fv(self.model_loc, 1, GL_TRUE, model_matrix)
        
         # --- Draw the Cube ---
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        self.check_gl_error("After glDrawElements")

        # --- Unbind ---
        glBindVertexArray(0)
        if self.cube_texture:
            self.cube_texture.unbind(texture_unit=1) # Unbind from texture unit 0
        glUseProgram(0)

    def check_gl_error(self, stage=""):
        err = glGetError()
        if err != GL_NO_ERROR:
            error_str = f"OpenGL Error at {stage}: {err}"
            logger.log_message(error_str, level="ERROR")


if __name__ == '__main__':
    try:
        app = Cubeapp()
        app.run()
    except Exception as e:
        logger.log_error(e, context="Application crashed")
