from collections import deque
from helpers.camera import Camera
from helpers.camera_controls import CameraControls
from .texture_cache import TextureCache
from core.entity import Entity
from helpers.transform import Transform
from core.logger import logger  # Add logger import

class Scene:
    
    def __init__(self, width, height, fov=60):
        logger.log_message(f"Initializing Scene with dimensions {width}x{height}, FOV: {fov}", level="INFO")
        
        try:
            self.entities = []
            self.camera = Camera(angleOfView=fov, aspectRatio=width/height)
            
            # Log camera matrices
            if hasattr(self.camera, 'projectionMatrix'):
                logger.log_message(f"Camera projection matrix initialized: {self.camera.projectionMatrix is not None}", level="DEBUG")
            else:
                logger.log_message("Camera missing projectionMatrix attribute", level="ERROR")
                
            self.camera_controls = CameraControls()
            self.camera_controls.add(self.camera)
            self.camera_controls.setPosition([0, 0, 5])  # Start camera at a viewable position
            logger.log_message(f"Camera position set to: {self.camera.getWorldPosition()}", level="DEBUG")
            
            self.texture_cache = TextureCache()
            self.ui = []
            
        except Exception as e:
            logger.log_error(e, context="Error initializing Scene")
    
    def get_UI(self):
        return self.ui
    
    def set_UI(self, ui):
        self.ui = ui
        
    def add(self, entity):
        if not isinstance(entity, Entity):
            raise TypeError("Child must be instance of Entity")

        if self.is_descendant(entity):
            raise ValueError("Cannot add a xhild that is already a descendant.")
        self.entities.append(entity)
        entity.parent = self
        
    def remove(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)
            entity.parent = None
            
    def is_descendant(self, entity):
        for scene_entity in self.entities:
            if scene_entity == entity or scene_entity.is_descendant(entity):
                return True
            return False
        
    def get_descendants(self):
        try:
            descendants = []
            queue = deque(self.entities)
            while queue:
                node = queue.popleft()
                descendants.append(node)
                queue.extend(node.children)
            
            logger.log_message(f"Found {len(descendants)} descendants in scene", level="DEBUG")
            return descendants
            
        except Exception as e:
            logger.log_error(e, context="Error retrieving scene descendants")
            return []
    
    def getWorldMatrix(self):
        return Transform.identity()
    
    def get_texture_cache(self):
        return self.texture_cache
    
    def resize(self, width, height):
        logger.log_message(f"Resizing scene to {width}x{height}", level="DEBUG")
        try:
            self.camera.update_projection_mat(width, height)
        except Exception as e:
            logger.log_error(e, context="Error resizing scene")
    
    def update(self, input, delta_time):
        try:
            self.camera_controls.update(input, delta_time)
        except Exception as e:
            logger.log_error(e, context="Error updating camera controls")
