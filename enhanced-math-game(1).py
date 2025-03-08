import pygame
import random
import sys
import math
import json
import time
from pathlib import Path
from typing import List, Tuple, Dict, Union, Optional

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Game Constants
GAME_CONSTANTS = {
    'WINDOW_WIDTH': 900,
    'WINDOW_HEIGHT': 700,
    'FPS': 60,
    'COLORS': {
        'background': (10, 10, 30),  # Dark blue background
        'grid': (20, 50, 80, 120),   # Semi-transparent grid lines
        'primary': (0, 200, 255),    # Cyan for main elements
        'secondary': (0, 255, 180),  # Teal for secondary elements
        'accent': (255, 80, 120),    # Pink accent
        'success': (50, 255, 100),   # Bright green for success
        'error': (255, 60, 80),      # Bright red for errors
        'neutral': (180, 180, 220),  # Light purple for neutral elements
        'text': {
            'light': (220, 220, 255),  # Light text
            'dark': (40, 40, 80),      # Dark text
            'highlight': (255, 240, 100)  # Yellow highlight text
        },
        'button': {
            'default': (60, 120, 200),
            'hover': (80, 160, 250),
            'correct': (50, 220, 100),
            'incorrect': (255, 60, 80)
        },
        'enemy': {
            'basic': (255, 80, 80),      # Red
            'advanced': (255, 160, 60),  # Orange
            'expert': (255, 60, 200)     # Magenta
        },
        'player': (40, 200, 240)       # Player color
    },
    'PLAYER_SPEED': 6,
    'BULLET_SPEED': 12,
    'BULLET_SIZE': 6,
    'ENEMY_SPEED_BASE': 1.5,
    'PARTICLE_LIFETIME': 40
}

# Helper Functions
def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b with factor t."""
    return a + (b - a) * t

def ease_out_quad(t: float) -> float:
    """Quadratic ease out function."""
    return 1 - (1 - t) * (1 - t)

def ease_in_out_cubic(t: float) -> float:
    """Cubic ease in-out function."""
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min_val and max_val."""
    return max(min_val, min(value, max_val))

def create_glow_surface(radius: int, color: Tuple[int, int, int], alpha_factor: float = 1.0) -> pygame.Surface:
    """Create a circular gradient surface that simulates a glow effect."""
    diameter = radius * 2
    glow = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    
    for x in range(diameter):
        for y in range(diameter):
            # Calculate distance from center
            distance = math.sqrt((x - radius) ** 2 + (y - radius) ** 2)
            if distance <= radius:
                # Calculate alpha based on distance from center
                alpha = int(255 * (1 - distance / radius) * alpha_factor)
                glow.set_at((x, y), (*color, alpha))
    
    return glow

# Classes
class Particle:
    def __init__(self, x: float, y: float, velocity: Tuple[float, float], 
                 color: Tuple[int, int, int], lifetime: int = GAME_CONSTANTS['PARTICLE_LIFETIME'],
                 size_start: float = 3.0, size_end: float = 0.5):
        self.x = x
        self.y = y
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.alpha = 255
        self.size_start = size_start
        self.size_end = size_end
        self.size = size_start

    def update(self):
        self.x += self.vx
        self.y += self.vy
        
        # Apply some drag to slow down particles
        self.vx *= 0.96
        self.vy *= 0.96
        
        # Update lifetime and properties
        self.lifetime -= 1
        life_ratio = self.lifetime / self.max_lifetime
        self.alpha = int(255 * life_ratio)
        self.size = lerp(self.size_end, self.size_start, life_ratio)

    def draw(self, surface: pygame.Surface):
        if self.lifetime > 0:
            # Create a small surface with alpha for the particle
            s = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, self.alpha), (self.size, self.size), self.size)
            surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_particle(self, x: float, y: float, velocity: Tuple[float, float], 
                     color: Tuple[int, int, int], lifetime: int = GAME_CONSTANTS['PARTICLE_LIFETIME'],
                     size_start: float = 3.0, size_end: float = 0.5):
        self.particles.append(Particle(x, y, velocity, color, lifetime, size_start, size_end))
    
    def add_explosion(self, x: float, y: float, color: Tuple[int, int, int], 
                      particle_count: int = 20, speed_min: float = 2.0, speed_max: float = 5.0,
                      lifetime_min: int = 20, lifetime_max: int = 40,
                      size_start: float = 3.0, size_end: float = 0.5):
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(speed_min, speed_max)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.randint(lifetime_min, lifetime_max)
            self.add_particle(x, y, (vx, vy), color, lifetime, size_start, size_end)
    
    def add_directional_burst(self, x: float, y: float, direction: Tuple[float, float], 
                             color: Tuple[int, int, int], spread: float = math.pi/4,
                             particle_count: int = 12, speed_min: float = 3.0, speed_max: float = 7.0):
        """Add particles in a specific direction with some spread."""
        base_angle = math.atan2(direction[1], direction[0])
        
        for _ in range(particle_count):
            angle = base_angle + random.uniform(-spread, spread)
            speed = random.uniform(speed_min, speed_max)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.add_particle(x, y, (vx, vy), color)
    
    def update(self):
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for particle in self.particles:
            particle.update()
    
    def draw(self, surface: pygame.Surface):
        for particle in self.particles:
            particle.draw(surface)

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 color: Tuple[int, int, int] = GAME_CONSTANTS['COLORS']['button']['default'], 
                 font_size: int = 36, border_radius: int = 10, shadow_offset: int = 4):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.original_color = color
        self.font = pygame.font.Font(None, font_size)
        self.active = True
        self.hover = False
        self.clicked = False
        self.border_radius = border_radius
        self.shadow_offset = shadow_offset
        self.animation_progress = 0  # For button press animation
    
    def update(self, mouse_pos: Tuple[int, int], mouse_pressed: bool = False):
        if not self.active:
            return False
        
        prev_hover = self.hover
        self.hover = self.rect.collidepoint(mouse_pos)
        
        # Handle hover state change with a sound effect
        if self.hover and not prev_hover:
            # You could add a hover sound here
            pass
        
        # Handle button press animation
        if self.hover and mouse_pressed and not self.clicked:
            self.clicked = True
            # You could add a click sound here
            return True
        
        # Animation updates
        if self.clicked:
            self.animation_progress = min(1, self.animation_progress + 0.2)
            if self.animation_progress >= 1:
                self.clicked = False
                self.animation_progress = 0
        
        return False
    
    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        
        # Calculate button position based on animation
        anim_offset = int(self.shadow_offset * (1 - self.animation_progress)) if self.clicked else self.shadow_offset
        button_rect = self.rect.copy()
        
        # Draw shadow (slightly larger black rect behind the button)
        shadow_rect = button_rect.copy()
        shadow_rect.x += anim_offset
        shadow_rect.y += anim_offset
        pygame.draw.rect(surface, (20, 20, 40), shadow_rect, border_radius=self.border_radius)
        
        # Determine button color based on state
        if self.hover:
            color = GAME_CONSTANTS['COLORS']['button']['hover']
        else:
            color = self.color
        
        # Draw button
        pygame.draw.rect(surface, color, button_rect, border_radius=self.border_radius)
        
        # Add a subtle highlight on top
        highlight_rect = button_rect.copy()
        highlight_rect.height = button_rect.height // 3
        pygame.draw.rect(surface, [min(c + 30, 255) for c in color], highlight_rect, 
                       border_radius=self.border_radius, border_top_left_radius=self.border_radius,
                       border_top_right_radius=self.border_radius, border_bottom_left_radius=0,
                       border_bottom_right_radius=0)
        
        # Draw text
        text_color = GAME_CONSTANTS['COLORS']['text']['light']
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=button_rect.center)
        surface.blit(text_surface, text_rect)

