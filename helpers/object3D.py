from helpers.transform import Transform
import numpy
from collections import deque

class Object3D:
    """
    A class representing a 3D object in space, managing transformations and hierarchical relationships.

    This class supports transformations (translation, rotation, scaling),
    scene hierarchy (parent-child relationships), and computing world-space transformations.
    """

    def __init__(self):
        """Initialize an Object3D with an identity transform, no parent, and no children."""
        self.transform = Transform.identity()  # Local transformation matrix
        self.parent = None                  # Reference to parent object
        self.children = []                  # List of child objects

    def add(self, child):
        """Add a child object to this object."""
        if not isinstance(child, Object3D):
            raise TypeError("Child must be an instance of Object3D.")
        if self.isDescendant(child):
            raise ValueError("Cannot add a child that is already a descendant.")
        self.children.append(child)
        child.parent = self

    def remove(self, child):
        """Remove a child object."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def isDescendant(self, potentialDescendant):
        """Check if an object is a descendant of this object."""
        for child in self.children:
            if child == potentialDescendant or child.isDescendant(potentialDescendant):
                return True
        return False

    def getWorldMatrix(self):
        """Get the world transformation matrix."""
        if self.parent is None:
            return self.transform
        return self.parent.getWorldMatrix() @ self.transform

    def getDescendantList(self):
        """Retrieve all descendant objects using breadth-first search (excluding self)."""
        descendants = []
        queue = deque(self.children)  # Start with immediate children
        while queue:
            node = queue.popleft()
            descendants.append(node)
            queue.extend(node.children)  # Add children of the current node to the queue
        return descendants

    def applyMatrix(self, matrix, localCoord=True):
        """Apply a transformation matrix to the object."""
        if localCoord:
            self.transform = self.transform @ matrix  # Local transformation (post-multiply)
        else:
            self.transform = matrix @ self.transform  # Global transformation (pre-multiply)

    def translate(self, x, y, z, localCoord=True):
        """Translate the object."""
        self.applyMatrix(Transform.translation(x, y, z), localCoord)

    def rotateX(self, angle, localCoord=True):
        """Rotate the object around the X-axis."""
        self.applyMatrix(Transform.rotation(angle, 0, 0), localCoord)

    def rotateY(self, angle, localCoord=True):
        """Rotate the object around the Y-axis."""
        self.applyMatrix(Transform.rotation(0, angle, 0), localCoord)

    def rotateZ(self, angle, localCoord=True):
        """Rotate the object around the Z-axis."""
        self.applyMatrix(Transform.rotation(0, 0, angle), localCoord)

    def scale(self, s, localCoord=True):
        """Scale the object."""
        self.applyMatrix(Transform.scale(s), localCoord)

    def getPosition(self):
        """Get the object's position in local space."""
        return [self.transform.item(0, 3),
                self.transform.item(1, 3),
                self.transform.item(2, 3)]

    def getWorldPosition(self):
        """Get the object's position in world space."""
        worldTransform = self.getWorldMatrix()
        return [worldTransform.item(3, 0),
                worldTransform.item(3, 1),
                worldTransform.item(3, 2)]

    def setPosition(self, position):
        """Set the object's position in local space."""
        if not (isinstance(position, (list, tuple)) and len(position) == 3):
            raise ValueError("Position must be a list or tuple of length 3.")
        self.transform[0, 3] = position[0]
        self.transform[1, 3] = position[1]
        self.transform[2, 3] = position[2]

    def lookAt(self, targetPosition):
        """Make the object look at a target position in world space."""
        currentWorldPos = numpy.array(self.getWorldPosition())
        targetPos = numpy.array(targetPosition)

        # Check if target is significantly different from current position
        if numpy.linalg.norm(targetPos - currentWorldPos) > 1e-6:
            # Calculate forward vector (direction from current position to target)
            forward = targetPos - currentWorldPos
            forward /= numpy.linalg.norm(forward)  # Already checked magnitude > 1e-6

            # Calculate right vector
            world_up = numpy.array([0.0, 1.0, 0.0])
            right = numpy.cross(world_up, forward)
            norm_right = numpy.linalg.norm(right)

            # Handle case where forward vector is parallel to world_up
            if norm_right < 1e-6:
                # If looking straight up or down, use a different 'up' vector for cross product
                # For example, use world_x if looking straight up/down
                if numpy.allclose(forward, world_up) or numpy.allclose(forward, -world_up):
                    world_right = numpy.array([1.0, 0.0, 0.0])
                    up = numpy.cross(forward, world_right)  # Calculate local up
                    right = numpy.cross(up, forward)  # Recalculate local right
                else:
                    # This case should ideally not happen if forward is normalized
                    # Fallback: maintain previous rotation or use identity
                    return  # Avoid changing rotation
            else:
                right /= norm_right
                # Calculate actual up vector
                up = numpy.cross(forward, right)
                # Normalization of 'up' is usually not needed if 'forward' and 'right' are orthonormal

            # Construct the rotation matrix: columns are the local axes in world space
            # Assuming object's local +Z is forward, +Y is up, +X is right
            rotationMatrix = numpy.identity(3)
            rotationMatrix[:, 0] = right
            rotationMatrix[:, 1] = up
            rotationMatrix[:, 2] = forward

            # Apply this rotation to the object's transform (top-left 3x3 part)
            self.transform[:3, :3] = rotationMatrix
        # else: If target is too close, do nothing to avoid division by zero.

    # returns 3x3 submatrix with rotation data
    def getRotationMatrix(self):
        return numpy.array([self.transform[0][0:3],
                            self.transform[1][0:3],
                            self.transform[2][0:3]])

    def getDirection(self):
        forward = numpy.array([0, 0, -1])
        return list(self.getRotationMatrix() @ forward)

    def setDirection(self, direction):
        position = self.getPosition()
        targetPosition = [position[0] + direction[0],
                          position[1] + direction[1],
                          position[2] + direction[2]]
        self.lookAt(targetPosition)