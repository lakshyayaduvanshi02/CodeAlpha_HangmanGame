import pygame
import random
import math
import sys
import time

pygame.init()
pygame.font.init()
pygame.mixer.init()

# Display Config
WIDTH, HEIGHT = 980, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("⚔️ HANGMAN: PROTOCOL OVERDRIVE ⚔️")
clock = pygame.time.Clock()

# Color Palette (Deep Sci-Fi Realism)
VOID_BG = (8, 9, 14)
SURFACE_GRAD = (18, 20, 30)
CYAN_CORE = (200, 255, 255)
CYAN_GLOW = (0, 220, 255)
MAGENTA_CORE = (255, 210, 240)
MAGENTA_GLOW = (255, 20, 147)
EMERALD_CORE = (220, 255, 230)
EMERALD_GLOW = (0, 255, 128)
AMBER_GLOW = (255, 170, 0)
CRIMSON_GLOW = (255, 30, 60)
TEXT_WHITE = (240, 245, 255)
TEXT_MUTED = (120, 130, 155)

# Fonts
FONT_BRAND = pygame.font.SysFont("segoeui", 22, bold=True)
FONT_WORD = pygame.font.SysFont("consolas", 40, bold=True)
FONT_BTN = pygame.font.SysFont("segoeui", 17, bold=True)
FONT_HUD = pygame.font.SysFont("segoeui", 14, bold=True)
FONT_ALERT = pygame.font.SysFont("impact", 44)

# Dynamic Audio Synthesizer
def play_sfx(freq_list, duration=0.08, volume=0.25):
    try:
        sample_rate = 44100
        total_samples = int(sample_rate * duration * len(freq_list))
        buf = bytearray()
        samples_per_tone = int(sample_rate * duration)
        for freq in freq_list:
            for i in range(samples_per_tone):
                t = float(i) / sample_rate
                # Smooth decay envelope
                decay = max(0.0, 1.0 - (float(i) / samples_per_tone))
                val = int(32767.0 * volume * decay * math.sin(2.0 * math.pi * freq * t))
                buf += val.to_bytes(2, byteorder="little", signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.play()
    except Exception:
        pass

# Visual Effects Engines
class Particle:
    def __init__(self, x, y, color_glow, speed_range=(2, 6), lifespan=35):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(*speed_range)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.radius = random.uniform(2, 5.5)
        self.glow = color_glow
        self.life = lifespan
        self.max_life = lifespan

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= 1

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = int((self.life / self.max_life) * 255)
        r = max(1, int(self.radius * (self.life / self.max_life)))
        # Glow halo
        halo_surf = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
        pygame.draw.circle(halo_surf, (*self.glow, int(alpha * 0.4)), (r * 3, r * 3), r * 3)
        pygame.draw.circle(halo_surf, (255, 255, 255, alpha), (r * 3, r * 3), r)
        surface.blit(halo_surf, (self.x - r * 3, self.y - r * 3))

# Floating Ambient Dust
ambient_dust = []
for _ in range(40):
    ambient_dust.append([random.uniform(0, WIDTH), random.uniform(0, HEIGHT), random.uniform(0.2, 0.8), random.uniform(1, 2.5)])

def draw_bloom_line(surface, start, end, core_color, glow_color, width=3):
    """Renders multi-pass realistic neon lighting"""
    # Outer Glow Pass
    glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.line(glow_surf, (*glow_color, 45), start, end, width + 8)
    pygame.draw.line(glow_surf, (*glow_color, 90), start, end, width + 4)
    surface.blit(glow_surf, (0, 0))
    # Core Beam
    pygame.draw.line(surface, core_color, start, end, width)

def draw_bloom_circle(surface, center, radius, core_color, glow_color, width=3):
    glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (*glow_color, 50), center, radius + 5, width + 6)
    pygame.draw.circle(glow_surf, (*glow_color, 100), center, radius + 2, width + 2)
    surface.blit(glow_surf, (0, 0))
    pygame.draw.circle(surface, core_color, center, radius, width)

