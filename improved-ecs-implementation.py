# core/ecs/components.py
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

# core/ecs/entity.py
import numpy as np
from typing import Dict, List, Type, Optional, Any, Set, TypeVar

from core.ecs.components import Component, TransformComponent
from helpers.transform import Transform

T = TypeVar('T', bound=Component)

class Entity:
    """
    Entity class for the ECS architecture with scene graph functionality.
    Entities form a hierarchical structure and can have components attached.
    """
    _next_id = 0
    _entities: Dict[int, 'Entity'] = {}  # Registry of all entities

    def __init__(self, name: str = "Entity", parent: Optional['Entity'] = None):
        self.id = Entity._next_id
        Entity._next_id += 1
        
        # Register in global entity dictionary
        Entity._entities[self.id] = self

        self.name = name
        self.parent = None
        self.children: List['Entity'] = []
        self.components: Dict[Type[Component], Component] = {}
        
        # Transformation matrices
        self.local_matrix = np.identity(4, dtype=np.float32)
        self.world_matrix = np.identity(4, dtype=np.float32)

        # Set parent if provided
        if parent:
            parent.add_child(self)
    
    @classmethod
    def get_entity(cls, entity_id: int) -> Optional['Entity']:
        """Get entity by ID"""
        return cls._entities.get(entity_id)
    
    @classmethod
    def get_all_entities(cls) -> List['Entity']:
        """Get all entities"""
        return list(cls._entities.values())
    
    def add_child(self, child: 'Entity') -> None:
        """
        Add a child entity to this entity
        """
        if child.parent:
            child.parent.remove_child(child)
        
        self.children.append(child)
        child.parent = self
    
    def remove_child(self, child: 'Entity') -> None:
        """
        Remove a child entity from this entity
        """
        if child in self.children:
            self.children.remove(child)
            child.parent = None
    
    def add_component(self, component: Component) -> None:
        """
        Add a component to this entity
        """
        component_type = type(component)
        self.components[component_type] = component
    
    def get_component(self, component_type: Type[T]) -> Optional[T]:
        """
        Get a component by type
        """
        return self.components.get(component_type)
    
    def has_component(self, component_type: Type[Component]) -> bool:
        """
        Check if entity has a component of given type
        """
        return component_type in self.components
    
    def remove_component(self, component_type: Type[Component]) -> None:
        """
        Remove a component by type
        """
        if component_type in self.components:
            del self.components[component_type]
    
    def get_root(self) -> 'Entity':
        """
        Get the root entity in the hierarchy
        """
        if self.parent is None:
            return self
        return self.parent.get_root()
    
    def destroy(self) -> None:
        """
        Destroy this entity and all its children
        """
        # First detach from parent
        if self.parent:
            self.parent.remove_child(self)
        
        # Destroy all children
        for child in list(self.children):
            child.destroy()
        
        # Remove from registry
        if self.id in Entity._entities:
            del Entity._entities[self.id]
    
    def __repr__(self) -> str:
        return f"Entity({self.id}, {self.name})"

# core/ecs/systems.py
from typing import List, Set, Dict, Type
import numpy as np

from core.ecs.entity import Entity
from core.ecs.components import Component, TransformComponent
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

# core/ecs/world.py
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
    
    def update(self) -> float:
        """
        Update all systems
        
        Returns:
            Time delta in seconds since last update
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
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

# Example usage:
"""
# Create a world
world = World()

# Create entities
root = world.create_entity("Root")
child1 = world.create_entity("Child1", parent=root)
child2 = world.create_entity("Child2", parent=root)
grandchild = world.create_entity("Grandchild", parent=child1)

# Add components
root.add_component(TransformComponent(position=(0, 0, 0)))
child1.add_component(TransformComponent(position=(1, 0, 0)))
child2.add_component(TransformComponent(position=(0, 1, 0)))
grandchild.add_component(TransformComponent(position=(0, 0, 1)))

# Game loop
while True:
    dt = world.update()
    # ... render and other logic
"""
