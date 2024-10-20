import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
pygame.init()

# Set the caption of the window
pygame.display.set_caption("Platformer")

# Constants for window dimensions and frames per second
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 4  # Player movement speed

# Create a display window
window = pygame.display.set_mode((WIDTH, HEIGHT))

# Function to flip sprites horizontally
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

# Function to load sprite sheets from the assets folder
def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)  # Create the path to the folder
    images = [f for f in listdir(path) if isfile(join(path, f))]  # List all images in the folder

    all_sprites = {}

    # Iterate through each image in the sprite sheet
    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()  # Load the sprite sheet

        sprites = []
        # Extract individual sprites from the sprite sheet
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)  # Copy each sprite into the surface
            sprites.append(pygame.transform.scale2x(surface))  # Scale up the sprite

        # Store flipped versions if necessary
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

# Function to get a block image for terrain
def get_block(size, sprite_x=96, sprite_y=0):  # Add sprite_x and sprite_y
    path = join("assets", "Terrain", "Terrain.png")  # Load the terrain sprite sheet
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(sprite_x, sprite_y, size, size)  # Use sprite_x and sprite_y for block coordinates
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)  # Scale up the block

# Player class with attributes and behavior
class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)  # Red color for player (for debugging or placeholder)
    GRAVITY = 5  # Gravity constant
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)  # Load player sprites
    ANIMATION_DELAY = 3  # Delay between animation frames

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)  # Player's rectangle for positioning
        self.x_vel = 0  # Horizontal velocity
        self.y_vel = 0  # Vertical velocity
        self.mask = None  # Mask for collision detection
        self.direction = "right"  # Default direction
        self.animation_count = 0  # Animation frame counter
        self.fall_count = 0  # Counter for falling
        self.jump_count = 0  # Counter for jumps
        self.hit = False  # Whether the player is hit
        self.hit_count = 0  # Counter for hit duration
        self.health = 1

    def take_damage(self):
        if self.hit_count == 0:  # Only decrease health once per hit
            self.health -= 1
            self.hit = True

    # Function to handle jumping logic
    def jump(self):
        self.y_vel = -self.GRAVITY * 4  # Set upward velocity for jump
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    # Move the player by a certain amount
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    # Set hit state to True
    def make_hit(self):
        self.hit = True

    # Move player left
    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0  # Reset animation if direction changes

    # Move player right
    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    # Game loop logic for the player
    def loop(self, fps):
        # Gravity effect
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        # Handle hit logic
        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:  # Reset hit after a delay
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    # Handle when the player lands on a surface
    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    # Handle head collision when hitting a ceiling
    def hit_head(self):
        self.count = 0
        self.y_vel *= -1  # Invert the velocity when hitting a ceiling

    # Update the current sprite based on the player's state
    def update_sprite(self):
        sprite_sheet = "idle"  # Default state is idle
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:  # Jumping
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 8:  # Falling
            sprite_sheet = "fall"
        elif self.x_vel != 0:  # Running
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction  # Determine direction-specific sprite
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)  # Cycle through animation frames
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    # Update player's rectangle and mask based on current sprite
    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    # Draw the player on the screen
    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

# Base class for objects in the game world
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name  # Name for identifying object type

    # Draw the object on the screen
    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))
            

# Block class for terrain objects
# Block class for terrain objects
class Block(Object):
    def __init__(self, x, y, size, sprite_x=96, sprite_y=0):  # Add sprite_x and sprite_y parameters
        super().__init__(x, y, size, size)
        block = get_block(size, sprite_x, sprite_y)  # Pass custom coordinates to get_block
        self.image.blit(block, (0, 0))  # Draw the block on the object's image
        self.mask = pygame.mask.from_surface(self.image)  # Create a mask for collision

# SpikeHead trap class
class SpikeHead(Object):
    ANIMATION_DELAY = 12  # Delay between animation frames

    def __init__(self, x, y, width, height, speed=3, min_y=100, max_y=800):
        super().__init__(x, y, width, height, "spike_head")  # Set spikehead name
        self.spike_head = load_sprite_sheets("Traps", "Spike Head", width, height)  # Load SpikeHead sprites
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "Blink (54x52)"  # Default state is off
        self.speed = speed  # Vertical movement speed
        self.direction = 1  # Direction of movement (1 for down, -1 for up)
        self.min_y = min_y  # Minimum Y position (top limit)
        self.max_y = max_y  # Maximum Y position (bottom limit)

    # Turn the spikehead trap off
    def Blink(self):
        self.animation_name = "Blink (54x52)"

        # Move the spike head up and down
    def move(self):
        self.rect.y += self.speed * self.direction  # Move vertically

        # Reverse direction if it hits the movement limits
        if self.rect.y <= self.min_y:
            self.direction = 1  # Start moving down
        elif self.rect.y >= self.max_y:
            self.direction = -1  # Start moving up

    # Handle the spikehead trap animation loop and movement
    def loop(self):
        self.move()  # Move the spike head up and down

        sprites = self.spike_head[self.animation_name]  # Get current animation based on state
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        # Reset animation counter if it exceeds the sprite list length
        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

        # Update the rect and mask after movement
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

