import pygame
import math
import random
import json
import os
import sys
import traceback

# Initialize Pygame with error handling
try:
    pygame.init()
    if not pygame.get_init():
        raise RuntimeError("Pygame failed to initialize")
except Exception as e:
    print(f"Error initializing Pygame: {e}")
    sys.exit(1)

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

class Camera:
    """Dynamic camera that follows the player smoothly"""
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.target_x = 0
        self.smoothness = 0.1
    
    def update(self, target):
        # Calculate target camera position
        self.target_x = target.rect.centerx - SCREEN_WIDTH // 2
        
        # Smooth camera movement
        current_x = self.camera.x
        diff = self.target_x - current_x
        self.camera.x += diff * self.smoothness
        
        # Keep camera within bounds
        self.camera.x = max(0, self.camera.x)
    
    def apply(self, entity):
        """Apply camera offset to entity"""
        return entity.rect.move(-self.camera.x, 0)

class Projectile:
    """Projectile class for bullets and missiles"""
    def __init__(self, x, y, direction, speed=8, damage=1, owner="player"):
        self.rect = pygame.Rect(x, y, 8, 4)
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.owner = owner
        self.color = YELLOW if owner == "player" else RED
    
    def update(self):
        """Update projectile position"""
        self.rect.x += self.direction * self.speed
        
        # Remove if off screen
        if self.rect.x < -50 or self.rect.x > SCREEN_WIDTH + 1000:
            return False
        return True
    
    def draw(self, screen, camera):
        """Draw projectile"""
        draw_rect = camera.apply(self)
        pygame.draw.rect(screen, self.color, draw_rect)
        # Add glow effect
        pygame.draw.rect(screen, WHITE, draw_rect, 1)

class Enemy:
    """Enemy tank class"""
    def __init__(self, x, y, enemy_type="basic"):
        self.rect = pygame.Rect(x, y, 60, 40)
        self.enemy_type = enemy_type
        self.speed = 1 if enemy_type == "basic" else 0.5
        self.direction = -1  # Moving left
        self.last_shot = 0
        self.shoot_delay = 2000 if enemy_type == "basic" else 1500  # milliseconds
        
        # Health based on type
        if enemy_type == "basic":
            self.max_health = 2
            self.color = RED
        elif enemy_type == "heavy":
            self.max_health = 4
            self.color = (150, 0, 0)
        else:  # boss
            self.max_health = 10
            self.color = (100, 0, 0)
            self.rect.width = 100
            self.rect.height = 60
        
        self.health = self.max_health
        self.alive = True
    
    def update(self, player_pos, current_time):
        """Update enemy behavior"""
        if not self.alive:
            return []
        
        # Move towards player or patrol
        if self.enemy_type == "boss":
            # Boss stays in place but shoots more
            pass
        else:
            self.rect.x += self.direction * self.speed
            
            # Change direction occasionally
            if random.randint(1, 200) == 1:
                self.direction *= -1
        
        # Shooting logic
        projectiles = []
        if current_time - self.last_shot > self.shoot_delay:
            if abs(self.rect.x - player_pos[0]) < 400:  # In range
                self.last_shot = current_time
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery, 
                    self.direction, 5, 1, "enemy"
                ))
        
        return projectiles
    
    def take_damage(self, damage):
        """Take damage and check if destroyed"""
        self.health -= damage
        if self.health <= 0:
            self.alive = False
            return True
        return False
    
    def draw(self, screen, camera):
        """Draw enemy tank"""
        if not self.alive:
            return
        
        draw_rect = camera.apply(self)
        
        # Tank body
        pygame.draw.rect(screen, self.color, draw_rect)
        pygame.draw.rect(screen, BLACK, draw_rect, 2)
        
        # Tank barrel
        barrel_rect = pygame.Rect(draw_rect.right - 5, draw_rect.centery - 3, 15, 6)
        pygame.draw.rect(screen, GRAY, barrel_rect)
        
        # Health bar
        health_width = 40
        health_height = 4
        health_x = draw_rect.x + (draw_rect.width - health_width) // 2
        health_y = draw_rect.y - 10
        
        # Health background
        pygame.draw.rect(screen, RED, (health_x, health_y, health_width, health_height))
        
        # Health foreground
        health_ratio = self.health / self.max_health
        pygame.draw.rect(screen, GREEN, (health_x, health_y, health_width * health_ratio, health_height))