class Problem:
    def __init__(self, difficulty: int = 1):
        self.difficulty = difficulty
        self.max_difficulty = 15  # Maximum difficulty level
        self.generate()
    
    def generate(self):
        """Generate a math problem based on the current difficulty level."""
        # Clamp difficulty to max
        diff = min(self.difficulty, self.max_difficulty)
        
        # Different problem types based on difficulty
        if diff <= 3:
            # Basic arithmetic: addition and subtraction
            self._generate_basic_arithmetic()
        elif diff <= 6:
            # Multiplication and division added
            self._generate_intermediate_arithmetic()
        elif diff <= 9:
            # Powers, roots, and more complex operations
            self._generate_advanced_arithmetic()
        elif diff <= 12:
            # Simple algebraic equations
            self._generate_simple_algebra()
        else:
            # Trigonometry and more complex algebra
            self._generate_advanced_math()
    
    def _generate_basic_arithmetic(self):
        """Generate basic addition and subtraction problems (difficulty 1-3)."""
        max_num = 10 * self.difficulty
        self.num1 = random.randint(1, max_num)
        self.num2 = random.randint(1, max_num)
        
        # Ensure subtraction doesn't result in negative numbers for very early levels
        if self.difficulty == 1:
            self.operator = '+'
        else:
            self.operator = random.choice(['+', '-'])
            if self.operator == '-' and self.num2 > self.num1:
                self.num1, self.num2 = self.num2, self.num1  # Swap to avoid negative result
        
        self.correct_answer = self._calculate_answer()
        self.problem_text = f"{self.num1} {self.operator} {self.num2}"
    
    def _generate_intermediate_arithmetic(self):
        """Generate problems with all four basic operations (difficulty 4-6)."""
        max_num = 8 * self.difficulty
        small_max = max_num // 2
        
        self.num1 = random.randint(2, max_num)
        
        # Choose operator based on difficulty
        if self.difficulty <= 4:
            self.operator = random.choice(['+', '-', '×'])
        else:
            self.operator = random.choice(['+', '-', '×', '÷'])
        
        # Adjust second number based on operator
        if self.operator == '+' or self.operator == '-':
            self.num2 = random.randint(1, max_num)
            if self.operator == '-' and self.num2 > self.num1:
                self.num1, self.num2 = self.num2, self.num1  # Swap to avoid negative result
        
        elif self.operator == '×':
            self.num2 = random.randint(2, small_max)  # Keep multiplication manageable
        
        elif self.operator == '÷':
            # Create a division problem that results in a whole number
            self.num2 = random.randint(2, small_max)
            self.num1 = self.num2 * random.randint(1, 10)  # Ensure divisible
        
        self.correct_answer = self._calculate_answer()
        self.problem_text = f"{self.num1} {self.operator} {self.num2}"
    
    def _generate_advanced_arithmetic(self):
        """Generate problems with powers, roots, etc. (difficulty 7-9)."""
        operation_type = random.randint(1, 5)
        
        if operation_type == 1:
            # Squares
            self.num1 = random.randint(2, 20)
            self.operator = '^2'
            self.correct_answer = self.num1 ** 2
            self.problem_text = f"{self.num1}{self.operator}"
        
        elif operation_type == 2:
            # Square roots (of perfect squares)
            result = random.randint(2, 15)
            self.num1 = result ** 2
            self.operator = '√'
            self.correct_answer = result
            self.problem_text = f"{self.operator}{self.num1}"
        
        elif operation_type == 3:
            # Cubes
            self.num1 = random.randint(2, 10)
            self.operator = '^3'
            self.correct_answer = self.num1 ** 3
            self.problem_text = f"{self.num1}{self.operator}"
        
        elif operation_type == 4:
            # Powers
            self.num1 = random.randint(2, 8)
            self.num2 = random.randint(2, 4)
            self.operator = '^'
            self.correct_answer = self.num1 ** self.num2
            self.problem_text = f"{self.num1}{self.operator}{self.num2}"
        
        else:
            # Mixed operations (e.g., 3×5+7)
            self.num1 = random.randint(2, 15)
            self.num2 = random.randint(2, 10)
            self.num3 = random.randint(2, 20)
            
            ops = [('+', lambda a, b, c: a * b + c),
                   ('-', lambda a, b, c: a * b - c),
                   ('+', lambda a, b, c: a + b * c),
                   ('-', lambda a, b, c: a - b * c)]
            
            op_choice = random.choice(ops)
            self.operator = op_choice[0]
            self.correct_answer = op_choice[1](self.num1, self.num2, self.num3)
            
            if random.choice([True, False]):
                self.problem_text = f"{self.num1}×{self.num2}{self.operator}{self.num3}"
            else:
                self.problem_text = f"{self.num1}{self.operator}{self.num2}×{self.num3}"
    
    def _generate_simple_algebra(self):
        """Generate simple algebraic equations (difficulty 10-12)."""
        equation_type = random.randint(1, 3)
        
        if equation_type == 1:
            # Linear equation: ax + b = c, solve for x
            a = random.randint(1, 8)
            x = random.randint(1, 12)  # The answer
            b = random.randint(1, 20)
            c = a * x + b
            
            self.correct_answer = x
            self.problem_text = f"{a}x + {b} = {c}, x = ?"
        
        elif equation_type == 2:
            # Linear equation: ax - b = c, solve for x
            a = random.randint(1, 8)
            x = random.randint(1, 12)  # The answer
            b = random.randint(1, 20)
            c = a * x - b
            
            self.correct_answer = x
            self.problem_text = f"{a}x - {b} = {c}, x = ?"
        
        else:
            # Simple system: x + y = a, x - y = b, find x (or y)
            x = random.randint(1, 20)
            y = random.randint(1, 20)
            a = x + y
            b = x - y
            
            if random.choice([True, False]):
                self.correct_answer = x
                self.problem_text = f"If x + y = {a} and x - y = {b}, then x = ?"
            else:
                self.correct_answer = y
                self.problem_text = f"If x + y = {a} and x - y = {b}, then y = ?"
    
    def _generate_advanced_math(self):
        """Generate advanced math problems (difficulty 13-15)."""
        problem_type = random.randint(1, 5)
        
        if problem_type == 1:
            # Basic trigonometry (sine of common angles)
            angle_choices = [(0, 0), (30, 0.5), (45, 0.707), (60, 0.866), (90, 1)]
            angle, result = random.choice(angle_choices)
            
            self.correct_answer = result
            self.problem_text = f"sin({angle}°) = ?"
        
        elif problem_type == 2:
            # Basic trigonometry (cosine of common angles)
            angle_choices = [(0, 1), (30, 0.866), (45, 0.707), (60, 0.5), (90, 0)]
            angle, result = random.choice(angle_choices)
            
            self.correct_answer = result
            self.problem_text = f"cos({angle}°) = ?"
        
        elif problem_type == 3:
            # Quadratic formula application
            # For simplicity, we'll create equations with integer solutions
            x1 = random.randint(-5, 5)
            x2 = random.randint(-5, 5)
            
            # (x - x1)(x - x2) = x² - (x1+x2)x + (x1*x2)
            a = 1
            b = -(x1 + x2)
            c = x1 * x2
            
            self.correct_answer = x1 if abs(x1) <= abs(x2) else x2
            equation = f"x² "
            if b > 0:
                equation += f"+ {b}x "
            elif b < 0:
                equation += f"- {abs(b)}x "
            
            if c > 0:
                equation += f"+ {c} "
            elif c < 0:
                equation += f"- {abs(c)} "
            
            equation += "= 0"
            self.problem_text = f"Smaller solution of {equation} = ?"
        
        elif problem_type == 4:
            # Basic geometry
            shape = random.choice(["square", "circle", "triangle", "rectangle"])
            
            if shape == "square":
                side = random.randint(3, 15)
                if random.choice([True, False]):
                    self.correct_answer = side * side  # Area
                    self.problem_text = f"Area of square with side {side} = ?"
                else:
                    self.correct_answer = 4 * side  # Perimeter
                    self.problem_text = f"Perimeter of square with side {side} = ?"
            
            elif shape == "circle":
                radius = random.randint(1, 10)
                if random.choice([True, False]):
                    self.correct_answer = round(math.pi * radius * radius, 2)  # Area
                    self.problem_text = f"Area of circle with radius {radius} ≈ ?"
                else:
                    self.correct_answer = round(2 * math.pi * radius, 2)  # Circumference
                    self.problem_text = f"Circumference of circle with radius {radius} ≈ ?"
            
            elif shape == "triangle":
                base = random.randint(5, 20)
                height = random.randint(5, 15)
                self.correct_answer = (base * height) // 2  # Area
                self.problem_text = f"Area of triangle with base {base} and height {height} = ?"
            
            else:  # rectangle
                length = random.randint(5, 20)
                width = random.randint(3, 15)
                if random.choice([True, False]):
                    self.correct_answer = length * width  # Area
                    self.problem_text = f"Area of rectangle with length {length} and width {width} = ?"
                else:
                    self.correct_answer = 2 * (length + width)  # Perimeter
                    self.problem_text = f"Perimeter of rectangle with length {length} and width {width} = ?"
        
        else:
            # Logarithms and exponents
            base = random.choice([2, 10])
            power = random.randint(1, 5)
            
            if random.choice([True, False]):
                # Logarithm
                result = base ** power
                self.correct_answer = power
                self.problem_text = f"log{base}({result}) = ?"
            else:
                # Exponent
                self.correct_answer = base ** power
                self.problem_text = f"{base}^{power} = ?"
    
    def _calculate_answer(self) -> Union[int, float]:
        """Calculate the answer based on the selected operation."""
        if not hasattr(self, 'operator'):
            return 0
            
        if self.operator == '+':
            return self.num1 + self.num2
        elif self.operator == '-':
            return self.num1 - self.num2
        elif self.operator == '×':
            return self.num1 * self.num2
        elif self.operator == '÷':
            return self.num1 // self.num2 if self.num1 % self.num2 == 0 else round(self.num1 / self.num2, 2)
        else:
            return 0
    
    def generate_wrong_answers(self, count: int = 3) -> List[Union[int, float]]:
        """Generate plausible wrong answers."""
        wrong_answers = set()
        correct = self.correct_answer
        
        # Different strategies for generating wrong answers
        strategies = [
            # Near misses (off by a small amount)
            lambda: correct + random.randint(1, max(2, int(abs(correct) * 0.2))),
            lambda: correct - random.randint(1, max(2, int(abs(correct) * 0.2))),
            
            # Common mistakes
            lambda: correct * 2,  # Doubled
            lambda: correct // 2 if correct != 0 else 1,  # Halved
            lambda: -correct,  # Sign error
            
            # Operand confusion
            lambda: self.num1 + self.num2 if hasattr(self, 'num1') and hasattr(self, 'num2') and self.operator != '+' else correct + 1,
            lambda: self.num1 - self.num2 if hasattr(self, 'num1') and hasattr(self, 'num2') and self.operator != '-' else correct - 1,
            lambda: self.num1 * self.num2 if hasattr(self, 'num1') and hasattr(self, 'num2') and self.operator != '×' else correct * 2,
            
            # Off by one errors
            lambda: correct + 1,
            lambda: correct - 1,
            
            # Digit reversal for multi-digit numbers
            lambda: int(str(abs(correct))[::-1]) * (1 if correct >= 0 else -1) if abs(correct) > 9 else correct + 2,
            
            # Random but plausible
            lambda: correct + random.randint(3, max(5, int(abs(correct) * 0.5))),
            lambda: correct - random.randint(3, max(5, int(abs(correct) * 0.5)))
        ]
        
        # Try each strategy until we have enough wrong answers
        while len(wrong_answers) < count and len(wrong_answers) < len(strategies):
            strategy = random.choice(strategies)
            wrong = strategy()
            
            # Ensure the wrong answer isn't the correct one and is reasonably close
            max_diff = max(10, abs(correct) * 2)
            if (wrong != correct and wrong not in wrong_answers and 
                abs(wrong - correct) <= max_diff and abs(wrong) <= abs(correct) * 5):
                wrong_answers.add(wrong)
        
        # If we still need more wrong answers, generate them randomly
        while len(wrong_answers) < count:
            # For small answers, use a small range
            if abs(correct) < 10:
                wrong = random.randint(max(-20, int(correct) - 20), int(correct) + 20)
            else:
                wrong = int(correct * random.uniform(0.2, 1.8))
            
            if wrong != correct and wrong not in wrong_answers:
                wrong_answers.add(wrong)
        
        return list(wrong_answers)

