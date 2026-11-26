#===========
# Preparar imagens
#===========

# Transforma as imagens de originais/ nas imagens leves que o jogo usa (imagens/)
# Rode da pasta backrooms:  python ferramentas/preparar_imagens.py   (precisa de numpy)

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import numpy as np
import pygame as pg

PASTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAIS = os.path.join(PASTA, 'originais')
IMAGENS = os.path.join(PASTA, 'imagens')

# Altura final de cada quadro do Clark (em pixels)
ALTURA_CLARK = 256

# Tamanho das texturas de parede e porta
TAM_TEXTURA = 128


#===========
# Ajudantes
#===========

# Abre uma imagem dos originais
def abrir(nome):
    return pg.image.load(os.path.join(ORIGINAIS, nome)).convert()

# Salva uma imagem em imagens/
def salvar(imagem, nome):
    caminho = os.path.join(IMAGENS, nome)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    pg.image.save(imagem, caminho)
    print('salvo:', nome, imagem.get_size())


#===========
# Clark (tirar o fundo verde e separar os quadros)
#===========

# Tira o fundo verde: quanto mais o verde passa do vermelho/azul, mais transparente
def tirar_fundo_verde(imagem):
    rgb = pg.surfarray.array3d(imagem).astype(np.int32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    verdice = g - np.maximum(r, b)
    alfa = np.clip(1 - (verdice - 40) / 50, 0, 1)
    # Tira o reflexo verde das bordas
    rgb[..., 1] = np.where(alfa > 0, np.minimum(g, np.maximum(r, b) + 8), g)
    limpa = pg.Surface(imagem.get_size(), pg.SRCALPHA)
    pg.surfarray.blit_array(limpa, rgb.astype(np.uint8))
    pg.surfarray.pixels_alpha(limpa)[:] = (alfa * 255).astype(np.uint8)
    return limpa, alfa

# Acha as colunas onde cada personagem está (separadas por faixas vazias)
def separar_quadros(alfa):
    tem = (alfa > 0.5).sum(axis=1) > 3
    quadros, inicio = [], None
    for x, ocupado in enumerate(list(tem) + [False]):
        if ocupado and inicio is None:
            inicio = x
        elif not ocupado and inicio is not None:
            if x - inicio > 40:
                quadros.append((inicio, x))
            inicio = None
    return quadros

# Caixa (x, y, largura, altura) do que não é transparente
def caixa(alfa, x0, x1):
    linhas = np.where((alfa[x0:x1] > 0.5).sum(axis=0) > 1)[0]
    return x0, linhas[0], x1 - x0, linhas[-1] - linhas[0] + 1

def preparar_clark():
    limpa, alfa = tirar_fundo_verde(abrir('Captain.jpg'))
    colunas = separar_quadros(alfa)
    print('quadros do Clark encontrados:', len(colunas))
    caixas = [caixa(alfa, x0, x1) for x0, x1 in colunas]
    # Todos os quadros no mesmo tamanho, com os pés alinhados embaixo
    largura = max(c[2] for c in caixas)
    altura = max(c[3] for c in caixas)
    escala = ALTURA_CLARK / altura
    for i, (x, y, w, h) in enumerate(caixas):
        quadro = pg.Surface((largura, altura), pg.SRCALPHA)
        quadro.blit(limpa, ((largura - w) // 2, altura - h), (x, y, w, h))
        quadro = pg.transform.smoothscale(quadro, (round(largura * escala), ALTURA_CLARK))
        salvar(quadro, f'clark/{i}.png')
    preparar_rosto(limpa, caixas[-1])

# Rosto do último quadro (olhos vermelhos) para o jumpscare
def preparar_rosto(limpa, caixa_quadro):
    x, y, w, h = caixa_quadro
    alfa = pg.surfarray.array_alpha(limpa)
    # O chapéu fica nos primeiros 8% da altura: o meio dele é o meio do rosto
    topo = alfa[x:x + w, y:y + int(h * 0.08)] > 128
    colunas = np.where(topo.sum(axis=1) > 0)[0]
    meio = x + (colunas[0] + colunas[-1]) // 2
    largura = int((colunas[-1] - colunas[0]) * 1.25)
    altura = int(largura * 0.75)
    recorte = pg.Surface((largura, altura))
    recorte.fill((0, 0, 0))
    recorte.blit(limpa, (0, 0), (meio - largura // 2, y, largura, altura))
    salvar(pg.transform.smoothscale(recorte, (256, 192)), 'clark/rosto.png')


#===========
# Texturas
#===========

# Papel de parede
def preparar_parede():
    salvar(pg.transform.smoothscale(abrir('walls.jpg'), (TAM_TEXTURA, TAM_TEXTURA)), 'parede.png')

# Porta recortada do fundo branco, na parede, com a placa verde de SAÍDA em cima
def preparar_porta():
    foto = abrir('door.jpg')
    rgb = pg.surfarray.array3d(foto)
    escuro = rgb.min(axis=2) < 215
    xs, ys = np.where(escuro.sum(axis=1) > 5)[0], np.where(escuro.sum(axis=0) > 5)[0]
    folha = foto.subsurface((xs[0], ys[0], xs[-1] - xs[0] + 1, ys[-1] - ys[0] + 1))
    tex = pg.transform.smoothscale(abrir('walls.jpg'), (TAM_TEXTURA, TAM_TEXTURA))
    # Batente escuro e a porta por cima
    pg.draw.rect(tex, (70, 66, 58), (30, 22, 68, 106))
    tex.blit(pg.transform.smoothscale(folha, (60, 102)), (34, 26))
    # Placa verde de SAÍDA
    pg.draw.rect(tex, (20, 120, 50), (38, 4, 52, 15))
    pg.draw.rect(tex, (10, 70, 30), (38, 4, 52, 15), 1)
    fonte = pg.font.Font(None, 18)
    texto = fonte.render('SAÍDA', True, (225, 255, 225))
    tex.blit(texto, (64 - texto.get_width() // 2, 6))
    salvar(tex, 'porta.png')

# Carpete (um bloco)
def preparar_chao():
    salvar(pg.transform.smoothscale(abrir('ground.jpg'), (64, 64)), 'chao.png')

# Forro do teto (a imagem tem 4x2 placas e cobre 2x2 blocos)
def preparar_teto():
    salvar(pg.transform.smoothscale(abrir('roof.jpg'), (128, 128)), 'teto.png')

# Painel de luz: o meio da foto, mais claro, com moldura
def preparar_luz():
    foto = abrir('ligth.jpg')
    w, h = foto.get_size()
    lado = min(w, h) // 2
    luz = pg.transform.smoothscale(foto.subsurface((w // 2 - lado // 2, h // 2 - lado // 2, lado, lado)), (64, 64))
    luz.fill((25, 25, 20), special_flags=pg.BLEND_RGB_ADD)
    pg.draw.rect(luz, (150, 150, 140), (0, 0, 64, 64), 3)
    salvar(luz, 'luz.png')


if __name__ == '__main__':
    pg.init()
    pg.display.set_mode((1, 1))
    preparar_clark()
    preparar_parede()
    preparar_porta()
    preparar_chao()
    preparar_teto()
    preparar_luz()
    sys.exit(0)