class Collectible:
    """Collectible items class"""
    def __init__(self, x, y, collectible_type="health"):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.collectible_type = collectible_type
        self.collected = False
        self.bob_offset = 0
        self.bob_speed = 0.2
        
        # Different types of collectibles
        if collectible_type == "health":
            self.color = GREEN
            self.value = 1
        elif collectible_type == "extra_life":
            self.color = BLUE
            self.value = 1
        else:  # score
            self.color = YELLOW
            self.value = 100
    
    def update(self):
        """Update collectible (bobbing animation)"""
        self.bob_offset += self.bob_speed
        if self.bob_offset > 6.28:  # 2 * pi
            self.bob_offset = 0
    
    def draw(self, screen, camera):
        """Draw collectible"""
        if self.collected:
            return
        
        draw_rect = camera.apply(self)
        bob_y = draw_rect.y + math.sin(self.bob_offset) * 3
        
        if self.collectible_type == "health":
            # Draw cross
            pygame.draw.rect(screen, self.color, (draw_rect.x + 7, draw_rect.y + 2, 6, 16))
            pygame.draw.rect(screen, self.color, (draw_rect.x + 2, draw_rect.y + 7, 16, 6))
        elif self.collectible_type == "extra_life":
            # Draw diamond
            points = [
                (draw_rect.centerx, draw_rect.y),
                (draw_rect.right, draw_rect.centery),
                (draw_rect.centerx, draw_rect.bottom),
                (draw_rect.x, draw_rect.centery)
            ]
            pygame.draw.polygon(screen, self.color, points)
        else:  # score
            # Draw star
            pygame.draw.circle(screen, self.color, (draw_rect.centerx, int(bob_y + 10)), 8)

class Player:
    """Player tank class"""
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 50, 35)
        self.speed = 5
        self.jump_speed = 15
        self.gravity = 0.8
        self.y_velocity = 0
        self.on_ground = False
        self.max_health = 5
        self.health = self.max_health
        self.lives = 3
        self.last_shot = 0
        self.shoot_delay = 200  # milliseconds
        self.alive = True
        self.ground_y = SCREEN_HEIGHT - 100  # Ground level
    
    def update(self, keys, current_time):
        """Update player movement and actions"""
        if not self.alive:
            return []
        
        # Horizontal movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        
        # Jumping
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.y_velocity = -self.jump_speed
            self.on_ground = False
        
        # Apply gravity
        self.y_velocity += self.gravity
        self.rect.y += self.y_velocity
        
        # Ground collision
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.y_velocity = 0
            self.on_ground = True
        
        # Keep player on screen (left boundary)
        if self.rect.x < 0:
            self.rect.x = 0
        
        # Shooting
        projectiles = []
        if (keys[pygame.K_x] or keys[pygame.K_LCTRL]) and current_time - self.last_shot > self.shoot_delay:
            self.last_shot = current_time
            projectiles.append(Projectile(
                self.rect.right, self.rect.centery, 
                1, 10, 1, "player"
            ))
        
        return projectiles
    
    def take_damage(self, damage):
        """Take damage and handle death"""
        self.health -= damage
        if self.health <= 0:
            self.lives -= 1
            if self.lives > 0:
                self.health = self.max_health
                return False  # Respawn
            else:
                self.alive = False
                return True  # Game over
        return False
    
    def heal(self, amount):
        """Heal player"""
        self.health = min(self.max_health, self.health + amount)
    
    def add_life(self):
        """Add extra life"""
        self.lives += 1
    
    def draw(self, screen, camera):
        """Draw player tank"""
        if not self.alive:
            return
        
        draw_rect = camera.apply(self)
        
        # Tank body
        pygame.draw.rect(screen, DARK_GREEN, draw_rect)
        pygame.draw.rect(screen, BLACK, draw_rect, 2)
        
        # Tank barrel
        barrel_rect = pygame.Rect(draw_rect.right, draw_rect.centery - 2, 20, 4)
        pygame.draw.rect(screen, GRAY, barrel_rect)
        
        # Tank tracks
        track_rect = pygame.Rect(draw_rect.x, draw_rect.bottom - 8, draw_rect.width, 8)
        pygame.draw.rect(screen, BLACK, track_rect)

