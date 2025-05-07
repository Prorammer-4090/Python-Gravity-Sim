from core.entity import Entity
from core.render_target import RenderTarget
from helpers.camera import Camera
from materials.material import Material
from OpenGL.GL import *

class Light(Entity):

    AMBIENT     = 1
    DIRECTIONAL = 2
    POINT       = 3

    def __init__(self, lightType=0):
        super().__init__()
        self.lightType   = lightType
        self.color       = [1, 1, 1]
        self.attenuation = [1, 0, 0]


class PointLight(Light):

    def __init__(self, color=[1, 1, 1], position=[0, 0, 0], attenuation=[1, 0, 0.1]):
        super().__init__(Light.POINT)
        self.color = color
        self.setPosition(position)
        self.attenuation = attenuation
        

class AmbientLight(Light):

    def __init__(self, color = [1, 1, 1]):
        super().__init__(Light.AMBIENT)
        self.color = color
        


class DirectionalLight(Light):

    def __init__(self, color=[1, 1, 1], direction=[0, -1, 0]):
        super().__init__(Light.DIRECTIONAL)
        self.color = color
        self.setDirection(direction)


class Shadow:
    def __init__(self, light_source, strength=0.5, resolution=[800/600], camera_bounds=[-5,5, -5,5, 0,20], bias=0.01):
        
        self.light_source = light_source
        
        self.camera = Camera()
        left, right, bottom, top, near, far = camera_bounds
        self.camera.setOrthographic(left=left, right=right, bottom=bottom, top=top, near=near, far=far)
        self.light_source.add(self.camera)
        
        self.render_target = RenderTarget(resolution=resolution, properties={"wrap" : GL_CLAMP_TO_BORDER})
        
        self.depth_material = Material("shaders/depth_V_shader.vert", "shaders/depth_F_shader.frag")
        
        self.strength = strength
        self.bias = bias
        
    def update(self):
        self.camera.updateViewMatrix()
        # actually use the depth_material for the depth pass
        self.depth_material.uniforms["view"].data       = self.camera.viewMatrix
        self.depth_material.uniforms["projection"].data = self.camera.projectionMatrix