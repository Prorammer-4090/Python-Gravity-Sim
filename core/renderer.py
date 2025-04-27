import numpy as np
from OpenGL.GL import *
from pyrr import Matrix44
# from helpers.camera import Camera # For type hinting
# from meshes.mesh_data import MeshData # For type hinting
# from helpers.lighting_manager import LightingManager # For type hinting

class Renderer:
    def __init__(self, shader_program_id):
        if not glIsProgram(shader_program_id):
            raise ValueError("Invalid shader program ID provided to Renderer.")
        self.shader = shader_program_id
        self._get_uniform_locations()

    def _get_uniform_locations(self):
        """Cache uniform locations for efficiency."""
        glUseProgram(self.shader) # Ensure shader is active for glGetUniformLocation
        self.locations = {
            "projection": glGetUniformLocation(self.shader, "projection"),
            "view": glGetUniformLocation(self.shader, "view"),
            "model": glGetUniformLocation(self.shader, "model"),
            "time": glGetUniformLocation(self.shader, "time"),
            "ambientStrength": glGetUniformLocation(self.shader, "ambientStrength"),
            "ambientColor": glGetUniformLocation(self.shader, "ambientColor"),
            "meshColor": glGetUniformLocation(self.shader, "meshColor"),
            "useCustomColor": glGetUniformLocation(self.shader, "useCustomColor"),
            # Add other uniforms if needed
        }
        glUseProgram(0) # Unbind shader

        for name, loc in self.locations.items():
            if loc == -1:
                print(f"Warning: Uniform '{name}' not found in shader program {self.shader}")

    def set_projection_matrix(self, matrix: Matrix44):
        """Sets the projection matrix uniform."""
        if self.locations["projection"] != -1:
            glUseProgram(self.shader)
            glUniformMatrix4fv(self.locations["projection"], 1, GL_TRUE, matrix.astype(np.float32))
            glUseProgram(0)

    def render_mesh(self, mesh, camera, model_matrix: Matrix44,
                    lighting_manager, # Accept LightingManager object
                    time: float, wireframe: bool = False):
        """Renders a given mesh with specified parameters using LightingManager."""
        if not mesh or mesh.vao_id is None:
            print("Renderer: Invalid or unloaded mesh provided.")
            return
        if not lighting_manager:
             print("Renderer: LightingManager not provided.")
             return

        glUseProgram(self.shader)

        # --- Update Uniforms ---
        # Time
        if self.locations["time"] != -1:
            glUniform1f(self.locations["time"], time)

        # Lighting (Get values from LightingManager)
        if self.locations["ambientStrength"] != -1:
            glUniform1f(self.locations["ambientStrength"], lighting_manager.get_ambient_strength())
        if self.locations["ambientColor"] != -1:
            glUniform3fv(self.locations["ambientColor"], 1, lighting_manager.get_ambient_color())
        if self.locations["meshColor"] != -1:
            glUniform3fv(self.locations["meshColor"], 1, lighting_manager.get_mesh_color())
        if self.locations["useCustomColor"] != -1:
            glUniform1i(self.locations["useCustomColor"], int(lighting_manager.get_use_custom_color()))

        # Matrices
        if self.locations["view"] != -1:
            glUniformMatrix4fv(self.locations["view"], 1, GL_TRUE, camera.viewMatrix.astype(np.float32))
        if self.locations["model"] != -1:
            glUniformMatrix4fv(self.locations["model"], 1, GL_FALSE, model_matrix.astype(np.float32))
        # Projection matrix is assumed to be set via set_projection_matrix

        # --- Draw Call ---
        glBindVertexArray(mesh.vao_id)

        original_polygon_mode = glGetIntegerv(GL_POLYGON_MODE)
        if wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        # Use mesh.num_vertices (assuming it's the index count for glDrawElements)
        glDrawElements(GL_TRIANGLES, mesh.num_vertices, GL_UNSIGNED_INT, None)

        glPolygonMode(GL_FRONT_AND_BACK, original_polygon_mode[0])

        # --- Cleanup ---
        glBindVertexArray(0)
        glUseProgram(0)
        # Leave face culling enabled; main app disables it for UI