import pygame
import sys
import random
import math

# Initialize Pygame and Mixer (Audio)
pygame.init()
pygame.mixer.init() # Inisialisasi modul suara
pygame.font.init()

# Game Constants
TILE_SIZE = 40
FPS = 60
POWERUP_DURATION = 7000 # 7 detik

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
CYAN = (0, 255, 255)

# --- LOAD AUDIO ASSETS ---
try:
    pygame.mixer.music.load("bgm.mp3")
    pygame.mixer.music.set_volume(0.4) 
    pygame.mixer.music.play(-1) 
except Exception:
    print("Warning: bgm.mp3 tidak ditemukan.")

try:
    chomp_sound = pygame.mixer.Sound("chomp.wav")
    chomp_sound.set_volume(0.3)
except Exception:
    chomp_sound = None
    print("Warning: chomp.wav tidak ditemukan.")

try:
    death_sound = pygame.mixer.Sound("death.wav")
    death_sound.set_volume(0.7)
except Exception:
    death_sound = None
    print("Warning: death.wav tidak ditemukan.")

# --- LOAD IMAGE ASSETS ---
# Load Hantu Normal
try:
    raw_ghost_img = pygame.image.load("ghost.png")
    ghost_img = pygame.transform.scale(raw_ghost_img, (TILE_SIZE - 10, TILE_SIZE - 10))
except Exception:
    ghost_img = None
    print("Warning: ghost.png not found.")

# Load Hantu Biru (Saat Ketakutan)
try:
    raw_scared_img = pygame.image.load("scared_ghost.png")
    scared_ghost_img = pygame.transform.scale(raw_scared_img, (TILE_SIZE - 10, TILE_SIZE - 10))
except Exception:
    scared_ghost_img = None
    print("Warning: scared_ghost.png not found.")

