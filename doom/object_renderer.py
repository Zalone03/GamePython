import pygame as pg
from settings import *


class ObjectRenderer:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.wall_textures = self.load_wall_textures()
        self.sky_image = self.get_texture('resources/textures/sky.png', (WIDTH, HALF_HEIGHT))
        self.sky_offset = 0
        self.blood_screen = self.get_texture('resources/textures/blood_screen.png', RES)
        self.digit_size = 90
        self.digit_images = [self.get_texture(f'resources/textures/digits/{i}.png', [self.digit_size] * 2)
                             for i in range(11)]
        self.digits = dict(zip(map(str, range(11)), self.digit_images))
        self.game_over_image = self.get_texture('resources/textures/game_over.png', RES)
        self.win_image = self.get_texture('resources/textures/win.png', RES)
        # Fontes do HUD (tamanho proporcional à altura da tela)
        self.font = pg.font.Font(None, HEIGHT // 14)
        self.big_font = pg.font.Font(None, HEIGHT // 6)

    def draw(self):
        self.draw_background()
        self.render_game_objects()
        self.draw_player_health()

    def win(self):
        self.screen.blit(self.win_image, (0, 0))

    def game_over(self):
        self.screen.blit(self.game_over_image, (0, 0))

    #===========
    # HUD das ondas e armas
    #===========

    # Escreve um texto com sombra (pos é o canto de cima à esquerda, ou o centro se center=True)
    def draw_text(self, text, font, color, pos, center=False):
        image = font.render(text, True, color)
        shadow = font.render(text, True, (0, 0, 0))
        rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
        self.screen.blit(shadow, rect.move(2, 2))
        self.screen.blit(image, rect)

    # Onda, inimigos restantes, armas e o aviso entre ondas
    def draw_hud(self):
        handler = self.game.object_handler
        margin = HEIGHT // 40
        line = self.font.get_height()
        right = WIDTH - margin - self.font.size('INIMIGOS 00')[0]
        self.draw_text(f'ONDA {handler.wave}/{TOTAL_WAVES}', self.font, (255, 220, 80), (right, margin))
        self.draw_text(f'INIMIGOS {handler.enemies_left}', self.font, (255, 255, 255), (right, margin + line))
        self.draw_weapons(margin, line)
        if handler.waiting_wave:
            self.draw_wave_banner(handler)

    # Lista as armas no canto de baixo, com a escolhida em amarelo
    def draw_weapons(self, margin, line):
        for i, weapon in enumerate(self.game.weapons):
            color = (255, 220, 80) if weapon is self.game.weapon else (160, 160, 160)
            self.draw_text(f'[{i + 1}] {weapon.name}', self.font, color, (margin, HEIGHT - margin - line * (2 - i)))

    # Aviso no meio da tela durante a pausa entre ondas
    def draw_wave_banner(self, handler):
        seconds = max(0, handler.next_wave_time - pg.time.get_ticks()) // 1000 + 1
        self.draw_text(f'ONDA {handler.wave} LIMPA!', self.big_font, (255, 220, 80), (HALF_WIDTH, HALF_HEIGHT - HEIGHT // 10), True)
        self.draw_text(f'PRÓXIMA ONDA EM {seconds}', self.font, (255, 255, 255), (HALF_WIDTH, HALF_HEIGHT + HEIGHT // 20), True)

    # Monta a tela final: imagem de vitória ou derrota + até que onda o jogador chegou
    def end_screen(self, won):
        image = (self.win_image if won else self.game_over_image).copy()
        screen = self.screen
        self.screen = image
        wave = self.game.object_handler.wave
        text = f'VOCÊ VENCEU AS {TOTAL_WAVES} ONDAS!' if won else f'VOCÊ CHEGOU ATÉ A ONDA {wave}'
        self.draw_text(text, self.font, (255, 220, 80), (HALF_WIDTH, HEIGHT - HEIGHT // 8), True)
        self.screen = screen
        return image

    def draw_player_health(self):
        health = str(self.game.player.health)
        for i, char in enumerate(health):
            self.screen.blit(self.digits[char], (i * self.digit_size, 0))
        self.screen.blit(self.digits['10'], ((i + 1) * self.digit_size, 0))

    def player_damage(self):
        self.screen.blit(self.blood_screen, (0, 0))

    def draw_background(self):
        self.sky_offset = (self.sky_offset + 4.5 * self.game.player.rel) % WIDTH
        self.screen.blit(self.sky_image, (-self.sky_offset, 0))
        self.screen.blit(self.sky_image, (-self.sky_offset + WIDTH, 0))
        # floor
        pg.draw.rect(self.screen, FLOOR_COLOR, (0, HALF_HEIGHT, WIDTH, HEIGHT))

    def render_game_objects(self):
        list_objects = sorted(self.game.raycasting.objects_to_render, key=lambda t: t[0], reverse=True)
        for depth, image, pos in list_objects:
            self.screen.blit(image, pos)

    @staticmethod
    def get_texture(path, res=(TEXTURE_SIZE, TEXTURE_SIZE)):
        texture = pg.image.load(path).convert_alpha()
        return pg.transform.scale(texture, res)

    def load_wall_textures(self):
        return {
            1: self.get_texture('resources/textures/1.png'),
            2: self.get_texture('resources/textures/2.png'),
            3: self.get_texture('resources/textures/3.png'),
            4: self.get_texture('resources/textures/4.png'),
            5: self.get_texture('resources/textures/5.png'),
        }