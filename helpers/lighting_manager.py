from lights.light import Light, AmbientLight, DirectionalLight, PointLight
# if you add a SpotLight subclass later:
# from lights.spot_light import SpotLight
from typing import Any
from OpenGL.GL import *

class LightingManager():
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

        # --- Multi‐light & shadows support ---
        self.lights: list = []           # holds Light instances
        self.max_lights = 10                   # cap on lights
        self.shadows_enabled = False
        self.shadow_settings = {
            "resolution": (512, 512),
            "strength": 0.5,
            "bias": 0.005
        }

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

    # --- Light management ---
    def add_light(self, light: Light) -> bool:
        """Add a Light object if under max_lights."""
        if len(self.lights) < self.max_lights:
            self.lights.append(light)
            return True
        return False

    def remove_light(self, index: int) -> None:
        """Remove the light at the given index."""
        if 0 <= index < len(self.lights):
            self.lights.pop(index)

    def get_lights(self) -> list:
        """
        Return a list of current lights, padded with None to max_lights.
        Renderer can skip None entries.
        """
        result = self.lights.copy()
        while len(result) < self.max_lights:
            result.append(None)
        return result

    def enable_shadows(self, enable: bool = True) -> None:
        """Turn shadow mapping on or off."""
        self.shadows_enabled = enable

    def set_shadow_settings(self,
                            resolution: tuple[int,int] = None,
                            strength: float = None,
                            bias: float = None) -> None:
        """Configure shadow map resolution, strength, and depth bias."""
        if resolution:
            self.shadow_settings["resolution"] = tuple(resolution)
        if strength is not None:
            self.shadow_settings["strength"] = strength
        if bias is not None:
            self.shadow_settings["bias"] = bias

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

    # --- Type-specific light getters ---
    def get_ambient_lights(self) -> list[AmbientLight]:
        """Return all ambient lights."""
        return [l for l in self.lights if l.lightType == Light.AMBIENT]

    def get_directional_lights(self) -> list[DirectionalLight]:
        """Return all directional lights."""
        return [l for l in self.lights if l.lightType == Light.DIRECTIONAL]

    def get_point_lights(self) -> list[PointLight]:
        """Return all point lights."""
        return [l for l in self.lights if l.lightType == Light.POINT]

    def apply_to_shader(self, shader):
        """Upload all current lights & ambient data into the given shader."""
        # ambient
        shader.set_uniform("uAmbientStrength", self.ambient_strength)
        shader.set_uniform("uAmbientColor",     self.ambient_color)

        # directional lights
        dirs = self.get_directional_lights()
        shader.set_uniform("uNumDirectional", len(dirs))
        for i, L in enumerate(dirs):
            shader.set_uniform(f"uDirLights[{i}].direction", L.getDirection())
            shader.set_uniform(f"uDirLights[{i}].color",     L.color)

        # point lights
        pts = self.get_point_lights()
        shader.set_uniform("uNumPoint", len(pts))
        for i, L in enumerate(pts):
            shader.set_uniform(f"uPointLights[{i}].position",    L.getPosition())
            shader.set_uniform(f"uPointLights[{i}].color",       L.color)
            shader.set_uniform(f"uPointLights[{i}].attenuation", L.attenuation)

        # spot‐light stub (uncomment once SpotLight is available)
        # spots = self.get_spot_lights()
        # shader.set_uniform("uNumSpot", len(spots))
        # for i, L in enumerate(spots):
        #     shader.set_uniform(f"uSpotLights[{i}].position",    L.getPosition())
        #     shader.set_uniform(f"uSpotLights[{i}].direction",   L.getDirection())
        #     shader.set_uniform(f"uSpotLights[{i}].color",       L.color)
        #     shader.set_uniform(f"uSpotLights[{i}].attenuation", L.attenuation)
        #     shader.set_uniform(f"uSpotLights[{i}].cutOff",      L.cutOff)
