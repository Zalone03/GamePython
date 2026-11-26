#===========
# Gerar sons
#===========

# Cria os sons do jogo (sons/*.wav) por síntese: filtros, reverb de sala vazia, madeira, sinos...
# Rode da pasta backrooms:  python ferramentas/gerar_sons.py   (precisa de numpy)

import math
import os
import wave
import numpy as np

PASTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONS = os.path.join(PASTA, 'sons')

# Amostras por segundo
TAXA = 22050


#===========
# Ferramentas de áudio
#===========

# Momentos (em segundos) de cada amostra
def tempo(duracao):
    return np.arange(int(duracao * TAXA)) / TAXA

# Ruído branco (com semente, para sair sempre igual)
def ruido(n, semente):
    return np.random.default_rng(semente).uniform(-1, 1, n)

# Passa-baixa de 1 polo: tira os agudos acima de fc (fc pode mudar com o tempo)
def passa_baixa(x, fc):
    fc = np.broadcast_to(np.asarray(fc, dtype=float), x.shape)
    coef = (1 - np.exp(-2 * np.pi * fc / TAXA)).tolist()
    saida, acc = [], 0.0
    for valor, a in zip(x.tolist(), coef):
        acc += a * (valor - acc)
        saida.append(acc)
    return np.array(saida)

# Passa-alta: tira os graves abaixo de fc
def passa_alta(x, fc):
    return x - passa_baixa(x, fc)

# Passa-banda (biquad): deixa só a região perto de f (q maior = mais estreito)
def passa_banda(x, f, q):
    w = 2 * np.pi * f / TAXA
    alfa = np.sin(w) / (2 * q)
    a0 = 1 + alfa
    b0, b2 = alfa / a0, -alfa / a0
    a1, a2 = -2 * np.cos(w) / a0, (1 - alfa) / a0
    saida, x1, x2, y1, y2 = [], 0.0, 0.0, 0.0, 0.0
    for valor in x.tolist():
        y = b0 * valor + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, valor, y1, y
        saida.append(y)
    return np.array(saida)

# Eco em pente (cada eco volta mais fraco)
def pente(x, atraso, ganho):
    y = x.copy()
    for inicio in range(atraso, len(y), atraso):
        fim = min(inicio + atraso, len(y))
        y[inicio:fim] += ganho * y[inicio - atraso:fim - atraso]
    return y

# Passa-tudo: espalha os ecos sem mudar o timbre
def passa_tudo(x, atraso, ganho):
    y = -ganho * x
    y[atraso:] += x[:-atraso]
    for inicio in range(atraso, len(y), atraso):
        fim = min(inicio + atraso, len(y))
        y[inicio:fim] += ganho * y[inicio - atraso:fim - atraso]
    return y

# Valor eficaz (volume médio) de um som
def rms(x):
    return float(np.sqrt(np.mean(x ** 2))) + 1e-12

# Reverb de sala grande e vazia (tamanho = quanto os ecos duram; brilho = quão agudos eles são)
def reverb(x, tamanho=0.84, brilho=3000, mistura=0.3, cauda=1.5):
    seco = np.concatenate([x, np.zeros(int(cauda * TAXA))])
    escala = TAXA / 44100
    molhado = np.zeros_like(seco)
    for atraso in (1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617):
        molhado += pente(seco, int(atraso * escala), tamanho)
    for atraso in (556, 441, 341, 225):
        molhado = passa_tudo(molhado, int(atraso * escala), 0.5)
    molhado = passa_baixa(molhado, brilho)
    molhado *= rms(seco) / rms(molhado)
    return seco * (1 - mistura) + molhado * mistura

# Envelope: sobe em "ataque" segundos e depois cai exponencialmente (zero antes de começar)
def envelope(t, ataque, queda):
    e = np.minimum(1, np.maximum(t, 0) / max(ataque, 1e-6)) * np.exp(-np.maximum(0, t - ataque) / queda)
    e[t < 0] = 0
    return e

# Arco suave que sobe e desce entre dois momentos (forma > 1 = mais pontudo)
def arco(t, inicio, fim, forma=1.0):
    fase = np.clip((t - inicio) / (fim - inicio), 0, 1)
    return np.sin(np.pi * fase) ** forma

