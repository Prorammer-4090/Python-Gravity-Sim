import pygame as pg
from pygame.locals import *
import numpy as np
from OpenGL.GL import *
from pyrr import Matrix44, Vector3
import math

from core.compile_shader import CompileShader
from core.window import Window
from core.ui import Button, Label

# Import ECS classes
from core.ecs.world import World
from core.ecs.entity import Entity
from core.ecs.components import TransformComponent
from core.ecs.components import Component
from core.ecs.systems import TransformSystem, System
from helpers.transform import Transform

# Import mesh classes for visualization
from meshes.polyhedronGeo import PolyhedronGeometry
from meshes.torusGeo import TorusGeometry

# Define new components for celestial bodies
class RotationComponent(Component):
    """Component for autonomous rotation behavior"""
    def __init__(self, rotation_speed=(0, 0, 0)):
        self.rotation_speed = rotation_speed  # Degrees per second on each axis

class OrbitComponent(Component):
    """Component for orbital movement"""
    def __init__(self, 
                 center=(0, 0, 0),         # Center point to orbit around
                 radius=1.0,               # Orbit radius
                 orbit_speed=10.0,         # Degrees per second
                 inclination=0.0,          # Orbit inclination in degrees
                 initial_angle=0.0,        # Starting angle in degrees
                 eccentricity=0.0):        # Orbit eccentricity (0=circle, 0.99=nearly line)
        self.center = center
        self.radius = radius
        self.orbit_speed = orbit_speed
        self.inclination = inclination
        self.current_angle = initial_angle
        self.eccentricity = min(max(eccentricity, 0.0), 0.99)  # Clamp between 0 and 0.99

# Define systems for these components
class RotationSystem(System):
    """System that handles rotation of entities"""
    def update(self, dt):
        all_entities = Entity.get_all_entities()
        
        for entity in all_entities:
            # Check if entity has both required components
            if entity.has_component(RotationComponent) and entity.has_component(TransformComponent):
                rotation_component = entity.get_component(RotationComponent)
                transform_component = entity.get_component(TransformComponent)
                
                # Apply rotation based on rotation speed and delta time
                rotation = transform_component.rotation
                speed = rotation_component.rotation_speed
                
                new_rotation = (
                    (rotation[0] + speed[0] * dt) % 360,
                    (rotation[1] + speed[1] * dt) % 360,
                    (rotation[2] + speed[2] * dt) % 360
                )
                
                transform_component.rotation = new_rotation

class OrbitSystem(System):
    """System that handles orbital movement of entities"""
    def update(self, dt):
        all_entities = Entity.get_all_entities()
        
        for entity in all_entities:
            # Check if entity has both required components
            if entity.has_component(OrbitComponent) and entity.has_component(TransformComponent):
                orbit_component = entity.get_component(OrbitComponent)
                transform_component = entity.get_component(TransformComponent)
                
                # Update current angle
                orbit_component.current_angle += orbit_component.orbit_speed * dt
                orbit_component.current_angle %= 360.0
                
                # Calculate new position based on Kepler's laws
                angle_rad = math.radians(orbit_component.current_angle)
                inclination_rad = math.radians(orbit_component.inclination)
                
                # Calculate distance from focus based on eccentricity and angle
                # Using simplified orbital equation: r = a(1-e²)/(1+e*cos(θ))
                # where a = semi-major axis, e = eccentricity, θ = angle
                a = orbit_component.radius / (1 - orbit_component.eccentricity)
                distance = a * (1 - orbit_component.eccentricity**2) / (1 + orbit_component.eccentricity * math.cos(angle_rad))
                
                # Calculate position in orbital plane
                x = distance * math.cos(angle_rad)
                z = distance * math.sin(angle_rad)
                
                # Apply inclination
                y = z * math.sin(inclination_rad)
                z = z * math.cos(inclination_rad)
                
                # Set new position (maintaining local coordinate system if it's a child)
                transform_component.position = (x, y, z)

