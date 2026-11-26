import math
import os
import random
import pygame as pg
from config import *
from mapa import PAREDE, MANCHADA, PORTA

#===========
# Arquivos
#===========

# Pasta das imagens (geradas por ferramentas/preparar_imagens.py a partir de originais/)
PASTA_IMAGENS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imagens')

# Quadros do Clark: 0 parado, 1 e 2 andando, 3 falhando (teleporte), 4 olhos vermelhos
QUADROS_CLARK = 5


# Abre uma imagem da pasta imagens/
def abrir(nome, transparente=False):
    imagem = pg.image.load(os.path.join(PASTA_IMAGENS, nome))
    return imagem.convert_alpha() if transparente else imagem.convert()


#===========
# Neblina
#===========

# Cobre uma imagem com neblina mantendo a transparência (t=0 nada, t=1 só neblina)
def cobrir_de_neblina(imagem, t):
    copia = imagem.copy()
    resto = int(255 * (1 - t))
    copia.fill((resto, resto, resto), special_flags=pg.BLEND_RGB_MULT)
    copia.fill(tuple(int(c * t) for c in COR_NEBLINA), special_flags=pg.BLEND_RGB_ADD)
    return copia

# Todas as versões de uma imagem, da mais nítida até a totalmente coberta de neblina
def niveis_de_neblina(imagem, transparente=False):
    niveis = []
    for n in range(NIVEIS_NEBLINA):
        nivel = cobrir_de_neblina(imagem, n / (NIVEIS_NEBLINA - 1))
        niveis.append(nivel.convert_alpha() if transparente else nivel.convert())
    return niveis


#===========
# Paredes
#===========

# Rodapé de madeira escura na base da parede
def rodape(tex):
    tam = tex.get_height()
    pg.draw.rect(tex, (112, 92, 52), (0, tam - 10, tex.get_width(), 10))
    pg.draw.line(tex, (82, 66, 36), (0, tam - 10), (tex.get_width(), tam - 10), 2)

# Manchas de umidade escorrendo pelo papel de parede
def manchas(tex, sorte, quantas):
    tam = tex.get_width()
    for _ in range(quantas):
        mancha = pg.Surface((tam, tam), pg.SRCALPHA)
        cx, cy, raio = sorte.randrange(tam), sorte.randrange(tam // 3, tam), sorte.randint(8, 22)
        pg.draw.ellipse(mancha, (96, 74, 30, 60), (cx - raio, cy - raio * 2, raio * 2, raio * 3))
        pg.draw.ellipse(mancha, (80, 60, 24, 70), (cx - raio // 2, cy - raio, raio, raio * 2))
        pg.draw.line(mancha, (90, 70, 28, 80), (cx, cy), (cx, min(tam - 11, cy + raio * 2)), 2)
        tex.blit(mancha, (0, 0))

# Texturas por tipo de bloco, cada uma com seus níveis de neblina
def texturas_das_paredes():
    sorte = random.Random('texturas')
    comum = abrir('parede.png')
    manchada = comum.copy()
    manchas(comum, sorte, 1)
    manchas(manchada, sorte, 6)
    rodape(comum)
    rodape(manchada)
    return {
        PAREDE: niveis_de_neblina(comum),
        MANCHADA: niveis_de_neblina(manchada),
        PORTA: niveis_de_neblina(abrir('porta.png')),
    }


#===========
# Efeitos de tela
#===========

# Bordas escuras da tela (feita pequena e ampliada, para ser rápida)
def vinheta(cor):
    largura, altura = 160, 90
    sup = pg.Surface((largura, altura), pg.SRCALPHA)
    for y in range(altura):
        for x in range(largura):
            dx = (x - largura / 2) / (largura / 2)
            dy = (y - altura / 2) / (altura / 2)
            forca = min(1, max(0, math.hypot(dx, dy) - 0.55) / 0.6)
            sup.set_at((x, y), (*cor, int(255 * forca)))
    return pg.transform.smoothscale(sup, (LARGURA, ALTURA))


#===========
# Tudo junto
#===========

# Carrega todas as imagens do jogo de uma vez
class Texturas:
    def __init__(self):
        self.paredes = texturas_das_paredes()
        self.chao = abrir('chao.png')
        # Forro um pouco amarelado e mais escuro, para as luzes se destacarem
        self.teto = abrir('teto.png')
        self.teto.fill((206, 198, 160), special_flags=pg.BLEND_RGB_MULT)
        self.luz = abrir('luz.png')
        self.luz.fill((40, 40, 30), special_flags=pg.BLEND_RGB_ADD)
        self.vinheta = vinheta((0, 0, 0))
        self.vinheta_vermelha = vinheta((120, 0, 0))
        # Clark: [quadro][nível de neblina]
        self.clark = [niveis_de_neblina(abrir(f'clark/{i}.png', True), True) for i in range(QUADROS_CLARK)]
        self.rosto = abrir('clark/rosto.png')
