from .texture import Texture  # Use relative import if in the same package
from typing import Dict, Optional
from .logger import logger  # Import the global logger instance

DEFAULT_TEXTURE_PATH = "textures/default_texture.png"  # Renamed for clarity

class TextureCache():
    
    def __init__(self):
        """Initializes the texture cache."""
        self.textures: Dict[str, Texture] = {}
        logger.log_message("Initializing TextureCache.", level="INFO")
        # Load default texture lazily or eagerly depending on needs
        # Eager loading:
        try:
            default_tex = self._load_texture(DEFAULT_TEXTURE_PATH)
            if default_tex is None or default_tex.texture_id is None:
                # _load_texture handles logging the specific load error
                logger.log_message(f"Critical: Default texture '{DEFAULT_TEXTURE_PATH}' failed to load properly during cache initialization.", level="ERROR")
                # Depending on the application, you might want to raise an exception here
                # raise RuntimeError("Failed to load essential default texture.")
            else:
                logger.log_message(f"Default texture '{DEFAULT_TEXTURE_PATH}' loaded successfully.", level="INFO")

        except Exception as e:
            # Catch any unexpected errors during the initial load
            logger.log_error(e, context=f"Unexpected error loading default texture '{DEFAULT_TEXTURE_PATH}' during cache init")
            # Handle this critical failure appropriately (e.g., exit, raise)
            
    def _load_texture(self, texture_path: str) -> Optional[Texture]:
        """Loads a texture and adds it to the cache. Internal use. Returns None on failure."""
        if texture_path not in self.textures:
            logger.log_message(f"Cache miss. Loading texture: {texture_path}", level="INFO")
            try:
                new_texture = Texture(texture_path)
                # Texture.__init__ now handles its own detailed loading errors
                if new_texture.texture_id is None: 
                    logger.log_message(f"Failed to load texture '{texture_path}' (Texture init failed).", level="WARNING")
                    # Attempt to return default if available, otherwise return None
                    default_tex = self.textures.get(DEFAULT_TEXTURE_PATH)
                    if default_tex:
                        logger.log_message(f"Using default texture as fallback for '{texture_path}'.", level="WARNING")
                        return default_tex
                    else:
                        logger.log_message(f"Cannot provide fallback for '{texture_path}'; default texture is unavailable.", level="ERROR")
                        return None  # Indicate failure
                else:
                    self.textures[texture_path] = new_texture
                    logger.log_message(f"Texture '{texture_path}' loaded and cached.", level="INFO")
                    return new_texture
            except Exception as e:  # Catch potential errors during Texture instantiation
                logger.log_error(e, context=f"Exception during Texture instantiation for '{texture_path}' in _load_texture")
                # Attempt to return default as fallback
                default_tex = self.textures.get(DEFAULT_TEXTURE_PATH)
                if default_tex:
                    logger.log_message(f"Using default texture as fallback for '{texture_path}' due to exception.", level="WARNING")
                    return default_tex
                else:
                    logger.log_message(f"Cannot provide fallback for '{texture_path}'; default texture unavailable after exception.", level="ERROR")
                    return None  # Indicate failure
        else:
            logger.log_message(f"Cache hit for texture: {texture_path}", level="DEBUG")
            return self.textures[texture_path]

    def get_texture(self, texture_path: Optional[str]) -> Optional[Texture]:
        """Gets a texture from the cache, loading it if necessary.

        Args:
            texture_path: The path to the texture file. If None, returns 
                          the default texture.

        Returns:
            The Texture object, or the default texture if path is None or loading fails.
            Returns None if the requested texture fails to load AND the default
            texture is also unavailable.
        """
        if texture_path is None:
            logger.log_message("Requested default texture.", level="DEBUG")
            default_tex = self.textures.get(DEFAULT_TEXTURE_PATH)
            if not default_tex:
                logger.log_message("Default texture requested but is not available in cache.", level="WARNING")
            return default_tex
        
        # Use _load_texture which handles caching, loading, error logging, and fallback logic
        return self._load_texture(texture_path)

    def cleanup(self):
        """Cleans up all loaded OpenGL texture resources."""
        logger.log_message("Cleaning up TextureCache...", level="INFO")
        count = len(self.textures)
        for path, texture in list(self.textures.items()):  # Iterate over a copy of items for safe removal
            try:
                texture.cleanup()  # Texture.cleanup now logs its own messages
            except Exception as e:
                logger.log_error(e, context=f"Exception during cleanup of texture '{path}'")
        self.textures.clear()  # Clear the dictionary
        logger.log_message(f"TextureCache cleanup complete. Removed {count} textures.", level="INFO")
