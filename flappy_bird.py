"""
Final Project: Flappy Bird AI
Author: Landon T.
"""

# IMPORT MODULES
import pygame
import random
import os
import neat
import button
pygame.font.init()

# GAME SETUP
WIN_WIDTH = 500
WIN_HEIGHT = 800
GAME_FONT = pygame.font.Font("04B_19.ttf", 30)
DRAW_LINES = False

# WINDOW SETUP
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT)) 
pygame.display.set_caption("Flappy Bird AI") 
pygame.display.set_icon(pygame.image.load(os.path.join("imgs", "bird3.png")))

# LOAD IMAGES 
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird" + str(x) + ".png"))) for x in range(1, 4)]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
DAY_BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "day_bg.png")))
NIGHT_BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "night_bg.png")))
MESSAGE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "message.png")))
GAMEOVER_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "gameover.png")))
START_IMG = pygame.image.load(os.path.join("imgs", "start_btn.png"))
EXIT_IMG = pygame.image.load(os.path.join("imgs", "exit_btn.png"))
PAUSE_IMG = pygame.image.load(os.path.join("imgs", "pause_btn.png"))
RESUME_IMG = pygame.image.load(os.path.join("imgs", "resume_btn.png"))

# GAME VARIABLES
gen = 0
active_game = True
end_game = False
paused_game = False


# BIRD CLASS TO REPRESENT FLAPPY BIRD
class Bird:
  IMGS = BIRD_IMGS
  MAX_ROTATION = 25 # max tilt of bird
  ROT_VEL = 20 # rotation of bird
  ANIMATION_TIME = 5 # length of bird animation

  # INITIALIZES BIRD OBJECT
  def __init__(self, x, y): # starting x/y position
    self.x = x
    self.y = y
    self.tilt = 0 # degrees to tilt image
    self.tick_count = 0 # for physics of bird (time)
    self.vel = 0 # velocity of bird
    self.height = self.y # for moving bird
    self.img_count = 0 # tracks shown image 
    self.img = self.IMGS[0] # starting bird image
  
  # MAKES THE BIRD JUMP
  def jump(self):
    self.vel = -10.5 # velocity of bird 
    self.tick_count = 0 # tracks when bird last jumped
    self.height = self.y # tracks where bird jumped from
  
  # MAKES THE BIRD MOVE
  def move(self):
    self.tick_count += 1 # tracks number of frames since last jump

    # calculates displacement for downward acceleration
    displacment = self.vel * self.tick_count + 1.5 * self.tick_count**2

    # terminal velcoity
    if displacment >= 16:
      displacment = 16
    if displacment < 0:
      displacment -= 2
    
    self.y += displacment # change y position based on displacement

    if displacment < 0 or self.y < self.height + 50: # tilt up 
      if self.tilt < self.MAX_ROTATION:
        self.tilt = self.MAX_ROTATION
    else: # tilt down
      if self.tilt > -90:
        self.tilt -= self.ROT_VEL
  
  # DRAWS BIRD TO WINDOW
  def draw(self, win):
    self.img_count += 1 # tracks number of frames shown for image
    
    # creates bird animation by looping through three images
    if self.img_count < self.ANIMATION_TIME:
      self.img = self.IMGS[0]
    elif self.img_count < self.ANIMATION_TIME*2:
      self.img = self.IMGS[1]
    elif self.img_count < self.ANIMATION_TIME*3:
      self.img = self.IMGS[2]
    elif self.img_count < self.ANIMATION_TIME*4:
      self.img = self.IMGS[1]
    elif self.img_count == self.ANIMATION_TIME*4 + 1:
      self.img = self.IMGS[0]
      self.img_count = 0
    
    # no flap if bird moving downwards
    if self.tilt <= -80:
      self.img = self.IMGS[1]
      self.img_count = self.ANIMATION_TIME*2
    
    # tilts bird and blit to window
    rotated_img = pygame.transform.rotate(self.img, self.tilt)
    rotated_rect = rotated_img.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
    win.blit(rotated_img, rotated_rect.topleft)
  
  # GETS MASK OF CURRENT BIRD IMAGE
  def get_mask(self):
    return pygame.mask.from_surface(self.img)


