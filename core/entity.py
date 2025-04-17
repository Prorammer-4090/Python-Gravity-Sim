from helpers.transform import Transform
import numpy as np

class Entity:
    _next_id = 0

    def __init__(self, name="Entity", parent=None):
        self.id = Entity._next_id
        Entity._next_id += 1

        self.name = name
        self.parent = parent
        self.children = []

        self.components = {}
        self.local_matrix = np.identity(4, dtype=np.float32)
        self.world_matrix = np.identity(4, dtype=np.float32)

        if parent:
            parent.add_child(self)

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def add_component(self, component_type, data):
        self.components[component_type] = data

    def get_component(self, component_type):
        return self.components.get(component_type)

    def update_local_transform(self):
        """Update only the local transform matrix from components"""
        transform = self.get_component("Transform")
        if transform:
            self.local_matrix = Transform.compose(
                transform["position"],
                transform["rotation"],
                transform["scale"]
            )
        else:
            self.local_matrix = np.identity(4, dtype=np.float32)
        
        return self.local_matrix
            
    def update_world_transform(self):
        """Update world transform based on parent's world and local transform"""
        if self.parent:
            # Matrix multiplication: parent.world_matrix * self.local_matrix
            self.world_matrix = np.matmul(self.parent.world_matrix, self.local_matrix)
        else:
            self.world_matrix = self.local_matrix.copy()
            
        # Propagate to children
        for child in self.children:
            child.update_world_transform()
        
        return self.world_matrix
            
    def update_transform(self):
        """Update both local and world transforms in the correct order"""
        # First update local transform
        self.update_local_transform()
        
        # Then update world transform (this will recursively update children)
        self.update_world_transform()
        
        return self.world_matrix