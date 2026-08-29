from flask import Flask, render_template, request, redirect, jsonify, session
import sqlite3
import os
import json

app = Flask(__name__)

# =========================================================
# CHAVE DA SESSÃO
# =========================================================

app.secret_key = "devjuan-chave-secreta-2026"


# =========================================================
# CAMINHO DO BANCO
# =========================================================

CAMINHO_BANCO = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "lanchonete.db"
    )
)

print("")
print("========================================")
print("BANCO USADO PELO FLASK:")
print(CAMINHO_BANCO)
print("========================================")
print("")


# =========================================================
# CONEXÃO COM BANCO
# =========================================================

def conectar():
    banco = sqlite3.connect(
        CAMINHO_BANCO,
        timeout=15
    )

    banco.row_factory = sqlite3.Row

    banco.execute(
        "PRAGMA busy_timeout = 15000"
    )

    return banco


# =========================================================
# CRIAR / ATUALIZAR TABELAS
# =========================================================

def criar_tabelas():

    banco = None

    try:

        banco = conectar()
        cursor = banco.cursor()

        # -------------------------------------------------
        # CLIENTES
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                telefone TEXT NOT NULL DEFAULT '',
                endereco TEXT NOT NULL DEFAULT ''
            )
        """)

        # -------------------------------------------------
        # PEDIDOS
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                itens TEXT NOT NULL,
                total REAL NOT NULL,
                pagamento TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        # -------------------------------------------------
        # ADMINISTRADORES
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS administradores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL
            )
        """)

        banco.commit()

        # -------------------------------------------------
        # VERIFICAR COLUNAS CLIENTES
        # -------------------------------------------------

        cursor.execute(
            "PRAGMA table_info(clientes)"
        )

        colunas = [
            coluna["name"]
            for coluna in cursor.fetchall()
        ]

        if "telefone" not in colunas:

            print("Adicionando coluna telefone...")

            cursor.execute("""
                ALTER TABLE clientes
                ADD COLUMN telefone TEXT NOT NULL DEFAULT ''
            """)

        if "endereco" not in colunas:

            print("Adicionando coluna endereco...")

            cursor.execute("""
                ALTER TABLE clientes
                ADD COLUMN endereco TEXT NOT NULL DEFAULT ''
            """)

        banco.commit()

        print("Tabelas verificadas com sucesso.")
        print("Estrutura do banco atualizada.")
        print("")

    except sqlite3.Error as erro:

        print("ERRO AO CRIAR/ATUALIZAR TABELAS:")
        print(erro)

    finally:

        if banco:
            banco.close()


criar_tabelas()


# =========================================================
# FILTRO JSON
# =========================================================

@app.template_filter("from_json")
def from_json(valor):

    try:
        return json.loads(valor)

    except Exception:
        return []


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    cliente = session.get("cliente")

    return render_template(
        "home.html",
        cliente=cliente
    )


# =========================================================
# HOME COM ID
# =========================================================

@app.route("/home/<int:cliente_id>")
def home_cliente(cliente_id):

    if "cliente" not in session:
        return redirect("/login")

    return render_template(
        "home.html",
        cliente=session.get("cliente")
    )


# =========================================================
# LOGIN CLIENTE
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        return render_template(
            "login.html",
            mensagem=""
        )

    nome = request.form.get(
        "nome",
        ""
    ).strip()

    senha = request.form.get(
        "senha",
        ""
    )

    if not nome:

        return render_template(
            "login.html",
            mensagem="Digite seu nome."
        )

    if not senha:

        return render_template(
            "login.html",
            mensagem="Digite sua senha."
        )

    banco = None

    try:

        banco = conectar()
        cursor = banco.cursor()

        cursor.execute("""
            SELECT id, nome, senha, telefone
            FROM clientes
            WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?))
            LIMIT 1
        """, (nome,))

        cliente = cursor.fetchone()

    except sqlite3.Error as erro:

        print("ERRO SQLITE NO LOGIN:", erro)

        return render_template(
            "login.html",
            mensagem="Erro ao acessar o banco de dados."
        )

    finally:

        if banco:
            banco.close()

    if cliente is None:

        return render_template(
            "login.html",
            mensagem="Nome ou senha incorretos."
        )

    if str(cliente["senha"]) != senha:

        return render_template(
            "login.html",
            mensagem="Nome ou senha incorretos."
        )

    session.clear()

    session["cliente"] = cliente["nome"]
    session["cliente_id"] = cliente["id"]
    session["telefone"] = cliente["telefone"]

    destino = session.pop(
        "voltar_depois_login",
        None
    )

    if destino:
        return redirect(destino)

    return redirect("/")