# PIPE CLASS TO REPRESENT PIPES
class Pipe:
  GAP = 200 # gap between pipes
  VEL = 5 # speed of moving pipes

  # INITIALIZES PIPE OBJECT
  def __init__(self, x):
    self.x = x
    self.height = 0

    # location of top and bottom of pipe
    self.top = 0
    self.bottom = 0

    # sets top and bottom pipe images
    self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
    self.PIPE_BOTTOM = PIPE_IMG

    self.passed = False # returns for passed pipes

    self.set_height() 
  
  # SETS HEIGHT OF PIPE FROM TOP OF SCREEN
  def set_height(self):
    self.height = random.randrange(50, 450) # gets random height
    self.top = self.height - self.PIPE_TOP.get_height() # sets top pipe height
    self.bottom = self.height + self.GAP # sets bottom pipe height
  
  # MOVES PIPE BASED ON VELOCITY
  def move(self):
    self.x -= self.VEL
  
  # DRAWS TOP AND BOTTOM PIPE TO WINDOW
  def draw(self, win):
    win.blit(self.PIPE_TOP, (self.x, self.top)) 
    win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
  
  # RETURNS TRUE IF BIRD POINT COLLIDES WITH PIPE
  def collide(self, bird):

    # creates mask for bird and top/bottom pipe
    bird_mask = bird.get_mask()
    top_mask = pygame.mask.from_surface(self.PIPE_TOP)
    bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

    # calculates offset - distance between bird mask and pipe masks
    top_offset = (self.x - bird.x, self.top - round(bird.y))
    bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

    # check if masks collide by finding point of collision
    t_point = bird_mask.overlap(top_mask, top_offset)
    b_point = bird_mask.overlap(bottom_mask, bottom_offset)

    if t_point or b_point:
      return True # collision
    return False # no collision


# BASE CLASS TO REPRESENT FLOOR
class Base:
  VEL = 5 # velocity of floor
  WIDTH = BASE_IMG.get_width()
  IMG = BASE_IMG

  # INITIALIZES BASE OBJECT
  def __init__(self, y): # y position
    self.y = y
    self.x1 = 0
    self.x2 = self.WIDTH
  
  # MOVES ADJACENT FLOORS TO CREATE MOVING EFFECT
  def move(self):
    self.x1 -= self.VEL
    self.x2 -= self.VEL

    # resets floor x position if it fully exits screen (to create moving floor effect)
    if self.x1 + self.WIDTH < 0:
      self.x1 = self.x2 + self.WIDTH
    if self.x2 + self.WIDTH < 0:
      self.x2 = self.x1 + self.WIDTH
  
  # DRAWS TWO ADJACENT FLOORS
  def draw(self, win):
    win.blit(self.IMG, (self.x1, self.y))
    win.blit(self.IMG, (self.x2, self.y))


# DRAWS THE WINDOW FOR MAIN GAME LOOP
def draw_window(win, birds, pipes, base, score, gen, pipe_ind, pause_button, resume_button):
  win.blit(DAY_BG_IMG, (0,0)) # draws background
  for bird in birds:
    if DRAW_LINES: # draws lines from bird to top/bottom pipe
      try:
        pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 4)
        pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 4)
      except:
        pass
    bird.draw(win) # draws bird

  for pipe in pipes: # draws pipes
    pipe.draw(win)
  
  base.draw(win) # draws base

  # score
  score_label = GAME_FONT.render("Score: " + str(score), 1,(255,255,255))
  win.blit(score_label, (WIN_WIDTH - 10 - score_label.get_width(), 10))

  # current generation
  gen_label = GAME_FONT.render("Gen: " + str(gen), 1,(255,255,255))
  win.blit(gen_label, (10, 10))

  # number of birds alive
  alive_label = GAME_FONT.render("Alive: " + str(len(birds)), 1,(255,255,255))
  win.blit(alive_label, (10, 50))

  pause(win, pause_button, resume_button) # pause function

  pygame.display.update()


# PAUSE FUNCTION
def pause(win, pause_button, resume_button):
  global paused_game
  clock = pygame.time.Clock()
  
  # if paused game, creates new game loop
  while paused_game:
    clock.tick(5)
    # checks for pygame quit event
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        quit()

    # draws resume button - if clicked, unpauses game
    if resume_button.draw(win):
      paused_game = False
    
    pygame.display.update()
  
  if not paused_game:
    # draws pause button - if clicked, pauses game
    if pause_button.draw(win):
      paused_game = True
  

# DISPLAYS MAIN MENU SCREEN
def menu_screen(win, base, start_button, exit_button):
  global active_game
  
  win.blit(NIGHT_BG_IMG, (0, 0))
  win.blit(MESSAGE_IMG, (70, 80)) 
  base.draw(win)

  # draws start button - if clicked, starts game
  if start_button.draw(win):
    active_game = True
  
  # draws exit button - if clicked, exits pygame
  if exit_button.draw(win):
    pygame.quit()
    quit()

  pygame.display.update()

# DISPLAYS END SCREEN
def end_screen(win, base):
  clock = pygame.time.Clock()

  start_ticks = pygame.time.get_ticks() # starts ticker
  ending = True
  end_text = GAME_FONT.render("Thanks for playing!", 1,(255,255,255))

  # creates game loop
  while ending:
    clock.tick(30)
    # checks for pygame quit event
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        quit()

    # draws game over display   
    win.blit(NIGHT_BG_IMG, (0, 0))
    win.blit(GAMEOVER_IMG, (60, 300))
    win.blit(end_text, (100, 425))

    base.draw(win)
    base.move()

    pygame.display.update()

    seconds = (pygame.time.get_ticks() - start_ticks) / 1000 # calculates seconds
    if seconds >= 10: # quits pygame after 10 seconds
      pygame.quit()
      quit()


