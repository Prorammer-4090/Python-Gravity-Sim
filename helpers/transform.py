import pyrr
import numpy as np
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
            4x4 translation matrix as numpy array
        """
        try:
            print(f"Translation{pyrr.matrix44.create_from_translation(
                pyrr.Vector3([x, y, z]), dtype=np.float32
            )}")
            return pyrr.matrix44.create_from_translation(
                pyrr.Vector3([x, y, z]), dtype=np.float32
            )
        except Exception as e:
            logger.log_error(e, f"Failed to create translation matrix with values ({x}, {y}, {z})")
            raise

    @staticmethod
    def rotation(x: float, y: float, z: float) -> np.ndarray:
        """
        Create a rotation matrix from Euler angles (in radians).
        
        Args:
            angx: Rotation around x-axis in radians
            angy: Rotation around y-axis in radians
            angz: Rotation around z-axis in radians
            
        Returns:
            4x4 rotation matrix as numpy array
        """
        
        angx = Transform.deg_to_rad(x)
        angy = Transform.deg_to_rad(y)
        angz = Transform.deg_to_rad(z)
        
        try:
            quat_x = pyrr.quaternion.create_from_x_rotation(angx)
            quat_y = pyrr.quaternion.create_from_y_rotation(angy)
            quat_z = pyrr.quaternion.create_from_z_rotation(angz)

            quat = pyrr.quaternion.cross(quat_y, quat_x)
            quat = pyrr.quaternion.cross(quat_z, quat)
            print(f"Rotation: {pyrr.matrix44.create_from_quaternion(quat, dtype=np.float32)}")
            return pyrr.matrix44.create_from_quaternion(quat, dtype=np.float32)
        except Exception as e:
            logger.log_error(e, f"Failed to create rotation matrix with angles ({angx}, {angy}, {angz}) radians")
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
            4x4 scaling matrix as numpy array
        """
        try:
            print(f"Scale: {pyrr.matrix44.create_from_scale([x, y, z], dtype=np.float32)}")
            return pyrr.matrix44.create_from_scale([x, y, z], dtype=np.float32)
        except Exception as e:
            logger.log_error(e, f"Failed to create scale matrix with factors ({x}, {y}, {z})")
            raise

    @staticmethod
    def inverse(matrix: np.ndarray) -> np.ndarray:
        """
        Calculate the inverse of a matrix.
        
        Args:
            matrix: Input 4x4 matrix
            
        Returns:
            Inverse of the input matrix
        """
        try:
            return pyrr.matrix44.inverse(matrix)
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
        try:
            return pyrr.matrix44.transpose(matrix)
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
    def multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        Multiply two matrices.
        
        Args:
            a: First matrix
            b: Second matrix
            
        Returns:
            Result of a * b
        """
        try:
            return pyrr.matrix44.multiply(a, b)
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
            View matrix
        """
        try:
            return pyrr.matrix44.create_look_at(
                eye=pyrr.Vector3(eye),
                target=pyrr.Vector3(target),
                up=pyrr.Vector3(up),
                dtype=np.float32
            )
        except Exception as e:
            context = f"Failed to create look_at matrix: eye={eye}, target={target}, up={up}"
            logger.log_error(e, context)
            raise
    
    @staticmethod
    def perspective(
        fov: float, 
        aspect: float, 
        near: float, 
        far: float
    ) -> np.ndarray:
        """
        Create a perspective projection matrix.
        
        Args:
            fov: Field of view in radians
            aspect: Aspect ratio (width/height)
            near: Near clipping plane distance
            far: Far clipping plane distance
            
        Returns:
            Perspective projection matrix
        """
        try:
            return pyrr.matrix44.create_perspective_projection(
                fovy=fov,
                aspect=aspect,
                near=near,
                far=far,
                dtype=np.float32
            )
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
            Orthographic projection matrix
        """
        try:
            return pyrr.matrix44.create_orthogonal_projection(
                left=left,
                right=right,
                bottom=bottom,
                top=top,
                near=near,
                far=far,
                dtype=np.float32
            )
        except Exception as e:
            context = f"Failed to create orthographic matrix: left={left}, right={right}, bottom={bottom}, top={top}, near={near}, far={far}"
            logger.log_error(e, context)
            raise