# =========================================================
# CADASTRO CLIENTE
# =========================================================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "GET":

        return render_template(
            "cadastro.html",
            mensagem=""
        )

    nome = request.form.get(
        "nome",
        ""
    ).strip()

    telefone = request.form.get(
        "telefone",
        ""
    ).strip()

    senha = request.form.get(
        "senha",
        ""
    )

    confirmar_senha = request.form.get(
        "confirmar_senha",
        ""
    )

    if not nome:

        return render_template(
            "cadastro.html",
            mensagem="Digite seu nome."
        )

    if not telefone:

        return render_template(
            "cadastro.html",
            mensagem="Digite seu telefone."
        )

    if not senha:

        return render_template(
            "cadastro.html",
            mensagem="Digite uma senha."
        )

    if len(senha) < 4:

        return render_template(
            "cadastro.html",
            mensagem="A senha precisa ter pelo menos 4 caracteres."
        )

    if senha != confirmar_senha:

        return render_template(
            "cadastro.html",
            mensagem="As senhas não são iguais."
        )

    banco = None

    try:

        banco = conectar()
        cursor = banco.cursor()

        cursor.execute("""
            SELECT id
            FROM clientes
            WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?))
            LIMIT 1
        """, (nome,))

        existente = cursor.fetchone()

        if existente:

            return render_template(
                "cadastro.html",
                mensagem="Esse nome já está cadastrado."
            )

        cursor.execute("""
            INSERT INTO clientes (
                nome,
                senha,
                telefone,
                endereco
            )
            VALUES (?, ?, ?, ?)
        """, (
            nome,
            senha,
            telefone,
            ""
        ))

        cliente_id = cursor.lastrowid

        banco.commit()

    except sqlite3.IntegrityError:

        if banco:
            banco.rollback()

        return render_template(
            "cadastro.html",
            mensagem="Esse nome já está cadastrado."
        )

    except sqlite3.Error as erro:

        if banco:
            banco.rollback()

        print("ERRO SQLITE NO CADASTRO:", erro)

        return render_template(
            "cadastro.html",
            mensagem="Erro ao cadastrar usuário."
        )

    finally:

        if banco:
            banco.close()

    session.clear()

    session["cliente"] = nome
    session["cliente_id"] = cliente_id
    session["telefone"] = telefone

    destino = session.pop(
        "voltar_depois_login",
        None
    )

    if destino:
        return redirect(destino)

    return redirect("/")


# =========================================================
# SAIR CLIENTE
# =========================================================

@app.route("/sair")
def sair():

    session.clear()

    return redirect("/login")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# CARDÁPIO
# =========================================================

@app.route("/pedido")
def pedido():

    return render_template(
        "pedido.html",
        cliente=session.get("cliente"),
        cliente_id=session.get("cliente_id")
    )


# =========================================================
# VERIFICAR LOGIN
# =========================================================

@app.route("/verificar-login")
def verificar_login():

    if "cliente" in session:

        return jsonify({
            "logado": True,
            "cliente": session.get("cliente"),
            "cliente_id": session.get("cliente_id")
        })

    return jsonify({
        "logado": False
    })


# =========================================================
# IR PARA LOGIN
# =========================================================

@app.route("/ir-para-login")
def ir_para_login():

    destino = request.args.get(
        "next",
        "/pedido"
    )

    if not destino.startswith("/"):
        destino = "/pedido"

    session["voltar_depois_login"] = destino

    return redirect("/login")


# =========================================================
# PAGAMENTO
# =========================================================

@app.route("/pagamento")
def pagamento():

    if "cliente" not in session:

        session["voltar_depois_login"] = "/pagamento"

        return redirect("/login")

    return render_template(
        "pagamento.html"
    )


# =========================================================
# FINALIZAR PEDIDO
# =========================================================

