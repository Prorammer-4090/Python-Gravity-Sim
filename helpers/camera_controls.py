from math import pi
from core.entity import Entity

class CameraControls(Entity):
   """
   Controller for managing camera movement and rotation based on user input.
   
   Inherits from the Object3D to provides the ability to be loaded into the scene; move around the scene using transformations;
   and add child objects.

   Dependencies:
   - math: For PI constant and angle calculations
   - core.object3D: Base class for 3D object transformation
   
   Params:
       unitsPerSecond (float): Movement speed in world units per second. Defaults to 1.
       degreesPerSecond (float): Rotation speed in degrees per second. Defaults to 60.
   """
   def __init__(self, unitsPerSecond=2, degreesPerSecond=60):
       super().__init__()

       # Create pitch control object as child
       self.lookAttachment = Entity()  # Handles vertical rotation (pitch)
       self.children = [self.lookAttachment]  # Add to children list
       self.lookAttachment.parent = self      # Set parent reference

       # Movement and rotation speed settings
       self.unitsPerSecond = unitsPerSecond      # Translation speed
       self.degreesPerSecond = degreesPerSecond  # Rotation speed

       # Mouse control configuration
       self.mouseEnabled = True              # Toggle for mouse control
       self.mouseSensitivity = 0.1          # Mouse movement multiplier
       self.is_dragging = False             # Track mouse drag state
       self.last_mouse_pos = (0, 0)         # Last known mouse position

       # Define control key mappings
       self.KEY_MOVE_FORWARDS = "w"     # Move camera forward
       self.KEY_MOVE_BACKWARDS = "s"    # Move camera backward
       self.KEY_MOVE_LEFT = "a"         # Strafe camera left
       self.KEY_MOVE_RIGHT = "d"        # Strafe camera right
       self.KEY_MOVE_UP = "space"       # Move camera up
       self.KEY_MOVE_DOWN = "z"         # Move camera down
       self.KEY_TURN_LEFT = "q"         # Rotate camera left
       self.KEY_TURN_RIGHT = "e"        # Rotate camera right
       self.KEY_LOOK_UP = "t"           # Tilt camera up
       self.KEY_LOOK_DOWN = "g"         # Tilt camera down

   def update(self, input_handler, delta_time):
       """
        Update camera position/rotation based on input.
       
       Params:
           input_handler(object): Provides input Information
           delta_time (float): Time elapsed since last update in seconds
       """
       self.updateKeyboardControls(input_handler, delta_time)
       if self.mouseEnabled:
           self.updateMouseControls(input_handler)

   def updateKeyboardControls(self, inputObject, deltaTime):
       """
       Handles keyboard input for camera movement and rotation.
       
       Params:
           inputObject(object): Provides keyboard input information
           deltaTime (float): Time elapsed since last update in seconds
       """
       # Calculate frame-adjusted movement and rotation amounts
       moveAmount = self.unitsPerSecond * deltaTime
       rotateAmount = self.degreesPerSecond  * deltaTime

       # Process movement inputs
       if inputObject.key_held(self.KEY_MOVE_FORWARDS):
           self.translate(0, 0, -moveAmount)
       if inputObject.key_held(self.KEY_MOVE_BACKWARDS):
           self.translate(0, 0, moveAmount)
       if inputObject.key_held(self.KEY_MOVE_LEFT):
           self.translate(-moveAmount, 0, 0)
       if inputObject.key_held(self.KEY_MOVE_RIGHT):
           self.translate(moveAmount, 0, 0)
       if inputObject.key_held(self.KEY_MOVE_UP):
           self.translate(0, moveAmount, 0)
       if inputObject.key_held(self.KEY_MOVE_DOWN):
           self.translate(0, -moveAmount, 0)
           
       # Process rotation inputs
       if inputObject.key_held(self.KEY_TURN_RIGHT):
           self.rotateY(rotateAmount)
       if inputObject.key_held(self.KEY_TURN_LEFT):
           self.rotateY(-rotateAmount)
       if inputObject.key_held(self.KEY_LOOK_UP):
           self.lookAttachment.rotateX(-rotateAmount)
       if inputObject.key_held(self.KEY_LOOK_DOWN):
           self.lookAttachment.rotateX(rotateAmount)

   def updateMouseControls(self, input_handler):
       """
       Handles mouse input for camera rotation.
       
       Params:
           input_handler: Provides mouse input and movement information.
       """
       # Get mouse states from input handler
       mouse_states = input_handler.get_mouse_states()
       
       # Check if right mouse button is pressed
       if mouse_states["right"]:
           if not self.is_dragging:  # Start of new drag
               self.is_dragging = True
               self.last_mouse_pos = input_handler.mouse_pos
           else:  # Continue drag
               # Get mouse motion from input handler
               dx, dy = input_handler.mouse_motion
               
               if dx != 0:  # Only apply horizontal rotation if there's movement
                   # Apply horizontal rotation to camera body
                   self.rotateY(-dx * self.mouseSensitivity)
               
               if dy != 0:  # Only apply vertical rotation if there's movement
                   # Apply vertical rotation to pitch control
                   # Clamp vertical rotation to avoid flipping
                   self.lookAttachment.rotateX(-dy * self.mouseSensitivity)
       else:
           self.is_dragging = False  # End drag when button released

   def add(self, child):
       """
       Add a child object to the camera controller.
       
       Params:
           child: Object3D instance to be added as a child
       """
       self.lookAttachment.add(child)

   def remove(self, child):
       """
       Remove a child object from the camera controller.
       
       Params:
           child: Object3D instance to be removed
       """
       self.lookAttachment.remove(child)