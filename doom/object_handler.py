from sprite_object import *
from npc import *
from random import choices, randrange


class ObjectHandler:
    def __init__(self, game):
        self.game = game
        self.sprite_list = []
        self.npc_list = []
        self.npc_sprite_path = 'resources/sprites/npc/'
        self.static_sprite_path = 'resources/sprites/static_sprites/'
        self.anim_sprite_path = 'resources/sprites/animated_sprites/'
        add_sprite = self.add_sprite
        add_npc = self.add_npc
        self.npc_positions = {}

        # Ondas: onda atual, se está na pausa entre ondas e quando a próxima começa
        self.npc_types = [SoldierNPC, CacoDemonNPC, CyberDemonNPC]
        self.wave = 0
        self.waiting_wave = False
        self.next_wave_time = 0
        self.start_next_wave()

        # sprite map
        add_sprite(AnimatedSprite(game))
        add_sprite(AnimatedSprite(game, pos=(1.5, 1.5)))
        add_sprite(AnimatedSprite(game, pos=(1.5, 7.5)))
        add_sprite(AnimatedSprite(game, pos=(5.5, 3.25)))
        add_sprite(AnimatedSprite(game, pos=(5.5, 4.75)))
        add_sprite(AnimatedSprite(game, pos=(7.5, 2.5)))
        add_sprite(AnimatedSprite(game, pos=(7.5, 5.5)))
        add_sprite(AnimatedSprite(game, pos=(14.5, 1.5)))
        add_sprite(AnimatedSprite(game, pos=(14.5, 4.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'red_light/0.png', pos=(14.5, 5.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'red_light/0.png', pos=(14.5, 7.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'red_light/0.png', pos=(12.5, 7.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'red_light/0.png', pos=(9.5, 7.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'red_light/0.png', pos=(14.5, 12.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'red_light/0.png', pos=(9.5, 20.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'red_light/0.png', pos=(10.5, 20.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'red_light/0.png', pos=(3.5, 14.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'red_light/0.png', pos=(3.5, 18.5)))
        add_sprite(AnimatedSprite(game, pos=(14.5, 24.5)))
        add_sprite(AnimatedSprite(game, pos=(14.5, 30.5)))
        add_sprite(AnimatedSprite(game, pos=(1.5, 30.5)))
        add_sprite(AnimatedSprite(game, pos=(1.5, 24.5)))

    #===========
    # Ondas
    #===========

    # Quantos inimigos a onda atual tem
    def wave_size(self):
        return WAVE_BASE_ENEMIES + WAVE_EXTRA_ENEMIES * (self.wave - 1)

    # Chance de cada tipo (soldado, caco, cyber): ondas mais altas trazem inimigos mais fortes
    def wave_weights(self):
        step = self.wave - 1
        return [max(70 - 5 * step, 25), 20 + 3 * step, 10 + 2 * step]

    # Escolhe um lugar livre, longe do jogador, para um inimigo nascer
    def free_spawn_position(self):
        player_x, player_y = self.game.player.map_pos
        while True:
            pos = randrange(self.game.map.cols), randrange(self.game.map.rows)
            far = math.hypot(pos[0] - player_x, pos[1] - player_y) >= SPAWN_MIN_DIST
            taken = pos in self.game.map.world_map or pos in self.npc_positions
            if far and not taken:
                return pos

    # Começa a próxima onda: tira os corpos da onda anterior e cria os novos inimigos
    def start_next_wave(self):
        self.wave += 1
        self.waiting_wave = False
        self.npc_list = [npc for npc in self.npc_list if npc.alive]
        for _ in range(self.wave_size()):
            npc = choices(self.npc_types, self.wave_weights())[0]
            x, y = self.free_spawn_position()
            self.add_npc(npc(self.game, pos=(x + 0.5, y + 0.5)))
            self.npc_positions = {npc.map_pos for npc in self.npc_list if npc.alive}

    # Onda limpa: espera a pausa e chama a próxima (ou vence depois da última)
    def check_wave(self):
        if self.npc_positions:
            return
        now = pg.time.get_ticks()
        if self.wave >= TOTAL_WAVES:
            self.game.finish(won=True)
        elif not self.waiting_wave:
            self.waiting_wave = True
            self.next_wave_time = now + WAVE_PAUSE
        elif now >= self.next_wave_time:
            self.start_next_wave()

    # Inimigos vivos na onda atual
    @property
    def enemies_left(self):
        return sum(npc.alive for npc in self.npc_list)

    def update(self):
        self.npc_positions = {npc.map_pos for npc in self.npc_list if npc.alive}
        [sprite.update() for sprite in self.sprite_list]
        [npc.update() for npc in self.npc_list]
        self.check_wave()

    def add_npc(self, npc):
        self.npc_list.append(npc)

    def add_sprite(self, sprite):
        self.sprite_list.append(sprite)
