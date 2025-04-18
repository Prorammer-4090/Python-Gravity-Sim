import numpy as np
from typing import Tuple, Optional

from core.ecs.entity import Entity
from core.ecs.components import TransformComponent, CameraComponent
from core.ecs.systems import CameraSystem

class Camera(Entity):
    """
    A 3D Camera entity that allows for viewing of the 3D scene.
    
    Creates an Entity with TransformComponent and CameraComponent to handle
    camera properties and operations using the ECS architecture.
    
    Parameters:
        name (str): Name of the camera entity
        angle_of_view (float): Vertical field of view in degrees
        aspect_ratio (float): Width/height ratio of the viewport
        near (float): Distance to near clipping plane
        far (float): Distance to far clipping plane
    """
    def __init__(
        self, 
        name: str = "Camera", 
        angle_of_view: float = 60, 
        aspect_ratio: float = 1, 
        near: float = 0.1, 
        far: float = 1000
    ):
        super().__init__(name=name)
        
        # Add TransformComponent for position and orientation
        self.add_component(TransformComponent())
        
        # Add CameraComponent for camera-specific properties
        self.add_component(CameraComponent(
            angle_of_view=angle_of_view,
            aspect_ratio=aspect_ratio,
            near=near,
            far=far
        ))
        
        # Cache for common camera system operations
        self._camera_system = CameraSystem()
    
    def set_perspective(self, angle_of_view: float = 60, aspect_ratio: float = 1, near: float = 0.1, far: float = 1000) -> None:
        """Set camera to perspective projection mode"""
        camera_component = self.get_component(CameraComponent)
        if camera_component:
            camera_component.angle_of_view = angle_of_view
            camera_component.aspect_ratio = aspect_ratio
            camera_component.near = near
            camera_component.far = far
            camera_component.projection_type = "perspective"
            camera_component.update_projection_matrix()
    
    def set_orthographic(
        self, 
        left: float = -1, 
        right: float = 1, 
        bottom: float = -1, 
        top: float = 1, 
        near: float = -1, 
        far: float = 1
    ) -> None:
        """Set camera to orthographic projection mode"""
        camera_component = self.get_component(CameraComponent)
        if camera_component:
            camera_component.left = left
            camera_component.right = right
            camera_component.bottom = bottom
            camera_component.top = top
            camera_component.near = near
            camera_component.far = far
            camera_component.projection_type = "orthographic"
            camera_component.update_projection_matrix()
    
    def is_moving(self) -> bool:
        """Check if the camera is currently moving"""
        camera_component = self.get_component(CameraComponent)
        if camera_component:
            return camera_component.is_moving
        return False
    
    def get_view_matrix(self) -> Optional[np.ndarray]:
        """Get the camera's current view matrix"""
        camera_component = self.get_component(CameraComponent)
        if camera_component:
            # Ensure view matrix is up to date
            self._camera_system._update_view_matrix(self, camera_component)
            return camera_component.view_matrix
        return None
    
    def get_projection_matrix(self) -> Optional[np.ndarray]:
        """Get the camera's current projection matrix"""
        camera_component = self.get_component(CameraComponent)
        if camera_component:
            return camera_component.projection_matrix
        return None
    
    def get_ray_from_mouse(self, mouse_pos: Tuple[int, int], screen_size: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a ray from the camera through the given screen position
        
        Args:
            mouse_pos: (x, y) mouse position in screen coordinates
            screen_size: (width, height) of the screen in pixels
        
        Returns:
            tuple: (ray_origin, ray_direction) where both are numpy arrays
        """
        return self._camera_system.get_ray_from_mouse(self, mouse_pos, screen_size)