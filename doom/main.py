import pygame as pg
import sys
from settings import *
from map import *
from player import *
from raycasting import *
from object_renderer import *
from sprite_object import *
from object_handler import *
from weapon import *
from sound import *
from pathfinding import *


class Game:
    def __init__(self):
        pg.init()
        pg.mouse.set_visible(False)
        self.screen = pg.display.set_mode(RES)
        pg.event.set_grab(True)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.last_global_trigger = 0
        self.new_game()

    def new_game(self):
        self.map = Map(self)
        self.player = Player(self)
        self.object_renderer = ObjectRenderer(self)
        self.raycasting = RayCasting(self)
        self.object_handler = ObjectHandler(self)
        # Armas: [1] espingarda e [2] minigun
        self.weapons = [Weapon(self), Minigun(self)]
        self.weapon = self.weapons[0]
        self.sound = Sound(self)
        self.pathfinding = PathFinding(self)
        # Fim de jogo: imagem mostrada e momento em que o jogo fecha
        self.end_image = None
        self.end_time = 0
        pg.mixer.music.play(-1)

    #===========
    # Fim de jogo
    #===========

    # Mostra vitória ou derrota por alguns segundos sem travar (o jogo fecha depois)
    def finish(self, won):
        if self.end_image:
            return
        self.end_image = self.object_renderer.end_screen(won)
        self.end_time = pg.time.get_ticks() + END_SCREEN_TIME

    # Desenha a tela final e fecha o jogo quando o tempo acabar
    def show_end_screen(self):
        self.screen.blit(self.end_image, (0, 0))
        pg.display.flip()
        self.delta_time = self.clock.tick(30)
        if pg.time.get_ticks() >= self.end_time:
            pg.quit()
            sys.exit()

    #===========
    # Armas
    #===========

    # Troca de arma pelas teclas 1 e 2
    def switch_weapon(self, index):
        if self.weapons[index] is self.weapon:
            return
        self.weapon = self.weapons[index]
        self.weapon.reloading = False
        self.player.shot = False

    #===========
    # Laço do jogo
    #===========

    def update(self):
        self.player.update()
        self.raycasting.update()
        self.object_handler.update()
        self.weapon.update()
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'{self.clock.get_fps() :.1f}')

    def draw(self):
        # self.screen.fill('black')
        self.object_renderer.draw()
        self.weapon.draw()
        self.object_renderer.draw_hud()
        # self.map.draw()
        # self.player.draw()

    # Liga o gatilho das animações de morte a cada GLOBAL_TRIGGER_TIME ms (sem depender de timer)
    def update_global_trigger(self):
        now = pg.time.get_ticks()
        self.global_trigger = now - self.last_global_trigger >= GLOBAL_TRIGGER_TIME
        if self.global_trigger:
            self.last_global_trigger = now

    def check_events(self):
        self.update_global_trigger()
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()
            elif event.type == pg.KEYDOWN and event.key == pg.K_1:
                self.switch_weapon(0)
            elif event.type == pg.KEYDOWN and event.key == pg.K_2:
                self.switch_weapon(1)
            if not self.end_image:
                self.player.single_fire_event(event)

    def run(self):
        while True:
            self.check_events()
            if self.end_image:
                self.show_end_screen()
                continue
            self.update()
            self.draw()


if __name__ == '__main__':
    game = Game()
    game.run()
