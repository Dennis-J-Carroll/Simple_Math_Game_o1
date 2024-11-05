import pygame
import random
import sys
import math
import json
from pathlib import Path

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Combine and organize constants
GAME_CONSTANTS = {
    'WINDOW_WIDTH': 800,
    'WINDOW_HEIGHT': 600,
    'FPS': 60,
    'COLORS': {
        'background': (245, 245, 245),
        'dark': (34, 40, 49),
        'primary': (48, 71, 94),
        'secondary': (0, 173, 181),
        'accent': (255, 89, 94),
        'success': (46, 213, 115),
        'error': (255, 71, 87),
        'neutral': (238, 238, 238),
        'text': (52, 58, 64),
        'shadow': (0, 0, 0, 25),
        'button': {
            'default': (0, 0, 255),
            'correct': (0, 255, 0),
            'incorrect': (255, 0, 0)
        }
    }
}

class Button:
    def __init__(self, x, y, width, height, text, color, font_size=36):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.original_color = color
        self.font = pygame.font.Font(None, font_size)
        self.active = True
        self.hover = False
    
    def draw(self, surface):
        if not self.active:
            return
            
        # Add hover effect
        color = self.color
        if self.hover:
            color = tuple(max(0, min(255, c + 30)) for c in self.color)
            
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        text_surface = self.font.render(self.text, True, GAME_CONSTANTS['COLORS']['text'])
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def update(self, mouse_pos):
        if self.active:
            self.hover = self.rect.collidepoint(mouse_pos)

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

class Game:
    def __init__(self):
        self.score = 0
        self.current_problem = None
        self.buttons = []
        self.difficulty = 1
        self.streak = 0
        self.create_new_problem()
        
    def create_new_problem(self):
        self.current_problem = Problem(self.difficulty)
        self.create_answer_buttons()
        
    def create_answer_buttons(self):
        correct_answer = self.current_problem.correct_answer
        wrong_answers = self.generate_wrong_answers(correct_answer)
        answers = wrong_answers + [correct_answer]
        random.shuffle(answers)
        
        self.buttons = []
        button_width = 120
        spacing = 20
        total_width = (button_width + spacing) * len(answers) - spacing
        start_x = (GAME_CONSTANTS['WINDOW_WIDTH'] - total_width) // 2
        
        for i, answer in enumerate(answers):
            x = start_x + (button_width + spacing) * i
            button = Button(x, 400, button_width, 50, str(answer), 
                          GAME_CONSTANTS['COLORS']['button']['default'])
            self.buttons.append((button, answer == correct_answer))
    
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
    
    def update(self):
        # Update button hover states
        mouse_pos = pygame.mouse.get_pos()
        for button, _ in self.buttons:
            button.update(mouse_pos)
    
    def draw(self, surface):
        # Draw problem
        font = pygame.font.Font(None, 48)
        problem_surface = font.render(self.current_problem.text + " = ?", True, 
                                    GAME_CONSTANTS['COLORS']['text'])
        problem_rect = problem_surface.get_rect(center=(GAME_CONSTANTS['WINDOW_WIDTH']//2, 200))
        surface.blit(problem_surface, problem_rect)
        
        # Draw score
        score_surface = font.render(f"Score: {self.score}", True, 
                                  GAME_CONSTANTS['COLORS']['text'])
        surface.blit(score_surface, (20, 20))
        
        # Draw difficulty level
        level_surface = font.render(f"Level: {self.difficulty}", True, 
                                  GAME_CONSTANTS['COLORS']['text'])
        surface.blit(level_surface, (GAME_CONSTANTS['WINDOW_WIDTH'] - 150, 20))
        
        # Draw buttons
        for button, _ in self.buttons:
            button.draw(surface)
    
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

class CompetitiveGame:
    pass

def main():
    # Initialize display and clock
    DISPLAY_SURF = pygame.display.set_mode((GAME_CONSTANTS['WINDOW_WIDTH'], 
                                          GAME_CONSTANTS['WINDOW_HEIGHT']))
    pygame.display.set_caption('Math Learning Game')
    clock = pygame.time.Clock()
    
    game_manager = Game()
    game_manager.create_new_problem()  # Start with practice mode
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            game_manager.handle_input(event)
        
        DISPLAY_SURF.fill(GAME_CONSTANTS['COLORS']['background'])
        game_manager.draw(DISPLAY_SURF)
        pygame.display.update()
        clock.tick(GAME_CONSTANTS['FPS'])

if __name__ == '__main__':
    main()
    