from core.window import Window
from core.scene import Scene
from core.renderer import Renderer
from core.object import Object
from meshes.torusGeo import TorusGeometry
from materials.material import Material
from core.ui import Button, Label
from core.logger import logger  # Add logger import


# Vertex shader - Ensure uniform names match exactly what the Material class is looking for
VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color; 
layout(location = 2) in vec2 texCoords;

uniform mat4 model;      // Exact name must match Material's uniform
uniform mat4 view;       // Exact name must match Material's uniform
uniform mat4 projection; // Exact name must match Material's uniform

out vec3  fragColor;
out vec2  fragUV;

void main() {
    gl_Position = projection * view * model * vec4(position, 1.0);
    fragColor = color;
    fragUV = texCoords;
}
"""

# Fragment shader - Use texture color directly with less vertex color influence
FRAGMENT_SHADER = """
#version 330 core
in  vec3  fragColor; 
in  vec2  fragUV;
out vec4  outColor;

uniform sampler2D texture1;

void main() {
    // Sample texture directly 
    vec4 texColor = texture(texture1, fragUV);
    
    // Mix with vertex color but give texture more weight (80% texture, 20% vertex color)
    //outColor = mix(vec4(fragColor, 1.0), texColor, 0.8);
    outColor = texColor;
    // Uncomment this line for debugging - show pure red if UV coordinates are out of expected range
    // if(fragUV.x < 0.0 || fragUV.x > 1.0 || fragUV.y < 0.0 || fragUV.y > 1.0) outColor = vec4(1.0, 0.0, 0.0, 1.0);
}
"""

class Test(Window):
    
    
    def initialize(self):
        logger.log_message("Initializing Test application", level="INFO")
        try:
            super().initialize()                       # ← make the base window + UI manager
            self.scene = Scene(self.screenSize[0], self.screenSize[1])
            logger.log_message("Scene created", level="DEBUG")
            
            try:
                self.mesh = TorusGeometry(radial_segments=32, tubular_segments=32, minor_radius=0.5)
                logger.log_message("Torus geometry created", level="DEBUG")
            except Exception as e:
                logger.log_error(e, context="Failed to create torus geometry")
                return
                
            try:
                self.material = Material([(VERTEX_SHADER, "vertex shader"), (FRAGMENT_SHADER, "fragment shader")])
                logger.log_message(f"Material created with program ID: {self.material.program_id}", level="DEBUG")
                
                # Check if uniforms were located properly
                for name, uniform in self.material.uniforms.items():
                    logger.log_message(f"Uniform '{name}' location: {uniform.variable_ref}", level="DEBUG")
            except Exception as e:
                logger.log_error(e, context="Failed to create material")
                return
                
            try:
                self.material.set_texture("textures/stone.png")
                logger.log_message("Texture set on material", level="DEBUG")
                
                # Check if texture is loaded properly
                if self.material._texture and self.material._texture.texture_id:
                    logger.log_message(f"Texture successfully loaded with ID: {self.material._texture.texture_id}", level="INFO")
                else:
                    logger.log_message("Texture failed to load properly", level="ERROR")
            except Exception as e:
                logger.log_error(e, context="Failed to set texture")
                
            try:
                # Make sure to use texture unit 0 for main texture
                texture_unit = 0
                self.material.add_uniform("sampler2D", "texture1", 
                                     (self.material._texture.texture_id, texture_unit))
                logger.log_message(f"Added texture uniform to material with texture ID: {self.material._texture.texture_id} on unit {texture_unit}", level="DEBUG")
                
                # Verify that texture1 is in the uniforms dict and has a valid location
                texture_uniform = self.material.uniforms.get("texture1")
                if texture_uniform:
                    logger.log_message(f"Texture uniform 'texture1' location is: {texture_uniform.variable_ref}", level="INFO")
                else:
                    logger.log_message("Failed to add texture uniform to material", level="ERROR")
            except Exception as e:
                logger.log_error(e, context="Failed to add texture uniform")
                
            try:
                self.object = Object(self.mesh, self.material)
                self.scene.add(self.object)
                logger.log_message("Object created and added to scene", level="DEBUG")
            except Exception as e:
                logger.log_error(e, context="Failed to create or add object")
                return
                
            try:
                self.renderer = Renderer()
                logger.log_message("Renderer created", level="DEBUG")
            except Exception as e:
                logger.log_error(e, context="Failed to create renderer")
                return

            # Move camera to a viewable position
            try:
                self.scene.camera_controls.setPosition([0, 0, 5])
                logger.log_message(f"Camera positioned at {self.scene.camera.getWorldPosition()}", level="DEBUG")
            except Exception as e:
                logger.log_error(e, context="Failed to position camera")
            
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
            
        except Exception as e:
            logger.log_error(e, context="Error in Test.initialize()")
    
    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_button.text = "Resume" if self.paused else "Pause"
        print(f"Simulation {'paused' if self.paused else 'resumed'}")
    
    def reset_simulation(self):
        self.reset = True
        print("Simulation reset")
        
        return super().initialize()
    
    def render_opengl(self):
        try:
            logger.log_message("Starting OpenGL rendering", level="DEBUG")
            super().render_opengl()                    # ← clear the back‐buffer first
            
            # Log camera state before rendering
            camera_pos = self.scene.camera.getWorldPosition()
            logger.log_message(f"Camera position before render: {camera_pos}", level="DEBUG")
            
            # Check if matrices are initialized
            if self.scene.camera.viewMatrix is None:
                logger.log_message("Camera view matrix is None!", level="ERROR")
            if self.scene.camera.projectionMatrix is None:
                logger.log_message("Camera projection matrix is None!", level="ERROR")
                
            self.renderer.render(self.scene)            # ← then draw your 3D
            
            # Check for OpenGL errors after rendering
            from OpenGL.GL import glGetError, GL_NO_ERROR
            error = glGetError()
            if error != GL_NO_ERROR:
                logger.log_message(f"OpenGL error after rendering: {error}", level="ERROR")
                
            logger.log_message("OpenGL rendering completed", level="DEBUG")
            
        except Exception as e:
            logger.log_error(e, context="Error in render_opengl method")
        return
    
    def update(self):
        try:
            # Update FPS display
            fps = self.clock.get_fps()
            self.fps_label.text = f"FPS: {fps:.1f}"
            
            cursor_scale = self.ui_manager.cursor_scale
            self.scale_label.text = f"Scale: {cursor_scale:.2f}"
            self.scene.update(self.input, self.delta_time)

            # Adjust rotation to be frame rate-independent (e.g., 30 degrees per second)
            rotation_speed = 30.0  # Degrees per second
            if not self.paused: # Only rotate if not paused
                self.object.rotateX(rotation_speed * self.delta_time)
                self.object.rotateY(rotation_speed * 1.5 * self.delta_time) # Example different speed for Y
            
        except Exception as e:
            logger.log_error(e, context="Error in update method")
            
        return super().update()

# Start the application with appropriate logging
try:
    logger.log_message("Starting Test application", level="INFO")
    Test(screenSize=[800, 600]).run()
except Exception as e:
    logger.log_error(e, context="Error starting application")