# Saturação suave (deixa o som mais "sujo" e audível em caixinhas pequenas)
def saturar(x, forca):
    return np.tanh(x * forca) / np.tanh(forca)

# Ajusta o volume para o pico ficar em "pico"
def normalizar(x, pico):
    return x * (pico / max(1e-9, float(np.abs(x).max())))

# Fase acumulada de uma frequência que pode mudar com o tempo
def fase(freq, n):
    return 2 * np.pi * np.cumsum(np.broadcast_to(np.asarray(freq, dtype=float), (n,))) / TAXA

# Dente de serra sem chiado digital (soma de harmônicos)
def serra(freq, n, harmonicos=12):
    f = fase(freq, n)
    maior = float(np.max(freq))
    saida = np.zeros(n)
    for k in range(1, harmonicos + 1):
        if k * maior < TAXA / 2:
            saida += np.sin(k * f) / k
    return saida

# Batida em madeira: soma de ressonâncias que somem rápido + o clique do impacto
def madeira(t, modos, semente):
    som = sum(a * np.sin(2 * np.pi * f * t) * envelope(t, 0.0005, d) for f, a, d in modos)
    clique = passa_alta(ruido(len(t), semente), 2000) * envelope(t, 0.0002, 0.003)
    return som + 0.5 * clique

# Junta o fim do som com o começo (loop sem emenda)
def fazer_loop(x, fade):
    corpo = x[:-fade].copy()
    rampa = np.linspace(0, 1, fade)
    corpo[:fade] = corpo[:fade] * rampa + x[-fade:] * (1 - rampa)
    return corpo

# Dobra a cauda do reverb de volta para o começo (loop com eco contínuo)
def dobrar_cauda(x, duracao):
    n = int(duracao * TAXA)
    saida = x[:n].copy()
    cauda = x[n:]
    saida[:len(cauda)] += cauda[:n]
    return saida

# Coloca um som dentro de outro a partir de um momento
def colar(destino, som, inicio):
    i = int(inicio * TAXA)
    fim = min(len(destino), i + len(som))
    destino[i:fim] += som[:fim - i]


#===========
# Ambiente
#===========

# Zumbido limpo das lâmpadas fluorescentes (sem distorção e sem grave pesado, loop de 4 s)
def zumbido():
    duracao, fade = 4.0, 0.4
    t = tempo(duracao + fade)
    n = len(t)
    # 120 Hz com poucos harmônicos fracos
    tom = (np.sin(2 * np.pi * 120 * t) + 0.35 * np.sin(2 * np.pi * 240 * t + 0.5)
           + 0.18 * np.sin(2 * np.pi * 360 * t + 1.1) + 0.08 * np.sin(2 * np.pi * 480 * t + 2.0))
    # O brilho "respira" devagar e sem ritmo certo
    tremor = 1 + 0.15 * normalizar(passa_baixa(ruido(n, 1), 2), 1)
    # Chiado fino do reator da lâmpada, bem baixinho e oscilando
    reator = np.sin(2 * np.pi * 7500 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t))
    # Ar parado da sala: ruído suave só nos médios
    ar = passa_baixa(passa_alta(ruido(n, 2), 200), 1200)
    som = 0.7 * tom * tremor + 0.015 * reator + 0.06 * normalizar(ar, 1)
    return normalizar(fazer_loop(som, int(fade * TAXA)), 0.35)

