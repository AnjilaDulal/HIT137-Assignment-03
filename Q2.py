import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
GRAVITY = 0.8
GROUND_LEVEL = SCREEN_HEIGHT - 100

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
DARK_GREEN = (0, 100, 0)
SKY_BLUE = (135, 206, 235)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 50
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_power = -15
        self.on_ground = False
        self.health = 100
        self.max_health = 100
        self.lives = 3
        self.score = 0
        self.facing_right = True
        self.shoot_cooldown = 0
        self.invulnerable = 0
        
    def update(self, keys):
        # Handle input
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -self.speed
            self.facing_right = False
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = self.speed
            self.facing_right = True
        else:
            self.vel_x = 0
            
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
            
        # Apply gravity
        self.vel_y += GRAVITY
        
        # Update position
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Ground collision
        if self.y + self.height >= GROUND_LEVEL:
            self.y = GROUND_LEVEL - self.height
            self.vel_y = 0
            self.on_ground = True
            
        # Screen boundaries
        if self.x < 0:
            self.x = 0
        elif self.x + self.width > 2000:  # Level width
            self.x = 2000 - self.width
            
        # Update cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.invulnerable > 0:
            self.invulnerable -= 1
            
    def shoot(self):
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = 20
            direction = 1 if self.facing_right else -1
            return Projectile(self.x + self.width//2, self.y + self.height//2, direction)
        return None
        
    def take_damage(self, damage):
        if self.invulnerable <= 0:
            self.health -= damage
            self.invulnerable = 60
            if self.health <= 0:
                self.lives -= 1
                if self.lives > 0:
                    self.health = self.max_health
                    
    def draw(self, screen, camera_x):
        x = self.x - camera_x
        y = self.y
        color = ORANGE if self.invulnerable % 10 < 5 else (255, 140, 0)
        
        # Fox body
        pygame.draw.ellipse(screen, color, (x, y + 20, self.width, 25))
        # Fox head
        pygame.draw.ellipse(screen, color, (x + 5, y, 30, 25))
        # Fox ears
        ear_x = x + 8 if self.facing_right else x + 22
        pygame.draw.polygon(screen, color, [(ear_x, y), (ear_x + 8, y), (ear_x + 4, y - 10)])
        # Fox tail
        tail_x = x - 15 if self.facing_right else x + self.width + 5
        pygame.draw.ellipse(screen, color, (tail_x, y + 15, 20, 15))
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Projectile:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = 8
        self.width = 6
        self.height = 3
        self.damage = 25
        
    def update(self):
        self.x += self.speed * self.direction
        
    def draw(self, screen, camera_x):
        x = self.x - camera_x
        pygame.draw.ellipse(screen, YELLOW, (x, self.y, self.width, self.height))
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Enemy:
    def __init__(self, x, y, enemy_type="soldier"):
        self.x = x
        self.y = y
        self.width = 35
        self.height = 45
        self.enemy_type = enemy_type
        self.speed = 2 if enemy_type == "soldier" else 1
        self.health = 50 if enemy_type == "soldier" else 100
        self.max_health = self.health
        self.damage = 20 if enemy_type == "soldier" else 30
        self.direction = -1
        self.patrol_range = 150
        self.start_x = x
        self.shoot_cooldown = 0
        self.alive = True
        
    def update(self, player):
        if not self.alive:
            return None
            
        # Simple AI - patrol and chase player if close
        dist_to_player = abs(self.x - player.x)
        if dist_to_player < 200:
            # Chase player
            if player.x < self.x:
                self.direction = -1
            else:
                self.direction = 1
        else:
            # Patrol
            if abs(self.x - self.start_x) > self.patrol_range:
                self.direction *= -1
                
        self.x += self.speed * self.direction
        
        # Shoot at player occasionally
        if dist_to_player < 300 and self.shoot_cooldown <= 0 and random.randint(1, 100) < 3:
            self.shoot_cooldown = 60
            direction = 1 if player.x > self.x else -1
            return Projectile(self.x + self.width//2, self.y + self.height//2, direction)
            
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        return None
        
    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.alive = False
            
    def draw(self, screen, camera_x):
        if not self.alive:
            return
            
        x = self.x - camera_x
        
        if self.enemy_type == "soldier":
            # Human soldier
            pygame.draw.rect(screen, BROWN, (x, self.y, self.width, self.height))
            # Head
            pygame.draw.circle(screen, (255, 220, 177), (x + self.width//2, self.y - 10), 12)
            # Weapon
            pygame.draw.rect(screen, BLACK, (x + self.width//2, self.y + 15, 20, 3))
        else:
            # Boss enemy
            pygame.draw.rect(screen, GRAY, (x, self.y, self.width, self.height))
            pygame.draw.circle(screen, BLACK, (x + self.width//2, self.y - 15), 15)
            
        # Health bar
        if self.health < self.max_health:
            bar_width = 30
            bar_height = 4
            health_ratio = self.health / self.max_health
            pygame.draw.rect(screen, RED, (x, self.y - 20, bar_width, bar_height))
            pygame.draw.rect(screen, GREEN, (x, self.y - 20, bar_width * health_ratio, bar_height))
            
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Collectible:
    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.item_type = item_type  # "health", "life", "score"
        self.collected = False
        self.bob_offset = 0
        
    def update(self):
        self.bob_offset += 0.1
        
    def draw(self, screen, camera_x):
        if self.collected:
            return
            
        x = self.x - camera_x
        y = self.y + math.sin(self.bob_offset) * 3
        
        if self.item_type == "health":
            pygame.draw.rect(screen, RED, (x, y, self.width, self.height))
            pygame.draw.rect(screen, WHITE, (x + 6, y + 2, 8, 16))
            pygame.draw.rect(screen, WHITE, (x + 2, y + 6, 16, 8))
        elif self.item_type == "life":
            pygame.draw.circle(screen, GREEN, (x + 10, int(y + 10)), 10)
            pygame.draw.circle(screen, WHITE, (x + 10, int(y + 10)), 6)
        else:  # score
            pygame.draw.circle(screen, YELLOW, (x + 10, int(y + 10)), 10)
            
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Fox Adventure")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = "menu"
        self.current_level = 1
        self.camera_x = 0
        self.level_width = 2000
        
        # Initialize empty game objects
        self.player = Player(100, GROUND_LEVEL - 50)
        self.projectiles = []
        self.enemy_projectiles = []
        self.enemies = []
        self.collectibles = []
        
    def reset_game(self):
        self.player = Player(100, GROUND_LEVEL - 50)
        self.projectiles = []
        self.enemy_projectiles = []
        self.enemies = []
        self.collectibles = []
        self.current_level = 1
        self.camera_x = 0
        self.load_level(self.current_level)
        
    def load_level(self, level):
        self.enemies.clear()
        self.collectibles.clear()
        self.projectiles.clear()
        self.enemy_projectiles.clear()
        
        if level == 1:
            # Level 1: Forest
            for i in range(5):
                self.enemies.append(Enemy(300 + i * 200, GROUND_LEVEL - 45, "soldier"))
            for i in range(8):
                x = random.randint(200, self.level_width - 200)
                y = random.randint(GROUND_LEVEL - 200, GROUND_LEVEL - 50)
                item_type = random.choice(["health", "score", "score", "score"])
                self.collectibles.append(Collectible(x, y, item_type))
        elif level == 2:
            # Level 2: Desert
            for i in range(7):
                self.enemies.append(Enemy(250 + i * 180, GROUND_LEVEL - 45, "soldier"))
            for i in range(10):
                x = random.randint(200, self.level_width - 200)
                y = random.randint(GROUND_LEVEL - 200, GROUND_LEVEL - 50)
                item_type = random.choice(["health", "life", "score", "score"])
                self.collectibles.append(Collectible(x, y, item_type))
        else:
            # Level 3: Final boss level
            self.enemies.append(Enemy(self.level_width - 300, GROUND_LEVEL - 45, "boss"))
            for i in range(3):
                self.enemies.append(Enemy(400 + i * 200, GROUND_LEVEL - 45, "soldier"))
            for i in range(12):
                x = random.randint(200, self.level_width - 400)
                y = random.randint(GROUND_LEVEL - 200, GROUND_LEVEL - 50)
                item_type = random.choice(["health", "life", "score"])
                self.collectibles.append(Collectible(x, y, item_type))
                
    def update_camera(self):
        # Smooth camera following
        target_x = self.player.x - SCREEN_WIDTH // 3
        self.camera_x += (target_x - self.camera_x) * 0.1
        
        # Keep camera within level bounds
        self.camera_x = max(0, min(self.camera_x, self.level_width - SCREEN_WIDTH))
        
    def handle_collisions(self):
        player_rect = self.player.get_rect()
        
        # Player projectiles vs enemies
        for projectile in self.projectiles[:]:
            proj_rect = projectile.get_rect()
            for enemy in self.enemies:
                if enemy.alive and proj_rect.colliderect(enemy.get_rect()):
                    enemy.take_damage(projectile.damage)
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    if not enemy.alive:
                        self.player.score += 100
                    break
                    
        # Enemy projectiles vs player
        for projectile in self.enemy_projectiles[:]:
            if projectile.get_rect().colliderect(player_rect):
                self.player.take_damage(15)
                self.enemy_projectiles.remove(projectile)
                
        # Player vs enemies
        for enemy in self.enemies:
            if enemy.alive and player_rect.colliderect(enemy.get_rect()):
                self.player.take_damage(enemy.damage)
                
        # Player vs collectibles
        for collectible in self.collectibles:
            if not collectible.collected and player_rect.colliderect(collectible.get_rect()):
                collectible.collected = True
                if collectible.item_type == "health":
                    self.player.health = min(self.player.max_health, self.player.health + 25)
                elif collectible.item_type == "life":
                    self.player.lives += 1
                else:  # score
                    self.player.score += 50
                    
    def check_level_complete(self):
        # Check if all enemies are defeated
        alive_enemies = [e for e in self.enemies if e.alive]
        if not alive_enemies:
            if self.current_level < 3:
                self.current_level += 1
                self.load_level(self.current_level)
                self.player.x = 100
                self.camera_x = 0
            else:
                # Game won!
                self.game_state = "victory"
                
    def draw_hud(self):
        # Health bar
        pygame.draw.rect(self.screen, RED, (20, 20, 200, 20))
        health_ratio = self.player.health / self.player.max_health
        pygame.draw.rect(self.screen, GREEN, (20, 20, 200 * health_ratio, 20))
        
        # Lives
        font = pygame.font.Font(None, 36)
        lives_text = font.render(f"Lives: {self.player.lives}", True, WHITE)
        self.screen.blit(lives_text, (20, 50))
        
        # Score
        score_text = font.render(f"Score: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (20, 80))
        
        # Level
        level_text = font.render(f"Level: {self.current_level}", True, WHITE)
        self.screen.blit(level_text, (20, 110))
        
    def draw_background(self):
        if self.current_level == 1:
            # Forest background
            self.screen.fill(SKY_BLUE)
            # Trees
            for i in range(0, self.level_width, 100):
                x = i - (self.camera_x * 0.5) % 100
                if -50 < x < SCREEN_WIDTH + 50:
                    pygame.draw.rect(self.screen, BROWN, (x, GROUND_LEVEL - 150, 20, 150))
                    pygame.draw.circle(self.screen, DARK_GREEN, (x + 10, GROUND_LEVEL - 140), 30)
        elif self.current_level == 2:
            # Desert background
            self.screen.fill((255, 218, 185))
            # Cacti
            for i in range(0, self.level_width, 150):
                x = i - (self.camera_x * 0.3) % 150
                if -50 < x < SCREEN_WIDTH + 50:
                    pygame.draw.rect(self.screen, DARK_GREEN, (x, GROUND_LEVEL - 80, 15, 80))
                    pygame.draw.rect(self.screen, DARK_GREEN, (x - 10, GROUND_LEVEL - 60, 35, 10))
        else:
            # Boss level
            self.screen.fill((64, 64, 128))
            
        # Ground
        pygame.draw.rect(self.screen, BROWN, (0, GROUND_LEVEL, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_LEVEL))
        
    def run(self):
        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if self.game_state == "menu":
                            if event.key == pygame.K_RETURN:
                                self.game_state = "playing"
                                self.reset_game()
                        elif self.game_state == "playing":
                            if event.key == pygame.K_x or event.key == pygame.K_LCTRL:
                                projectile = self.player.shoot()
                                if projectile:
                                    self.projectiles.append(projectile)
                        elif self.game_state in ["game_over", "victory"]:
                            if event.key == pygame.K_RETURN:
                                self.reset_game()
                                self.game_state = "playing"
                            elif event.key == pygame.K_ESCAPE:
                                self.game_state = "menu"
                                
                if self.game_state == "menu":
                    self.screen.fill(BLACK)
                    font = pygame.font.Font(None, 72)
                    title = font.render("FOX ADVENTURE", True, ORANGE)
                    self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
                    
                    font = pygame.font.Font(None, 36)
                    instructions = [
                        "Arrow Keys / WASD to Move",
                        "Space / Up to Jump",
                        "X / Ctrl to Shoot",
                        "",
                        "Press ENTER to Start"
                    ]
                    for i, instruction in enumerate(instructions):
                        text = font.render(instruction, True, WHITE)
                        self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 350 + i * 40))
                        
                elif self.game_state == "playing":
                    keys = pygame.key.get_pressed()
                    
                    # Update
                    self.player.update(keys)
                    self.update_camera()
                    
                    # Update projectiles
                    for projectile in self.projectiles[:]:
                        projectile.update()
                        if projectile.x < 0 or projectile.x > self.level_width:
                            self.projectiles.remove(projectile)
                            
                    for projectile in self.enemy_projectiles[:]:
                        projectile.update()
                        if projectile.x < 0 or projectile.x > self.level_width:
                            self.enemy_projectiles.remove(projectile)
                    
                    # Update enemies
                    for enemy in self.enemies:
                        enemy_projectile = enemy.update(self.player)
                        if enemy_projectile:
                            self.enemy_projectiles.append(enemy_projectile)
                            
                    # Update collectibles
                    for collectible in self.collectibles:
                        collectible.update()
                    
                    # Handle collisions
                    self.handle_collisions()
                    
                    # Check level completion
                    self.check_level_complete()
                    
                    # Check game over
                    if self.player.lives <= 0:
                        self.game_state = "game_over"
                    
                    # Draw
                    self.draw_background()
                    
                    self.player.draw(self.screen, self.camera_x)
                    
                    for projectile in self.projectiles:
                        projectile.draw(self.screen, self.camera_x)
                        
                    for projectile in self.enemy_projectiles:
                        projectile.draw(self.screen, self.camera_x)
                    
                    for enemy in self.enemies:
                        enemy.draw(self.screen, self.camera_x)
                        
                    for collectible in self.collectibles:
                        collectible.draw(self.screen, self.camera_x)
                    
                    self.draw_hud()
                    
                elif self.game_state == "game_over":
                    self.screen.fill(BLACK)
                    font = pygame.font.Font(None, 72)
                    title = font.render("GAME OVER", True, RED)
                    self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 250))
                    
                    font = pygame.font.Font(None, 36)
                    score_text = font.render(f"Final Score: {self.player.score}", True, WHITE)
                    self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 350))
                    
                    restart_text = font.render("Press ENTER to Restart or ESC for Menu", True, WHITE)
                    self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 450))
                    
                elif self.game_state == "victory":
                    self.screen.fill(BLACK)
                    font = pygame.font.Font(None, 72)
                    title = font.render("VICTORY!", True, GREEN)
                    self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
                    
                    font = pygame.font.Font(None, 48)
                    congrats = font.render("You defeated all enemies!", True, WHITE)
                    self.screen.blit(congrats, (SCREEN_WIDTH//2 - congrats.get_width()//2, 300))
                    
                    font = pygame.font.Font(None, 36)
                    score_text = font.render(f"Final Score: {self.player.score}", True, WHITE)
                    self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 380))
                    
                    restart_text = font.render("Press ENTER to Play Again or ESC for Menu", True, WHITE)
                    self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 450))
                
                pygame.display.flip()
                self.clock.tick(FPS)
                
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Failed to start game: {e}")
        pygame.quit()
        sys.exit()