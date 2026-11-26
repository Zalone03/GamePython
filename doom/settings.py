import math

# game settings
RES = WIDTH, HEIGHT = 1600, 900
# RES = WIDTH, HEIGHT = 1920, 1080
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
FPS = 0

PLAYER_POS = 1.5, 5  # mini_map
PLAYER_ANGLE = 0
PLAYER_SPEED = 0.004
PLAYER_ROT_SPEED = 0.002
PLAYER_SIZE_SCALE = 60
PLAYER_MAX_HEALTH = 100

MOUSE_SENSITIVITY = 0.0003
MOUSE_MAX_REL = 40
MOUSE_BORDER_LEFT = 100
MOUSE_BORDER_RIGHT = WIDTH - MOUSE_BORDER_LEFT

FLOOR_COLOR = (30, 30, 30)

FOV = math.pi / 3
HALF_FOV = FOV / 2
NUM_RAYS = WIDTH // 2
HALF_NUM_RAYS = NUM_RAYS // 2
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 20

SCREEN_DIST = HALF_WIDTH / math.tan(HALF_FOV)
SCALE = WIDTH // NUM_RAYS

TEXTURE_SIZE = 256
HALF_TEXTURE_SIZE = TEXTURE_SIZE // 2

#===========
# Ondas
#===========

# Quantidade de ondas até a vitória
TOTAL_WAVES = 10

# Inimigos na primeira onda e quantos a mais em cada onda seguinte
WAVE_BASE_ENEMIES = 4
WAVE_EXTRA_ENEMIES = 2

# Pausa entre uma onda e outra (ms)
WAVE_PAUSE = 3000

# Distância mínima (em blocos) entre o jogador e um inimigo que nasce
SPAWN_MIN_DIST = 6

# Tempo que a tela de vitória ou derrota fica antes de o jogo fechar (ms)
END_SCREEN_TIME = 4000

# Intervalo das animações de morte dos inimigos (ms)
GLOBAL_TRIGGER_TIME = 40

#===========
# Armas
#===========

# Minigun: dano por bala e tempo entre balas (ms)
MINIGUN_DAMAGE = 14
MINIGUN_FIRE_DELAY = 90