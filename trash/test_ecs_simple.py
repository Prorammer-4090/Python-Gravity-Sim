import unittest
import numpy as np

# Import ECS classes
from core.ecs.world import World
from core.ecs.entity import Entity
from core.ecs.components import Component, TransformComponent
from core.ecs.systems import System

class TestECS(unittest.TestCase):
    def setUp(self):
        # Reset entity counter between tests
        Entity._next_id = 1
        Entity._entities = {}
        # Create a fresh world for each test
        self.world = World()
    
    def test_entity_creation(self):
        # Test basic entity creation
        entity = self.world.create_entity("Test Entity")
        self.assertEqual(entity.name, "Test Entity")
        self.assertEqual(entity.id, 1)
        self.assertIn(entity.id, Entity._entities)
    
    def test_add_get_component(self):
        # Test adding and retrieving components
        entity = self.world.create_entity("Test Entity")
        
        # Add a transform component
        transform = TransformComponent(position=(1, 2, 3), rotation=(0, 90, 0), scale=2.0)
        entity.add_component(transform)
        
        # Verify component was added
        self.assertTrue(entity.has_component(TransformComponent))
        
        # Retrieve and verify component data
        retrieved = entity.get_component(TransformComponent)
        self.assertEqual(retrieved.position, (1, 2, 3))
        self.assertEqual(retrieved.rotation, (0, 90, 0))
        self.assertEqual(retrieved.scale, 2.0)
    
    def test_remove_component(self):
        # Test removing components
        entity = self.world.create_entity("Test Entity")
        
        transform = TransformComponent()
        entity.add_component(transform)
        self.assertTrue(entity.has_component(TransformComponent))
        
        entity.remove_component(TransformComponent)
        self.assertFalse(entity.has_component(TransformComponent))
    
    def test_entity_hierarchy(self):
        # Test parent-child entity relationships
        parent = self.world.create_entity("Parent")
        child = self.world.create_entity("Child", parent=parent)
        
        # Verify parent-child relationship
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children)
        
        # Test world matrix calculation
        parent.add_component(TransformComponent(position=(0, 10, 0)))
        child.add_component(TransformComponent(position=(5, 0, 0)))
        
        # Child's world position should be relative to parent
        world_matrix = child.world_matrix
        world_position = (world_matrix[0, 3], world_matrix[1, 3], world_matrix[2, 3])
        self.assertAlmostEqual(world_position[0], 5)
        self.assertAlmostEqual(world_position[1], 10)
        self.assertAlmostEqual(world_position[2], 0)
    
    def test_system_execution(self):
        # Create a test component
        class VelocityComponent(Component):
            def __init__(self, velocity=(0, 0, 0)):
                self.velocity = velocity
        
        # Create a test system that applies velocity to position
        class MovementSystem(System):
            def update(self, dt=1.0):
                all_entities = Entity.get_all_entities()
                
                for entity in all_entities:
                    if entity.has_component(TransformComponent) and entity.has_component(VelocityComponent):
                        transform = entity.get_component(TransformComponent)
                        velocity = entity.get_component(VelocityComponent)
                        
                        # Update position based on velocity
                        pos = transform.position
                        vel = velocity.velocity
                        transform.position = (
                            pos[0] + vel[0] * dt,
                            pos[1] + vel[1] * dt,
                            pos[2] + vel[2] * dt
                        )
        
        # Add system to world
        movement_system = MovementSystem()
        self.world.add_system(movement_system)
        
        # Create entity with position and velocity
        entity = self.world.create_entity("Moving Entity")
        entity.add_component(TransformComponent(position=(0, 0, 0)))
        entity.add_component(VelocityComponent(velocity=(1, 2, 3)))
        
        # Update world (execute systems)
        self.world.update(dt=2.0)
        
        # Verify position was updated correctly
        transform = entity.get_component(TransformComponent)
        self.assertEqual(transform.position, (2, 4, 6))

    def test_get_entities_with_components(self):
        # Test finding entities with specific components
        
        # Create a test component
        class TagComponent(Component):
            def __init__(self, tag=""):
                self.tag = tag
        
        # Create entities with different component combinations
        e1 = self.world.create_entity("Entity1")
        e1.add_component(TransformComponent())
        
        e2 = self.world.create_entity("Entity2")
        e2.add_component(TransformComponent())
        e2.add_component(TagComponent("test"))
        
        e3 = self.world.create_entity("Entity3")
        e3.add_component(TagComponent("other"))
        
        # Test getting entities with components
        entities_with_transform = Entity.get_entities_with_component(TransformComponent)
        self.assertEqual(len(entities_with_transform), 2)
        self.assertIn(e1, entities_with_transform)
        self.assertIn(e2, entities_with_transform)
        
        entities_with_tag = Entity.get_entities_with_component(TagComponent)
        self.assertEqual(len(entities_with_tag), 2)
        self.assertIn(e2, entities_with_tag)
        self.assertIn(e3, entities_with_tag)
        
        entities_with_both = Entity.get_entities_with_components(TransformComponent, TagComponent)
        self.assertEqual(len(entities_with_both), 1)
        self.assertIn(e2, entities_with_both)

if __name__ == '__main__':
    unittest.main()
