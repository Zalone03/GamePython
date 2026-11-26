import math
import pygame as pg
from config import *

#===========
# Raycasting
#===========

# Lança um raio por coluna (de 2 em 2 pixels) e monta as fatias de parede da tela
class Raycasting:
    def __init__(self, jogo):
        self.jogo = jogo
        self.texturas = jogo.texturas.paredes
        # O que desenhar neste quadro: (distância, imagem, posição), do mais longe ao mais perto
        self.objetos = []
        # Distância da parede em cada raio (o Clark usa para saber se está escondido)
        self.profundidade = [PROFUNDIDADE_MAX] * NUM_RAIOS

    # Anda de bloco em bloco na direção do raio até achar parede (DDA)
    def lancar(self, x, y, seno, cosseno):
        tipo_do_bloco = self.jogo.mapa.tipo
        bx, by = math.floor(x), math.floor(y)
        passo_x_dist = abs(1 / cosseno) if cosseno else 1e30
        passo_y_dist = abs(1 / seno) if seno else 1e30
        if cosseno < 0:
            passo_x, lado_x = -1, (x - bx) * passo_x_dist
        else:
            passo_x, lado_x = 1, (bx + 1 - x) * passo_x_dist
        if seno < 0:
            passo_y, lado_y = -1, (y - by) * passo_y_dist
        else:
            passo_y, lado_y = 1, (by + 1 - y) * passo_y_dist
        while True:
            if lado_x < lado_y:
                distancia, vertical = lado_x, True
                lado_x += passo_x_dist
                bx += passo_x
            else:
                distancia, vertical = lado_y, False
                lado_y += passo_y_dist
                by += passo_y
            if distancia > PROFUNDIDADE_MAX:
                return distancia, 0, vertical
            tipo = tipo_do_bloco(bx, by)
            if tipo:
                return distancia, tipo, vertical

    # Recorta a coluna da textura e estica até a altura que a parede tem na tela
    def fatia(self, textura, coluna_tex, altura, raio):
        if altura < ALTURA:
            coluna = textura.subsurface(coluna_tex, 0, 1, TAM_TEXTURA)
            coluna = pg.transform.scale(coluna, (ESCALA, int(altura)))
            return coluna, (raio * ESCALA, METADE_ALTURA - int(altura) // 2)
        # Parede maior que a tela: só a parte do meio aparece
        visivel = max(1, TAM_TEXTURA * ALTURA / altura)
        coluna = textura.subsurface(coluna_tex, (TAM_TEXTURA - visivel) / 2, 1, visivel)
        return pg.transform.scale(coluna, (ESCALA, ALTURA)), (raio * ESCALA, 0)

    def atualizar(self):
        self.objetos = []
        jogador = self.jogo.jogador
        x, y = jogador.x, jogador.y
        inicio = jogador.angulo - METADE_CAMPO + 0.0001
        for raio in range(NUM_RAIOS):
            angulo = inicio + raio * ANGULO_RAIO
            seno, cosseno = math.sin(angulo), math.cos(angulo)
            distancia, tipo, vertical = self.lancar(x, y, seno, cosseno)
            if not tipo:
                self.profundidade[raio] = PROFUNDIDADE_MAX
                continue
            # Onde o raio bateu dentro do bloco (0 a 1), para escolher a coluna da textura
            if vertical:
                deslocamento = (y + distancia * seno) % 1
                if cosseno < 0:
                    deslocamento = 1 - deslocamento
            else:
                deslocamento = (x + distancia * cosseno) % 1
                if seno > 0:
                    deslocamento = 1 - deslocamento
            # Corrige o efeito olho de peixe
            distancia *= math.cos(jogador.angulo - angulo)
            self.profundidade[raio] = distancia
            # Mais longe = mais neblina; paredes de lado ficam um tom mais escuras
            nivel = min(int(distancia / DIST_NEBLINA * (NIVEIS_NEBLINA - 1)) + vertical, NIVEIS_NEBLINA - 1)
            textura = self.texturas[tipo][nivel]
            altura = DIST_TELA / (distancia + 0.0001)
            coluna_tex = int(deslocamento * (TAM_TEXTURA - 1))
            imagem, pos = self.fatia(textura, coluna_tex, altura, raio)
            self.objetos.append((distancia, imagem, pos))

    # Desenha chão e teto e depois tudo do mais longe para o mais perto
    def desenhar(self, tela):
        self.jogo.chao_teto.desenhar(tela, self.jogo.jogador)
        for _distancia, imagem, pos in sorted(self.objetos, key=lambda objeto: objeto[0], reverse=True):
            tela.blit(imagem, pos)
