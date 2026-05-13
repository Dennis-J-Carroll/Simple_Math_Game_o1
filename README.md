# MATH APOCALYPSE: DIMENSIONAL FLIP [ULTIMATE EDITION]

> A balls-to-the-wall math game that starts as a retro shooter and **FLIPS** into a calculus platformer at Level 11.

Built by Dennis J. Carroll — evolved from a simple Pygame math quiz into a full chaos engine with 7 interlocking systems.

---

## Quick Start

```bash
pip install pygame numpy sympy
python math_apocalypse_ultimate.py
```

NumPy and SymPy are optional but unlock the audio engine, Mandelbrot skill tree, and advanced math problems.

---

## Controls

| Key / Input | Action |
|-------------|--------|
| `WASD` / Arrow Keys | Move |
| `SPACE` | Shoot (shooter mode) / Jump (platformer mode) |
| Mouse click | Select answer buttons |
| `P` | Pause |
| `M` | Open / close Mandelbrot Skill Tree |
| `TAB` | Toggle Polar View (requires Polar View skill) |
| `R` | Restart after game over |

---

## Game Flow

1. **Levels 1–10 — Shooter Mode**: Move your ship, dodge enemies, shoot enemies for bonus points, and click the correct answer before the timer runs out.
2. **Level 11 — THE FLIP**: Dimensional tear. Screen glitches. Reality destabilizes. You land in a calculus platformer.
3. **Levels 11+ — Platformer Mode**: Walk on living mathematical functions, smash `∫` question blocks, collect power-ups, fight differential equation bosses.
4. **Every 5 levels (≥15)**: A boss fight triggers — a giant integral sign with glasses whose movement is governed by a real differential equation.
5. **Skill Tree**: Press `M` at any time to spend skill points on upgrades.

---

## The 7 Chaos Systems

### 1 — Question Blocks (Mario Math)
- Hit `∫` blocks by jumping into them from below
- Solve the integral/derivative to spawn a power-up (health, speed, invincibility, +50 score)
- Wrong answer spawns an enemy on top of you instead

### 2 — Differential Equation Boss Fights
The boss (a giant integral sign with glasses) moves according to a real ODE:

```
y'' = -2β·y' - ω²·(y - 200) + F₀·cos(γt)
```

| Phase | Equation type | Notes |
|-------|--------------|-------|
| Phase 1 | Harmonic oscillator | `β = 0`, no damping |
| Phase 2 | Damped vibration | Adds `-2β·y'` term |
| Phase 3 | RESONANCE CHAOS | Forced oscillation `F₀cos(γt)` with `γ ≈ ω` |

The boss is **only vulnerable when velocity ≈ 0** (at amplitude peaks). Click to shoot when "VULNERABLE!" appears.

### 3 — Mandelbrot Skill Tree
- Press `M` to open
- Skill nodes are placed on a rendered Mandelbrot set fractal background
- Earn 1 skill point for every 5 correct answers
- Click an affordable node to unlock it

| Skill | Cost | Effect |
|-------|------|--------|
| Double Jump | 3 | Jump twice in the air |
| Taylor Jump | 5 | +30% jump height |
| Prime Gun | 4 | 30% chance of faster prime-factorization shots |
| L'Hôpital Rush | 6 | Death save (extra life) |
| Fourier Vision | 4 | Shows enemy attack frequency wave overlay |
| +1 Heart | 3 | Increases max health by 1 |
| Rapid Fire | 3 | Halves the shoot delay |
| Polar View | 2 | Unlocks `TAB` toggle for polar coordinate mode |

### 4 — Polar Coordinate View
- Requires the **Polar View** skill, then press `TAB` to toggle
- The entire platformer redraws in polar coordinates — terrain, player, and all
- Terrain renders as `r = f(θ)` curves wrapping around the screen center
- Pure visual chaos; physics still computed in Cartesian space

