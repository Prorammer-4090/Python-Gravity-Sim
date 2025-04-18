import pygame as pg
from pygame.locals import *
import numpy as np
from OpenGL.GL import *
from pyrr import Matrix44, Vector3
import math
import random

from core.compile_shader import CompileShader
from core.window import Window
from core.ui import Button, Label

# Import ECS classes
from core.ecs.world import World
from core.ecs.entity import Entity
from core.ecs.components import Component, TransformComponent
from core.ecs.systems import System

# Import mesh classes for visualization
from meshes.polyhedronGeo import PolyhedronGeometry

# Define components for simulation
class VelocityComponent(Component):
    """Component for storing velocity"""
    def __init__(self, velocity=(0, 0, 0)):
        self.velocity = velocity  # Units per second
        
class CollisionComponent(Component):
    """Component for collision detection"""
    def __init__(self, radius=1.0, elasticity=0.8, mass=1.0):
        self.radius = radius
        self.elasticity = elasticity  # Bounce factor (0-1)
        self.mass = mass              # Object mass for collision response

class ColorComponent(Component):
    """Component for storing object color"""
    def __init__(self, color=(1.0, 1.0, 1.0)):
        self.color = color

# Define systems
class MovementSystem(System):
    """System that updates positions based on velocity"""
    def update(self, dt):
        all_entities = Entity.get_all_entities()
        
        for entity in all_entities:
            if entity.has_component(TransformComponent) and entity.has_component(VelocityComponent):
                transform = entity.get_component(TransformComponent)
                velocity = entity.get_component(VelocityComponent)
                
                # Update position based on velocity
                pos = transform.position
                vel = velocity.velocity
                transform.position = (
                    pos[0] + vel[0] * dt,
                    pos[1] + vel[1] * dt,
                    pos[2] + vel[2] * dt
                )

class CollisionSystem(System):
    """System that handles collisions"""
    def __init__(self, boundary_size):
        super().__init__()
        self.boundary_size = boundary_size
        
    def update(self, dt):
        # Get all entities with transform, velocity, and collision components
        entities = Entity.get_entities_with_components(
            TransformComponent, VelocityComponent, CollisionComponent)
        
        # Check boundary collisions
        for entity in entities:
            self._check_boundary_collision(entity)
        
        # Check entity-to-entity collisions
        self._check_entity_collisions(entities)
    
    def _check_boundary_collision(self, entity):
        """Check and handle collisions with boundary walls"""
        transform = entity.get_component(TransformComponent)
        velocity = entity.get_component(VelocityComponent)
        collision = entity.get_component(CollisionComponent)
        
        position = transform.position
        radius = collision.radius
        elasticity = collision.elasticity
        half_size = self.boundary_size / 2
        
        # Check for collisions with each wall and reflect velocity
        # X-axis walls
        if position[0] - radius < -half_size:
            transform.position = (-half_size + radius, position[1], position[2])
            velocity.velocity = (-velocity.velocity[0] * elasticity, velocity.velocity[1], velocity.velocity[2])
        elif position[0] + radius > half_size:
            transform.position = (half_size - radius, position[1], position[2])
            velocity.velocity = (-velocity.velocity[0] * elasticity, velocity.velocity[1], velocity.velocity[2])
        
        # Y-axis walls
        if position[1] - radius < -half_size:
            transform.position = (position[0], -half_size + radius, position[2])
            velocity.velocity = (velocity.velocity[0], -velocity.velocity[1] * elasticity, velocity.velocity[2])
        elif position[1] + radius > half_size:
            transform.position = (position[0], half_size - radius, position[2])
            velocity.velocity = (velocity.velocity[0], -velocity.velocity[1] * elasticity, velocity.velocity[2])
        
        # Z-axis walls
        if position[2] - radius < -half_size:
            transform.position = (position[0], position[1], -half_size + radius)
            velocity.velocity = (velocity.velocity[0], velocity.velocity[1], -velocity.velocity[2] * elasticity)
        elif position[2] + radius > half_size:
            transform.position = (position[0], position[1], half_size - radius)
            velocity.velocity = (velocity.velocity[0], velocity.velocity[1], -velocity.velocity[2] * elasticity)
    
    def _check_entity_collisions(self, entities):
        """Check and handle entity-to-entity collisions"""
        # Compare each pair of entities once
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i + 1:]:
                self._handle_collision(entity1, entity2)
    
    def _handle_collision(self, entity1, entity2):
        """Handle collision between two entities using elastic collision physics"""
        transform1 = entity1.get_component(TransformComponent)
        velocity1 = entity1.get_component(VelocityComponent)
        collision1 = entity1.get_component(CollisionComponent)
        
        transform2 = entity2.get_component(TransformComponent)
        velocity2 = entity2.get_component(VelocityComponent)
        collision2 = entity2.get_component(CollisionComponent)
        
        pos1 = np.array(transform1.position)
        pos2 = np.array(transform2.position)
        
        # Calculate distance between objects
        distance_vector = pos2 - pos1
        distance = np.linalg.norm(distance_vector)
        min_distance = collision1.radius + collision2.radius
        
        # Check if collision occurred
        if distance < min_distance:
            # Normalize the collision vector
            if distance == 0:  # Prevent division by zero
                collision_normal = np.array([1, 0, 0])
            else:
                collision_normal = distance_vector / distance
            
            # Calculate relative velocity
            vel1 = np.array(velocity1.velocity)
            vel2 = np.array(velocity2.velocity)
            rel_velocity = vel1 - vel2
            
            # Calculate impulse
            vel_along_normal = np.dot(rel_velocity, collision_normal)
            
            # Objects moving apart - skip collision resolution
            if vel_along_normal > 0:
                return
            
            # Calculate elasticity
            e = min(collision1.elasticity, collision2.elasticity)
            
            # Calculate impulse scalar
            m1 = collision1.mass
            m2 = collision2.mass
            impulse_scalar = -(1 + e) * vel_along_normal / (1/m1 + 1/m2)
            
            # Apply impulse
            impulse = impulse_scalar * collision_normal
            
            velocity1.velocity = tuple(vel1 + (impulse / m1))
            velocity2.velocity = tuple(vel2 - (impulse / m2))
            
            # Separate objects to prevent sticking
            overlap = min_distance - distance
            separation = collision_normal * overlap * 0.5
            transform1.position = tuple(pos1 - separation)
            transform2.position = tuple(pos2 + separation)

