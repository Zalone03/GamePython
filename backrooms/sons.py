import math
import os
import random
import pygame as pg

#===========
# Arquivos
#===========

# Pasta dos sons (gerados por ferramentas/gerar_sons.py)
PASTA_SONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sons')

# Volume geral: com tudo tocando junto a soma não pode passar do máximo (senão o som estoura)
VOLUME_GERAL = 0.5


# Abre um som da pasta sons/
def abrir(nome):
    return pg.mixer.Sound(os.path.join(PASTA_SONS, f'{nome}.wav'))

# Volume da esquerda e da direita para um som vindo de uma direção (0 = na frente), já com o volume geral
def estereo(volume, diferenca):
    lado = math.sin(diferenca)
    volume *= VOLUME_GERAL
    return volume * min(1.0, 1 - lado), volume * min(1.0, 1 + lado)


#===========
# Mesa de som
#===========

# Toca cada som no canal certo e ajusta volume e direção conforme o jogo
class Sons:
    def __init__(self):
        self.ligado = pg.mixer.get_init() is not None
        if not self.ligado:
            return
        # Se o som falhar por qualquer motivo, o jogo continua mudo em vez de travar
        try:
            self.carregar()
        except (pg.error, RuntimeError, OSError) as erro:
            print('Sem som:', erro)
            self.ligado = False

    # Abre os sons e separa um canal fixo para cada som contínuo
    def carregar(self):
        pg.mixer.set_num_channels(20)
        pg.mixer.set_reserved(4)
        self.canal_zumbido = pg.mixer.Channel(0)
        self.canal_musica = pg.mixer.Channel(1)
        self.canal_coracao = pg.mixer.Channel(2)
        self.canal_respiracao = pg.mixer.Channel(3)
        self.zumbido = abrir('zumbido')
        self.musica = abrir('musica_distante')
        self.coracao_lento = abrir('coracao_lento')
        self.coracao_rapido = abrir('coracao_rapido')
        self.respiracao = abrir('respiracao')
        self.passos = [abrir(f'passo_{i}') for i in range(4)]
        self.clark_bota = abrir('clark_bota')
        self.clark_perna = abrir('clark_perna')
        self.som_teleporte = abrir('teleporte')
        self.susto_curto = abrir('susto_curto')
        self.susto_final = abrir('susto_final')
        self.lampada = abrir('lampada')
        self.distantes = [abrir('batidas'), abrir('estrondo')]
        self.som_vitoria = abrir('vitoria')
        # Qual coração está tocando e de qual pé é o próximo passo do Clark
        self.coracao_atual = None
        self.perna_de_pau = False

    # Toca um som solto com volume e direção
    def tocar(self, som, volume, diferenca=0.0):
        if not self.ligado:
            return
        canal = som.play()
        if canal:
            canal.set_volume(*estereo(volume, diferenca))

    #===========
    # Sons contínuos
    #===========

    # Liga o zumbido das lâmpadas e deixa música, coração e respiração prontos (mudos)
    def iniciar_ambiente(self):
        if not self.ligado:
            return
        self.canal_zumbido.play(self.zumbido, loops=-1)
        self.canal_zumbido.set_volume(*estereo(0.35, 0))
        self.canal_musica.play(self.musica, loops=-1)
        self.canal_musica.set_volume(0)
        self.canal_respiracao.play(self.respiracao, loops=-1)
        self.canal_respiracao.set_volume(0)
        self.trocar_coracao(self.coracao_lento)

    # Troca entre o coração lento e o acelerado
    def trocar_coracao(self, coracao):
        if coracao is not self.coracao_atual:
            self.coracao_atual = coracao
            self.canal_coracao.play(coracao, loops=-1)
            self.canal_coracao.set_volume(0)

    # Música da saída (mais alta perto dela e vindo do lado dela), coração e respiração do Clark
    def atualizar(self, dist_saida, direcao_saida, dist_clark, direcao_clark):
        if not self.ligado:
            return
        volume_musica = max(0.05, 1 - dist_saida / 50) * 0.6
        self.canal_musica.set_volume(*estereo(volume_musica, direcao_saida))
        self.trocar_coracao(self.coracao_rapido if dist_clark < 4.5 else self.coracao_lento)
        self.canal_coracao.set_volume(*estereo(max(0, 1 - dist_clark / 9) * 0.65, 0))
        volume_respiracao = max(0, 1 - dist_clark / 6) * 0.6
        self.canal_respiracao.set_volume(*estereo(volume_respiracao, direcao_clark))

    #===========
    # Sons soltos
    #===========

    # Passo no carpete (uma das 4 variações, com volume levemente diferente)
    def passo(self):
        if self.ligado:
            self.tocar(random.choice(self.passos), 0.3 * random.uniform(0.85, 1.1))

    # Passos do Clark: bota e perna de pau, alternando
    def passo_clark(self, volume, diferenca):
        if not self.ligado or volume <= 0:
            return
        self.perna_de_pau = not self.perna_de_pau
        som = self.clark_perna if self.perna_de_pau else self.clark_bota
        self.tocar(som, volume * (1.0 if self.perna_de_pau else 0.9), diferenca)

    def teleporte(self, volume, diferenca):
        if self.ligado:
            self.tocar(self.som_teleporte, volume * 0.8, diferenca)

    # Lâmpada falhando (faíscas e zumbido rasgado)
    def estalo(self):
        if self.ligado:
            self.tocar(self.lampada, 0.55)

    # Batidas ou estrondo bem longe, vindo de uma direção
    def evento_distante(self, diferenca):
        if self.ligado:
            self.tocar(random.choice(self.distantes), 0.4, diferenca)

    # Jumpscare: o final para todo o resto antes; o rápido é mais baixo para não estourar com o ambiente
    def susto(self, final=False):
        if not self.ligado:
            return
        if final:
            pg.mixer.stop()
            # Toca sozinho: pode ir mais alto que o volume geral
            self.tocar(self.susto_final, 0.9 / VOLUME_GERAL)
        else:
            self.tocar(self.susto_curto, 0.7)

    # Para tudo e toca o acorde de vitória
    def vitoria(self):
        if self.ligado:
            pg.mixer.stop()
            self.tocar(self.som_vitoria, 0.8 / VOLUME_GERAL)