# Música de elevador tocando longe num rádio velho (chamado da saída, loop de 8 s)
def musica_distante():
    duracao = 8.0
    t = tempo(duracao + 2.0)
    n = len(t)
    # Fita oscilando e tudo um pouco desafinado (fica estranho)
    fita = (1 + 0.004 * np.sin(2 * np.pi * 0.6 * t) + 0.002 * np.sin(2 * np.pi * 5.3 * t)) * 2 ** (-25 / 1200)
    nota = lambda midi: 440 * 2 ** ((midi - 69) / 12)
    melodia = [(0.0, 76, 0.5), (0.5, 74, 0.5), (1.0, 72, 0.5), (1.5, 71, 0.5), (2.0, 72, 1.0), (3.0, 69, 1.0),
               (4.0, 77, 0.5), (4.5, 76, 0.5), (5.0, 74, 0.5), (5.5, 72, 0.5), (6.0, 71, 1.0), (7.0, 64, 1.0)]
    acordes = [(0.0, (57, 60, 64)), (2.0, (57, 60, 64)), (4.0, (53, 57, 60)), (6.0, (52, 56, 59))]
    som = np.zeros(n)
    # Piano elétrico: tom com ataque de sino que vira um som redondo
    for inicio, midi, dur in melodia:
        ti = t - inicio
        f = fase(nota(midi) * fita, n)
        sino = np.exp(-np.maximum(ti, 0) / 0.08)
        tecla = np.sin(f + 1.2 * sino * np.sin(f)) + 0.3 * np.sin(2 * f) + 0.08 * np.sin(3 * f)
        som += 0.5 * tecla * envelope(ti, 0.004, 0.55) * (ti < dur + 1.2)
    # Acordes de fundo bem suaves
    for inicio, notas in acordes:
        ti = t - inicio
        corpo = arco(t, inicio, inicio + 2.4, 0.6)
        for midi in notas:
            f = fase(nota(midi) * fita, n)
            som += 0.12 * (np.sin(f) + 0.15 * np.sin(3 * f)) * corpo
    # Rádio: só os médios, um pouco sujo, com chiado e estalos
    som = passa_alta(som, 350)
    som = passa_baixa(passa_baixa(som, 2800), 2800)
    som = saturar(normalizar(som, 1), 1.5)
    estalos = np.zeros(n)
    rng = np.random.default_rng(11)
    for i in rng.integers(0, n, 14):
        estalos[i] = rng.uniform(-1, 1)
    som += 0.025 * passa_alta(ruido(n, 12), 3000) + 0.4 * estalos
    som = reverb(som, 0.86, 2600, 0.45, 1.5)
    return normalizar(dobrar_cauda(som, duracao), 0.7)


#===========
# Coração e respiração
#===========

# Uma batida do coração: grave caindo de tom + baque abafado
def tum(forca, semente):
    t = tempo(0.3)
    corpo = np.sin(fase(42 + 28 * np.exp(-t / 0.035), len(t))) * envelope(t, 0.006, 0.07)
    baque = passa_baixa(passa_baixa(ruido(len(t), semente), 180), 180) * envelope(t, 0.004, 0.025) * 1.2
    # Saturação leve só para dar para ouvir em caixinha pequena; some suave no fim
    return forca * saturar(corpo + baque, 1.4) * np.clip((0.3 - t) / 0.08, 0, 1)

# Coração (tum-tum) num ciclo de "periodo" segundos
def coracao(periodo, intervalo):
    som = np.zeros(int(periodo * TAXA))
    colar(som, tum(1.0, 21), 0.0)
    colar(som, tum(0.75, 22), intervalo)
    return normalizar(passa_baixa(som, 900), 0.9)

# Respiração do Clark: inspira chiada, expira rouca com ronco (loop de 3,4 s)
def respiracao():
    t = tempo(3.4)
    n = len(t)
    ar = ruido(n, 31)
    inspira = (passa_banda(ar, 1400, 1.2) + 0.6 * passa_banda(ar, 2600, 2.0)) * arco(t, 0.05, 1.05, 1.5)
    expira = (passa_banda(ar, 750, 1.0) + 0.5 * passa_banda(ar, 1800, 1.5)) * arco(t, 1.3, 2.9, 1.2)
    tremido = 68 + 6 * np.sin(2 * np.pi * 7 * t) + 3 * passa_baixa(ruido(n, 32), 20)
    ronco = passa_baixa(serra(tremido, n, 8), 900) * arco(t, 1.35, 2.8, 1.5)
    # Ar raspando na garganta: o volume treme rápido e sem ritmo
    raspado = 0.65 + 0.35 * normalizar(passa_baixa(ruido(n, 33), 35), 1)
    som = (0.7 * normalizar(inspira, 1) + normalizar(expira, 1)) * raspado + 0.25 * normalizar(ronco, 1)
    som = passa_baixa(passa_baixa(som, 3500), 3500)
    return normalizar(saturar(normalizar(som, 1) * 1.2, 1.5), 0.8)


#===========
# Passos
#===========

