import pygame as pg
from pygame.locals import *
import numpy as np
from OpenGL.GL import *
from core.compile_shader import CompileShader
from pyrr import Matrix44, Vector3
from core.window import Window
from core.ui import Button, Label
from helpers.camera import Camera
from helpers.cameraController import CameraController
from helpers.transform import Transform

# Import our mesh classes
from meshes.polyhedronGeo import PolyhedronGeometry
from meshes.torusGeo import TorusGeometry
from meshes.mesh_data import MeshData

class LitMeshViewerApp(Window):
    def __init__(self):
        # Initialize with window size
        self.screen_size = [800, 600]
        super().__init__(self.screen_size)
        
        # Store dimensions explicitly
        self.width = self.screen_size[0]
        self.height = self.screen_size[1]
        
        self.theta = 0
        
        # Initialize camera and camera controller
        self.camera = Camera(angleOfView=60, aspectRatio=self.width/self.height, near=0.1, far=1000.0)
        self.camera_controller = CameraController(unitsPerSecond=3, degreesPerSecond=60)
        self.camera_controller.add(self.camera)
        self.camera_controller.setPosition([0.0, 0, 5.5])
        self.rotation_speed = 30.0  # Degrees per second
        
        # Active mesh type
        self.current_mesh_type = "icosahedron"
        self.mesh_subdivisions = 0
        self.num_vertices = 0
        
        # Lighting parameters
        self.ambient_strength = 0.5
        self.ambient_color = [1.0, 1.0, 1.0]  # White ambient light
        self.mesh_color = [0.0, 0.7, 1.0]     # Default blue color
        self.use_custom_color = True          # Use the uniform color by default
        
        # Add UI elements
        self.fps_label = self.ui_manager.add_element(
            Label(10, 10, "FPS: 0", color=(255, 255, 0), font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        self.mesh_label = self.ui_manager.add_element(
            Label(10, 40, f"Mesh: {self.current_mesh_type}", color=(255, 255, 0), 
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        self.subdivision_label = self.ui_manager.add_element(
            Label(10, 70, f"Subdivisions: {self.mesh_subdivisions}", color=(255, 255, 0), 
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        self.num_vertices_label = self.ui_manager.add_element(
            Label(600, 10, f"Vertices: {self.num_vertices}", color=(255, 255, 0), 
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        self.ambient_label = self.ui_manager.add_element(
            Label(600, 40, f"Ambient: {self.ambient_strength:.1f}", color=(255, 255, 0), 
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        self.color_mode_label = self.ui_manager.add_element(
            Label(600, 70, "Using Custom Color", color=(255, 255, 0), 
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        # Mesh control buttons
        self.next_mesh_button = self.ui_manager.add_element(
            Button(10, 100, 150, 30, "Next Mesh", self.next_mesh, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255), font_size=18)
        )
        
        self.increase_subdiv_button = self.ui_manager.add_element(
            Button(10, 140, 200, 30, "Add Subdivision", self.increase_subdivision, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255),
                   font_size=18
                   )
        )
        
        self.wireframe_button = self.ui_manager.add_element(
            Button(10, 180, 200, 30, "Toggle Wireframe", self.toggle_wireframe, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255),
                   font_size=16)
        )
        
        self.increase_ambient_button = self.ui_manager.add_element(
            Button(10, 220, 200, 30, "Increase Ambient", self.increase_ambient, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255),
                   font_size=16)
        )
        
        self.decrease_ambient_button = self.ui_manager.add_element(
            Button(10, 260, 200, 30, "Decrease Ambient", self.decrease_ambient, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255),
                   font_size=16)
        )
        
        self.toggle_color_button = self.ui_manager.add_element(
            Button(10, 300, 200, 30, "Toggle Color Mode", self.toggle_color_mode, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255),
                   font_size=16)
        )
        
        self.cycle_color_button = self.ui_manager.add_element(
            Button(10, 340, 200, 30, "Cycle Mesh Color", self.cycle_color, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255),
                   font_size=16)
        )
        
        # App state
        self.paused = False
        self.wireframe = False
        self.mesh_types = ["tetrahedron", "octahedron", "cube", "icosahedron", "dodecahedron", "torus"]
        
        # Predefined colors for cycling
        self.color_presets = [
            [0.0, 0.7, 1.0],  # Blue
            [0.0, 0.8, 0.4],  # Green
            [1.0, 0.4, 0.0],  # Orange
            [0.8, 0.2, 0.8],  # Purple
            [1.0, 0.8, 0.0],  # Yellow
        ]
        self.color_index = 0
    
    def next_mesh(self):
        # Cycle to the next mesh type
        current_index = self.mesh_types.index(self.current_mesh_type)
        next_index = (current_index + 1) % len(self.mesh_types)
        self.current_mesh_type = self.mesh_types[next_index]
        self.mesh_label.text = f"Mesh: {self.current_mesh_type}"
        
        # Reset subdivisions when changing mesh type
        self.mesh_subdivisions = 0
        self.subdivision_label.text = f"Subdivisions: {self.mesh_subdivisions}"
        
        # Reload the mesh
        self.load_mesh()
    
    def increase_subdivision(self):
        # Increase subdivision level (max 5 to prevent performance issues)
        if self.mesh_subdivisions < 5:
            self.mesh_subdivisions += 1
            self.subdivision_label.text = f"Subdivisions: {self.mesh_subdivisions}"
            self.load_mesh()
    
    def toggle_wireframe(self):
        # Toggle wireframe rendering mode
        self.wireframe = not self.wireframe
        self.wireframe_button.text = "Disable Wireframe" if self.wireframe else "Enable Wireframe"
    
    def increase_ambient(self):
        # Increase ambient light intensity (max 1.0)
        self.ambient_strength = min(1.0, self.ambient_strength + 0.1)
        self.ambient_label.text = f"Ambient: {self.ambient_strength:.1f}"
    
    def decrease_ambient(self):
        # Decrease ambient light intensity (min 0.0)
        self.ambient_strength = max(0.0, self.ambient_strength - 0.1)
        self.ambient_label.text = f"Ambient: {self.ambient_strength:.1f}"
    
    def toggle_color_mode(self):
        # Toggle between custom color and vertex colors
        self.use_custom_color = not self.use_custom_color
        self.color_mode_label.text = "Using Custom Color" if self.use_custom_color else "Using Vertex Colors"
    
    def cycle_color(self):
        # Cycle through predefined colors
        self.color_index = (self.color_index + 1) % len(self.color_presets)
        self.mesh_color = self.color_presets[self.color_index]
    
    def load_mesh(self):
        """Load the currently selected mesh with appropriate subdivisions"""
        if self.current_mesh_type == "torus":
            segments = 8 + 8 * self.mesh_subdivisions  # Scale segments with subdivision level
            self.mesh = TorusGeometry(
                major_radius=1.0, 
                minor_radius=0.4, 
                radial_segments=segments, 
                tubular_segments=segments
            )
        else:
            # For polyhedra, use the built-in subdivision algorithm
            self.mesh = PolyhedronGeometry(
                radius=1.0,
                polyhedron_type=self.current_mesh_type,
                subdivisions=self.mesh_subdivisions
            )
        
        # Load mesh data to GPU
        if not self.mesh.gpu_load():
            print(f"Failed to load mesh: {self.current_mesh_type}")
        self.num_vertices = self.mesh.num_vertices
        self.num_vertices_label.text = f"Vertices: {self.num_vertices}"

    def initialize(self):
        print("OpenGL version:", glGetString(GL_VERSION).decode())
        print("GLSL version:", glGetString(GL_SHADING_LANGUAGE_VERSION).decode())

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        
        # Create shader with our lit shaders
        self.compile = CompileShader([("shaders/vert_shader_lit.vert", "vertex shader"), 
                                     ("shaders/frag_shader_lit.frag", "fragment shader")])
        self.shader = self.compile.get_program_id()
        glUseProgram(self.shader)
        
        # Load initial mesh
        self.load_mesh()
        
        # Update camera's aspect ratio based on window dimensions
        self.camera.setPerspective(angleOfView=60, aspectRatio=self.width/self.height, near=0.1, far=1000.0)
        
        # Get uniform locations
        self.proj_loc = glGetUniformLocation(self.shader, "projection")
        self.view_loc = glGetUniformLocation(self.shader, "view")
        self.model_loc = glGetUniformLocation(self.shader, "model")
        
        # Lighting uniform locations
        self.ambient_str_loc = glGetUniformLocation(self.shader, "ambientStrength")
        self.ambient_color_loc = glGetUniformLocation(self.shader, "ambientColor")
        self.mesh_color_loc = glGetUniformLocation(self.shader, "meshColor")
        self.use_custom_color_loc = glGetUniformLocation(self.shader, "useCustomColor")

        # Set initial projection matrix
        glUniformMatrix4fv(self.proj_loc, 1, GL_FALSE, self.camera.projectionMatrix)
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, self.camera.viewMatrix)

    def update(self):
        super().update()
        
        # Update FPS display
        fps = self.clock.get_fps()
        self.fps_label.text = f"FPS: {fps:.1f}"
        
        # Update rotation angle based on time and rotation speed (degrees per second)
        delta_time = 1.0 / max(self.clock.get_fps(), 1.0)  # Get seconds per frame, avoid division by zero
        if self.theta == 360:
            self.theta = 0
        self.theta = (self.theta + self.rotation_speed * delta_time) % 360
        
        # Update camera controls
        self.camera_controller.update(self.input, delta_time)
        self.camera.updateViewMatrix()

    def render_opengl(self):
        glUseProgram(self.shader)

        # Update time uniform
        t = pg.time.get_ticks() / 1000.0  # Get time in seconds
        time_loc = glGetUniformLocation(self.shader, "time")
        if time_loc != -1:
            glUniform1f(time_loc, t)
        
        # Update lighting uniforms
        glUniform1f(self.ambient_str_loc, self.ambient_strength)
        glUniform3f(self.ambient_color_loc, *self.ambient_color)
        glUniform3f(self.mesh_color_loc, *self.mesh_color)
        glUniform1i(self.use_custom_color_loc, int(self.use_custom_color))

        # Apply projection and view matrices from camera
        glUniformMatrix4fv(self.proj_loc, 1, GL_FALSE, self.camera.projectionMatrix)
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, self.camera.viewMatrix)

        # Create and apply model matrix with rotation
        model = Matrix44.from_y_rotation(np.radians(self.theta)) @ Matrix44.from_x_rotation(np.radians(self.theta * 0.5))
        glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, model.astype(np.float32))

        # Bind the mesh VAO
        glBindVertexArray(self.mesh.vao_id)
        
        # Apply wireframe mode if enabled
        if self.wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        
        # Draw the mesh
        glDrawElements(GL_TRIANGLES, self.mesh.num_vertices, GL_UNSIGNED_INT, None)
        
        # CRITICAL: Always restore polygon mode to GL_FILL when done
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        # CRITICAL: Disable face culling so UI will render properly
        glDisable(GL_CULL_FACE)
        
        # Unbind VAO and shader
        glBindVertexArray(0)
        glUseProgram(0)

    # Add a method to handle window resize events
    def resize_callback(self, width, height):
        # Update stored dimensions
        self.width = width
        self.height = height
        
        # Update camera projection matrix with new aspect ratio
        self.camera.setPerspective(angleOfView=60, aspectRatio=width/height, near=0.1, far=1000.0)
        
        # Update pygame viewport
        pg.display.set_mode((width, height), pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE)
        
        # Update OpenGL viewport
        glViewport(0, 0, width, height)


if __name__ == '__main__':
    app = LitMeshViewerApp()
    app.run()
