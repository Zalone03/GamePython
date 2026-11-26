import adivinha from "../../../Adivinha.py?raw";
import forca from "../../../forca.py?raw";
import snake from "../../../Snake.py?raw";

// ===========
// Jogos com pasta própria
// ===========

// Endereços de todos os arquivos do DOOM (código .py + imagens e sons)
const arquivosDoom = import.meta.glob(["../../../doom/*.py", "../../../doom/resources/**/*"], {
  query: "?url",
  import: "default",
  eager: true,
});

// Endereços dos arquivos das Backrooms (código + imagens e sons prontos)
const arquivosBackrooms = import.meta.glob(
  ["../../../backrooms/*.py", "../../../backrooms/imagens/**/*", "../../../backrooms/sons/*.wav"],
  { query: "?url", import: "default", eager: true },
);

// ===========
// Cartuchos
// ===========

// Lista de jogos: jogo de um arquivo usa "codigo"; jogo com pasta usa "pasta" + "arquivos"
// tipo "texto" usa input()/print() no terminal; tipo "pygame" desenha no canvas
// musica: false tira a música de fundo (os efeitos de som continuam)
// ajustes troca um trecho de um arquivo só na cópia do navegador (o original não muda)
export const JOGOS = [
  {
    id: "doom",
    nome: "DOOM STYLE GAME",
    arquivo: "main.py",
    descricao: "Sobreviva a 10 ondas de monstros. Feito por StanislavPetrovV",
    controles: "Clique na tela · WASD anda · mouse mira · clique atira · 1/2 troca arma · ESC sai",
    tipo: "pygame",
    pasta: "doom",
    arquivos: arquivosDoom,
    musica: false,
    ajustes: [
      // Resolução menor (a tela do portátil já mostra nesse tamanho): bem mais rápido
      { arquivo: "settings.py", de: "RES = WIDTH, HEIGHT = 1600, 900", para: "RES = WIDTH, HEIGHT = 640, 360" },
      // Números da vida na mesma proporção da nova resolução (90 x 0,4)
      { arquivo: "object_renderer.py", de: "self.digit_size = 90", para: "self.digit_size = 36" },
      // Arma na mesma proporção da nova resolução (0,4 x 0,4)
      { arquivo: "weapon.py", de: "scale=0.4", para: "scale=0.16" },
      // Mira com metade da sensibilidade (o mouse travado do navegador gira mais rápido)
      { arquivo: "settings.py", de: "MOUSE_SENSITIVITY = 0.0003", para: "MOUSE_SENSITIVITY = 0.00015" },
      // Paredes sem transparência: desenhar cada coluna fica muito mais rápido (11,7 -> 6,7 ms por quadro)
      {
        arquivo: "raycasting.py",
        de: "self.textures = self.game.object_renderer.wall_textures",
        para: "self.textures = {k: v.convert() for k, v in self.game.object_renderer.wall_textures.items()}",
      },
      // Céu sem transparência, pelo mesmo motivo
      {
        arquivo: "object_renderer.py",
        de: "self.sky_image = self.get_texture('resources/textures/sky.png', (WIDTH, HALF_HEIGHT))",
        para: "self.sky_image = self.get_texture('resources/textures/sky.png', (WIDTH, HALF_HEIGHT)).convert()",
      },
    ],
  },
  {
    id: "backrooms",
    nome: "BACKROOMS",
    arquivo: "main.py",
    descricao: "Ache a porta de saída antes que o Captain Clark te pegue",
    controles: "Clique na tela · WASD anda · mouse/setas giram · Shift corre · ESC sai",
    tipo: "pygame",
    pasta: "backrooms",
    arquivos: arquivosBackrooms,
  },
  {
    id: "adivinha",
    nome: "ADIVINHA O NÚMERO",
    arquivo: "Adivinha.py",
    descricao: "Descubra o número secreto antes das tentativas acabarem",
    tipo: "texto",
    codigo: adivinha,
  },
  {
    id: "forca",
    nome: "FORCA",
    arquivo: "forca.py",
    descricao: "Adivinhe a palavra, letra por letra",
    tipo: "texto",
    codigo: forca,
  },
  {
    id: "snake",
    nome: "SNAKE",
    arquivo: "Snake.py",
    descricao: "Coma as maçãs e fuja dos obstáculos",
    controles: "Setas movem · ESC sai",
    tipo: "pygame",
    codigo: snake,
  },
];
