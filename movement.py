import pygame
import sys
import random

# Инициализация
pygame.init()
pygame.font.init()

# --- КОНСТАНТЫ И НАСТРОЙКИ ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF | pygame.HWSURFACE)
pygame.display.set_caption("Кооп Платформер: Исправленная версия")
clock = pygame.time.Clock()

# Состояния
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_WIN = "win"
current_state = STATE_MENU

# Физика
GRAVITY = 0.8
JUMP_FORCE = -16  # Немного меньше для проходимости
MOVE_SPEED = 6
CHAR_SCALE = 0.18
GROUND_Y = SCREEN_HEIGHT - 60

# Коды клавиш для русской раскладки
KEY_RU_W = 1094
KEY_RU_A = 1092
KEY_RU_D = 1074

# КРОССПЛАТФОРМЕННАЯ поддержка стрелок
# Используем ТОЛЬКО константы Pygame для надежности
ARROW_UP_CODES = [pygame.K_UP]
ARROW_LEFT_CODES = [pygame.K_LEFT]
ARROW_RIGHT_CODES = [pygame.K_RIGHT]

# Определяем платформу
import platform
IS_MACOS = platform.system() == 'Darwin'
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Цвета
COLOR_SKY_TOP = (100, 160, 240)
COLOR_SKY_BOTTOM = (200, 230, 255)
COLOR_LAVA_BG = (220, 50, 20)
COLOR_LAVA_BUBBLE = (255, 200, 80)
COLOR_BRICK_MAIN = (166, 76, 58)
COLOR_BRICK_MORTAR = (80, 30, 20)

# Шрифты
font_title = pygame.font.SysFont("Arial", 80, bold=True)
font_btn = pygame.font.SysFont("Arial", 40, bold=True)
font_debug = pygame.font.SysFont("Arial", 16, bold=False)  # Для отладки

# Переменная для отладки
show_debug = False

# Кэш
sky_cache = None
lava_cache = None

# --- ХЕЛПЕРЫ ---
def load_and_scale(path, target_h):
    try:
        img = pygame.image.load(path).convert_alpha()
        scale = target_h / img.get_height()
        new_w = int(img.get_width() * scale)
        new_h = int(img.get_height() * scale)
        return pygame.transform.smoothscale(img, (new_w, new_h))
    except:
        surf = pygame.Surface((40, 60))
        surf.fill((255, 0, 255))
        return surf

def is_action_active(keys, key_list):
    """Проверяет нажатие клавиш с поддержкой раскладок"""
    for k in key_list:
        if isinstance(k, int) and k < len(keys) and keys[k]:
            return True
    return False

# --- ОКРУЖЕНИЕ ---
class Cloud:
    def __init__(self):
        self.reset(random_x=True)
        
    def reset(self, random_x=False):
        self.x = random.randint(0, SCREEN_WIDTH) if random_x else -200
        self.y = random.randint(20, 200)
        self.speed = random.uniform(0.2, 0.5)
        self.parts = []
        for _ in range(random.randint(4, 7)):
            self.parts.append({
                'dx': random.randint(0, 100),
                'dy': random.randint(0, 30),
                'r': random.randint(25, 45)
            })
            
    def update(self):
        self.x += self.speed
        if self.x > SCREEN_WIDTH + 100:
            self.reset(random_x=False)

    def draw(self, surface):
        for p in self.parts:
            center = (int(self.x + p['dx']), int(self.y + p['dy']))
            pygame.draw.circle(surface, (230, 240, 255), center, p['r'] + 2)
            pygame.draw.circle(surface, (255, 255, 255), center, p['r'])

clouds_list = [Cloud() for _ in range(5)]
lava_particles = []

def create_sky_cache():
    global sky_cache
    sky_cache = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        t = y / SCREEN_HEIGHT
        color = tuple(int(COLOR_SKY_TOP[i] + (COLOR_SKY_BOTTOM[i] - COLOR_SKY_TOP[i]) * t) for i in range(3))
        pygame.draw.line(sky_cache, color, (0, y), (SCREEN_WIDTH, y))

def create_lava_cache():
    global lava_cache
    lava_cache = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
    lava_cache.fill(COLOR_LAVA_BG)

def draw_world(surface, cam_x):
    if sky_cache:
        surface.blit(sky_cache, (0, 0))
    for c in clouds_list: 
        c.draw(surface)

