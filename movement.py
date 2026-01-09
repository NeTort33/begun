import pygame
import sys

# --- НАСТРОЙКИ ЭКРАНА ---
pygame.init()
# Можешь менять эти значения, персонажи подстроятся сами
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Платформер: Динамический масштаб")
clock = pygame.time.Clock()

# --- ФИЗИКА И МИР ---
GRAVITY = 0.8
JUMP_FORCE = -16
GROUND_LEVEL_OFFSET = 100 # Высота земли от нижнего края
GROUND_Y = SCREEN_HEIGHT - GROUND_LEVEL_OFFSET

# --- ДИНАМИЧЕСКИЙ МАСШТАБ ---
# Вычисляем масштаб так, чтобы персонаж был высотой примерно 1/6 экрана
# Если твои исходные спрайты около 100px, этот коэффициент сделает их идеальными
CHAR_TARGET_HEIGHT = SCREEN_HEIGHT * 0.15 

def load_and_scale(path, target_h):
    try:
        img = pygame.image.load(path).convert_alpha()
        # Вычисляем коэффициент пропорционально целевой высоте
        scale = target_h / img.get_height()
        new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
        return pygame.transform.scale(img, new_size)
    except:
        # Если файла нет, создаем цветной квадрат, чтобы код не вылетал
        surf = pygame.Surface((30, 50))
        surf.fill((255, 0, 0))
        return surf

# --- КЛАСС ИГРОКА ---
class Player:
    def __init__(self, x, controls, paths):
        self.idle_r = [load_and_scale(paths['idle'], CHAR_TARGET_HEIGHT)]
        self.run_r = [load_and_scale(p, CHAR_TARGET_HEIGHT) for p in paths['run']]
        self.jump_r = load_and_scale(paths['jump'], CHAR_TARGET_HEIGHT)
        self.fall_r = load_and_scale(paths['fall'], CHAR_TARGET_HEIGHT)
        
        # Отражение для движения влево
        self.idle_l = [pygame.transform.flip(img, True, False) for img in self.idle_r]
        self.run_l = [pygame.transform.flip(img, True, False) for img in self.run_r]
        self.jump_l = pygame.transform.flip(self.jump_r, True, False)
        self.fall_l = pygame.transform.flip(self.fall_r, True, False)

        self.rect = self.idle_r[0].get_rect(topleft=(x, GROUND_Y - 100))
        self.controls = controls
        self.vel_y = 0
        self.is_jumping = False
        self.look_left = False
        self.anim_count = 0
        self.moving = False

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.moving = False
        
        if keys[self.controls['left']] and self.rect.left > 0:
            self.rect.x -= 6
            self.look_left = True
            self.moving = True
        if keys[self.controls['right']] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += 6
            self.look_left = False
            self.moving = True
            
    def jump(self):
        if not self.is_jumping:
            self.vel_y = JUMP_FORCE
            self.is_jumping = True

    def apply_physics(self):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vel_y = 0
            self.is_jumping = False

    def draw(self):
        self.anim_count += 1
        div = 8 # Скорость анимации
        
        # Выбор текущего спрайта
        if self.is_jumping:
            if self.vel_y < 0:
                img = self.jump_l if self.look_left else self.jump_r
            else:
                img = self.fall_l if self.look_left else self.fall_r
        elif self.moving:
            frames = self.run_l if self.look_left else self.run_r
            img = frames[(self.anim_count // div) % len(frames)]
        else:
            frames = self.idle_l if self.look_left else self.idle_r
            img = frames[(self.anim_count // div) % len(frames)]
            
        screen.blit(img, self.rect)

# --- СОЗДАНИЕ ПЕРСОНАЖЕЙ ---
player1 = Player(200, 
    {'left': pygame.K_a, 'right': pygame.K_d, 'up': pygame.K_w}, 
    {'idle': 'sprites/stoit1.png', 'run': ['sprites/run1.png', 'sprites/run2.png'], 
     'jump': 'sprites/jumpup.png', 'fall': 'sprites/falldown.png'})

player2 = Player(600, 
    {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'up': pygame.K_UP}, 
    {'idle': 'sprites/Kstoit.png', 'run': ['sprites/Krun1.png', 'sprites/Krun2.png'], 
     'jump': 'sprites/Kjump1.png', 'fall': 'sprites/Kfall1.png'})

# --- ГЛАВНЫЙ ЦИКЛ ---
while True:
    screen.fill((135, 206, 235)) # Небо
    pygame.draw.rect(screen, (34, 139, 34), (0, GROUND_Y, SCREEN_WIDTH, GROUND_LEVEL_OFFSET)) # Земля

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_w:
                player1.jump()
            if event.key == pygame.K_UP:
                player2.jump()

    for p in [player1, player2]:
        p.handle_input()
        p.apply_physics()
        p.draw()

    pygame.display.update()
    clock.tick(60)