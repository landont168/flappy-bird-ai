import pygame

# BUTTON CLASS TO CONSTRUCT BUTTON OBJECTS
class Button:
  # INITIALIZES OBJECT
  def __init__(self, x, y, image, scale): # param: x/y position, image, scale
    self.img = pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale))) # scales image
    self.rect = self.img.get_rect() # gets rect object
    self.rect.topleft = (x, y)
    self.clicked = False
  
  # DRAWS BUTTON
  def draw(self, win):
    action = False 
    pos = pygame.mouse.get_pos() # gets mouse position

    if self.rect.collidepoint(pos): # checks for mouse collision
      if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False: # checks for click
        self.clicked = True
        action = True # confirms click

    if pygame.mouse.get_pressed()[0] == 0:
      self.clicked = False # resets boolean
      
    win.blit(self.img, (self.rect.x, self.rect.y)) # blits button
    return action # returns boolean