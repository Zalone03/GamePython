import math
import random
import sys
import pygame as pg
from config import *
from mapa import Mapa
from texturas import Texturas
from jogador import Jogador
from raycasting import Raycasting
from chao_teto import ChaoTeto
from clark import Clark
from sons import Sons
from hud import Hud


#===========
# Jogo
#===========

# Estados: "menu" (escolhe a dificuldade) -> "jogando" -> "susto" (pego) ou vitória -> "fim"
class Jogo:
    def __init__(self):
        pg.mixer.pre_init(22050, -16, 2, 512)
        pg.init()
        # No PC a janela é ampliada sem borrar; no navegador o portátil já cuida disso
        flags = 0 if NO_NAVEGADOR else pg.SCALED
        self.tela = pg.display.set_mode((LARGURA, ALTURA), flags)
        pg.display.set_caption('BACKROOMS')
        pg.mouse.set_visible(False)
        pg.event.set_grab(True)
        self.relogio = pg.time.Clock()
        self.dt = 1
        # Mapa novo a cada partida
        self.mapa = Mapa(random.randrange(1_000_000_000))
        self.texturas = Texturas()
        self.jogador = Jogador(self)
        self.raycasting = Raycasting(self)
        self.chao_teto = ChaoTeto(self)
        self.sons = Sons()
        self.hud = Hud(self)
        self.clark = Clark(self)
        self.estado = 'menu'
        self.escolha = 1
        self.dificuldade = DIFICULDADES[self.escolha]
        # Tempo de jogo (ms desde o começo da partida)
        self.inicio = 0
        self.tempo = 0
        # Sustos, fim de jogo e piscadas das lâmpadas
        self.susto_ate = 0
        self.fim_ate = 0
        self.venceu = False
        self.piscadas = []
        self.proxima_piscada = 0
        # Próximo som distante (batidas, estrondo) vindo de algum lado
        self.proximo_som_distante = 0

    #===========
    # Começo e fim
    #===========

    # Começa a partida com a dificuldade escolhida
    def comecar(self):
        self.dificuldade = DIFICULDADES[self.escolha]
        self.mapa.colocar_porta(*self.dificuldade['saida'])
        self.jogador.angulo = random.uniform(0, math.tau)
        self.estado = 'jogando'
        self.inicio = pg.time.get_ticks()
        self.proxima_piscada = self.inicio + random.uniform(5_000, 12_000)
        self.proximo_som_distante = self.inicio + random.uniform(12_000, 25_000)
        self.sons.iniciar_ambiente()
        self.clark.preparar()

    # Susto rápido (o Clark aparece na cara e o jogo continua)
    def susto_rapido(self):
        self.susto_ate = pg.time.get_ticks() + SUSTO_RAPIDO
        self.sons.susto()

    # O Clark pegou o jogador: susto final e depois a tela de derrota
    def pego(self):
        if self.estado != 'jogando':
            return
        self.estado = 'susto'
        self.susto_ate = pg.time.get_ticks() + SUSTO_FINAL
        self.sons.susto(final=True)

    # Mostra a tela final por um tempo e depois fecha
    def terminar(self, venceu):
        self.venceu = venceu
        self.estado = 'fim'
        self.fim_ate = pg.time.get_ticks() + TEMPO_TELA_FINAL
        if venceu:
            self.sons.vitoria()

    # Fecha o jogo
    def sair(self):
        pg.quit()
        sys.exit()

    #===========
    # Lâmpadas piscando
    #===========

    # De tempos em tempos a luz falha (mais vezes quando a caçada aperta)
    def piscar_lampadas(self, agora):
        if agora < self.proxima_piscada:
            return
        quantas = random.randint(2, 4)
        self.piscadas = [(agora + i * 140, agora + i * 140 + random.randint(40, 110)) for i in range(quantas)]
        espera = random.uniform(6_000, 15_000) * (1 - 0.6 * self.clark.intensidade())
        self.proxima_piscada = agora + espera
        self.sons.estalo()

    # Batidas ou estrondos ao longe, de um lado qualquer, de tempos em tempos
    def sons_distantes(self, agora):
        if agora >= self.proximo_som_distante:
            self.sons.evento_distante(random.uniform(-math.pi, math.pi))
            self.proximo_som_distante = agora + random.uniform(20_000, 45_000)

    # A luz está apagada neste momento?
    def luz_apagada(self, agora):
        self.piscadas = [(inicio, fim) for inicio, fim in self.piscadas if fim > agora]
        return any(inicio <= agora for inicio, _fim in self.piscadas)

    #===========
    # Laço
    #===========

    # Teclado e mouse
    def eventos(self):
        for evento in pg.event.get():
            if evento.type == pg.QUIT or (evento.type == pg.KEYDOWN and evento.key == pg.K_ESCAPE):
                self.sair()
            elif self.estado == 'menu' and evento.type == pg.KEYDOWN:
                self.tecla_no_menu(evento.key)
            elif self.estado == 'jogando' and evento.type == pg.MOUSEMOTION:
                self.jogador.giro_mouse += evento.rel[0]

    # Menu: setas ou números escolhem, ENTER começa
    def tecla_no_menu(self, tecla):
        if tecla in (pg.K_UP, pg.K_w):
            self.escolha = (self.escolha - 1) % len(DIFICULDADES)
        elif tecla in (pg.K_DOWN, pg.K_s):
            self.escolha = (self.escolha + 1) % len(DIFICULDADES)
        elif pg.K_1 <= tecla < pg.K_1 + len(DIFICULDADES):
            self.escolha = tecla - pg.K_1
        elif tecla in (pg.K_RETURN, pg.K_KP_ENTER, pg.K_SPACE):
            self.comecar()

    # Distância e direção até a porta de saída
    def direcao_da_saida(self):
        return self.jogador.direcao_para(*self.mapa.porta)

    def atualizar(self):
        agora = pg.time.get_ticks()
        if self.estado == 'menu':
            self.jogador.angulo += 0.00015 * self.dt
            self.raycasting.atualizar()
        elif self.estado == 'jogando':
            self.tempo = agora - self.inicio
            self.jogador.atualizar()
            self.raycasting.atualizar()
            self.clark.atualizar()
            self.clark.projetar()
            self.piscar_lampadas(agora)
            self.sons_distantes(agora)
            dist_saida, direcao_saida = self.direcao_da_saida()
            dist_clark, direcao_clark = self.clark.direcao() if self.clark.visivel else (99, 0.0)
            self.sons.atualizar(dist_saida, direcao_saida, dist_clark, direcao_clark)
            if dist_saida < DIST_ESCAPAR and self.estado == 'jogando':
                self.terminar(venceu=True)
        elif self.estado == 'susto' and agora >= self.susto_ate:
            self.terminar(venceu=False)
        elif self.estado == 'fim' and agora >= self.fim_ate:
            self.sair()

    def desenhar(self):
        agora = pg.time.get_ticks()
        tela = self.tela
        if self.estado == 'menu':
            self.raycasting.desenhar(tela)
            tela.blit(self.texturas.vinheta, (0, 0))
            self.hud.menu(tela, self.escolha)
        elif self.estado == 'jogando':
            self.raycasting.desenhar(tela)
            if self.luz_apagada(agora):
                self.hud.escurecer(tela, 200)
            self.hud.vinhetas(tela, self.clark.direcao()[0] if self.clark.visivel else 99)
            self.hud.mensagem_inicial(tela)
            self.hud.folego(tela)
            if agora < self.susto_ate:
                self.hud.susto(tela, 0.3)
        elif self.estado == 'susto':
            self.hud.susto(tela, 1 - (self.susto_ate - agora) / SUSTO_FINAL)
        elif self.estado == 'fim':
            self.hud.tela_final(tela, self.venceu, self.tempo)

    def rodar(self):
        while True:
            self.eventos()
            self.atualizar()
            self.desenhar()
            pg.display.flip()
            # Limite para um travamento não virar um salto enorme
            self.dt = min(self.relogio.tick(FPS), 50)


if __name__ == '__main__':
    Jogo().rodar()
