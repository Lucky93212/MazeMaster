#!/usr/bin/env python3
"""
MazeMaster - A retro-style maze game
Player (red square) must escape mazes while avoiding orange adversaries
"""

import pygame
import random
import math
import sys
from enum import Enum
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
CELL_SIZE = 20
MAZE_WIDTH = 35
MAZE_HEIGHT = 25

# Colors (retro palette)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    LEVEL_COMPLETE = 4

class Maze:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[1 for _ in range(width)] for _ in range(height)]
        self.generate_maze()
    
    def generate_maze(self):
        """Generate maze using recursive backtracking algorithm"""
        # Start with all walls
        self.grid = [[1 for _ in range(self.width)] for _ in range(self.height)]
        
        # Create paths
        stack = [(1, 1)]
        self.grid[1][1] = 0
        
        while stack:
            current_x, current_y = stack[-1]
            neighbors = []
            
            # Check all four directions
            for dx, dy in [(0, 2), (2, 0), (0, -2), (-2, 0)]:
                nx, ny = current_x + dx, current_y + dy
                if (0 < nx < self.width - 1 and 0 < ny < self.height - 1 and 
                    self.grid[ny][nx] == 1):
                    neighbors.append((nx, ny))
            
            if neighbors:
                # Choose random neighbor
                next_x, next_y = random.choice(neighbors)
                # Remove wall between current and next
                wall_x = current_x + (next_x - current_x) // 2
                wall_y = current_y + (next_y - current_y) // 2
                self.grid[wall_y][wall_x] = 0
                self.grid[next_y][next_x] = 0
                stack.append((next_x, next_y))
            else:
                stack.pop()
        
        # Ensure exit is accessible
        self.grid[self.height - 2][self.width - 2] = 0
        self.grid[self.height - 2][self.width - 3] = 0
    
    def is_wall(self, x: int, y: int) -> bool:
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        return self.grid[y][x] == 1
    
    def is_valid_position(self, x: int, y: int) -> bool:
        return not self.is_wall(x, y)

class Player:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.gun_direction = Direction.RIGHT  # Gun orientation separate from movement
        self.shoot_cooldown = 0
        self.move_cooldown = 0  # Add movement cooldown for smooth continuous movement
        self.move_speed = 6  # Frames between moves (lower = faster)
    
    def move_to_nearest_tunnel(self, direction: Direction, maze: Maze) -> bool:
        """Move to the immediate next tunnel in the given direction (no wall jumping)"""
        dx, dy = direction.value
        
        # Check the immediate next position in the chosen direction
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Only move if the immediate next position is valid (no wall jumping)
        if maze.is_valid_position(new_x, new_y):
            self.x, self.y = new_x, new_y
            return True
        
        # If blocked by wall, don't move
        return False
    
    def can_move(self) -> bool:
        """Check if player can move (cooldown expired)"""
        return self.move_cooldown <= 0
    
    def rotate_gun(self, direction: Direction):
        """Rotate gun left or right"""
        self.gun_direction = direction
    
    def shoot(self) -> 'Laser':
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = 15  # Reduced cooldown for better gameplay
            dx, dy = self.gun_direction.value
            return Laser(self.x, self.y, dx, dy)
        return None
    
    def update(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.move_cooldown > 0:
            self.move_cooldown -= 1

class Adversary:
    def __init__(self, x: int, y: int, speed: float = 1.0):
        self.x = x
        self.y = y
        self.speed = speed
        self.move_timer = 0
        self.path = []
    
    def update(self, player: Player, maze: Maze):
        self.move_timer += 1
        move_interval = max(1, int(60 / self.speed))  # Adjust speed
        
        if self.move_timer >= move_interval:
            self.move_timer = 0
            self.move_towards_player(player, maze)
    
    def move_towards_player(self, player: Player, maze: Maze):
        """Simple AI to move towards player"""
        dx = player.x - self.x
        dy = player.y - self.y
        
        # Prioritize movement direction
        moves = []
        if abs(dx) > abs(dy):
            if dx > 0:
                moves.append((1, 0))
            else:
                moves.append((-1, 0))
            if dy > 0:
                moves.append((0, 1))
            else:
                moves.append((0, -1))
        else:
            if dy > 0:
                moves.append((0, 1))
            else:
                moves.append((0, -1))
            if dx > 0:
                moves.append((1, 0))
            else:
                moves.append((-1, 0))
        
        # Try moves in order of preference
        for move_dx, move_dy in moves:
            new_x, new_y = self.x + move_dx, self.y + move_dy
            if maze.is_valid_position(new_x, new_y):
                self.x, self.y = new_x, new_y
                break

class Laser:
    def __init__(self, x: int, y: int, dx: int, dy: int):
        self.x = float(x)
        self.y = float(y)
        self.dx = dx * 0.5  # Laser speed
        self.dy = dy * 0.5
        self.active = True
        self.trail = []  # For visual trail effect
        self.max_trail_length = 8
    
    def update(self, maze: Maze):
        if not self.active:
            return
        
        # Add current position to trail
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)
        
        # Move laser
        self.x += self.dx
        self.y += self.dy
        
        # Check if laser hits wall
        if maze.is_wall(int(self.x), int(self.y)):
            self.active = False

