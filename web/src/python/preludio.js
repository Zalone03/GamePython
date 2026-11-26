// ===========
// Python base
// ===========

// Troca input(), time.sleep() e quit() por versões que esperam o navegador
export const PRELUDIO = String.raw`
import builtins, os, sys, time, traceback
from pyodide.ffi import run_sync
import ponte

# Encerra o jogo se o jogador apertou ESC
def _checar():
    if ponte.parado():
        raise SystemExit

# input() que espera o jogador digitar na página
def _input(prompt=""):
    if prompt:
        sys.stdout.write(str(prompt))
    sys.stdout.flush()
    _checar()
    linha = run_sync(ponte.lerLinha())
    _checar()
    return linha

# time.sleep() que devolve o controle ao navegador enquanto espera
def _sleep(segundos):
    _checar()
    run_sync(ponte.esperar(max(0, segundos) * 1000))
    _checar()

# quit() e exit() encerram só o jogo, não o Python inteiro
def _sair(*args):
    raise SystemExit(*args)

# Substitui as funções originais
builtins.input = _input
builtins.quit = _sair
builtins.exit = _sair
time.sleep = _sleep

# Entra na pasta de um jogo com vários arquivos (como "cd pasta" no terminal)
def _entrar_na_pasta(pasta):
    os.chdir(pasta)
    sys.path.insert(0, pasta)

# Sai da pasta e esquece os módulos do jogo (a próxima partida começa do zero)
def _sair_da_pasta(pasta, pasta_anterior):
    os.chdir(pasta_anterior)
    sys.path.remove(pasta)
    for nome, modulo in list(sys.modules.items()):
        if (getattr(modulo, "__file__", None) or "").startswith(pasta):
            del sys.modules[nome]

# Roda um jogo como se fosse "python arquivo.py" (codigo vem pronto ou é lido da pasta)
def _executar(arquivo, codigo=None, pasta=None):
    pasta_anterior = os.getcwd()
    if pasta:
        _entrar_na_pasta(pasta)
        with open(arquivo, encoding="utf-8") as f:
            codigo = f.read()
    globais = {"__name__": "__main__", "__file__": arquivo}
    try:
        exec(compile(codigo, arquivo, "exec"), globais)
    except SystemExit:
        pass
    except BaseException:
        traceback.print_exc()
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        # Fecha o pygame se o jogo não fechou
        if "pygame" in sys.modules:
            sys.modules["pygame"].quit()
        if pasta:
            _sair_da_pasta(pasta, pasta_anterior)
`;

// ===========
// Python do pygame
// ===========

// Ajusta o pygame para desenhar no canvas e não travar o navegador
export const PRELUDIO_PYGAME = String.raw`
import os, warnings

# O teclado do pygame só escuta o canvas (não atrapalha o resto da página)
os.environ["SDL_EMSCRIPTEN_KEYBOARD_ELEMENT"] = "#canvas"

# No navegador não há fontes do sistema: o pygame usa a fonte padrão sem avisar
warnings.filterwarnings("ignore", message="The system font")

import pygame, time

# Relógio que espera devolvendo o controle ao navegador (substitui pygame.time.Clock)
class _Relogio:
    # Guarda o momento do último quadro e a média de quadros por segundo
    def __init__(self):
        self._ultimo = time.perf_counter()
        self._fps = 0.0

    # Espera o tempo de um quadro e devolve quantos ms se passaram
    def tick(self, fps=0):
        if fps:
            espera = 1.0 / fps - (time.perf_counter() - self._ultimo)
            time.sleep(max(espera, 0.001))
        else:
            # Sem limite de FPS: acompanha o ritmo do monitor (quadros regulares, sem trancos)
            _checar()
            run_sync(ponte.proximoQuadro())
            _checar()
        novo = time.perf_counter()
        segundos = max(novo - self._ultimo, 1e-6)
        self._ultimo = novo
        # Média suave, para o número não ficar pulando
        self._fps = self._fps * 0.9 + (1 / segundos) * 0.1 if self._fps else 1 / segundos
        return int(segundos * 1000)

    # Mesmo comportamento do tick normal
    tick_busy_loop = tick

    # Quadros por segundo (o DOOM mostra no título da aba)
    def get_fps(self):
        return self._fps

pygame.time.Clock = _Relogio

# Mover o mouse por código não existe no navegador: o "pulo" para o centro virava tranco na mira
pygame.mouse.set_pos = lambda *args, **kwargs: None

# set_caption original (muda o título da aba)
_set_caption_original = pygame.display.set_caption

# Momento da última troca de título
_ultima_troca_de_titulo = [-1.0]

# Troca o título no máximo uma vez por segundo (o DOOM troca a cada quadro e isso pesa)
def _set_caption(titulo, *args):
    agora = time.perf_counter()
    if agora - _ultima_troca_de_titulo[0] >= 1:
        _ultima_troca_de_titulo[0] = agora
        _set_caption_original(titulo, *args)

pygame.display.set_caption = _set_caption

# Timers ativos: tipo do evento -> [intervalo, próximo disparo, repetições, evento]
_timers = {}

# set_timer() próprio (o do pygame ainda não existe no navegador)
def _set_timer(evento, milis, loops=0):
    tipo = evento if isinstance(evento, int) else evento.type
    if milis <= 0:
        _timers.pop(tipo, None)
        return
    _timers[tipo] = [milis, pygame.time.get_ticks() + milis, loops, evento]

# Coloca na fila os eventos dos timers que já venceram
def _disparar_timers():
    agora = pygame.time.get_ticks()
    for tipo, timer in list(_timers.items()):
        milis, proximo, loops, evento = timer
        if agora < proximo:
            continue
        pygame.event.post(pygame.event.Event(tipo) if isinstance(evento, int) else evento)
        timer[1] = agora + milis
        timer[2] -= 1
        # loops=0 repete para sempre; senão para quando acabar
        if loops and timer[2] <= 0:
            del _timers[tipo]

# event.get() original, chamado depois de disparar os timers
_event_get_original = pygame.event.get

# event.get() que dispara os timers antes de ler os eventos
def _event_get(*args, **kwargs):
    _disparar_timers()
    return _event_get_original(*args, **kwargs)

# quit() original, chamado depois de limpar os timers
_quit_original = pygame.quit

# quit() que também desliga os timers
def _quit():
    _timers.clear()
    _quit_original()

pygame.time.set_timer = _set_timer
pygame.event.get = _event_get
pygame.quit = _quit

# music.play() original, usado quando o jogo pode tocar música
_musica_original = pygame.mixer.music.play

# Liga ou desliga a música de fundo do próximo jogo (os efeitos de som continuam)
def _permitir_musica(permitir):
    pygame.mixer.music.play = _musica_original if permitir else (lambda *args, **kwargs: None)
`;
