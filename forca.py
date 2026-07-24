import random

# Crie uma lista de palavras para o jogo da forca
palavras = ["python", "jogo", "desenvolvimento", "computador", "tecnologia", "inteligencia", "artificial", "machine", "learning"]

# Escolha uma palavra aleatória da lista
palavra = random.choice(palavras)

# Crie uma lista para armazenar as letras não adivinhadas (usando '_' para melhor visual)
letras_escondidas = ['_'] * len(palavra)

# Crie uma lista para armazenar as letras já adivinhadas
letras_adivinhadas = []

# Defina o número máximo de tentativas
tentativas = 6

while True:
    # EXIBE A PALAVRA FORMATADA: Junta a lista separando cada elemento por um espaço em branco
    print("\nPalavra atual:", " ".join(letras_escondidas))

    # Solicitar ao jogador que adivinhe uma letra
    letra = input("Digite uma letra: ").lower() # .lower() garante que letras maiúsculas funcionem

    # Verificar se a letra já foi adivinhada
    if letra in letras_adivinhadas:
        print("Você já tentou essa letra. Tente outra.")
        continue
        
    # Adicionar a letra à lista de letras adivinhadas
    letras_adivinhadas.append(letra)

    # Verificar se a letra está na palavra
    if letra in palavra:
        # Atualizar a lista de letras escondidas com a letra adivinhada
        lista_indices = [i for i, l in enumerate(palavra) if l == letra]
        
        for i in lista_indices:
            letras_escondidas[i] = letra
        print("Letra correta!")
    else:
        tentativas -= 1
        print(f"Letra incorreta. Você ainda tem {tentativas} tentativas restantes.")

    # Verificar se o jogador ganhou (agora checando pelo '_')
    if '_' not in letras_escondidas:
        print(f"\nParabéns! Você adivinhou a palavra: {palavra}")
        break
        
    # Verificar se o jogador perdeu
    if tentativas == 0:
        print(f"\nVocê perdeu! A palavra era: {palavra}")
        break