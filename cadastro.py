import sqlite3


# ========================================
# CONECTANDO AO BANCO
# ========================================

conexao = sqlite3.connect("lanchonete.db")
cursor = conexao.cursor()


# ========================================
# TABELA
# ========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    telefone TEXT NOT NULL,
    endereco TEXT NOT NULL
)
""")

conexao.commit()


# ========================================
# ADICIONANDO USUARIO E SENHA
# ========================================

cursor.execute("PRAGMA table_info(clientes)")
colunas = [coluna[1] for coluna in cursor.fetchall()]

if "usuario" not in colunas:
    cursor.execute("ALTER TABLE clientes ADD COLUMN usuario TEXT")

if "senha" not in colunas:
    cursor.execute("ALTER TABLE clientes ADD COLUMN senha TEXT")

conexao.commit()


# ========================================
# CADASTRAR CLIENTE
# ========================================

def cadastrar_cliente():

    print("\n==============================")
    print("      CADASTRO DE CLIENTE")
    print("==============================")

    nome = input("Nome: ")
    telefone = input("Telefone: ")
    endereco = input("Endereco: ")
    usuario = input("Usuario: ")
    senha = input("Senha: ")

    cursor.execute("""
        INSERT INTO clientes
        (nome, telefone, endereco, usuario, senha)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, telefone, endereco, usuario, senha))

    conexao.commit()

    print("\nCliente cadastrado com sucesso!")


# ========================================
# LISTAR CLIENTES
# ========================================

def listar_clientes():

    print("\n==============================")
    print("       CLIENTES CADASTRADOS")
    print("==============================")

    cursor.execute("""
        SELECT id, nome, telefone, endereco, usuario
        FROM clientes
    """)

    clientes = cursor.fetchall()

    print("\nQuantidade de clientes:", len(clientes))

    if len(clientes) == 0:

        print("\nNenhum cliente cadastrado.")

    else:

        for cliente in clientes:

            print("\n------------------------------")
            print("ID:", cliente[0])
            print("Nome:", cliente[1])
            print("Telefone:", cliente[2])
            print("Endereco:", cliente[3])
            print("Usuario:", cliente[4])


# ========================================
# MENU PRINCIPAL
# ========================================

while True:

    print("\n==============================")
    print("       LANCHONETE DEVJUAN")
    print("==============================")

    print("1 - Cadastrar cliente")
    print("2 - Listar clientes")
    print("3 - Sair")

    opcao = input("\nEscolha uma opcao: ")

    if opcao == "1":

        cadastrar_cliente()

    elif opcao == "2":

        listar_clientes()

    elif opcao == "3":

        print("\nPrograma encerrado!")

        conexao.close()

        break

    else:

        print("\nOpcao invalida!")
        