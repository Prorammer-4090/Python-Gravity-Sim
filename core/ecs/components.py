from typing import Tuple, Union

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
