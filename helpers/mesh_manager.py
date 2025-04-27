from meshes.polyhedronGeo import PolyhedronGeometry
from meshes.torusGeo import TorusGeometry

class MeshManager:
    def __init__(self, initial_mesh_type="icosahedron", initial_subdivisions=0):
        self.mesh_types = ["tetrahedron", "octahedron", "cube", "icosahedron", "dodecahedron", "torus"]
        if initial_mesh_type not in self.mesh_types:
            raise ValueError(f"Invalid initial mesh type: {initial_mesh_type}")

        self.current_mesh_type = initial_mesh_type
        self.mesh_subdivisions = initial_subdivisions
        self.mesh = None
        self.num_vertices = 0
        self.load_mesh() # Load the initial mesh

    def load_mesh(self):
        """Load the currently selected mesh."""
        # Clean up old mesh buffers if they exist
        if self.mesh and hasattr(self.mesh, 'del_buffers'):
            self.mesh.del_buffers()
            self.mesh = None # Ensure old mesh is cleared

        try:
            if self.current_mesh_type == "torus":
                segments = 8 + 8 * self.mesh_subdivisions
                self.mesh = TorusGeometry(
                    major_radius=1.0, minor_radius=0.4,
                    radial_segments=segments, tubular_segments=segments
                )
            else:
                self.mesh = PolyhedronGeometry(
                    radius=1.0, polyhedron_type=self.current_mesh_type,
                    subdivisions=self.mesh_subdivisions
                )

            # Load mesh data to GPU
            if not self.mesh.gpu_load():
                print(f"Failed to load mesh to GPU: {self.current_mesh_type}")
                self.mesh = None
                self.num_vertices = 0
                return False
            else:
                # Update vertex count based on the loaded mesh
                if hasattr(self.mesh, 'num_vertices') and self.mesh.num_vertices is not None:
                    self.num_vertices = self.mesh.num_vertices
                elif "indices" in self.mesh.attributes:
                     # Assuming indices holds the count for drawing elements
                    self.num_vertices = len(self.mesh.attributes["indices"][1])
                else:
                    self.num_vertices = 0
                    print("Warning: Could not determine vertex count for drawing.")
                return True

        except Exception as e:
            print(f"Error creating mesh geometry {self.current_mesh_type}: {e}")
            self.mesh = None
            self.num_vertices = 0
            return False

    def next_mesh(self):
        """Cycles to the next mesh type and reloads."""
        current_index = self.mesh_types.index(self.current_mesh_type)
        next_index = (current_index + 1) % len(self.mesh_types)
        self.current_mesh_type = self.mesh_types[next_index]
        self.mesh_subdivisions = 0 # Reset subdivisions
        self.load_mesh()

    def increase_subdivision(self, max_subdivisions=5):
        """Increases the subdivision level and reloads the mesh."""
        if self.mesh_subdivisions < max_subdivisions:
            self.mesh_subdivisions += 1
            self.load_mesh()
        else:
            print(f"Maximum subdivisions ({max_subdivisions}) reached.")

    def get_mesh(self):
        """Returns the current mesh object."""
        return self.mesh

    def get_mesh_info(self):
        """Returns current mesh type, subdivisions, and vertex count."""
        return self.current_mesh_type, self.mesh_subdivisions, self.num_vertices

    def cleanup(self):
        """Releases GPU resources safely."""
        try:
            if self.mesh and hasattr(self.mesh, 'del_buffers'):
                print("Cleaning up mesh GPU resources...")
                self.mesh.del_buffers()
                self.mesh = None
        except Exception as e:
            print(f"Warning: Error during mesh manager cleanup: {e}")