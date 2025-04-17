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