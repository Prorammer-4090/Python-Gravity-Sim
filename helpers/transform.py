import pyrr
import numpy as np
import math  # Import math module
from typing import Union, Tuple, List, Optional
from core.logger import logger

class Transform:
    """
    Utility class for 3D transformations and matrix operations.
    Provides static methods to create and manipulate transformation matrices.
    """
    
    @staticmethod
    def translation(x: float, y: float, z: float) -> np.ndarray:
        """
        Create a translation matrix.
        
        Args:
            x: Translation along x-axis
            y: Translation along y-axis
            z: Translation along z-axis
            
        Returns:
            4x4 translation matrix as numpy array (Column-Major)
        """
        try:
            # Add .T to convert Pyrr's row-major to column-major
            return pyrr.matrix44.create_from_translation(
                pyrr.Vector3([x, y, z]), dtype=np.float32
            ).T 
        except Exception as e:
            logger.log_error(e, f"Failed to create translation matrix with values ({x}, {y}, {z})")
            raise

    @staticmethod
    def rotation(x: float, y: float, z: float) -> np.ndarray:
        """
        Create a rotation matrix from Euler angles (in degrees).
        
        Args:
            x: Rotation around x-axis in degrees
            y: Rotation around y-axis in degrees
            z: Rotation around z-axis in degrees
            
        Returns:
            4x4 rotation matrix as numpy array (Column-Major)
        """
        
        angx = Transform.deg_to_rad(x)
        angy = Transform.deg_to_rad(y)
        angz = Transform.deg_to_rad(z)
        
        try:
            # Add .T to convert Pyrr's row-major to column-major
            return pyrr.matrix44.create_from_eulers(np.array([angx, angz, angy]), dtype=np.float32).T
        except Exception as e:
            logger.log_error(e, f"Failed to create rotation matrix with angles ({x}, {y}, {z}) degrees")
            raise

    @staticmethod
    def scale(x: float = 1, y: float = 1, z: float = 1) -> np.ndarray:
        """
        Create a scaling matrix.
        
        Args:
            x: Scale factor along x-axis
            y: Scale factor along y-axis
            z: Scale factor along z-axis
            
        Returns:
            4x4 scaling matrix as numpy array (Column-Major)
        """
        try:
            # Add .T to convert Pyrr's row-major to column-major
            return pyrr.matrix44.create_from_scale([x, y, z], dtype=np.float32).T
        except Exception as e:
            logger.log_error(e, f"Failed to create scale matrix with factors ({x}, {y}, {z})")
            raise

    @staticmethod
    def inverse(matrix: np.ndarray) -> np.ndarray:
        """
        Calculate the inverse of a matrix.
        
        Args:
            matrix: Input 4x4 matrix (Column-Major)
            
        Returns:
            Inverse of the input matrix (Column-Major)
        """
        # Note: Inverse needs care. If input is column-major, inverse is column-major.
        # If the input 'matrix' is assumed column-major (coming from elsewhere in the app)
        # then pyrr expects row-major, so transpose before, and transpose back after.
        try:
            # Assuming input 'matrix' is column-major as used elsewhere in the app
            row_major_matrix = matrix.T
            inverse_row_major = pyrr.matrix44.inverse(row_major_matrix)
            return inverse_row_major.T # Convert back to column-major
        except Exception as e:
            logger.log_error(e, "Failed to calculate matrix inverse")
            raise

    @staticmethod
    def transpose(matrix: np.ndarray) -> np.ndarray:
        """
        Transpose a matrix.
        
        Args:
            matrix: Input 4x4 matrix
            
        Returns:
            Transposed matrix
        """
        # This function's purpose is transposition, so it just does that.
        try:
            return pyrr.matrix44.transpose(matrix) # Or just matrix.T
        except Exception as e:
            logger.log_error(e, "Failed to transpose matrix")
            raise

    @staticmethod
    def deg_to_rad(degrees: Union[float, List[float], np.ndarray]) -> Union[float, np.ndarray]:
        """
        Convert degrees to radians.
        
        Args:
            degrees: Angle(s) in degrees
            
        Returns:
            Angle(s) in radians
        """
        try:
            return np.radians(degrees)
        except Exception as e:
            logger.log_error(e, f"Failed to convert {degrees} degrees to radians")
            raise
    
    @staticmethod
    def multiply(m1: np.ndarray, m2: np.ndarray) -> np.ndarray:
        """
        Multiply two matrices.
        
        Args:
            m1: First matrix
            m2: Second matrix
            
        Returns:
            Result of m1 @ m2
        """
        # Assuming inputs m1, m2 are column-major
        # Standard column-major multiplication: M = M1 @ M2
        try:
            return m1 @ m2
        except Exception as e:
            logger.log_error(e, "Failed to multiply matrices")
            raise

    @staticmethod
    def compose(
        position: Tuple[float, float, float], 
        rotation: Tuple[float, float, float], 
        scale: Union[float, Tuple[float, float, float]]
    ) -> np.ndarray:
        """
        Compose a transformation matrix from position, rotation, and scale.
        
        Args:
            position: (x, y, z) translation
            rotation: (x, y, z) rotation in radians
            scale: Either a uniform scale factor or (x, y, z) scale factors
            
        Returns:
            Combined transformation matrix
        """
        try:
            t = Transform.translation(*position)
            r = Transform.rotation(*rotation)
            
            if isinstance(scale, (list, tuple)):
                s = Transform.scale(*scale)
            else:
                s = Transform.scale(scale, scale, scale)

            # Multiply in TRS order: Scale first, then Rotate, then Translate
            # For matrix multiplication: t * r * s
            return pyrr.matrix44.multiply(t, pyrr.matrix44.multiply(r, s))
        except Exception as e:
            context = f"Failed to compose transformation matrix: pos={position}, rot={rotation}, scale={scale}"
            logger.log_error(e, context)
            raise
    
    @staticmethod
    def look_at(
        eye: Tuple[float, float, float],
        target: Tuple[float, float, float],
        up: Tuple[float, float, float] = (0, 1, 0)
    ) -> np.ndarray:
        """
        Create a view matrix for a camera looking at a target.
        
        Args:
            eye: Camera position (x, y, z)
            target: Point to look at (x, y, z)
            up: Up vector, default is (0, 1, 0)
            
        Returns:
            View matrix (Column-Major)
        """
        try:
            # Add .T to convert Pyrr's row-major to column-major
            return pyrr.matrix44.create_look_at(
                eye=pyrr.Vector3(eye),
                target=pyrr.Vector3(target),
                up=pyrr.Vector3(up),
                dtype=np.float32
            ).T
        except Exception as e:
            context = f"Failed to create look_at matrix: eye={eye}, target={target}, up={up}"
            logger.log_error(e, context)
            raise
    
    @staticmethod
    def perspective(fov: float, aspect: float, near: float, far: float) -> np.ndarray:
        """
        Create a perspective projection matrix (Column-Major).
        Manually calculated based on standard OpenGL formula.
        
        Args:
            fov: Field of view in degrees (vertical)
            aspect: Aspect ratio (width/height)
            near: Near clipping plane distance
            far: Far clipping plane distance
            
        Returns:
            Perspective projection matrix (Column-Major)
        """
        try:
            # Convert FoV to radians
            fov_rad = Transform.deg_to_rad(fov) 
            # Calculate 'f' from tangent of half FoV
            f = 1.0 / math.tan(fov_rad / 2.0)
            
            # Initialize a 4x4 zero matrix
            matrix = np.zeros((4, 4), dtype=np.float32)
            
            # Populate matrix elements according to column-major perspective formula
            matrix[0, 0] = f / aspect
            matrix[1, 1] = f
            matrix[2, 2] = (far + near) / (near - far)
            matrix[2, 3] = (2 * far * near) / (near - far)
            matrix[3, 2] = -1.0
            # matrix[3, 3] remains 0, which is correct
            
            return matrix
        except Exception as e:
            context = f"Failed to create perspective matrix: fov={fov}, aspect={aspect}, near={near}, far={far}"
            logger.log_error(e, context)
            raise
    
    @staticmethod
    def orthographic(
        left: float, 
        right: float, 
        bottom: float, 
        top: float, 
        near: float, 
        far: float
    ) -> np.ndarray:
        """
        Create an orthographic projection matrix.
        
        Args:
            left: Left plane coordinate
            right: Right plane coordinate
            bottom: Bottom plane coordinate
            top: Top plane coordinate
            near: Near plane distance
            far: Far plane distance
            
        Returns:
            Orthographic projection matrix (Column-Major)
        """
        try:
            # Add .T to convert Pyrr's row-major to column-major
            return pyrr.matrix44.create_orthogonal_projection(
                left=left,
                right=right,
                bottom=bottom,
                top=top,
                near=near,
                far=far,
                dtype=np.float32
            ).T
        except Exception as e:
            context = f"Failed to create orthographic matrix: left={left}, right={right}, bottom={bottom}, top={top}, near={near}, far={far}"
            logger.log_error(e, context)
            raise

    @staticmethod
    def identity() -> np.ndarray:
        """
        Create an identity matrix.
        
        Returns:
            4x4 identity matrix as numpy array
        """
        try:
            return np.identity(4, dtype=np.float32)
        except Exception as e:
            logger.log_error(e, "Failed to create identity matrix")
            raise