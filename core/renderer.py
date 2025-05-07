import numpy as np
from OpenGL.GL import *
from pyrr import Matrix44
from utils.uniform import Uniform
from typing import Dict
import pygame
from lights.light import Light, Shadow
from .object import Object
from core.logger import logger  # Add logger import

class Renderer:
    def __init__(self):
        # match the attribute name used in render()
        self.windowSize = pygame.display.get_surface().get_size()
        
        logger.log_message(f"Initializing Renderer with window size: {self.windowSize}", level="INFO")
        
        try:
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)
            logger.log_message("OpenGL state initialized: DEPTH_TEST and CULL_FACE enabled", level="DEBUG")
        except Exception as e:
            logger.log_error(e, context="Failed to initialize OpenGL state in Renderer")
        
        # Initialize shadow-related attributes
        self.shadows_enabled = False
        self.shadow_object = None

    def enable_shadows(self, shadow_light, strength=0.5, resolution=[512, 512]):
        """
        Enable shadow mapping pass.
        """
        self.shadows_enabled = True
        self.shadow_object = Shadow(shadow_light,
                                    strength=strength,
                                    resolution=resolution)

    def render(self, scene, clear_color=True, clear_depth=True, render_target=None):
        """
        Full scene render: optional shadow pass + main pass.
        """
        logger.log_message("Beginning render process", level="DEBUG")
        
        try:
            # gather objects
            desc_list = scene.get_descendants()
            object_list = [m for m in desc_list if isinstance(m, Object)]
            logger.log_message(f"Found {len(object_list)} renderable objects", level="DEBUG")

            # --- Shadow pass ---
            if getattr(self, 'shadows_enabled', False):
                # bind shadow FBO
                glBindFramebuffer(GL_FRAMEBUFFER,
                                  self.shadow_object.render_target.framebufferRef)
                glViewport(0, 0,
                           self.shadow_object.render_target.width,
                           self.shadow_object.render_target.height)
                glClearColor(1, 1, 1, 1)
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                glUseProgram(self.shadow_object.depth_material.program_id)
                self.shadow_object.update()
                for object in object_list:
                    if not object.visible or object.material.settings["drawStyle"] != GL_TRIANGLES:
                        continue
                    glBindVertexArray(object.vao_id)
                    # update model matrix
                    self.shadow_object.depth_material.uniforms["modelMatrix"].data = object.getWorldMatrix()
                    for uni in self.shadow_object.depth_material.uniforms.values():
                        uni.upload_data()
                    glDrawArrays(GL_TRIANGLES, 0, object.mesh.num_vertices)

            # --- Main pass setup ---
            width, height = self.windowSize
            if render_target is None:
                glBindFramebuffer(GL_FRAMEBUFFER, 0)
                glViewport(0, 0, width, height)
                logger.log_message(f"Rendering to screen with viewport {width}x{height}", level="DEBUG")
            else:
                glBindFramebuffer(GL_FRAMEBUFFER, render_target.framebufferRef)
                glViewport(0, 0, render_target.width, render_target.height)
                logger.log_message(f"Rendering to render target with viewport {render_target.width}x{render_target.height}", level="DEBUG")
                
            if clear_color: 
                glClear(GL_COLOR_BUFFER_BIT)
            if clear_depth: 
                glClear(GL_DEPTH_BUFFER_BIT)

            # Check camera matrices
            scene.camera.updateViewMatrix()
            if scene.camera.viewMatrix is None or scene.camera.projectionMatrix is None:
                logger.log_message("Camera matrices not properly initialized", level="ERROR")
                return
                
            logger.log_message(f"Camera position: {scene.camera.getWorldPosition()}", level="DEBUG")
            
            desc_list = scene.get_descendants()
            object_list = [o for o in desc_list if isinstance(o, Object)]
            light_list = [l for l in desc_list if isinstance(l, Light)]
            while len(light_list) < 4:
                light_list.append(Light())

            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            # Log OpenGL state and errors before rendering objects
            gl_error = glGetError()
            if gl_error != GL_NO_ERROR:
                logger.log_message(f"OpenGL error before rendering: {gl_error}", level="ERROR")

            for i, object in enumerate(object_list):
                try:
                    if not object.visible:
                        continue
                        
                    logger.log_message(f"Rendering object {i} with VAO_ID: {object.vao_id}", level="DEBUG")
                    
                    if object.material.program_id is None:
                        logger.log_message(f"Object {i} has invalid shader program", level="ERROR")
                        continue
                        
                    glUseProgram(object.material.program_id)
                    
                    # Check for valid VAO
                    if object.vao_id is None or object.vao_id == 0:
                        logger.log_message(f"Object {i} has invalid VAO ID: {object.vao_id}", level="ERROR")
                        continue
                        
                    glBindVertexArray(object.vao_id)

                    # matrices
                    object.material.uniforms["model"].data = object.getWorldMatrix()
                    object.material.uniforms["view"].data = scene.camera.viewMatrix
                    object.material.uniforms["projection"].data = scene.camera.projectionMatrix
                    
                    # Log matrix values for debugging
                    logger.log_message(f"Object {i} model matrix first row: {object.getWorldMatrix()[0]}", level="DEBUG")
                    logger.log_message(f"Camera view matrix first row: {scene.camera.viewMatrix[0]}", level="DEBUG")
                    
                    # lights
                    if "light0" in object.material.uniforms:
                        for i, light in enumerate(light_list):
                            object.material.uniforms[f"light{i}"].data = light

                    # camera position
                    if "viewPosition" in object.material.uniforms:
                        object.material.uniforms["view_pos"].data = scene.camera.getWorldPosition()

                    # Upload uniforms with additional validation
                    for uniform_name, uniform in object.material.uniforms.items():
                        try:
                            if uniform.variable_ref in (None, -1):
                                if uniform_name in ["model", "view", "projection"]:
                                    # These are critical uniforms that should trigger an error if missing
                                    logger.log_message(f"Critical uniform '{uniform_name}' not found in shader - 3D rendering will fail", level="ERROR")
                                elif uniform_name not in ["light0", "light1", "light2", "light3", "viewPosition"]:
                                    # Less critical uniforms
                                    logger.log_message(f"Uniform '{uniform_name}' not found in shader", level="WARNING")
                            
                            # If we have valid matrix data and a valid location, upload it
                            if uniform.data is not None and uniform.variable_ref != -1:
                                logger.log_message(f"Uploading uniform '{uniform_name}'", level="DEBUG")
                                uniform.upload_data()
                        except Exception as e:
                            logger.log_error(e, context=f"Error uploading uniform '{uniform_name}'")

                    object.material.update_render_settings()
                    
                    # Check for errors before draw
                    gl_error = glGetError()
                    if gl_error != GL_NO_ERROR:
                        logger.log_message(f"OpenGL error before drawing object {i}: {gl_error}", level="ERROR")
                        
                    # --- Draw Call ---
                    glBindVertexArray(object.vao_id)
                    
                    original_polygon_mode = glGetIntegerv(GL_POLYGON_MODE)
                    
                    # Use object.num_vertices (assuming it's the index count for glDrawElements)
                    if object.mesh.num_vertices is None or object.mesh.num_vertices <= 0:
                        logger.log_message(f"Object {i} has invalid vertex count: {object.mesh.num_vertices}", level="ERROR")
                        continue
                        
                    logger.log_message(f"Drawing object {i} with {object.mesh.num_vertices} vertices", level="DEBUG")
                    glDrawElements(GL_TRIANGLES, object.mesh.num_vertices, GL_UNSIGNED_INT, None)
                    
                    # Check for errors after draw
                    gl_error = glGetError()
                    if gl_error != GL_NO_ERROR:
                        logger.log_message(f"OpenGL error after drawing object {i}: {gl_error}", level="ERROR")

                    glPolygonMode(GL_FRONT_AND_BACK, original_polygon_mode[0])
                    
                except Exception as e:
                    logger.log_error(e, context=f"Error rendering object {i}")
                    
            # --- Cleanup ---
            glBindVertexArray(0)
            glUseProgram(0)
            
            logger.log_message("Render process completed", level="DEBUG")
            
            # Final error check
            gl_error = glGetError()
            if gl_error != GL_NO_ERROR:
                logger.log_message(f"OpenGL error at end of rendering: {gl_error}", level="ERROR")
                
        except Exception as e:
            logger.log_error(e, context="Error in render method")