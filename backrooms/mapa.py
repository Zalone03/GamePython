import math
import random
from config import *

#===========
# Tipos de bloco
#===========

# Chão livre, parede, parede manchada e a porta de saída
VAZIO, PAREDE, MANCHADA, PORTA = 0, 1, 2, 3


#===========
# Mapa infinito
#===========

# Mapa gerado aos poucos, sala por sala (a mesma semente sempre gera o mesmo mapa)
class Mapa:
    def __init__(self, semente):
        self.semente = semente
        # Blocos já gerados: (x, y) -> tipo
        self.blocos = {}
        # Blocos fixados à mão (sala inicial e porta), valem mais que o sorteado
        self.fixos = {(int(POSICAO_INICIAL[0]), int(POSICAO_INICIAL[1])): VAZIO}
        self.porta = None

    # Sorteador de uma sala (a mesma sala sempre sorteia os mesmos valores)
    def sorteador(self, *chave):
        return random.Random(f'{self.semente}:' + ':'.join(map(str, chave)))

    # Tipo do bloco (x, y), gerando a sala dele se ela ainda não existe
    def tipo(self, x, y):
        tipo = self.blocos.get((x, y))
        if tipo is None:
            self.gerar_sala(x // TAM_SALA, y // TAM_SALA)
            tipo = self.blocos[(x, y)]
        return tipo

    # Diz se dá para andar no bloco (x, y)
    def livre(self, x, y):
        return self.tipo(x, y) == VAZIO

    # Parede comum ou manchada
    def parede(self, sorte):
        return MANCHADA if sorte.random() < CHANCE_MANCHA else PAREDE

    # Cria uma sala: pilar no canto, bordas de cima e da esquerda com parede (sempre com passagem)
    def gerar_sala(self, sx, sy):
        sorte = self.sorteador(sx, sy)
        x0, y0 = sx * TAM_SALA, sy * TAM_SALA
        for dx in range(TAM_SALA):
            for dy in range(TAM_SALA):
                self.blocos[(x0 + dx, y0 + dy)] = VAZIO
        # Pilar onde as paredes se encontram
        self.blocos[(x0, y0)] = self.parede(sorte)
        # Borda de cima (horizontal) e da esquerda (vertical)
        for horizontal in (True, False):
            if sorte.random() >= CHANCE_PAREDE:
                continue
            passagem = sorte.choice((1, 1, 2))
            inicio = sorte.randint(1, TAM_SALA - passagem)
            for i in range(1, TAM_SALA):
                if inicio <= i < inicio + passagem:
                    continue
                pos = (x0 + i, y0) if horizontal else (x0, y0 + i)
                self.blocos[pos] = self.parede(sorte)
        # Pilar solto no meio da sala (nunca fecha caminho)
        if sorte.random() < CHANCE_PILAR:
            meio = TAM_SALA // 2
            self.blocos[(x0 + meio, y0 + meio)] = self.parede(sorte)
        # Os fixos ganham do sorteio
        for pos, tipo in self.fixos.items():
            if pos in self.blocos:
                self.blocos[pos] = tipo

    #===========
    # Porta de saída
    #===========

    # Coloca a porta numa sala longe do começo, numa direção sorteada
    def colocar_porta(self, dist_min, dist_max):
        sorte = self.sorteador('porta')
        angulo = sorte.uniform(0, math.tau)
        dist = sorte.uniform(dist_min, dist_max)
        sx = round((POSICAO_INICIAL[0] + math.cos(angulo) * dist) / TAM_SALA)
        sy = round((POSICAO_INICIAL[1] + math.sin(angulo) * dist) / TAM_SALA)
        x0, y0 = sx * TAM_SALA, sy * TAM_SALA
        meio = TAM_SALA // 2
        # Borda de cima vira parede com a porta no meio e uma passagem no canto
        for i in range(1, TAM_SALA):
            self.fixos[(x0 + i, y0)] = PAREDE
        self.fixos[(x0 + 1, y0)] = VAZIO
        self.fixos[(x0 + meio, y0)] = PORTA
        # Nada de pilar atrapalhando a frente da porta
        self.fixos[(x0 + meio, y0 + meio)] = VAZIO
        self.porta = (x0 + meio + 0.5, y0 + 0.5)
        # Atualiza as salas que já tinham sido geradas
        for pos, tipo in self.fixos.items():
            if pos in self.blocos:
                self.blocos[pos] = tipo
