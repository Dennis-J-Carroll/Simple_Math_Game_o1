import pygame
import random
import sys
import math
import json
from pathlib import Path
from typing import List, Tuple

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Combine and organize constants
GAME_CONSTANTS = {
    'WINDOW_WIDTH': 800,
    'WINDOW_HEIGHT': 600,
    'FPS': 60,
    'COLORS': {
        'background': (0, 0, 0),  # Black background for retro feel
        'dark': (20, 20, 20),
        'primary': (0, 255, 0),   # Classic green terminal color
        'secondary': (0, 200, 0),
        'accent': (255, 50, 50),
        'success': (0, 255, 0),
        'error': (255, 0, 0),
        'neutral': (100, 100, 100),
        'text': (0, 255, 0),      # Matrix-style green text
        'shadow': (0, 0, 0, 25),
        'button': {
            'default': (0, 200, 0),
            'correct': (0, 255, 0),
            'incorrect': (255, 0, 0)
        },
        'enemy': (255, 0, 0)  # Red color for enemies
    },
    'PLAYER_SPEED': 5,  # New constant for player movement
    'BULLET_SPEED': 10,
    'BULLET_SIZE': 5,
    'ENEMY_SPEED': 1,  # Speed of enemies
}

class Particle:
    def __init__(self, x: float, y: float, velocity: Tuple[float, float], lifetime: int = 30):
        self.x = x
        self.y = y
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.alpha = 255
        self.size = random.randint(2, 4)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.alpha = int((self.lifetime / 30) * 255)
        self.size = max(1, self.size - 0.1)

    def draw(self, surface):
        if self.lifetime > 0:
            color = (*GAME_CONSTANTS['COLORS']['primary'][:3], self.alpha)
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (self.size, self.size), self.size)
            surface.blit(s, (self.x - self.size, self.y - self.size))

