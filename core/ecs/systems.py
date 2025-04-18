from typing import List, Set, Dict, Type
import numpy as np
import pygame as pg
from math import pi

from core.ecs.entity import Entity
from core.ecs.components import Component, TransformComponent, CameraComponent, CameraControllerComponent
from helpers.transform import Transform

class System:
    """Base class for all ECS systems"""
    def update(self, dt: float) -> None:
        pass

class TransformSystem(System):
    """
    System responsible for updating entity transforms
    """
    def update(self, dt: float) -> None:
        # Get all entities with transform components
        all_entities = Entity.get_all_entities()
        
        # First update local transforms for all entities
        for entity in all_entities:
            self._update_local_transform(entity)
        
        # Then update world transforms starting from root entities
        root_entities = [e for e in all_entities if e.parent is None]
        for root in root_entities:
            self._update_world_transform_recursive(root)
    
    def _update_local_transform(self, entity: Entity) -> None:
        """Update entity's local transform matrix based on transform component"""
        transform = entity.get_component(TransformComponent)
        if transform:
            entity.local_matrix = Transform.compose(
                transform.position,
                transform.rotation,
                transform.scale
            )
        else:
            entity.local_matrix = np.identity(4, dtype=np.float32)
    
    def _update_world_transform_recursive(self, entity: Entity) -> None:
        """
        Update entity's world transform and propagate to children
        """
        if entity.parent:
            # world_matrix = parent.world_matrix * self.local_matrix
            entity.world_matrix = np.matmul(entity.parent.world_matrix, entity.local_matrix)
        else:
            entity.world_matrix = entity.local_matrix.copy()
        
        # Recursively update children
        for child in entity.children:
            self._update_world_transform_recursive(child)

class CameraSystem(System):
    """System for processing camera components"""
    def update(self, dt: float) -> None:
        camera_entities = Entity.get_entities_with_component(CameraComponent)
        
        for entity in camera_entities:
            camera_component = entity.get_component(CameraComponent)
            # Update view matrix and check movement state for each camera
            self._update_view_matrix(entity, camera_component)
            self._check_movement_state(entity, camera_component)
    
    def _update_view_matrix(self, entity: Entity, camera: CameraComponent) -> None:
        """Update the view matrix for a camera entity"""
        # View matrix is the inverse of the world transform
        camera.view_matrix = Transform.inverse(entity.world_matrix)
    
    def _check_movement_state(self, entity: Entity, camera: CameraComponent) -> None:
        """Check if the camera is moving and update its state"""
        # Extract current position and orientation from world matrix
        position = np.array([
            entity.world_matrix[3, 0],
            entity.world_matrix[3, 1],
            entity.world_matrix[3, 2]
        ])
        orientation = entity.world_matrix[:3, :3]
        
        # Initialize last_position and last_orientation if they're None
        if camera.last_position is None:
            camera.last_position = position.copy()
        if camera.last_orientation is None:
            camera.last_orientation = orientation.copy()
        
        # Detect changes in position or orientation
        position_changed = not np.allclose(position, camera.last_position, atol=1e-6)
        orientation_changed = not np.allclose(orientation, camera.last_orientation, atol=1e-6)
        
        # Update movement tracking state if any change detected
        if position_changed or orientation_changed:
            camera.is_moving = True
            camera.last_movement_time = pg.time.get_ticks()
            camera.last_position = position.copy()
            camera.last_orientation = orientation.copy()
        elif camera.is_moving and (pg.time.get_ticks() - camera.last_movement_time) > camera.movement_cooldown:
            camera.is_moving = False
    
    def get_ray_from_mouse(self, camera_entity: Entity, mouse_pos, screen_size):
        """
        Generate a world-space ray from the camera through a screen-space point.
        
        Args:
            camera_entity: The entity with the camera component
            mouse_pos (tuple): (x, y) mouse position in screen coordinates
            screen_size (tuple): (width, height) of the screen in pixels
        
        Returns:
            tuple: (ray_origin, ray_direction) 
        """
        camera_component = camera_entity.get_component(CameraComponent)
        if not camera_component:
            return None
        
        # Make sure the view matrix is up to date
        self._update_view_matrix(camera_entity, camera_component)
        
        # Extract camera position from world matrix
        position = np.array([
            camera_entity.world_matrix[3, 0],
            camera_entity.world_matrix[3, 1],
            camera_entity.world_matrix[3, 2]
        ])
        
        # Convert screen coordinates to normalized device coordinates (-1 to 1)
        x = (2.0 * mouse_pos[0]) / screen_size[0] - 1.0
        y = 1.0 - (2.0 * mouse_pos[1]) / screen_size[1]  # Flip y for screen space
        
        # Create clip space point at the near plane
        clip_space = np.array([x, y, -1.0, 1.0])
        
        # Transform to world space through inverse view-projection matrix
        view_projection_matrix = camera_component.projection_matrix @ camera_component.view_matrix
        inverse_view_projection = Transform.inverse(view_projection_matrix)
        world_space = inverse_view_projection @ clip_space
        
        # Calculate and normalize ray direction
        world_space_dir = world_space[:3] / world_space[3]
        ray_direction = world_space_dir - position
        ray_direction = ray_direction / np.linalg.norm(ray_direction)
        
        return position, ray_direction

