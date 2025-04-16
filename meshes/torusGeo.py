from meshes.parametricGeo import ParametricGeometry
from math import sin, cos, pi

class TorusGeometry(ParametricGeometry):
    """
    A torus (donut) geometry.
    """

    def __init__(self, major_radius=1.0, minor_radius=0.3, radial_segments=32, tubular_segments=16):
        """
        Initialize a torus geometry.
        
        Args:
            major_radius (float): Radius from the center of the torus to the center of the tube
            minor_radius (float): Radius of the tube
            radial_segments (int): Number of segments along the major circle
            tubular_segments (int): Number of segments along the minor circle
        """
        # Define the parametric function for the torus geometry
        def torus_function(u, v):
            x = (major_radius + minor_radius * cos(v)) * cos(u)  # X-coordinate
            y = (major_radius + minor_radius * cos(v)) * sin(u)  # Y-coordinate
            z = minor_radius * sin(v)                            # Z-coordinate
            return [x, y, z]

        # Initialize the parent class with the parametric function and segmentation details
        super().__init__(
            0, 2 * pi,            # uMin, uMax (range for the major circle)
            radial_segments,      # Number of segments for the major circle
            0, 2 * pi,            # vMin, vMax (range for the minor circle)
            tubular_segments,     # Number of segments for the minor circle
            torus_function        # Parametric function to define the torus
        )