import numpy as np
import pygame
from helpers.transform import Transform
from core.entity import Entity
from numpy.linalg import inv

class Camera(Entity):
    """
    A 3D Camera that allows for viewing of the 3D scene using a perspective projection and view transformations. it includes 
    for tracking camera movement and generating rays for mouse interaction.

    Inherits from the Object3D to provides the ability to be loaded into the scene; move around the scene using transformations;
    and add child objects.

    Dependencies:
    - numpy: For matrix and vector operations
    - pygame: For timing and movement tracking
    - core.matrix: Custom Matrix class for projection calculations
    - core.object3D: Base class for 3D objects

    Parameters:
        angleOfView (float): Vertical field of view in degrees. Defaults to 60.
        aspectRatio (float): Width/height ratio of the viewport. Defaults to 1.
        near (float): Distance to near clipping plane. Defaults to 0.1.
        far (float): Distance to far clipping plane. Defaults to 1000.
    """

    def __init__(self, angleOfView=60, aspectRatio=1, near=0.1, far=1000):
        super().__init__()
        self.aspect_ratio = aspectRatio
        self.fov = angleOfView
        self.near = near
        self.far = far
        # Create projection matrix
        self.projectionMatrix = Transform.perspective(
            self.fov, self.aspect_ratio, self.near, self.far)
        self.viewMatrix = Transform.identity()
        
        # Initialize camera state tracking variables
        self.position = np.array([0.0, 0.0, 0.0])  # Current world position
        self.orientation = np.identity(3)  # Current rotation matrix
        self.last_position = self.position.copy()  # Previous position for movement detection
        self.last_orientation = self.orientation.copy()  # Previous orientation for movement detection
        self.movement_cooldown = 200  # Time in ms before camera is considered stationary
        self.last_movement_time = pygame.time.get_ticks()  # Timestamp of last movement
        self.is_currently_moving = False  # Current movement state
        
        # Initialize view matrix with current transform
        self.updateViewMatrix()

    def updateViewMatrix(self):
        """
        Calculates view matrix and updates the position tracking variables.
        """
        # Get the world matrix from the parent hierarchy
        world_matrix = self.getWorldMatrix()
        
        # Calculate view matrix as inverse of world matrix
        self.viewMatrix = inv(world_matrix)

        # Extract current position from world matrix
        self.position = np.array([
            world_matrix[0, 3],
            world_matrix[1, 3],
            world_matrix[2, 3]
        ])
        
        # Extract orientation (rotation) from world matrix
        self.orientation = world_matrix[:3, :3]

        # Detect changes in position or orientation
        position_changed = not np.allclose(self.position, self.last_position, atol=1e-6)
        orientation_changed = not np.allclose(self.orientation, self.last_orientation, atol=1e-6)

        # Update movement tracking state if any change detected
        if position_changed or orientation_changed:
            self.is_currently_moving = True
            self.last_movement_time = pygame.time.get_ticks()
            self.last_position = self.position.copy()
            self.last_orientation = self.orientation.copy()
            
    def update_projection_mat(self, width, height):
        self.projectionMatrix = Transform.perspective( self.fov, width/height, self.near, self.far)

    def is_moving(self):
        """
        Checks if the camera is moving.

        Returns:
            bool: True if the camera has moved within the movement cooldown period,
                 False if it hasn't.
        """
        current_time = pygame.time.get_ticks()
        
        # Reset movement state if cooldown period has elapsed
        if self.is_currently_moving and (current_time - self.last_movement_time) > self.movement_cooldown:
            self.is_currently_moving = False
        
        return self.is_currently_moving

    def get_ray_from_mouse(self, mouse_pos, screen_size):
        """
        Generates a world-space ray from the camera through a screen-space point.
        
        Converts mouse coordinates to normalized device coordinates, then unprojects
        through the inverse view-projection matrix to get a world-space ray.
        
        Args:
            mouse_pos (tuple): (x, y) mouse position in screen coordinates
            screen_size (tuple): (width, height) of the screen in pixels
        
        Returns:
            tuple: (ray_origin, ray_direction) where:
                  - ray_origin: numpy array [x, y, z] of ray start position
                  - ray_direction: normalized numpy array [x, y, z] of ray direction
        """

        self.updateViewMatrix()
        
        # Convert screen coordinates to normalized device coordinates (-1 to 1)
        x = (2.0 * mouse_pos[0]) / screen_size[0] - 1.0
        y = 1.0 - (2.0 * mouse_pos[1]) / screen_size[1]  # Flip y for screen space
        
        # Create clip space point at the near plane
        clip_space = np.array([x, y, -1.0, 1.0])
        
        # Transform to world space through inverse view-projection matrix
        view_projection_matrix = self.projectionMatrix @ self.viewMatrix
        inverse_view_projection = inv(view_projection_matrix)
        world_space = inverse_view_projection @ clip_space
        
        # Calculate and normalize ray direction
        if world_space[3] != 0:  # Check for division by zero
            world_space_dir = world_space[:3] / world_space[3]
        else:
            world_space_dir = world_space[:3]
            
        ray_direction = world_space_dir - self.position
        
        # Normalize ray_direction, checking for zero magnitude
        norm_direction = np.linalg.norm(ray_direction)
        if norm_direction > 1e-6: # Use a small epsilon
            ray_direction = ray_direction / norm_direction
        else:
            # Handle zero direction case, e.g., return camera's forward direction
            # Get forward direction from the camera's orientation matrix (third column, negated)
            ray_direction = -self.orientation[:, 2] 
            # Ensure it's normalized (should be if orientation is a rotation matrix)
            norm_fallback = np.linalg.norm(ray_direction)
            if norm_fallback > 1e-6:
                ray_direction = ray_direction / norm_fallback
            else:
                ray_direction = np.array([0.0, 0.0, -1.0]) # Default fallback

        return self.position, ray_direction

    def setPerspective(self, angleOfView=60, aspectRatio=1, near=0.1, far=1000):
        """Set a perspective projection matrix with the given parameters"""
        # Transform.perspective now handles degree-to-radian conversion internally
        self.projectionMatrix = Transform.perspective(
            angleOfView, aspectRatio, near, far) # Pass degrees directly

    def setOrthographic(self, left=-1, right=1, bottom=-1, top=1, near=-1, far=1):
        """Set an orthographic projection matrix with the given parameters"""
        self.projectionMatrix = Transform.orthographic(left, right, bottom, top, near, far)