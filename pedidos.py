import sqlite3


# ========================================
# CONECTANDO AO BANCO
# ========================================

conexao = sqlite3.connect("lanchonete.db")
cursor = conexao.cursor()


# ========================================
# TABELA DE PEDIDOS
# ========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    produto TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    preco REAL NOT NULL,
    total REAL NOT NULL,
    pagamento TEXT,
    status TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
)
""")

conexao.commit()


# ========================================
# CORRIGIR BANCO ANTIGO
# ========================================

cursor.execute("PRAGMA table_info(pedidos)")
colunas = [coluna[1] for coluna in cursor.fetchall()]

if "pagamento" not in colunas:
    cursor.execute("""
        ALTER TABLE pedidos
        ADD COLUMN pagamento TEXT
    """)

if "status" not in colunas:
    cursor.execute("""
        ALTER TABLE pedidos
        ADD COLUMN status TEXT
    """)

conexao.commit()


# ========================================
# CARDÁPIO
# ========================================

cardapio = {
    1: ("X-Burguer", 12.00),
    2: ("X-Salada", 14.00),
    3: ("X-Bacon", 16.00),
    4: ("Batata Frita", 10.00),
    5: ("Refrigerante", 6.00)
}


# ========================================
# LISTAR CLIENTES
# ========================================

def listar_clientes():

    cursor.execute("""
        SELECT id, nome, telefone
        FROM clientes
    """)

    clientes = cursor.fetchall()

    print("\n==============================")
    print("          CLIENTES")
    print("==============================")

    if len(clientes) == 0:
        print("\nNenhum cliente cadastrado.")
        return []

    for cliente in clientes:
        print(
            f"ID: {cliente[0]} | "
            f"Nome: {cliente[1]} | "
            f"Telefone: {cliente[2]}"
        )

    return clientes


# ========================================
# MOSTRAR CARDÁPIO
# ========================================

def mostrar_cardapio():

    print("\n==============================")
    print("           CARDÁPIO")
    print("==============================")

    for codigo, produto in cardapio.items():

        print(
            f"{codigo} - {produto[0]} "
            f"- R$ {produto[1]:.2f}"
        )

    print("0 - Finalizar carrinho")

    print("==============================")


# ========================================
# MOSTRAR CARRINHO
# ========================================

def mostrar_carrinho(carrinho):

    print("\n==============================")
    print("           CARRINHO")
    print("==============================")

    if len(carrinho) == 0:

        print("Carrinho vazio.")
        print("==============================")
        return

    total_geral = 0

    for i, item in enumerate(carrinho, start=1):

        nome = item["produto"]
        quantidade = item["quantidade"]
        preco = item["preco"]

        total = preco * quantidade

        total_geral += total

        print(
            f"{i} - {quantidade}x {nome} "
            f"- R$ {total:.2f}"
        )

    print("------------------------------")
    print(f"TOTAL: R$ {total_geral:.2f}")
    print("==============================")


# ========================================
# REMOVER ITEM
# ========================================

def remover_item(carrinho):

    if len(carrinho) == 0:

        print("\nCarrinho vazio!")
        return

    mostrar_carrinho(carrinho)

    try:

        numero = int(
            input("\nDigite o número do item para remover: ")
        )

    except ValueError:

        print("\nDigite apenas números!")
        return

    if numero < 1 or numero > len(carrinho):

        print("\nItem inválido!")
        return

    removido = carrinho.pop(numero - 1)

    print(
        f"\n{removido['produto']} removido do carrinho!"
    )


# ========================================
# ESCOLHER PAGAMENTO
# ========================================

def escolher_pagamento():

    print("\n==============================")
    print("          PAGAMENTO")
    print("==============================")

    print("1 - Dinheiro")
    print("2 - Pix")
    print("3 - Cartão")
    print("0 - Cancelar")

    opcao = input("\nEscolha: ")

    if opcao == "1":
        return "Dinheiro"

    elif opcao == "2":
        return "Pix"

    elif opcao == "3":
        return "Cartão"

    elif opcao == "0":
        return None

    else:

        print("\nOpção inválida!")
        return None


# ========================================
# FINALIZAR PEDIDO
# ========================================

def finalizar_pedido(
    cliente_id,
    nome_cliente,
    carrinho
):

    if len(carrinho) == 0:

        print("\nCarrinho vazio!")
        return

    # ------------------------------------
    # CALCULAR TOTAL
    # ------------------------------------

    total_geral = 0

    for item in carrinho:

        total_geral += (
            item["preco"] * item["quantidade"]
        )


    # ------------------------------------
    # MOSTRAR RESUMO
    # ------------------------------------

    print("\n==============================")
    print("        RESUMO DO PEDIDO")
    print("==============================")

    print("Cliente:", nome_cliente)

    for item in carrinho:

        total_item = (
            item["preco"] * item["quantidade"]
        )

        print(
            f"{item['quantidade']}x "
            f"{item['produto']} "
            f"- R$ {total_item:.2f}"
        )

    print("------------------------------")

    print(f"TOTAL: R$ {total_geral:.2f}")

    print("==============================")


    # ------------------------------------
    # PAGAMENTO
    # ------------------------------------

    pagamento = escolher_pagamento()

    if pagamento is None:

        print("\nPedido cancelado.")
        return


    # ------------------------------------
    # CONFIRMAR
    # ------------------------------------

    print("\n==============================")
    print("       CONFIRMAR PAGAMENTO")
    print("==============================")

    print(f"Cliente: {nome_cliente}")
    print(f"Total: R$ {total_geral:.2f}")
    print(f"Pagamento: {pagamento}")

    print("\n1 - SIM")
    print("2 - NÃO")

    confirmar = input("\nConfirmar pagamento? ")


    if confirmar == "2":

        print("\nPagamento cancelado.")
        print("Pedido não finalizado.")

        return


    if confirmar != "1":

        print("\nOpção inválida.")
        print("Pedido não finalizado.")

        return


    # ------------------------------------
    # SALVAR CADA ITEM
    # ------------------------------------

    for item in carrinho:

        total_item = (
            item["preco"] * item["quantidade"]
        )

        cursor.execute("""
            INSERT INTO pedidos
            (
                cliente_id,
                produto,
                quantidade,
                preco,
                total,
                pagamento,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente_id,
            item["produto"],
            item["quantidade"],
            item["preco"],
            total_item,
            pagamento,
            "Finalizado"
        ))


    conexao.commit()


    # ------------------------------------
    #NÚMERO O ÚLTIMO PEDIDO
    # ------------------------------------

    pedido_id = cursor.lastrowid


    # ------------------------------------
    # FINALIZADO
    # ------------------------------------

    print("\n==============================")
    print("       PEDIDO FINALIZADO")
    print("==============================")

    print(f"Pedido: #{pedido_id}")
    print("Cliente:", nome_cliente)

    print("------------------------------")

    for item in carrinho:

        total_item = (
            item["preco"] * item["quantidade"]
        )

        print(
            f"{item['quantidade']}x "
            f"{item['produto']} "
            f"- R$ {total_item:.2f}"
        )

    print("------------------------------")

    print(f"TOTAL: R$ {total_geral:.2f}")
    print("Pagamento:", pagamento)
    print("Status: FINALIZADO")

    print("==============================")
    print("Pagamento confirmado!")
    print("Pedido salvo com sucesso!")
    print("==============================")


