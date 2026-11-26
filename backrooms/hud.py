import random
import pygame as pg
from config import *

#===========
# Cores
#===========

AMARELO = (240, 220, 120)
BRANCO = (240, 236, 220)
CINZA = (150, 144, 120)
VERMELHO = (200, 40, 30)
VERDE = (120, 230, 140)


# Tempo em minutos:segundos
def relogio(ms):
    segundos = int(ms // 1000)
    return f'{segundos // 60}:{segundos % 60:02d}'


#===========
# HUD
#===========

# Tudo que é desenhado por cima da cena: textos, fôlego, sustos e telas
class Hud:
    def __init__(self, jogo):
        self.jogo = jogo
        self.fontes = {tamanho: pg.font.Font(None, tamanho) for tamanho in (22, 28, 40, 76)}
        # Textos já desenhados (desenhar texto é lento, então guarda)
        self.cache = {}
        self.escuro = pg.Surface((LARGURA, ALTURA))
        self.escuro.fill((0, 0, 0))

    # Texto com sombra, centralizado em x (ou começando em x se centro=False)
    def texto(self, tela, texto, tamanho, cor, x, y, centro=True, alfa=255):
        chave = (texto, tamanho, cor)
        if chave not in self.cache:
            fonte = self.fontes[tamanho]
            self.cache[chave] = (fonte.render(texto, True, cor), fonte.render(texto, True, (0, 0, 0)))
        imagem, sombra = self.cache[chave]
        if centro:
            x -= imagem.get_width() // 2
        if alfa < 255:
            imagem, sombra = imagem.copy(), sombra.copy()
            imagem.set_alpha(alfa)
            sombra.set_alpha(alfa)
        tela.blit(sombra, (x + 2, y + 2))
        tela.blit(imagem, (x, y))

    # Escurece a tela inteira (0 a 255)
    def escurecer(self, tela, quanto):
        self.escuro.set_alpha(quanto)
        tela.blit(self.escuro, (0, 0))

    #===========
    # Menu
    #===========

    # Escolha da dificuldade, com as Backrooms girando ao fundo
    def menu(self, tela, escolha):
        self.escurecer(tela, 150)
        self.texto(tela, 'BACKROOMS', 76, AMARELO, METADE_LARGURA, 34)
        self.texto(tela, 'Ache a porta de SAÍDA. Não deixe o Captain Clark te pegar.', 22, BRANCO, METADE_LARGURA, 96)
        for i, dificuldade in enumerate(DIFICULDADES):
            y = 132 + i * 54
            marcado = i == escolha
            cor = AMARELO if marcado else CINZA
            if marcado:
                self.texto(tela, '>', 40, cor, 196, y, centro=False)
                self.texto(tela, dificuldade['descricao'], 22, BRANCO, 226, y + 30, centro=False)
            self.texto(tela, f'[{i + 1}] {dificuldade["nome"]}', 40, cor, 222, y, centro=False)
        self.texto(tela, 'Setas ou 1-3 escolhem   ·   ENTER começa', 22, CINZA, METADE_LARGURA, 300)
        self.texto(tela, 'WASD anda · mouse/setas giram · Shift corre · ESC sai', 22, CINZA, METADE_LARGURA, 324)

    #===========
    # Durante o jogo
    #===========

    # Mensagem do começo, sumindo aos poucos
    def mensagem_inicial(self, tela):
        tempo = self.jogo.tempo
        if tempo > TEMPO_MENSAGEM_INICIAL:
            return
        alfa = int(255 * min(1, (TEMPO_MENSAGEM_INICIAL - tempo) / 1500))
        self.texto(tela, 'Você acordou nas Backrooms...', 28, BRANCO, METADE_LARGURA, 60, alfa=alfa)
        self.texto(tela, 'Ache a porta de SAÍDA. Siga o som.', 28, AMARELO, METADE_LARGURA, 90, alfa=alfa)

    # Barra de fôlego (só aparece quando não está cheio)
    def folego(self, tela):
        folego = self.jogo.jogador.folego
        if folego >= FOLEGO_MAX:
            return
        largura = 160
        x, y = METADE_LARGURA - largura // 2, ALTURA - 18
        pg.draw.rect(tela, (30, 26, 14), (x - 1, y - 1, largura + 2, 7))
        cor = VERMELHO if folego < 25 else AMARELO
        pg.draw.rect(tela, cor, (x, y, int(largura * folego / FOLEGO_MAX), 5))

    # Bordas escuras sempre, e avermelhadas quando o Clark está perto
    def vinhetas(self, tela, dist_clark):
        tela.blit(self.jogo.texturas.vinheta, (0, 0))
        perto = max(0, 1 - dist_clark / 7)
        if perto > 0:
            vinheta = self.jogo.texturas.vinheta_vermelha
            vinheta.set_alpha(int(220 * perto))
            tela.blit(vinheta, (0, 0))

    #===========
    # Sustos
    #===========

    # Rosto do Clark tremendo na tela, com falhas de imagem, chuvisco e tom de sangue
    def susto(self, tela, forca):
        tela.fill((0, 0, 0))
        rosto = self.jogo.texturas.rosto
        zoom = 1.05 + 0.3 * forca + random.uniform(0, 0.08)
        largura, altura = int(LARGURA * zoom), int(LARGURA * zoom * rosto.get_height() / rosto.get_width())
        imagem = pg.transform.scale(rosto, (largura, altura))
        x = METADE_LARGURA - largura // 2 + random.randint(-16, 16)
        y = METADE_ALTURA - altura // 2 + random.randint(-12, 12)
        tela.blit(imagem, (x, y))
        # Faixas da imagem deslocadas (falha de vídeo)
        for _ in range(random.randint(2, 6)):
            faixa_y, faixa_h = random.randrange(ALTURA), random.randint(4, 24)
            faixa = tela.subsurface((0, faixa_y, LARGURA, min(faixa_h, ALTURA - faixa_y))).copy()
            tela.blit(faixa, (random.randint(-40, 40), faixa_y))
        # Chuvisco de linhas escuras
        for _ in range(30):
            linha_y = random.randrange(ALTURA)
            pg.draw.line(tela, (0, 0, 0), (0, linha_y), (LARGURA, linha_y))
        # Tom de sangue (escurece puxando para o vermelho) piscando
        if random.random() < 0.6:
            tela.fill((255, 70, 60), special_flags=pg.BLEND_RGB_MULT)

    #===========
    # Telas finais
    #===========

    # Vitória ou derrota, com o tempo que o jogador durou
    def tela_final(self, tela, venceu, tempo):
        if venceu:
            tela.fill((18, 22, 14))
            self.texto(tela, 'VOCÊ ESCAPOU', 76, VERDE, METADE_LARGURA, 110)
            self.texto(tela, 'A porta se fechou atrás de você... por enquanto.', 28, BRANCO, METADE_LARGURA, 180)
        else:
            tela.fill((24, 0, 0))
            self.texto(tela, 'O CAPTAIN CLARK TE PEGOU', 40, VERMELHO, METADE_LARGURA, 120)
            self.texto(tela, 'Ninguém sai das Backrooms sem ser visto.', 28, BRANCO, METADE_LARGURA, 170)
        nome = self.jogo.dificuldade['nome']
        self.texto(tela, f'Tempo: {relogio(tempo)}   ·   {nome}', 28, CINZA, METADE_LARGURA, 230)
