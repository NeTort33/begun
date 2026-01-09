import pygame
import sys
import random

pygame.init()

# --- ЭКРАН ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Кооп платформер")
clock = pygame.time.Clock()

# --- ФИЗИКА ---
GRAVITY = 0.8
JUMP_FORCE = -16
GROUND_Y = SCREEN_HEIGHT - 60   # ЛИНИЯ СМЕРТИ

CHAR_TARGET_HEIGHT = SCREEN_HEIGHT * 0.15

camera_x = 0

def load_and_scale(path, target_h):
    try:
        img = pygame.image.load(path).convert_alpha()
        scale = target_h / img.get_height()
        return pygame.transform.scale(
            img,
            (int(img.get_width() * scale), int(img.get_height() * scale))
        )
    except:
        surf = pygame.Surface((30, 50))
        surf.fill((255, 0, 0))
        return surf

# --- ИГРОК ---
class Player:
    def __init__(self, x, controls, paths):
        self.idle = load_and_scale(paths['idle'], CHAR_TARGET_HEIGHT)
        self.run = [load_and_scale(p, CHAR_TARGET_HEIGHT) for p in paths['run']]
        self.jump_img = load_and_scale(paths['jump'], CHAR_TARGET_HEIGHT)
        self.fall_img = load_and_scale(paths['fall'], CHAR_TARGET_HEIGHT)

        self.start_x = x
        self.controls = controls

    def reset(self, start_y):
        self.rect = self.idle.get_rect(topleft=(self.start_x, start_y))
        self.vel_y = 0
        self.is_jumping = False
        self.anim = 0
        self.moving = False

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.moving = False
        if keys[self.controls['left']]:
            self.rect.x -= 6
            self.moving = True
        if keys[self.controls['right']]:
            self.rect.x += 6
            self.moving = True

    def jump(self):
        if not self.is_jumping:
            self.vel_y = JUMP_FORCE
            self.is_jumping = True

    def apply_physics(self, platforms):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        for p in platforms:
            if self.rect.colliderect(p) and self.vel_y >= 0:
                self.rect.bottom = p.top
                self.vel_y = 0
                self.is_jumping = False

    def draw(self, cam_x):
        img = self.idle
        if self.is_jumping:
            img = self.jump_img if self.vel_y < 0 else self.fall_img
        elif self.moving:
            img = self.run[(self.anim // 8) % len(self.run)]

        screen.blit(img, (self.rect.x - cam_x, self.rect.y))
        self.anim += 1

# --- ГЕНЕРАЦИЯ УРОВНЯ ---
def generate_level():
    platforms = []

    # --- СТАРТОВАЯ ПЛАТФОРМА ---
    start_platform = pygame.Rect(100, GROUND_Y - 120, 300, 20)
    platforms.append(start_platform)

    x = start_platform.right + 150
    y = start_platform.y

    for _ in range(18):
        width = random.randint(140, 220)
        platforms.append(pygame.Rect(x, y, width, 20))

        x += random.randint(180, 260)
        y += random.randint(-100, 100)
        y = max(160, min(y, GROUND_Y - 120))

    # --- ФИНАЛЬНАЯ ПЛАТФОРМА ---
    final_platform = pygame.Rect(x + 200, GROUND_Y - 120, 320, 20)
    platforms.append(final_platform)

    exit_zone = pygame.Rect(
        final_platform.centerx - 60,
        final_platform.top - 60,
        120,
        60
    )

    level_end_x = final_platform.right + 300
    return platforms, exit_zone, level_end_x, start_platform

# --- ИГРОКИ ---
player1 = Player(
    160,
    {'left': pygame.K_a, 'right': pygame.K_d},
    {'idle': 'sprites/stoit1.png',
     'run': ['sprites/run1.png', 'sprites/run2.png'],
     'jump': 'sprites/jumpup.png',
     'fall': 'sprites/falldown.png'}
)

player2 = Player(
    240,
    {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT},
    {'idle': 'sprites/Kstoit.png',
     'run': ['sprites/Krun1.png', 'sprites/Krun2.png'],
     'jump': 'sprites/Kjump1.png',
     'fall': 'sprites/Kfall1.png'}
)

def reset_level():
    global platforms, exit_zone, level_end_x, camera_x, win, start_platform
    platforms, exit_zone, level_end_x, start_platform = generate_level()
    player1.reset(start_platform.top - player1.idle.get_height())
    player2.reset(start_platform.top - player2.idle.get_height())
    camera_x = 0
    win = False

reset_level()

font = pygame.font.SysFont(None, 60)
win = False

# --- ЦИКЛ ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                player1.jump()
            if event.key == pygame.K_UP:
                player2.jump()

    if not win:
        player1.handle_input()
        player2.handle_input()

        player1.apply_physics(platforms)
        player2.apply_physics(platforms)

        # --- СМЕРТЬ ОТ ЗЕМЛИ ---
        if (player1.rect.bottom >= GROUND_Y or
            player2.rect.bottom >= GROUND_Y):
            reset_level()

        # камера
        lead_x = max(player1.rect.centerx, player2.rect.centerx)
        camera_x = max(0, lead_x - SCREEN_WIDTH // 2)
        camera_x = min(camera_x, level_end_x - SCREEN_WIDTH)

        if (player1.rect.colliderect(exit_zone) and
            player2.rect.colliderect(exit_zone)):
            win = True

    # --- ОТРИСОВКА ---
    screen.fill((135, 206, 235))

    # визуальная "земля-смерть"
    pygame.draw.rect(
        screen, (180, 60, 60),
        (-camera_x, GROUND_Y, level_end_x, SCREEN_HEIGHT - GROUND_Y)
    )

    for p in platforms:
        pygame.draw.rect(
            screen, (120, 120, 120),
            (p.x - camera_x, p.y, p.width, p.height)
        )

    pygame.draw.rect(
        screen, (255, 215, 0),
        (exit_zone.x - camera_x, exit_zone.y, exit_zone.width, exit_zone.height)
    )

    player1.draw(camera_x)
    player2.draw(camera_x)

    if win:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        text = font.render("УРОВЕНЬ ПРОЙДЕН", True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=(500, 300)))

    pygame.display.update()
    clock.tick(60)