# Words Database
WORDS_DATABASE = {
    "QUANTUM": {"cat": "COMPUTING", "hint": "Superposition of states enabling hyper-speed calculations."},
    "CYBERSPACE": {"cat": "NETWORK", "hint": "The virtual realm of interconnected computer systems."},
    "FIREWALL": {"cat": "SECURITY", "hint": "Network security barrier filtering incoming and outgoing traffic."},
    "NEURALINK": {"cat": "BIOTECH", "hint": "Brain-computer direct neural interface architecture."},
    "MICROPROCESSOR": {"cat": "HARDWARE", "hint": "The central integrated silicon logic processing unit."},
    "BLOCKCHAIN": {"cat": "CRYPTOGRAPHY", "hint": "Decentralized immutable distributed public ledger."}
}

# State Management
chosen_word = ""
word_info = {}
guessed = set()
wrong_count = 0
max_wrong = 6
score = 0
particles = []
game_status = "PLAYING"
hint_revealed = False
rope_angle = 0.0

# Setup Keyboard Grid
buttons = []
def init_keyboard():
    global buttons
    buttons = []
    rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    btn_w, btn_h, gap = 48, 48, 8
    start_y = 500
    for r_idx, row in enumerate(rows):
        total_w = len(row) * (btn_w + gap) - gap
        start_x = (WIDTH - total_w) // 2
        for c_idx, char in enumerate(row):
            x = start_x + c_idx * (btn_w + gap)
            y = start_y + r_idx * (btn_h + gap)
            buttons.append({"char": char, "rect": pygame.Rect(x, y, btn_w, btn_h), "state": "idle"})

def start_game():
    global chosen_word, word_info, guessed, wrong_count, game_status, hint_revealed
    chosen_word, word_info = random.choice(list(WORDS_DATABASE.items()))
    guessed.clear()
    wrong_count = 0
    game_status = "PLAYING"
    hint_revealed = False
    init_keyboard()

start_game()

# Main Interactive Engine Loop
running = True
hint_btn_rect = pygame.Rect(WIDTH - 210, 25, 85, 36)
rst_btn_rect = pygame.Rect(WIDTH - 110, 25, 85, 36)