class Level:
    """Level class to manage level-specific data"""
    def __init__(self, level_num):
        self.level_num = level_num
        self.enemies = []
        self.collectibles = []
        self.background_color = BLACK
        self.completed = False
        self.boss_spawned = False
        
        self.generate_level()
    
    def generate_level(self):
        """Generate level content"""
        if self.level_num == 1:
            # Level 1: Basic enemies
            for i in range(5):
                x = 800 + i * 300
                y = SCREEN_HEIGHT - 140
                self.enemies.append(Enemy(x, y, "basic"))
            
            # Add collectibles
            for i in range(3):
                x = 600 + i * 400
                y = SCREEN_HEIGHT - 150
                ctype = ["health", "score", "extra_life"][i % 3]
                self.collectibles.append(Collectible(x, y, ctype))
        
        elif self.level_num == 2:
            # Level 2: Mix of basic and heavy enemies
            for i in range(3):
                x = 800 + i * 400
                y = SCREEN_HEIGHT - 140
                self.enemies.append(Enemy(x, y, "basic"))
            
            for i in range(2):
                x = 1000 + i * 500
                y = SCREEN_HEIGHT - 140
                self.enemies.append(Enemy(x, y, "heavy"))
            
            for i in range(4):
                x = 700 + i * 300
                y = SCREEN_HEIGHT - 150
                ctype = ["health", "score", "extra_life"][i % 3]
                self.collectibles.append(Collectible(x, y, ctype))
        
        elif self.level_num == 3:
            # Level 3: Final level with boss
            for i in range(4):
                x = 800 + i * 350
                y = SCREEN_HEIGHT - 140
                etype = "heavy" if i % 2 == 0 else "basic"
                self.enemies.append(Enemy(x, y, etype))
            
            # Boss at the end
            boss_x = 2000
            boss_y = SCREEN_HEIGHT - 160
            self.enemies.append(Enemy(boss_x, boss_y, "boss"))
            
            for i in range(5):
                x = 600 + i * 350
                y = SCREEN_HEIGHT - 150
                ctype = ["health", "score", "extra_life"][i % 3]
                self.collectibles.append(Collectible(x, y, ctype))