### 5 — Math Melody Audio System
- Correct answers play the next note in a C major pentatonic scale — string answers together to build a melody
- 5+ consecutive correct answers = you're composing
- Wrong answer = dissonant beat + melody resets to the beginning
- Jump = frequency sweep upward
- Shoot = short blip
- Dimensional flip = epic four-note chord

> Requires `numpy`. Falls back to silence without it.

### 6 — JSON Save / Load Progression
Auto-saves after every skill unlock and boss kill. Save file: `math_apocalypse_save.json` (created next to the script).

Tracked fields:

| Field | Description |
|-------|-------------|
| `high_score` | All-time best score |
| `total_correct` | Lifetime correct answers |
| `skill_points` | Spendable points |
| `unlocked_skills` | List of purchased skills |
| `bosses_defeated` | Total bosses killed |
| `play_time` | Cumulative seconds played |

### 7 — Advanced Terrain Functions
The platformer floor is drawn from one of 11 live mathematical functions. The terrain randomly mutates as you play.

| Type | Equation |
|------|---------|
| `sin` | `y = A·sin(fx) + v` |
| `cos` | `y = A·cos(fx) + v` |
| `parabola` | `y = v - A·(f(x-600))²` |
| `exponential` | `y = v - A·e^(f(x-400))` |
| `logarithmic` | `y = v - A·ln(fx)` |
| `absolute` | `y = v - A·\|f(x-600)\|` |
| `tangent` | `y = v + A·tan(fx)` — discontinuities exploitable! |
| `hyperbola` | `y = v - A/(fx)` |
| `cycloid` | `y = v - A·(1 - cos(ft))` |
| `combo` | Superposition of sin + cos harmonics |
| `rose_polar` | `r = A·cos(3θ)` |

Terrain slope is colour-coded in real time:
- **Green** — gentle slope
- **Gold** — steep
- **Red** — near-vertical (slide risk)

Exploit tangent discontinuities — enemies can't cross `x = π/2` gaps!

---

## Math Difficulty Progression

| Levels | Category | Sample problem |
|--------|----------|---------------|
| 1–2 | Arithmetic | `7 × 8 = ?` |
| 3–4 | Algebra | `Solve: 3x + 5 = 20` |
| 5–6 | Trigonometry | `sin(30°) = ?` |
| 7–8 | Derivatives | `d/dx [x³] = ?` |
| 9+ | Integrals | `∫ 2x dx = ?` |

---

## Tips

- **Prime Gun** fires 50% faster golden shots — great for clearing packed enemy clusters
- **L'Hôpital Rush** gives you one free death (the 0/0 moment slows time briefly)
- **Taylor Jump** makes the cycloid and parabola terrains trivially crossable
- **Fourier Vision** overlays the boss's attack wave so you can anticipate burst fire
- Ride the tangent terrain's discontinuities — the gap teleports you across the screen like a warp pipe
- Boss Phase 3 resonance means velocity swings violently and vulnerable windows are very brief — position yourself before the peak

---

## Installation

```bash
# Clone
git clone https://github.com/Dennis-J-Carroll/Simple_Math_Game_o1.git
cd Simple_Math_Game_o1

# Install dependencies
pip install -r requirements.txt

# Run the ultimate edition
python math_apocalypse_ultimate.py
```

### Optional (required for audio and Mandelbrot)

```bash
pip install numpy sympy
```

---

## Repository Layout

```
Simple_Math_Game_o1/
├── math_apocalypse_ultimate.py   # Main game — all 7 chaos systems
├── pygame_o2(retro).py           # v2: retro shooter with Greek letter enemies
├── pygame_o1.py                  # v1: the original simple math quiz
├── requirements.txt
└── math_apocalypse_save.json     # Auto-generated save file (gitignored)
```

---

## License

MIT License — Copyright (c) 2024 Dennis J. Carroll

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## Author

**Dennis J. Carroll**
- GitHub: [Dennis-J-Carroll](https://github.com/Dennis-J-Carroll)
- Email: denniscarrollj@gmail.com

Happy coding!