# Passo abafado no carpete (cada semente dá uma variação)
def passo_carpete(semente):
    rng = np.random.default_rng(semente)
    t = tempo(0.22)
    n = len(t)
    corte = 300 * rng.uniform(0.85, 1.15)
    baque = passa_baixa(passa_baixa(passa_baixa(ruido(n, semente), corte), corte), corte) * envelope(t, 0.004, 0.045)
    grave = np.sin(2 * np.pi * 85 * rng.uniform(0.9, 1.1) * t) * envelope(t, 0.003, 0.035)
    tecido = passa_banda(ruido(n, semente + 100), 1800, 1.2) * envelope(t - 0.012, 0.003, 0.02)
    som = saturar(normalizar(baque, 1) + 0.5 * grave, 1.5) + 0.12 * normalizar(tecido, 1)
    return normalizar(reverb(som, 0.7, 1500, 0.1, 0.4), 0.7)

# Bota pesada do Clark, arrastando no carpete
def passo_bota():
    t = tempo(0.6)
    n = len(t)
    baque = passa_baixa(passa_baixa(ruido(n, 41), 260), 260) * envelope(t, 0.005, 0.09)
    grave = np.sin(fase(45 + 25 * np.exp(-t / 0.05), n)) * envelope(t, 0.004, 0.12)
    arrasto = passa_banda(ruido(n, 42), 1200, 0.7) * envelope(t - 0.08, 0.12, 0.12)
    som = saturar(normalizar(baque, 1) + 0.8 * grave, 1.8) + 0.35 * normalizar(arrasto, 1)
    return normalizar(reverb(som, 0.84, 2500, 0.35, 1.2), 0.85)

# Perna de pau do Clark: "TOC" de madeira oca com um rangido
def passo_perna_de_pau():
    t = tempo(0.5)
    n = len(t)
    toc = madeira(t, [(390, 1.0, 0.05), (870, 0.55, 0.035), (1340, 0.4, 0.022), (2110, 0.22, 0.014)], 51)
    baque = passa_baixa(ruido(n, 52), 300) * envelope(t, 0.002, 0.03)
    rangido = np.sin(fase(600 - 80 * np.clip((t - 0.05) / 0.12, 0, 1), n)) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * t))
    rangido *= arco(t, 0.05, 0.17, 1.0)
    som = normalizar(toc, 1) + 0.6 * normalizar(baque, 1) + 0.12 * rangido
    # Batida curta: satura um pouco para ficar tão presente quanto a bota
    return normalizar(saturar(reverb(som, 0.84, 3000, 0.38, 1.2) * 2, 2), 0.95)


#===========
# Clark
#===========

# Teleporte: aspirado subindo que vira um anel metálico desafinado entortando para baixo
def teleporte():
    t = tempo(1.4)
    n = len(t)
    subida = np.clip(t / 0.4, 0, 1)
    aspirado = passa_baixa(ruido(n, 61), 150 + 3500 * subida ** 2) * subida ** 3 * (t < 0.4)
    ti = t - 0.4
    entorta = 1 - 0.06 * np.clip(ti / 0.8, 0, 1)
    anel = sum(a * np.sin(fase(f * entorta, n)) for f, a in ((311.1, 1.0), (466.2, 0.7), (740.0, 0.5), (1108.7, 0.35)))
    anel *= envelope(ti, 0.01, 0.6)
    grave = np.sin(fase(55 * entorta, n)) * envelope(ti, 0.02, 0.5)
    falha = np.zeros(n)
    pedaco = ruido(int(0.03 * TAXA), 63)
    for k, inicio in enumerate((0.42, 0.47, 0.51, 0.57)):
        colar(falha, pedaco * 0.9 ** k, inicio)
    # Menos bits e menos amostras: som de falha digital
    falha = np.round(falha * 4) / 4
    falha = np.repeat(falha[::6], 6)[:n]
    som = 0.7 * normalizar(aspirado, 1) + 0.6 * normalizar(anel, 1) + 0.5 * grave + 0.25 * falha
    # Some suave no fim (sem estalo)
    som *= np.clip((1.4 - t) / 0.3, 0, 1)
    return normalizar(reverb(som, 0.88, 3000, 0.45, 1.6), 0.8)