while running:
    dt = clock.tick(60) / 1000.0
    t = time.time()
    screen.fill(VOID_BG)

    # Ambient Background Particle Drift
    for dust in ambient_dust:
        dust[1] -= dust[2]
        if dust[1] < 0:
            dust[1] = HEIGHT
            dust[0] = random.uniform(0, WIDTH)
        pygame.draw.circle(screen, (40, 50, 80), (int(dust[0]), int(dust[1])), int(dust[3]))

    # Top Glassmorphism HUD Bar
    hud_bg = pygame.Surface((WIDTH - 40, 65), pygame.SRCALPHA)
    pygame.draw.rect(hud_bg, (18, 22, 35, 210), (0, 0, WIDTH - 40, 65), border_radius=12)
    pygame.draw.rect(hud_bg, (0, 220, 255, 80), (0, 0, WIDTH - 40, 65), 1, border_radius=12)
    screen.blit(hud_bg, (20, 15))

    title_txt = FONT_BRAND.render("⚡ PROTOCOL: OVERDRIVE", True, CYAN_GLOW)
    screen.blit(title_txt, (40, 28))

    cat_txt = FONT_HUD.render(f"DOMAIN: {word_info['cat']}", True, TEXT_MUTED)
    screen.blit(cat_txt, (350, 35))

    score_txt = FONT_HUD.render(f"SCORE: {score}", True, EMERALD_GLOW)
    screen.blit(score_txt, (560, 35))

    # Real-Time Life Gauge
    lives_left = max_wrong - wrong_count
    life_color = EMERALD_GLOW if lives_left > 3 else (AMBER_GLOW if lives_left > 1 else CRIMSON_GLOW)
    gauge_w = 120
    pygame.draw.rect(screen, (30, 35, 50), (660, 38, gauge_w, 14), border_radius=7)
    pygame.draw.rect(screen, life_color, (660, 38, int(gauge_w * (lives_left / max_wrong)), 14), border_radius=7)

    # Action Buttons (Hint / Restart)
    mouse_p = pygame.mouse.get_pos()
    for btn_r, label, b_col in [(hint_btn_rect, "HINT", AMBER_GLOW), (rst_btn_rect, "RESET", CYAN_GLOW)]:
        is_h = btn_r.collidepoint(mouse_p)
        bg_a = 240 if is_h else 160
        b_surf = pygame.Surface((btn_r.w, btn_r.h), pygame.SRCALPHA)
        pygame.draw.rect(b_surf, (25, 30, 45, bg_a), (0, 0, btn_r.w, btn_r.h), border_radius=8)
        pygame.draw.rect(b_surf, (*b_col, 200 if is_h else 100), (0, 0, btn_r.w, btn_r.h), 1, border_radius=8)
        screen.blit(b_surf, (btn_r.x, btn_r.y))
        lbl = FONT_HUD.render(label, True, b_col)
        screen.blit(lbl, (btn_r.centerx - lbl.get_width()//2, btn_r.centery - lbl.get_height()//2))

    # --- Realistic Physics & Gallows Rendering ---
    # Metal Platform
    draw_bloom_line(screen, (100, 430), (320, 430), (220, 230, 255), CYAN_GLOW, 6)
    draw_bloom_line(screen, (160, 430), (160, 130), (220, 230, 255), CYAN_GLOW, 6)
    draw_bloom_line(screen, (160, 130), (280, 130), (220, 230, 255), CYAN_GLOW, 6)
    draw_bloom_line(screen, (160, 180), (210, 130), (200, 220, 255), CYAN_GLOW, 3)

    # Harmonic Rope Swinging Physics
    if wrong_count > 0:
        rope_angle = math.sin(t * 2.8) * 0.08 * (wrong_count / 2.0)
    else:
        rope_angle = 0.0

    pivot_x, pivot_y = 280, 130
    rope_len = 50
    head_x = pivot_x + math.sin(rope_angle) * rope_len
    head_y = pivot_y + math.cos(rope_angle) * rope_len
    draw_bloom_line(screen, (pivot_x, pivot_y), (head_x, head_y), (255, 230, 200), AMBER_GLOW, 3)

    # Android Character Construction
    if wrong_count >= 1: # Holographic Head
        draw_bloom_circle(screen, (int(head_x), int(head_y + 20)), 20, CYAN_CORE, CYAN_GLOW, 3)
    if wrong_count >= 2: # Cyber Spine / Core
        body_end_x = head_x + math.sin(rope_angle) * 75
        body_end_y = head_y + 40 + math.cos(rope_angle) * 75
        draw_bloom_line(screen, (head_x, head_y + 40), (body_end_x, body_end_y), MAGENTA_CORE, MAGENTA_GLOW, 4)
    if wrong_count >= 3: # Left Arm
        draw_bloom_line(screen, (head_x, head_y + 55), (head_x - 30, head_y + 85), CYAN_CORE, CYAN_GLOW, 3)
    if wrong_count >= 4: # Right Arm
        draw_bloom_line(screen, (head_x, head_y + 55), (head_x + 30, head_y + 85), CYAN_CORE, CYAN_GLOW, 3)
    if wrong_count >= 5: # Left Leg
        draw_bloom_line(screen, (head_x, head_y + 115), (head_x - 25, head_y + 165), EMERALD_CORE, EMERALD_GLOW, 3)
    if wrong_count >= 6: # Right Leg
        draw_bloom_line(screen, (head_x, head_y + 115), (head_x + 25, head_y + 165), EMERALD_CORE, EMERALD_GLOW, 3)

    # --- Interactive Word Decoding Matrix ---
    word_panel = pygame.Surface((560, 110), pygame.SRCALPHA)
    pygame.draw.rect(word_panel, (18, 22, 35, 200), (0, 0, 560, 110), border_radius=14)
    pygame.draw.rect(word_panel, (80, 95, 130, 100), (0, 0, 560, 110), 1, border_radius=14)
    screen.blit(word_panel, (380, 170))

    revealed_str = " ".join([letter if letter in guessed else "•" for letter in chosen_word])
    w_surf = FONT_WORD.render(revealed_str, True, TEXT_WHITE)
    screen.blit(w_surf, (380 + (560 - w_surf.get_width()) // 2, 200))

    if hint_revealed:
        hint_s = FONT_HUD.render(f"DECRYPTED INTEL: {word_info['hint']}", True, AMBER_GLOW)
        screen.blit(hint_s, (380 + (560 - hint_s.get_width()) // 2, 255))

    # --- Realistic Glass Keypad Rendering ---
    for b in buttons:
        r = b["rect"]
        is_hover = r.collidepoint(mouse_p) and game_status == "PLAYING" and b["state"] == "idle"
        
        bg_col = (26, 32, 48)
        border_col = (50, 60, 85)
        txt_col = TEXT_WHITE

        if b["state"] == "correct":
            bg_col = (10, 50, 30)
            border_col = EMERALD_GLOW
            txt_col = EMERALD_GLOW
        elif b["state"] == "wrong":
            bg_col = (50, 15, 25)
            border_col = CRIMSON_GLOW
            txt_col = CRIMSON_GLOW
        elif is_hover:
            bg_col = (35, 45, 70)
            border_col = CYAN_GLOW
            txt_col = CYAN_CORE

        btn_s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(btn_s, (*bg_col, 220), (0, 0, r.w, r.h), border_radius=8)
        pygame.draw.rect(btn_s, border_col, (0, 0, r.w, r.h), 2 if is_hover else 1, border_radius=8)
        screen.blit(btn_s, (r.x, r.y))

        char_s = FONT_BTN.render(b["char"], True, txt_col)
        screen.blit(char_s, (r.centerx - char_s.get_width()//2, r.centery - char_s.get_height()//2))

    # Update Real-Time Particle Spark Field
    for p in particles[:]:
        p.update()
        p.draw(screen)
        if p.life <= 0:
            particles.remove(p)

    # --- End Game Overlays ---
    if game_status != "PLAYING":
        dark_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dark_overlay.fill((5, 7, 12, 220))
        screen.blit(dark_overlay, (0, 0))

        if game_status == "WON":
            banner_col = EMERALD_GLOW
            banner_txt = "SYSTEM RESTORED: ACCESS GRANTED"
        else:
            banner_col = CRIMSON_GLOW
            banner_txt = "CORE BREACH: TERMINATION IMMINENT"

        t_win = FONT_ALERT.render(banner_txt, True, banner_col)
        screen.blit(t_win, (WIDTH//2 - t_win.get_width()//2, HEIGHT//2 - 70))

        dec_txt = FONT_BRAND.render(f"Target Cipher Was: [ {chosen_word} ]", True, TEXT_WHITE)
        screen.blit(dec_txt, (WIDTH//2 - dec_txt.get_width()//2, HEIGHT//2))

        sub = FONT_HUD.render("PRESS ANY KEY OR CLICK RESET TO RE-ENGAGE", True, CYAN_GLOW)
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 65))

    # Core Action Logic
    def handle_letter_guess(char):
        global wrong_count, score, game_status
        if char in guessed or game_status != "PLAYING":
            return
        guessed.add(char)
        found = False
        for b in buttons:
            if b["char"] == char:
                if char in chosen_word:
                    b["state"] = "correct"
                    found = True
                    play_sfx([600, 900], 0.07)
                    for _ in range(25):
                        particles.append(Particle(b["rect"].centerx, b["rect"].centery, EMERALD_GLOW))
                else:
                    b["state"] = "wrong"
                    wrong_count += 1
                    play_sfx([300, 180], 0.1)
                    for _ in range(25):
                        particles.append(Particle(b["rect"].centerx, b["rect"].centery, CRIMSON_GLOW))
                break

        if all(c in guessed for c in chosen_word):
            game_status = "WON"
            score += 200
            play_sfx([523, 659, 784, 1046], 0.15)
            for _ in range(80):
                particles.append(Particle(WIDTH//2, HEIGHT//2, EMERALD_GLOW, (3, 10), 60))
        elif wrong_count >= max_wrong:
            game_status = "LOST"
            play_sfx([220, 160, 110], 0.2)
            for _ in range(80):
                particles.append(Particle(WIDTH//2, HEIGHT//2, CRIMSON_GLOW, (3, 10), 60))

    # Event Dispatcher
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_status != "PLAYING":
                start_game()
            else:
                if rst_btn_rect.collidepoint(event.pos):
                    start_game()
                elif hint_btn_rect.collidepoint(event.pos) and not hint_revealed:
                    if (max_wrong - wrong_count) > 1:
                        hint_revealed = True
                        wrong_count += 1
                        play_sfx([440, 550], 0.1)
                for b in buttons:
                    if b["rect"].collidepoint(event.pos) and b["state"] == "idle":
                        handle_letter_guess(b["char"])
        elif event.type == pygame.KEYDOWN:
            if game_status != "PLAYING":
                start_game()
            else:
                k = pygame.key.name(event.key).upper()
                if k in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and len(k) == 1:
                    handle_letter_guess(k)

    pygame.display.flip()

pygame.quit()
sys.exit()