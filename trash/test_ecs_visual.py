import unittest
import numpy as np
import math
from pyrr import Matrix44, Vector3

# Import ECS classes
from core.ecs.world import World
from core.ecs.entity import Entity
from core.ecs.components import TransformComponent
from core.ecs.systems import System

class TestECSVisual(unittest.TestCase):
    def setUp(self):
        # Reset entity counter between tests
        Entity._next_id = 1
        Entity._entities = {}
        # Create a fresh world for each test
        self.world = World()
    
    def create_model_matrix(self, transform):
        """Create model matrix from transform component"""
        # Create translation matrix
        pos = transform.position
        translation = Matrix44.from_translation(Vector3(pos))
        
        # Create rotation matrices for each axis
        rot = transform.rotation
        rotation_x = Matrix44.from_x_rotation(math.radians(rot[0]))
        rotation_y = Matrix44.from_y_rotation(math.radians(rot[1]))
        rotation_z = Matrix44.from_z_rotation(math.radians(rot[2]))
        rotation = rotation_z * rotation_y * rotation_x
        
        # Create scale matrix - handle both scalar and tuple scale values
        if isinstance(transform.scale, (float, int)):
            # If scale is a single number, convert to Vector3 with uniform scale
            scale = Matrix44.from_scale(Vector3([transform.scale, transform.scale, transform.scale]))
        else:
            # If scale is already a tuple, use it directly
            scale = Matrix44.from_scale(Vector3(transform.scale))
        
        # Combine matrices: translation * rotation * scale
        return translation * rotation * scale
    
    def test_model_matrix_creation(self):
        # Test model matrix creation
        transform = TransformComponent(
            position=(1, 2, 3),
            rotation=(45, 90, 30),
            scale=(2, 2, 2)
        )
        model_matrix = self.create_model_matrix(transform)
        
        # Verify matrix dimensions
        self.assertEqual(model_matrix.shape, (4, 4))
        
        # Verify translation part
        self.assertAlmostEqual(model_matrix[3, 0], 1)
        self.assertAlmostEqual(model_matrix[3, 1], 2)
        self.assertAlmostEqual(model_matrix[3, 2], 3)
        
        # Verify scale part
        self.assertAlmostEqual(model_matrix[0, 0], 2)
        self.assertAlmostEqual(model_matrix[1, 1], 2)
        self.assertAlmostEqual(model_matrix[2, 2], 2)

if __name__ == '__main__':
    unittest.main()