@app.route("/finalizar-pedido", methods=["POST"])
def finalizar_pedido():

    if "cliente" not in session:

        return jsonify({
            "sucesso": False,
            "login": False,
            "mensagem": "Faça login para finalizar o pedido."
        }), 401

    dados = request.get_json(
        silent=True
    )

    if not dados:

        return jsonify({
            "sucesso": False,
            "mensagem": "Nenhum pedido recebido."
        }), 400

    carrinho = dados.get("carrinho")

    if carrinho is None:

        carrinho = dados.get(
            "itens",
            []
        )

    pagamento = dados.get(
        "pagamento",
        ""
    )

    if not carrinho:

        return jsonify({
            "sucesso": False,
            "mensagem": "O carrinho está vazio."
        }), 400

    if not pagamento:

        return jsonify({
            "sucesso": False,
            "mensagem": "Escolha uma forma de pagamento."
        }), 400

    lista_itens = []
    total_calculado = 0.0

    try:

        for item in carrinho:

            nome_produto = str(
                item.get(
                    "nome",
                    "Produto"
                )
            ).strip()

            try:

                quantidade = int(
                    item.get(
                        "quantidade",
                        1
                    )
                )

            except Exception:

                quantidade = 1

            try:

                preco = float(
                    item.get(
                        "preco",
                        0
                    )
                )

            except Exception:

                preco = 0.0

            if quantidade < 1:
                quantidade = 1

            if preco < 0:
                preco = 0.0

            subtotal = preco * quantidade

            total_calculado += subtotal

            lista_itens.append({
                "nome": nome_produto,
                "quantidade": quantidade,
                "preco": preco
            })

    except Exception as erro:

        print(
            "ERRO AO PROCESSAR CARRINHO:",
            erro
        )

        return jsonify({
            "sucesso": False,
            "mensagem": "Não foi possível processar os produtos."
        }), 400

    total = total_calculado

    itens_texto = json.dumps(
        lista_itens,
        ensure_ascii=False
    )

    banco = None

    try:

        banco = conectar()
        cursor = banco.cursor()

        cursor.execute("""
            INSERT INTO pedidos (
                cliente,
                itens,
                total,
                pagamento,
                status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["cliente"],
            itens_texto,
            total,
            pagamento,
            "Em processamento"
        ))

        pedido_id = cursor.lastrowid

        banco.commit()

    except sqlite3.Error as erro:

        if banco:
            banco.rollback()

        print(
            "ERRO AO SALVAR PEDIDO:",
            erro
        )

        return jsonify({
            "sucesso": False,
            "mensagem": "Erro ao salvar o pedido."
        }), 500

    finally:

        if banco:
            banco.close()

    return jsonify({
        "sucesso": True,
        "pedido_id": pedido_id,
        "total": total,
        "status": "Em processamento"
    })


# =========================================================
# PEDIDO CONFIRMADO
# =========================================================

@app.route("/pedido-confirmado")
def pedido_confirmado():

    if "cliente" not in session:
        return redirect("/login")

    pedido_id = request.args.get("id")

    return render_template(
        "pedido_confirmado.html",
        pedido_id=pedido_id
    )


# =========================================================
# MEUS PEDIDOS
# =========================================================

@app.route("/meus-pedidos")
def meus_pedidos():

    if "cliente" not in session:
        return redirect("/login")

    banco = None

    try:

        banco = conectar()
        cursor = banco.cursor()

        cursor.execute("""
            SELECT *
            FROM pedidos
            WHERE cliente = ?
            ORDER BY id DESC
        """, (
            session["cliente"],
        ))

        pedidos = cursor.fetchall()

    except sqlite3.Error as erro:

        print(
            "ERRO AO BUSCAR PEDIDOS:",
            erro
        )

        pedidos = []

    finally:

        if banco:
            banco.close()

    return render_template(
        "meus_pedidos.html",
        pedidos=pedidos
    )


@app.route("/meus-pedidos/<int:cliente_id>")
def meus_pedidos_cliente(cliente_id):

    if "cliente" not in session:
        return redirect("/login")

    return redirect("/meus-pedidos")


# =========================================================
# =========================================================
#                    ADMINISTRADOR
# =========================================================
# =========================================================


# =========================================================
# CADASTRO ADMIN
# =========================================================

@app.route("/admin-cadastro", methods=["GET", "POST"])
def admin_cadastro():

    if request.method == "GET":

        return render_template(
            "admin_cadastro.html",
            mensagem=""
        )

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    senha = request.form.get(
        "senha",
        ""
    )

    confirmar_senha = request.form.get(
        "confirmar_senha",
        ""
    )

    if not email:

        return render_template(
            "admin_cadastro.html",
            mensagem="Digite o e-mail do administrador."
        )

    if "@" not in email:

        return render_template(
            "admin_cadastro.html",
            mensagem="Digite um e-mail válido."
        )

    if not senha:

        return render_template(
            "admin_cadastro.html",
            mensagem="Digite uma senha."
        )

    if len(senha) < 4:

        return render_template(
            "admin_cadastro.html",
            mensagem="A senha precisa ter pelo menos 4 caracteres."
        )

    if senha != confirmar_senha:

        return render_template(
            "admin_cadastro.html",
            mensagem="As senhas não são iguais."
        )

    banco = None

    try:

        banco = conectar()
        cursor = banco.cursor()

        cursor.execute("""
            SELECT id
            FROM administradores
            WHERE LOWER(email) = LOWER(?)
            LIMIT 1
        """, (email,))

        existente = cursor.fetchone()

        if existente:

            return render_template(
                "admin_cadastro.html",
                mensagem="Esse e-mail já está cadastrado como administrador."
            )

        cursor.execute("""
            INSERT INTO administradores (
                email,
                senha
            )
            VALUES (?, ?)
        """, (
            email,
            senha
        ))

        banco.commit()

    except sqlite3.IntegrityError:

        if banco:
            banco.rollback()

        return render_template(
            "admin_cadastro.html",
            mensagem="Esse e-mail já está cadastrado."
        )

    except sqlite3.Error as erro:

        if banco:
            banco.rollback()

        print(
            "ERRO AO CADASTRAR ADMIN:",
            erro
        )

        return render_template(
            "admin_cadastro.html",
            mensagem="Erro ao cadastrar administrador."
        )

    finally:

        if banco:
            banco.close()

    return redirect("/admin-login")


# =========================================================
# LOGIN ADMIN
# =========================================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "GET":

        return render_template(
            "admin_login.html",
            mensagem=""
        )

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    senha = request.form.get(
        "senha",
        ""
    )

    if not email:

        return render_template(
            "admin_login.html",
            mensagem="Digite seu e-mail."
        )

    if not senha:

        return render_template(
            "admin_login.html",
            mensagem="Digite sua senha."
        )

    banco = None

    try:

        banco = conectar()
        cursor = banco.cursor()

        cursor.execute("""
            SELECT id, email, senha
            FROM administradores
            WHERE LOWER(TRIM(email)) = LOWER(TRIM(?))
            LIMIT 1
        """, (email,))

        admin = cursor.fetchone()

    except sqlite3.Error as erro:

        print(
            "ERRO NO LOGIN ADMIN:",
            erro
        )

        return render_template(
            "admin_login.html",
            mensagem="Erro ao acessar o banco de dados."
        )

    finally:

        if banco:
            banco.close()

    if admin is None:

        return render_template(
            "admin_login.html",
            mensagem="E-mail ou senha incorretos."
        )

    if str(admin["senha"]) != senha:

        return render_template(
            "admin_login.html",
            mensagem="E-mail ou senha incorretos."
        )

    session.clear()

    session["admin"] = True
    session["admin_id"] = admin["id"]
    session["admin_email"] = admin["email"]

    return redirect("/admin")


# =========================================================
# PAINEL ADMIN
# =========================================================

@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/admin-login")

    banco = None

    try:

        banco = conectar()
        cursor = banco.cursor()

        # -------------------------------------------------
        # TODOS OS PEDIDOS
        # -------------------------------------------------

        cursor.execute("""
            SELECT *
            FROM pedidos
            ORDER BY id DESC
        """)

        pedidos = cursor.fetchall()

        # -------------------------------------------------
        # CLIENTES
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM clientes
        """)

        total_clientes = cursor.fetchone()["total"]

        # -------------------------------------------------
        # TOTAL DE PEDIDOS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM pedidos
        """)

        total_pedidos = cursor.fetchone()["total"]

        # -------------------------------------------------
        # PEDIDOS PAGOS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM pedidos
            WHERE status = 'Pago'
        """)

        pedidos_pagos = cursor.fetchone()["total"]

        # -------------------------------------------------
        # PEDIDOS EM PROCESSAMENTO
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM pedidos
            WHERE status = 'Em processamento'
        """)

        pedidos_processamento = cursor.fetchone()["total"]

        # -------------------------------------------------
        # PEDIDOS EM PREPARAÇÃO
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM pedidos
            WHERE status = 'Em preparação'
        """)

        pedidos_preparacao = cursor.fetchone()["total"]

        # -------------------------------------------------
        # PEDIDOS PRONTOS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM pedidos
            WHERE status = 'Pronto'
        """)

        pedidos_prontos = cursor.fetchone()["total"]

        # -------------------------------------------------
        # PEDIDOS ENTREGUES
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM pedidos
            WHERE status = 'Entregue'
        """)

        pedidos_entregues = cursor.fetchone()["total"]

        # -------------------------------------------------
        # PEDIDOS CANCELADOS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM pedidos
            WHERE status = 'Cancelado'
        """)

        pedidos_cancelados = cursor.fetchone()["total"]

        # -------------------------------------------------
        # FATURAMENTO TOTAL
        # NÃO CONSIDERA CANCELADOS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) AS total
            FROM pedidos
            WHERE status != 'Cancelado'
        """)

        faturamento = cursor.fetchone()["total"]

        # -------------------------------------------------
        # VALOR CANCELADO
        # -------------------------------------------------

        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) AS total
            FROM pedidos
            WHERE status = 'Cancelado'
        """)

        valor_cancelado = cursor.fetchone()["total"]

        # -------------------------------------------------
        # VALOR DOS PEDIDOS ENTREGUES
        # -------------------------------------------------

        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) AS total
            FROM pedidos
            WHERE status = 'Entregue'
        """)

        valor_entregue = cursor.fetchone()["total"]

    except sqlite3.Error as erro:

        print(
            "ERRO AO CARREGAR ADMIN:",
            erro
        )

        pedidos = []

        total_clientes = 0
        total_pedidos = 0

        pedidos_pagos = 0
        pedidos_processamento = 0
        pedidos_preparacao = 0
        pedidos_prontos = 0
        pedidos_entregues = 0
        pedidos_cancelados = 0

        faturamento = 0
        valor_cancelado = 0
        valor_entregue = 0

    finally:

        if banco:
            banco.close()

    return render_template(
        "admin.html",

        pedidos=pedidos,

        total_clientes=total_clientes,
        total_pedidos=total_pedidos,

        pedidos_pagos=pedidos_pagos,
        pedidos_processamento=pedidos_processamento,
        pedidos_preparacao=pedidos_preparacao,
        pedidos_prontos=pedidos_prontos,
        pedidos_entregues=pedidos_entregues,
        pedidos_cancelados=pedidos_cancelados,

        faturamento=faturamento,
        valor_cancelado=valor_cancelado,
        valor_entregue=valor_entregue,

        admin_email=session.get("admin_email")
    )