class Enemy:
    def __init__(self, x: float, y: float, difficulty: int = 1, 
                 size: int = 30, letter: Optional[str] = None):
        self.x = x
        self.y = y
        self.difficulty = difficulty
        self.size = size
        
        # Set enemy properties based on difficulty
        if difficulty <= 3:
            self.color = GAME_CONSTANTS['COLORS']['enemy']['basic']
            self.health = 1
            self.speed = GAME_CONSTANTS['ENEMY_SPEED_BASE'] * 0.8
        elif difficulty <= 8:
            self.color = GAME_CONSTANTS['COLORS']['enemy']['advanced']
            self.health = 2
            self.speed = GAME_CONSTANTS['ENEMY_SPEED_BASE'] * 1.2
        else:
            self.color = GAME_CONSTANTS['COLORS']['enemy']['expert']
            self.health = 3
            self.speed = GAME_CONSTANTS['ENEMY_SPEED_BASE'] * 1.5
        
        # Set movement pattern
        self.movement_type = random.choice(["linear", "sinusoidal", "circular", "accelerating"])
        self.direction = random.uniform(0, 2 * math.pi)
        self.movement_timer = 0
        self.center_x, self.center_y = x, y  # For circular movement
        
        # For explosion animation
        self.is_alive = True
        self.explosion_particles = []
        self.explosion_progress = 0
        
        # Choose a mathematical symbol or letter
        if letter:
            self.letter = letter
        else:
            symbols = ['∑', '∫', '∏', '√', '∞', 'π', 'θ', 'Δ', 'α', 'β', 'γ', 'λ']
            self.letter = random.choice(symbols)
        
        # Create a glow surface for the enemy
        self.glow = create_glow_surface(size + 10, self.color, 0.6)
    
    def update(self, delta_time: float):
        if not self.is_alive:
            # Update explosion animation
            self.explosion_progress += 0.05
            return
        
        self.movement_timer += delta_time
        
        if self.movement_type == "linear":
            # Simple linear movement with occasional direction changes
            if random.random() < 0.01:
                self.direction += random.uniform(-math.pi/4, math.pi/4)
            
            self.x += math.cos(self.direction) * self.speed
            self.y += math.sin(self.direction) * self.speed
        
        elif self.movement_type == "sinusoidal":
            # Sinusoidal wave movement
            base_direction = self.direction
            wave = math.sin(self.movement_timer * 2) * 2
            
            self.x += math.cos(base_direction) * self.speed
            self.y += math.sin(base_direction) * self.speed + wave
        
        elif self.movement_type == "circular":
            # Circular motion around a point
            radius = 50
            self.x = self.center_x + math.cos(self.movement_timer) * radius
            self.y = self.center_y + math.sin(self.movement_timer) * radius
        
        else:  # accelerating
            # Gradually increasing speed in one direction, then reset
            cycle_time = 3.0  # seconds
            cycle_progress = (self.movement_timer % cycle_time) / cycle_time
            
            speed_factor = ease_out_quad(cycle_progress)
            self.x += math.cos(self.direction) * self.speed * speed_factor * 1.5
            self.y += math.sin(self.direction) * self.speed * speed_factor * 1.5
        
        # Check screen boundaries and bounce
        if self.x < self.size:
            self.x = self.size
            self.direction = math.pi - self.direction
        elif self.x > GAME_CONSTANTS['WINDOW_WIDTH'] - self.size:
            self.x = GAME_CONSTANTS['WINDOW_WIDTH'] - self.size
            self.direction = math.pi - self.direction
        
        if self.y < self.size:
            self.y = self.size
            self.direction = -self.direction
        elif self.y > GAME_CONSTANTS['WINDOW_HEIGHT'] - self.size:
            self.y = GAME_CONSTANTS['WINDOW_HEIGHT'] - self.size
            self.direction = -self.direction
    
    def draw(self, surface: pygame.Surface):
        if not self.is_alive:
            # Enemy is dead, skip drawing
            return
        
        # Draw the glow effect
        glow_rect = self.glow.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(self.glow, glow_rect)
        
        # Draw the enemy
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
        
        # Add a highlight (lighter circle inside)
        highlight_color = tuple(min(c + 50, 255) for c in self.color)
        pygame.draw.circle(surface, highlight_color, 
                         (int(self.x), int(self.y)), 
                         int(self.size * 0.7))
        
        # Draw the letter/symbol
        font = pygame.font.Font(None, 36)
        text_surface = font.render(self.letter, True, GAME_CONSTANTS['COLORS']['text']['dark'])
        text_rect = text_surface.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(text_surface, text_rect)
    
    def hit(self, particles: ParticleSystem) -> bool:
        """Handle enemy being hit. Returns True if enemy is killed."""
        self.health -= 1
        
        # Add particles for hit effect
        particles.add_explosion(
            self.x, self.y, 
            self.color, 
            particle_count=10, 
            speed_min=1, speed_max=3
        )
        
        if self.health <= 0:
            self.is_alive = False
            
            # Add particles for death explosion
            particles.add_explosion(
                self.x, self.y, 
                self.color, 
                particle_count=30, 
                speed_min=2, speed_max=6,
                lifetime_min=30, lifetime_max=60,
                size_start=5.0, size_end=0.5
            )
            
            return True
        return False

