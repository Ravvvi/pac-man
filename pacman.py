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
    scores = scores[:5]
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
        pass

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

# Map Definition
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

# Global flag to track fullscreen status
is_fullscreen = False
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pac-Man: Hardcore Endless")
clock = pygame.time.Clock()

font_title = pygame.font.SysFont("Arial", 48, bold=True)
font_menu = pygame.font.SysFont("Arial", 28)
font_score = pygame.font.SysFont("Arial", 24)

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
        self.next_dx = 0  
        self.next_dy = 0  
        self.score = 0
        self.lives = 3 
        self.mouth_open = True
        self.animation_timer = 0

    def reset_position(self):
        self.rect.x = self.spawn_x + 5
        self.rect.y = self.spawn_y + 5
        self.dx, self.dy = 0, 0
        self.next_dx, self.next_dy = 0, 0

    def draw(self, surface):
        center_x, center_y = self.rect.centerx, self.rect.centery
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

    def check_collisions(self, tiles, rect_to_check=None):
        if rect_to_check is None:
            rect_to_check = self.rect
        for tile in tiles:
            if rect_to_check.colliderect(tile): 
                return True
        return False

    def update(self):
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.mouth_open = not self.mouth_open
            self.animation_timer = 0

        if self.next_dx != 0 or self.next_dy != 0:
            target_x = round((self.rect.x - 5) / TILE_SIZE) * TILE_SIZE + 5
            target_y = round((self.rect.y - 5) / TILE_SIZE) * TILE_SIZE + 5
            
            margin = 18 
            can_turn = False
            test_rect = self.rect.copy()
            
            if self.next_dx != 0 and self.dy != 0: 
                if abs(self.rect.y - target_y) <= margin:
                    test_rect.y = target_y
                    test_rect.x += self.next_dx * self.speed
                    if not self.check_collisions(walls, test_rect):
                        self.rect.y = target_y 
                        self.dx, self.dy = self.next_dx, self.next_dy
                        self.next_dx, self.next_dy = 0, 0
                        can_turn = True

            elif self.next_dy != 0 and self.dx != 0: 
                if abs(self.rect.x - target_x) <= margin:
                    test_rect.x = target_x
                    test_rect.y += self.next_dy * self.speed
                    if not self.check_collisions(walls, test_rect):
                        self.rect.x = target_x 
                        self.dx, self.dy = self.next_dx, self.next_dy
                        self.next_dx, self.next_dy = 0, 0
                        can_turn = True
            
            if not can_turn:
                test_rect = self.rect.copy()
                test_rect.x += self.next_dx * self.speed
                test_rect.y += self.next_dy * self.speed
                if not self.check_collisions(walls, test_rect):
                    self.dx, self.dy = self.next_dx, self.next_dy
                    self.next_dx, self.next_dy = 0, 0

        self.rect.x += self.dx * self.speed
        if self.check_collisions(walls): 
            self.rect.x -= self.dx * self.speed

        self.rect.y += self.dy * self.speed
        if self.check_collisions(walls): 
            self.rect.y -= self.dy * self.speed

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
        if self.x % TILE_SIZE == 0 and self.y % TILE_SIZE == 0:
            grid_x, grid_y = int(self.x // TILE_SIZE), int(self.y // TILE_SIZE)
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

def reset_level(current_level):
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
                
    ghosts = []
    num_ghosts_to_spawn = min(current_level, 5)
    if ghost_spawns:
        for i in range(num_ghosts_to_spawn):
            gx, gy = ghost_spawns[i % len(ghost_spawns)]
            ghosts.append(Ghost(gx, gy))

    return Player(*player_spawn), ghosts, pellets, power_pellets

# --- INITIAL GAME STATE ---
game_state = "MENU"
running = True
scared_timer = 0
high_scores = load_scores()

# Progress Variables
current_level = 1
powerup_duration = 7000 
current_fps = 40

play_music(BGM_LOBBY)
pacman, ghosts, pellets, power_pellets = reset_level(current_level)

while running:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN:
            # Fullscreen toggle via F key
            if event.key == pygame.K_f:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
                else:
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

            if game_state == "MENU":
                if event.key == pygame.K_RETURN:
                    current_level = 1
                    current_fps = 40 
                    powerup_duration = 7000
                    pacman, ghosts, pellets, power_pellets = reset_level(current_level)
                    game_state = "PLAYING"
                    high_scores = load_scores()
                    play_music(BGM_INGAME)
                    
            elif game_state == "GAMEOVER":
                if event.key == pygame.K_RETURN:
                    game_state = "MENU"
                    high_scores = load_scores()
                    play_music(BGM_LOBBY)

            elif game_state == "PLAYING":
                if event.key == pygame.K_LEFT: pacman.next_dx, pacman.next_dy = -1, 0
                elif event.key == pygame.K_RIGHT: pacman.next_dx, pacman.next_dy = 1, 0
                elif event.key == pygame.K_UP: pacman.next_dx, pacman.next_dy = 0, -1
                elif event.key == pygame.K_DOWN: pacman.next_dx, pacman.next_dy = 0, 1

    # --- DRAW & UPDATE LOGIC ---
    screen.fill(BLACK)

    if game_state == "MENU":
        title = font_title.render("PAC-MAN: ENDLESS RUN", True, YELLOW)
        start_txt = font_menu.render("Press [ENTER] to Play (F for Fullscreen)", True, WHITE)
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
        
        for pellet in pellets[:]:
            if pacman.rect.colliderect(pellet):
                pellets.remove(pellet)
                pacman.score += 4 # Changed to 4 points per pellet
                
        for p_pellet in power_pellets[:]:
            if pacman.rect.colliderect(p_pellet):
                power_pellets.remove(p_pellet)
                pacman.score += 50
                scared_timer = current_time + powerup_duration
                for ghost in ghosts:
                    ghost.is_scared = True
                    ghost.dx, ghost.dy = -ghost.dx, -ghost.dy 
                if chomp_sound: 
                    chomp_sound.play()

        if current_time > scared_timer:
            for ghost in ghosts: 
                ghost.is_scared = False

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
                
        # --- ENDLESS MODE PROGRESSION LOGIC ---
        if len(pellets) == 0 and len(power_pellets) == 0:
            current_score = pacman.score
            current_lives = pacman.lives
            
            if current_level <= 10 and current_lives < 3:
                current_lives += 1
            
            current_level += 1
            powerup_duration = max(1000, powerup_duration - 1000)
            
            if current_level <= 5:
                current_fps = 40
            else:
                current_fps = 40 + ((current_level - 5) * 5)
            
            pacman, ghosts, pellets, power_pellets = reset_level(current_level)
            
            pacman.score = current_score
            pacman.lives = current_lives
            
            pygame.time.delay(1000)

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

        score_text = font_score.render(f"Score: {pacman.score}  |  Lvl: {current_level}", True, WHITE)
        lives_text = font_score.render(f"Lives: {pacman.lives}", True, YELLOW)
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (SCREEN_WIDTH - 100, 10))

    elif game_state == "GAMEOVER":
        for wall in walls: 
            pygame.draw.rect(screen, (0, 0, 100), wall, 2, border_radius=5)
        
        end_text = font_title.render("GAME OVER", True, RED)
        score_txt = font_menu.render(f"Final Score: {pacman.score} (Lvl {current_level})", True, WHITE)
        retry_txt = font_score.render("Press [ENTER] to return to Lobby (F to toggle Fullscreen)", True, YELLOW)
        
        screen.blit(end_text, (SCREEN_WIDTH//2 - end_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
        screen.blit(score_txt, (SCREEN_WIDTH//2 - score_txt.get_width()//2, SCREEN_HEIGHT//2))
        screen.blit(retry_txt, (SCREEN_WIDTH//2 - retry_txt.get_width()//2, SCREEN_HEIGHT//2 + 50))

    pygame.display.flip()
    
    clock.tick(current_fps)

pygame.quit()
sys.exit()