class Button:
    def __init__(self, x, y, width, height, text, color, font_size=36):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.original_color = color
        self.font = pygame.font.Font(None, font_size)
        self.active = True
        self.hover = False
        self.particles = []
    
    def add_particles(self, is_correct):
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(
                Particle(self.rect.centerx, self.rect.centery, (vx, vy))
            )
    
    def update(self, mouse_pos):
        if self.active:
            self.hover = self.rect.collidepoint(mouse_pos)
            # Update particles
            self.particles = [p for p in self.particles if p.lifetime > 0]
            for particle in self.particles:
                particle.update()
    
    def draw(self, surface):
        if not self.active:
            return
        
        # Draw particles
        for particle in self.particles:
            particle.draw(surface)
        
        # Draw button
        pygame.draw.rect(surface, self.color, self.rect, 2)
        if self.hover:
            pygame.draw.rect(surface, self.color, self.rect.inflate(-4, -4), 1)
        
        text_surface = self.font.render(self.text, True, self.color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

class Problem:
    def __init__(self, difficulty=1):
        self.difficulty = difficulty
        self.generate()
    
    def generate(self):
        max_num = 10 * self.difficulty
        self.num1 = random.randint(1, max_num)
        self.num2 = random.randint(1, max_num)
        self.operators = ['+', '-', '*'] if self.difficulty > 1 else ['+']
        self.operator = random.choice(self.operators)
        self.correct_answer = self.calculate_answer()
        
    def calculate_answer(self):
        if self.operator == '+':
            return self.num1 + self.num2
        elif self.operator == '-':
            return self.num1 - self.num2
        else:
            return self.num1 * self.num2
    
    @property
    def text(self):
        return f"{self.num1} {self.operator} {self.num2}"

class Character:
    def __init__(self, name, sprite_path=None, position=(0, 0)):
        self.name = name
        self.position = position
        self.sprite = None
        self.animation_frame = 0
        self.animation_timer = 0
        self.direction = 'right'
        self.state = 'idle'
        self.sprites = {
            'idle': [],
            'attack': [],
            'hurt': [],
            'victory': []
        }
        
        # Load sprite if provided, otherwise create placeholder
        if sprite_path and Path(sprite_path).exists():
            self.load_sprite(sprite_path)
        else:
            self.create_placeholder_sprite()
    
    def load_sprite(self, path):
        try:
            self.sprite = pygame.image.load(path).convert_alpha()
        except:
            self.create_placeholder_sprite()
    
    def create_placeholder_sprite(self):
        # Create a simple colored rectangle as placeholder
        self.sprite = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.rect(self.sprite, GAME_CONSTANTS['COLORS']['primary'], (0, 0, 64, 64))
        pygame.draw.rect(self.sprite, GAME_CONSTANTS['COLORS']['secondary'], (10, 10, 44, 44))
    
    def update_animation(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= 0.1:  # Animation frame rate
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % len(self.sprites[self.state])
    
    def draw(self, surface):
        if self.sprite:
            surface.blit(self.sprite, self.position)

class Boss(Character):
    def __init__(self, name, sprite_path=None, position=(0, 0), difficulty=1):
        super().__init__(name, sprite_path, position)
        self.difficulty = difficulty
        self.health = 100
        self.attack_patterns = []
        self.current_pattern = 0
        self.dialog = []
    
    def add_dialog(self, text):
        self.dialog.append(text)
    
    def get_next_dialog(self):
        if self.dialog:
            return self.dialog.pop(0)
        return None

class StoryScene:
    def __init__(self, background=None):
        self.background = background
        self.characters = []
        self.dialog = []
        self.completed = False
    
    def add_character(self, character, position):
        character.position = position
        self.characters.append(character)
    
    def add_dialog(self, character_name, text):
        self.dialog.append((character_name, text))
    
    def draw(self, surface):
        # Draw background if available
        if self.background:
            surface.blit(self.background, (0, 0))
        
        # Draw characters
        for character in self.characters:
            character.draw(surface)
        
        # Draw dialog if available
        if self.dialog:
            self.draw_dialog_box(surface)
    
    def draw_dialog_box(self, surface):
        if not self.dialog:
            return
            
        char_name, text = self.dialog[0]
        
        # Create dialog box
        box_height = 150
        box_rect = pygame.Rect(50, GAME_CONSTANTS['WINDOW_HEIGHT'] - box_height - 20, 
                             GAME_CONSTANTS['WINDOW_WIDTH'] - 100, box_height)
        
        # Draw semi-transparent background
        dialog_surface = pygame.Surface((box_rect.width, box_rect.height), 
                                      pygame.SRCALPHA)
        dialog_surface.fill((*GAME_CONSTANTS['COLORS']['story_box'][:3], 180))
        surface.blit(dialog_surface, box_rect)
        
        # Draw name and text
        font = pygame.font.Font(None, 32)
        name_surface = font.render(char_name, True, GAME_CONSTANTS['COLORS']['dialog'])
        text_surface = font.render(text, True, GAME_CONSTANTS['COLORS']['dialog'])
        
        surface.blit(name_surface, (box_rect.x + 20, box_rect.y + 20))
        surface.blit(text_surface, (box_rect.x + 20, box_rect.y + 60))

class StoryMode:
    def __init__(self):
        self.current_scene = 0
        self.scenes = []
        self.player = None
        self.current_boss = None
        self.setup_story()
    
    def setup_story(self):
        # Create player character
        self.player = Character("Hero")
        
        # Create sample story scenes
        self.create_introduction_scene()
        self.create_first_boss_scene()
        # Add more scenes as needed
    
    def create_introduction_scene(self):
        scene = StoryScene()
        scene.add_character(self.player, (GAME_CONSTANTS['WINDOW_WIDTH']//4, GAME_CONSTANTS['WINDOW_HEIGHT']//2))
        scene.add_dialog("Narrator", "In a world where mathematics holds magical power...")
        scene.add_dialog("Hero", "I must master these numerical arts to save our realm!")
        self.scenes.append(scene)
    
    def create_first_boss_scene(self):
        scene = StoryScene()
        boss = Boss("Number Wizard", position=(GAME_CONSTANTS['WINDOW_WIDTH']*3//4, GAME_CONSTANTS['WINDOW_HEIGHT']//2))
        boss.add_dialog("You dare challenge my mathematical might?")
        boss.add_dialog("Solve these puzzles if you can!")
        
        scene.add_character(self.player, (GAME_CONSTANTS['WINDOW_WIDTH']//4, GAME_CONSTANTS['WINDOW_HEIGHT']//2))
        scene.add_character(boss, boss.position)
        scene.add_dialog("Number Wizard", boss.get_next_dialog())
        self.scenes.append(scene)
    
    def next_scene(self):
        if self.current_scene < len(self.scenes) - 1:
            self.current_scene += 1
            return True
        return False
    
    def draw_current_scene(self, surface):
        if 0 <= self.current_scene < len(self.scenes):
            self.scenes[self.current_scene].draw(surface)

class Bullet:
    def __init__(self, x: float, y: float, target_x: float, target_y: float):
        self.x = x
        self.y = y
        dx = target_x - x
        dy = target_y - y
        length = math.sqrt(dx**2 + dy**2)
        self.dx = (dx/length) * GAME_CONSTANTS['BULLET_SPEED']
        self.dy = (dy/length) * GAME_CONSTANTS['BULLET_SPEED']
        self.active = True
        self.trail = []
        self.trail_length = 10

    def update(self):
        self.trail.insert(0, (self.x, self.y))
        if len(self.trail) > self.trail_length:
            self.trail.pop()
        
        self.x += self.dx
        self.y += self.dy
        
        if (self.x < 0 or self.x > GAME_CONSTANTS['WINDOW_WIDTH'] or
            self.y < 0 or self.y > GAME_CONSTANTS['WINDOW_HEIGHT']):
            self.active = False

    def draw(self, surface):
        pygame.draw.circle(surface, GAME_CONSTANTS['COLORS']['primary'], 
                         (int(self.x), int(self.y)), 
                         GAME_CONSTANTS['BULLET_SIZE'])
        # Draw trail
        for i, (trail_x, trail_y) in enumerate(self.trail):
            radius = GAME_CONSTANTS['BULLET_SIZE'] * (1 - i/self.trail_length)
            pygame.draw.circle(surface, GAME_CONSTANTS['COLORS']['primary'], 
                             (int(trail_x), int(trail_y)), 
                             int(radius))

class Enemy:
    def __init__(self, x: float, y: float, letter: str):
        self.x = x
        self.y = y
        self.letter = letter
        self.direction = random.choice([-1, 1])  # Randomly float left or right
        self.speed = GAME_CONSTANTS['ENEMY_SPEED']
        self.is_alive = True  # Track if the enemy is alive
        self.explosion = None  # Explosion effect

    def update(self):
        if self.is_alive:
            # Move the enemy left or right
            self.x += self.direction * self.speed
            # Bounce off the edges of the screen
            if self.x < 0 or self.x > GAME_CONSTANTS['WINDOW_WIDTH']:
                self.direction *= -1  # Reverse direction

    def draw(self, surface):
        if self.is_alive:
            font = pygame.font.Font(None, 48)
            text_surface = font.render(self.letter, True, GAME_CONSTANTS['COLORS']['enemy'])
            text_rect = text_surface.get_rect(center=(self.x, self.y))
            surface.blit(text_surface, text_rect)
        else:
            if self.explosion:
                self.explosion.draw(surface)  # Draw explosion

    def hit(self):
        self.is_alive = False  # Mark enemy as dead
        self.explosion = Explosion(self.x, self.y)  # Create explosion effect
        # Set a timer to remove the enemy after a short delay
        pygame.time.set_timer(pygame.USEREVENT, 2000)  # 2 seconds delay for the explosion

class Game:
    def __init__(self, display_surface):
        self.display_surface = display_surface  # Store the display surface
        self.score = 0
        self.current_problem = None
        self.buttons = []  # Initialize buttons as an empty list
        self.difficulty = 1
        self.streak = 0
        self.player_pos = [GAME_CONSTANTS['WINDOW_WIDTH'] // 2, GAME_CONSTANTS['WINDOW_HEIGHT'] // 2]
        self.health = 3  # Player health
        self.create_new_problem()  # Create the first problem
        self.bullets = []
        self.last_shot_time = 0
        self.shoot_delay = 250  # Milliseconds between shots
        self.shooting_direction = [0, -1]  # Default shooting up
        self.enemies = self.create_enemies()  # Initialize enemies

    def create_enemies(self):
        letters = ['α', 'β', 'γ', 'δ', 'ε']  # Greek letters
        enemies = []
        for _ in range(5):  # Create 5 enemies
            x = random.randint(50, GAME_CONSTANTS['WINDOW_WIDTH'] - 50)
            y = random.randint(50, GAME_CONSTANTS['WINDOW_HEIGHT'] - 50)
            letter = random.choice(letters)
            enemies.append(Enemy(x, y, letter))
        return enemies

    def create_new_problem(self):
        self.current_problem = Problem(self.difficulty)
        self.buttons = self.create_answer_buttons()  # Create answer buttons
        print(f"Buttons initialized: {self.buttons}")  # Debugging line
        self.enemies = self.create_enemies()  # Regenerate enemies for the new problem
    
    def create_answer_buttons(self):
        correct_answer = self.current_problem.correct_answer
        wrong_answers = self.generate_wrong_answers(correct_answer)
        answers = wrong_answers + [correct_answer]
        random.shuffle(answers)
        
        buttons = []  # Initialize buttons as an empty list
        button_width = 120
        spacing = 20
        total_width = (button_width + spacing) * len(answers) - spacing
        start_x = (GAME_CONSTANTS['WINDOW_WIDTH'] - total_width) // 2
        
        for i, answer in enumerate(answers):
            x = start_x + (button_width + spacing) * i
            button = Button(x, 400, button_width, 50, str(answer), 
                          GAME_CONSTANTS['COLORS']['button']['default'])
            buttons.append((button, answer == correct_answer))
        
        return buttons  # Return the list of buttons
    
    def generate_wrong_answers(self, correct):
        wrong_answers = set()
        while len(wrong_answers) < 3:
            if random.random() < 0.5:
                wrong = correct + random.randint(-5 * self.difficulty, 5 * self.difficulty)
            else:
                wrong = correct + (random.choice([-1, 1]) * correct // 2)
            if wrong != correct and wrong not in wrong_answers:
                wrong_answers.add(wrong)
        return list(wrong_answers)

    def increase_difficulty(self):
        self.difficulty += 1
        for enemy in self.enemies:
            enemy.speed += 0.5  # Increase enemy speed
        # Create a new problem with increased difficulty
        self.create_new_problem()
    
    def update(self):
        # Handle player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player_pos[0] = max(20, self.player_pos[0] - GAME_CONSTANTS['PLAYER_SPEED'])
            self.shooting_direction = [-1, 0]
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player_pos[0] = min(GAME_CONSTANTS['WINDOW_WIDTH'] - 20, 
                                   self.player_pos[0] + GAME_CONSTANTS['PLAYER_SPEED'])
            self.shooting_direction = [1, 0]
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.player_pos[1] = max(20, self.player_pos[1] - GAME_CONSTANTS['PLAYER_SPEED'])
            self.shooting_direction = [0, -1]
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.player_pos[1] = min(GAME_CONSTANTS['WINDOW_HEIGHT'] - 20, 
                                   self.player_pos[1] + GAME_CONSTANTS['PLAYER_SPEED'])
            self.shooting_direction = [0, 1]

        # Handle shooting with spacebar
        if keys[pygame.K_SPACE]:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_shot_time >= self.shoot_delay:
                self.last_shot_time = current_time
                # Calculate target position based on shooting direction
                target_x = self.player_pos[0] + self.shooting_direction[0] * 100
                target_y = self.player_pos[1] + self.shooting_direction[1] * 100
                new_bullet = Bullet(self.player_pos[0], self.player_pos[1], 
                                  target_x, target_y)
                self.bullets.append(new_bullet)

        # Update bullets and check collisions
        self.bullets = [bullet for bullet in self.bullets if bullet.active]
        for bullet in self.bullets:
            bullet.update()
            bullet_rect = pygame.Rect(bullet.x - GAME_CONSTANTS['BULLET_SIZE'],
                                    bullet.y - GAME_CONSTANTS['BULLET_SIZE'],
                                    GAME_CONSTANTS['BULLET_SIZE'] * 2,
                                    GAME_CONSTANTS['BULLET_SIZE'] * 2)
            for button, is_correct in self.buttons:
                if button.active and button.rect.colliderect(bullet_rect):
                    self.handle_answer(button, is_correct)
                    button.add_particles(is_correct)  # Add particle effect
                    bullet.active = False

            # Check for collisions with enemies
            for enemy in self.enemies:
                if enemy.is_alive and bullet_rect.colliderect(pygame.Rect(enemy.x - 20, enemy.y - 20, 40, 40)):
                    enemy.hit()  # Trigger enemy hit
                    bullet.active = False  # Deactivate bullet
                    break  # Exit loop after hitting one enemy

        # Check for events to remove dead enemies
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                self.enemies = [enemy for enemy in self.enemies if enemy.is_alive]  # Remove dead enemies
                self.enemies.extend(self.create_enemies())  # Regenerate enemies

        # Check for collisions with enemies
        for enemy in self.enemies:
            if enemy.is_alive and pygame.Rect(enemy.x - 20, enemy.y - 20, 40, 40).colliderect(pygame.Rect(self.player_pos[0] - 20, self.player_pos[1] - 20, 40, 40)):
                self.health -= 1  # Decrease health
                enemy.hit()  # Trigger enemy hit
                if self.health <= 0:
                    self.display_game_over_message(self.display_surface)  # Pass the display surface

        # Update enemies
        for enemy in self.enemies:
            enemy.update()  # Call the update method for each enemy

    def draw(self, surface):
        font = pygame.font.Font(None, 48)  # Define the font here
        # Draw retro grid background
        for i in range(0, GAME_CONSTANTS['WINDOW_WIDTH'], 40):
            pygame.draw.line(surface, (0, 50, 0), (i, 0), (i, GAME_CONSTANTS['WINDOW_HEIGHT']))
        for i in range(0, GAME_CONSTANTS['WINDOW_HEIGHT'], 40):
            pygame.draw.line(surface, (0, 50, 0), (0, i), (GAME_CONSTANTS['WINDOW_WIDTH'], i))
        
        # Draw player with direction indicator
        points = []
        if self.shooting_direction[0] == 0 and self.shooting_direction[1] == -1:  # Up
            points = [
                (self.player_pos[0], self.player_pos[1] - 15),
                (self.player_pos[0] - 10, self.player_pos[1] + 10),
                (self.player_pos[0] + 10, self.player_pos[1] + 10)
            ]
        elif self.shooting_direction[0] == 0 and self.shooting_direction[1] == 1:  # Down
            points = [
                (self.player_pos[0], self.player_pos[1] + 15),
                (self.player_pos[0] - 10, self.player_pos[1] - 10),
                (self.player_pos[0] + 10, self.player_pos[1] - 10)
            ]
        elif self.shooting_direction[0] == -1:  # Left
            points = [
                (self.player_pos[0] - 15, self.player_pos[1]),
                (self.player_pos[0] + 10, self.player_pos[1] - 10),
                (self.player_pos[0] + 10, self.player_pos[1] + 10)
            ]
        elif self.shooting_direction[0] == 1:  # Right
            points = [
                (self.player_pos[0] + 15, self.player_pos[1]),
                (self.player_pos[0] - 10, self.player_pos[1] - 10),
                (self.player_pos[0] - 10, self.player_pos[1] + 10)
            ]
        
        pygame.draw.polygon(surface, GAME_CONSTANTS['COLORS']['primary'], points)
        
        # Draw problem with retro effect
        font = pygame.font.Font(None, 48)
        problem_surface = font.render(self.current_problem.text + " = ?", True, 
                                    GAME_CONSTANTS['COLORS']['text'])
        problem_rect = problem_surface.get_rect(center=(GAME_CONSTANTS['WINDOW_WIDTH']//2, 200))
        surface.blit(problem_surface, problem_rect)
        
        # Draw score and level with retro effect
        score_surface = font.render(f"SCORE: {self.score}", True, 
                                  GAME_CONSTANTS['COLORS']['text'])
        level_surface = font.render(f"LEVEL: {self.difficulty}", True, 
                                  GAME_CONSTANTS['COLORS']['text'])
        health_surface = font.render(f"Health: {self.health}", True, 
                                   GAME_CONSTANTS['COLORS']['text'])
        surface.blit(score_surface, (20, 20))
        surface.blit(level_surface, (GAME_CONSTANTS['WINDOW_WIDTH'] - 150, 20))
        surface.blit(health_surface, (20, 60))
        
        # Draw buttons
        for button, _ in self.buttons:
            button.draw(surface)
        
        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(surface)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(surface)
    
    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for button, is_correct in self.buttons:
                if button.rect.collidepoint(mouse_pos):
                    if is_correct:
                        self.score += 1
                        self.streak += 1
                        if self.streak % 5 == 0:  # Increase difficulty every 5 correct answers
                            self.difficulty += 1
                        button.color = GAME_CONSTANTS['COLORS']['button']['correct']
                    else:
                        self.streak = 0
                        button.color = GAME_CONSTANTS['COLORS']['button']['incorrect']
                    pygame.time.wait(300)  # Brief pause to show correct/incorrect color
                    self.create_new_problem()
                    break

    def handle_answer(self, button, is_correct):
        if is_correct:
            self.score += 1
            self.streak += 1
            if self.streak % 5 == 0:  # Increase difficulty every 5 correct answers
                self.difficulty += 1
            button.color = GAME_CONSTANTS['COLORS']['button']['correct']
        else:
            self.streak = 0
            button.color = GAME_CONSTANTS['COLORS']['button']['incorrect']
        
        pygame.time.wait(300)  # Brief pause to show correct/incorrect color
        self.create_new_problem()

    def display_game_over_message(self, surface):
        font = pygame.font.Font(None, 74)
        game_over_surface = font.render("Game Over", True, GAME_CONSTANTS['COLORS']['text'])
        game_over_rect = game_over_surface.get_rect(center=(GAME_CONSTANTS['WINDOW_WIDTH'] // 2, GAME_CONSTANTS['WINDOW_HEIGHT'] // 2))
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    self.health = 3  # Reset health for a new game
                    self.create_new_problem()  # Restart the game
                    return  # Exit the game over message loop
            
            surface.fill(GAME_CONSTANTS['COLORS']['background'])
            surface.blit(game_over_surface, game_over_rect)
            pygame.display.update()

class CompetitiveGame:
    pass

class Explosion:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.lifetime = 30  # Duration of the explosion
        self.particles = []
        self.acronyms = ["SUM", "PROD", "DIFF", "QUOT", "MATH"]  # Math acronyms
        self.acronym = random.choice(self.acronyms)  # Randomly select an acronym
        self.font = pygame.font.Font(None, 48)

        # Create particles for the explosion
        for _ in range(50):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(Particle(self.x, self.y, (vx, vy)))

    def update(self):
        self.lifetime -= 1
        for particle in self.particles:
            particle.update()

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)
        
        # Draw the acronym at the explosion center
        text_surface = self.font.render(self.acronym, True, GAME_CONSTANTS['COLORS']['primary'])
        text_rect = text_surface.get_rect(center=(self.x, self.y))
        surface.blit(text_surface, text_rect)

def start_screen(surface):
    font = pygame.font.Font(None, 74)
    title_surface = font.render("Math Learning Game", True, GAME_CONSTANTS['COLORS']['text'])
    title_rect = title_surface.get_rect(center=(GAME_CONSTANTS['WINDOW_WIDTH'] // 2, 100))
    
    instructions_surface = font.render("Press SPACE to Start", True, GAME_CONSTANTS['COLORS']['text'])
    instructions_rect = instructions_surface.get_rect(center=(GAME_CONSTANTS['WINDOW_WIDTH'] // 2, 300))
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return  # Start the game
        
        surface.fill(GAME_CONSTANTS['COLORS']['background'])
        surface.blit(title_surface, title_rect)
        surface.blit(instructions_surface, instructions_rect)
        pygame.display.update()

def main():
    # Initialize display and clock
    DISPLAY_SURF = pygame.display.set_mode((GAME_CONSTANTS['WINDOW_WIDTH'], 
                                          GAME_CONSTANTS['WINDOW_HEIGHT']))
    pygame.display.set_caption('Math Learning Game')
    clock = pygame.time.Clock()
    
    start_screen(DISPLAY_SURF)  # Show start screen
    
    game_manager = Game(DISPLAY_SURF)  # Pass the display surface to the Game class
    game_manager.create_new_problem()  # Start with practice mode
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            game_manager.handle_input(event)
        
        game_manager.update()
        DISPLAY_SURF.fill(GAME_CONSTANTS['COLORS']['background'])
        game_manager.draw(DISPLAY_SURF)
        pygame.display.update()
        clock.tick(GAME_CONSTANTS['FPS'])

if __name__ == '__main__':
    main()
    