class Bullet:
    def __init__(self, x: float, y: float, direction: Tuple[float, float], 
                 speed: float = GAME_CONSTANTS['BULLET_SPEED'], 
                 size: float = GAME_CONSTANTS['BULLET_SIZE']):
        self.x = x
        self.y = y
        
        # Normalize direction vector
        length = math.sqrt(direction[0]**2 + direction[1]**2)
        if length > 0:
            self.dx = (direction[0] / length) * speed
            self.dy = (direction[1] / length) * speed
        else:
            self.dx = 0
            self.dy = -speed  # Default to shooting upward
        
        self.size = size
        self.active = True
        self.trail = []
        self.trail_length = 6
        self.color = GAME_CONSTANTS['COLORS']['primary']
        
        # Create a glow surface for the bullet
        self.glow = create_glow_surface(size * 2, self.color, 0.7)
    
    def update(self, particles: ParticleSystem):
        # Add current position to trail
        self.trail.insert(0, (self.x, self.y))
        if len(self.trail) > self.trail_length:
            self.trail.pop()
        
        # Update position
        self.x += self.dx
        self.y += self.dy
        
        # Occasionally add particles for trail effect
        if random.random() < 0.3:
            particles.add_particle(
                self.x, self.y,
                (-self.dx * 0.1, -self.dy * 0.1),
                self.color,
                lifetime=15,
                size_start=self.size * 0.7,
                size_end=0.5
            )
        
        # Check if bullet is out of bounds
        if (self.x < 0 or self.x > GAME_CONSTANTS['WINDOW_WIDTH'] or
            self.y < 0 or self.y > GAME_CONSTANTS['WINDOW_HEIGHT']):
            self.active = False
    
    def draw(self, surface: pygame.Surface):
        # Draw the glow
        glow_rect = self.glow.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(self.glow, glow_rect)
        
        # Draw the bullet
        pygame.draw.circle(
            surface, self.color, 
            (int(self.x), int(self.y)), self.size
        )
        
        # Draw trail
        for i, (trail_x, trail_y) in enumerate(self.trail):
            alpha = 150 * (1 - i / self.trail_length)
            radius = self.size * (1 - i / self.trail_length * 0.7)
            
            trail_surface = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(
                trail_surface, 
                (*self.color, int(alpha)),
                (int(radius), int(radius)), int(radius)
            )
            surface.blit(trail_surface, (int(trail_x - radius), int(trail_y - radius)))

