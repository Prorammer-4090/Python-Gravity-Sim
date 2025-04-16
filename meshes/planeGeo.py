from meshes.parametricGeo import ParametricGeometry

class PlaneGeometry(ParametricGeometry):
    """
    A plane geometry in the XY plane.
    """

    def __init__(self, width=1, height=1, width_segments=8, height_segments=8):
        """
        Initialize a plane geometry.
        
        Args:
            width (float): Width of the plane
            height (float): Height of the plane
            width_segments (int): Number of width subdivisions
            height_segments (int): Number of height subdivisions
        """
        # Define the parametric function for a plane
        def surface_function(u, v):
            return [u, v, 0]  # Z-coordinate is 0 for all points on the plane

        # Initialize the parent class with the parametric function and range
        super().__init__(
            -width / 2,  # uMin: Start of the width range (left edge)
            width / 2,   # uMax: End of the width range (right edge)
            width_segments,  # Subdivisions along the width
            -height / 2,  # vMin: Start of the height range (bottom edge)
            height / 2,   # vMax: End of the height range (top edge)
            height_segments,  # Subdivisions along the height
            surface_function  # Parametric function
        )