# Map Definition (1 = Wall, 0 = Pellet, 2 = Power Pellet, 9 = Ghost, 8 = Player)
level_map = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 8, 0, 0, 0, 2, 1, 9, 2, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 9, 0, 0, 1, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1],
    [1, 2, 0, 0, 0, 0, 1, 9, 0, 0, 0, 0, 0, 2, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

SCREEN_WIDTH = len(level_map[0]) * TILE_SIZE
SCREEN_HEIGHT = len(level_map) * TILE_SIZE
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pac-Man: Full Assets")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)

# Create Environment
walls = []
pellets = []
power_pellets = []
ghost_spawns = []
player_spawn = (TILE_SIZE, TILE_SIZE)

for row_idx, row in enumerate(level_map):
    for col_idx, tile in enumerate(row):
        x = col_idx * TILE_SIZE
        y = row_idx * TILE_SIZE
        if tile == 1:
            walls.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
        elif tile in [0, 8, 9]: 
            pellet_size = 6
            pellets.append(pygame.Rect(x + (TILE_SIZE//2) - (pellet_size//2), 
                                       y + (TILE_SIZE//2) - (pellet_size//2), 
                                       pellet_size, pellet_size))
            if tile == 8: player_spawn = (x, y)
            elif tile == 9: ghost_spawns.append((col_idx, row_idx))
        elif tile == 2:
            p_size = 16
            power_pellets.append(pygame.Rect(x + (TILE_SIZE//2) - (p_size//2), 
                                             y + (TILE_SIZE//2) - (p_size//2), 
                                             p_size, p_size))

class Player:
    def __init__(self, x, y):
        self.spawn_x = x
        self.spawn_y = y
        self.rect = pygame.Rect(x + 5, y + 5, TILE_SIZE - 10, TILE_SIZE - 10)
        self.speed = 4
        self.dx = 0
        self.dy = 0
        self.score = 0
        self.lives = 3 
        self.mouth_open = True
        self.animation_timer = 0

    def reset_position(self):
        self.rect.x = self.spawn_x + 5
        self.rect.y = self.spawn_y + 5
        self.dx = 0
        self.dy = 0

    def draw(self, surface):
        center_x = self.rect.centerx
        center_y = self.rect.centery
        radius = self.rect.width // 2

        pygame.draw.circle(surface, YELLOW, (center_x, center_y), radius)

        if self.mouth_open:
            angle = 0
            if self.dx == 1: angle = 0
            elif self.dx == -1: angle = 180
            elif self.dy == -1: angle = 90
            elif self.dy == 1: angle = 270

            spread = 45 
            rad1 = math.radians(angle - spread)
            rad2 = math.radians(angle + spread)
            
            p1 = (center_x + radius * math.cos(rad1), center_y - radius * math.sin(rad1))
            p2 = (center_x + radius * math.cos(rad2), center_y - radius * math.sin(rad2))
            
            pygame.draw.polygon(surface, BLACK, [(center_x, center_y), p1, p2])

    def update(self):
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.mouth_open = not self.mouth_open
            self.animation_timer = 0

        self.rect.x += self.dx * self.speed
        if self.check_collisions(walls): self.rect.x -= self.dx * self.speed

        self.rect.y += self.dy * self.speed
        if self.check_collisions(walls): self.rect.y -= self.dy * self.speed

    def check_collisions(self, tiles):
        for tile in tiles:
            if self.rect.colliderect(tile): return True
        return False

class Ghost:
    def __init__(self, grid_x, grid_y):
        self.spawn_grid_x = grid_x
        self.spawn_grid_y = grid_y
        self.x = grid_x * TILE_SIZE
        self.y = grid_y * TILE_SIZE
        self.rect = pygame.Rect(self.x + 5, self.y + 5, TILE_SIZE - 10, TILE_SIZE - 10)
        self.speed = 2 
        self.dx = 1
        self.dy = 0
        self.is_scared = False

    def reset_position(self):
        self.x = self.spawn_grid_x * TILE_SIZE
        self.y = self.spawn_grid_y * TILE_SIZE
        self.rect.x = self.x + 5
        self.rect.y = self.y + 5
        self.is_scared = False

    def draw(self, surface):
        if self.is_scared:
            # Gunakan gambar hantu biru jika tersedia
            if scared_ghost_img:
                surface.blit(scared_ghost_img, (self.rect.x, self.rect.y))
            else:
                pygame.draw.rect(surface, CYAN, self.rect, border_radius=5)
        else:
            # Gunakan gambar hantu normal jika tersedia
            if ghost_img:
                surface.blit(ghost_img, (self.rect.x, self.rect.y))
            else:
                pygame.draw.rect(surface, RED, self.rect, border_radius=5)

    def update(self):
        if self.x % TILE_SIZE == 0 and self.y % TILE_SIZE == 0:
            grid_x = int(self.x // TILE_SIZE)
            grid_y = int(self.y // TILE_SIZE)
            
            possible_dirs = []
            for nx, ny in [(1,0), (-1,0), (0,1), (0,-1)]:
                if 0 <= grid_y + ny < len(level_map) and 0 <= grid_x + nx < len(level_map[0]):
                    if level_map[grid_y + ny][grid_x + nx] != 1:
                        possible_dirs.append((nx, ny))
            
            if len(possible_dirs) > 1 and (-self.dx, -self.dy) in possible_dirs:
                possible_dirs.remove((-self.dx, -self.dy))
                
            if possible_dirs:
                self.dx, self.dy = random.choice(possible_dirs)
                
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        
        self.rect.x = self.x + 5
        self.rect.y = self.y + 5

# Initialize Entities
pacman = Player(*player_spawn)
ghosts = [Ghost(gx, gy) for gx, gy in ghost_spawns]

# Game State
running = True
game_over = False
scared_timer = 0

while running:
    current_time = pygame.time.get_ticks()
    
    # 1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN and not game_over:
            if event.key == pygame.K_LEFT: pacman.dx, pacman.dy = -1, 0
            elif event.key == pygame.K_RIGHT: pacman.dx, pacman.dy = 1, 0
            elif event.key == pygame.K_UP: pacman.dx, pacman.dy = 0, -1
            elif event.key == pygame.K_DOWN: pacman.dx, pacman.dy = 0, 1

    # 2. Game Logic Update
    if not game_over:
        pacman.update()
        
        # Makan Titik Kecil (Play Audio)
        for pellet in pellets[:]:
            if pacman.rect.colliderect(pellet):
                pellets.remove(pellet)
                pacman.score += 10
                if chomp_sound: 
                    chomp_sound.play() 
                
        # Makan Power Pellet
        for p_pellet in power_pellets[:]:
            if pacman.rect.colliderect(p_pellet):
                power_pellets.remove(p_pellet)
                pacman.score += 50
                scared_timer = current_time + POWERUP_DURATION
                for ghost in ghosts:
                    ghost.is_scared = True
                    ghost.dx, ghost.dy = -ghost.dx, -ghost.dy 
                if chomp_sound: 
                    chomp_sound.play()

        # Cek status takut hantu
        if current_time > scared_timer:
            for ghost in ghosts:
                ghost.is_scared = False

        # Update Hantu dan Cek Tabrakan
        for ghost in ghosts:
            ghost.update()
            if pacman.rect.colliderect(ghost.rect):
                if ghost.is_scared:
                    pacman.score += 200
                    ghost.reset_position() 
                else:
                    if death_sound:
                        death_sound.play() 
                        
                    pacman.lives -= 1
                    if pacman.lives <= 0:
                        game_over = True
                        pygame.mixer.music.stop() 
                    else:
                        pacman.reset_position()
                        for g in ghosts:
                            g.reset_position()
                        pygame.time.delay(1000)
                
        # Cek kondisi menang
        if len(pellets) == 0 and len(power_pellets) == 0:
            game_over = True
            pygame.mixer.music.stop()

    # 3. Drawing
    screen.fill(BLACK)
    for wall in walls:
        pygame.draw.rect(screen, BLUE, wall, 2, border_radius=5)
    for pellet in pellets:
        pygame.draw.circle(screen, WHITE, pellet.center, pellet.width // 2)
    for p_pellet in power_pellets:
        if (current_time // 200) % 2 == 0:
            pygame.draw.circle(screen, WHITE, p_pellet.center, p_pellet.width // 2)

    for ghost in ghosts:
        ghost.draw(screen)
    pacman.draw(screen)

    score_text = font.render(f"Score: {pacman.score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    lives_text = font.render(f"Lives: {pacman.lives}", True, YELLOW)
    screen.blit(lives_text, (SCREEN_WIDTH - 100, 10))

    if game_over:
        msg = "YOU WIN!" if (len(pellets) == 0 and len(power_pellets) == 0) else "GAME OVER"
        color = YELLOW if (len(pellets) == 0 and len(power_pellets) == 0) else RED
        end_text = font.render(msg, True, color)
        screen.blit(end_text, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 - 20))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()