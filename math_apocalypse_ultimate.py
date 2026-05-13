"""
MATH APOCALYPSE: DIMENSIONAL FLIP - ULTIMATE EDITION
======================================================
All 7 Chaos Systems Implemented:
1. Question Blocks with Math Power-ups
2. Differential Equation Boss Fights
3. Mandelbrot Skill Tree
4. Polar Coordinate View Toggle
5. Math Melody Music System
6. JSON Save/Load Progression
7. Advanced Terrain Types (Exp, Log, Tan, Hyperbola, Cycloid, Rose)

INSTALL:
    pip install pygame numpy sympy

RUN:
    python math_apocalypse_ultimate.py
"""

import pygame
import random
import sys
import math
import json
import os
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass, field
from enum import Enum, auto

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("WARNING: numpy not installed. Sound and Mandelbrot will be limited.")

try:
    import sympy as sp
    from sympy import symbols, diff, integrate, sin, cos, tan, exp, log, sqrt, pi, E, oo, latex, simplify
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False
    print("WARNING: sympy not installed. Advanced math problems limited.")

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2)

# =============================================================================
# CONFIGURATION
# =============================================================================
@dataclass
class Config:
    WIDTH: int = 1200
    HEIGHT: int = 800
    FPS: int = 60
    BG: Tuple[int,int,int] = (5, 5, 10)
    GREEN: Tuple[int,int,int] = (0, 255, 128)
    DIM: Tuple[int,int,int] = (0, 100, 50)
    BRIGHT: Tuple[int,int,int] = (128, 255, 200)
    RED: Tuple[int,int,int] = (255, 50, 80)
    GOLD: Tuple[int,int,int] = (255, 200, 50)
    CYAN: Tuple[int,int,int] = (0, 200, 255)
    PURPLE: Tuple[int,int,int] = (200, 50, 255)
    WHITE: Tuple[int,int,int] = (240, 240, 240)
    PLAYER_SPEED: float = 6.0
    BULLET_SPEED: float = 12.0
    GRAVITY: float = 0.6
    JUMP: float = -14.0
    SAVE_FILE: str = "math_apocalypse_save.json"

CFG = Config()

# =============================================================================
# AUDIO ENGINE (System 5: Math Melody)
# =============================================================================
class AudioEngine:
    def __init__(self):
        self.sample_rate = 44100
        # C major pentatonic - sounds good in any order
        self.scale = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25]
        self.melody_idx = 0
        self.sounds = {}
        if NUMPY_AVAILABLE:
            self._generate_sounds()

    def _generate_sounds(self):
        # Correct notes
        duration = 0.15
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        for i, freq in enumerate(self.scale):
            wave = 0.3 * np.sin(2 * np.pi * freq * t)
            wave *= np.linspace(1, 0, len(wave))  # fade out
            stereo = np.column_stack((wave, wave))
            sound = pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))
            self.sounds[f"note_{i}"] = sound

        # Wrong sound (dissonant beat)
        wave = 0.3 * (np.sin(2 * np.pi * 150 * t) + np.sin(2 * np.pi * 165 * t))
        wave *= np.linspace(1, 0, len(wave))
        stereo = np.column_stack((wave, wave))
        self.sounds["wrong"] = pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))

        # Jump (sweep up)
        freq_sweep = np.linspace(200, 450, len(t))
        wave = 0.2 * np.sin(2 * np.pi * freq_sweep * t)
        stereo = np.column_stack((wave, wave))
        self.sounds["jump"] = pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))

        # Shoot (short blip)
        t_short = np.linspace(0, 0.05, int(self.sample_rate * 0.05), False)
        wave = 0.25 * np.sin(2 * np.pi * 900 * t_short)
        stereo = np.column_stack((wave, wave))
        self.sounds["shoot"] = pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))

        # Flip (epic chord)
        chord_freqs = [261.63, 329.63, 392.00, 523.25]
        t_long = np.linspace(0, 0.8, int(self.sample_rate * 0.8), False)
        wave = np.zeros_like(t_long)
        for f in chord_freqs:
            wave += 0.12 * np.sin(2 * np.pi * f * t_long)
        wave *= np.linspace(1, 0, len(wave))
        stereo = np.column_stack((wave, wave))
        self.sounds["flip"] = pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def play_correct(self):
        note = f"note_{self.melody_idx % len(self.scale)}"
        self.play(note)
        self.melody_idx += 1

    def play_wrong(self):
        self.play("wrong")
        self.melody_idx = 0  # Reset melody

    def play_jump(self):
        self.play("jump")

    def play_shoot(self):
        self.play("shoot")

    def play_flip(self):
        self.play("flip")