# ========================================
# FAZER PEDIDO
# ========================================

def fazer_pedido():

    # ------------------------------------
    # ESCOLHER CLIENTE
    # ------------------------------------

    clientes = listar_clientes()

    if len(clientes) == 0:
        return

    try:

        cliente_id = int(
            input("\nDigite o ID do cliente: ")
        )

    except ValueError:

        print("\nDigite apenas números!")
        return


    cursor.execute(
        "SELECT id, nome FROM clientes WHERE id = ?",
        (cliente_id,)
    )

    cliente = cursor.fetchone()


    if cliente is None:

        print("\nCliente não encontrado!")
        return


    nome_cliente = cliente[1]


    # ------------------------------------
    # CARRINHO
    # ------------------------------------

    carrinho = []


    while True:

        mostrar_cardapio()

        mostrar_carrinho(carrinho)


        try:

            opcao = int(
                input("\nEscolha um produto: ")
            )

        except ValueError:

            print("\nDigite apenas números!")
            continue


        # --------------------------------
        # FINALIZAR CARRINHO
        # --------------------------------

        if opcao == 0:

            if len(carrinho) == 0:

                print("\nCarrinho vazio!")
                continue

            break


        # --------------------------------
        # PRODUTO INVÁLIDO
        # --------------------------------

        if opcao not in cardapio:

            print("\nProduto inválido!")
            continue


        # --------------------------------
        # QUANTIDADE
        # --------------------------------

        try:

            quantidade = int(
                input("Quantidade: ")
            )

        except ValueError:

            print("\nDigite apenas números!")
            continue


        if quantidade <= 0:

            print(
                "\nA quantidade deve ser maior que zero!"
            )

            continue


        # --------------------------------
        # ADICIONAR AO CARRINHO
        # --------------------------------

        nome_produto = cardapio[opcao][0]
        preco = cardapio[opcao][1]


        # Verificar se já existe
        # o produto no carrinho

        encontrado = False


        for item in carrinho:

            if item["produto"] == nome_produto:

                item["quantidade"] += quantidade

                encontrado = True

                break


        # Se não existir adiciona

        if not encontrado:

            carrinho.append({
                "produto": nome_produto,
                "preco": preco,
                "quantidade": quantidade
            })


        print(
            f"\n{quantidade}x "
            f"{nome_produto} "
            f"adicionado ao carrinho!"
        )


        # --------------------------------
        # OPÇÕES DO CARRINHO
        # --------------------------------

        print("\n==============================")
        print("1 - Continuar comprando")
        print("2 - Remover item")
        print("0 - Finalizar carrinho")
        print("==============================")


        escolha = input("\nEscolha: ")


        if escolha == "2":

            remover_item(carrinho)


        elif escolha == "0":

            if len(carrinho) == 0:

                print("\nCarrinho vazio!")
                continue

            break


    # ------------------------------------
    # FINALIZAR
    # ------------------------------------

    finalizar_pedido(
        cliente_id,
        nome_cliente,
        carrinho
    )