# =========================================================
# ALTERAR STATUS DO PEDIDO
#
# AGORA ACEITA FORMULÁRIO.
# NÃO PRECISA DE JAVASCRIPT.
# =========================================================

@app.route(
    "/admin/alterar-status/<int:pedido_id>",
    methods=["POST"]
)
def alterar_status(pedido_id):

    if not session.get("admin"):

        return redirect("/admin-login")

    # -----------------------------------------------------
    # RECEBER STATUS PELO FORMULÁRIO
    # -----------------------------------------------------

    novo_status = request.form.get(
        "status",
        ""
    ).strip()

    status_permitidos = [
        "Em processamento",
        "Pago",
        "Em preparação",
        "Pronto",
        "Entregue",
        "Cancelado"
    ]

    if novo_status not in status_permitidos:

        return redirect("/admin")

    banco = None

    try:

        banco = conectar()
        cursor = banco.cursor()

        cursor.execute("""
            SELECT id
            FROM pedidos
            WHERE id = ?
            LIMIT 1
        """, (pedido_id,))

        pedido = cursor.fetchone()

        if pedido is None:

            return redirect("/admin")

        cursor.execute("""
            UPDATE pedidos
            SET status = ?
            WHERE id = ?
        """, (
            novo_status,
            pedido_id
        ))

        banco.commit()

    except sqlite3.Error as erro:

        if banco:
            banco.rollback()

        print(
            "ERRO AO ALTERAR STATUS:",
            erro
        )

    finally:

        if banco:
            banco.close()

    return redirect("/admin")


# =========================================================
# LOGOUT ADMIN
# =========================================================

@app.route("/admin-logout")
def admin_logout():

    session.clear()

    return redirect("/admin-login")


# =========================================================
# EXECUTAR
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=False,
        use_reloader=False,
        host="127.0.0.1",
        port=5000
    )