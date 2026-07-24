import random

modo = input("Qual o modo de jogo você deseja jogar? (1) Fácil(1 à 10, 3 tentativas) (2) Moderado(1 à 50, 5 tentativas) (3) Difícil(1 à 80, 7 tentativas) (4) Personalizado\n")

if modo == "1":
    n_min = 1
    n_max = 10
    tentativas = 3
elif modo == "2":
    n_min = 1
    n_max = 50
    tentativas = 5
elif modo == "3":
    n_min = 1
    n_max = 80
    tentativas = 7
elif modo == "4":
    n_min = int(input("Qual o número mínimo do intervalo?\n"))
    n_max = int(input("Qual o número Máximo do intervalo?\n"))
    tentativas = int(input("Qual o número de Tentativas?\n"))


sorteado = random.randint(n_min, n_max)

while True:
    tentativa = int(input(f"Digite um número entre {n_min} e {n_max}.\n"))

    if tentativa == sorteado:
        print("Parabéns você acertou o  número.")
        break
    else:
        tentativas -= 1
        if tentativas == 0:
            print(f"Você não acertou e não tem mais tentativas. O número era {sorteado}")
            break
        else:
            print(f"Número errado. Tente novamente. Você ainda tem {tentativas} tentativas restante.")

