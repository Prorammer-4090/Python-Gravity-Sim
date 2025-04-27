import pygame as pg
from pygame.locals import *
import numpy as np
from OpenGL.GL import *
from core.compile_shader import CompileShader
from pyrr import Matrix44, Vector3
from core.window import Window
from core.ui import Button, Label
# Import camera system
from helpers.camera import Camera
from helpers.cameraController import CameraController
from helpers.transform import Transform
# Import managers and renderer
from helpers.mesh_manager import MeshManager       # Import MeshManager
from helpers.lighting_manager import LightingManager # Import LightingManager
from core.renderer import Renderer             # Keep Renderer import

class LitMeshViewerApp(Window):
    def __init__(self):
        self.screen_size = [800, 600]
        super().__init__(self.screen_size)

        self.width = self.screen_size[0]
        self.height = self.screen_size[1]

        self.theta = 0
        self.rotation_speed = 30.0

        # Camera setup (remains the same)
        self.camera_controller = CameraController(unitsPerSecond=2, degreesPerSecond=60)
        self.camera = Camera(aspectRatio=self.width / self.height)
        self.camera_controller.setPosition([0, 0, 5])
        self.camera_controller.add(self.camera)

        # Create Managers
        try:
            self.mesh_manager = MeshManager(initial_mesh_type="icosahedron")
        except Exception as e:
            print(f"Error initializing MeshManager: {e}")
            pg.quit()
            quit() # Exit if mesh manager fails (e.g., initial load fails)

        self.lighting_manager = LightingManager(initial_ambient_strength=0.5)

        # App state
        self.paused = False
        self.wireframe = False

        # Renderer instance
        self.renderer = None # Will be created in initialize

        # --- UI Setup (Use managers for initial values) ---
        mesh_type, subdivisions, num_vertices = self.mesh_manager.get_mesh_info()
        ambient_strength = self.lighting_manager.get_ambient_strength()
        color_mode_str = self.lighting_manager.get_color_mode_string()

        self.fps_label = self.ui_manager.add_element(
            Label(10, 10, "FPS: 0", color=(255, 255, 0), font_family="Fonts/Silkscreen-Regular.ttf")
        )
        self.mesh_label = self.ui_manager.add_element(
            Label(10, 40, f"Mesh: {mesh_type}", color=(255, 255, 0),
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        self.subdivision_label = self.ui_manager.add_element(
            Label(10, 70, f"Subdivisions: {subdivisions}", color=(255, 255, 0),
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        self.num_vertices_label = self.ui_manager.add_element(
            Label(600, 10, f"Vertices: {num_vertices}", color=(255, 255, 0),
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        self.ambient_label = self.ui_manager.add_element(
            Label(600, 40, f"Ambient: {ambient_strength:.1f}", color=(255, 255, 0),
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        self.color_mode_label = self.ui_manager.add_element(
            Label(600, 70, color_mode_str, color=(255, 255, 0),
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        # --- Buttons (Link to handler methods) ---
        self.next_mesh_button = self.ui_manager.add_element(
            Button(10, 100, 150, 30, "Next Mesh", self.handle_next_mesh, # Use handler
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255), font_size=18)
        )
        self.increase_subdiv_button = self.ui_manager.add_element(
            Button(10, 140, 200, 30, "Add Subdivision", self.handle_increase_subdivision, # Use handler
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255),
                   font_size=18)
        )
        self.wireframe_button = self.ui_manager.add_element(
            Button(10, 180, 200, 30, "Toggle Wireframe", self.toggle_wireframe, # Can stay direct
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255),
                   font_size=16)
        )
        self.increase_ambient_button = self.ui_manager.add_element(
            Button(10, 220, 200, 30, "Increase Ambient", self.handle_increase_ambient, # Use handler
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255),
                   font_size=16)
        )
        self.decrease_ambient_button = self.ui_manager.add_element(
            Button(10, 260, 200, 30, "Decrease Ambient", self.handle_decrease_ambient, # Use handler
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255),
                   font_size=16)
        )
        self.toggle_color_button = self.ui_manager.add_element(
            Button(10, 300, 200, 30, "Toggle Color Mode", self.handle_toggle_color_mode, # Use handler
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255),
                   font_size=16)
        )
        self.cycle_color_button = self.ui_manager.add_element(
            Button(10, 340, 200, 30, "Cycle Mesh Color", self.handle_cycle_color, # Use handler
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255),
                   font_size=16)
        )

    # --- UI Update Methods ---
    def update_mesh_labels(self):
        """Updates UI labels related to the mesh."""
        mesh_type, subdivisions, num_vertices = self.mesh_manager.get_mesh_info()
        self.mesh_label.text = f"Mesh: {mesh_type}"
        self.subdivision_label.text = f"Subdivisions: {subdivisions}"
        self.num_vertices_label.text = f"Vertices: {num_vertices}"

    def update_lighting_labels(self):
        """Updates UI labels related to lighting."""
        self.ambient_label.text = f"Ambient: {self.lighting_manager.get_ambient_strength():.1f}"
        self.color_mode_label.text = self.lighting_manager.get_color_mode_string()

    # --- UI Handler Methods (Call managers and update UI) ---
    def handle_next_mesh(self):
        self.mesh_manager.next_mesh()
        self.update_mesh_labels() # Update labels after action

    def handle_increase_subdivision(self):
        self.mesh_manager.increase_subdivision()
        self.update_mesh_labels() # Update labels after action

    def toggle_wireframe(self): # This directly modifies app state
        self.wireframe = not self.wireframe
        self.wireframe_button.text = "Disable Wireframe" if self.wireframe else "Enable Wireframe"

    def handle_increase_ambient(self):
        self.lighting_manager.increase_ambient()
        self.update_lighting_labels() # Update labels after action

    def handle_decrease_ambient(self):
        self.lighting_manager.decrease_ambient()
        self.update_lighting_labels() # Update labels after action

    def handle_toggle_color_mode(self):
        self.lighting_manager.toggle_color_mode()
        self.update_lighting_labels() # Update labels after action

    def handle_cycle_color(self):
        self.lighting_manager.cycle_color()
        # No label update needed here unless mesh color itself was displayed

    # --- Core Methods ---
    def initialize(self):
        print("OpenGL version:", glGetString(GL_VERSION).decode())
        print("GLSL version:", glGetString(GL_SHADING_LANGUAGE_VERSION).decode())

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glClearColor(0.1, 0.1, 0.1, 1)

        # Create shader and renderer
        try:
            self.compile = CompileShader([("shaders/vert_shader_lit.vert", "vertex shader"),
                                         ("shaders/frag_shader_lit.frag", "fragment shader")])
            shader_id = self.compile.get_program_id()
            if not shader_id:
                 raise RuntimeError("Failed to compile or link shaders.")
            self.renderer = Renderer(shader_id)
        except Exception as e:
            print(f"Error initializing shader or renderer: {e}")
            pg.quit()
            quit()

        # Initial mesh is loaded by MeshManager constructor, check if it succeeded
        if self.mesh_manager.get_mesh() is None:
             # MeshManager should have printed an error, but we double-check
             raise RuntimeError("Failed to load initial mesh via MeshManager.")

        # Set up camera projection and pass to renderer
        self.camera.setPerspective(45.0, self.width/self.height, 0.1, 50.0)
        if self.renderer:
            self.renderer.set_projection_matrix(self.camera.projectionMatrix)

    def update(self):
        super().update() # Handles input, UI updates, clock tick

        fps = self.clock.get_fps()
        self.fps_label.text = f"FPS: {fps:.1f}"

        delta_time = self.clock.get_time() / 1000.0

        self.camera_controller.update(self.input, delta_time)

        if not self.paused:
            if self.theta >= 360:
                self.theta = 0
            self.theta = (self.theta + self.rotation_speed * delta_time)

    def render_opengl(self):

        current_mesh = self.mesh_manager.get_mesh() # Get mesh from manager

        if not self.renderer or not current_mesh:
            return # Skip if renderer or mesh isn't ready

        self.camera.updateViewMatrix()

        model = Matrix44.from_y_rotation(np.radians(self.theta)) @ Matrix44.from_x_rotation(np.radians(self.theta * 0.5))

        t = pg.time.get_ticks() / 1000.0

        # Call the renderer, passing the lighting manager
        self.renderer.render_mesh(
            mesh=current_mesh,
            camera=self.camera,
            model_matrix=model,
            lighting_manager=self.lighting_manager, # Pass the manager object
            time=t,
            wireframe=self.wireframe
        )

        # Disable face culling after rendering the scene for UI
        glDisable(GL_CULL_FACE)

    def cleanup(self):
        """Override cleanup to release resources before OpenGL context is destroyed."""
        print("Cleaning up application resources...")
        try:
            # Clean up managers first (which handle GPU resources)
            if hasattr(self, 'mesh_manager') and self.mesh_manager:
                self.mesh_manager.cleanup()
        except Exception as e:
            print(f"Warning during cleanup: {e}")
        
        # Call base class cleanup (which might destroy OpenGL context)
        super().cleanup()


if __name__ == '__main__':
    app = None # Define app outside try block for finally
    try:
        app = LitMeshViewerApp()
        app.run()
    except Exception as e:
        print(f"An error occurred during runtime: {e}")
        import traceback
        traceback.print_exc() # Print detailed traceback
    finally:
        # Ensure cleanup runs even if errors occur during run()
        if app:
            app.cleanup() # Explicitly call cleanup