# Violinos arranhando no agudo: dente de serra com vibrato, chiado do arco e corpo de madeira
def violinos(notas, t, deslize, semente):
    n = len(t)
    som = np.zeros(n)
    for i, nota in enumerate(notas):
        vibrato = 1 + 0.012 * np.sin(2 * np.pi * (6.2 + 0.4 * i) * t + i)
        som += serra(nota * deslize * vibrato, n, 8)
    arco = passa_alta(ruido(n, semente), 3000)
    som = normalizar(som, 1) + 0.12 * normalizar(arco, 1)
    # Ressonâncias do corpo do violino
    return passa_banda(som, 1100, 0.7) + 0.6 * passa_banda(som, 2900, 1.0) + 0.3 * passa_banda(som, 450, 0.8)

# Grito quase humano: voz rouca e trêmula passando pelos filtros da vogal "A"
def grito_humano(t, altura, semente):
    n = len(t)
    tremor = 1 + 0.03 * normalizar(passa_baixa(ruido(n, semente), 40), 1)
    voz = serra(altura * tremor, n, 14) + 0.25 * ruido(n, semente + 1)
    return passa_banda(voz, 800, 6) + 0.7 * passa_banda(voz, 1150, 7) + 0.4 * passa_banda(voz, 2900, 8)

# Jumpscare: violinos arranhando (estilo Psicose), grito quase humano e um peso grave por baixo
def susto(duracao, semente, final):
    t = tempo(duracao)
    n = len(t)
    curva = t / duracao
    # No susto final, tudo cai de tom no fim (como se estivesse morrendo)
    queda = np.clip((curva - 0.55) / 0.45, 0, 1) ** 2 if final else np.zeros(n)
    deslize = (1 + 0.08 * curva) * (1 - 0.35 * queda)
    cordas = violinos((1174.7, 1244.5, 1318.5, 1396.9), t, deslize, semente) * envelope(t, 0.004, duracao * 0.8)
    altura = (480 + 340 * np.clip(t / 0.25, 0, 1)) * (1 - 0.6 * queda)
    grito = grito_humano(t, altura, semente + 5) * envelope(t, 0.015, duracao * 0.6)
    grave = passa_baixa(serra(65.4, n, 20) + serra(69.3, n, 20), 500) * envelope(t, 0.03, duracao * 0.9)
    som = 0.55 * normalizar(cordas, 1) + 0.5 * normalizar(grito, 1) + 0.3 * normalizar(grave, 1)
    som *= np.clip((duracao - t) / 0.3, 0, 1)
    return normalizar(reverb(saturar(som, 1.2), 0.86, 5000, 0.35, 1.2), 0.9)


#===========
# Lâmpada, sons distantes e vitória
#===========

# Lâmpada falhando: zumbido rasgado ligando e desligando, faíscas e o "tink" do vidro
def lampada_falhando():
    t = tempo(0.8)
    n = len(t)
    rng = np.random.default_rng(71)
    ligado = np.zeros(n)
    bordas, pos, aceso = [], 0, True
    while pos < n:
        dur = int(rng.integers(int(0.015 * TAXA), int(0.09 * TAXA)))
        if aceso:
            ligado[pos:pos + dur] = 1
            bordas.append(pos)
        pos += dur
        aceso = not aceso
    rasgado = saturar(sum(np.sin(2 * np.pi * 120 * k * t) / k for k in range(1, 21)), 5)
    faiscas = np.zeros(n)
    for borda in bordas:
        faisca = passa_alta(ruido(int(0.006 * TAXA), borda), 2500) * rng.uniform(0.6, 1)
        colar(faiscas, faisca, borda / TAXA)
    vidro = np.sin(2 * np.pi * 3300 * t) * envelope(t, 0.001, 0.03)
    som = 0.5 * rasgado * ligado + 0.9 * faiscas + 0.3 * vidro
    som *= np.clip((0.8 - t) / 0.1, 0, 1)
    return normalizar(reverb(som, 0.6, 5000, 0.15, 0.3), 0.75)

# Três batidas em madeira bem longe, ecoando
def batidas_distantes():
    som = np.zeros(int(1.2 * TAXA))
    t = tempo(0.4)
    for k, inicio in enumerate((0.0, 0.33, 0.62)):
        toc = madeira(t, [(330, 1.0, 0.06), (760, 0.5, 0.04), (1190, 0.3, 0.025)], 81 + k)
        colar(som, toc * (1 - 0.15 * k), inicio)
    som = passa_baixa(passa_baixa(som, 1400), 1400)
    return normalizar(reverb(som, 0.9, 1800, 0.65, 2.5), 0.8)