# RUNS SIMULATION OF BIRD GENERATIONS AND MODIFIES FITNESS BASED ON PERFORMANCE IN FLAPPY BIRD GAME
def eval_genomes(genomes, config):
  global WIN, DRAW_LINES, gen, active_game, end_game
  win = WIN
  gen += 1 # increments generation

  nets = [] # list of neural networks of birds
  ge = [] # list of genomes
  birds = [] # list of birds
  
  # sets up neural network and bird object for genome
  for _, genome in genomes:
    genome.fitness = 0 # set initial fitness of genomes
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    nets.append(net)
    ge.append(genome)
    birds.append(Bird(230, 350))

  # start and exit button
  start_button = button.Button(175, 400, START_IMG, 0.6)
  exit_button = button.Button(185, 550, EXIT_IMG, 0.6)

  # pause and resume button
  pause_button = button.Button(10, 100, PAUSE_IMG, 3)
  resume_button = button.Button(10, 100, RESUME_IMG, 3)

  # initalizes pipes, base, and score variables
  pipes = [Pipe(600)]
  base = Base(700)
  score = 0
  
  clock = pygame.time.Clock()

  # main game loop
  run = True
  while run and len(birds) > 0:
    clock.tick(30)
    for event in pygame.event.get():
      # checks for pygame quit event
      if event.type == pygame.QUIT:
        pygame.quit()
        quit()
      # checks for pygame key events
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_q and not DRAW_LINES: # enables tracking lines
          DRAW_LINES = True
        elif event.key == pygame.K_q and DRAW_LINES: # disables tracking lines
          DRAW_LINES = False
        
    # runs game   
    if active_game:
      # determines whether to use first or second pipe on screen for neural network input
      pipe_ind = 0 
      if len(birds) > 0:
        if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
          pipe_ind = 1 # use second pipe
      
      # moves bird - rewards birds with a bit of fitness for each frame it survives
      for x, bird in enumerate(birds):
        bird.move()
        ge[x].fitness += 0.1

        # activate neural network with input to get output
        # input: y position of bord, distance bird and top/bottom pipe
        output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

        # use tanh activation function to get output between -1 and 1
        if output[0] > 0.5: # jump if > 0.5
          bird.jump()

      add_pipe = False
      rem = []
      for pipe in pipes:
        pipe.move() 
        # checks for collisions -> removes bird and corresponding genome/neural network
        for x, bird in enumerate(birds):
          if pipe.collide(bird): # checks for collisions
            ge[x].fitness -= 1 # reduces genome fitness
            nets.pop(x)
            ge.pop(x) 
            birds.pop(x)
          
        # if bird passed pipes -> generate new pipes
        if not pipe.passed and pipe.x < bird.x:
          pipe.passed = True
          add_pipe = True
        
        # appends off screen pipes to list
        if pipe.x + pipe.PIPE_TOP.get_width() < 0:
          rem.append(pipe)
        
      # checks if bird passed pipes 
      if add_pipe:
        score += 1 # increase score
        for g in ge: 
          g.fitness += 5 # increases fitness for passing pipes
        pipes.append(Pipe(600)) # creates new pipes
        
      # remove old pipes
      for r in rem:
        pipes.remove(r)
      
      # checks if birds hits floor or ceiling
      for x, bird in enumerate(birds):
        if bird.y + bird.img.get_height() >= 700 or bird.y < 0:
          birds.pop(x) # removes bird
          nets.pop(x) # removes corresponding neural network
          ge.pop(x) # removes corresponding genome
    
      draw_window(win, birds, pipes, base, score, gen, pipe_ind, pause_button, resume_button)# draws window
      base.move() # moves base

      # goes to end screen display
      if score >= 50:
        active_game = False
        end_game = True

    # checks if inactive game
    else:
      if end_game:
        end_screen(win, base) # displays end screen
      else:
        menu_screen(win, base, start_button, exit_button) # displays menu screen
      base.move()


# RUNS NEAT ALGORITHM TO TRAIN NEURAL NETWORKS
def run(config_path):
  # loads in configuration file
  config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path) 

  p = neat.Population(config) # creates genome population
  p.run(eval_genomes, 50) # runs algorithm for up to 50 generations

if __name__ == "__main__":
  # gets path to configuration file
  local_dir = os.path.dirname(__file__)
  config_path = os.path.join(local_dir, "config-feedforward.txt")
  run(config_path)