# ========================================
# LISTAR PEDIDOS
# ========================================

def listar_pedidos():

    print("\n==============================")
    print("       PEDIDOS REALIZADOS")
    print("==============================")


    cursor.execute("""
        SELECT
            pedidos.id,
            clientes.nome,
            pedidos.produto,
            pedidos.quantidade,
            pedidos.preco,
            pedidos.total,
            pedidos.pagamento,
            pedidos.status
        FROM pedidos
        INNER JOIN clientes
        ON pedidos.cliente_id = clientes.id
        ORDER BY pedidos.id DESC
    """)


    pedidos = cursor.fetchall()


    if len(pedidos) == 0:

        print("\nNenhum pedido realizado.")
        return


    pedido_atual = None


    for pedido in pedidos:

        if pedido_atual != pedido[0]:

            print("\n------------------------------")

            print("Pedido:", pedido[0])
            print("Cliente:", pedido[1])

            pedido_atual = pedido[0]


        print(
            f"  {pedido[3]}x "
            f"{pedido[2]} "
            f"- R$ {pedido[5]:.2f}"
        )

        print("  Pagamento:", pedido[6])
        print("  Status:", pedido[7])


    print("\n==============================")


# ========================================
# MENU PRINCIPAL
# ========================================

while True:

    print("\n==============================")
    print("       LANCHONETE DEVJUAN")
    print("==============================")

    print("1 - Fazer pedido")
    print("2 - Listar pedidos")
    print("0 - Finalizar programa")

    opcao = input("\nEscolha uma opção: ")


    # ------------------------------------
    # FAZER PEDIDO
    # ------------------------------------

    if opcao == "1":

        fazer_pedido()


    # ------------------------------------
    # LISTAR PEDIDOS
    # ------------------------------------

    elif opcao == "2":

        listar_pedidos()


    # ------------------------------------
    # FINALIZAR PROGRAMA
    # ------------------------------------

    elif opcao == "0":

        print("\n==============================")
        print("    PROGRAMA FINALIZADO")
        print("==============================")

        conexao.close()

        break


    else:

        print("\nOpção inválida!")


    