# Estrondo de metal bem longe (algo pesado caindo em outra sala)
def estrondo_distante():
    t = tempo(2.0)
    n = len(t)
    metal = sum(a * np.sin(2 * np.pi * f * t) * envelope(t, 0.004, d)
                for f, a, d in ((196, 1, 0.9), (353, 0.7, 0.7), (561, 0.5, 0.5), (797, 0.35, 0.4), (1213, 0.2, 0.25)))
    baque = passa_baixa(passa_baixa(ruido(n, 91), 150), 150) * envelope(t, 0.01, 0.2)
    som = passa_baixa(normalizar(metal, 1) + 0.5 * normalizar(baque, 1), 1200)
    # Some suave no fim (sem estalo)
    som *= np.clip((2.0 - t) / 0.5, 0, 1)
    return normalizar(reverb(som, 0.92, 1500, 0.75, 3.0), 0.6)

# Vitória: acorde de alívio que cresce devagar, com sinos
def vitoria():
    t = tempo(3.0)
    n = len(t)
    pad = sum(np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t) for f in (261.6, 329.6, 392.0, 587.3))
    pad *= envelope(t, 0.6, 1.8)
    sinos = np.zeros(n)
    for i, f in enumerate((659.3, 784.0, 1046.5)):
        ti = t - (0.35 + i * 0.22)
        modulacao = 1.2 * np.exp(-np.maximum(ti, 0) / 0.2) * np.sin(2 * np.pi * 2 * f * ti)
        sinos += np.sin(2 * np.pi * f * ti + modulacao) * envelope(ti, 0.002, 0.9)
    som = passa_baixa(0.5 * normalizar(pad, 1) + 0.35 * sinos, 3500)
    return normalizar(reverb(som, 0.85, 3500, 0.4, 1.5), 0.8)


#===========
# Salvar
#===========

# Grava um som em sons/ como WAV de 16 bits e mostra as medidas dele
def salvar(nome, amostras, loop=False):
    os.makedirs(SONS, exist_ok=True)
    # Sons soltos entram e saem suaves (loops não, para não emendar com buraco)
    if not loop:
        amostras = amostras.copy()
        entrada, saida = int(0.002 * TAXA), int(0.02 * TAXA)
        amostras[:entrada] *= np.linspace(0, 1, entrada)
        amostras[-saida:] *= np.linspace(1, 0, saida)
    dados = (np.clip(amostras, -1, 1) * 32000).astype('<i2')
    with wave.open(os.path.join(SONS, f'{nome}.wav'), 'wb') as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(TAXA)
        arquivo.writeframes(dados.tobytes())
    espectro = np.abs(np.fft.rfft(amostras))
    frequencias = np.fft.rfftfreq(len(amostras), 1 / TAXA)
    centro = float((espectro * frequencias).sum() / espectro.sum())
    volume = 20 * math.log10(rms(amostras))
    print(f'{nome:18s} {len(amostras) / TAXA:5.2f} s   pico {np.abs(amostras).max():.2f}   '
          f'volume {volume:6.1f} dB   centro {centro:6.0f} Hz')


if __name__ == '__main__':
    salvar('zumbido', zumbido(), loop=True)
    salvar('musica_distante', musica_distante(), loop=True)
    salvar('coracao_lento', coracao(1.0, 0.30), loop=True)
    salvar('coracao_rapido', coracao(0.5, 0.18), loop=True)
    salvar('respiracao', respiracao(), loop=True)
    for i in range(4):
        salvar(f'passo_{i}', passo_carpete(100 + i))
    salvar('clark_bota', passo_bota())
    salvar('clark_perna', passo_perna_de_pau())
    salvar('teleporte', teleporte())
    salvar('susto_curto', susto(1.0, 201, final=False))
    salvar('susto_final', susto(2.2, 202, final=True))
    salvar('lampada', lampada_falhando())
    salvar('batidas', batidas_distantes())
    salvar('estrondo', estrondo_distante())
    salvar('vitoria', vitoria())
