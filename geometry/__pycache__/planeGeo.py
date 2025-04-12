from parametricGeo import ParametricGeometry

class PlaneGeometry(ParametricGeometry):

    def __init__(self, width=1, height=1, widthSegments=8, heightSegments=8):

        # Define the parametric function for a plane
        def S(u, v):
            
            return [u, v, 0]  # Z-coordinate is 0 for all points on the plane

        # Initialize the parent class with the parametric function and range
        super().__init__(
            -width / 2,  # uMin: Start of the width range (left edge)
            width / 2,   # uMax: End of the width range (right edge)
            widthSegments,  # Subdivisions along the width
            -height / 2,  # vMin: Start of the height range (bottom edge)
            height / 2,   # vMax: End of the height range (top edge)
            heightSegments,  # Subdivisions along the height
            S  # Parametric function
        )