# =============================================================================
# SAVE MANAGER (System 6)
# =============================================================================
class SaveManager:
    @staticmethod
    def default():
        return {
            "high_score": 0,
            "total_correct": 0,
            "skill_points": 0,
            "unlocked_skills": [],
            "max_level": 1,
            "flip_seen": False,
            "play_time": 0,
            "bosses_defeated": 0
        }

    @staticmethod
    def save(data: dict):
        try:
            with open(CFG.SAVE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Save failed: {e}")

    @staticmethod
    def load() -> dict:
        if os.path.exists(CFG.SAVE_FILE):
            try:
                with open(CFG.SAVE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Load failed: {e}")
        return SaveManager.default()

# =============================================================================
# MATH ENGINE
# =============================================================================
class MathEngine:
    def __init__(self):
        self.x = symbols('x') if SYMPY_AVAILABLE else None

    def generate(self, difficulty: int) -> dict:
        tier = min(difficulty, 10)
        if tier <= 2:
            return self._arithmetic(tier)
        elif tier <= 4:
            return self._algebra(tier)
        elif tier <= 6:
            return self._trig(tier)
        elif tier <= 8:
            return self._calc1(tier)
        else:
            return self._calc2(tier)

    def _arithmetic(self, d):
        a, b = random.randint(1, 10*d), random.randint(1, 10*d)
        op = random.choice(['+', '-', '*'])
        q = f"{a} {op} {b}"
        ans = eval(f"{a}{op}{b}")
        wrong = [ans+random.randint(1,10), ans-random.randint(1,10), ans*2]
        return self._pack(q, ans, wrong, "Arithmetic")

    def _algebra(self, d):
        a = random.randint(2, 3*d)
        b = random.randint(1, 5*d)
        c = a * random.randint(2, 4*d) + b
        q = f"Solve: {a}x + {b} = {c}"
        ans = (c - b) // a
        wrong = [ans+1, ans-1, ans+2]
        return self._pack(q, ans, wrong, "Algebra")

    def _trig(self, d):
        angles = {0: 0, 30: 0.5, 45: "√2/2", 60: "√3/2", 90: 1}
        ang = random.choice(list(angles.keys()))
        q = f"sin({ang}°) = ?"
        ans = angles[ang]
        wrong = [0, 0.5, 1, -1]
        return self._pack(q, ans, wrong, "Trig")

    def _calc1(self, d):
        funcs = [("x²", "2x"), ("x³", "3x²"), ("sin(x)", "cos(x)"), ("cos(x)", "-sin(x)")]
        f, der = random.choice(funcs)
        q = f"d/dx [{f}] = ?"
        wrong = ["x", "1", "0"]
        return self._pack(q, der, wrong, "Derivative")

    def _calc2(self, d):
        q = "∫ 2x dx = ?"
        ans = "x² + C"
        wrong = ["2x² + C", "x + C", "2 + C"]
        return self._pack(q, ans, wrong, "Integral")

    def _pack(self, q, ans, wrong, cat):
        opts = [ans] + wrong[:3]
        random.shuffle(opts)
        return {"q": q, "a": ans, "opts": opts, "cat": cat}

# =============================================================================
# PARTICLES
# =============================================================================
class Particle:
    def __init__(self, x, y, vx, vy, color, life=60, size=4):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color
        self.gravity = 0.15

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1
        self.size = max(0.5, self.size * 0.98)

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = int((self.life / self.max_life) * 255)
        s = max(1, int(self.size * (self.life / self.max_life)))
        glow = pygame.Surface((s*4, s*4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color[:3], alpha//3), (s*2, s*2), s*2)
        surf.blit(glow, (int(self.x-s*2), int(self.y-s*2)))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), s)

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn(self, x, y, count, color, speed):
        for _ in range(count):
            a = random.uniform(0, 2*math.pi)
            s = random.uniform(1, speed)
            self.particles.append(Particle(x, y, math.cos(a)*s, math.sin(a)*s-2, color))

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surf):
        for p in self.particles:
            p.draw(surf)

# =============================================================================
# SCREEN EFFECTS
# =============================================================================
class ScreenEffects:
    def __init__(self):
        self.shake_x = self.shake_y = 0
        self.glitch = 0

    def shake(self, amt=10):
        self.shake_x = random.uniform(-amt, amt)
        self.shake_y = random.uniform(-amt, amt)

    def glitch_fx(self, dur=10):
        self.glitch = dur

    def update(self):
        self.shake_x *= 0.9
        self.shake_y *= 0.9
        if self.glitch > 0:
            self.glitch -= 1

    def apply(self, surf):
        if abs(self.shake_x) > 0.5 or abs(self.shake_y) > 0.5:
            shaken = pygame.Surface((CFG.WIDTH, CFG.HEIGHT), pygame.SRCALPHA)
            shaken.blit(surf, (int(self.shake_x), int(self.shake_y)))
            surf = shaken
        # Scanlines
        for y in range(0, CFG.HEIGHT, 4):
            pygame.draw.line(surf, (0,0,0,30), (0,y), (CFG.WIDTH,y))
        # Vignette
        v = pygame.Surface((CFG.WIDTH, CFG.HEIGHT), pygame.SRCALPHA)
        for r in range(max(CFG.WIDTH, CFG.HEIGHT)//2, 0, -30):
            a = int(25 * (r / (max(CFG.WIDTH, CFG.HEIGHT)//2)))
            pygame.draw.rect(v, (0,0,0,a), (0,0,CFG.WIDTH,CFG.HEIGHT), border_radius=r)
        surf.blit(v, (0,0))
        # Glitch strips
        if self.glitch > 0:
            for _ in range(3):
                y = random.randint(0, CFG.HEIGHT-20)
                h = random.randint(5, 20)
                o = random.randint(-40, 40)
                strip = surf.subsurface((0,y,CFG.WIDTH,h)).copy()
                surf.blit(strip, (o,y))
        return surf

# =============================================================================
# SKILL TREE (System 3: Mandelbrot)
# =============================================================================
class SkillTree:
    SKILLS = {
        "double_jump": {"name": "Double Jump", "cost": 3, "desc": "Jump twice!", "pos": (0.35, 0.3), "color": CFG.CYAN},
        "taylor_jump": {"name": "Taylor Jump", "cost": 5, "desc": "Higher jumps", "pos": (0.65, 0.25), "color": CFG.GOLD},
        "prime_gun": {"name": "Prime Gun", "cost": 4, "desc": "Factor shots", "pos": (0.5, 0.5), "color": CFG.RED},
        "lhospital": {"name": "L'Hôpital Rush", "cost": 6, "desc": "Death save", "pos": (0.2, 0.6), "color": CFG.PURPLE},
        "fourier": {"name": "Fourier Vision", "cost": 4, "desc": "See waves", "pos": (0.8, 0.55), "color": CFG.GREEN},
        "extra_hp": {"name": "+1 Heart", "cost": 3, "desc": "More health", "pos": (0.4, 0.75), "color": CFG.RED},
        "fast_shoot": {"name": "Rapid Fire", "cost": 3, "desc": "Shoot faster", "pos": (0.6, 0.75), "color": CFG.GOLD},
        "polar_unlock": {"name": "Polar View", "cost": 2, "desc": "TAB to toggle", "pos": (0.5, 0.15), "color": CFG.CYAN},
    }

    def __init__(self, save_data: dict):
        self.points = save_data.get("skill_points", 0)
        self.unlocked = set(save_data.get("unlocked_skills", []))
        self.fractal = None
        if NUMPY_AVAILABLE:
            self._generate_mandelbrot()

    def _generate_mandelbrot(self, w=800, h=600, max_iter=50):
        y, x = np.ogrid[-1.4:1.4:h*1j, -2.3:0.8:w*1j]
        c = x + y*1j
        z = np.zeros_like(c)
        div_time = np.zeros(c.shape, dtype=int)
        mask = np.ones(c.shape, dtype=bool)

        for i in range(max_iter):
            z[mask] = z[mask]**2 + c[mask]
            diverged = np.abs(z) > 2
            mask[diverged] = False
            div_time[mask] = i

        img = np.zeros((h, w, 3), dtype=np.uint8)
        norm = div_time / max_iter
        img[:,:,0] = (norm * 50).astype(np.uint8)
        img[:,:,1] = (norm * 255).astype(np.uint8)
        img[:,:,2] = (norm * 128).astype(np.uint8)

        self.fractal = pygame.surfarray.make_surface(img)

    def draw(self, surf, font):
        overlay = pygame.Surface((CFG.WIDTH, CFG.HEIGHT))
        overlay.set_alpha(220)
        overlay.fill((0,0,0))
        surf.blit(overlay, (0,0))

        if self.fractal:
            fw, fh = self.fractal.get_size()
            fx = (CFG.WIDTH - fw) // 2
            fy = (CFG.HEIGHT - fh) // 2
            surf.blit(self.fractal, (fx, fy))

        title = font.render("MANDELBROT SKILL TREE", True, CFG.BRIGHT)
        surf.blit(title, (CFG.WIDTH//2 - title.get_width()//2, 20))

        pts = font.render(f"Points: {self.points}", True, CFG.GOLD)
        surf.blit(pts, (20, 20))

        for sid, skill in self.SKILLS.items():
            sx = int(skill["pos"][0] * CFG.WIDTH)
            sy = int(skill["pos"][1] * CFG.HEIGHT)
            unlocked = sid in self.unlocked
            affordable = self.points >= skill["cost"]

            color = skill["color"] if unlocked else (CFG.DIM if not affordable else CFG.WHITE)
            radius = 25 if unlocked else 20

            if not unlocked and affordable:
                glow = pygame.Surface((radius*3, radius*3), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*color[:3], 100), (radius*1.5, radius*1.5), radius*1.5)
                surf.blit(glow, (sx - radius*1.5, sy - radius*1.5))

            pygame.draw.circle(surf, color, (sx, sy), radius)
            pygame.draw.circle(surf, CFG.WHITE, (sx, sy), radius, 2)

            name = font.render(skill["name"], True, CFG.WHITE)
            surf.blit(name, (sx - name.get_width()//2, sy + radius + 5))
            cost = font.render(f"[{skill['cost']}]", True, CFG.GOLD)
            surf.blit(cost, (sx - cost.get_width()//2, sy - radius - 20))

        hint = font.render("Click node to unlock | M to close", True, CFG.DIM)
        surf.blit(hint, (CFG.WIDTH//2 - hint.get_width()//2, CFG.HEIGHT - 40))

    def handle_click(self, pos):
        for sid, skill in self.SKILLS.items():
            if sid in self.unlocked:
                continue
            sx = int(skill["pos"][0] * CFG.WIDTH)
            sy = int(skill["pos"][1] * CFG.HEIGHT)
            if math.hypot(pos[0]-sx, pos[1]-sy) < 30:
                if self.points >= skill["cost"]:
                    self.points -= skill["cost"]
                    self.unlocked.add(sid)
                    return sid
        return None

    def is_unlocked(self, sid):
        return sid in self.unlocked

    def to_dict(self):
        return {"points": self.points, "unlocked": list(self.unlocked)}

# =============================================================================
# TERRAIN (System 7: Advanced Functions)
# =============================================================================
class FunctionTerrain:
    TYPES = ["sin", "cos", "parabola", "exponential", "logarithmic",
             "absolute", "tangent", "hyperbola", "cycloid", "combo", "rose_polar"]

    def __init__(self, ftype="sin", amp=100, freq=0.01, phase=0, vshift=400):
        self.ftype = ftype
        self.amp = amp
        self.freq = freq
        self.phase = phase
        self.vshift = vshift
        self.points = []
        self.derivs = []
        self.generate()

    def generate(self):
        self.points = []
        self.derivs = []
        for x in range(0, CFG.WIDTH + 50, 5):
            y = self.eval(x)
            self.points.append((x, int(y)))
            self.derivs.append((x, self.deriv(x)))

    def eval(self, x):
        if self.ftype == "sin":
            return self.vshift + self.amp * math.sin(self.freq*x + self.phase)
        elif self.ftype == "cos":
            return self.vshift + self.amp * math.cos(self.freq*x + self.phase)
        elif self.ftype == "parabola":
            return self.vshift - self.amp * ((x-600)*self.freq)**2
        elif self.ftype == "exponential":
            val = (x - 400) * self.freq
            if val > 5:
                val = 5
            return self.vshift - self.amp * math.exp(val)
        elif self.ftype == "logarithmic":
            if x > 10:
                return self.vshift - self.amp * math.log(self.freq * x)
            return self.vshift
        elif self.ftype == "absolute":
            return self.vshift - self.amp * abs((x-600)*self.freq)
        elif self.ftype == "tangent":
            val = self.vshift + self.amp * math.tan(self.freq*x + self.phase)
            if abs(val) > 10000 or math.isnan(val) or math.isinf(val):
                return self.vshift
            return val
        elif self.ftype == "hyperbola":
            den = self.freq * x * 0.1
            if den < 0.01:
                return self.vshift
            return self.vshift - self.amp / den
        elif self.ftype == "cycloid":
            t = x * self.freq
            return self.vshift - self.amp * (1 - math.cos(t))
        elif self.ftype == "combo":
            return self.vshift + 0.5*self.amp*math.sin(self.freq*x) + 0.3*self.amp*math.cos(self.freq*2*x)
        elif self.ftype == "rose_polar":
            theta = x * self.freq
            r = self.amp * math.cos(3 * theta)
            return self.vshift + r
        return self.vshift

    def deriv(self, x):
        dx = 0.5
        return (self.eval(x+dx) - self.eval(x-dx)) / (2*dx)

    def get_y(self, x):
        return self.eval(x)

    def draw(self, surf, camera=0, polar=False):
        if polar:
            self._draw_polar(surf, camera)
            return

        pts = [(p[0]-int(camera), p[1]) for p in self.points]
        pts += [(CFG.WIDTH, CFG.HEIGHT), (0, CFG.HEIGHT)]
        if len(pts) > 2:
            glow = pygame.Surface((CFG.WIDTH, CFG.HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(glow, (*CFG.DIM[:3], 40), pts)
            surf.blit(glow, (0,0))

        for i in range(len(self.points)-1):
            x1 = self.points[i][0] - int(camera)
            y1 = self.points[i][1]
            x2 = self.points[i+1][0] - int(camera)
            y2 = self.points[i+1][1]
            slope = abs(self.derivs[i][1])
            color = CFG.RED if slope > 1.5 else (CFG.GOLD if slope > 0.8 else CFG.GREEN)
            pygame.draw.line(surf, color, (x1,y1), (x2,y2), 3)

        f = pygame.font.Font(None, 28)
        surf.blit(f.render(self.eq_text(), True, CFG.BRIGHT), (20, 20))

    def _draw_polar(self, surf, camera):
        cx, cy = CFG.WIDTH//2, CFG.HEIGHT//2
        polar_pts = []
        for x, y in self.points:
            theta = (x - camera) * 0.003
            r = (CFG.HEIGHT - y) * 0.5
            px = cx + r * math.cos(theta)
            py = cy + r * math.sin(theta)
            polar_pts.append((px, py))

        if len(polar_pts) > 1:
            for i in range(len(polar_pts)-1):
                pygame.draw.line(surf, CFG.GREEN, polar_pts[i], polar_pts[i+1], 2)

    def eq_text(self):
        eqs = {
            "sin": f"y = {self.amp:.0f}sin({self.freq:.3f}x)+{self.vshift:.0f}",
            "cos": f"y = {self.amp:.0f}cos({self.freq:.3f}x)+{self.vshift:.0f}",
            "parabola": f"y = -{self.amp:.0f}(({self.freq:.3f}(x-600))²)+{self.vshift:.0f}",
            "exponential": f"y = {self.vshift:.0f} - {self.amp:.0f}e^{self.freq:.3f}(x-400)",
            "logarithmic": f"y = {self.vshift:.0f} - {self.amp:.0f}ln({self.freq:.3f}x)",
            "absolute": f"y = {self.vshift:.0f} - {self.amp:.0f}|{self.freq:.3f}(x-600)|",
            "tangent": f"y = {self.vshift:.0f} + {self.amp:.0f}tan({self.freq:.3f}x)",
            "hyperbola": f"y = {self.vshift:.0f} - {self.amp:.0f}/({self.freq:.3f}x)",
            "cycloid": f"y = cycloid(x)",
            "combo": "y = combo wave",
            "rose_polar": "r = a·cos(3θ)"
        }
        return eqs.get(self.ftype, "y = f(x)")

# =============================================================================
# QUESTION BLOCK (System 1)
# =============================================================================
class QuestionBlock:
    def __init__(self, x, y, problem):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, 44, 44)
        self.active = True
        self.bounce = 0
        self.problem = problem
        self.answered = False
        self.anim = 0

    def hit(self):
        if not self.active or self.answered:
            return None
        self.bounce = 12
        return self.problem

    def update(self):
        self.anim += 0.1
        if self.bounce > 0:
            self.bounce -= 1

    def draw(self, surf, camera):
        if self.answered:
            return
        bx = self.x - int(camera)
        by = self.y - int(self.bounce * 2) + int(math.sin(self.anim) * 3)

        color = CFG.GOLD if self.active else CFG.DIM
        pygame.draw.rect(surf, color, (bx, by, 44, 44), border_radius=4)
        pygame.draw.rect(surf, CFG.WHITE, (bx, by, 44, 44), 2, border_radius=4)

        f = pygame.font.Font(None, 32)
        sym = f.render("∫", True, CFG.BG)
        surf.blit(sym, (bx + 12, by + 8))

class PowerUp:
    TYPES = ["health", "speed", "invincible", "score"]

    def __init__(self, x, y, ptype):
        self.x = x
        self.y = y
        self.type = ptype
        self.vy = -3
        self.life = 300
        self.radius = 12

    def update(self):
        self.y += self.vy
        self.vy += 0.2
        self.life -= 1

    def draw(self, surf, camera):
        if self.life <= 0:
            return
        px = self.x - int(camera)
        colors = {"health": CFG.RED, "speed": CFG.CYAN, "invincible": CFG.GOLD, "score": CFG.PURPLE}
        c = colors.get(self.type, CFG.WHITE)
        pygame.draw.circle(surf, c, (int(px), int(self.y)), self.radius)
        pygame.draw.circle(surf, CFG.WHITE, (int(px), int(self.y)), self.radius, 2)

# =============================================================================
# BOSS (System 2: Differential Equation Boss)
# =============================================================================
class BossProjectile:
    def __init__(self, x, y, vx, vy, ptype="math"):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.type = ptype
        self.life = 300

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.life -= 1

    def draw(self, surf, camera):
        if self.life <= 0:
            return
        px = int(self.x - camera)
        pygame.draw.circle(surf, CFG.RED, (px, int(self.y)), 8)
        f = pygame.font.Font(None, 20)
        t = f.render("∞", True, CFG.WHITE)
        surf.blit(t, (px-4, int(self.y)-8))

class DifferentialBoss:
    PHASES = [
        {"name": "Harmonic Oscillator", "omega": 0.08, "beta": 0.0, "F0": 0, "gamma": 0, "color": CFG.RED},
        {"name": "Damped Vibration", "omega": 0.08, "beta": 0.03, "F0": 0, "gamma": 0, "color": CFG.GOLD},
        {"name": "RESONANCE CHAOS", "omega": 0.08, "beta": 0.01, "F0": 80, "gamma": 0.08, "color": CFG.PURPLE}
    ]

    def __init__(self, level):
        self.level = level
        self.phase_idx = 0
        self.health = 100
        self.max_health = 100
        self.x = CFG.WIDTH // 2
        self.y = 200
        self.vy = 0
        self.time = 0
        self.projectiles = []
        self.shoot_timer = 0
        self.vulnerable = False
        self.vuln_timer = 0
        self.flash = 0

    def current_phase(self):
        idx = min(self.phase_idx, len(self.PHASES)-1)
        return self.PHASES[idx]

    def update(self):
        self.time += 1
        phase = self.current_phase()

        # DE: y'' = -2*beta*y' - omega^2*(y-200) + F0*cos(gamma*time)
        ay = (-2 * phase["beta"] * self.vy
              - phase["omega"]**2 * (self.y - 200)
              + phase["F0"] * math.cos(phase["gamma"] * self.time))

        self.vy += ay * 0.1
        self.y += self.vy
        self.y = max(50, min(CFG.HEIGHT - 200, self.y))

        self.vulnerable = abs(self.vy) < 0.5
        if self.vulnerable:
            self.vuln_timer += 1
        else:
            self.vuln_timer = 0

        self.shoot_timer += 1
        shoot_rate = max(20, 60 - self.phase_idx * 15)
        if self.shoot_timer > shoot_rate:
            self.shoot_timer = 0
            angle = random.uniform(0, 2*math.pi)
            spd = random.uniform(2, 5)
            self.projectiles.append(BossProjectile(
                self.x, self.y,
                math.cos(angle)*spd, math.sin(angle)*spd + 2
            ))

        for p in self.projectiles:
            p.update()
        self.projectiles = [p for p in self.projectiles if p.life > 0]
        self.flash = max(0, self.flash - 1)

    def hit(self, dmg=10):
        if not self.vulnerable:
            return False
        self.health -= dmg
        self.flash = 10
        if self.health <= 0:
            return True
        if self.health < 66 and self.phase_idx == 0:
            self.phase_idx = 1
        elif self.health < 33 and self.phase_idx == 1:
            self.phase_idx = 2
        return False

    def draw(self, surf, camera):
        px = int(self.x - camera)
        py = int(self.y)
        phase = self.current_phase()
        color = phase["color"] if self.flash <= 0 else CFG.WHITE

        glow = pygame.Surface((200, 200), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color[:3], 80), (100, 100), 80)
        surf.blit(glow, (px-100, py-100))

        # Integral sign body
        pygame.draw.rect(surf, color, (px-30, py-60, 60, 120), border_radius=10)
        pygame.draw.ellipse(surf, color, (px-40, py-70, 80, 30))
        pygame.draw.ellipse(surf, color, (px-40, py+40, 80, 30))

        # Glasses
        pygame.draw.rect(surf, CFG.WHITE, (px-25, py-20, 20, 15), 2)
        pygame.draw.rect(surf, CFG.WHITE, (px+5, py-20, 20, 15), 2)
        pygame.draw.line(surf, CFG.WHITE, (px-5, py-12), (px+5, py-12), 2)

        # Health bar
        bar_w = 100
        fill = int(bar_w * (self.health / self.max_health))
        pygame.draw.rect(surf, (50,0,0), (px-bar_w//2, py-90, bar_w, 10))
        pygame.draw.rect(surf, CFG.GREEN, (px-bar_w//2, py-90, fill, 10))

        f = pygame.font.Font(None, 24)
        name = f.render(phase["name"], True, color)
        surf.blit(name, (px - name.get_width()//2, py - 110))

        if self.vulnerable:
            v = f.render("VULNERABLE!", True, CFG.GOLD)
            surf.blit(v, (px - v.get_width()//2, py + 70))

        for p in self.projectiles:
            p.draw(surf, camera)

# =============================================================================
# ENTITIES
# =============================================================================
class Bullet:
    def __init__(self, x, y, tx, ty, btype="normal"):
        self.x, self.y = x, y
        self.active = True
        self.type = btype
        dx, dy = tx-x, ty-y
        dist = math.hypot(dx, dy)
        spd = CFG.BULLET_SPEED * (1.5 if btype == "prime" else 1.0)
        self.vx = (dx/dist * spd) if dist > 0 else 0
        self.vy = (dy/dist * spd) if dist > 0 else -spd
        self.trail = []
        colors = {"normal": CFG.BRIGHT, "prime": CFG.GOLD, "derivative": CFG.CYAN}
        self.color = colors.get(btype, CFG.BRIGHT)

    def update(self):
        self.trail.insert(0, (self.x, self.y))
        if len(self.trail) > 12:
            self.trail.pop()
        self.x += self.vx
        self.y += self.vy
        if not (-50 < self.x < CFG.WIDTH+50 and -50 < self.y < CFG.HEIGHT+50):
            self.active = False

    def draw(self, surf):
        for i, (tx, ty) in enumerate(self.trail):
            a = 1 - i/12
            pygame.draw.circle(surf, (*self.color[:3], int(255*a)), (int(tx), int(ty)), max(1, int(4*a)))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), 6)
        pygame.draw.circle(surf, CFG.WHITE, (int(self.x), int(self.y)), 6, 2)

class Enemy:
    def __init__(self, x, y, etype="wander", diff=1):
        self.x, self.y = x, y
        self.type = etype
        self.diff = diff
        self.alive = True
        self.hp = 1 + diff//3
        self.max_hp = self.hp
        self.size = 20
        self.t = 0
        self.ox, self.oy = x, y
        self.number = random.randint(2, 20*diff)
        self.flash = 0

    def update(self):
        self.t += 1
        self.flash = max(0, self.flash-1)
        if self.type == "wander":
            self.x += random.choice([-1,1]) * (1 + self.diff*0.2)
            self.y += random.choice([-1,1]) * (1 + self.diff*0.2)
        elif self.type == "sine":
            self.x = self.ox + self.t * 2
            self.y = self.oy + 50 * math.sin(self.t * 0.05)
        elif self.type == "circle":
            self.x = self.ox + 100 * math.cos(self.t * 0.03)
            self.y = self.oy + 100 * math.sin(self.t * 0.03)

        self.x = max(20, min(CFG.WIDTH-20, self.x))
        self.y = max(20, min(CFG.HEIGHT-150, self.y))

    def hit(self, dmg=1):
        self.hp -= dmg
        self.flash = 10
        if self.hp <= 0:
            self.alive = False

    def rect(self):
        return pygame.Rect(self.x-self.size, self.y-self.size, self.size*2, self.size*2)

    def draw(self, surf):
        if not self.alive:
            return
        c = CFG.WHITE if self.flash > 0 else CFG.GOLD
        pygame.draw.circle(surf, c, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(surf, CFG.WHITE, (int(self.x), int(self.y)), self.size, 2)
        f = pygame.font.Font(None, 22)
        t = f.render(str(self.number), True, CFG.BG)
        surf.blit(t, (int(self.x)-t.get_width()//2, int(self.y)-8))
        if self.hp < self.max_hp:
            bw = 30
            f2 = int(bw * (self.hp/self.max_hp))
            pygame.draw.rect(surf, CFG.RED, (int(self.x)-bw//2, int(self.y)-self.size-8, bw, 4))
            pygame.draw.rect(surf, CFG.GREEN, (int(self.x)-bw//2, int(self.y)-self.size-8, f2, 4))

class AnswerButton:
    def __init__(self, x, y, w, h, text, correct):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = str(text)
        self.correct = correct
        self.hover = False
        self.clicked = False
        self.click_t = 0

    def update(self, mpos):
        self.hover = self.rect.collidepoint(mpos)
        if self.clicked:
            self.click_t -= 1
            if self.click_t <= 0:
                self.clicked = False

    def draw(self, surf):
        if self.clicked:
            c = CFG.BRIGHT if self.correct else CFG.RED
        elif self.hover:
            c = CFG.GREEN
        else:
            c = CFG.DIM

        if self.hover or self.clicked:
            g = pygame.Surface((self.rect.w+10, self.rect.h+10), pygame.SRCALPHA)
            pygame.draw.rect(g, (*c[:3], 60), g.get_rect(), border_radius=8)
            surf.blit(g, (self.rect.x-5, self.rect.y-5))

        pygame.draw.rect(surf, c, self.rect, border_radius=5, width=2)
        if self.hover:
            pygame.draw.rect(surf, (*c[:3], 80), self.rect.inflate(-4,-4), border_radius=3)

        f = pygame.font.Font(None, 36)
        t = f.render(self.text, True, CFG.WHITE)
        surf.blit(t, t.get_rect(center=self.rect.center))

# =============================================================================
# PLATFORMER PLAYER
# =============================================================================
class PlatformerPlayer:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx = self.vy = 0
        self.size = 22
        self.grounded = False
        self.jumps = 0
        self.max_jumps = 1
        self.facing_right = True
        self.invincible = 0
        self.speed_boost = 0

    def update(self, terrain, keys, skills):
        if skills.is_unlocked("double_jump"):
            self.max_jumps = 2

        spd = CFG.PLAYER_SPEED * (1.5 if self.speed_boost > 0 else 1.0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -spd
            self.facing_right = False
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = spd
            self.facing_right = True
        else:
            self.vx *= 0.8

        self.vy += CFG.GRAVITY
        self.vy = min(self.vy, 16)

        jump_str = CFG.JUMP * (1.3 if skills.is_unlocked("taylor_jump") else 1.0)
        if keys[pygame.K_SPACE] and self.jumps < self.max_jumps:
            self.vy = jump_str
            self.jumps += 1
            self.grounded = False

        self.x += self.vx
        self.y += self.vy

        ty = terrain.get_y(self.x)
        if self.y + self.size >= ty and self.vy >= 0:
            self.y = ty - self.size
            self.vy = 0
            self.grounded = True
            self.jumps = 0
            slope = terrain.deriv(self.x)
            if abs(slope) > 1.0:
                self.vx += slope * 0.3
        else:
            self.grounded = False

        self.x = max(self.size, min(CFG.WIDTH - self.size, self.x))
        if self.invincible > 0:
            self.invincible -= 1
        if self.speed_boost > 0:
            self.speed_boost -= 1

    def draw(self, surf, polar=False):
        if polar:
            cx, cy = CFG.WIDTH//2, CFG.HEIGHT//2
            theta = self.x * 0.003
            r = (CFG.HEIGHT - self.y) * 0.5
            px = cx + r * math.cos(theta)
            py = cy + r * math.sin(theta)
            self._draw_body(surf, px, py)
        else:
            self._draw_body(surf, self.x, self.y)

    def _draw_body(self, surf, x, y):
        x, y = int(x), int(y)
        pygame.draw.rect(surf, CFG.GREEN, (x-12, y-20, 24, 28), border_radius=3)
        pygame.draw.rect(surf, CFG.BG, (x-8, y-16, 16, 10))
        pygame.draw.rect(surf, CFG.BRIGHT, (x-6, y-14, 12, 6))
        lc = CFG.DIM
        if self.grounded:
            pygame.draw.line(surf, lc, (x-6, y+8), (x-6, y+20), 3)
            pygame.draw.line(surf, lc, (x+6, y+8), (x+6, y+20), 3)
        else:
            pygame.draw.line(surf, lc, (x-6, y+8), (x-10, y+16), 3)
            pygame.draw.line(surf, lc, (x+6, y+8), (x+10, y+12), 3)
        if self.vx != 0:
            ay = y + 2
            if self.facing_right:
                pygame.draw.line(surf, lc, (x+12, ay), (x+20, ay-5), 3)
            else:
                pygame.draw.line(surf, lc, (x-12, ay), (x-20, ay-5), 3)
        if self.invincible > 0 and self.invincible % 4 < 2:
            pygame.draw.circle(surf, CFG.GOLD, (x, y), 30, 3)

# =============================================================================
# MAIN GAME
# =============================================================================
class MathApocalypse:
    def __init__(self):
        pygame.display.set_caption("MATH APOCALYPSE: DIMENSIONAL FLIP [ULTIMATE]")
        self.screen = pygame.display.set_mode((CFG.WIDTH, CFG.HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = {
            'large': pygame.font.Font(None, 72),
            'med': pygame.font.Font(None, 48),
            'small': pygame.font.Font(None, 28)
        }

        self.audio = AudioEngine()
        self.save = SaveManager.load()
        self.math = MathEngine()
        self.particles = ParticleSystem()
        self.effects = ScreenEffects()
        self.skills = SkillTree(self.save)

        self.phase = "start"
        self.level = 1
        self.score = 0
        self.health = 3
        self.max_health = 3
        self.streak = 0
        self.correct_total = 0

        self.px = CFG.WIDTH//2
        self.py = CFG.HEIGHT//2
        self.sdir = (0, -1)
        self.bullets = []
        self.enemies = []
        self.last_shot = 0

        self.problem = None
        self.buttons = []
        self.prob_timer = 0
        self.prob_max = 600

        self.plr = None
        self.terrain = None
        self.blocks = []
        self.powerups = []
        self.polar_mode = False

        self.boss = None
        self.boss_active = False

        self.flip_prog = 0
        self.flip_msg = ""

        self.block_problem = None
        self.block_buttons = []
        self.block_owner = None

        self.start_time = time.time()

        self.reset()

    def reset(self):
        self.level = 1
        self.score = 0
        self.health = self.max_health
        self.streak = 0
        self.px = CFG.WIDTH//2
        self.py = CFG.HEIGHT//2
        self.bullets = []
        self.enemies = []
        self.plr = None
        self.terrain = None
        self.blocks = []
        self.powerups = []
        self.boss = None
        self.boss_active = False
        self.polar_mode = False
        self.spawn_enemies()
        self.gen_problem()

    def spawn_enemies(self):
        self.enemies = []
        for _ in range(3 + self.level):
            et = random.choice(["wander", "sine", "circle"]) if self.level > 2 else "wander"
            self.enemies.append(Enemy(
                random.randint(50, CFG.WIDTH-50),
                random.randint(50, CFG.HEIGHT-150),
                et, self.level
            ))

    def gen_problem(self):
        self.problem = self.math.generate(self.level)
        self.prob_timer = self.prob_max
        opts = self.problem["opts"]
        self.buttons = []
        bw, bh, sp = 140, 60, 20
        tw = len(opts)*(bw+sp) - sp
        sx = (CFG.WIDTH - tw)//2
        for i, o in enumerate(opts):
            self.buttons.append(AnswerButton(sx+i*(bw+sp), 520, bw, bh, str(o), o==self.problem["a"]))

    def spawn_blocks(self):
        self.blocks = []
        if not self.terrain:
            return
        for x in range(200, CFG.WIDTH-100, 300):
            y = self.terrain.get_y(x) - 80
            p = self.math.generate(max(1, self.level-5))
            self.blocks.append(QuestionBlock(x, y, p))

    def start_flip(self):
        self.phase = "flip"
        self.flip_prog = 0
        self.flip_msg = random.choice([
            "REALITY UNSTABLE...", "MATHEMATICAL SINGULARITY DETECTED",
            "DIMENSIONAL FLIP IMMINENT", "ABANDON CARTESIAN COORDINATES"
        ])
        self.plr = PlatformerPlayer(100, 300)
        self.terrain = FunctionTerrain("sin", 80, 0.008, 0, 500)
        self.spawn_blocks()
        self.audio.play_flip()

    def start_boss(self):
        self.boss = DifferentialBoss(self.level)
        self.boss_active = True
        self.enemies = []

    def events(self):
        mpos = pygame.mouse.get_pos()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_p:
                    self.pause()
                if e.key == pygame.K_m:
                    if self.phase == "skilltree":
                        self.phase = "platformer" if self.plr else "shooter"
                    elif self.phase in ("shooter", "platformer", "boss"):
                        self.phase = "skilltree"
                if e.key == pygame.K_TAB and self.phase in ("platformer", "boss"):
                    if self.skills.is_unlocked("polar_unlock"):
                        self.polar_mode = not self.polar_mode
                if e.key == pygame.K_r and self.phase == "gameover":
                    self.reset()
                    self.phase = "shooter"
                if e.key == pygame.K_SPACE and self.phase == "start":
                    self.phase = "shooter"

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.phase == "skilltree":
                    sid = self.skills.handle_click(mpos)
                    if sid:
                        if sid == "extra_hp":
                            self.max_health += 1
                            self.health += 1
                        self.save["unlocked_skills"] = list(self.skills.unlocked)
                        self.save["skill_points"] = self.skills.points
                        SaveManager.save(self.save)
                elif self.phase == "shooter":
                    self.click_shooter(mpos)
                elif self.phase == "block_question":
                    self.click_block(mpos)
                elif self.phase in ("platformer", "boss") and self.boss_active:
                    self.click_boss_shoot(mpos)

        return True

    def click_shooter(self, mpos):
        for btn in self.buttons:
            if btn.rect.collidepoint(mpos):
                btn.clicked = True
                btn.click_t = 20
                if btn.correct:
                    self.handle_correct()
                else:
                    self.handle_wrong()
                break

    def click_block(self, mpos):
        for btn in self.block_buttons:
            if btn.rect.collidepoint(mpos):
                btn.clicked = True
                btn.click_t = 20
                if btn.correct:
                    ptype = random.choice(PowerUp.TYPES)
                    self.powerups.append(PowerUp(self.block_owner.x, self.block_owner.y - 20, ptype))
                    self.block_owner.answered = True
                    self.score += 15
                    self.audio.play_correct()
                    self.particles.spawn(self.block_owner.x, self.block_owner.y, 30, CFG.GOLD, 6)
                else:
                    self.enemies.append(Enemy(self.block_owner.x, self.block_owner.y, "wander", self.level))
                    self.audio.play_wrong()
                    self.effects.shake(8)
                self.phase = "platformer"
                self.block_owner = None
                break

    def click_boss_shoot(self, mpos):
        if self.boss and self.boss.vulnerable:
            bx = self.plr.x if self.plr else CFG.WIDTH//2
            by = self.plr.y if self.plr else CFG.HEIGHT//2
            self.bullets.append(Bullet(bx, by, self.boss.x, self.boss.y, "derivative"))
            self.audio.play_shoot()

    def handle_correct(self):
        self.score += 10 + self.streak * 2
        self.streak += 1
        self.correct_total += 1
        self.audio.play_correct()
        self.particles.spawn(CFG.WIDTH//2, 300, 40, CFG.BRIGHT, 7)
        self.effects.shake(5)

        if self.correct_total % 5 == 0:
            self.skills.points += 1
            self.save["skill_points"] = self.skills.points
            SaveManager.save(self.save)

        if self.streak % 3 == 0:
            self.level += 1
            self.effects.glitch_fx(15)
            self.effects.shake(15)
            if self.level == 11:
                self.start_flip()
                return
            if self.level >= 15 and self.level % 5 == 0 and not self.boss_active:
                if self.phase in ("platformer", "boss"):
                    self.start_boss()
                    self.phase = "boss"
                    return

        self.spawn_enemies()
        self.gen_problem()

    def handle_wrong(self):
        self.streak = 0
        self.health -= 1
        self.audio.play_wrong()
        self.particles.spawn(CFG.WIDTH//2, 300, 30, CFG.RED, 6)
        self.effects.shake(10)
        if self.health <= 0:
            self.game_over()

    def game_over(self):
        self.phase = "gameover"
        self.save["high_score"] = max(self.save["high_score"], self.score)
        self.save["total_correct"] += self.correct_total
        self.save["play_time"] += time.time() - self.start_time
        SaveManager.save(self.save)

    def pause(self):
        paused = True
        while paused:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_p:
                    paused = False
            overlay = pygame.Surface((CFG.WIDTH, CFG.HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0,0,0))
            self.screen.blit(overlay, (0,0))
            t = self.fonts['med'].render("PAUSED", True, CFG.GREEN)
            self.screen.blit(t, t.get_rect(center=(CFG.WIDTH//2, CFG.HEIGHT//2)))
            pygame.display.flip()
            self.clock.tick(30)

    def update(self):
        keys = pygame.key.get_pressed()
        mpos = pygame.mouse.get_pos()

        if self.phase == "shooter":
            self.update_shooter(keys, mpos)
        elif self.phase == "flip":
            self.update_flip()
        elif self.phase == "platformer":
            self.update_platformer(keys)
        elif self.phase == "boss":
            self.update_boss(keys)

        self.effects.update()
        self.particles.update()

    def update_shooter(self, keys, mpos):
        ct = pygame.time.get_ticks()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.px -= CFG.PLAYER_SPEED; self.sdir = (-1,0)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.px += CFG.PLAYER_SPEED; self.sdir = (1,0)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.py -= CFG.PLAYER_SPEED; self.sdir = (0,-1)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.py += CFG.PLAYER_SPEED; self.sdir = (0,1)

        self.px = max(20, min(CFG.WIDTH-20, self.px))
        self.py = max(20, min(CFG.HEIGHT-20, self.py))

        fast = self.skills.is_unlocked("fast_shoot")
        delay = 120 if fast else 250
        if keys[pygame.K_SPACE] and ct - self.last_shot > delay:
            self.last_shot = ct
            tx = self.px + self.sdir[0]*100
            ty = self.py + self.sdir[1]*100
            btype = "prime" if self.skills.is_unlocked("prime_gun") and random.random()<0.3 else "normal"
            self.bullets.append(Bullet(self.px, self.py, tx, ty, btype))
            self.audio.play_shoot()

        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.active]

        for en in self.enemies:
            en.update()

        for b in self.bullets[:]:
            for en in self.enemies:
                if en.alive and b.active and math.hypot(b.x-en.x, b.y-en.y) < en.size+6:
                    en.hit()
                    b.active = False
                    self.particles.spawn(en.x, en.y, 20, CFG.GOLD, 5)
                    self.score += 5
                    break

        self.enemies = [e for e in self.enemies if e.alive]
        if not self.enemies:
            self.spawn_enemies()

        for en in self.enemies:
            if math.hypot(self.px-en.x, self.py-en.y) < 30:
                self.health -= 1
                en.hit()
                self.effects.shake(10)
                self.particles.spawn(self.px, self.py, 30, CFG.RED, 6)
                if self.health <= 0:
                    self.game_over()

        for btn in self.buttons:
            btn.update(mpos)

        self.prob_timer -= 1
        if self.prob_timer <= 0:
            self.health -= 1
            self.streak = 0
            self.effects.shake(8)
            self.gen_problem()
            if self.health <= 0:
                self.game_over()

    def update_flip(self):
        self.flip_prog += 0.004
        if random.random() < 0.3:
            self.effects.glitch_fx(5)
        if random.random() < 0.2:
            self.effects.shake(random.uniform(2,8))
        if random.random() < 0.5:
            self.particles.spawn(random.randint(0,CFG.WIDTH), random.randint(0,CFG.HEIGHT), 5, CFG.PURPLE, 3)
        if self.flip_prog >= 1:
            self.phase = "platformer"

    def update_platformer(self, keys):
        if self.plr:
            self.plr.update(self.terrain, keys, self.skills)

        if random.random() < 0.001:
            ft = random.choice(FunctionTerrain.TYPES)
            self.terrain = FunctionTerrain(ft, random.uniform(50,150), random.uniform(0.005,0.015), 0, random.uniform(400,600))
            self.spawn_blocks()

        for blk in self.blocks:
            blk.update()
            if blk.active and not blk.answered and self.plr:
                plr_rect = pygame.Rect(self.plr.x-12, self.plr.y-20, 24, 28)
                blk_rect = pygame.Rect(blk.x, blk.y, 44, 44)
                if plr_rect.colliderect(blk_rect) and self.plr.vy < 0:
                    prob = blk.hit()
                    if prob:
                        self.block_problem = prob
                        self.block_owner = blk
                        self.block_buttons = []
                        opts = prob["opts"]
                        bw, bh, sp = 140, 60, 20
                        tw = len(opts)*(bw+sp)-sp
                        sx = (CFG.WIDTH-tw)//2
                        for i,o in enumerate(opts):
                            self.block_buttons.append(AnswerButton(sx+i*(bw+sp), 520, bw, bh, str(o), o==prob["a"]))
                        self.phase = "block_question"
                        self.audio.play_jump()

        for p in self.powerups[:]:
            p.update()
            if self.plr and math.hypot(p.x-self.plr.x, p.y-self.plr.y) < 25:
                if p.type == "health":
                    self.health = min(self.max_health, self.health+1)
                elif p.type == "speed":
                    self.plr.speed_boost = 180
                elif p.type == "invincible":
                    self.plr.invincible = 300
                elif p.type == "score":
                    self.score += 50
                self.powerups.remove(p)
                self.audio.play_correct()
        self.powerups = [p for p in self.powerups if p.life > 0]

        if random.random() < 0.008:
            self.enemies.append(Enemy(random.randint(0,CFG.WIDTH), random.randint(0,CFG.HEIGHT//2), "wander", self.level))
        for en in self.enemies[:]:
            en.update()
            if self.plr and math.hypot(en.x-self.plr.x, en.y-self.plr.y) < 30:
                if self.plr.invincible <= 0:
                    self.health -= 1
                    self.effects.shake(10)
                    self.audio.play_wrong()
                    if self.health <= 0:
                        self.game_over()
                        return
                en.alive = False
        self.enemies = [e for e in self.enemies if e.alive]

        if self.level >= 15 and self.level % 5 == 0 and not self.boss_active and not self.boss:
            self.start_boss()
            self.phase = "boss"

    def update_boss(self, keys):
        if self.plr:
            self.plr.update(self.terrain, keys, self.skills)
        if self.boss:
            self.boss.update()
            for b in self.bullets[:]:
                if b.active and math.hypot(b.x-self.boss.x, b.y-self.boss.y) < 60:
                    dead = self.boss.hit(10)
                    b.active = False
                    self.particles.spawn(self.boss.x, self.boss.y, 25, CFG.PURPLE, 6)
                    self.audio.play_correct()
                    if dead:
                        self.boss_active = False
                        self.boss = None
                        self.score += 500
                        self.save["bosses_defeated"] = self.save.get("bosses_defeated",0)+1
                        SaveManager.save(self.save)
                        self.phase = "platformer"
                        self.particles.spawn(CFG.WIDTH//2, CFG.HEIGHT//2, 100, CFG.GOLD, 10)
                        self.effects.shake(20)
                        self.audio.play_flip()
                        return
            if self.plr:
                for p in self.boss.projectiles:
                    if math.hypot(p.x-self.plr.x, p.y-self.plr.y) < 20:
                        if self.plr.invincible <= 0:
                            self.health -= 1
                            self.effects.shake(10)
                            self.audio.play_wrong()
                            p.life = 0
                            if self.health <= 0:
                                self.game_over()
                                return
                self.boss.projectiles = [p for p in self.boss.projectiles if p.life > 0]

        for blk in self.blocks:
            blk.update()
        for p in self.powerups:
            p.update()

    def draw(self):
        self.screen.fill(CFG.BG)

        if self.phase == "start":
            self.draw_start()
        elif self.phase == "shooter":
            self.draw_shooter()
        elif self.phase == "flip":
            self.draw_flip()
        elif self.phase == "platformer":
            self.draw_platformer()
        elif self.phase == "boss":
            self.draw_boss_scene()
        elif self.phase == "block_question":
            self.draw_platformer()
            self.draw_block_overlay()
        elif self.phase == "skilltree":
            self.skills.draw(self.screen, self.fonts['small'])
        elif self.phase == "gameover":
            self.draw_gameover()

        self.particles.draw(self.screen)
        self.screen = self.effects.apply(self.screen)
        pygame.display.flip()

    def draw_start(self):
        t = pygame.time.get_ticks()/1000
        title = self.fonts['large'].render("MATH APOCALYPSE", True, CFG.BRIGHT)
        r = title.get_rect(center=(CFG.WIDTH//2, 200))
        pulse = int(50 + 30*math.sin(t*3))
        glow = pygame.Surface((r.w+40, r.h+40), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*CFG.GREEN[:3], pulse), glow.get_rect(), border_radius=10)
        self.screen.blit(glow, (r.x-20, r.y-20))
        self.screen.blit(title, r)

        sub = self.fonts['med'].render("DIMENSIONAL FLIP [ULTIMATE]", True, CFG.PURPLE)
        self.screen.blit(sub, sub.get_rect(center=(CFG.WIDTH//2, 280)))

        lines = [
            "WASD/Arrows = Move | SPACE = Shoot/Jump",
            "MOUSE = Click answers | P = Pause | M = Skill Tree",
            "Reach Level 11 to trigger THE FLIP...",
            f"High Score: {self.save['high_score']} | Bosses: {self.save.get('bosses_defeated',0)}"
        ]
        for i, line in enumerate(lines):
            txt = self.fonts['small'].render(line, True, CFG.DIM)
            self.screen.blit(txt, txt.get_rect(center=(CFG.WIDTH//2, 400+i*35)))

        if int(t*2)%2 == 0:
            s = self.fonts['med'].render("Press SPACE", True, CFG.GREEN)
            self.screen.blit(s, s.get_rect(center=(CFG.WIDTH//2, 600)))

    def draw_shooter(self):
        for i in range(0, CFG.WIDTH, 40):
            pygame.draw.line(self.screen, (0,30,15), (i,0), (i,CFG.HEIGHT))
        for i in range(0, CFG.HEIGHT, 40):
            pygame.draw.line(self.screen, (0,30,15), (0,i), (CFG.WIDTH,i))

        if self.problem:
            q = self.fonts['large'].render(self.problem["q"], True, CFG.BRIGHT)
            self.screen.blit(q, q.get_rect(center=(CFG.WIDTH//2, 150)))
            c = self.fonts['small'].render(f"[{self.problem['cat']}]", True, CFG.CYAN)
            self.screen.blit(c, c.get_rect(center=(CFG.WIDTH//2, 210)))

            bw = 400
            f = int(bw * (self.prob_timer/self.prob_max))
            pygame.draw.rect(self.screen, (30,30,30), ((CFG.WIDTH-bw)//2, 240, bw, 6))
            clr = CFG.GREEN if self.prob_timer > 180 else CFG.RED
            pygame.draw.rect(self.screen, clr, ((CFG.WIDTH-bw)//2, 240, f, 6))

        for btn in self.buttons:
            btn.draw(self.screen)

        pg = pygame.Surface((60,60), pygame.SRCALPHA)
        pygame.draw.circle(pg, (*CFG.GREEN[:3], 60), (30,30), 25)
        self.screen.blit(pg, (int(self.px)-30, int(self.py)-30))
        angle = math.atan2(self.sdir[1], self.sdir[0])
        pts = [(int(self.px + math.cos(angle + i*2.094)*18),
                int(self.py + math.sin(angle + i*2.094)*18)) for i in range(3)]
        pygame.draw.polygon(self.screen, CFG.BRIGHT, pts)
        pygame.draw.polygon(self.screen, CFG.WHITE, pts, 2)

        for b in self.bullets:
            b.draw(self.screen)
        for en in self.enemies:
            en.draw(self.screen)

        self.draw_hud()

    def draw_flip(self):
        for _ in range(20):
            x, y = random.randint(0,CFG.WIDTH), random.randint(0,CFG.HEIGHT)
            sz = random.randint(10,100)
            c = random.choice([CFG.GREEN, CFG.RED, CFG.GOLD, CFG.PURPLE])
            pts = [(x+random.randint(-sz,sz), y+random.randint(-sz,sz)) for _ in range(3)]
            pygame.draw.polygon(self.screen, (*c[:3], 100), pts)

        bw = 600
        f = int(bw * self.flip_prog)
        pygame.draw.rect(self.screen, (30,30,30), ((CFG.WIDTH-bw)//2, CFG.HEIGHT//2+100, bw, 20))
        pygame.draw.rect(self.screen, CFG.PURPLE, ((CFG.WIDTH-bw)//2, CFG.HEIGHT//2+100, f, 20))

        txt = self.fonts['med'].render(self.flip_msg, True, CFG.BRIGHT)
        r = txt.get_rect(center=(CFG.WIDTH//2, CFG.HEIGHT//2))
        self.screen.blit(txt, r)
        if random.random() < 0.3:
            g = self.fonts['med'].render(self.flip_msg, True, CFG.RED)
            self.screen.blit(g, (r.x+random.randint(-5,5), r.y))

    def draw_platformer(self):
        for y in range(CFG.HEIGHT):
            v = int(5 + (y/CFG.HEIGHT)*20)
            pygame.draw.line(self.screen, (0, v, v//2), (0,y), (CFG.WIDTH,y))

        if self.terrain:
            self.terrain.draw(self.screen, polar=self.polar_mode)
        if self.plr:
            self.plr.draw(self.screen, polar=self.polar_mode)
        for blk in self.blocks:
            blk.draw(self.screen, 0)
        for p in self.powerups:
            p.draw(self.screen, 0)
        for en in self.enemies:
            en.draw(self.screen)

        mode_txt = "POLAR VIEW" if self.polar_mode else "CARTESIAN VIEW"
        mode_color = CFG.PURPLE if self.polar_mode else CFG.GREEN
        txt = self.fonts['small'].render(mode_txt, True, mode_color)
        self.screen.blit(txt, (20, 80))

        self.draw_hud()

    def draw_boss_scene(self):
        self.draw_platformer()
        if self.boss:
            self.boss.draw(self.screen, 0)
        if self.boss:
            txt = self.fonts['med'].render(f"BOSS: {self.boss.current_phase()['name']}", True, self.boss.current_phase()['color'])
            self.screen.blit(txt, (CFG.WIDTH//2 - txt.get_width()//2, 20))

    def draw_block_overlay(self):
        overlay = pygame.Surface((CFG.WIDTH, CFG.HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0,0,0))
        self.screen.blit(overlay, (0,0))

        if self.block_problem:
            q = self.fonts['large'].render(self.block_problem["q"], True, CFG.BRIGHT)
            self.screen.blit(q, q.get_rect(center=(CFG.WIDTH//2, 200)))
            cat = self.fonts['small'].render(f"[{self.block_problem['cat']}]", True, CFG.GOLD)
            self.screen.blit(cat, cat.get_rect(center=(CFG.WIDTH//2, 260)))

        for btn in self.block_buttons:
            btn.draw(self.screen)

        hint = self.fonts['small'].render("Click the correct answer!", True, CFG.DIM)
        self.screen.blit(hint, hint.get_rect(center=(CFG.WIDTH//2, 620)))

    def draw_gameover(self):
        overlay = pygame.Surface((CFG.WIDTH, CFG.HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((10,0,0))
        self.screen.blit(overlay, (0,0))

        t = self.fonts['large'].render("GAME OVER", True, CFG.RED)
        self.screen.blit(t, t.get_rect(center=(CFG.WIDTH//2, CFG.HEIGHT//2-50)))

        s = self.fonts['med'].render(f"Score: {self.score}  Level: {self.level}", True, CFG.WHITE)
        self.screen.blit(s, s.get_rect(center=(CFG.WIDTH//2, CFG.HEIGHT//2+20)))

        h = self.fonts['small'].render(f"High Score: {self.save['high_score']}", True, CFG.GOLD)
        self.screen.blit(h, h.get_rect(center=(CFG.WIDTH//2, CFG.HEIGHT//2+70)))

        r = self.fonts['small'].render("Press R to restart", True, CFG.DIM)
        self.screen.blit(r, r.get_rect(center=(CFG.WIDTH//2, CFG.HEIGHT//2+120)))

    def draw_hud(self):
        self.screen.blit(self.fonts['med'].render(f"SCORE: {self.score}", True, CFG.GREEN), (20,20))
        self.screen.blit(self.fonts['med'].render(f"LVL: {self.level}", True, CFG.GOLD), (CFG.WIDTH-150,20))

        for i in range(self.max_health):
            x, y = 20+i*35, 70
            c = CFG.RED if i < self.health else (50,20,20)
            pygame.draw.polygon(self.screen, c, [
                (x, y+5), (x+5, y), (x+10, y+5), (x+15, y),
                (x+15, y+8), (x+7, y+18), (x, y+8)
            ])
        if self.streak > 0:
            self.screen.blit(self.fonts['small'].render(f"STREAK: {self.streak}x", True, CFG.GOLD), (20, 110))

    def run(self):
        running = True
        while running:
            if not self.events():
                break
            self.update()
            self.draw()
            self.clock.tick(CFG.FPS)
        pygame.quit()

if __name__ == "__main__":
    print("="*60)
    print("  MATH APOCALYPSE: DIMENSIONAL FLIP [ULTIMATE EDITION]")
    print("="*60)
    print("Controls: WASD=Move  SPACE=Shoot/Jump  MOUSE=Answers")
    print("          P=Pause  M=Skill Tree  TAB=Polar (if unlocked)")
    print("="*60)
    if not NUMPY_AVAILABLE:
        print("WARNING: pip install numpy for sound & Mandelbrot")
    if not SYMPY_AVAILABLE:
        print("WARNING: pip install sympy for advanced math")
    print("="*60)
    MathApocalypse().run()
