from geometry.geometry import Geometry
from math import sin, cos, pi

class PolygonGeometry(Geometry):

   def __init__(self, sides=3, radius=1):
       super().__init__()

       # Calculate angle increment between vertices
       A = 2 * pi / sides
       
       # Initialize data arrays
       positionData = []
       colorData = []
       uvData = []
       uvCenter = [0.5, 0.5]  # Center point for UV mapping

       normalData = []
       normalVector = [0, 0, 1]

       # Generate vertex data for each triangle in the polygon
       for n in range(sides):
           # Add triangle vertices: center point and two points on circumference
           positionData.append([0, 0, 0])  # Center point
           positionData.append([radius*cos(n*A), radius*sin(n*A), 0])  # First outer point
           positionData.append([radius*cos((n+1)*A), radius*sin((n+1)*A), 0])  # Second outer point

           # Add colors for each vertex
           colorData.append([1, 1, 1])  # White for center
           colorData.append([1, 0, 0])  # Red for first outer point
           colorData.append([0, 0, 1])  # Blue for second outer point

           # Add UV coordinates for texture mapping
           uvData.append(uvCenter)  # Center UV
           # Map outer points to UV space (transform from [-1,1] to [0,1] range)
           uvData.append([cos(n*A)*0.5 + 0.5, sin(n*A)*0.5 + 0.5])
           uvData.append([cos((n+1)*A)*0.5 + 0.5, sin((n+1)*A)*0.5 + 0.5])

           normalData.append(normalVector)
           normalData.append(normalVector)
           normalData.append(normalVector)

       # Add attribute data to geometry
       self.addAttribute("vec2", "vertexUV", uvData)
       self.addAttribute("vec3", "vertexPosition", positionData)
       self.addAttribute("vec3", "vertexColor", colorData)
       self.addAttribute("vec3", "vertexNormal", normalData)
       self.addAttribute("vec3", "faceNormal", normalData)
       self.countVertices()