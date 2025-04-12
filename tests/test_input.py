import pygame
import os
import time
import math  # Add import for math functions
from core.input import Input

def test_input():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Input Test")
    pygame.display.set_icon(pygame.image.load("Images/tool-box.png"))
    
    input_handler = Input()
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # Clear terminal
        os.system('clear')
        
        print("Input Test Started - Move mouse, press keys, click, etc.")
        print("Press ESC to exit")
        
        # Update and display input state
        input_handler.update()
        print(input_handler)
        
        # Display specific input tests
        print("\nTest Results:")
        print(f"Mouse Position: {input_handler.get_mouse_pos()}")
        print(f"Mouse Direction: {input_handler.get_mouse_dir()}")
        print(f"Left Mouse Button: {input_handler.mouse_buttons['left']}")
        print(f"Is Dragging: {input_handler.is_dragging}")
        print(f"Drag Distance: {input_handler.get_drag_distance()}")
        print(f"Double Click: {input_handler.is_double_click()}")
        
        if input_handler.key_down('escape'):
            running = False
        if input_handler.quit:
                running = False
            
        # Render some visual feedback
        screen.fill((30, 30, 30))
        
        # Draw mouse position
        pygame.draw.circle(screen, (255, 0, 0), input_handler.get_mouse_pos(), 5)
        
        # Draw drag line if dragging
        if input_handler.is_dragging and input_handler.drag_start_pos:
            # Draw the line from start position to current mouse position
            pygame.draw.line(
                screen, 
                (0, 255, 0), 
                input_handler.drag_start_pos, 
                input_handler.get_mouse_pos(), 
                2
            )
            
            # Draw arrow head at drag start position
            start_pos = input_handler.drag_start_pos
            mouse_pos = input_handler.get_mouse_pos()
            
            # Calculate angle between start position and mouse position
            dx = mouse_pos[0] - start_pos[0]
            dy = mouse_pos[1] - start_pos[1]
            angle = math.atan2(dy, dx)
            
            # Arrow head size
            arrow_size = 15
            
            # Calculate arrow head points (triangle vertices)
            # The tip points away from the mouse
            tip_x = start_pos[0] - math.cos(angle) * arrow_size
            tip_y = start_pos[1] - math.sin(angle) * arrow_size
            
            # The other two points of the triangle
            left_x = start_pos[0] - math.cos(angle - math.pi/4) * arrow_size * 0.6
            left_y = start_pos[1] - math.sin(angle - math.pi/4) * arrow_size * 0.6
            
            right_x = start_pos[0] - math.cos(angle + math.pi/4) * arrow_size * 0.6
            right_y = start_pos[1] - math.sin(angle + math.pi/4) * arrow_size * 0.6
            
            # Draw the arrow head (triangle)
            pygame.draw.polygon(screen, (0, 255, 0), [
                (tip_x, tip_y), 
                (left_x, left_y), 
                (right_x, right_y)
            ])
        
        pygame.display.flip()
        clock.tick(30)
        
    pygame.quit()

if __name__ == "__main__":
    test_input()
    os.system("clear")