class Game:
    """Main game class"""
    def __init__(self):
        try:
            # Initialize display
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            if not self.screen:
                raise RuntimeError("Failed to create display surface")
            
            pygame.display.set_caption("Tank Battle - Side Scrolling")
            self.clock = pygame.time.Clock()
            self.running = True
            
            # Game state
            self.state = "menu"  # menu, playing, game_over, level_complete
            self.current_level = 1
            self.score = 0
            self.high_score = self.load_high_score()
            
            # Game objects
            self.player = None
            self.level = None
            self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
            self.projectiles = []
            
            # Initialize fonts with error handling
            try:
                self.font_large = pygame.font.Font(None, 48)
                self.font_medium = pygame.font.Font(None, 32)
                self.font_small = pygame.font.Font(None, 24)
            except Exception as e:
                print(f"Warning: Could not load fonts, using default: {e}")
                # Fallback to system default
                self.font_large = pygame.font.SysFont("arial", 48)
                self.font_medium = pygame.font.SysFont("arial", 32)
                self.font_small = pygame.font.SysFont("arial", 24)
            
            self.reset_game()
            
        except Exception as e:
            print(f"Error initializing game: {e}")
            traceback.print_exc()
            sys.exit(1)
    
    def load_high_score(self):
        """Load high score from file"""
        try:
            if os.path.exists("high_score.txt"):
                with open("high_score.txt", "r") as f:
                    content = f.read().strip()
                    if content:
                        score = int(content)
                        if score < 0:
                            raise ValueError("Invalid negative score")
                        return score
                    else:
                        return 0
        except (ValueError, IOError, OSError) as e:
            print(f"Warning: Could not load high score: {e}")
        except Exception as e:
            print(f"Unexpected error loading high score: {e}")
        return 0
    
    def save_high_score(self):
        """Save high score to file"""
        try:
            with open("high_score.txt", "w") as f:
                f.write(str(self.high_score))
        except (IOError, OSError) as e:
            print(f"Warning: Could not save high score: {e}")
        except Exception as e:
            print(f"Unexpected error saving high score: {e}")
    
    def reset_game(self):
        """Reset game to initial state"""
        try:
            self.current_level = 1
            self.score = 0
            self.player = Player(100, SCREEN_HEIGHT - 135)
            self.level = Level(self.current_level)
            self.projectiles = []
            self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        except Exception as e:
            print(f"Error resetting game: {e}")
            traceback.print_exc()
    
    def handle_events(self):
        """Handle pygame events"""
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    if self.state == "menu":
                        if event.key == pygame.K_RETURN:
                            self.state = "playing"
                            self.reset_game()
                        elif event.key == pygame.K_ESCAPE:
                            self.running = False
                    
                    elif self.state == "game_over":
                        if event.key == pygame.K_RETURN:
                            self.state = "menu"
                        elif event.key == pygame.K_r:
                            self.state = "playing"
                            self.reset_game()
                    
                    elif self.state == "level_complete":
                        if event.key == pygame.K_RETURN:
                            self.next_level()
        except Exception as e:
            print(f"Error handling events: {e}")
            # Continue running to avoid crash
    
    def next_level(self):
        """Advance to next level"""
        self.current_level += 1
        if self.current_level > 3:
            # Game completed
            self.state = "game_over"
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
        else:
            self.level = Level(self.current_level)
            self.projectiles = []
            self.player.rect.x = 100  # Reset player position
            self.state = "playing"
    
    def update_game(self):
        """Update game logic"""
        if self.state != "playing":
            return
        
        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        
        # Update player
        new_projectiles = self.player.update(keys, current_time)
        self.projectiles.extend(new_projectiles)
        
        # Update camera
        self.camera.update(self.player)
        
        # Update enemies
        for enemy in self.level.enemies:
            if enemy.alive:
                new_projectiles = enemy.update((self.player.rect.x, self.player.rect.y), current_time)
                self.projectiles.extend(new_projectiles)
        
        # Update collectibles
        for collectible in self.level.collectibles:
            collectible.update()
        
        # Update projectiles
        self.projectiles = [p for p in self.projectiles if p.update()]
        
        # Collision detection
        self.check_collisions()
        
        # Check level completion
        if all(not enemy.alive for enemy in self.level.enemies):
            self.state = "level_complete"
        
        # Check game over
        if not self.player.alive:
            self.state = "game_over"
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
    
    def check_collisions(self):
        """Check all collisions"""
        # Projectile vs Enemy collisions
        for projectile in self.projectiles[:]:
            if projectile.owner == "player":
                for enemy in self.level.enemies:
                    if enemy.alive and projectile.rect.colliderect(enemy.rect):
                        if enemy.take_damage(projectile.damage):
                            # Enemy destroyed
                            score_bonus = 50 if enemy.enemy_type == "basic" else 100
                            if enemy.enemy_type == "boss":
                                score_bonus = 500
                            self.score += score_bonus
                        self.projectiles.remove(projectile)
                        break
        
        # Projectile vs Player collisions
        for projectile in self.projectiles[:]:
            if projectile.owner == "enemy" and projectile.rect.colliderect(self.player.rect):
                self.player.take_damage(projectile.damage)
                self.projectiles.remove(projectile)
        
        # Player vs Collectible collisions
        for collectible in self.level.collectibles:
            if not collectible.collected and collectible.rect.colliderect(self.player.rect):
                collectible.collected = True
                if collectible.collectible_type == "health":
                    self.player.heal(collectible.value)
                elif collectible.collectible_type == "extra_life":
                    self.player.add_life()
                else:  # score
                    self.score += collectible.value
    
    def draw_menu(self):
        """Draw main menu"""
        self.screen.fill(BLACK)
        
        title = self.font_large.render("TANK BATTLE", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 200))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render("Side-Scrolling Tank Combat", True, GRAY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 250))
        self.screen.blit(subtitle, subtitle_rect)
        
        start_text = self.font_medium.render("Press ENTER to Start", True, WHITE)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, 350))
        self.screen.blit(start_text, start_rect)
        
        controls_text = [
            "Controls:",
            "Arrow Keys / WASD - Move",
            "SPACE - Jump",
            "X / CTRL - Shoot",
            "ESC - Quit"
        ]
        
        y_offset = 450
        for line in controls_text:
            text = self.font_small.render(line, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 30
        
        high_score_text = self.font_medium.render(f"High Score: {self.high_score}", True, YELLOW)
        high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH//2, 700))
        self.screen.blit(high_score_text, high_score_rect)
    
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill(BLACK)
        
        game_over_text = self.font_large.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, 250))
        self.screen.blit(game_over_text, game_over_rect)
        
        score_text = self.font_medium.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, 320))
        self.screen.blit(score_text, score_rect)
        
        if self.score == self.high_score:
            new_high_text = self.font_medium.render("NEW HIGH SCORE!", True, YELLOW)
            new_high_rect = new_high_text.get_rect(center=(SCREEN_WIDTH//2, 360))
            self.screen.blit(new_high_text, new_high_rect)
        
        restart_text = self.font_medium.render("Press R to Restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, 450))
        self.screen.blit(restart_text, restart_rect)
        
        menu_text = self.font_medium.render("Press ENTER for Main Menu", True, WHITE)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH//2, 490))
        self.screen.blit(menu_text, menu_rect)
    
    def draw_level_complete(self):
        """Draw level complete screen"""
        self.screen.fill(BLACK)
        
        if self.current_level >= 3:
            title = "CONGRATULATIONS!"
            subtitle = "You completed all levels!"
        else:
            title = f"LEVEL {self.current_level} COMPLETE!"
            subtitle = f"Preparing Level {self.current_level + 1}..."
        
        title_text = self.font_large.render(title, True, GREEN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 300))
        self.screen.blit(title_text, title_rect)
        
        subtitle_text = self.font_medium.render(subtitle, True, WHITE)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH//2, 350))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, 400))
        self.screen.blit(score_text, score_rect)
        
        continue_text = self.font_medium.render("Press ENTER to Continue", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH//2, 500))
        self.screen.blit(continue_text, continue_rect)
    
    def draw_game(self):
        """Draw game screen"""
        self.screen.fill((50, 50, 100))  # Sky color
        
        # Draw ground
        ground_rect = pygame.Rect(0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100)
        pygame.draw.rect(self.screen, BROWN, ground_rect)
        
        # Draw game objects
        self.player.draw(self.screen, self.camera)
        
        for enemy in self.level.enemies:
            enemy.draw(self.screen, self.camera)
        
        for collectible in self.level.collectibles:
            collectible.draw(self.screen, self.camera)
        
        for projectile in self.projectiles:
            projectile.draw(self.screen, self.camera)
        
        # Draw UI
        self.draw_ui()
    
    def draw_ui(self):
        """Draw user interface"""
        # Health bar
        health_width = 200
        health_height = 20
        health_x = 20
        health_y = 20
        
        # Health background
        pygame.draw.rect(self.screen, RED, (health_x, health_y, health_width, health_height))
        
        # Health foreground
        if self.player.alive:
            health_ratio = self.player.health / self.player.max_health
            pygame.draw.rect(self.screen, GREEN, (health_x, health_y, health_width * health_ratio, health_height))
        
        # Health text
        health_text = self.font_small.render(f"Health: {self.player.health}/{self.player.max_health}", True, WHITE)
        self.screen.blit(health_text, (health_x, health_y + 25))
        
        # Lives
        lives_text = self.font_small.render(f"Lives: {self.player.lives}", True, WHITE)
        self.screen.blit(lives_text, (health_x, health_y + 50))
        
        # Score
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH - 200, 20))
        
        # Level
        level_text = self.font_medium.render(f"Level: {self.current_level}", True, WHITE)
        self.screen.blit(level_text, (SCREEN_WIDTH - 200, 50))
        
        # Enemies remaining
        enemies_alive = sum(1 for enemy in self.level.enemies if enemy.alive)
        enemies_text = self.font_small.render(f"Enemies: {enemies_alive}", True, WHITE)
        self.screen.blit(enemies_text, (SCREEN_WIDTH - 200, 80))
    
    def run(self):
        """Main game loop"""
        try:
            while self.running:
                try:
                    self.handle_events()
                    self.update_game()
                    
                    # Draw based on current state
                    if self.state == "menu":
                        self.draw_menu()
                    elif self.state == "playing":
                        self.draw_game()
                    elif self.state == "game_over":
                        self.draw_game_over()
                    elif self.state == "level_complete":
                        self.draw_level_complete()
                    
                    pygame.display.flip()
                    self.clock.tick(FPS)
                    
                except Exception as e:
                    print(f"Error in game loop iteration: {e}")
                    # Try to continue running
                    continue
        
        except KeyboardInterrupt:
            print("Game interrupted by user")
        except Exception as e:
            print(f"Critical error in main game loop: {e}")
            traceback.print_exc()
        finally:
            try:
                pygame.quit()
            except Exception as e:
                print(f"Error during cleanup: {e}")

def main():
    """Main function to start the game"""
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Critical error starting game: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()