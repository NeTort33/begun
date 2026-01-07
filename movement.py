import pygame
import sys

# --- КОНСТАНТЫ И НАСТРОЙКИ ---
pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Платформер с физикой")
clock = pygame.time.Clock()

# Цвета
SKY_BLUE = (135, 206, 235)
GROUND_COLOR = (34, 139, 34)

# Настройки мира
GROUND_LEVEL = SCREEN_HEIGHT - 100 
GRAVITY = 0.8       # Сила притяжения (чем больше, тем тяжелее персонаж)
JUMP_FORCE = -15    # Сила прыжка (чем меньше число, тем выше прыжок, т.к. ось Y идет вниз)

# МАСШТАБ
# Если спрайты большие — ставь 0.2 или 0.3
# Если спрайты маленькие (пиксельные) — ставь 2.0 или 3.0
SCALE_FACTOR = 0.25 

# --- ФУНКЦИЯ ЗАГРУЗКИ ---
def load_scaled_image(path, scale):
    try:
        img = pygame.image.load(path).convert_alpha()
        new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
        # Используем scale, а не smoothscale для пиксель-арта, чтобы было четче
        return pygame.transform.scale(img, new_size) 
    except pygame.error as e:
        print(f"Не найден файл: {path}")
        sys.exit()

# --- ЗАГРУЗКА СПРАЙТОВ (Твои новые названия) ---
# 1. Анимация покоя (дыхание)
anim_idle_right = [
    load_scaled_image('sprites/stoit1.png', SCALE_FACTOR),
    #load_scaled_image('sprites/stoit2.png', SCALE_FACTOR)
]

# 2. Анимация бега
anim_run_right = [
    load_scaled_image('sprites/run1.png', SCALE_FACTOR),
    load_scaled_image('sprites/run4.png', SCALE_FACTOR),

]

# 3. Прыжок и падение
img_jump_right = load_scaled_image('sprites/jumpup.png', SCALE_FACTOR)
img_fall_right = load_scaled_image('sprites/falldown.png', SCALE_FACTOR)

# --- СОЗДАНИЕ ЗЕРКАЛЬНЫХ КОПИЙ (ВЛЕВО) ---
def flip_list(images):
    return [pygame.transform.flip(img, True, False) for img in images]

anim_idle_left = flip_list(anim_idle_right)
anim_run_left = flip_list(anim_run_right)
img_jump_left = pygame.transform.flip(img_jump_right, True, False)
img_fall_left = pygame.transform.flip(img_fall_right, True, False)

# Берем размеры персонажа по первому кадру
CHAR_WIDTH = anim_idle_right[0].get_width()
CHAR_HEIGHT = anim_idle_right[0].get_height()

# --- ПЕРЕМЕННЫЕ ИГРОКА ---
player_x = 50
player_y = GROUND_LEVEL - CHAR_HEIGHT
player_speed = 5
player_vel_y = 0      # Вертикальная скорость (для прыжков)
is_jumping = False    # Находится ли персонаж в воздухе
last_dir_left = False # Куда смотрел в последний раз
anim_count = 0        # Счетчик анимации

# --- ОТРИСОВКА ---
def draw_window():
    global anim_count
    
    screen.fill(SKY_BLUE)
    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_LEVEL, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_LEVEL))

    # Определяем, какой спрайт рисовать
    current_image = None
    
    # 1. Если персонаж в воздухе (ПРЫЖОК или ПАДЕНИЕ)
    if is_jumping:
        if player_vel_y < 0: # Летит вверх
            current_image = img_jump_left if last_dir_left else img_jump_right
        else: # Летит вниз
            current_image = img_fall_left if last_dir_left else img_fall_right
    
    # 2. Если персонаж на земле
    else:
        keys = pygame.key.get_pressed()
        # Замедляем анимацию (меняем кадр каждые 10 тиков)
        speed_div = 10 
        
        if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
            # БЕГ
            frames = anim_run_left if last_dir_left else anim_run_right
            if anim_count >= len(frames) * speed_div:
                anim_count = 0
            current_image = frames[anim_count // speed_div]
            anim_count += 1
        else:
            # ПОКОЙ (IDLE) - тоже анимируем (stoit1 -> stoit2)
            # Делаем дыхание медленнее (каждые 20 тиков)
            idle_speed_div = 20
            frames = anim_idle_left if last_dir_left else anim_idle_right
            if anim_count >= len(frames) * idle_speed_div:
                anim_count = 0
            current_image = frames[anim_count // idle_speed_div]
            anim_count += 1

    screen.blit(current_image, (player_x, player_y))
    pygame.display.update()

# --- ГЛАВНЫЙ ЦИКЛ ---
while True:
    clock.tick(60) # 60 FPS
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        # Обработка нажатия прыжка (одиночное нажатие)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not is_jumping:
                player_vel_y = JUMP_FORCE
                is_jumping = True

    keys = pygame.key.get_pressed()

    # Движение влево/вправо
    if keys[pygame.K_LEFT] and player_x > 0:
        player_x -= player_speed
        last_dir_left = True
    elif keys[pygame.K_RIGHT] and player_x < SCREEN_WIDTH - CHAR_WIDTH:
        player_x += player_speed
        last_dir_left = False
    else:
        # Если стоим и не прыгаем, не сбрасываем anim_count полностью, 
        # чтобы анимация "дыхания" не дергалась, но это опционально.
        pass

    # --- ФИЗИКА ---
    player_vel_y += GRAVITY       # Применяем гравитацию
    player_y += player_vel_y      # Двигаем персонажа по вертикали

    # Проверка столкновения с землей
    if player_y + CHAR_HEIGHT >= GROUND_LEVEL:
        player_y = GROUND_LEVEL - CHAR_HEIGHT # Ставим ровно на землю
        is_jumping = False
        player_vel_y = 0
    else:
        is_jumping = True # Если мы выше земли, значит мы падаем или прыгаем

    draw_window()