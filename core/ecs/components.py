from typing import Tuple, Union
import numpy as np
from helpers.transform import Transform
import pygame as pg

class Component:
    """Base class for all ECS components"""
    pass

class TransformComponent(Component):
    """Component for spatial transformation data"""
    def __init__(
        self, 
        position: Tuple[float, float, float] = (0, 0, 0),
        rotation: Tuple[float, float, float] = (0, 0, 0),
        scale: Union[Tuple[float, float, float], float] = (1, 1, 1)
    ):
        self.position = position
        self.rotation = rotation
        
        # Handle uniform scale parameter
        if isinstance(scale, (int, float)):
            self.scale = (scale, scale, scale)
        else:
            self.scale = scale

class CameraComponent(Component):
    """Component for camera-specific data and settings"""
    def __init__(
        self,
        angle_of_view=60,
        aspect_ratio=1,
        near=0.1,
        far=1000,
        projection_type="perspective"
    ):
        self.angle_of_view = angle_of_view
        self.aspect_ratio = aspect_ratio
        self.near = near
        self.far = far
        self.projection_type = projection_type  # "perspective" or "orthographic"
        
        # Orthographic settings
        self.left = -1
        self.right = 1
        self.bottom = -1
        self.top = 1
        
        # View and projection matrices
        self.projection_matrix = None
        self.view_matrix = None
        
        # Movement tracking
        self.last_position = None
        self.last_orientation = None
        self.last_movement_time = 0
        self.is_moving = False
        self.movement_cooldown = 200  # ms
        
        # Update the projection matrix
        self.update_projection_matrix()
    
    def update_projection_matrix(self):
        """Update the projection matrix based on current settings"""
        if self.projection_type == "perspective":
            self.projection_matrix = Transform.perspective(
                self.angle_of_view, self.aspect_ratio, self.near, self.far
            )
        else:  # orthographic
            self.projection_matrix = Transform.orthographic(
                self.left, self.right, self.bottom, self.top, self.near, self.far
            )

class CameraControllerComponent(Component):
    """Component for camera movement and rotation control settings"""
    def __init__(
        self,
        units_per_second: float = 2.0,
        degrees_per_second: float = 60.0,
        mouse_sensitivity: float = 0.1,
        mouse_enabled: bool = True
    ):
        # Movement and rotation speed settings
        self.units_per_second = units_per_second
        self.degrees_per_second = degrees_per_second
        
        # Mouse control configuration
        self.mouse_enabled = mouse_enabled
        self.mouse_sensitivity = mouse_sensitivity
        self.is_dragging = False
        self.last_mouse_pos = (0, 0)
        
        # Define control key mappings
        self.key_move_forwards = "w"
        self.key_move_backwards = "s"
        self.key_move_left = "a"
        self.key_move_right = "d"
        self.key_move_up = "space"
        self.key_move_down = "z"
        self.key_turn_left = "q"
        self.key_turn_right = "e"
        self.key_look_up = "t"
        self.key_look_down = "g"
        
        # Reference to the pitch control entity (to be set by the controller)
        self.look_attachment = None