class ECSVisualTest(Window):
    def __init__(self):
        # Initialize window
        self.screen_size = [1024, 768]
        super().__init__(self.screen_size)
        
        # Initialize ECS world
        self.world = World()
        self.boundary_size = 20.0  # Size of the cube boundary
        
        # Add systems
        self.movement_system = MovementSystem()
        self.collision_system = CollisionSystem(self.boundary_size)
        
        self.world.add_system(self.movement_system)
        self.world.add_system(self.collision_system)
        
        # Camera settings
        self.camera_pos = np.array([0.0, 0.0, 30.0])
        self.target_pos = np.array([0.0, 0.0, 0.0])
        self.camera_rotation = [0, 0]  # Pitch, yaw
        self.camera_speed = 0.1
        
        # Simulation settings
        self.paused = False
        self.wireframe = False
        self.time_scale = 1.0
        self.gravity_enabled = True
        
        # Mouse controls
        self.mouse_captured = False
        self.last_mouse_pos = (0, 0)
        self.mouse_sensitivity = 0.2
        
        # Add UI elements
        self.fps_label = self.ui_manager.add_element(
            Label(10, 10, "FPS: 0", color=(255, 255, 0), font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        self.entity_count_label = self.ui_manager.add_element(
            Label(10, 40, "Entities: 0", color=(255, 255, 0), 
                  font_family="Fonts/Silkscreen-Regular.ttf")
        )
        
        self.wireframe_button = self.ui_manager.add_element(
            Button(10, 80, 180, 30, "Toggle Wireframe", self.toggle_wireframe, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255), font_size=16)
        )
        
        self.pause_button = self.ui_manager.add_element(
            Button(10, 120, 150, 30, "Pause", self.toggle_pause, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255), font_size=16)
        )
        
        self.add_entity_button = self.ui_manager.add_element(
            Button(10, 160, 150, 30, "Add Object", self.add_random_entity, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255), font_size=16)
        )
        
        self.toggle_gravity_button = self.ui_manager.add_element(
            Button(10, 200, 150, 30, "Disable Gravity", self.toggle_gravity, 
                   font_family="Fonts/Silkscreen-Regular.ttf", color=(34, 221, 34, 255), font_size=16)
        )
    
    def initialize(self):
        print("OpenGL version:", glGetString(GL_VERSION).decode())
        
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
        self.proj = Matrix44.perspective_projection(
            45, self.screen_size[0]/self.screen_size[1], 0.1, 100.0)
        glUniformMatrix4fv(self.proj_loc, 1, GL_FALSE, self.proj.astype(np.float32))
        
        # Create meshes
        self.create_meshes()
        
        # Create boundary cube
        self.create_boundary()
        
        # Create initial entities
        for _ in range(100):
            self.add_random_entity()
    
    def create_meshes(self):
        self.meshes = {}
        
        # Polyhedron meshes with different subdivisions
        self.meshes["tetrahedron"] = PolyhedronGeometry(radius=1.0, polyhedron_type="tetrahedron", subdivisions=4)
        self.meshes["octahedron"] = PolyhedronGeometry(radius=1.0, polyhedron_type="octahedron", subdivisions=4)
        self.meshes["icosahedron"] = PolyhedronGeometry(radius=1.0, polyhedron_type="icosahedron", subdivisions=4)
        
        # Boundary cube
        self.meshes["cube"] = PolyhedronGeometry(radius=1.0, polyhedron_type="cube", subdivisions=0)
        
        # Load meshes to GPU
        for name, mesh in self.meshes.items():
            if not mesh.gpu_load():
                print(f"Failed to load mesh: {name}")
    
    def create_boundary(self):
        # Create the boundary cube entity
        self.boundary = self.world.create_entity("Boundary")
        self.boundary.add_component(TransformComponent(
            position=(0, 0, 0),
            scale=self.boundary_size
        ))
        self.boundary.add_component(ColorComponent(color=(0.2, 0.2, 0.2)))
    
    def add_random_entity(self):
        # Random position inside boundary
        half_size = self.boundary_size / 2 - 2.0  # Stay away from edges
        position = (
            random.uniform(-half_size, half_size),
            random.uniform(-half_size, half_size),
            random.uniform(-half_size, half_size)
        )
        
        # Random scale between 0.5 and 2.0
        scale = 0.5
        
        # Random velocity
        velocity = (
            random.uniform(-5.0, 5.0),
            random.uniform(-5.0, 5.0),
            random.uniform(-5.0, 5.0)
        )
        
        # Random color
        color = (
            random.uniform(0.3, 1.0),
            random.uniform(0.3, 1.0),
            random.uniform(0.3, 1.0)
        )
        
        # Choose random mesh type
        mesh_type = random.choice(["tetrahedron", "octahedron", "icosahedron"])
        
        # Create entity
        entity = self.world.create_entity(f"{mesh_type.capitalize()}")
        
        entity.add_component(TransformComponent(
            position=position,
            rotation=(
                random.uniform(0, 360),
                random.uniform(0, 360),
                random.uniform(0, 360)
            ),
            scale=scale
        ))
        
        entity.add_component(VelocityComponent(velocity=velocity))
        
        entity.add_component(CollisionComponent(
            radius=scale,
            elasticity=random.uniform(0.7, 0.9),
            mass=scale**3  # Mass proportional to volume
        ))
        
        entity.add_component(ColorComponent(color=color))
        
        # Save mesh type for rendering
        setattr(entity, "mesh_type", mesh_type)
        
        # Update entity count
        self.entity_count_label.text = f"Entities: {len(Entity.get_entities_with_component(CollisionComponent))}"
    
    def update(self):
        super().update()
        
        # Update FPS display
        fps = self.clock.get_fps()
        self.fps_label.text = f"FPS: {fps:.1f}"
        
        # Calculate delta time
        dt = 1.0 / max(fps, 1.0)  # Avoid division by zero
        
        # Apply gravity if enabled
        if self.gravity_enabled:
            for entity in Entity.get_entities_with_component(VelocityComponent):
                if entity != self.boundary:
                    velocity = entity.get_component(VelocityComponent)
                    velocity.velocity = (
                        velocity.velocity[0],
                        velocity.velocity[1] - 9.8 * dt,  # Apply gravity in Y direction
                        velocity.velocity[2]
                    )
        
        # Update physics
        if not self.paused:
            self.world.update(self.time)
        
        # Handle camera movement
        self.handle_camera_movement(dt)
        
        # Check for mouse capture toggle
        keys = pg.key.get_pressed()
        if keys[pg.K_ESCAPE] and self.mouse_captured:
            self.release_mouse()
    
    def handle_camera_movement(self, dt):
        # If mouse is captured, handle rotation
        if self.mouse_captured:
            mouse_pos = pg.mouse.get_pos()
            
            # Calculate mouse movement
            mouse_dx = mouse_pos[0] - self.last_mouse_pos[0]
            mouse_dy = mouse_pos[1] - self.last_mouse_pos[1]
            
            # Update camera rotation (yaw, pitch)
            self.camera_rotation[1] += mouse_dx * self.mouse_sensitivity
            self.camera_rotation[0] += mouse_dy * self.mouse_sensitivity
            
            # Clamp pitch to avoid gimbal lock
            self.camera_rotation[0] = max(-89, min(89, self.camera_rotation[0]))
            
            # Reset mouse position to center to avoid hitting screen edges
            center_x, center_y = self.width // 2, self.height // 2
            pg.mouse.set_pos(center_x, center_y)
            self.last_mouse_pos = (center_x, center_y)
            
            # Calculate camera direction from the updated rotation
            pitch = math.radians(self.camera_rotation[0])
            yaw = math.radians(self.camera_rotation[1])
            
            camera_direction = np.array([
                math.cos(yaw) * math.cos(pitch),
                math.sin(pitch),
                math.sin(yaw) * math.cos(pitch)
            ])
            
            # Normalize the direction
            camera_direction = camera_direction / np.linalg.norm(camera_direction)
            
            # Calculate right vector
            right_vec = np.cross(camera_direction, np.array([0, 1, 0]))
            if np.linalg.norm(right_vec) > 0:
                right_vec = right_vec / np.linalg.norm(right_vec)
            
            # Calculate up vector
            up_vec = np.cross(right_vec, camera_direction)
            if np.linalg.norm(up_vec) > 0:
                up_vec = up_vec / np.linalg.norm(up_vec)
            
            # Handle keyboard input for movement
            keys = pg.key.get_pressed()
            movement = np.zeros(3)
            speed = self.camera_speed * (5 if keys[pg.K_LSHIFT] else 1)
            
            if keys[pg.K_w]:
                movement += camera_direction * speed
            if keys[pg.K_s]:
                movement -= camera_direction * speed
            if keys[pg.K_a]:
                movement -= right_vec * speed
            if keys[pg.K_d]:
                movement += right_vec * speed
            if keys[pg.K_SPACE]:
                movement += np.array([0, 1, 0]) * speed
            if keys[pg.K_LCTRL]:
                movement -= np.array([0, 1, 0]) * speed
            
            # Update camera position
            self.camera_pos += movement
            
            # Update view matrix based on new position and target
            self.target_pos = self.camera_pos + camera_direction
            self.view = Matrix44.look_at(
                eye=Vector3(self.camera_pos),
                target=Vector3(self.target_pos),
                up=Vector3(up_vec)
            )
        else:
            # Simple orbital camera when mouse is not captured
            keys = pg.key.get_pressed()
            
            # Simple camera rotation
            rotation_speed = 1.0
            if keys[pg.K_LEFT]:
                self.camera_rotation[1] -= rotation_speed
            if keys[pg.K_RIGHT]:
                self.camera_rotation[1] += rotation_speed
            if keys[pg.K_UP]:
                self.camera_rotation[0] -= rotation_speed
            if keys[pg.K_DOWN]:
                self.camera_rotation[0] += rotation_speed
            
            # Clamp pitch
            self.camera_rotation[0] = max(-89, min(89, self.camera_rotation[0]))
            
            # Calculate position from spherical coordinates
            pitch = math.radians(self.camera_rotation[0])
            yaw = math.radians(self.camera_rotation[1])
            
            # Orbit distance
            orbit_radius = 30.0
            
            # Camera position based on orbit
            self.camera_pos = np.array([
                math.cos(yaw) * math.cos(pitch),
                math.sin(pitch),
                math.sin(yaw) * math.cos(pitch)
            ]) * orbit_radius
            
            # Camera always looks at center
            self.target_pos = np.array([0, 0, 0])
            
            # Update view matrix
            self.view = Matrix44.look_at(
                eye=Vector3(self.camera_pos),
                target=Vector3(self.target_pos),
                up=Vector3([0.0, 1.0, 0.0])
            )
    
    def render_opengl(self):
        glUseProgram(self.shader)
        
        # Set view matrix uniform
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, self.view.astype(np.float32))
        
        # Set wireframe mode if enabled
        if self.wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        # Render boundary cube with wireframe
        old_wireframe = self.wireframe
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)  # Always wireframe for boundary
        
        # Set color for boundary
        glUniform3f(self.color_loc, 0.3, 0.3, 0.3)  # Grey for boundary
        
        # Set model matrix for boundary
        transform = self.boundary.get_component(TransformComponent)
        model_matrix = self.create_model_matrix(transform)
        glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, model_matrix.astype(np.float32))
        
        # Render boundary
        cube_mesh = self.meshes["cube"]
        glBindVertexArray(cube_mesh.vao_id)
        glDrawElements(GL_TRIANGLES, cube_mesh.num_vertices, GL_UNSIGNED_INT, None)
        
        # Restore wireframe setting
        if not old_wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        # Render all entities with collision components
        entities = Entity.get_entities_with_component(CollisionComponent)
        for entity in entities:
            if entity == self.boundary:  # Skip boundary as it's rendered differently
                continue
            
            # Get components
            transform = entity.get_component(TransformComponent)
            color_comp = entity.get_component(ColorComponent)
            
            # Set color
            glUniform3f(self.color_loc, *color_comp.color)
            
            # Set model matrix
            model_matrix = self.create_model_matrix(transform)
            glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, model_matrix.astype(np.float32))
            
            # Get mesh type associated with entity
            mesh_type = getattr(entity, "mesh_type", "tetrahedron")
            
            # Render entity
            mesh = self.meshes.get(mesh_type, self.meshes["tetrahedron"])
            glBindVertexArray(mesh.vao_id)
            glDrawElements(GL_TRIANGLES, mesh.num_vertices, GL_UNSIGNED_INT, None)
        
        # Restore polygon mode
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        # Unbind VAO and shader
        glBindVertexArray(0)
        glUseProgram(0)
    
    def create_model_matrix(self, transform):
        """Create model matrix from transform component"""
        # Create translation matrix
        pos = transform.position
        translation = Matrix44.from_translation(Vector3(pos))
        
        # Create rotation matrices for each axis
        rot = transform.rotation
        rotation_x = Matrix44.from_x_rotation(math.radians(rot[0]))
        rotation_y = Matrix44.from_y_rotation(math.radians(rot[1]))
        rotation_z = Matrix44.from_z_rotation(math.radians(rot[2]))
        rotation = rotation_z * rotation_y * rotation_x
        
        # Create scale matrix - handle both scalar and tuple scale values
        if isinstance(transform.scale, (float, int)):
            # If scale is a single number, convert to Vector3 with uniform scale
            scale = Matrix44.from_scale(Vector3([transform.scale, transform.scale, transform.scale]))
        else:
            # If scale is already a tuple, use it directly
            scale = Matrix44.from_scale(Vector3(transform.scale))
        
        # Combine matrices: translation * rotation * scale
        return translation * rotation * scale
    
    def process_event(self, event):
        super().process_event(event)
        
        if event.type == KEYDOWN:
            if event.key == K_F1:  # Toggle mouse capture with F1
                if self.mouse_captured:
                    self.release_mouse()
                else:
                    self.capture_mouse()
        
        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1 and not self.ui_manager.is_point_over_element(event.pos):
                # Left-click not over UI - capture mouse
                self.capture_mouse()
    
    def capture_mouse(self):
        """Capture mouse for camera control"""
        pg.mouse.set_visible(False)
        self.mouse_captured = True
        self.last_mouse_pos = pg.mouse.get_pos()
    
    def release_mouse(self):
        """Release mouse capture"""
        pg.mouse.set_visible(True)
        self.mouse_captured = False
    
    def toggle_wireframe(self):
        """Toggle wireframe rendering mode"""
        self.wireframe = not self.wireframe
        self.wireframe_button.text = "Disable Wireframe" if self.wireframe else "Enable Wireframe"
    
    def toggle_pause(self):
        """Toggle simulation pause state"""
        self.paused = not self.paused
        self.pause_button.text = "Resume" if self.paused else "Pause"
    
    def toggle_gravity(self):
        """Toggle gravity on/off"""
        self.gravity_enabled = not self.gravity_enabled
        self.toggle_gravity_button.text = "Enable Gravity" if not self.gravity_enabled else "Disable Gravity"

if __name__ == '__main__':
    app = ECSVisualTest()
    app.run()
