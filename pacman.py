import pygame
import sys
import random
import math
import os
import json

# Initialize Pygame and Mixer
pygame.init()
pygame.mixer.init() 
pygame.font.init()

# Game Constants
TILE_SIZE = 40
FPS = 60
POWERUP_DURATION = 7000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCORE_FILE = os.path.join(BASE_DIR, "scores.json")

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
CYAN = (0, 255, 255)
GREEN = (0, 255, 0)

# --- SCORE MANAGEMENT ---
def load_scores():
    try:
        with open(SCORE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_score(new_score):
    if new_score == 0: 
        return 
    scores = load_scores()
    scores.append(new_score)
    scores.sort(reverse=True) 
    scores = scores[:5] # Keep only top 5 scores
    with open(SCORE_FILE, "w") as f:
        json.dump(scores, f)

# --- AUDIO & ASSET PATHS ---
BGM_LOBBY = os.path.join(BASE_DIR, "bgm_lobby.mp3")
BGM_INGAME = os.path.join(BASE_DIR, "bgm.mp3")

def play_music(music_path):
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"Error loading {music_path}: {e}")

try:
    chomp_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, "chomp.mp3"))
    chomp_sound.set_volume(0.3)
except Exception:
    chomp_sound = None

try:
    death_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, "death.mp3"))
    death_sound.set_volume(0.7)
except Exception:
    death_sound = None

try:
    raw_ghost_img = pygame.image.load(os.path.join(BASE_DIR, "ghost.png"))
    ghost_img = pygame.transform.scale(raw_ghost_img, (TILE_SIZE - 10, TILE_SIZE - 10))
except Exception:
    ghost_img = None

try:
    raw_scared_img = pygame.image.load(os.path.join(BASE_DIR, "scared_ghost.png"))
    scared_ghost_img = pygame.transform.scale(raw_scared_img, (TILE_SIZE - 10, TILE_SIZE - 10))
except Exception:
    scared_ghost_img = None

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
pygame.display.set_caption("Pac-Man: Arcade Edition")
clock = pygame.time.Clock()

font_title = pygame.font.SysFont("Arial", 48, bold=True)
font_menu = pygame.font.SysFont("Arial", 28)
font_score = pygame.font.SysFont("Arial", 24)

