import math
import pygame as pg
from config import *

#===========
# Jogador
#===========

# Movimento no estilo DOOM: WASD anda, setas ou mouse giram, Shift corre
class Jogador:
    def __init__(self, jogo):
        self.jogo = jogo
        self.x, self.y = POSICAO_INICIAL
        self.angulo = 0.0
        self.folego = FOLEGO_MAX
        self.correndo = False
        self.andando = False
        # Movimento do mouse acumulado desde o último quadro
        self.giro_mouse = 0
        self.proximo_passo = 0

    # Diz se o jogador cabe em (x, y) sem encostar em parede
    def cabe(self, x, y):
        livre = self.jogo.mapa.livre
        r = RAIO_JOGADOR
        return (livre(math.floor(x - r), math.floor(y - r)) and livre(math.floor(x + r), math.floor(y - r))
                and livre(math.floor(x - r), math.floor(y + r)) and livre(math.floor(x + r), math.floor(y + r)))

    # Gira pelo mouse e pelas setas
    def girar(self, teclas):
        dt = self.jogo.dt
        self.angulo += self.giro_mouse * SENSIBILIDADE_MOUSE
        self.giro_mouse = 0
        if teclas[pg.K_LEFT]:
            self.angulo -= GIRO_TECLADO * dt
        if teclas[pg.K_RIGHT]:
            self.angulo += GIRO_TECLADO * dt
        self.angulo %= math.tau

    # Anda (ou corre) batendo nas paredes, um eixo de cada vez para deslizar nelas
    def andar(self, teclas):
        frente = (teclas[pg.K_w] or teclas[pg.K_UP]) - (teclas[pg.K_s] or teclas[pg.K_DOWN])
        lado = teclas[pg.K_d] - teclas[pg.K_a]
        self.andando = bool(frente or lado)
        quer_correr = teclas[pg.K_LSHIFT] or teclas[pg.K_RSHIFT]
        self.correndo = self.andando and quer_correr and self.folego > 1
        if not self.andando:
            return
        velocidade = (VELOCIDADE_CORRENDO if self.correndo else VELOCIDADE) * self.jogo.dt
        # Andar na diagonal não pode ser mais rápido
        if frente and lado:
            velocidade /= math.sqrt(2)
        seno, cosseno = math.sin(self.angulo), math.cos(self.angulo)
        dx = (cosseno * frente - seno * lado) * velocidade
        dy = (seno * frente + cosseno * lado) * velocidade
        if self.cabe(self.x + dx, self.y):
            self.x += dx
        if self.cabe(self.x, self.y + dy):
            self.y += dy

    # Correr gasta fôlego; parado ou andando ele volta
    def respirar(self):
        dt = self.jogo.dt
        if self.correndo:
            self.folego = max(0, self.folego - GASTO_FOLEGO * dt)
        else:
            self.folego = min(FOLEGO_MAX, self.folego + RECUPERA_FOLEGO * dt)

    # Som dos próprios passos no carpete
    def pisar(self):
        agora = pg.time.get_ticks()
        if self.andando and agora >= self.proximo_passo:
            self.jogo.sons.passo()
            self.proximo_passo = agora + (280 if self.correndo else 430)

    def atualizar(self):
        teclas = pg.key.get_pressed()
        self.girar(teclas)
        self.andar(teclas)
        self.respirar()
        self.pisar()

    # Distância e ângulo (relativo para onde o jogador olha) até um ponto
    def direcao_para(self, x, y):
        distancia = math.hypot(x - self.x, y - self.y)
        diferenca = (math.atan2(y - self.y, x - self.x) - self.angulo + math.pi) % math.tau - math.pi
        return distancia, diferenca
