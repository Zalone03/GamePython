from sprite_object import *


class Weapon(AnimatedSprite):
    def __init__(self, game, path='resources/sprites/weapon/shotgun/0.png', scale=0.4, animation_time=90):
        super().__init__(game=game, path=path, scale=scale, animation_time=animation_time)
        self.images = deque(
            [pg.transform.smoothscale(img, (self.image.get_width() * scale, self.image.get_height() * scale))
             for img in self.images])
        self.weapon_pos = (HALF_WIDTH - self.images[0].get_width() // 2, HEIGHT - self.images[0].get_height())
        self.reloading = False
        self.num_images = len(self.images)
        self.frame_counter = 0
        self.damage = 50
        # Nome no HUD, tiro por clique e momento do último tiro
        self.name = 'ESPINGARDA'
        self.automatic = False
        self.last_shot = 0

    # Som do tiro
    @property
    def fire_sound(self):
        return self.game.sound.shotgun

    def animate_shot(self):
        if self.reloading:
            self.game.player.shot = False
            if self.animation_trigger:
                self.images.rotate(-1)
                self.image = self.images[0]
                self.frame_counter += 1
                if self.frame_counter == self.num_images:
                    self.reloading = False
                    self.frame_counter = 0

    def draw(self):
        self.game.screen.blit(self.images[0], self.weapon_pos)

    def update(self):
        self.check_animation_time()
        self.animate_shot()


#===========
# Minigun
#===========

# Arma automática: muitas balas fracas enquanto o botão estiver segurado
class Minigun:
    # Pasta dos quadros: 0-7.png giram os canos, fogo/0-7.png são os mesmos com o clarão do tiro
    PATH = 'resources/sprites/weapon/minigun'

    # Largura da arma em relação à largura da tela
    SCREEN_RATIO = 0.5

    def __init__(self, game):
        self.game = game
        self.name = 'MINIGUN'
        self.automatic = True
        self.damage = MINIGUN_DAMAGE
        self.reloading = False
        self.last_shot = 0
        self.frame = 0
        self.images = [self.load_frame(f'{self.PATH}/{i}.png') for i in range(8)]
        self.fire_images = [self.load_frame(f'{self.PATH}/fogo/{i}.png') for i in range(8)]
        width, height = self.images[0].get_size()
        self.weapon_pos = (HALF_WIDTH - width // 2, HEIGHT - height)

    # Carrega um quadro e amplia sem borrar os pixels (mesmo tamanho em qualquer resolução)
    @classmethod
    def load_frame(cls, path):
        image = pg.image.load(path).convert_alpha()
        width = int(WIDTH * cls.SCREEN_RATIO)
        height = int(image.get_height() * width / image.get_width())
        return pg.transform.scale(image, (width, height))

    # Som do tiro
    @property
    def fire_sound(self):
        return self.game.sound.minigun

    # Libera o próximo tiro depois de MINIGUN_FIRE_DELAY e gira os canos a cada tiro
    def update(self):
        if not self.reloading:
            return
        self.game.player.shot = False
        if pg.time.get_ticks() - self.last_shot >= MINIGUN_FIRE_DELAY:
            self.reloading = False
            self.frame = (self.frame + 1) % len(self.images)

    # Logo depois de cada tiro mostra o quadro com o clarão
    def draw(self):
        firing = pg.time.get_ticks() - self.last_shot < 45
        images = self.fire_images if firing else self.images
        self.game.screen.blit(images[self.frame], self.weapon_pos)