class Explosion:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.timer = 20  # Animation duration
        self.max_timer = 20
    
    def update(self):
        self.timer -= 1
        return self.timer > 0
    
    def get_radius(self):
        # Explosion grows then shrinks
        progress = 1 - (self.timer / self.max_timer)
        if progress < 0.5:
            return int(progress * 2 * CELL_SIZE)
        else:
            return int((2 - progress * 2) * CELL_SIZE)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("MazeMaster")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.state = GameState.MENU
        self.level = 1
        self.score = 0
        
        self.reset_level()
    
    def reset_level(self):
        """Initialize/reset level"""
        self.maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)
        
        # Place player in center
        center_x, center_y = MAZE_WIDTH // 2, MAZE_HEIGHT // 2
        # Find nearest valid position to center
        for radius in range(min(MAZE_WIDTH, MAZE_HEIGHT) // 2):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x, y = center_x + dx, center_y + dy
                    if self.maze.is_valid_position(x, y):
                        self.player = Player(x, y)
                        break
                else:
                    continue
                break
            else:
                continue
            break
        
        # Create adversaries (starting from level 2)
        self.adversaries = []
        if self.level > 1:
            num_adversaries = min(self.level - 1, 5)  # Max 5 adversaries
            adversary_speed = 0.5 + (self.level - 2) * 0.2  # Increase speed each level
            
            for _ in range(num_adversaries):
                # Place adversaries in random valid positions
                attempts = 0
                while attempts < 100:
                    x = random.randint(1, MAZE_WIDTH - 2)
                    y = random.randint(1, MAZE_HEIGHT - 2)
                    if (self.maze.is_valid_position(x, y) and 
                        abs(x - self.player.x) + abs(y - self.player.y) > 5):
                        self.adversaries.append(Adversary(x, y, adversary_speed))
                        break
                    attempts += 1
        
        self.lasers = []
        self.explosions = []
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        if self.state == GameState.PLAYING:
            # Player movement (continuous when holding keys)
            if self.player.can_move():
                moved = False
                if keys[pygame.K_UP]:
                    moved = self.player.move_to_nearest_tunnel(Direction.UP, self.maze)
                elif keys[pygame.K_DOWN]:
                    moved = self.player.move_to_nearest_tunnel(Direction.DOWN, self.maze)
                elif keys[pygame.K_LEFT]:
                    moved = self.player.move_to_nearest_tunnel(Direction.LEFT, self.maze)
                elif keys[pygame.K_RIGHT]:
                    moved = self.player.move_to_nearest_tunnel(Direction.RIGHT, self.maze)
                
                # Reset movement cooldown if player moved
                if moved:
                    self.player.move_cooldown = self.player.move_speed
            
            # Gun rotation (continuous)
            if keys[pygame.K_a]:
                self.player.rotate_gun(Direction.LEFT)
            elif keys[pygame.K_d]:
                self.player.rotate_gun(Direction.RIGHT)
            elif keys[pygame.K_w]:
                self.player.rotate_gun(Direction.UP)
            elif keys[pygame.K_s]:
                self.player.rotate_gun(Direction.DOWN)
            
            # Shooting (continuous)
            if keys[pygame.K_SPACE]:
                laser = self.player.shoot()
                if laser:
                    self.lasers.append(laser)
    
    def handle_key_press(self, key):
        """Handle single key press events (not used for movement anymore)"""
        pass
    
    def update(self):
        if self.state == GameState.PLAYING:
            self.player.update()
            
            # Update adversaries
            for adversary in self.adversaries:
                adversary.update(self.player, self.maze)
            
            # Update lasers
            for laser in self.lasers[:]:
                laser.update(self.maze)
                if not laser.active:
                    self.lasers.remove(laser)
            
            # Update explosions
            for explosion in self.explosions[:]:
                if not explosion.update():
                    self.explosions.remove(explosion)
            
            # Check laser-adversary collisions
            for laser in self.lasers[:]:
                for adversary in self.adversaries[:]:
                    if (abs(laser.x - adversary.x) < 1 and 
                        abs(laser.y - adversary.y) < 1):
                        self.lasers.remove(laser)
                        self.adversaries.remove(adversary)
                        self.explosions.append(Explosion(adversary.x, adversary.y))
                        self.score += 100
                        
                        # Spawn new adversary
                        if self.level > 1:
                            self.spawn_new_adversary()
                        break
            
            # Check player-adversary collisions
            for adversary in self.adversaries:
                if abs(self.player.x - adversary.x) + abs(self.player.y - adversary.y) <= 1:
                    self.state = GameState.GAME_OVER
            
            # Check if player reached exit
            if (self.player.x >= MAZE_WIDTH - 2 and 
                self.player.y >= MAZE_HEIGHT - 2):
                self.state = GameState.LEVEL_COMPLETE
                self.score += 1000 * self.level
    
    def spawn_new_adversary(self):
        """Spawn a new adversary at maze entrance"""
        adversary_speed = 0.5 + (self.level - 2) * 0.2
        # Try to spawn near entrance
        for _ in range(50):
            x = random.randint(1, 5)
            y = random.randint(1, 5)
            if (self.maze.is_valid_position(x, y) and 
                abs(x - self.player.x) + abs(y - self.player.y) > 3):
                self.adversaries.append(Adversary(x, y, adversary_speed))
                break
    
    def draw(self):
        self.screen.fill(BLACK)
        
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        elif self.state == GameState.LEVEL_COMPLETE:
            self.draw_level_complete()
        
        pygame.display.flip()
    
    def draw_menu(self):
        title = self.font.render("MAZEMASTER", True, WHITE)
        subtitle = self.small_font.render("Press SPACE to Start", True, GRAY)
        instructions = [
            "Arrow Keys: Hold to move continuously",
            "WASD Keys: Rotate gun (W=up, S=down, A=left, D=right)",
            "SPACE: Shoot laser",
            "Escape mazes, avoid orange enemies!",
            "Shoot enemies to clear your path!"
        ]
        
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 200))
        self.screen.blit(subtitle, (WINDOW_WIDTH // 2 - subtitle.get_width() // 2, 250))
        
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, WHITE)
            self.screen.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, 320 + i * 30))
    
    def draw_game(self):
        # Calculate maze offset to center it
        maze_pixel_width = self.maze.width * CELL_SIZE
        maze_pixel_height = self.maze.height * CELL_SIZE
        offset_x = (WINDOW_WIDTH - maze_pixel_width) // 2
        offset_y = 50  # Leave space for UI
        
        # Draw maze
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                rect = pygame.Rect(
                    offset_x + x * CELL_SIZE,
                    offset_y + y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                
                if self.maze.is_wall(x, y):
                    pygame.draw.rect(self.screen, WHITE, rect)
                else:
                    pygame.draw.rect(self.screen, DARK_GRAY, rect)
        
        # Draw exit
        exit_rect = pygame.Rect(
            offset_x + (MAZE_WIDTH - 2) * CELL_SIZE,
            offset_y + (MAZE_HEIGHT - 2) * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
        pygame.draw.rect(self.screen, GREEN, exit_rect)
        
        # Draw player with gun
        player_rect = pygame.Rect(
            offset_x + self.player.x * CELL_SIZE + 2,
            offset_y + self.player.y * CELL_SIZE + 2,
            CELL_SIZE - 4,
            CELL_SIZE - 4
        )
        pygame.draw.rect(self.screen, RED, player_rect)
        
        # Draw gun barrel
        gun_dx, gun_dy = self.player.gun_direction.value
        gun_start_x = offset_x + self.player.x * CELL_SIZE + CELL_SIZE // 2
        gun_start_y = offset_y + self.player.y * CELL_SIZE + CELL_SIZE // 2
        gun_end_x = gun_start_x + gun_dx * (CELL_SIZE // 2 + 4)
        gun_end_y = gun_start_y + gun_dy * (CELL_SIZE // 2 + 4)
        
        pygame.draw.line(self.screen, WHITE, 
                        (gun_start_x, gun_start_y), 
                        (gun_end_x, gun_end_y), 3)
        
        # Draw adversaries
        for adversary in self.adversaries:
            adv_rect = pygame.Rect(
                offset_x + adversary.x * CELL_SIZE + 2,
                offset_y + adversary.y * CELL_SIZE + 2,
                CELL_SIZE - 4,
                CELL_SIZE - 4
            )
            pygame.draw.rect(self.screen, ORANGE, adv_rect)
        
        # Draw lasers with trail effect
        for laser in self.lasers:
            # Draw trail
            for i, (trail_x, trail_y) in enumerate(laser.trail):
                alpha = int(255 * (i + 1) / len(laser.trail))
                trail_color = (*YELLOW[:3], alpha) if len(YELLOW) == 4 else YELLOW
                trail_rect = pygame.Rect(
                    offset_x + trail_x * CELL_SIZE + CELL_SIZE // 2 - 1,
                    offset_y + trail_y * CELL_SIZE + CELL_SIZE // 2 - 1,
                    2,
                    2
                )
                pygame.draw.rect(self.screen, trail_color, trail_rect)
            
            # Draw main laser
            laser_rect = pygame.Rect(
                offset_x + int(laser.x) * CELL_SIZE + CELL_SIZE // 2 - 2,
                offset_y + int(laser.y) * CELL_SIZE + CELL_SIZE // 2 - 2,
                4,
                4
            )
            pygame.draw.rect(self.screen, YELLOW, laser_rect)
        
        # Draw explosions
        for explosion in self.explosions:
            explosion_center_x = offset_x + explosion.x * CELL_SIZE + CELL_SIZE // 2
            explosion_center_y = offset_y + explosion.y * CELL_SIZE + CELL_SIZE // 2
            radius = explosion.get_radius()
            
            if radius > 0:
                # Draw multiple circles for explosion effect
                colors = [YELLOW, ORANGE, RED]
                for i, color in enumerate(colors):
                    exp_radius = max(1, radius - i * 2)
                    if exp_radius > 0:
                        pygame.draw.circle(self.screen, color, 
                                         (explosion_center_x, explosion_center_y), 
                                         exp_radius)
        
        # Draw UI
        level_text = self.small_font.render(f"Level: {self.level}", True, WHITE)
        score_text = self.small_font.render(f"Score: {self.score}", True, WHITE)
        enemies_text = self.small_font.render(f"Enemies: {len(self.adversaries)}", True, WHITE)
        ammo_text = self.small_font.render(f"Gun: {'Ready' if self.player.shoot_cooldown == 0 else 'Reloading'}", True, WHITE)
        
        self.screen.blit(level_text, (10, 10))
        self.screen.blit(score_text, (10, 30))
        self.screen.blit(enemies_text, (WINDOW_WIDTH - 120, 10))
        self.screen.blit(ammo_text, (WINDOW_WIDTH - 120, 30))
    
    def draw_game_over(self):
        self.draw_game()  # Draw game state behind
        
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("GAME OVER", True, RED)
        score_text = self.small_font.render(f"Final Score: {self.score}", True, WHITE)
        restart_text = self.small_font.render("Press R to Restart or ESC to Menu", True, GRAY)
        
        self.screen.blit(game_over_text, (WINDOW_WIDTH // 2 - game_over_text.get_width() // 2, 250))
        self.screen.blit(score_text, (WINDOW_WIDTH // 2 - score_text.get_width() // 2, 300))
        self.screen.blit(restart_text, (WINDOW_WIDTH // 2 - restart_text.get_width() // 2, 350))
    
    def draw_level_complete(self):
        self.draw_game()  # Draw game state behind
        
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        complete_text = self.font.render("LEVEL COMPLETE!", True, GREEN)
        score_text = self.small_font.render(f"Score: {self.score}", True, WHITE)
        next_text = self.small_font.render("Press SPACE for Next Level", True, GRAY)
        
        self.screen.blit(complete_text, (WINDOW_WIDTH // 2 - complete_text.get_width() // 2, 250))
        self.screen.blit(score_text, (WINDOW_WIDTH // 2 - score_text.get_width() // 2, 300))
        self.screen.blit(next_text, (WINDOW_WIDTH // 2 - next_text.get_width() // 2, 350))
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if self.state == GameState.MENU:
                        if event.key == pygame.K_SPACE:
                            self.state = GameState.PLAYING
                    
                    elif self.state == GameState.GAME_OVER:
                        if event.key == pygame.K_r:
                            self.level = 1
                            self.score = 0
                            self.reset_level()
                            self.state = GameState.PLAYING
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.MENU
                    
                    elif self.state == GameState.LEVEL_COMPLETE:
                        if event.key == pygame.K_SPACE:
                            self.level += 1
                            self.reset_level()
                            self.state = GameState.PLAYING
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.MENU
                    
                    # Handle movement key presses (no longer needed)
                    # self.handle_key_press(event.key)
            
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