class ECSDemo(Window):
    def __init__(self):
        # Initialize window
        self.screen_size = [1024, 768]
        super().__init__(self.screen_size)
        
        # Store dimensions explicitly
        self.width = self.screen_size[0]
        self.height = self.screen_size[1]
        
        # Initialize ECS world
        self.world = World()
        
        # Add our new systems to the world
        self.world.add_system(RotationSystem())
        self.world.add_system(OrbitSystem())
        
        # Camera settings
        self.camera_pos = np.array([0.0, 15.0, 40.0])
        self.target_pos = np.array([0.0, 0.0, 0.0])
        self.camera_speed = 0.1
        
        # Simulation settings
        self.paused = False
        self.wireframe = True
        self.time_scale = 1.0
        self.selected_entity_index = 0
        self.show_orbits = True
        
        # Create UI elements
        self.fps_label = self.ui_manager.add_element(
            Label(10, 10, "FPS: 0", color=(255, 255, 0), font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        self.entity_name_label = self.ui_manager.add_element(
            Label(10, 40, "Selected: None", color=(255, 255, 0), 
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        self.entity_count_label = self.ui_manager.add_element(
            Label(10, 70, "Entities: 0", color=(255, 255, 0), 
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        # Control buttons
        self.next_entity_button = self.ui_manager.add_element(
            Button(10, 100, 150, 30, "Next Entity", self.select_next_entity, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255), font_size=16)
        )
        
        self.wireframe_button = self.ui_manager.add_element(
            Button(10, 140, 180, 30, "Toggle Wireframe", self.toggle_wireframe, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255), font_size=16)
        )
        
        self.pause_button = self.ui_manager.add_element(
            Button(10, 180, 150, 30, "Pause", self.toggle_pause, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255), font_size=16)
        )
        
        self.speed_up_button = self.ui_manager.add_element(
            Button(10, 220, 150, 30, "Speed Up", self.speed_up, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255), font_size=16)
        )
        
        self.slow_down_button = self.ui_manager.add_element(
            Button(10, 260, 150, 30, "Slow Down", self.slow_down, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255), font_size=16)
        )
        
        self.orbit_button = self.ui_manager.add_element(
            Button(10, 300, 150, 30, "Hide Orbits", self.toggle_orbits, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255), font_size=16)
        )
        
        self.time_scale_label = self.ui_manager.add_element(
            Label(10, 340, f"Time Scale: {self.time_scale:.1f}x", color=(255, 255, 0), 
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
    
    def initialize(self):
        print("OpenGL version:", glGetString(GL_VERSION).decode())
        print("GLSL version:", glGetString(GL_SHADING_LANGUAGE_VERSION).decode())
        
        # Configure OpenGL
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        
        # Create shader
        self.compile = CompileShader([("shaders/vert_shader.vert", "vertex shader"), 
                                      ("shaders/frag_shader.frag", "fragment shader")])
        self.shader = self.compile.get_program_id()
        glUseProgram(self.shader)
        
        # Get uniform locations
        self.proj_loc = glGetUniformLocation(self.shader, "projection")
        self.view_loc = glGetUniformLocation(self.shader, "view")
        self.model_loc = glGetUniformLocation(self.shader, "model")
        self.color_loc = glGetUniformLocation(self.shader, "objectColor")
        
        # Set up projection matrix
        self.proj = Matrix44.perspective_projection(45, self.width/self.height, 0.1, 1000.0)
        glUniformMatrix4fv(self.proj_loc, 1, GL_FALSE, self.proj.astype(np.float32))
        
        # Set up view matrix
        self.view = Matrix44.look_at(
            eye=Vector3(self.camera_pos),
            target=Vector3(self.target_pos),
            up=Vector3([0.0, 1.0, 0.0])
        )
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, self.view.astype(np.float32))
        
        # Create meshes for visualization
        self.create_meshes()
        
        # Set up solar system hierarchy using ECS
        self.create_solar_system()
        
        # Create orbit visualization
        self.create_orbit_visualizations()
    
    def create_meshes(self):
        # Dictionary to store different mesh types
        self.meshes = {}
        
        # Create different shapes for different celestial bodies
        self.meshes["sun"] = PolyhedronGeometry(radius=1.0, polyhedron_type="icosahedron", subdivisions=4)
        self.meshes["planet"] = PolyhedronGeometry(radius=1.0, polyhedron_type="octahedron", subdivisions=4)
        self.meshes["moon"] = PolyhedronGeometry(radius=1.0, polyhedron_type="tetrahedron", subdivisions=4)
        self.meshes["ring"] = TorusGeometry(major_radius=1.0, minor_radius=0.1, radial_segments=16, tubular_segments=48)
        
        # Create a circle for orbit visualization
        self.meshes["orbit"] = self.create_circle_geometry(segments=64)
        
        # Load meshes to GPU
        for name, mesh in self.meshes.items():
            if not mesh.gpu_load():
                print(f"Failed to load mesh: {name}")
    
    def create_circle_geometry(self, segments=32, radius=1.0):
        """Create a simple circle geometry for orbit visualization"""
        # Create a simple circle mesh for orbit paths
        vertices = []
        indices = []
        
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            
            # Position, Normal, UV
            vertices.extend([x, 0.0, z, 0.0, 1.0, 0.0, 0.0, 0.0])
            
            # Add indices for line loop
            indices.append(i)
            indices.append((i + 1) % segments)
        
        # Create a simple mesh object
        class CircleGeometry:
            def __init__(self, vertices, indices):
                self.vertices = np.array(vertices, dtype=np.float32)
                self.indices = np.array(indices, dtype=np.uint32)
                self.vao_id = None
                self.num_vertices = len(indices)
            
            def gpu_load(self):
                # Set up VAO
                self.vao_id = glGenVertexArrays(1)
                glBindVertexArray(self.vao_id)
                
                # VBO for vertices
                vbo_id = glGenBuffers(1)
                glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
                glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
                
                # Vertex positions (3 floats)
                glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(GLfloat), ctypes.c_void_p(0))
                glEnableVertexAttribArray(0)
                
                # Vertex normals (3 floats)
                glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(GLfloat), ctypes.c_void_p(3 * sizeof(GLfloat)))
                glEnableVertexAttribArray(1)
                
                # Vertex UVs (2 floats)
                glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 8 * sizeof(GLfloat), ctypes.c_void_p(6 * sizeof(GLfloat)))
                glEnableVertexAttribArray(2)
                
                # EBO for indices
                ebo_id = glGenBuffers(1)
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo_id)
                glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
                
                # Unbind
                glBindVertexArray(0)
                glBindBuffer(GL_ARRAY_BUFFER, 0)
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
                
                return True
        
        return CircleGeometry(vertices, indices)
    
    def create_solar_system(self):
        # Define astronomical data (with artistic adjustments for visualization)
        # Values are not to scale but represent relative differences
        
        # Sun at the center
        self.sun = self.world.create_entity("Sun")
        self.sun.add_component(TransformComponent(
            position=(0, 0, 0),
            rotation=(0, 0, 0),
            scale=3.0
        ))
        self.sun.add_component(RotationComponent(
            rotation_speed=(0, 5, 0)  # Sun rotates slowly on its axis
        ))
        
        # Mercury
        self.mercury = self.world.create_entity("Mercury")
        self.mercury.add_component(TransformComponent(
            position=(5, 0, 0),
            scale=0.4
        ))
        self.mercury.add_component(RotationComponent(
            rotation_speed=(0, 10, 0)  # Mercury rotates slowly
        ))
        self.mercury.add_component(OrbitComponent(
            radius=5.0,
            orbit_speed=47.87,  # Fastest orbit
            inclination=7.0,
            eccentricity=0.206  # Mercury has high eccentricity
        ))
        
        # Venus
        self.venus = self.world.create_entity("Venus")
        self.venus.add_component(TransformComponent(
            position=(7, 0, 0),
            scale=0.9
        ))
        self.venus.add_component(RotationComponent(
            rotation_speed=(0, -5, 0)  # Venus rotates retrograde (opposite direction)
        ))
        self.venus.add_component(OrbitComponent(
            radius=7.0,
            orbit_speed=35.02,
            inclination=3.4,
            eccentricity=0.007  # Nearly circular
        ))
        
        # Earth
        self.earth = self.world.create_entity("Earth")
        self.earth.add_component(TransformComponent(
            position=(10, 0, 0),
            scale=1.0
        ))
        self.earth.add_component(RotationComponent(
            rotation_speed=(0, 36.5, 0)  # Earth rotates once per day
        ))
        self.earth.add_component(OrbitComponent(
            radius=10.0,
            orbit_speed=29.78,
            inclination=0.0,  # Reference plane
            eccentricity=0.017  # Nearly circular
        ))
        
        # Moon orbiting Earth
        self.moon = self.world.create_entity("Moon", parent=self.earth)
        self.moon.add_component(TransformComponent(
            position=(2, 0, 0),
            scale=0.27
        ))
        self.moon.add_component(RotationComponent(
            rotation_speed=(0, 13.2, 0)  # Tidally locked to Earth
        ))
        self.moon.add_component(OrbitComponent(
            radius=2.0,
            orbit_speed=120.0,  # Moon orbits Earth quickly
            inclination=5.1,
            eccentricity=0.055
        ))
        
        # Mars
        self.mars = self.world.create_entity("Mars")
        self.mars.add_component(TransformComponent(
            position=(15, 0, 0),
            scale=0.53
        ))
        self.mars.add_component(RotationComponent(
            rotation_speed=(0, 35.0, 0)  # Similar to Earth
        ))
        self.mars.add_component(OrbitComponent(
            radius=15.0,
            orbit_speed=24.13,
            inclination=1.8,
            eccentricity=0.093  # Moderately eccentric
        ))
        
        # Jupiter
        self.jupiter = self.world.create_entity("Jupiter")
        self.jupiter.add_component(TransformComponent(
            position=(20, 0, 0),
            scale=2.0
        ))
        self.jupiter.add_component(RotationComponent(
            rotation_speed=(0, 87.0, 0)  # Jupiter rotates very fast
        ))
        self.jupiter.add_component(OrbitComponent(
            radius=20.0,
            orbit_speed=13.07,
            inclination=1.3,
            eccentricity=0.048
        ))
        
        # Saturn
        self.saturn = self.world.create_entity("Saturn")
        self.saturn.add_component(TransformComponent(
            position=(25, 0, 0),
            scale=1.7
        ))
        self.saturn.add_component(RotationComponent(
            rotation_speed=(0, 80.0, 0)  # Saturn also rotates quickly
        ))
        self.saturn.add_component(OrbitComponent(
            radius=25.0,
            orbit_speed=9.69,
            inclination=2.5,
            eccentricity=0.056
        ))
        
        # Saturn's ring
        self.saturn_ring = self.world.create_entity("Saturn Ring", parent=self.saturn)
        self.saturn_ring.add_component(TransformComponent(
            position=(0, 0, 0),
            rotation=(90, 0, 0),  # Rotate to make ring flat
            scale=(2.5, 2.5, 0.1)  # Scale to make ring thin
        ))
        
        # Store entities in a list for easy selection
        self.entities = [
            self.sun, self.mercury, self.venus, self.earth, self.moon, 
            self.mars, self.jupiter, self.saturn, self.saturn_ring
        ]
        self.entity_count_label.text = f"Entities: {len(self.entities)}"
        self.update_selected_entity_label()
    
    def create_orbit_visualizations(self):
        """Create visualization entities for orbits"""
        self.orbit_entities = []
        
        # Create orbit visualization for each planet (not the sun or rings)
        for entity in self.entities:
            if entity.has_component(OrbitComponent) and entity.parent is None:
                # Create orbit visualization entity
                orbit_viz = self.world.create_entity(f"{entity.name} Orbit")
                
                # Get orbit component data
                orbit_comp = entity.get_component(OrbitComponent)
                
                # Add transform with appropriate scale for the orbit
                orbit_viz.add_component(TransformComponent(
                    position=(0, 0, 0),
                    rotation=(orbit_comp.inclination, 0, 0),
                    scale=(orbit_comp.radius, 1.0, orbit_comp.radius)
                ))
                
                # Store in list
                self.orbit_entities.append(orbit_viz)
    
    def update(self):
        super().update()
        
        # Update FPS display
        fps = self.clock.get_fps()
        self.fps_label.text = f"FPS: {fps:.1f}"
        
        self.update_selected_entity_label()
        
        # Calculate delta time
        dt = 1.0 / max(fps, 1.0)  # Avoid division by zero
        
        # Skip physics update if paused
        if not self.paused:
            # Update the ECS world with scaled time
            self.world.update()
        
        # Handle camera movement
        self.handle_camera_movement(dt)
    
    def handle_camera_movement(self, dt):
        # Calculate camera movement vectors
        front_vec = self.target_pos - self.camera_pos
        front_vec = front_vec / np.linalg.norm(front_vec)  # Normalize
        
        # Calculate right vector (perpendicular to front and world up)
        world_up = np.array([0.0, 1.0, 0.0])
        right_vec = np.cross(front_vec, world_up)
        right_vec = right_vec / np.linalg.norm(right_vec)  # Normalize
        
        # Handle camera movement
        keys = pg.key.get_pressed()
        speed = self.camera_speed * (3 if pg.key.get_mods() & pg.KMOD_SHIFT else 1)
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
            movement += np.array([0, 1, 0]) * speed
        if keys[pg.K_e]:
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
        # The uniform will be set in render_opengl when the shader is active
    
    def render_opengl(self):
        glUseProgram(self.shader)
        
        # Update view matrix uniform now that the shader is active
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, self.view.astype(np.float32))

        # Update time uniform
        t = pg.time.get_ticks() / 1000.0  # Get time in seconds
        time_loc = glGetUniformLocation(self.shader, "time")
        glUniform1f(time_loc, t)

        # Set wireframe mode if enabled
        if self.wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        
        # Render orbit visualizations first (if enabled)
        if self.show_orbits:
            for orbit_entity in self.orbit_entities:
                # Set color for orbit lines (a subtle gray)
                glUniform3f(self.color_loc, 0.4, 0.4, 0.4)
                
                # Use the world matrix from the entity
                model_matrix = orbit_entity.world_matrix
                glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, model_matrix.astype(np.float32))
                
                # Render the orbit
                orbit_mesh = self.meshes["orbit"]
                glBindVertexArray(orbit_mesh.vao_id)
                glDrawElements(GL_LINES, orbit_mesh.num_vertices, GL_UNSIGNED_INT, None)
        
        # Render all celestial bodies
        self.render_entity(self.sun)
        
        # Render entities that have orbit components (planets)
        for entity in self.entities:
            if entity.has_component(OrbitComponent) and entity != self.moon:
                self.render_entity(entity)
        
        # Restore polygon mode
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        # Disable face culling for UI
        glDisable(GL_CULL_FACE)
        
        # Unbind VAO and shader
        glBindVertexArray(0)
        glUseProgram(0)
    
    def render_entity(self, entity, parent_matrix=None):
        """Recursively render an entity and all its children"""
        # Get the mesh type based on entity name
        mesh_type = self.get_mesh_type_for_entity(entity)
        
        # Set color based on entity type
        self.set_entity_color(entity)
        
        # Use the world matrix from the entity
        model_matrix = entity.world_matrix
        
        # Apply model matrix
        glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, model_matrix.astype(np.float32))
        
        # Render the entity
        if mesh_type in self.meshes:
            mesh = self.meshes[mesh_type]
            glBindVertexArray(mesh.vao_id)
            glDrawElements(GL_TRIANGLES, mesh.num_vertices, GL_UNSIGNED_INT, None)
        
        # Render all children
        for child in entity.children:
            self.render_entity(child)
    
    def set_entity_color(self, entity):
        """Set color uniform based on entity type"""
        name = entity.name.lower()
        
        if "sun" in name:
            glUniform3f(self.color_loc, 1.0, 0.7, 0.0)  # Yellow-orange
        elif "mercury" in name:
            glUniform3f(self.color_loc, 0.7, 0.7, 0.7)  # Gray
        elif "venus" in name:
            glUniform3f(self.color_loc, 0.9, 0.7, 0.5)  # Beige
        elif "earth" in name:
            glUniform3f(self.color_loc, 0.0, 0.5, 0.8)  # Blue
        elif "moon" in name:
            glUniform3f(self.color_loc, 0.8, 0.8, 0.8)  # Light gray
        elif "mars" in name:
            glUniform3f(self.color_loc, 0.8, 0.3, 0.1)  # Red-orange
        elif "jupiter" in name:
            glUniform3f(self.color_loc, 0.8, 0.6, 0.4)  # Tan
        elif "saturn" in name and "ring" not in name:
            glUniform3f(self.color_loc, 0.9, 0.8, 0.5)  # Light tan
        elif "ring" in name:
            glUniform3f(self.color_loc, 0.7, 0.6, 0.3)  # Dark tan
        else:
            glUniform3f(self.color_loc, 0.8, 0.8, 0.8)  # Default white-ish
    
    def get_mesh_type_for_entity(self, entity):
        """Get the appropriate mesh type based on entity name"""
        name = entity.name.lower()
        if "sun" in name:
            return "sun"
        elif "ring" in name:
            return "ring"
        elif "moon" in name:
            return "moon"
        elif "mercury" in name or "venus" in name or "earth" in name or "mars" in name or "jupiter" in name or "saturn" in name:
            return "planet"
        elif "orbit" in name:
            return "orbit"
        else:
            return "planet"  # Default
    
    def select_next_entity(self):
        """Select the next entity in the list"""
        self.selected_entity_index = (self.selected_entity_index + 1) % len(self.entities)
        self.update_selected_entity_label()
    
    def update_selected_entity_label(self):
        """Update the label showing the currently selected entity"""
        selected = self.entities[self.selected_entity_index]
        transform = selected.get_component(TransformComponent)
        
        # Get the local position from the transform component
        local_pos = transform.position
        
        # Get orbit info if available
        orbit_info = ""
        if selected.has_component(OrbitComponent):
            orbit = selected.get_component(OrbitComponent)
            orbit_info = f" | Orbit: {orbit.orbit_speed:.1f}°/s"
        
        # Get rotation info if available
        rotation_info = ""
        if selected.has_component(RotationComponent):
            rotation = selected.get_component(RotationComponent)
            rotation_info = f" | Rotation: {rotation.rotation_speed[1]:.1f}°/s"
        
        # For children entities, also show the world position
        if selected.parent:
            # Calculate world position from the world matrix
            world_matrix = selected.world_matrix
            world_pos = (world_matrix[0, 3], world_matrix[1, 3], world_matrix[2, 3])
            pos_str = f"Local: ({local_pos[0]:.1f}, {local_pos[1]:.1f}, {local_pos[2]:.1f}) | World: ({world_pos[0]:.1f}, {world_pos[1]:.1f}, {world_pos[2]:.1f})"
        else:
            # For root entities, local and world positions are the same
            pos_str = f"({local_pos[0]:.1f}, {local_pos[1]:.1f}, {local_pos[2]:.1f})"
        
        self.entity_name_label.text = f"Selected: {selected.name} {pos_str}{orbit_info}{rotation_info}"
    
    def toggle_wireframe(self):
        """Toggle wireframe rendering mode"""
        self.wireframe = not self.wireframe
        self.wireframe_button.text = "Disable Wireframe" if self.wireframe else "Enable Wireframe"
    
    def toggle_pause(self):
        """Toggle simulation pause state"""
        self.paused = not self.paused
        self.pause_button.text = "Resume" if self.paused else "Pause"
    
    def toggle_orbits(self):
        """Toggle orbit visualization"""
        self.show_orbits = not self.show_orbits
        self.orbit_button.text = "Show Orbits" if not self.show_orbits else "Hide Orbits"
    
    def speed_up(self):
        """Increase simulation speed"""
        self.time_scale = min(self.time_scale * 1.5, 10.0)
        self.time_scale_label.text = f"Time Scale: {self.time_scale:.1f}x"
    
    def slow_down(self):
        """Decrease simulation speed"""
        self.time_scale = max(self.time_scale / 1.5, 0.1)
        self.time_scale_label.text = f"Time Scale: {self.time_scale:.1f}x"

if __name__ == '__main__':
    app = ECSDemo()
    app.run()