class CameraControllerSystem(System):
    """System for processing camera controller components and handling input"""
    
    def update(self, dt: float, input_handler) -> None:
        """
        Update all camera controllers based on input
        
        Args:
            dt: Delta time in seconds
            input_handler: Object providing input information
        """
        controller_entities = Entity.get_entities_with_component(CameraControllerComponent)
        
        for entity in controller_entities:
            controller = entity.get_component(CameraControllerComponent)
            
            # Skip if no input handler or controller
            if not input_handler or not controller:
                continue
            
            # Update keyboard and mouse controls
            self._update_keyboard_controls(entity, controller, input_handler, dt)
            
            if controller.mouse_enabled:
                self._update_mouse_controls(entity, controller, input_handler)
    
    def _update_keyboard_controls(self, entity: Entity, controller: CameraControllerComponent, 
                                 input_handler, delta_time: float) -> None:
        """
        Handle keyboard input for camera movement and rotation
        """
        # Calculate frame-adjusted movement and rotation amounts
        move_amount = controller.units_per_second * delta_time
        rotate_amount = controller.degrees_per_second * (pi / 180) * delta_time
        
        transform = entity.get_component(TransformComponent)
        if not transform:
            return
            
        # Get the look attachment entity
        look_attachment = controller.look_attachment
        
        # Process movement inputs
        if input_handler.key_held(controller.key_move_forwards):
            self._translate_entity(entity, 0, 0, -move_amount)
        
        if input_handler.key_held(controller.key_move_backwards):
            self._translate_entity(entity, 0, 0, move_amount)
        
        if input_handler.key_held(controller.key_move_left):
            self._translate_entity(entity, -move_amount, 0, 0)
        
        if input_handler.key_held(controller.key_move_right):
            self._translate_entity(entity, move_amount, 0, 0)
        
        if input_handler.key_held(controller.key_move_up):
            self._translate_entity(entity, 0, move_amount, 0)
        
        if input_handler.key_held(controller.key_move_down):
            self._translate_entity(entity, 0, -move_amount, 0)
        
        # Process rotation inputs
        if input_handler.key_held(controller.key_turn_right):
            self._rotate_entity_y(entity, -rotate_amount)
        
        if input_handler.key_held(controller.key_turn_left):
            self._rotate_entity_y(entity, rotate_amount)
        
        # Pitch control with look attachment
        if look_attachment and look_attachment.has_component(TransformComponent):
            if input_handler.key_held(controller.key_look_up):
                self._rotate_entity_x(look_attachment, rotate_amount)
            
            if input_handler.key_held(controller.key_look_down):
                self._rotate_entity_x(look_attachment, -rotate_amount)
    
    def _update_mouse_controls(self, entity: Entity, controller: CameraControllerComponent, 
                              input_handler) -> None:
        """
        Handle mouse input for camera rotation
        """
        # Get the look attachment entity
        look_attachment = controller.look_attachment
        if not look_attachment:
            return
            
        # Check if left mouse button is pressed
        if input_handler.get_mouse_state()["left"]:
            if not controller.is_dragging:  # Start of new drag
                controller.is_dragging = True
                controller.last_mouse_pos = input_handler.mouse_pos
            else:  # Continue drag
                dx, dy = input_handler.mouse_motion
                
                # Apply horizontal rotation to camera body
                self._rotate_entity_y(entity, -dx * controller.mouse_sensitivity)
                
                # Apply vertical rotation to pitch control
                self._rotate_entity_x(look_attachment, -dy * controller.mouse_sensitivity)
        else:
            controller.is_dragging = False  # End drag when button released
    
    def _translate_entity(self, entity: Entity, x: float, y: float, z: float) -> None:
        """
        Translate entity by local xyz amounts
        """
        transform = entity.get_component(TransformComponent)
        if transform:
            # Convert local direction to world space using rotation
            rot_matrix = Transform.rotation(*transform.rotation)
            # Apply local translation (simplified for minimal transformation)
            local_dir = np.array([x, y, z, 0])
            world_dir = rot_matrix @ local_dir
            
            # Update position
            px, py, pz = transform.position
            transform.position = (px + world_dir[0], py + world_dir[1], pz + world_dir[2])
    
    def _rotate_entity_y(self, entity: Entity, angle: float) -> None:
        """
        Rotate entity around Y axis
        """
        transform = entity.get_component(TransformComponent)
        if transform:
            x, y, z = transform.rotation
            transform.rotation = (x, y + angle, z)
    
    def _rotate_entity_x(self, entity: Entity, angle: float) -> None:
        """
        Rotate entity around X axis
        """
        transform = entity.get_component(TransformComponent)
        if transform:
            x, y, z = transform.rotation
            transform.rotation = (x + angle, y, z)