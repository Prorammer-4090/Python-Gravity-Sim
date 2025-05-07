from OpenGL.GL import *
import pygame
from .texture import Texture

class RenderTarget:

    def __init__(self, resolution=[800, 600], texture=None, properties={}):

        # values should equal texture dimensions
        self.width, self.height = resolution

        if texture is not None:
            self.texture = texture
        else:
            self.texture = Texture()
            self.texture.set_properties(properties)
            # now pass in the exact size to allocate
            self.texture.upload_data(self.width, self.height)

        # create a frame buffer
        self.framebufferRef = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebufferRef)
        # attach the color buffer from the texture
        glFramebufferTexture(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            self.texture.texture_id,
            0
        )
        # generate a buffer to store depth information
        self.depth_buffer_ref = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.depth_buffer_ref)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, self.width, self.height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.depth_buffer_ref)

        # set draw buffers explicitly (good practice if extend to multiple attachments)
        glDrawBuffers(1, [GL_COLOR_ATTACHMENT0])

        # check framebuffer status
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise Exception("Framebuffer status error")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def bind(self):
        """Bind this render target for drawing."""
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebufferRef)

    def unbind(self):
        """Unbind any FBO (back to default)."""
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def resize(self, resolution):
        """Reallocate texture and depth buffer to new size."""
        self.width, self.height = resolution
        self.texture.upload_data(self.width, self.height)

        self.bind()
        glBindRenderbuffer(GL_RENDERBUFFER, self.depth_buffer_ref)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, self.width, self.height)
        self.unbind()

    def cleanup(self):
        """Delete FBO, RBO and associated texture."""
        if hasattr(self, "depth_buffer_ref"):
            glDeleteRenderbuffers(1, [self.depth_buffer_ref])
        if hasattr(self, "framebufferRef"):
            glDeleteFramebuffers(1, [self.framebufferRef])
        # delegate texture cleanup
        self.texture.cleanup()