class Player:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.size = 20
        self.color = GAME_CONSTANTS['COLORS']['player']
        self.speed = GAME_CONSTANTS['PLAYER_SPEED']
        self.direction = (0, -1)  # Default pointing up
        self.health = 3
        self.max_health = 3
        self.invulnerable = False
        self.invulnerable_time = 0
        self.shooting = False
        self.shoot_timer = 0
        self.shoot_delay = 0.2  # Time between shots in seconds
        
        # Create a glow surface for the player
        self.glow = create_glow_surface(self.size * 2, self.color, 0.7)
    
    def update(self, delta_time: float, keys_pressed: List[bool], particles: ParticleSystem) -> Optional[Bullet]:
        # Get movement direction
        dx, dy = 0, 0
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            dx -= 1
            self.direction = (-1, 0)
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            dx += 1
            self.direction = (1, 0)
        if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            dy -= 1
            self.direction = (0, -1)
        if keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            dy += 1
            self.direction = (0, 1)
        
        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.7071  # 1/sqrt(2)
            dy *= 0.7071
            
            # Update direction for diagonal movement
            self.direction = (dx, dy)
        
        # Update position
        self.x += dx * self.speed
        self.y += dy * self.speed
        
        # Add movement particles
        if dx != 0 or dy != 0:
            particles.add_particle(
                self.x - dx * 5, self.y - dy * 5,
                (-dx * random.uniform(0.5, 1.5), -dy * random.uniform(0.5, 1.5)),
                self.color,
                lifetime=10,
                size_start=3,
                size_end=0.5
            )
        
        # Keep player within screen bounds
        self.x = clamp(self.x, self.size, GAME_CONSTANTS['WINDOW_WIDTH'] - self.size)
        self.y = clamp(self.y, self.size, GAME_CONSTANTS['WINDOW_HEIGHT'] - self.size)
        
        # Handle invulnerability
        if self.invulnerable:
            self.invulnerable_time -= delta_time
            if self.invulnerable_time <= 0:
                self.invulnerable = False
        
        # Handle shooting
        self.shoot_timer -= delta_time
        if keys_pressed[pygame.K_SPACE] and self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_delay
            
            # Add particle burst for muzzle flash
            particles.add_directional_burst(
                self.x + self.direction[0] * self.size,
                self.y + self.direction[1] * self.size,
                self.direction,
                self.color,
                particle_count=8
            )
            
            # Create new bullet
            return Bullet(
                self.x + self.direction[0] * self.size,
                self.y + self.direction[1] * self.size,
                self.direction
            )
        return None
    
    def draw(self, surface: pygame.Surface):
        # Draw glow effect
        if not self.invulnerable or (self.invulnerable and (int(self.invulnerable_time * 10) % 2 == 0)):
            glow_rect = self.glow.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.glow, glow_rect)
            
            # Draw the player ship
            points = []
            
            # Calculate ship vertices based on direction
            if abs(self.direction[0]) > abs(self.direction[1]):  # Horizontal movement
                if self.direction[0] > 0:  # Right
                    points = [
                        (self.x + self.size, self.y),  # Nose
                        (self.x - self.size / 2, self.y - self.size / 2),  # Left wing
                        (self.x - self.size / 3, self.y),  # Body
                        (self.x - self.size / 2, self.y + self.size / 2)   # Right wing
                    ]
                else:  # Left
                    points = [
                        (self.x - self.size, self.y),  # Nose
                        (self.x + self.size / 2, self.y - self.size / 2),  # Left wing
                        (self.x + self.size / 3, self.y),  # Body
                        (self.x + self.size / 2, self.y + self.size / 2)   # Right wing
                    ]
            else:  # Vertical movement
                if self.direction[1] < 0:  # Up
                    points = [
                        (self.x, self.y - self.size),  # Nose
                        (self.x - self.size / 2, self.y + self.size / 2),  # Left wing
                        (self.x, self.y + self.size / 3),  # Body
                        (self.x + self.size / 2, self.y + self.size / 2)   # Right wing
                    ]
                else:  # Down
                    points = [
                        (self.x, self.y + self.size),  # Nose
                        (self.x - self.size / 2, self.y - self.size / 2),  # Left wing
                        (self.x, self.y - self.size / 3),  # Body
                        (self.x + self.size / 2, self.y - self.size / 2)   # Right wing
                    ]
            
            # Draw the ship
            pygame.draw.polygon(surface, self.color, points)
            
            # Add a highlight to the ship
            highlight_color = tuple(min(c + 50, 255) for c in self.color)
            highlight_points = []
            
            # Calculate highlight based on the ship's shape (smaller version of the ship)
            center_x, center_y = sum(x for x, _ in points) / len(points), sum(y for _, y in points) / len(points)
            
            for px, py in points:
                # Move points 30% closer to center for highlight
                hx = px * 0.7 + center_x * 0.3
                hy = py * 0.7 + center_y * 0.3
                highlight_points.append((hx, hy))
            
            pygame.draw.polygon(surface, highlight_color, highlight_points)
    
    def take_damage(self, particles: ParticleSystem):
        """Handle player taking damage."""
        if self.invulnerable:
            return False
        
        self.health -= 1
        self.invulnerable = True
        self.invulnerable_time = 2.0  # 2 seconds of invulnerability
        
        # Add particles for damage effect
        particles.add_explosion(
            self.x, self.y, 
            (255, 100, 100),  # Red color for damage
            particle_count=40, 
            speed_min=3, speed_max=8,
            lifetime_min=20, lifetime_max=40
        )
        
        return self.health <= 0  # Return True if player died

class BackgroundEffect:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.stars = []
        self.grid_offset = 0
        self.grid_speed = 0.5
        self.generate_stars(100)
    
    def generate_stars(self, count: int):
        for _ in range(count):
            self.stars.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.uniform(0.5, 2.5),
                'brightness': random.uniform(0.3, 1.0),
                'speed': random.uniform(0.1, 0.5)
            })
    
    def update(self, delta_time: float, intensity: float = 1.0):
        # Update stars
        for star in self.stars:
            star['y'] += star['speed'] * intensity
            if star['y'] > self.height:
                star['y'] = 0
                star['x'] = random.randint(0, self.width)
        
        # Update grid
        self.grid_offset = (self.grid_offset + self.grid_speed * intensity) % 40
    
    def draw(self, surface: pygame.Surface):
        # Draw backdrop
        surface.fill(GAME_CONSTANTS['COLORS']['background'])
        
        # Draw stars
        for star in self.stars:
            brightness = int(255 * star['brightness'])
            color = (brightness, brightness, brightness)
            
            pygame.draw.circle(
                surface, color, 
                (int(star['x']), int(star['y'])), 
                star['size']
            )
        
        # Draw grid
        grid_color = GAME_CONSTANTS['COLORS']['grid']
        offset = int(self.grid_offset)
        
        # Vertical grid lines
        for x in range(-offset, self.width, 40):
            pygame.draw.line(
                surface, grid_color, 
                (x, 0), (x, self.height)
            )
        
        # Horizontal grid lines
        for y in range(-offset, self.height, 40):
            pygame.draw.line(
                surface, grid_color, 
                (0, y), (self.width, y)
            )

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.music_playing = False
        
        # Try to load sounds - gracefully fail if files not found
        try:
            self.load_sounds()
        except:
            print("Warning: Could not load some sound files.")
    
    def load_sounds(self):
        # Define sound files to load
        sound_files = {
            'shoot': 'sounds/shoot.wav',
            'enemy_hit': 'sounds/enemy_hit.wav',
            'enemy_explode': 'sounds/enemy_explode.wav',
            'player_hit': 'sounds/player_hit.wav',
            'correct': 'sounds/correct.wav',
            'incorrect': 'sounds/incorrect.wav',
            'level_up': 'sounds/level_up.wav',
            'game_over': 'sounds/game_over.wav',
            'button_hover': 'sounds/button_hover.wav',
            'button_click': 'sounds/button_click.wav'
        }
        
        # Create sounds directory if it doesn't exist
        Path("sounds").mkdir(exist_ok=True)
        
        # Load available sounds
        for name, path in sound_files.items():
            if Path(path).exists():
                self.sounds[name] = pygame.mixer.Sound(path)
            else:
                self.sounds[name] = None
    
    def play(self, sound_name: str, volume: float = 1.0):
        if sound_name in self.sounds and self.sounds[sound_name]:
            self.sounds[sound_name].set_volume(volume)
            self.sounds[sound_name].play()
    
    def play_music(self, music_file: str, volume: float = 0.5, loop: bool = True):
        if Path(music_file).exists():
            try:
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1 if loop else 0)
                self.music_playing = True
            except:
                print(f"Warning: Could not play music file {music_file}")
    
    def stop_music(self):
        pygame.mixer.music.stop()
        self.music_playing = False

