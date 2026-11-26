import math
import sys

#===========
# Tela
#===========

# Roda dentro do navegador (Pyodide)?
NO_NAVEGADOR = sys.platform == "emscripten"

# Resolução do jogo (no PC a janela é ampliada sem borrar)
LARGURA, ALTURA = 640, 360
METADE_LARGURA, METADE_ALTURA = LARGURA // 2, ALTURA // 2

# No navegador 0 = acompanha o monitor; no PC limita a 60
FPS = 0 if NO_NAVEGADOR else 60

#===========
# Raycasting
#===========

# Campo de visão e quantidade de raios (um raio a cada 2 pixels)
CAMPO_VISAO = math.pi / 3
METADE_CAMPO = CAMPO_VISAO / 2
NUM_RAIOS = LARGURA // 2
ESCALA = LARGURA // NUM_RAIOS
ANGULO_RAIO = CAMPO_VISAO / NUM_RAIOS
DIST_TELA = METADE_LARGURA / math.tan(METADE_CAMPO)

# Até onde os raios vão (em blocos) e a partir de onde a neblina cobre tudo
PROFUNDIDADE_MAX = 14
DIST_NEBLINA = 12

# Tamanho das texturas das paredes e quantos tons de neblina cada uma tem
TAM_TEXTURA = 128
NIVEIS_NEBLINA = 12

# Chão e teto: pixels por bloco na imagem vista de cima (menos = mais rápido) e a cada quantos
# blocos a estampa se repete
PIXELS_BLOCO = 12
PERIODO_ESTAMPA = 12

# Painéis de luz no teto: um a cada tantos blocos (em x e em y)
LUZ_A_CADA = (4, 3)

#===========
# Cores
#===========

# Cor da neblina (amarelo sujo e escuro)
COR_NEBLINA = (58, 52, 28)

#===========
# Jogador
#===========

# Posição inicial (centro da primeira sala)
POSICAO_INICIAL = 3.5, 3.5

# Velocidade andando e correndo (blocos por ms)
VELOCIDADE = 0.0026
VELOCIDADE_CORRENDO = 0.0045

# Giro pelas setas (radianos por ms) e pelo mouse (radianos por pixel)
GIRO_TECLADO = 0.0024
SENSIBILIDADE_MOUSE = 0.0022

# Tamanho do jogador para bater nas paredes
RAIO_JOGADOR = 0.22

# Fôlego da corrida: máximo, gasto e recuperação por ms
FOLEGO_MAX = 100
GASTO_FOLEGO = 0.028
RECUPERA_FOLEGO = 0.012

#===========
# Mapa
#===========

# Tamanho de cada sala em blocos (as paredes ficam nas bordas)
TAM_SALA = 6

# Chance de uma borda de sala ter parede (sempre com passagem) e de ter um pilar no meio
CHANCE_PAREDE = 0.62
CHANCE_PILAR = 0.18

# Chance de uma parede ser da versão manchada
CHANCE_MANCHA = 0.15

# Quão perto da porta precisa chegar para sair
DIST_ESCAPAR = 0.95

#===========
# Captain Clark
#===========

# Quão perto ele precisa chegar para pegar o jogador
CLARK_PEGA = 0.6

# Tempo mínimo entre dois sustos rápidos (ms)
CLARK_SUSTO_INTERVALO = 25_000

# Altura do Clark em relação à parede
CLARK_ALTURA = 0.92

#===========
# Dificuldades
#===========

# aparece: até quando ele só é ouvido (ms) | caca: quando começa a perseguir (ms)
# intensidade: tempo de caça até a força máxima (ms) | vel_min/vel_max: velocidade (blocos por ms)
# tele_max/tele_min: intervalo entre teleportes (ms) | dist_longe/dist_perto: onde ele surge (blocos)
# susto: chance de susto depois de teleportar | saida: distância da porta (blocos)
DIFICULDADES = [
    {
        "nome": "NORMAL",
        "descricao": "Ele demora a aparecer e anda devagar",
        "aparece": 40_000, "caca": 100_000, "intensidade": 240_000,
        "vel_min": 0.0014, "vel_max": 0.0028,
        "tele_max": 24_000, "tele_min": 9_000,
        "dist_longe": 11, "dist_perto": 6,
        "susto": 0.2, "saida": (30, 40),
    },
    {
        "nome": "MÉDIO",
        "descricao": "No fim ele anda mais rápido que você",
        "aparece": 30_000, "caca": 75_000, "intensidade": 180_000,
        "vel_min": 0.0016, "vel_max": 0.0034,
        "tele_max": 20_000, "tele_min": 6_000,
        "dist_longe": 10, "dist_perto": 5,
        "susto": 0.3, "saida": (35, 50),
    },
    {
        "nome": "DIFÍCIL",
        "descricao": "Ele chega cedo, teleporta muito e a saída é longe",
        "aparece": 15_000, "caca": 40_000, "intensidade": 120_000,
        "vel_min": 0.0020, "vel_max": 0.0040,
        "tele_max": 14_000, "tele_min": 4_000,
        "dist_longe": 8, "dist_perto": 4,
        "susto": 0.4, "saida": (45, 60),
    },
]

#===========
# Telas e efeitos
#===========

# Duração do susto rápido e do susto final (ms)
SUSTO_RAPIDO = 700
SUSTO_FINAL = 1600

# Tempo da tela de vitória ou derrota antes de o jogo fechar (ms)
TEMPO_TELA_FINAL = 4500

# Duração da mensagem do começo (ms)
TEMPO_MENSAGEM_INICIAL = 6000
