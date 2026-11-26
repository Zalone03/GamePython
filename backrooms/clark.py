import math
import random
from collections import deque
import pygame as pg
from config import *

#===========
# Ajudantes
#===========

# Valor entre a e b (t=0 dá a, t=1 dá b)
def entre(a, b, t):
    return a + (b - a) * t


#===========
# Captain Clark
#===========

# Fases: só passos ao longe -> aparece e some de longe -> caça, se teleportando cada vez mais perto
class Clark:
    def __init__(self, jogo):
        self.jogo = jogo
        # Quadros com neblina: [quadro][nível]
        self.imagens = jogo.texturas.clark
        self.proporcao = self.imagens[0][0].get_width() / self.imagens[0][0].get_height()
        # Até quando mostra o quadro "falhando" (logo depois de teleportar)
        self.falha_ate = 0
        self.x = self.y = 0.0
        self.visivel = False
        # Está aparecendo na tela do jogador neste quadro?
        self.na_tela = False
        # Próximo aparecimento (espreitando) ou teleporte (caçando)
        self.proximo_evento = 0
        self.some_em = 0
        # Passos ouvidos de longe antes de ele aparecer: [(quando, direção)]
        self.passos_fantasma = []
        self.caminho = []
        self.proximo_caminho = 0
        self.proximo_passo = 0
        self.ultimo_susto = -CLARK_SUSTO_INTERVALO

    # Primeiros passos fantasmas logo no começo
    def preparar(self):
        self.proximo_evento = pg.time.get_ticks() + random.uniform(8_000, 14_000)

    # Força da caçada: 0 quando ela começa, 1 no máximo
    def intensidade(self):
        d = self.jogo.dificuldade
        return min(max((self.jogo.tempo - d['caca']) / d['intensidade'], 0), 1)

    # Distância e direção do Clark em relação ao jogador
    def direcao(self):
        return self.jogo.jogador.direcao_para(self.x, self.y)

    #===========
    # Aparecer e sumir
    #===========

    # Diz se dá para ver (x, y) a partir do jogador, sem parede no meio
    def linha_livre(self, x, y):
        jogador = self.jogo.jogador
        distancia = math.hypot(x - jogador.x, y - jogador.y)
        passos = int(distancia / 0.25)
        for i in range(1, passos):
            t = i / passos
            px, py = entre(jogador.x, x, t), entre(jogador.y, y, t)
            if not self.jogo.mapa.livre(math.floor(px), math.floor(py)):
                return False
        return True

    # Surge num bloco livre a uma distância, na frente (à vista) ou atrás do jogador
    def surgir(self, distancia, atras, precisa_ver=False):
        jogador = self.jogo.jogador
        base = jogador.angulo + (math.pi if atras else 0)
        abertura = 0.9 if atras else 0.35
        for _ in range(60):
            angulo = base + random.uniform(-abertura, abertura)
            d = distancia * random.uniform(0.85, 1.15)
            x = math.floor(jogador.x + math.cos(angulo) * d) + 0.5
            y = math.floor(jogador.y + math.sin(angulo) * d) + 0.5
            if not self.jogo.mapa.livre(math.floor(x), math.floor(y)):
                continue
            if math.hypot(x - jogador.x, y - jogador.y) < 3:
                continue
            if precisa_ver and not self.linha_livre(x, y):
                continue
            self.x, self.y = x, y
            self.visivel = True
            self.caminho = []
            self.falha_ate = pg.time.get_ticks() + 400
            return True
        return False

    # Some (com o som de teleporte se o jogador estava olhando ou perto)
    def sumir(self, com_som):
        if com_som:
            distancia, diferenca = self.direcao()
            self.jogo.sons.teleporte(max(0.25, 1 - distancia / 14), diferenca)
        self.visivel = False

    #===========
    # Fases
    #===========

    # Fase 1: ele não aparece, só se ouvem passos vindo de algum lugar
    def ouvir_de_longe(self, agora):
        if agora >= self.proximo_evento:
            direcao = random.uniform(-math.pi, math.pi)
            self.passos_fantasma = [(agora + i * 520, direcao) for i in range(4)]
            self.proximo_evento = agora + random.uniform(9_000, 16_000)
        while self.passos_fantasma and agora >= self.passos_fantasma[0][0]:
            _quando, direcao = self.passos_fantasma.pop(0)
            self.jogo.sons.passo_clark(0.22, direcao)

    # Fase 2: aparece de longe, parado olhando, e some quando o jogador chega perto
    def espreitar(self, agora):
        d = self.jogo.dificuldade
        if self.visivel:
            perto = self.direcao()[0] < 3.5
            if perto or agora >= self.some_em:
                self.sumir(com_som=perto or self.na_tela)
                self.proximo_evento = agora + random.uniform(10_000, 18_000)
        elif agora >= self.proximo_evento:
            # Tenta na frente; se o jogador estiver de cara para a parede, aparece à vista atrás dele
            na_frente = self.surgir(d['dist_longe'], atras=False, precisa_ver=True)
            if na_frente or self.surgir(d['dist_longe'] * 0.8, atras=True, precisa_ver=True):
                self.some_em = agora + random.uniform(3_000, 6_000)
            else:
                self.proximo_evento = agora + 1_000

    # Fase 3: persegue e teleporta perto (cada vez mais perto e mais rápido)
    def cacar(self, agora):
        forca = self.intensidade()
        if not self.visivel or agora >= self.proximo_evento:
            self.teleportar(agora, forca)
        else:
            self.perseguir(agora, forca)
        if self.visivel and self.direcao()[0] < CLARK_PEGA:
            self.jogo.pego()

    # Teleporta para perto (de preferência atrás) e às vezes dá um susto logo depois
    def teleportar(self, agora, forca):
        d = self.jogo.dificuldade
        distancia = entre(d['dist_longe'], d['dist_perto'], forca)
        if not self.surgir(distancia, atras=random.random() < 0.65):
            self.proximo_evento = agora + 500
            return
        distancia, diferenca = self.direcao()
        self.jogo.sons.teleporte(max(0.3, 1 - distancia / 12), diferenca)
        self.proximo_evento = agora + entre(d['tele_max'], d['tele_min'], forca) * random.uniform(0.8, 1.2)
        pode_assustar = agora - self.ultimo_susto >= CLARK_SUSTO_INTERVALO
        if forca > 0.1 and pode_assustar and random.random() < d['susto']:
            self.ultimo_susto = agora
            self.jogo.susto_rapido()

    #===========
    # Perseguição
    #===========

    # Menor caminho (bloco a bloco) até o jogador, procurando só por perto
    def calcular_caminho(self):
        mapa = self.jogo.mapa
        jogador = self.jogo.jogador
        inicio = (math.floor(self.x), math.floor(self.y))
        destino = (math.floor(jogador.x), math.floor(jogador.y))
        anterior = {inicio: None}
        fila = deque([inicio])
        while fila and len(anterior) < 2500:
            atual = fila.popleft()
            if atual == destino:
                break
            x, y = atual
            for vizinho in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if vizinho not in anterior and mapa.livre(*vizinho):
                    anterior[vizinho] = atual
                    fila.append(vizinho)
        if destino not in anterior:
            return []
        caminho = []
        passo = destino
        while passo != inicio:
            caminho.append(passo)
            passo = anterior[passo]
        caminho.reverse()
        return caminho

    # Anda pelo caminho até o jogador (e direto nele quando estão no mesmo bloco)
    def perseguir(self, agora, forca):
        d = self.jogo.dificuldade
        jogador = self.jogo.jogador
        if agora >= self.proximo_caminho:
            self.caminho = self.calcular_caminho()
            self.proximo_caminho = agora + 400
        if self.caminho:
            alvo_x, alvo_y = self.caminho[0][0] + 0.5, self.caminho[0][1] + 0.5
        else:
            alvo_x, alvo_y = jogador.x, jogador.y
        dx, dy = alvo_x - self.x, alvo_y - self.y
        distancia = math.hypot(dx, dy)
        passo = entre(d['vel_min'], d['vel_max'], forca) * self.jogo.dt
        if distancia <= passo:
            self.x, self.y = alvo_x, alvo_y
            if self.caminho:
                self.caminho.pop(0)
        else:
            self.x += dx / distancia * passo
            self.y += dy / distancia * passo
        # Passos pesados, mais altos quanto mais perto
        if agora >= self.proximo_passo:
            distancia, diferenca = self.direcao()
            self.jogo.sons.passo_clark(max(0, 1 - distancia / 14), diferenca)
            self.proximo_passo = agora + 520

    #===========
    # Quadro a quadro
    #===========

    def atualizar(self):
        d = self.jogo.dificuldade
        agora = pg.time.get_ticks()
        tempo = self.jogo.tempo
        if tempo < d['aparece']:
            self.ouvir_de_longe(agora)
        elif tempo < d['caca']:
            self.espreitar(agora)
        else:
            self.cacar(agora)

    # Quadro da animação: falhando logo depois de teleportar, parado olhando quando espreita,
    # olhos vermelhos quando está perto e andando quando caça
    def quadro(self, agora, distancia):
        if agora < self.falha_ate:
            return 3
        if self.jogo.tempo < self.jogo.dificuldade['caca']:
            return 0
        if distancia < 4:
            return 4
        return 1 + (agora // 280) % 2

    # Coloca o Clark na lista de desenho, com neblina e escondido atrás das paredes mais perto
    def projetar(self):
        self.na_tela = False
        if not self.visivel:
            return
        distancia, diferenca = self.direcao()
        if abs(diferenca) > METADE_CAMPO + 0.25 or distancia < 0.25:
            return
        corrigida = distancia * math.cos(diferenca)
        tela_x = (diferenca + METADE_CAMPO) / ANGULO_RAIO * ESCALA
        raio = int(tela_x / ESCALA)
        if 0 <= raio < NUM_RAIOS and self.jogo.raycasting.profundidade[raio] > corrigida:
            self.na_tela = True
        parede = DIST_TELA / corrigida
        altura = min(parede * CLARK_ALTURA, ALTURA * 3)
        largura = altura * self.proporcao
        nivel = min(int(corrigida / DIST_NEBLINA * (NIVEIS_NEBLINA - 1)), NIVEIS_NEBLINA - 1)
        quadro = self.quadro(pg.time.get_ticks(), distancia)
        imagem = pg.transform.scale(self.imagens[quadro][nivel], (max(1, int(largura)), max(1, int(altura))))
        pos = (tela_x - largura / 2, METADE_ALTURA + parede / 2 - altura)
        self.jogo.raycasting.objetos.append((corrigida, imagem, pos))