class GameState:
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    LEVEL_TRANSITION = 4

class Game:
    def __init__(self, display_surface: pygame.Surface):
        self.display_surface = display_surface
        self.width = GAME_CONSTANTS['WINDOW_WIDTH']
        self.height = GAME_CONSTANTS['WINDOW_HEIGHT']
        
        # Game state
        self.state = GameState.MENU
        self.clock = pygame.time.Clock()
        self.delta_time = 0
        self.score = 0
        self.high_score = 0
        self.level = 1
        self.streak = 0
        self.enemies_killed = 0
        self.total_enemies_killed = 0
        self.state_timer = 0
        
        # Initialize game components
        self.background = BackgroundEffect(self.width, self.height)
        self.particles = ParticleSystem()
        self.player = Player(self.width // 2, self.height // 2)
        self.bullets = []
        self.enemies = []
        self.current_problem = None
        self.answer_buttons = []
        
        # UI elements
        self.menu_buttons = []
        self.pause_buttons = []
        self.create_menu_buttons()
        self.create_pause_buttons()
        
        # Initialize sound manager
        self.sound_manager = SoundManager()
        
        # Start with a new problem
        self.create_new_problem()
        self.spawn_enemies()
        
        # Load high score if available
        self.load_high_score()
    
    def create_menu_buttons(self):
        button_width = 200
        button_height = 60
        start_y = self.height // 2 - 50
        
        # Start Game button
        self.menu_buttons.append(
            Button(
                (self.width - button_width) // 2,
                start_y,
                button_width, button_height,
                "Start Game",
                GAME_CONSTANTS['COLORS']['button']['default']
            )
        )
        
        # Quit button
        self.menu_buttons.append(
            Button(
                (self.width - button_width) // 2,
                start_y + button_height + 30,
                button_width, button_height,
                "Quit",
                GAME_CONSTANTS['COLORS']['button']['default']
            )
        )
    
    def create_pause_buttons(self):
        button_width = 200
        button_height = 60
        start_y = self.height // 2 - 50
        
        # Resume button
        self.pause_buttons.append(
            Button(
                (self.width - button_width) // 2,
                start_y,
                button_width, button_height,
                "Resume",
                GAME_CONSTANTS['COLORS']['button']['default']
            )
        )
        
        # Quit to Menu button
        self.pause_buttons.append(
            Button(
                (self.width - button_width) // 2,
                start_y + button_height + 30,
                button_width, button_height,
                "Quit to Menu",
                GAME_CONSTANTS['COLORS']['button']['default']
            )
        )
    
    def create_new_problem(self):
        """Create a new math problem and answer buttons."""
        self.current_problem = Problem(min(15, max(1, self.level)))
        self.create_answer_buttons()
    
    def create_answer_buttons(self):
        correct_answer = self.current_problem.correct_answer
        wrong_answers = self.current_problem.generate_wrong_answers(3)
        answers = wrong_answers + [correct_answer]
        random.shuffle(answers)
        
        self.answer_buttons = []
        button_width = 150
        button_height = 60
        spacing = 20
        total_width = (button_width + spacing) * len(answers) - spacing
        start_x = (self.width - total_width) // 2
        
        for i, answer in enumerate(answers):
            x = start_x + (button_width + spacing) * i
            button = Button(
                x, self.height - 100, 
                button_width, button_height, 
                str(answer) if isinstance(answer, int) else f"{answer:.2f}".rstrip('0').rstrip('.'),
                GAME_CONSTANTS['COLORS']['button']['default']
            )
            self.answer_buttons.append((button, answer == correct_answer))
    
    def spawn_enemies(self):
        """Spawn enemies based on current level."""
        # Determine how many enemies to spawn
        enemy_count = min(3 + self.level // 2, 10)
        
        # Clear existing enemies
        self.enemies = []
        
        # Ensure enemies don't spawn too close to the player
        player_safe_zone = 150
        
        for _ in range(enemy_count):
            # Find a spawn position away from the player
            while True:
                x = random.randint(50, self.width - 50)
                y = random.randint(50, self.height - 180)  # Keep away from UI elements
                
                # Check distance from player
                dist_to_player = math.sqrt((x - self.player.x) ** 2 + (y - self.player.y) ** 2)
                if dist_to_player > player_safe_zone:
                    break
            
            # Create enemy with properties based on level
            enemy = Enemy(x, y, difficulty=self.level)
            self.enemies.append(enemy)
    
    def handle_input(self):
        """Process user input based on current game state."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]  # Left mouse button
        
        if self.state == GameState.MENU:
            # Update menu buttons
            for i, button in enumerate(self.menu_buttons):
                if button.update(mouse_pos, mouse_pressed):
                    self.sound_manager.play('button_click')
                    if i == 0:  # Start Game
                        self.state = GameState.PLAYING
                        self.reset_game()
                    elif i == 1:  # Quit
                        pygame.quit()
                        sys.exit()
        
        elif self.state == GameState.PAUSED:
            # Update pause menu buttons
            for i, button in enumerate(self.pause_buttons):
                if button.update(mouse_pos, mouse_pressed):
                    self.sound_manager.play('button_click')
                    if i == 0:  # Resume
                        self.state = GameState.PLAYING
                    elif i == 1:  # Quit to Menu
                        self.state = GameState.MENU
                        if self.score > self.high_score:
                            self.high_score = self.score
                            self.save_high_score()
        
        elif self.state == GameState.PLAYING:
            # Check for pause key
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                self.state = GameState.PAUSED
            
            # Update answer buttons
            for button, is_correct in self.answer_buttons:
                if button.update(mouse_pos, mouse_pressed):
                    self.sound_manager.play('button_click')
                    self.handle_answer(button, is_correct)
    
    def update(self):
        """Update game state."""
        # Calculate delta time
        self.delta_time = self.clock.get_time() / 1000.0  # Convert milliseconds to seconds
        
        # Update background regardless of game state
        self.background.update(self.delta_time, 1.0 if self.state == GameState.PLAYING else 0.2)
        
        # Update particles
        self.particles.update()
        
        if self.state == GameState.PLAYING:
            # Update player and handle shooting
            new_bullet = self.player.update(self.delta_time, pygame.key.get_pressed(), self.particles)
            if new_bullet:
                self.bullets.append(new_bullet)
                self.sound_manager.play('shoot', 0.3)
            
            # Update bullets
            for bullet in self.bullets:
                bullet.update(self.particles)
            
            # Remove inactive bullets
            self.bullets = [b for b in self.bullets if b.active]
            
            # Update enemies
            for enemy in self.enemies:
                enemy.update(self.delta_time)
            
            # Check collisions
            self.check_collisions()
            
            # Check if level is complete (all enemies defeated)
            if not self.enemies and self.state_timer <= 0:
                self.level_complete()
        
        elif self.state == GameState.LEVEL_TRANSITION:
            # Update state timer for level transition
            self.state_timer -= self.delta_time
            if self.state_timer <= 0:
                self.state = GameState.PLAYING
                self.create_new_problem()
                self.spawn_enemies()
        
        elif self.state == GameState.GAME_OVER:
            # Update state timer for game over screen
            self.state_timer -= self.delta_time
            if self.state_timer <= 0 and pygame.key.get_pressed()[pygame.K_SPACE]:
                self.state = GameState.MENU
    
    def check_collisions(self):
        """Check for collisions between game objects."""
        # Bullet-Enemy collisions
        for bullet in self.bullets:
            if not bullet.active:
                continue
                
            bullet_rect = pygame.Rect(
                bullet.x - bullet.size, bullet.y - bullet.size,
                bullet.size * 2, bullet.size * 2
            )
            
            for enemy in self.enemies:
                if not enemy.is_alive:
                    continue
                    
                enemy_rect = pygame.Rect(
                    enemy.x - enemy.size, enemy.y - enemy.size,
                    enemy.size * 2, enemy.size * 2
                )
                
                if bullet_rect.colliderect(enemy_rect):
                    # Hit enemy
                    enemy_killed = enemy.hit(self.particles)
                    bullet.active = False
                    
                    self.sound_manager.play('enemy_hit', 0.5)
                    
                    if enemy_killed:
                        self.sound_manager.play('enemy_explode', 0.7)
                        self.score += 10 * self.level
                        self.enemies_killed += 1
                        self.total_enemies_killed += 1
                    break
        
        # Player-Enemy collisions
        player_rect = pygame.Rect(
            self.player.x - self.player.size // 2, 
            self.player.y - self.player.size // 2,
            self.player.size, self.player.size
        )
        
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue
                
            enemy_rect = pygame.Rect(
                enemy.x - enemy.size * 0.7, 
                enemy.y - enemy.size * 0.7,
                enemy.size * 1.4, enemy.size * 1.4
            )
            
            if player_rect.colliderect(enemy_rect):
                # Player hit enemy
                player_died = self.player.take_damage(self.particles)
                enemy.hit(self.particles)
                
                self.sound_manager.play('player_hit', 0.8)
                
                if player_died:
                    self.game_over()
                break
        
        # Remove dead enemies
        self.enemies = [e for e in self.enemies if e.is_alive]
    
    def handle_answer(self, button, is_correct):
        """Process player's answer to the current problem."""
        if is_correct:
            self.score += 50 * self.level
            self.streak += 1
            button.color = GAME_CONSTANTS['COLORS']['button']['correct']
            self.particles.add_explosion(
                button.rect.centerx, button.rect.centery,
                GAME_CONSTANTS['COLORS']['success'],
                particle_count=30
            )
            self.sound_manager.play('correct', 0.7)
            
            # Add a multiplier for consecutive correct answers
            if self.streak > 1:
                streak_bonus = 25 * self.streak
                self.score += streak_bonus
            
            # Clear all enemies as a reward for correct answer!
            for enemy in self.enemies:
                if enemy.is_alive:
                    enemy.hit(self.particles)
                    self.score += 5 * self.level
            
            self.enemies = []
            
            # Increase difficulty/level every 3 correct answers
            if self.streak % 3 == 0:
                self.level_up()
        else:
            self.streak = 0
            button.color = GAME_CONSTANTS['COLORS']['button']['incorrect']
            self.particles.add_explosion(
                button.rect.centerx, button.rect.centery,
                GAME_CONSTANTS['COLORS']['error'],
                particle_count=20
            )
            self.sound_manager.play('incorrect', 0.5)
        
        # Short delay before creating a new problem
        self.state_timer = 0.8
        self.state = GameState.LEVEL_TRANSITION
    
    def level_up(self):
        """Increase game level and difficulty."""
        self.level += 1
        self.sound_manager.play('level_up', 0.8)
        
        # Add particles for level up celebration
        for _ in range(8):
            self.particles.add_explosion(
                random.randint(0, self.width),
                random.randint(0, self.height // 2),
                GAME_CONSTANTS['COLORS']['success'],
                particle_count=20
            )
    
    def level_complete(self):
        """Handle level completion."""
        self.state_timer = 1.0
        self.state = GameState.LEVEL_TRANSITION
    
    def game_over(self):
        """Handle game over state."""
        self.state = GameState.GAME_OVER
        self.state_timer = 3.0
        self.sound_manager.play('game_over', 0.9)
        
        # Update high score
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
    
    def reset_game(self):
        """Reset game to initial state."""
        self.score = 0
        self.level = 1
        self.streak = 0
        self.enemies_killed = 0
        self.player = Player(self.width // 2, self.height // 2)
        self.bullets = []
        self.create_new_problem()
        self.spawn_enemies()
    
    def draw(self):
        """Render the current game state."""
        # Draw background
        self.background.draw(self.display_surface)
        
        if self.state == GameState.MENU:
            self.draw_menu()
        
        elif self.state == GameState.PLAYING or self.state == GameState.LEVEL_TRANSITION:
            self.draw_game()
            
            # Draw problem and answers
            self.draw_problem()
            
            # Draw UI elements
            self.draw_ui()
        
        elif self.state == GameState.PAUSED:
            # Draw the game in the background
            self.draw_game()
            
            # Draw semi-transparent overlay
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 30, 180))
            self.display_surface.blit(overlay, (0, 0))
            
            # Draw pause menu
            self.draw_pause_menu()
        
        elif self.state == GameState.GAME_OVER:
            # Draw the game in the background
            self.draw_game()
            
            # Draw game over screen
            self.draw_game_over()
        
        # Always draw particles on top
        self.particles.draw(self.display_surface)
    
    def draw_menu(self):
        """Draw the main menu screen."""
        # Draw title
        title_font = pygame.font.Font(None, 80)
        title_text = title_font.render("Math Blaster", True, GAME_CONSTANTS['COLORS']['primary'])
        title_rect = title_text.get_rect(center=(self.width // 2, 150))
        self.display_surface.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_font = pygame.font.Font(None, 40)
        subtitle_text = subtitle_font.render("Learn Math While Destroying Enemies!", True, 
                                           GAME_CONSTANTS['COLORS']['text']['light'])
        subtitle_rect = subtitle_text.get_rect(center=(self.width // 2, 220))
        self.display_surface.blit(subtitle_text, subtitle_rect)
        
        # Draw high score
        if self.high_score > 0:
            score_font = pygame.font.Font(None, 36)
            score_text = score_font.render(f"High Score: {self.high_score}", True, 
                                         GAME_CONSTANTS['COLORS']['text']['highlight'])
            score_rect = score_text.get_rect(center=(self.width // 2, 280))
            self.display_surface.blit(score_text, score_rect)
        
        # Draw buttons
        for button in self.menu_buttons:
            button.draw(self.display_surface)
        
        # Draw instructions
        instructions_font = pygame.font.Font(None, 24)
        instructions = [
            "ARROW KEYS or WASD - Move ship",
            "SPACE - Shoot",
            "ESC - Pause game",
            "Solve math problems to progress!",
            "Destroy enemies for bonus points!"
        ]
        
        for i, instruction in enumerate(instructions):
            instr_text = instructions_font.render(instruction, True, 
                                                GAME_CONSTANTS['COLORS']['text']['light'])
            instr_rect = instr_text.get_rect(center=(self.width // 2, 400 + i * 30))
            self.display_surface.blit(instr_text, instr_rect)
    
    def draw_game(self):
        """Draw the main gameplay elements."""
        # Draw player
        self.player.draw(self.display_surface)
        
        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(self.display_surface)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.display_surface)
    
    def draw_problem(self):
        """Draw the current math problem and answer buttons."""
        # Draw problem inside a nice container
        problem_font = pygame.font.Font(None, 48)
        problem_text = problem_font.render(self.current_problem.problem_text, True, 
                                         GAME_CONSTANTS['COLORS']['text']['highlight'])
        
        # Create a background for the problem
        padding = 20
        box_width = problem_text.get_width() + padding * 2
        box_height = problem_text.get_height() + padding * 2
        box_rect = pygame.Rect(
            (self.width - box_width) // 2,
            40,
            box_width,
            box_height
        )
        
        # Draw box with a nice gradient
        s = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(s, (40, 60, 100, 180), (0, 0, box_width, box_height), border_radius=10)
        self.display_surface.blit(s, box_rect)
        
        # Add a subtle border
        pygame.draw.rect(self.display_surface, GAME_CONSTANTS['COLORS']['primary'], 
                       box_rect, 2, border_radius=10)
        
        # Draw problem text
        problem_rect = problem_text.get_rect(center=box_rect.center)
        self.display_surface.blit(problem_text, problem_rect)
        
        # Draw answer buttons
        for button, _ in self.answer_buttons:
            button.draw(self.display_surface)
    
    def draw_ui(self):
        """Draw UI elements like score, health, etc."""
        # Draw score
        score_font = pygame.font.Font(None, 36)
        score_text = score_font.render(f"Score: {self.score}", True, 
                                     GAME_CONSTANTS['COLORS']['text']['light'])
        self.display_surface.blit(score_text, (20, 20))
        
        # Draw level
        level_text = score_font.render(f"Level: {self.level}", True, 
                                     GAME_CONSTANTS['COLORS']['text']['light'])
        level_rect = level_text.get_rect(topright=(self.width - 20, 20))
        self.display_surface.blit(level_text, level_rect)
        
        # Draw streak
        if self.streak > 1:
            streak_text = score_font.render(f"Streak: {self.streak}x", True, 
                                          GAME_CONSTANTS['COLORS']['success'])
            streak_rect = streak_text.get_rect(midtop=(self.width // 2, 120))
            self.display_surface.blit(streak_text, streak_rect)
        
        # Draw health
        health_text = score_font.render(f"Health: ", True, 
                                      GAME_CONSTANTS['COLORS']['text']['light'])
        self.display_surface.blit(health_text, (20, 60))
        
        # Draw health icons
        heart_size = 24
        for i in range(self.player.max_health):
            if i < self.player.health:
                color = (255, 60, 80)  # Red for active health
            else:
                color = (100, 30, 40)  # Dark red for lost health
            
            pygame.draw.polygon(self.display_surface, color, [
                (130 + i * 35, 72),  # Top
                (120 + i * 35, 60),  # Left bump
                (110 + i * 35, 72),  # Middle dip
                (100 + i * 35, 60),  # Right bump
                (90 + i * 35, 72),   # Bottom
                (110 + i * 35, 85)   # Tip
            ])
    
    def draw_pause_menu(self):
        """Draw the pause menu."""
        # Draw "PAUSED" text
        pause_font = pygame.font.Font(None, 80)
        pause_text = pause_font.render("PAUSED", True, GAME_CONSTANTS['COLORS']['text']['light'])
        pause_rect = pause_text.get_rect(center=(self.width // 2, 150))
        self.display_surface.blit(pause_text, pause_rect)
        
        # Draw buttons
        for button in self.pause_buttons:
            button.draw(self.display_surface)
        
        # Draw current score
        score_font = pygame.font.Font(None, 40)
        score_text = score_font.render(f"Score: {self.score}", True, 
                                     GAME_CONSTANTS['COLORS']['text']['light'])
        score_rect = score_text.get_rect(center=(self.width // 2, 250))
        self.display_surface.blit(score_text, score_rect)
    
    def draw_game_over(self):
        """Draw the game over screen."""
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.display_surface.blit(overlay, (0, 0))
        
        # Draw "GAME OVER" text
        game_over_font = pygame.font.Font(None, 80)
        game_over_text = game_over_font.render("GAME OVER", True, 
                                             GAME_CONSTANTS['COLORS']['error'])
        game_over_rect = game_over_text.get_rect(center=(self.width // 2, 200))
        self.display_surface.blit(game_over_text, game_over_rect)
        
        # Draw final score
        score_font = pygame.font.Font(None, 60)
        final_score_text = score_font.render(f"Final Score: {self.score}", True, 
                                           GAME_CONSTANTS['COLORS']['text']['light'])
        final_score_rect = final_score_text.get_rect(center=(self.width // 2, 280))
        self.display_surface.blit(final_score_text, final_score_rect)
        
        # Draw high score
        high_score_text = score_font.render(f"High Score: {self.high_score}", True, 
                                          GAME_CONSTANTS['COLORS']['text']['highlight'])
        high_score_rect = high_score_text.get_rect(center=(self.width // 2, 340))
        self.display_surface.blit(high_score_text, high_score_rect)
        
        # Draw enemies defeated
        enemies_font = pygame.font.Font(None, 40)
        enemies_text = enemies_font.render(f"Enemies Defeated: {self.total_enemies_killed}", True, 
                                         GAME_CONSTANTS['COLORS']['text']['light'])
        enemies_rect = enemies_text.get_rect(center=(self.width // 2, 400))
        self.display_surface.blit(enemies_text, enemies_rect)
        
        # Draw level reached
        level_text = enemies_font.render(f"Level Reached: {self.level}", True, 
                                       GAME_CONSTANTS['COLORS']['text']['light'])
        level_rect = level_text.get_rect(center=(self.width // 2, 440))
        self.display_surface.blit(level_text, level_rect)
        
        # Draw continue instruction
        if self.state_timer <= 0:
            continue_font = pygame.font.Font(None, 36)
            continue_text = continue_font.render("Press SPACE to continue", True, 
                                               (255, 255, 255, int(abs(math.sin(pygame.time.get_ticks() / 500) * 255))))
            continue_rect = continue_text.get_rect(center=(self.width // 2, 520))
            self.display_surface.blit(continue_text, continue_rect)
    
    def load_high_score(self):
        """Load high score from file."""
        try:
            score_file = Path("high_score.txt")
            if score_file.exists():
                with open(score_file, "r") as f:
                    self.high_score = int(f.read().strip())
        except:
            self.high_score = 0
    
    def save_high_score(self):
        """Save high score to file."""
        try:
            with open("high_score.txt", "w") as f:
                f.write(str(self.high_score))
        except:
            print("Warning: Could not save high score.")

def main():
    # Initialize display and clock
    DISPLAY_SURF = pygame.display.set_mode((GAME_CONSTANTS['WINDOW_WIDTH'], 
                                          GAME_CONSTANTS['WINDOW_HEIGHT']))
    pygame.display.set_caption('Advanced Math Learning Game')
    
    # Create game instance
    game = Game(DISPLAY_SURF)
    
    # Main game loop
    while True:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Handle input, update, and render
        game.handle_input()
        game.update()
        game.draw()
        
        # Update display and tick clock
        pygame.display.update()
        game.clock.tick(GAME_CONSTANTS['FPS'])

if __name__ == '__main__':
    main()