class MovingPlatform(Object):
    def __init__(self, x, y, width, height, speed, min_y, max_y):
        super().__init__(x, y, width, height, "moving_platform")
        self.image.fill((0, 0, 0))  # Make the platform black
        self.speed = speed  # Speed of vertical movement
        self.direction = 1  # Direction of movement (1 for down, -1 for up)
        self.min_y = min_y  # Minimum Y position (top)
        self.max_y = max_y  # Maximum Y position (bottom)

    def move(self):
        # Move the platform vertically
        self.rect.y += self.speed * self.direction

        # Reverse direction if it reaches the limits
        if self.rect.y <= self.min_y:
            self.direction = 1  # Start moving down
        elif self.rect.y >= self.max_y:
            self.direction = -1  # Start moving up

    def loop(self):
        self.move()  # Move the platform every frame

# Function to load the background image and create tiles
def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))  # Load background image
    _, _, width, height = image.get_rect()  # Get dimensions of the image
    tiles = []

    # Fill the screen with the background tiles
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

# Function to draw everything on the screen
def draw(window, background, bg_image, player, objects, offset_x):
    # Draw the background
    for tile in background:
        window.blit(bg_image, tile)

    # Draw all objects in the game world
    for obj in objects:
        obj.draw(window, offset_x)

    # Draw the player
    player.draw(window, offset_x)

    # Display player health
    font = pygame.font.SysFont('comicsans', 30)
    health_text = font.render(f'Health: {player.health}', True, (255, 255, 255))
    window.blit(health_text, (10, 10))  # Display in the top-left corner

    pygame.display.update()  # Update the display

# Handle vertical collisions with the player and objects
def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):  # Check for mask-based collisions
            if dy > 0:  # Player is falling
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:  # Player is jumping and hits a ceiling
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects

# Handle horizontal collisions with the player and objects
def collide(player, objects, dx):
    player.move(dx, 0)  # Move player horizontally
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):  # Check for mask-based collisions
            collided_object = obj
            break

    player.move(-dx, 0)  # Move player back to original position
    player.update()
    return collided_object

# Handle player movement and check for collisions
def handle_move(player, objects):
    keys = pygame.key.get_pressed()  # Get the currently pressed keys

    player.x_vel = 0  # Reset horizontal velocity
    collide_left = collide(player, objects, -PLAYER_VEL * 2)  # Check for collision on the left
    collide_right = collide(player, objects, PLAYER_VEL * 2)  # Check for collision on the right

    # Move left if left arrow is pressed and no collision
    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    # Move right if right arrow is pressed and no collision
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    # Handle vertical collisions
    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "spike_head":
            player.take_damage()  # Decrease health if player touches spikehead

# Main game loop
def game_over(window):
    font = pygame.font.SysFont('comicsans', 60)
    game_over_text = font.render("Game Over", True, (255, 0, 0))
    restart_text = font.render("Press R to Restart or Q to Quit", True, (255, 255, 255))

    window.fill((0, 0, 0))  # Fill the screen with black
    window.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
    window.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))
    pygame.display.update()

    # Wait for the player to press R or Q
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Restart the game
                    main(window)
                if event.key == pygame.K_q:  # Quit the game
                    run = False
                    pygame.quit()
                    quit()