# Build Wall Rectangles
walls = []
for row_idx, row in enumerate(level_map):
    for col_idx, tile in enumerate(row):
        if tile == 1:
            walls.append(pygame.Rect(col_idx * TILE_SIZE, row_idx * TILE_SIZE, TILE_SIZE, TILE_SIZE))

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
        self.dx, self.dy = 0, 0

    def draw(self, surface):
        center_x, center_y = self.rect.centerx, self.rect.centery
        radius = self.rect.width // 2
        
        # Base Yellow Circle
        pygame.draw.circle(surface, YELLOW, (center_x, center_y), radius)

        # Mouth Animation
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

        # Horizontal Movement & Collision
        self.rect.x += self.dx * self.speed
        if self.check_collisions(walls): 
            self.rect.x -= self.dx * self.speed

        # Vertical Movement & Collision
        self.rect.y += self.dy * self.speed
        if self.check_collisions(walls): 
            self.rect.y -= self.dy * self.speed

    def check_collisions(self, tiles):
        for tile in tiles:
            if self.rect.colliderect(tile): 
                return True
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
            if scared_ghost_img: 
                surface.blit(scared_ghost_img, (self.rect.x, self.rect.y))
            else: 
                pygame.draw.rect(surface, CYAN, self.rect, border_radius=5)
        else:
            if ghost_img: 
                surface.blit(ghost_img, (self.rect.x, self.rect.y))
            else: 
                pygame.draw.rect(surface, RED, self.rect, border_radius=5)

    def update(self):
        # Only change direction when aligned perfectly with the grid
        if self.x % TILE_SIZE == 0 and self.y % TILE_SIZE == 0:
            grid_x, grid_y = int(self.x // TILE_SIZE), int(self.y // TILE_SIZE)
            possible_dirs = []
            
            # Check all 4 directions for available paths
            for nx, ny in [(1,0), (-1,0), (0,1), (0,-1)]:
                if 0 <= grid_y + ny < len(level_map) and 0 <= grid_x + nx < len(level_map[0]):
                    if level_map[grid_y + ny][grid_x + nx] != 1:
                        possible_dirs.append((nx, ny))
            
            # Prevent 180-degree turns unless it's a dead end
            if len(possible_dirs) > 1 and (-self.dx, -self.dy) in possible_dirs:
                possible_dirs.remove((-self.dx, -self.dy))
                
            if possible_dirs:
                self.dx, self.dy = random.choice(possible_dirs)
                
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.rect.x = self.x + 5
        self.rect.y = self.y + 5

def reset_level():
    pellets, power_pellets, ghost_spawns = [], [], []
    player_spawn = (TILE_SIZE, TILE_SIZE)
    
    for row_idx, row in enumerate(level_map):
        for col_idx, tile in enumerate(row):
            x, y = col_idx * TILE_SIZE, row_idx * TILE_SIZE
            if tile in [0, 8, 9]: 
                pellet_size = 6
                pellets.append(pygame.Rect(x + (TILE_SIZE//2) - (pellet_size//2), 
                                           y + (TILE_SIZE//2) - (pellet_size//2), pellet_size, pellet_size))
                if tile == 8: player_spawn = (x, y)
                elif tile == 9: ghost_spawns.append((col_idx, row_idx))
            elif tile == 2:
                p_size = 16
                power_pellets.append(pygame.Rect(x + (TILE_SIZE//2) - (p_size//2), 
                                                 y + (TILE_SIZE//2) - (p_size//2), p_size, p_size))
                
    return Player(*player_spawn), [Ghost(gx, gy) for gx, gy in ghost_spawns], pellets, power_pellets

# --- INITIAL GAME STATE ---
game_state = "MENU"
running = True
scared_timer = 0
high_scores = load_scores()

# Play Lobby BGM on startup
play_music(BGM_LOBBY)

# Initial Entity Declaration
pacman, ghosts, pellets, power_pellets = reset_level()

while running:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN:
            if game_state == "MENU":
                if event.key == pygame.K_RETURN:
                    # Start Game -> Play in-game BGM
                    pacman, ghosts, pellets, power_pellets = reset_level()
                    game_state = "PLAYING"
                    high_scores = load_scores()
                    play_music(BGM_INGAME)
                    
            elif game_state == "GAMEOVER":
                if event.key == pygame.K_RETURN:
                    # Return to Menu -> Reload scores & Play lobby BGM
                    game_state = "MENU"
                    high_scores = load_scores()
                    play_music(BGM_LOBBY)

            elif game_state == "PLAYING":
                if event.key == pygame.K_LEFT: pacman.dx, pacman.dy = -1, 0
                elif event.key == pygame.K_RIGHT: pacman.dx, pacman.dy = 1, 0
                elif event.key == pygame.K_UP: pacman.dx, pacman.dy = 0, -1
                elif event.key == pygame.K_DOWN: pacman.dx, pacman.dy = 0, 1

    # --- DRAW & UPDATE LOGIC ---
    screen.fill(BLACK)

    if game_state == "MENU":
        title = font_title.render("PAC-MAN PYTHON", True, YELLOW)
        start_txt = font_menu.render("Press [ENTER] to Play", True, WHITE)
        score_title = font_menu.render("TOP SCORES", True, CYAN)
        
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        screen.blit(start_txt, (SCREEN_WIDTH//2 - start_txt.get_width()//2, 160))
        screen.blit(score_title, (SCREEN_WIDTH//2 - score_title.get_width()//2, 240))
        
        if not high_scores:
            no_score = font_score.render("No scores yet!", True, WHITE)
            screen.blit(no_score, (SCREEN_WIDTH//2 - no_score.get_width()//2, 290))
        else:
            for i, score in enumerate(high_scores):
                s_txt = font_score.render(f"{i+1}.   {score}", True, WHITE)
                screen.blit(s_txt, (SCREEN_WIDTH//2 - s_txt.get_width()//2, 290 + (i * 30)))

    elif game_state == "PLAYING":
        pacman.update()
        
        # Eat Regular Pellets
        for pellet in pellets[:]:
            if pacman.rect.colliderect(pellet):
                pellets.remove(pellet)
                pacman.score += 10
                if chomp_sound: 
                    chomp_sound.play() 
                
        # Eat Power Pellets
        for p_pellet in power_pellets[:]:
            if pacman.rect.colliderect(p_pellet):
                power_pellets.remove(p_pellet)
                pacman.score += 50
                scared_timer = current_time + POWERUP_DURATION
                for ghost in ghosts:
                    ghost.is_scared = True
                    # Instantly reverse direction
                    ghost.dx, ghost.dy = -ghost.dx, -ghost.dy 
                if chomp_sound: 
                    chomp_sound.play()

        # Check Scared Status Timer
        if current_time > scared_timer:
            for ghost in ghosts: 
                ghost.is_scared = False

        # Ghost Collision Logic
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
                        save_score(pacman.score)
                        game_state = "GAMEOVER"
                        pygame.mixer.music.stop() 
                    else:
                        pacman.reset_position()
                        for g in ghosts: 
                            g.reset_position()
                        pygame.time.delay(1000)
                
        # Win Condition Checker
        if len(pellets) == 0 and len(power_pellets) == 0:
            save_score(pacman.score)
            game_state = "GAMEOVER"
            pygame.mixer.music.stop()

        # Render Game Objects
        for wall in walls:
            pygame.draw.rect(screen, BLUE, wall, 2, border_radius=5)
        for pellet in pellets:
            pygame.draw.circle(screen, WHITE, pellet.center, pellet.width // 2)
        for p_pellet in power_pellets:
            # Blinking effect for power pellets
            if (current_time // 200) % 2 == 0:
                pygame.draw.circle(screen, WHITE, p_pellet.center, p_pellet.width // 2)

        for ghost in ghosts: 
            ghost.draw(screen)
            
        pacman.draw(screen)

        # UI Overlay
        score_text = font_score.render(f"Score: {pacman.score}", True, WHITE)
        lives_text = font_score.render(f"Lives: {pacman.lives}", True, YELLOW)
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (SCREEN_WIDTH - 100, 10))

    elif game_state == "GAMEOVER":
        # Draw Darkened Map Background
        for wall in walls: 
            pygame.draw.rect(screen, (0, 0, 100), wall, 2, border_radius=5)
        
        msg = "YOU WIN!" if (len(pellets) == 0 and len(power_pellets) == 0) else "GAME OVER"
        color = GREEN if (len(pellets) == 0 and len(power_pellets) == 0) else RED
        
        end_text = font_title.render(msg, True, color)
        score_txt = font_menu.render(f"Final Score: {pacman.score}", True, WHITE)
        retry_txt = font_score.render("Press [ENTER] to return to Lobby", True, YELLOW)
        
        screen.blit(end_text, (SCREEN_WIDTH//2 - end_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
        screen.blit(score_txt, (SCREEN_WIDTH//2 - score_txt.get_width()//2, SCREEN_HEIGHT//2))
        screen.blit(retry_txt, (SCREEN_WIDTH//2 - retry_txt.get_width()//2, SCREEN_HEIGHT//2 + 50))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()