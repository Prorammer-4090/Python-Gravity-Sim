import pygame as pg
from pygame.locals import *
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from pyrr import Matrix44, Vector3
from core.window import Window
from core.ui import Button, Label
import ctypes

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
    fragColor = color;
    gl_Position = projection * view * model * vec4(position, 1.0);
}
"""

# Fragment shader
FRAGMENT_SHADER = """
#version 330 core

in vec3 fragColor;
out vec4 outColor;

uniform float time;

void main() {
    // Use fragColor as phase shift so each vertex gets a unique color pattern
    float r = abs(tan(time + fragColor.r * 10.0));
    float g = abs(cos(time + fragColor.g * 10.0));
    float b = abs(sin(time + fragColor.b * 10.0));

    outColor = vec4(r, g, b, 1.0);
}
"""


class Cubeapp(Window):
    def __init__(self):
        super().__init__([800, 600])
        self.theta = 0
        self.camera_pos = np.array([0.0, 0.0, 5.0])
        self.target_pos = np.array([0.0, 0.0, 0.0])  # What the camera is looking at
        self.rotation_speed = 60.0  # Much slower rotation (15 degrees per second)
        
        # Add some UI elements
        self.fps_label = self.ui_manager.add_element(
            Label(10, 10, "FPS: 0", color=(255, 255, 0), font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        self.scale_label = self.ui_manager.add_element(
            Label(600, 10, "Scale: 1", color=(255, 255, 0), font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        self.pause_button = self.ui_manager.add_element(
            Button(10, 40, 100, 30, "Pause", self.toggle_pause, font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255))
        )
        
        self.reset_button = self.ui_manager.add_element(
            Button(120, 40, 100, 30, "Reset", self.reset_simulation, font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255))
        )
        
        self.paused = False
        self.reset = False
    
    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_button.text = "Resume" if self.paused else "Pause"
        print(f"Simulation {'paused' if self.paused else 'resumed'}")
    
    def reset_simulation(self):
        # Add your reset code here
        self.reset = True
        print("Simulation reset")
            

    def initialize(self):
        print("OpenGL version:", glGetString(GL_VERSION).decode())
        print("GLSL version:", glGetString(GL_SHADING_LANGUAGE_VERSION).decode())

        glEnable(GL_DEPTH_TEST)
        
        # Create shader
        glBindVertexArray(glGenVertexArrays(1))  # Required for core profile
        self.shader = compileProgram(
            compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
            compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        )
        glUseProgram(self.shader)
        
        # Vertices: x, y, z, r, g, b

        new_vertices, new_indices = self.generate_sphere(subdivisions=2)

        # Final arrays
        vertices = np.array(new_vertices, dtype=np.float32).reshape(-1)
        indices = np.array(new_indices, dtype=np.uint32)


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

        # Set up projection and view matrices
        self.proj = Matrix44.perspective_projection(45, 640/480, 0.1, 50.0)
        self.view = Matrix44.look_at(
            eye=Vector3(self.camera_pos),
            target=Vector3(self.target_pos),
            up=Vector3([0.0, 1.0, 0.0])
        )

        # Get uniform locations
        self.proj_loc = glGetUniformLocation(self.shader, "projection")
        self.view_loc = glGetUniformLocation(self.shader, "view")
        self.model_loc = glGetUniformLocation(self.shader, "model")

        # Set initial projection matrix
        glUniformMatrix4fv(self.proj_loc, 1, GL_FALSE, self.proj.astype(np.float32))
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, self.view.astype(np.float32))

    def update(self):
        super().update()
        
        # Update FPS display
        fps = self.clock.get_fps()
        self.fps_label.text = f"FPS: {fps:.1f}"
        
        cursor_scale = self.ui_manager.cursor_scale
        self.scale_label.text = f"Scale: {cursor_scale:.2f}"
        
        # Skip physics updates when paused
        if hasattr(self, 'paused') and self.paused:
            return
        if self.reset:
            self.theta = 0
            self.reset = False
            
        # Calculate camera movement vectors
        # Direction vector from camera to target
        front_vec = self.target_pos - self.camera_pos
        front_vec = front_vec / np.linalg.norm(front_vec)  # Normalize
        
        # Calculate right vector (perpendicular to front and world up)
        world_up = np.array([0.0, 1.0, 0.0])
        right_vec = np.cross(front_vec, world_up)
        right_vec = right_vec / np.linalg.norm(right_vec)  # Normalize
        
        # Handle camera movement
        keys = pg.key.get_pressed()
        speed = 0.1
        movement = np.zeros(3)
        
        if keys[pg.K_a]:
            # Move left (strafe)
            movement -= right_vec * speed
        if keys[pg.K_d]:
            # Move right (strafe)
            movement += right_vec * speed
        if keys[pg.K_w]:
            # Move forward
            movement += front_vec * speed
        if keys[pg.K_s]:
            # Move backward
            movement -= front_vec * speed
            
        # Apply movement to both camera and target
        self.camera_pos += movement
        self.target_pos += movement
        
        # Update view matrix based on camera position
        self.view = Matrix44.look_at(
            eye=Vector3(self.camera_pos),
            target=Vector3(self.target_pos),
            up=Vector3([0.0, 1.0, 0.0])
        )
        
        # Update rotation angle based on time and rotation speed (degrees per second)
        delta_time = 1.0 / max(self.clock.get_fps(), 1.0)  # Get seconds per frame, avoid division by zero
        if self.theta == 360:
            self.theta == 0
        self.theta = (self.theta + self.rotation_speed * delta_time)

    def render_opengl(self):
        glUseProgram(self.shader)

        # Update time uniform
        t = pg.time.get_ticks() / 1000.0  # Get time in seconds
        time_loc = glGetUniformLocation(self.shader, "time")
        glUniform1f(time_loc, t)

        # Apply view matrix
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, self.view.astype(np.float32))

        # Create and apply model matrix with rotation
        model = Matrix44.from_y_rotation(np.radians(self.theta)) @ Matrix44.from_x_rotation(np.radians(self.theta * 0.3))
        glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, model.astype(np.float32))

        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)

    def normalize(self, vertex):
        """Normalize position vector, keep RGB intact."""
        pos = vertex[:3]
        rgb = vertex[3:]
        norm = np.linalg.norm(pos)
        return np.concatenate((pos / norm, rgb))

    def midpoint(self, v1, v2):
        """Compute midpoint and normalize for spherical shape."""
        mid = (v1 + v2) / 2
        return self.normalize(mid)

    def single_subdivision(self, vertices, indices):
        """Subdivide each triangle into 4 and return new vertices and indices."""
        vertex_list = vertices.reshape(-1, 6).tolist()
        new_indices = []
        midpoint_cache = {}

        def get_midpoint_idx(i1, i2):
            key = tuple(sorted((i1, i2)))
            if key in midpoint_cache:
                return midpoint_cache[key]
            v1 = np.array(vertex_list[i1])
            v2 = np.array(vertex_list[i2])
            mid = self.midpoint(v1, v2)
            vertex_list.append(mid.tolist())
            idx = len(vertex_list) - 1
            midpoint_cache[key] = idx
            return idx

        for i in range(0, len(indices), 3):
            i0, i1, i2 = indices[i:i+3]
            a = get_midpoint_idx(i0, i1)
            b = get_midpoint_idx(i1, i2)
            c = get_midpoint_idx(i2, i0)
            new_indices += [
                i0, a, c,
                i1, b, a,
                i2, c, b,
                a, b, c
            ]

        return np.array(vertex_list, dtype=np.float32).reshape(-1), np.array(new_indices, dtype=np.uint32)

    def generate_sphere(self, subdivisions=1):
        # Initial octahedron (6 vertices, 8 triangles)
        vertices = np.array([
            # x, y, z,       r, g, b
            0.0,  1.0,  0.0,  1.0, 0.0, 0.0,  # top
            1.0,  0.0,  0.0,  0.0, 1.0, 0.0,  # +x
            0.0,  0.0,  1.0,  0.0, 0.0, 1.0,  # +z
            -1.0,  0.0,  0.0,  1.0, 1.0, 0.0,  # -x
            0.0,  0.0, -1.0,  0.0, 1.0, 1.0,  # -z
            0.0, -1.0,  0.0,  1.0, 0.0, 1.0,  # bottom
        ], dtype=np.float32)

        indices = np.array([
            0, 1, 2,
            0, 2, 3,
            0, 3, 4,
            0, 4, 1,
            5, 2, 1,
            5, 3, 2,
            5, 4, 3,
            5, 1, 4,
        ], dtype=np.uint32)

        for _ in range(subdivisions):
            vertices, indices = self.single_subdivision(vertices, indices)

        return vertices, indices



if __name__ == '__main__':
    app = Cubeapp()
    app.run()