import math
import pygame as pg
from config import *

#===========
# Chão e teto (estilo "Mode 7")
#===========

# Raio (em blocos) da área em volta do jogador que vira chão/teto na tela
RAIO = DIST_NEBLINA + 2

# Desenha carpete e forro em perspectiva: uma imagem vista de cima, girada para onde o jogador
# olha e fatiada linha por linha (cada linha da tela é uma distância)
class ChaoTeto:
    def __init__(self, jogo):
        texturas = jogo.texturas
        self.janela = 2 * RAIO * PIXELS_BLOCO
        self.chao = self.estampa(texturas.chao, 1, None)
        self.teto = self.estampa(texturas.teto, 2, texturas.luz)
        # Linhas da tela (de 2 em 2 pixels): distância até o chão e metade da largura vista ali
        self.linhas = []
        for dy in range(1, METADE_ALTURA, 2):
            distancia = 0.5 * DIST_TELA / dy
            if distancia <= DIST_NEBLINA:
                self.linhas.append((dy, distancia, distancia * math.tan(METADE_CAMPO)))
        self.neblina = self.camada_de_neblina()

    # Imagem grande vista de cima com a estampa repetida (e as luzes, no teto)
    def estampa(self, textura, blocos_por_textura, luz):
        k = PIXELS_BLOCO
        periodo = PERIODO_ESTAMPA * k
        lado = periodo + self.janela
        pedaco = pg.transform.smoothscale(textura, (k * blocos_por_textura, k * blocos_por_textura))
        base = pg.Surface((periodo, periodo))
        for x in range(0, periodo, pedaco.get_width()):
            for y in range(0, periodo, pedaco.get_height()):
                base.blit(pedaco, (x, y))
        if luz:
            painel = pg.transform.smoothscale(luz, (k, k))
            for bx in range(0, PERIODO_ESTAMPA, LUZ_A_CADA[0]):
                for by in range(0, PERIODO_ESTAMPA, LUZ_A_CADA[1]):
                    base.blit(painel, (bx * k, by * k))
        grande = pg.Surface((lado, lado))
        for x in range(0, lado, periodo):
            for y in range(0, lado, periodo):
                grande.blit(base, (x, y))
        return grande.convert()

    # Neblina por cima do chão e do teto: mais forte perto do horizonte
    def camada_de_neblina(self):
        camada = pg.Surface((LARGURA, ALTURA), pg.SRCALPHA)
        camada.fill((*COR_NEBLINA, 255))
        for dy, distancia, _meia in self.linhas:
            alfa = int(255 * min(1, distancia / DIST_NEBLINA))
            for y in (METADE_ALTURA + dy - 1, METADE_ALTURA - dy - 1):
                pg.draw.rect(camada, (*COR_NEBLINA, alfa), (0, y, LARGURA, 2))
        return camada

    # Recorta a área em volta do jogador e gira para a frente dele ficar para cima
    def girar(self, estampa, jogador):
        k = PIXELS_BLOCO
        periodo = PERIODO_ESTAMPA * k
        ox, oy = ((jogador.x - RAIO) * k) % periodo, ((jogador.y - RAIO) * k) % periodo
        janela = estampa.subsurface((int(ox), int(oy), self.janela, self.janela))
        angulo = jogador.angulo + math.pi / 2
        girada = pg.transform.rotate(janela, math.degrees(angulo))
        # Onde o jogador ficou depois do giro (conta a fração de pixel, para não tremer)
        fx, fy = ox - int(ox), oy - int(oy)
        cx = girada.get_width() / 2 + fx * math.cos(angulo) + fy * math.sin(angulo)
        cy = girada.get_height() / 2 - fx * math.sin(angulo) + fy * math.cos(angulo)
        return girada, cx, cy

    def desenhar(self, tela, jogador):
        k = PIXELS_BLOCO
        for estampa, sinal in ((self.chao, 1), (self.teto, -1)):
            girada, cx, cy = self.girar(estampa, jogador)
            for dy, distancia, meia in self.linhas:
                largura = 2 * meia * k
                faixa = girada.subsurface((cx - largura / 2, cy - distancia * k, largura, 1))
                tela.blit(pg.transform.scale(faixa, (LARGURA, 2)), (0, METADE_ALTURA + sinal * dy - 1))
        tela.blit(self.neblina, (0, 0))
