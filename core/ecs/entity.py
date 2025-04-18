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
    
    @classmethod
    def get_entities_with_component(cls, component_type: Type[Component]) -> List['Entity']:
        """Get all entities that have a specific component type"""
        return [entity for entity in cls._entities.values() if entity.has_component(component_type)]
    
    @classmethod
    def get_entities_with_components(cls, *component_types: Type[Component]) -> List['Entity']:
        """Get all entities that have all of the specified component types"""
        return [entity for entity in cls._entities.values() 
                if all(entity.has_component(comp_type) for comp_type in component_types)]
    
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