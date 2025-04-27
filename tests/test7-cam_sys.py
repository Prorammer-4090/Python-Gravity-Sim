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

# Vertex shader
VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color; 

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection; 

out vec3 fragColor;

void main() {
    gl_Position = projection * view * model * vec4(position, 1.0); 
    fragColor = color;
}
"""

# Fragment shader
FRAGMENT_SHADER = """
#version 330 core
in vec3 fragColor; 
out vec4 outColor;
void main() {
    outColor = vec4(fragColor, 1.0);
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
        glBindVertexArray(glGenVertexArrays(1))
        self.shader = compileProgram(
            compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
            compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        )
        glUseProgram(self.shader)
        
        # Create cube
        vertices = np.array([
            # position        # color
            1, -1, -1,  0, 0, 0,   
            1,  1, -1,  0, 0, 1,
            -1,  1, -1,  0, 1, 0,
            -1, -1, -1,  0, 1, 1,
            1, -1,  1,  1, 0, 0,
            1,  1,  1,  1, 0, 1,
            -1, -1,  1,  1, 1, 0,
            -1,  1,  1,  1, 1, 1,
        ], dtype=np.float32)

        indices = np.array([
            0, 1, 2, 2, 3, 0,
            3, 2, 7, 7, 6, 3,
            6, 7, 5, 5, 4, 6,
            4, 5, 1, 1, 0, 4,
            1, 5, 7, 7, 2, 1,
            4, 0, 3, 3, 6, 4
        ], dtype=np.uint32)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        self.index_count = len(indices)

        # Set up projection matrix
        self.camera.setPerspective(aspectRatio=800 / 600)

        # Get uniform locations
        self.proj_loc = glGetUniformLocation(self.shader, "projection")
        self.view_loc = glGetUniformLocation(self.shader, "view")
        self.model_loc = glGetUniformLocation(self.shader, "model")

        # Verify uniform locations
        if -1 in [self.proj_loc, self.view_loc, self.model_loc]:
            print("ERROR: One or more uniform locations not found!")

        # Ensure camera inherits controller's position
        self.camera.updateViewMatrix()

        # Set initial matrices
        glUniformMatrix4fv(self.proj_loc, 1, GL_TRUE, self.camera.projectionMatrix)
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, self.camera.viewMatrix)
        self.check_gl_error("After initial matrix uploads")
        
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
        self.check_gl_error("After glUseProgram")

        self.camera.updateViewMatrix()

        # Apply matrices
        glUniformMatrix4fv(self.proj_loc, 1, GL_TRUE, self.camera.projectionMatrix)
        glUniformMatrix4fv(self.view_loc, 1, GL_TRUE, self.camera.viewMatrix)
        
        model_matrix = self.cube.getWorldMatrix()
        glUniformMatrix4fv(self.model_loc, 1, GL_TRUE, model_matrix)
        
        # Draw the cube
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        self.check_gl_error("After glDrawElements")
        
        glBindVertexArray(0)

    def check_gl_error(self, stage=""):
        err = glGetError()
        if err != GL_NO_ERROR:
            print(f"OpenGL Error at {stage}: {err}")


if __name__ == '__main__':
    app = Cubeapp()
    app.run()