import pygame
import sys
from core.input import Input
from core.ui import UIManager
import os
import ctypes
import OpenGL.GL as gl
from OpenGL.GL import shaders
import numpy as np
from core.logger import logger

class Window:
    
    def __init__(self, screenSize=[512, 512]):
        try:
            pygame.init()
            
            display_flags = pygame.DOUBLEBUF | pygame.OPENGL
            
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 1)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 8)
            
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
            
            self.screen = pygame.display.set_mode(screenSize, display_flags)
            
            try:
                pygame.display.set_caption("Gravity Simulator", "GraviSim")
                pygame.display.set_icon(pygame.image.load("Images/blackhole.png"))
            except Exception as e:
                logger.log_error(e, "Could not set window caption or icon")
                # Continue without the icon rather than failing
            
            self.running = True
            
            self.clock = pygame.time.Clock()
            
            self.input = Input()
            
            self.screenSize = screenSize
            
            self.time = 0
            
            # Create UI manager
            self.ui_manager = UIManager(self)
            
            # For switching between OpenGL and UI rendering
            self.ui_mode = False
            
            
        except Exception as e:
            logger.log_error(e, "Window initialization failed")
            raise
    
    def initialize(self):
        pass
    
    def update(self):
        pass
        
    def update_physics(self, delta_time):
        pass
    
    def render_opengl(self):
        # This is where your OpenGL rendering code would go
        pass
        
    def render_ui(self):
        try:
            logger.log_message("Starting UI rendering process", level="DEBUG")
            
            # Render UI elements to a separate surface
            ui_surface = self.ui_manager.render()
            
            if ui_surface is None:
                logger.log_message("UI surface is None, cannot render UI", level="ERROR")
                return
                
            width, height = self.screenSize
            logger.log_message(f"UI surface dimensions: {ui_surface.get_width()}x{ui_surface.get_height()}", level="DEBUG")
            
            self.delta_time = self.clock.get_time() / 1000
            
            # Create shader program for UI rendering if it doesn't exist
            if not hasattr(self, 'ui_shader'):
                logger.log_message("Creating UI shader and buffers", level="DEBUG")
                
                self.ui_vao = gl.glGenVertexArrays(1)
                gl.glBindVertexArray(self.ui_vao)
                
                vertex_shader = """
                #version 330 core
                layout(location = 0) in vec2 position;
                layout(location = 1) in vec2 texCoord;
                out vec2 uv;
                void main() {
                    gl_Position = vec4(position, 0.0, 1.0);
                    uv = texCoord;
                }
                """
                
                fragment_shader = """
                #version 330 core
                in vec2 uv;
                out vec4 fragColor;
                uniform sampler2D uiTexture;
                void main() {
                    fragColor = texture(uiTexture, uv);
                }
                """
                
                try:
                    vert = shaders.compileShader(vertex_shader, gl.GL_VERTEX_SHADER)
                    frag = shaders.compileShader(fragment_shader, gl.GL_FRAGMENT_SHADER)
                    
                    self.ui_shader = shaders.compileProgram(vert, frag)
                except Exception as e:
                    logger.log_error(e, "Failed to compile UI shaders")
                    raise
                
                quad_vertices = [
                    -1.0,  1.0,  0.0, 1.0,
                    1.0,  1.0,  1.0, 1.0,
                    1.0, -1.0,  1.0, 0.0,
                    -1.0, -1.0,  0.0, 0.0
                ]
                
                quad_vertices = np.array(quad_vertices, dtype=np.float32)
                
                self.ui_vbo = gl.glGenBuffers(1)
                gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.ui_vbo)
                gl.glBufferData(gl.GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, gl.GL_STATIC_DRAW)
                
                indices = [0, 1, 2, 0, 2, 3]
                indices = np.array(indices, dtype=np.uint32)
                self.ui_ebo = gl.glGenBuffers(1)
                gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ui_ebo)
                gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
                
                gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * 4, None)
                gl.glEnableVertexAttribArray(0)
                
                gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
                gl.glEnableVertexAttribArray(1)
                
                gl.glBindVertexArray(0)

            data = pygame.image.tostring(ui_surface, "RGBA", True)
            
            texture = gl.glGenTextures(1)
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
            
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            
            try:
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, 
                        gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
                logger.log_message("UI texture uploaded successfully", level="DEBUG")
            except Exception as e:
                logger.log_error(e, "Failed to upload UI texture data")
                return
            
            previous_blend_enabled = gl.glIsEnabled(gl.GL_BLEND)
            previous_depth_test_enabled = gl.glIsEnabled(gl.GL_DEPTH_TEST)
            previous_cull_face_enabled = gl.glIsEnabled(gl.GL_CULL_FACE)
            
            gl.glDisable(gl.GL_DEPTH_TEST)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glDisable(gl.GL_CULL_FACE)
            
            try:
                gl.glUseProgram(self.ui_shader)
                logger.log_message(f"UI shader program activated: {self.ui_shader}", level="DEBUG")
                
                texture_loc = gl.glGetUniformLocation(self.ui_shader, "uiTexture")
                if texture_loc == -1:
                    logger.log_message("Failed to locate uiTexture uniform in UI shader", level="ERROR")
                
                gl.glUniform1i(texture_loc, 0)
                
                gl.glBindVertexArray(self.ui_vao)
                gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
                gl.glBindVertexArray(0)
                
                error = gl.glGetError()
                if error != gl.GL_NO_ERROR:
                    logger.log_message(f"OpenGL error during UI rendering: {error}", level="ERROR")
                else:
                    logger.log_message("UI rendered successfully", level="DEBUG")
                
            except Exception as e:
                logger.log_error(e, "Error using UI shader program")
            
            gl.glDeleteTextures(1, [texture])
            gl.glUseProgram(0)
            
            if previous_depth_test_enabled:
                gl.glEnable(gl.GL_DEPTH_TEST)
            else:
                gl.glDisable(gl.GL_DEPTH_TEST)
                
            if previous_blend_enabled:
                gl.glEnable(gl.GL_BLEND)
            else:
                gl.glDisable(gl.GL_BLEND)
                
            if previous_cull_face_enabled:
                gl.glEnable(gl.GL_CULL_FACE)
            else:
                gl.glDisable(gl.GL_CULL_FACE)
                
            logger.log_message("UI rendering completed", level="DEBUG")
            
        except Exception as e:
            logger.log_error(e, "UI rendering failed")
            # Continue without UI rather than crashing
    
    def run(self):
        try:
            self.initialize()
            
            FIXED_DELTA = 1/60
            accumulator = 0
            current_time = pygame.time.get_ticks() / 1000

            while self.running:
                try:
                    self.clock.tick()
                    
                    self.input.update()
                    self.ui_manager.update(self.input)
                    
                    new_time = pygame.time.get_ticks() / 1000
                    frame_time = new_time - current_time
                    current_time = new_time
                    
                    if frame_time > 0.25:
                        frame_time = 0.25
                        
                    accumulator += frame_time
                    self.time += frame_time
                    
                    while accumulator >= FIXED_DELTA:
                        try:
                            self.update_physics(FIXED_DELTA)
                        except Exception as e:
                            logger.log_error(e, "Physics update failed")
                        accumulator -= FIXED_DELTA
                    
                    self.delta_time = frame_time
                    self.update()
                    
                    gl.glClearColor(0.0, 0.0, 0.0, 1.0)
                    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
                    
                    try:
                        self.render_opengl()
                    except Exception as e:
                        logger.log_error(e, "OpenGL rendering failed")
                    
                    try:
                        pygame.time.wait(1)
                        self.render_ui()
                    except Exception as e:
                        logger.log_error(e, "UI overlay failed")
                    
                    pygame.display.flip()
                    
                    if self.input.quit:
                        self.running = False
                except Exception as e:
                    logger.log_error(e, "Error in main loop")
                
            pygame.quit()
        except Exception as e:
            logger.log_error(e, "Fatal error in run method")
            pygame.quit()
        finally:
            sys.exit()