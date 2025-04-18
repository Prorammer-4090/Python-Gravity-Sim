from typing import Dict, Type, List
import time

from core.ecs.entity import Entity
from core.ecs.systems import System, TransformSystem

class World:
    """
    Container for all entities and systems, representing the game world
    """
    def __init__(self):
        self.systems: Dict[Type[System], System] = {}
        self.last_update_time = time.time()
        
        # Register default systems
        self.add_system(TransformSystem())
    
    def add_system(self, system: System) -> None:
        """
        Add a system to the world
        """
        self.systems[type(system)] = system
    
    def get_system(self, system_type: Type[System]) -> System:
        """
        Get a system by type
        """
        return self.systems.get(system_type)
    
    def create_entity(self, name: str = "Entity", parent: Entity = None) -> Entity:
        """
        Create a new entity in this world
        """
        return Entity(name, parent)
    
    def destroy_entity(self, entity: Entity) -> None:
        """
        Destroy an entity and all its children
        """
        entity.destroy()
    
    def update(self, dt) -> float:
        """
        Update all systems
        
        Returns:
            Time delta in seconds since last update
        """
        
        # Update systems
        # Note: TransformSystem should come first to ensure transforms are up to date
        transform_system = self.systems.get(TransformSystem)
        if transform_system:
            transform_system.update(dt)
        
        # Update other systems
        for system_type, system in self.systems.items():
            if system_type != TransformSystem:
                system.update(dt)
                
        return dt