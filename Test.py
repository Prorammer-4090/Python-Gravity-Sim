import pygame as pg
from pygame.locals import *
import numpy as np
from OpenGL.GL import *
from core.compile_shader import CompileShader
from pyrr import Matrix44, Vector3
from core.window import Window
from core.ui import Button, Label

# Import our mesh classes
from meshes.polyhedronGeo import PolyhedronGeometry
from meshes.torusGeo import TorusGeometry
from meshes.mesh_data import MeshData

class MeshViewerApp(Window):
    def __init__(self):
        # Initialize with window size
        self.screen_size = [800, 600]
        super().__init__(self.screen_size)
        
        # Store dimensions explicitly
        self.width = self.screen_size[0]
        self.height = self.screen_size[1]
        
        self.theta = 0
        self.camera_pos = np.array([0.0, 0.0, 5.0])
        self.target_pos = np.array([0.0, 0.0, 0.0])  # What the camera is looking at
        self.rotation_speed = 30.0  # Degrees per second
        
        # Active mesh type
        self.current_mesh_type = "icosahedron"
        self.mesh_subdivisions = 0
        self.num_vertices = 0
        
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
        
        self.num_vertices_label = self.ui_manager.add_element(
            Label(600, 10, f"Verticies: {self.num_vertices}", color=(255, 255, 0), 
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        # App state
        self.paused = False
        self.wireframe = True
        self.mesh_types = ["tetrahedron", "octahedron", "cube", "icosahedron", "dodecahedron", "torus"]
    
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
        # Increase subdivision level (max 3 to prevent performance issues)
        if self.mesh_subdivisions < 5:
            self.mesh_subdivisions += 1
            self.subdivision_label.text = f"Subdivisions: {self.mesh_subdivisions}"
            self.load_mesh()
    
    def toggle_wireframe(self):
        # Toggle wireframe rendering mode
        self.wireframe = not self.wireframe
        self.wireframe_button.text = "Disable Wireframe" if self.wireframe else "Enable Wireframe"
    
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

    def initialize(self):
        print("OpenGL version:", glGetString(GL_VERSION).decode())
        print("GLSL version:", glGetString(GL_SHADING_LANGUAGE_VERSION).decode())

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        
        # Create shader
        self.compile = CompileShader([("shaders/vert_shader.vert", "vertex shader"), 
                                     ("shaders/frag_shader.frag", "fragment shader")])
        self.shader = self.compile.get_program_id()
        glUseProgram(self.shader)
        
        # Load initial mesh
        self.load_mesh()
        
        # Get dimensions from pygame's display surface if needed
        if not hasattr(self, 'width') or not hasattr(self, 'height'):
            surface = pg.display.get_surface()
            if surface:
                self.width, self.height = surface.get_size()
            else:
                # Fallback to default values
                self.width, self.height = 800, 600
        
        # Set up projection and view matrices
        self.proj = Matrix44.perspective_projection(45, self.width/self.height, 0.1, 50.0)
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
        
        # Calculate camera movement vectors
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
            movement -= right_vec * speed
        if keys[pg.K_d]:
            movement += right_vec * speed
        if keys[pg.K_w]:
            movement += front_vec * speed
        if keys[pg.K_s]:
            movement -= front_vec * speed
        if keys[pg.K_q]:
            # Move up
            movement += np.array([0, 1, 0]) * speed
        if keys[pg.K_e]:
            # Move down
            movement += np.array([0, -1, 0]) * speed
            
        # Apply movement to both camera and target
        self.camera_pos += movement
        self.target_pos += movement
        
        # Update view matrix based on camera position
        self.view = Matrix44.look_at(
            eye=Vector3(self.camera_pos),
            target=Vector3(self.target_pos),
            up=Vector3([0.0, 1.0, 0.0])
        )
        
        # Update rotation angle based on time and rotation speed
        delta_time = 1.0 / max(self.clock.get_fps(), 1.0)  # Get seconds per frame, avoid division by zero
        self.num_vertices = self.mesh.num_vertices
        self.num_vertices_label.text = f"Verticies: {self.num_vertices}"  # Update the label text
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


if __name__ == '__main__':
    app = MeshViewerApp()
    app.run()