def main(window):
    clock = pygame.time.Clock()  # Create a clock object for managing time
    background, bg_image = get_background("Blue.png")  # Load the background

    block_size = 96  # Define the size of blocks

    player = Player(-950, 600, 50, 50)  # Initialize the player
    

    moving_platform = MovingPlatform(94, HEIGHT - block_size * 6, block_size *4, block_size // 
                                     4, speed=2, min_y=HEIGHT - block_size * 7, max_y=HEIGHT - block_size * 0)

    # Initialize spikehead traps
    spike_head = SpikeHead(-584, HEIGHT - block_size - 500, 54, 70, speed=5, min_y=HEIGHT - 800, max_y=HEIGHT - block_size)  # Adjust x, y position as needed
    spike_head.Blink()  # Turn the spikehead on

    spike_head1 = SpikeHead(-384, HEIGHT - block_size - 500, 54, 70, speed=5, min_y=HEIGHT - 500, max_y=HEIGHT - block_size)  # Adjust x, y position as needed
    spike_head1.Blink()  # Turn the spikehead on

    spike_head2 = SpikeHead(-284, HEIGHT - block_size - 500, 54, 70, speed=5, min_y=HEIGHT - 600, max_y=HEIGHT - block_size)  # Adjust x, y position as needed
    spike_head2.Blink()  # Turn the spikehead on

    spike_head3 = SpikeHead(-184, HEIGHT - block_size - 500, 54, 70, speed=5, min_y=HEIGHT - 700, max_y=HEIGHT - block_size)  # Adjust x, y position as needed
    spike_head3.Blink()  # Turn the spikehead on

    spike_head4 = SpikeHead(100, HEIGHT - block_size - 500, 54, 70, speed=4, min_y=HEIGHT - 800, max_y=HEIGHT - block_size)  # Adjust x, y position as needed
    spike_head4.Blink()  # Turn the spikehead on

    spike_head5 = SpikeHead(240, HEIGHT - block_size - 500, 54, 70, speed=4, min_y=HEIGHT - 600, max_y=HEIGHT - block_size)  # Adjust x, y position as needed
    spike_head5.Blink()  # Turn the spikehead on

    spike_head6 = SpikeHead(380, HEIGHT - block_size - 500, 54, 70, speed=4, min_y=HEIGHT - 700, max_y=HEIGHT - block_size)  # Adjust x, y position as needed
    spike_head6.Blink()  # Turn the spikehead on

    spike_head7 = SpikeHead(761, HEIGHT - block_size - 500, 54, 70, speed=7, min_y=HEIGHT - 900, max_y=HEIGHT - block_size)  # Adjust x, y position as needed
    spike_head7.Blink()  # Turn the spikehead on

    # Create the floor and other blocks
    floor = [Block(i * block_size, HEIGHT - block_size, block_size,)
             for i in range(-WIDTH // block_size, (WIDTH * 1) // block_size)]
    objects = [moving_platform, *floor, spike_head, spike_head1, spike_head2, spike_head3, spike_head4, spike_head5, spike_head6, spike_head7]

    # left wall
    objects.append(Block(-1056, HEIGHT - block_size * 2, block_size, 0, 128))
    objects.append(Block(-1056, HEIGHT - block_size * 3, block_size, 0, 128))
    objects.append(Block(-1056, HEIGHT - block_size * 4, block_size, 0, 128))
    objects.append(Block(-1056, HEIGHT - block_size * 5, block_size, 0, 128))
    objects.append(Block(-1056, HEIGHT - block_size * 6, block_size, 0, 128))
    objects.append(Block(-1056, HEIGHT - block_size * 7, block_size, 0, 128))
    objects.append(Block(-1056, HEIGHT - block_size * 8, block_size, 0, 128))
    objects.append(Block(-1056, HEIGHT - block_size * 9, block_size, 0, 128))
    objects.append(Block(-1056, HEIGHT - block_size * 10, block_size, 0, 128))
    objects.append(Block(-1056, HEIGHT - block_size * 11, block_size, 0, 128))
    objects.append(Block(-1056, HEIGHT - block_size * 12, block_size, 0, 128))

    # right wall
    objects.append(Block(864, HEIGHT - block_size * 2, block_size, 0, 128))
    objects.append(Block(864, HEIGHT - block_size * 3, block_size, 0, 128))
    objects.append(Block(864, HEIGHT - block_size * 4, block_size, 0, 128))
    objects.append(Block(864, HEIGHT - block_size * 5, block_size, 0, 128))
    objects.append(Block(864, HEIGHT - block_size * 6, block_size, 0, 128))
    objects.append(Block(864, HEIGHT - block_size * 7, block_size, 0, 128))
    objects.append(Block(864, HEIGHT - block_size * 9, block_size, 0, 128))
    objects.append(Block(864, HEIGHT - block_size * 10, block_size, 0, 128))
    objects.append(Block(864, HEIGHT - block_size * 11, block_size, 0, 128))
    objects.append(Block(864, HEIGHT - block_size * 12, block_size, 0, 128))
    objects.append(Block(864, HEIGHT - block_size * 13, block_size, 0, 128))
    objects.append(Block(864, HEIGHT - block_size * 14, block_size, 0, 128))
    objects.append(Block(864, HEIGHT - block_size * 15, block_size, 0, 128))

    objects.append(Block(960, HEIGHT - block_size * 9, block_size, 0, 128))
    objects.append(Block(1056, HEIGHT - block_size * 9, block_size, 0, 128))
    objects.append(Block(1056, HEIGHT - block_size * 8, block_size, 0, 128))
    objects.append(Block(1056, HEIGHT - block_size * 7, block_size, 0, 128))

    # platforms
    objects.append(Block(-864, HEIGHT - block_size * 2, block_size, 192, 128))
    objects.append(Block(-864, HEIGHT - block_size * 3, block_size, 192, 128))
    objects.append(Block(-864, HEIGHT - block_size * 4, block_size, 192, 128))
    objects.append(Block(-864, HEIGHT - block_size * 5, block_size, 192, 128))

    objects.append(Block(-672, HEIGHT - block_size * 2, block_size, 192, 128))
    objects.append(Block(-672, HEIGHT - block_size * 3, block_size, 192, 128))

    objects.append(Block(-480, HEIGHT - block_size * 2, block_size, 192, 128))
    objects.append(Block(-480, HEIGHT - block_size * 3, block_size, 192, 128))

    objects.append(Block(0, HEIGHT - block_size * 2, block_size, 0, 128))
    objects.append(Block(0, HEIGHT - block_size * 3, block_size, 0, 128))
    objects.append(Block(0, HEIGHT - block_size * 4, block_size, 0, 128))
    objects.append(Block(0, HEIGHT - block_size * 5, block_size, 0, 128))
    objects.append(Block(0, HEIGHT - block_size * 6, block_size, 0, 128))
    objects.append(Block(672, HEIGHT - block_size * 2, block_size, 192, 128))
    objects.append(Block(480, HEIGHT - block_size * 3, block_size, 0, 128))
    objects.append(Block(480, HEIGHT - block_size * 4, block_size, 0, 128))
    objects.append(Block(480, HEIGHT - block_size * 5, block_size, 0, 128))
    objects.append(Block(480, HEIGHT - block_size * 6, block_size, 0, 128))
    objects.append(Block(480, HEIGHT - block_size * 7, block_size, 0, 128))
    objects.append(Block(480, HEIGHT - block_size * 8, block_size, 0, 128))
    objects.append(Block(480, HEIGHT - block_size * 9, block_size, 0, 128))
    objects.append(Block(480, HEIGHT - block_size * 10, block_size, 0, 128))
    objects.append(Block(480, HEIGHT - block_size * 11, block_size, 0, 128))
    objects.append(Block(480, HEIGHT - block_size * 12, block_size, 0, 128))
    objects.append(Block(480, HEIGHT - block_size * 13, block_size, 0, 128))
    objects.append(Block(480, HEIGHT - block_size * 14, block_size, 0, 128))
    objects.append(Block(480, HEIGHT - block_size * 15, block_size, 0, 128))

    # Add a level complete block at the desired location
    level_end_block = Block(960, HEIGHT - block_size * 7, block_size, 272, 128)  # End block
    level_end_block.name = "level_end"  # Give the block a unique name
    objects.append(level_end_block)

    # row of blocks
    def add_row_of_blocks(objects, start_x, y, num_blocks, block_size, sprite_x=96, sprite_y=0):
   
        for i in range(num_blocks):
            x = start_x + i * block_size
            block = Block(x, y, block_size, sprite_x, sprite_y)  # Create the block
            objects.append(block)  # Add it to the list of objects

    # adding row of blocks
    
    add_row_of_blocks(objects, start_x=-1056, y=HEIGHT - block_size * 1, num_blocks=21, block_size=96, sprite_x=96, sprite_y=128)

    offset_x = -1550 + WIDTH // 2  # Offset horizontally based on player's starting x position
    offset_y = -1400 + HEIGHT // 2  # Offset vertically based on player's starting y position
    scroll_area_width = 200  # Define the scroll area width

    run = True
    while run:
        clock.tick(FPS)  # Cap the frame rate
    
        # Handle events like quitting and jumping
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:  # Allow double jumping
                    player.jump()

        player.loop(FPS)  # Update the player
        moving_platform.loop()
        spike_head.loop()
        spike_head1.loop()
        spike_head2.loop()
        spike_head3.loop()
        spike_head4.loop()
        spike_head5.loop()
        spike_head6.loop()
        spike_head7.loop()

        handle_move(player, objects,)  # Handle player movement and collisions
        draw(window, background, bg_image, player, objects, offset_x)  # Draw everything

        if player.health <= 0:  # Check if player's health is 0
            run = False  # End the game loop
            game_over(window)  # Display the game over screen

        # Handle screen scrolling based on player position
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

        # Check for collisions and update the game state
        handle_vertical_collision(player, objects, player.y_vel)

    pygame.quit()  # Quit the game
    quit()

if __name__ == "__main__":
    main(window)  # Run the game