def draw_platforms(surface, platforms, cam_x):
    brick_w, brick_h = 30, 15
    
    for p in platforms:
        if p.right < cam_x - 100 or p.left > cam_x + SCREEN_WIDTH + 100:
            continue
            
        rect_draw = pygame.Rect(p.x - int(cam_x), p.y, p.width, p.height)
        pygame.draw.rect(surface, COLOR_BRICK_MORTAR, rect_draw)
        
        # ИСПРАВЛЕНИЕ: Кирпичи рисуются относительно ПЛАТФОРМЫ, не камеры
        rows = (p.height // brick_h) + 1
        for row in range(rows):
            y_pos = row * brick_h
            x_shift = (brick_w // 2) if row % 2 else 0
            
            cols = (p.width + x_shift) // brick_w + 1
            for col in range(cols):
                brick_x = col * brick_w - x_shift
                brick_y = y_pos
                
                # Создаем кирпич ОТНОСИТЕЛЬНО платформы
                brick_rect = pygame.Rect(brick_x + 2, brick_y + 2, brick_w - 4, brick_h - 4)
                
                # Обрезаем по границам платформы (локальные координаты)
                platform_bounds = pygame.Rect(0, 0, p.width, p.height)
                clipped = brick_rect.clip(platform_bounds)
                
                if clipped.width > 0 and clipped.height > 0:
                    # Переводим в экранные координаты
                    screen_x = p.x + clipped.x - int(cam_x)
                    screen_y = p.y + clipped.y
                    screen_rect = pygame.Rect(screen_x, screen_y, clipped.width, clipped.height)
                    pygame.draw.rect(surface, COLOR_BRICK_MAIN, screen_rect)

def draw_lava(surface, cam_x):
    if lava_cache:
        surface.blit(lava_cache, (0, GROUND_Y))
    
    if len(lava_particles) < 20:
        lava_particles.append({
            'x': random.randint(0, SCREEN_WIDTH), 
            'y': SCREEN_HEIGHT, 
            's': random.randint(2, 6),
            'speed': random.uniform(1.5, 3)
        })
        
    for p in lava_particles[:]:
        p['y'] -= p['speed']
        if p['y'] < GROUND_Y:
            lava_particles.remove(p)
        else:
            pygame.draw.circle(surface, COLOR_LAVA_BUBBLE, (p['x'], int(p['y'])), p['s'])

# --- ИГРОК ---
class Player:
    def __init__(self, x, keys_map, sprites):
        self.target_h = SCREEN_HEIGHT * CHAR_SCALE
        
        self.idle_r = load_and_scale(sprites['idle'], self.target_h)
        self.idle_l = pygame.transform.flip(self.idle_r, True, False)
        
        self.run_r = [load_and_scale(s, self.target_h) for s in sprites['run']]
        self.run_l = [pygame.transform.flip(s, True, False) for s in self.run_r]
        
        self.jump_r = load_and_scale(sprites['jump'], self.target_h)
        self.jump_l = pygame.transform.flip(self.jump_r, True, False)
        
        self.fall_r = load_and_scale(sprites['fall'], self.target_h)
        self.fall_l = pygame.transform.flip(self.fall_r, True, False)
        
        self.start_x = x
        self.keys = keys_map
        self.rect = self.idle_r.get_rect()
        
        # СОБЫТИЙНАЯ МОДЕЛЬ: флаги вместо get_pressed()
        self.moving_left = False
        self.moving_right = False
        
        self.reset(0)

    def reset(self, y_pos):
        self.rect.x = self.start_x
        self.rect.bottom = y_pos
        self.vel_y = 0
        self.vel_x = 0
        self.on_ground = False
        self.is_jumping = False
        self.look_right = True
        self.anim_timer = 0
        self.coyote_timer = 0
        self.was_moving = False
        self.was_on_ground = True
        # Сбрасываем флаги движения
        self.moving_left = False
        self.moving_right = False

    def update(self, platforms):
        # СОБЫТИЙНАЯ МОДЕЛЬ: используем флаги вместо get_pressed()
        moving = False
        self.vel_x = 0
        
        # Проверяем флаги движения
        if self.moving_left:
            self.vel_x = -MOVE_SPEED
            self.look_right = False
            moving = True
        if self.moving_right:
            self.vel_x = MOVE_SPEED
            self.look_right = True
            moving = True
        
        # Применяем горизонтальное движение
        self.rect.x += self.vel_x
        
        # Горизонтальные коллизии
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_x > 0:
                    self.rect.right = p.left
                elif self.vel_x < 0:
                    self.rect.left = p.right
        
        # Гравитация
        self.vel_y += GRAVITY
        self.vel_y = min(self.vel_y, 15)
        
        # Применяем вертикальное движение
        old_y = self.rect.y
        self.rect.y += self.vel_y
        
        # Вертикальные коллизии
        self.was_on_ground = self.on_ground
        self.on_ground = False
        
        for p in platforms:
            if self.rect.colliderect(p):
                # Приземление на платформу
                if self.vel_y > 0 and old_y + self.rect.height <= p.top + 8:
                    self.rect.bottom = p.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.is_jumping = False
                    self.coyote_timer = 6
                    
                # Удар головой
                elif self.vel_y < 0 and old_y >= p.bottom - 8:
                    self.rect.top = p.bottom
                    self.vel_y = 0

        # Coyote time
        if not self.on_ground and self.was_on_ground:
            self.coyote_timer = 6
        elif not self.on_ground and self.coyote_timer > 0:
            self.coyote_timer -= 1
        
        self.was_moving = moving
        return moving

    def try_jump(self):
        if self.on_ground or self.coyote_timer > 0:
            self.vel_y = JUMP_FORCE
            self.is_jumping = True
            self.on_ground = False
            self.coyote_timer = 0

    def draw(self, surface, cam_x, moving):
        # ИСПРАВЛЕНИЕ: анимация обновляется только при движении
        if moving and self.on_ground:
            self.anim_timer += 1
        
        # Выбор спрайта с четкой логикой
        if not self.on_ground:
            # В воздухе
            if self.vel_y < -2:
                img = self.jump_r if self.look_right else self.jump_l
            else:
                img = self.fall_r if self.look_right else self.fall_l
        elif moving:
            # Бег
            frames = self.run_r if self.look_right else self.run_l
            frame_index = (self.anim_timer // 8) % len(frames)
            img = frames[frame_index]
        else:
            # Стоит
            img = self.idle_r if self.look_right else self.idle_l
        
        surface.blit(img, (int(self.rect.x - cam_x), int(self.rect.y)))


# --- НАСТРОЙКА ИГРОКОВ ---
# УПРОЩЕННАЯ поддержка клавиш - только константы Pygame
p1 = Player(100, 
    {
        'left': [pygame.K_a, ord('a')],  # A + русская А
        'right': [pygame.K_d, ord('d')],  # D + русская В
        'jump': [pygame.K_w, pygame.K_SPACE, ord('w')]  # W + пробел + русская Ц
    },
    {'idle': 'sprites/stoit1.png', 'run': ['sprites/run1.png', 'sprites/run2.png'], 
     'jump': 'sprites/jumpup.png', 'fall': 'sprites/falldown.png'}
)

p2 = Player(200, 
    {
        'left': [pygame.K_LEFT, pygame.K_j],  # Стрелка влево + J
        'right': [pygame.K_RIGHT, pygame.K_l],  # Стрелка вправо + L
        'jump': [pygame.K_UP, pygame.K_i, pygame.K_RCTRL]  # Стрелка вверх + I + RCtrl
    },
    {'idle': 'sprites/Kstoit.png', 'run': ['sprites/Krun1.png', 'sprites/Krun2.png'], 
     'jump': 'sprites/Kjump1.png', 'fall': 'sprites/Kfall1.png'}
)

# --- ГЕНЕРАЦИЯ УРОВНЯ ---
platforms = []
exit_zone = pygame.Rect(0, 0, 0, 0)
level_end_x = 0

def generate_level():
    """ИСПРАВЛЕННАЯ генерация - интересные, но проходимые платформы"""
    global platforms, exit_zone, level_end_x
    platforms = []
    
    # Стартовая платформа - широкая и низкая
    start_plat = pygame.Rect(50, GROUND_Y - 120, 450, 40)
    platforms.append(start_plat)
    
    curr_x = start_plat.right
    curr_y = start_plat.y
    
    # ИСПРАВЛЕНИЕ: Генерация платформ с гарантией проходимости
    platform_count = 15
    
    for i in range(platform_count):
        # Ширина платформы - достаточная для приземления
        w = random.randint(180, 320)
        
        # Расстояние - всегда проходимое (тест: jump_distance ~= 120-140px при vel=6)
        gap = random.randint(80, 160)
        
        # Изменение высоты - контролируемое
        # Максимальный прыжок вверх ~= 140px при JUMP_FORCE=-16
        # Позволяем прыгать вниз свободно, вверх - ограниченно
        
        if i < 3:
            # Первые платформы - легкие
            delta_h = random.randint(-40, 20)
        elif i < 8:
            # Средние - разнообразные
            delta_h = random.randint(-80, 60)
        else:
            # Последние - сложнее
            delta_h = random.randint(-100, 80)
        
        new_y = curr_y - delta_h
        
        # Границы по высоте
        new_y = max(100, min(new_y, GROUND_Y - 80))
        
        # Проверка проходимости по вертикали
        y_diff = abs(new_y - curr_y)
        if new_y < curr_y and y_diff > 120:
            # Слишком высоко - корректируем
            new_y = curr_y - 110
        
        curr_x += gap
        platforms.append(pygame.Rect(curr_x, new_y, w, 40))
        curr_y = new_y
        curr_x += w

    # Финишная платформа - большая и удобная
    final_plat = pygame.Rect(curr_x + 150, GROUND_Y - 130, 500, 40)
    platforms.append(final_plat)
    
    exit_zone = pygame.Rect(final_plat.centerx - 60, final_plat.top - 120, 120, 120)
    level_end_x = final_plat.right + 200
    
    # Правильный респаун на СТАРТОВОЙ платформе
    p1.reset(start_plat.top)
    p2.reset(start_plat.top)

# Создаем кэши
create_sky_cache()
create_lava_cache()
generate_level()

camera_x = 0.0

# --- UI ФУНКЦИЯ ---
def draw_ui(title_text, btn_text):
    draw_world(screen, 0)
    
    shadow = font_title.render(title_text, True, (0, 0, 0))
    txt = font_title.render(title_text, True, (255, 255, 255))
    screen.blit(shadow, (SCREEN_WIDTH//2 - txt.get_width()//2 + 4, 104))
    screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 100))
    
    btn_lbl = font_btn.render(btn_text, True, (255, 255, 255))
    btn_w = btn_lbl.get_width() + 60
    btn_h = 80
    btn_rect = pygame.Rect(SCREEN_WIDTH//2 - btn_w//2, 350, btn_w, btn_h)
    
    is_hover = btn_rect.collidepoint(pygame.mouse.get_pos())
    col = (50, 200, 50) if is_hover else (34, 139, 34)
    
    pygame.draw.rect(screen, col, btn_rect, border_radius=20)
    pygame.draw.rect(screen, (255, 255, 255), btn_rect, 3, 20)
    screen.blit(btn_lbl, (btn_rect.centerx - btn_lbl.get_width()//2, 
                          btn_rect.centery - btn_lbl.get_height()//2))
    
    return btn_rect, is_hover

# --- MAIN LOOP ---
running = True
last_keys_pressed = []  # Для отладки
shift_held = False  # Для комбинации Shift+0

while running:
    click = False
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            click = True
        
        # Отслеживание Shift
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
                shift_held = True
        if event.type == pygame.KEYUP:
            if event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
                shift_held = False
        
        # Переключение отладки по Shift+0
        if event.type == pygame.KEYDOWN and event.key == pygame.K_0 and shift_held:
            show_debug = not show_debug
        
        # Диагностика
        if event.type == pygame.KEYDOWN and show_debug:
            last_keys_pressed.append(event.key)
            if len(last_keys_pressed) > 10:
                last_keys_pressed.pop(0)
        
        # СОБЫТИЙНАЯ ОБРАБОТКА УПРАВЛЕНИЯ (macOS-friendly!)
        if current_state == STATE_PLAYING:
            if event.type == pygame.KEYDOWN:
                # Прыжки
                if event.key in p1.keys['jump']:
                    p1.try_jump()
                if event.key in p2.keys['jump']:
                    p2.try_jump()
                
                # Движение НАЖАТО
                if event.key in p1.keys['left']:
                    p1.moving_left = True
                if event.key in p1.keys['right']:
                    p1.moving_right = True
                if event.key in p2.keys['left']:
                    p2.moving_left = True
                if event.key in p2.keys['right']:
                    p2.moving_right = True
            
            if event.type == pygame.KEYUP:
                # Движение ОТПУЩЕНО
                if event.key in p1.keys['left']:
                    p1.moving_left = False
                if event.key in p1.keys['right']:
                    p1.moving_right = False
                if event.key in p2.keys['left']:
                    p2.moving_left = False
                if event.key in p2.keys['right']:
                    p2.moving_right = False

    # --- ЛОГИКА ---
    if current_state == STATE_MENU:
        for c in clouds_list: 
            c.update()
        btn, hover = draw_ui("КООП ПЛАТФОРМЕР", "НАЧАТЬ ПРИКЛЮЧЕНИЕ")
        if click and hover:
            generate_level()
            current_state = STATE_PLAYING

    elif current_state == STATE_WIN:
        for c in clouds_list: 
            c.update()
        btn, hover = draw_ui("ПОБЕДА!", "НОВЫЙ УРОВЕНЬ")
        if click and hover:
            generate_level()
            current_state = STATE_PLAYING

    elif current_state == STATE_PLAYING:
        for c in clouds_list: 
            c.update()
        
        # Обновление игроков
        mv1 = p1.update(platforms)
        mv2 = p2.update(platforms)
        
        # Проверка смерти в лаве
        if p1.rect.top > GROUND_Y + 50 or p2.rect.top > GROUND_Y + 50:
            generate_level()
            
        # Плавная камера
        target_cam = (p1.rect.centerx + p2.rect.centerx) / 2 - SCREEN_WIDTH / 2
        target_cam = max(0.0, min(target_cam, level_end_x - SCREEN_WIDTH))
        camera_x += (target_cam - camera_x) * 0.12

        # Победа
        if p1.rect.colliderect(exit_zone) and p2.rect.colliderect(exit_zone):
            current_state = STATE_WIN

        # --- ОТРИСОВКА ---
        draw_world(screen, camera_x)
        draw_platforms(screen, platforms, camera_x)
        draw_lava(screen, camera_x)
        
        # Зона выхода
        ex = exit_zone.copy()
        ex.x -= int(camera_x)
        pygame.draw.rect(screen, (255, 215, 0), ex, 4, border_radius=10)
        
        # Игроки
        p1.draw(screen, camera_x, mv1)
        p2.draw(screen, camera_x, mv2)
        
        # ОТЛАДОЧНАЯ ИНФОРМАЦИЯ (Shift+0 для включения/выключения)
        if show_debug:
            y_offset = 10
            
            # Информация о системе
            platform_name = "macOS" if IS_MACOS else ("Windows" if IS_WINDOWS else "Linux")
            debug_sys = font_debug.render(f"Platform: {platform_name} | Shift+0 to toggle | EVENT-DRIVEN MODEL", True, (255, 255, 0))
            screen.blit(debug_sys, (10, y_offset))
            y_offset += 20
            
            # Информация о клавишах
            debug_text = font_debug.render("Pressed keys (event.key codes):", True, (255, 255, 0))
            screen.blit(debug_text, (10, y_offset))
            y_offset += 20
            
            if last_keys_pressed:
                keys_str = ", ".join([str(k) for k in last_keys_pressed[-5:]])
                debug_text2 = font_debug.render(f"Last: {keys_str}", True, (255, 255, 0))
                screen.blit(debug_text2, (10, y_offset))
                y_offset += 20
            
            # Константы стрелок
            debug_text3 = font_debug.render(f"pygame.K_UP={pygame.K_UP}, K_LEFT={pygame.K_LEFT}, K_RIGHT={pygame.K_RIGHT}", True, (255, 255, 0))
            screen.blit(debug_text3, (10, y_offset))
            y_offset += 20
            
            # Альтернативные управления
            debug_alt = font_debug.render(f"P1: A/D/W/Space | P2: Arrows or I(up)/J(left)/L(right)", True, (255, 200, 0))
            screen.blit(debug_alt, (10, y_offset))
            y_offset += 20
            
            # Флаги движения (самое важное для диагностики!)
            debug_flags = font_debug.render(
                f"P1 flags: left={p1.moving_left}, right={p1.moving_right} | " +
                f"P2 flags: left={p2.moving_left}, right={p2.moving_right}", 
                True, (0, 255, 0)
            )
            screen.blit(debug_flags, (10, y_offset))
            y_offset += 20
            
            # Позиции игроков
            debug_text4 = font_debug.render(
                f"P1: x={int(p1.rect.x)}, y={int(p1.rect.y)}, vel_x={p1.vel_x:.1f}, ground={p1.on_ground}", 
                True, (100, 200, 255)
            )
            screen.blit(debug_text4, (10, y_offset))
            y_offset += 20
            
            debug_text5 = font_debug.render(
                f"P2: x={int(p2.rect.x)}, y={int(p2.rect.y)}, vel_x={p2.vel_x:.1f}, ground={p2.on_ground}", 
                True, (255, 100, 200)
            )
            screen.blit(debug_text5, (10, y_offset))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()