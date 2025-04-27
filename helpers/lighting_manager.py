class LightingManager:
    def __init__(self, initial_ambient_strength=0.5, initial_mesh_color_index=0):
        self.ambient_strength = initial_ambient_strength
        self.ambient_color = [1.0, 1.0, 1.0] # Default ambient color
        self.use_custom_color = True

        self.color_presets = [
            [0.0, 0.7, 1.0], [0.0, 0.8, 0.4], [1.0, 0.4, 0.0],
            [0.8, 0.2, 0.8], [1.0, 0.8, 0.0],
        ]
        self.color_index = initial_mesh_color_index % len(self.color_presets)
        self.mesh_color = self.color_presets[self.color_index]

    def increase_ambient(self, step=0.1, max_strength=2.0):
        """Increases ambient light strength."""
        self.ambient_strength = min(max_strength, self.ambient_strength + step)

    def decrease_ambient(self, step=0.1, min_strength=0.0):
        """Decreases ambient light strength."""
        self.ambient_strength = max(min_strength, self.ambient_strength - step)

    def toggle_color_mode(self):
        """Toggles between using custom mesh color and vertex colors."""
        self.use_custom_color = not self.use_custom_color

    def cycle_color(self):
        """Cycles through the preset mesh colors."""
        self.color_index = (self.color_index + 1) % len(self.color_presets)
        self.mesh_color = self.color_presets[self.color_index]

    # --- Getters for Renderer ---
    def get_ambient_strength(self):
        return self.ambient_strength

    def get_ambient_color(self):
        return self.ambient_color

    def get_mesh_color(self):
        return self.mesh_color

    def get_use_custom_color(self):
        return self.use_custom_color

    # --- Getter for UI ---
    def get_color_mode_string(self):
        return "Using Custom Color" if self.use_custom_color else "Using Vertex Colors"