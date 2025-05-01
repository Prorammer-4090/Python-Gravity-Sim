import pygame
from OpenGL.GL import *
from typing import Optional, Tuple
from .logger import logger # Import the global logger instance

class Texture():
    
    def __init__(self, texture_path: Optional[str] = None):
        """Initializes the Texture object.

        Args:
            texture_path: Optional path to the texture file. If None, 
                          no texture is loaded initially.
        """
        self.texture_id: Optional[int] = None # Initialize later
        self.texture_path: Optional[str] = texture_path
        self.width: int = 0
        self.height: int = 0
        
        if texture_path is not None:
            try:
                self._load_texture(texture_path)
                logger.log_message(f"Successfully initialized texture: {texture_path}", level="DEBUG")
            except Exception as e: # Catch Pygame errors and potentially others
                logger.log_error(e, context=f"Failed during texture initialization for '{texture_path}'")
                self.texture_path = None # Mark as failed
        
    def _load_texture(self, texture_path: str):
        """Loads, configures, and uploads texture data to the GPU."""
        logger.log_message(f"Attempting to load texture image: {texture_path}", level="DEBUG")
        try:
            surf = pygame.image.load(texture_path).convert_alpha() # Ensure alpha channel
        except pygame.error as e:
            logger.log_error(e, context=f"Pygame failed to load image file: {texture_path}")
            # Re-raise to be caught by __init__ or caller
            raise 

        self.width = surf.get_width()
        self.height = surf.get_height()
        
        logger.log_message(f"Image loaded: {texture_path} ({self.width}x{self.height})", level="DEBUG")
        
        # Use RGBA format consistently
        data = pygame.image.tostring(surf, "RGBA", False) # Use False for standard OpenGL coordinate system

        # Generate texture ID only when load is successful
        self.texture_id = glGenTextures(1) 
        if not self.texture_id:
             # This is a more critical OpenGL error
             err = glGetError()
             msg = f"glGenTextures failed with error code {err} for texture {texture_path}"
             logger.log_message(msg, level="ERROR") # Log as error
             raise RuntimeError(msg) # Raise a runtime error

        self.bind()
        
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        
        # Upload data
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        err = glGetError()
        if err != GL_NO_ERROR:
            msg = f"glTexImage2D failed with error code {err} for texture {texture_path}"
            logger.log_message(msg, level="ERROR")
            self.cleanup() # Attempt cleanup before raising
            raise RuntimeError(msg)

        # Set texture parameters
        glGenerateMipmap(GL_TEXTURE_2D)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        
        self.unbind()
        logger.log_message(f"OpenGL texture created and configured for: {texture_path} (ID: {self.texture_id})", level="DEBUG")
        
    
    def get_texture_path(self) -> Optional[str]:
        return self.texture_path

    def get_dimensions(self) -> Tuple[int, int]:
        return self.width, self.height
        
    def bind(self, texture_unit: int = 0):
        """Binds the texture to a specific texture unit."""
        if self.texture_id is not None:
            glActiveTexture(GL_TEXTURE0 + texture_unit)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
        else:
            logger.log_message(f"Attempted to bind texture '{self.texture_path}' but it has no valid ID.", level="WARNING")
        
    def unbind(self, texture_unit: int = 0):
        """Unbinds the texture from a specific texture unit."""
        glActiveTexture(GL_TEXTURE0 + texture_unit)
        glBindTexture(GL_TEXTURE_2D, 0)
        
    def cleanup(self):
        """Deletes the OpenGL texture resource."""
        if self.texture_id is not None:
            logger.log_message(f"Cleaning up texture: {self.texture_path} (ID: {self.texture_id})", level="DEBUG")
            try:
                glDeleteTextures(1, [self.texture_id]) # Pass ID as a list/array
                err = glGetError()
                if err != GL_NO_ERROR:
                     logger.log_message(f"glDeleteTextures failed with error code {err} for texture ID {self.texture_id}", level="WARNING")
            except Exception as e: # Catch potential OpenGL context issues
                 logger.log_error(e, context=f"Exception during glDeleteTextures for ID {self.texture_id}")
            self.texture_id = None # Mark as cleaned up
        else:
            logger.log_message(f"Cleanup called for texture '{self.texture_path}' which has no ID (already cleaned or failed load).", level="DEBUG")