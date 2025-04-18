from core.ecs.entity import Entity
from core.ecs.components import TransformComponent, CameraControllerComponent
from core.ecs.systems import CameraControllerSystem

class CameraController(Entity):
    """
    Controller for managing camera movement and rotation based on user input.
    
    Creates an entity hierarchy with controller component for camera movement,
    using the ECS architecture.
    
    Parameters:
        name (str): Name of the controller entity
        units_per_second (float): Movement speed in world units per second
        degrees_per_second (float): Rotation speed in degrees per second
        mouse_sensitivity (float): Multiplier for mouse movement
        mouse_enabled (bool): Whether mouse control is enabled
    """
    def __init__(
        self,
        name: str = "CameraController",
        units_per_second: float = 2.0,
        degrees_per_second: float = 60.0,
        mouse_sensitivity: float = 0.1,
        mouse_enabled: bool = True
    ):
        super().__init__(name=name)
        
        # Add transform component
        self.add_component(TransformComponent())
        
        # Create pitch control entity as child
        self.look_attachment = Entity(name=f"{name}_PitchControl")
        self.add_child(self.look_attachment)
        self.look_attachment.add_component(TransformComponent())
        
        # Add controller component
        controller_component = CameraControllerComponent(
            units_per_second=units_per_second,
            degrees_per_second=degrees_per_second,
            mouse_sensitivity=mouse_sensitivity,
            mouse_enabled=mouse_enabled
        )
        controller_component.look_attachment = self.look_attachment
        self.add_component(controller_component)
        
        # Cache the controller system for convenience
        self._controller_system = CameraControllerSystem()
    
    def update(self, input_handler, dt: float) -> None:
        """
        Update the camera controller based on input
        
        Args:
            input_handler: Object providing input information
            dt (float): Delta time in seconds
        """
        self._controller_system.update(dt, input_handler)
    
    def attach_camera(self, camera: Entity) -> None:
        """
        Attach a camera entity to this controller
        
        Args:
            camera: Camera entity to be controlled
        """
        self.look_attachment.add_child(camera)
