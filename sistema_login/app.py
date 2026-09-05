from flask import (
    Flask,
    render_template,
    render_template_string,
    request,
    redirect,
    jsonify,
    session,
    url_for,
    flash
)

import sqlite3
import os
import json
import uuid

from datetime import datetime
from werkzeug.utils import secure_filename


# =========================================================
# CONFIGURAÇÃO
# =========================================================

app = Flask(__name__)

app.secret_key = "devjuan-chave-secreta-2026"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Seu banco está um nível acima da pasta sistema_login
CAMINHO_BANCO = os.path.abspath(
    os.path.join(BASE_DIR, "..", "lanchonete.db")
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "uploads"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


# =========================================================
# ADMINISTRADOR
# =========================================================

ADMIN_EMAIL = "lanches@gmail.com"
ADMIN_SENHA = "2302"


# =========================================================
# STATUS DOS PEDIDOS
# =========================================================

STATUS_PERMITIDOS = [
    "Em processamento",
    "Pago",
    "Em preparação",
    "Pronto",
    "Entregue",
    "Cancelado"
]


# =========================================================
# BANCO
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
# FUNÇÕES AUXILIARES DO BANCO
# =========================================================

def colunas_tabela(banco, tabela):
    resultado = banco.execute(
        f"PRAGMA table_info({tabela})"
    ).fetchall()

    return {
        coluna["name"]
        for coluna in resultado
    }


def tem_coluna(banco, tabela, coluna):
    return coluna in colunas_tabela(
        banco,
        tabela
    )


def adicionar_coluna(
    banco,
    tabela,
    coluna,
    tipo
):
    if not tem_coluna(
        banco,
        tabela,
        coluna
    ):
        banco.execute(
            f"""
            ALTER TABLE {tabela}
            ADD COLUMN {coluna} {tipo}
            """
        )


# =========================================================
# CRIAR / CORRIGIR TABELAS
# =========================================================

def criar_tabelas():

    banco = conectar()

    try:

        # -------------------------------------------------
        # CLIENTES
        # -------------------------------------------------

        banco.execute(
            """
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                telefone TEXT DEFAULT '',
                endereco TEXT DEFAULT ''
            )
            """
        )

        adicionar_coluna(
            banco,
            "clientes",
            "telefone",
            "TEXT DEFAULT ''"
        )

        adicionar_coluna(
            banco,
            "clientes",
            "endereco",
            "TEXT DEFAULT ''"
        )


        # -------------------------------------------------
        # PRODUTOS
        # -------------------------------------------------

        banco.execute(
            """
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                preco REAL NOT NULL DEFAULT 0,
                imagem TEXT DEFAULT '',
                estoque INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        adicionar_coluna(
            banco,
            "produtos",
            "descricao",
            "TEXT DEFAULT ''"
        )

        adicionar_coluna(
            banco,
            "produtos",
            "preco",
            "REAL NOT NULL DEFAULT 0"
        )

        adicionar_coluna(
            banco,
            "produtos",
            "imagem",
            "TEXT DEFAULT ''"
        )

        adicionar_coluna(
            banco,
            "produtos",
            "estoque",
            "INTEGER NOT NULL DEFAULT 0"
        )


        # -------------------------------------------------
        # PEDIDOS
        #
        # Incluí também colunas antigas:
        # cliente_id
        # produto
        # quantidade
        # preco
        #
        # Isso evita os erros de NOT NULL que estavam
        # acontecendo no seu banco.
        # -------------------------------------------------

        banco.execute(
            """
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                cliente_id INTEGER,

                cliente TEXT NOT NULL DEFAULT '',

                produto TEXT,

                quantidade INTEGER,

                preco REAL,

                itens TEXT NOT NULL DEFAULT '[]',

                total REAL NOT NULL DEFAULT 0,

                pagamento TEXT NOT NULL DEFAULT '',

                status TEXT NOT NULL
                    DEFAULT 'Em processamento',

                entrega TEXT NOT NULL
                    DEFAULT 'Retirada no local',

                endereco TEXT DEFAULT '',

                arquivado INTEGER NOT NULL DEFAULT 0,

                criado_em TEXT DEFAULT ''
            )
            """
        )


        # -------------------------------------------------
        # MIGRAÇÃO DO BANCO ANTIGO
        # -------------------------------------------------

        adicionar_coluna(
            banco,
            "pedidos",
            "cliente_id",
            "INTEGER"
        )

        adicionar_coluna(
            banco,
            "pedidos",
            "cliente",
            "TEXT DEFAULT ''"
        )

        adicionar_coluna(
            banco,
            "pedidos",
            "produto",
            "TEXT"
        )

        adicionar_coluna(
            banco,
            "pedidos",
            "quantidade",
            "INTEGER"
        )

        adicionar_coluna(
            banco,
            "pedidos",
            "preco",
            "REAL"
        )

        adicionar_coluna(
            banco,
            "pedidos",
            "itens",
            "TEXT DEFAULT '[]'"
        )

        adicionar_coluna(
            banco,
            "pedidos",
            "total",
            "REAL DEFAULT 0"
        )

        adicionar_coluna(
            banco,
            "pedidos",
            "pagamento",
            "TEXT DEFAULT ''"
        )

        adicionar_coluna(
            banco,
            "pedidos",
            "status",
            "TEXT DEFAULT 'Em processamento'"
        )

        adicionar_coluna(
            banco,
            "pedidos",
            "entrega",
            "TEXT DEFAULT 'Retirada no local'"
        )

        adicionar_coluna(
            banco,
            "pedidos",
            "endereco",
            "TEXT DEFAULT ''"
        )

        adicionar_coluna(
            banco,
            "pedidos",
            "arquivado",
            "INTEGER NOT NULL DEFAULT 0"
        )

        adicionar_coluna(
            banco,
            "pedidos",
            "criado_em",
            "TEXT DEFAULT ''"
        )


        # -------------------------------------------------
        # CORRIGIR VALORES NULL ANTIGOS
        # -------------------------------------------------

        if tem_coluna(
            banco,
            "pedidos",
            "itens"
        ):
            banco.execute(
                """
                UPDATE pedidos
                SET itens = '[]'
                WHERE itens IS NULL
                """
            )

        if tem_coluna(
            banco,
            "pedidos",
            "total"
        ):
            banco.execute(
                """
                UPDATE pedidos
                SET total = 0
                WHERE total IS NULL
                """
            )

        if tem_coluna(
            banco,
            "pedidos",
            "status"
        ):
            banco.execute(
                """
                UPDATE pedidos
                SET status = 'Em processamento'
                WHERE status IS NULL
                   OR TRIM(status) = ''
                """
            )

        if tem_coluna(
            banco,
            "pedidos",
            "pagamento"
        ):
            banco.execute(
                """
                UPDATE pedidos
                SET pagamento = ''
                WHERE pagamento IS NULL
                """
            )

        if tem_coluna(
            banco,
            "pedidos",
            "entrega"
        ):
            banco.execute(
                """
                UPDATE pedidos
                SET entrega = 'Retirada no local'
                WHERE entrega IS NULL
                   OR TRIM(entrega) = ''
                """
            )

        if tem_coluna(
            banco,
            "pedidos",
            "arquivado"
        ):
            banco.execute(
                """
                UPDATE pedidos
                SET arquivado = 0
                WHERE arquivado IS NULL
                """
            )

        banco.commit()

        print("=" * 60)
        print("BANCO INICIALIZADO")
        print("Banco:", CAMINHO_BANCO)
        print("=" * 60)

    except Exception:
        banco.rollback()
        raise

    finally:
        banco.close()


# =========================================================
# JINJA - FILTRO from_json
# =========================================================

@app.template_filter("from_json")
def from_json(valor):

    if not valor:
        return []

    if isinstance(valor, list):
        return valor

    try:
        return json.loads(valor)

    except Exception:
        return []


# =========================================================
# FUNÇÕES DE LOGIN
# =========================================================

def cliente_logado():

    return (
        session.get("cliente_id") is not None
        and
        (
            session.get("tipo") == "cliente"
            or
            session.get("tipo_usuario") == "cliente"
        )
    )


def admin_logado():

    return (
        session.get("admin") is True
        or
        session.get("admin_logado") is True
        or
        session.get("tipo") == "admin"
        or
        session.get("tipo_usuario") == "admin"
    )


def logar_admin():

    session.clear()

    session["tipo"] = "admin"
    session["tipo_usuario"] = "admin"

    session["admin"] = True
    session["admin_logado"] = True

    session["admin_email"] = ADMIN_EMAIL


def logar_cliente(cliente):

    session.clear()

    session["tipo"] = "cliente"
    session["tipo_usuario"] = "cliente"

    session["admin"] = False
    session["admin_logado"] = False

    session["cliente"] = cliente["nome"]
    session["cliente_id"] = cliente["id"]

    if "telefone" in cliente.keys():
        session["telefone"] = cliente["telefone"] or ""

    if "endereco" in cliente.keys():
        session["endereco"] = cliente["endereco"] or ""


# =========================================================
# CONVERSÃO DE NÚMEROS
# =========================================================

def numero(valor, padrao=0):

    try:

        if valor is None:
            return padrao

        texto = str(valor).strip()

        texto = texto.replace(
            ",",
            "."
        )

        return float(texto)

    except Exception:
        return padrao


def inteiro(valor, padrao=0):

    try:
        return int(
            float(valor)
        )

    except Exception:
        return padrao


# =========================================================
# UPLOAD DE IMAGEM
# =========================================================

def preparar_imagem(arquivo):

    if not arquivo:
        return ""

    if not arquivo.filename:
        return ""

    if "." not in arquivo.filename:
        return ""

    extensao = (
        arquivo.filename
        .rsplit(".", 1)[1]
        .lower()
    )

    permitidas = {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp"
    }

    if extensao not in permitidas:
        return ""

    nome_seguro = secure_filename(
        arquivo.filename
    )

    novo_nome = (
        uuid.uuid4().hex
        + "."
        + nome_seguro.rsplit(".", 1)[1].lower()
    )

    return novo_nome


# =========================================================
# SALVAR PEDIDO
#
# Compatível com bancos antigos.
# =========================================================

def salvar_pedido(
    banco,
    cliente,
    itens,
    total,
    pagamento,
    entrega,
    endereco
):

    info = banco.execute(
        "PRAGMA table_info(pedidos)"
    ).fetchall()

    nomes_colunas = {
        coluna["name"]
        for coluna in info
    }


    nomes_produtos = []

    for item in itens:

        nome = str(
            item.get("nome", "")
        ).strip()

        if nome:
            nomes_produtos.append(nome)


    quantidade_total = 0

    for item in itens:

        quantidade_total += inteiro(
            item.get("quantidade", 1),
            1
        )


    preco_primeiro = 0

    if itens:

        preco_primeiro = numero(
            itens[0].get("preco"),
            0
        )


    agora = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )


    # -----------------------------------------------------
    # Valores para qualquer versão antiga do banco
    # -----------------------------------------------------

    valores = {

        "cliente_id":
            cliente["id"],

        "cliente":
            cliente["nome"],

        "produto":
            ", ".join(nomes_produtos),

        "quantidade":
            quantidade_total,

        "preco":
            preco_primeiro,

        "itens":
            json.dumps(
                itens,
                ensure_ascii=False
            ),

        "total":
            total,

        "pagamento":
            pagamento,

        "status":
            "Em processamento",

        "entrega":
            entrega,

        "endereco":
            endereco,

        "arquivado":
            0,

        "criado_em":
            agora,

        "data":
            agora,

        "data_pedido":
            agora,

        "created_at":
            agora,

        "observacao":
            "",

        "observacoes":
            ""
    }


    campos = []

    valores_sql = []


    for campo, valor in valores.items():

        if campo in nomes_colunas:

            campos.append(campo)
            valores_sql.append(valor)


    # -----------------------------------------------------
    # Verifica outras colunas obrigatórias antigas
    # -----------------------------------------------------

    obrigatorias = []

    for coluna in info:

        nome = coluna["name"]

        not_null = coluna["notnull"]
        primary_key = coluna["pk"]
        default = coluna["dflt_value"]

        if (
            not_null
            and not primary_key
            and default is None
            and nome not in campos
        ):

            obrigatorias.append(nome)


    if obrigatorias:

        raise sqlite3.IntegrityError(
            "Colunas obrigatórias não compatíveis: "
            + ", ".join(obrigatorias)
        )


    placeholders = ", ".join(
        "?"
        for _ in campos
    )


    sql = f"""
        INSERT INTO pedidos (
            {", ".join(campos)}
        )
        VALUES (
            {placeholders}
        )
    """


    cursor = banco.execute(
        sql,
        valores_sql
    )


    return cursor.lastrowid


# =========================================================
# INICIALIZAR BANCO
# =========================================================

criar_tabelas()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "home.html",
        cliente=session.get("cliente")
    )


@app.route("/home/<int:cliente_id>")
def home_id(cliente_id):

    if cliente_logado():
        return redirect(
            url_for("home")
        )

    return redirect(
        url_for("login")
    )


# =========================================================
# LOGIN UNIFICADO
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "GET":

        return render_template(
            "login.html",
            mensagem=None
        )


    nome = request.form.get(
        "nome",
        ""
    ).strip()

    senha = request.form.get(
        "senha",
        ""
    ).strip()


    if not nome or not senha:

        return render_template(
            "login.html",
            mensagem="Preencha o nome e a senha."
        )


    # -----------------------------------------------------
    # LOGIN ADMIN
    # -----------------------------------------------------

    if (
        nome.casefold()
        == ADMIN_EMAIL.casefold()
        and
        senha == ADMIN_SENHA
    ):

        logar_admin()

        return redirect(
            url_for("admin")
        )


    # -----------------------------------------------------
    # LOGIN CLIENTE
    # -----------------------------------------------------

    banco = conectar()

    try:

        cliente = banco.execute(
            """
            SELECT *
            FROM clientes

            WHERE LOWER(
                TRIM(nome)
            )
            =
            LOWER(
                TRIM(?)
            )

            LIMIT 1
            """,
            (nome,)
        ).fetchone()

    except sqlite3.Error as erro:

        print(
            "ERRO SQLITE NO LOGIN:",
            repr(erro)
        )

        return render_template(
            "login.html",
            mensagem="Erro ao acessar o banco de dados."
        )

    finally:
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


    destino = session.get(
        "voltar_depois_login"
    )


    logar_cliente(cliente)


    if destino:

        session.pop(
            "voltar_depois_login",
            None
        )

        return redirect(destino)


    return redirect(
        url_for("home")
    )


# =========================================================
# CADASTRO
# =========================================================

@app.route(
    "/cadastro",
    methods=["GET", "POST"]
)
def cadastro():

    if request.method == "GET":

        return render_template(
            "cadastro.html",
            mensagem=None
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
    ).strip()

    confirmar_senha = request.form.get(
        "confirmar_senha",
        ""
    ).strip()


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


    if senha != confirmar_senha:

        return render_template(
            "cadastro.html",
            mensagem="As senhas não coincidem."
        )


    if (
        nome.casefold()
        == ADMIN_EMAIL.casefold()
    ):

        return render_template(
            "cadastro.html",
            mensagem="Esse usuário é reservado para o administrador."
        )


    banco = conectar()

    try:

        existente = banco.execute(
            """
            SELECT id
            FROM clientes

            WHERE LOWER(
                TRIM(nome)
            )
            =
            LOWER(
                TRIM(?)
            )

            LIMIT 1
            """,
            (nome,)
        ).fetchone()


        if existente:

            return render_template(
                "cadastro.html",
                mensagem="Esse nome já está cadastrado."
            )


        colunas = colunas_tabela(
            banco,
            "clientes"
        )


        campos = [
            "nome",
            "senha"
        ]

        valores = [
            nome,
            senha
        ]


        if "telefone" in colunas:

            campos.append(
                "telefone"
            )

            valores.append(
                telefone
            )


        if "endereco" in colunas:

            campos.append(
                "endereco"
            )

            valores.append(
                ""
            )


        placeholders = ", ".join(
            "?"
            for _ in valores
        )


        cursor = banco.execute(
            f"""
            INSERT INTO clientes (
                {", ".join(campos)}
            )

            VALUES (
                {placeholders}
            )
            """,
            valores
        )


        cliente_id = cursor.lastrowid


        cliente = banco.execute(
            """
            SELECT *
            FROM clientes
            WHERE id = ?
            """,
            (cliente_id,)
        ).fetchone()


        banco.commit()


    except sqlite3.Error as erro:

        banco.rollback()

        print(
            "ERRO NO CADASTRO:",
            repr(erro)
        )

        return render_template(
            "cadastro.html",
            mensagem=f"Erro ao cadastrar: {erro}"
        )

    finally:

        banco.close()


    logar_cliente(
        cliente
    )


    return redirect(
        url_for("home")
    )


# =========================================================
# SAIR
# =========================================================

@app.route("/sair")
def sair():

    session.clear()

    return redirect(
        url_for("login")
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# PEDIDO / CARDÁPIO
# =========================================================

@app.route("/pedido")
def pedido():

    if not cliente_logado():

        session["voltar_depois_login"] = url_for(
            "pedido"
        )

        return redirect(
            url_for("login")
        )


    banco = conectar()

    try:

        produtos = banco.execute(
            """
            SELECT *
            FROM produtos
            ORDER BY id DESC
            """
        ).fetchall()

    finally:

        banco.close()


    return render_template(
        "pedido.html",
        produtos=produtos,
        cliente=session.get("cliente"),
        cliente_id=session.get("cliente_id")
    )


# =========================================================
# VERIFICAR LOGIN
# =========================================================

@app.route("/verificar-login")
def verificar_login():

    return jsonify(
        logado=cliente_logado(),
        admin=admin_logado(),
        cliente=session.get("cliente"),
        cliente_id=session.get("cliente_id"),
        tipo_usuario=session.get("tipo_usuario")
    )


# =========================================================
# IR PARA LOGIN
# =========================================================

@app.route("/ir-para-login")
def ir_para_login():

    destino = request.args.get(
        "proxima",
        url_for("pedido")
    )

    session["voltar_depois_login"] = destino

    return redirect(
        url_for("login")
    )


# =========================================================
# PAGAMENTO
# =========================================================

@app.route("/pagamento")
def pagamento():

    if not cliente_logado():

        session["voltar_depois_login"] = url_for(
            "pagamento"
        )

        return redirect(
            url_for("login")
        )


    return render_template(
        "pagamento.html",
        cliente=session.get("cliente"),
        telefone=session.get(
            "telefone",
            ""
        ),
        endereco=session.get(
            "endereco",
            ""
        )
    )


# =========================================================
# FINALIZAR PEDIDO
# =========================================================

@app.route(
    "/finalizar-pedido",
    methods=["POST"]
)
def finalizar_pedido():

    if not cliente_logado():

        return jsonify(
            sucesso=False,
            erro="Você precisa estar logado."
        ), 401


    dados = request.get_json(
        silent=True
    ) or {}


    carrinho = (
        dados.get("carrinho")
        or
        dados.get("itens")
        or
        []
    )


    pagamento = str(
        dados.get(
            "pagamento",
            ""
        )
    ).strip()


    entrega = str(
        dados.get(
            "entrega",
            "Retirada no local"
        )
    ).strip()


    if not entrega:

        entrega = "Retirada no local"


    endereco = str(
        dados.get(
            "endereco",
            ""
        )
    ).strip()


    if not carrinho:

        return jsonify(
            sucesso=False,
            erro="O carrinho está vazio."
        ), 400


    if not pagamento:

        return jsonify(
            sucesso=False,
            erro="Selecione uma forma de pagamento."
        ), 400


    if (
        entrega.lower()
        != "retirada no local"
        and
        not endereco
    ):

        return jsonify(
            sucesso=False,
            erro="Informe o endereço de entrega."
        ), 400


    banco = conectar()


    try:

        cliente = banco.execute(
            """
            SELECT *
            FROM clientes
            WHERE id = ?
            LIMIT 1
            """,
            (
                session["cliente_id"],
            )
        ).fetchone()


        if cliente is None:

            return jsonify(
                sucesso=False,
                erro="Cliente não encontrado."
            ), 404


        itens = []

        total = 0


        # -------------------------------------------------
        # VALIDAR CARRINHO NO BANCO
        # -------------------------------------------------

        for item_carrinho in carrinho:

            nome = str(
                item_carrinho.get(
                    "nome",
                    ""
                )
            ).strip()


            quantidade = inteiro(
                item_carrinho.get(
                    "quantidade",
                    1
                ),
                1
            )


            if not nome:

                raise ValueError(
                    "Item inválido no carrinho."
                )


            if quantidade <= 0:

                raise ValueError(
                    "Quantidade inválida."
                )


            produto = banco.execute(
                """
                SELECT *
                FROM produtos

                WHERE LOWER(
                    TRIM(nome)
                )
                =
                LOWER(
                    TRIM(?)
                )

                LIMIT 1
                """,
                (nome,)
            ).fetchone()


            if produto is None:

                raise ValueError(
                    f"O produto '{nome}' "
                    "não existe mais no cardápio."
                )


            estoque_atual = inteiro(
                produto["estoque"],
                0
            )


            if estoque_atual < quantidade:

                raise ValueError(
                    f"Estoque insuficiente para "
                    f"'{produto['nome']}'. "
                    f"Disponível: {estoque_atual}."
                )


            preco = numero(
                produto["preco"],
                0
            )


            subtotal = round(
                preco * quantidade,
                2
            )


            total += subtotal


            itens.append(
                {
                    "id": produto["id"],

                    "nome": produto["nome"],

                    "preco": preco,

                    "quantidade": quantidade,

                    "imagem":
                        produto["imagem"] or "",

                    "subtotal":
                        subtotal
                }
            )


        total = round(
            total,
            2
        )


        # -------------------------------------------------
        # BAIXAR ESTOQUE
        # -------------------------------------------------

        for item in itens:

            banco.execute(
                """
                UPDATE produtos

                SET estoque =
                    estoque - ?

                WHERE id = ?
                """,
                (
                    item["quantidade"],
                    item["id"]
                )
            )


        # -------------------------------------------------
        # SALVAR ENDEREÇO
        # -------------------------------------------------

        if tem_coluna(
            banco,
            "clientes",
            "endereco"
        ):

            banco.execute(
                """
                UPDATE clientes

                SET endereco = ?

                WHERE id = ?
                """,
                (
                    endereco,
                    session["cliente_id"]
                )
            )


        # -------------------------------------------------
        # SALVAR PEDIDO
        # -------------------------------------------------

        pedido_id = salvar_pedido(
            banco=banco,
            cliente=cliente,
            itens=itens,
            total=total,
            pagamento=pagamento,
            entrega=entrega,
            endereco=endereco
        )


        banco.commit()


        session["endereco"] = endereco


        print("=" * 60)
        print("PEDIDO SALVO COM SUCESSO")
        print("Pedido:", pedido_id)
        print("Cliente:", cliente["nome"])
        print("Total:", total)
        print("=" * 60)


        return jsonify(
            sucesso=True,
            pedido_id=pedido_id,
            total=total,
            status="Em processamento"
        )


    except ValueError as erro:

        banco.rollback()

        print(
            "ERRO DE VALIDAÇÃO:",
            repr(erro)
        )

        return jsonify(
            sucesso=False,
            erro=str(erro)
        ), 400


    except sqlite3.Error as erro:

        banco.rollback()

        print(
            "=" * 60
        )

        print(
            "ERRO SQLITE AO SALVAR PEDIDO:"
        )

        print(
            repr(erro)
        )

        print(
            "=" * 60
        )

        return jsonify(
            sucesso=False,
            erro=f"Erro ao salvar pedido: {erro}"
        ), 500


    except Exception as erro:

        banco.rollback()

        print(
            "ERRO INESPERADO:",
            repr(erro)
        )

        return jsonify(
            sucesso=False,
            erro="Erro inesperado ao finalizar pedido."
        ), 500


    finally:

        banco.close()


# =========================================================
# PEDIDO CONFIRMADO
# =========================================================

@app.route("/pedido-confirmado")
def pedido_confirmado():

    if not cliente_logado():

        return redirect(
            url_for("login")
        )


    return render_template(
        "pedido_confirmado.html",
        cliente=session.get("cliente")
    )


# =========================================================
# MEUS PEDIDOS
# =========================================================

@app.route("/meus-pedidos")
def meus_pedidos():

    if not cliente_logado():

        return redirect(
            url_for("login")
        )


    banco = conectar()

    try:

        pedidos = banco.execute(
            """
            SELECT *
            FROM pedidos

            WHERE
                cliente_id = ?

                OR

                (
                    cliente_id IS NULL
                    AND cliente = ?
                )

            ORDER BY id DESC
            """,
            (
                session["cliente_id"],
                session.get(
                    "cliente",
                    ""
                )
            )
        ).fetchall()

    finally:

        banco.close()


    return render_template(
        "meus_pedidos.html",
        pedidos=pedidos,
        cliente=session.get("cliente")
    )


@app.route(
    "/meus-pedidos/<int:cliente_id>"
)
def meus_pedidos_id(cliente_id):

    if (
        cliente_logado()
        and
        int(
            session["cliente_id"]
        )
        == cliente_id
    ):

        return redirect(
            url_for("meus_pedidos")
        )


    return redirect(
        url_for("login")
    )


# =========================================================
# LOGIN ADMIN - COMPATIBILIDADE
# =========================================================

@app.route(
    "/admin-login",
    methods=["GET", "POST"]
)
@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "GET":

        return redirect(
            url_for("login")
        )


    email = request.form.get(
        "email",
        ""
    ).strip()

    senha = request.form.get(
        "senha",
        ""
    ).strip()


    if (
        email.casefold()
        == ADMIN_EMAIL.casefold()
        and
        senha == ADMIN_SENHA
    ):

        logar_admin()

        return redirect(
            url_for("admin")
        )


    flash(
        "E-mail ou senha de administrador incorretos.",
        "erro"
    )


    return redirect(
        url_for("login")
    )


# =========================================================
# PAINEL ADMINISTRATIVO
# =========================================================

@app.route("/admin")
def admin():

    if not admin_logado():

        return redirect(
            url_for("login")
        )


    banco = conectar()


    try:

        # -------------------------------------------------
        # PRODUTOS
        # -------------------------------------------------

        produtos = banco.execute(
            """
            SELECT *
            FROM produtos
            ORDER BY id DESC
            """
        ).fetchall()


        # -------------------------------------------------
        # PEDIDOS ATIVOS
        # -------------------------------------------------

        pedidos = banco.execute(
            """
            SELECT *
            FROM pedidos

            WHERE COALESCE(
                arquivado,
                0
            ) = 0

            ORDER BY id DESC
            """
        ).fetchall()


        # -------------------------------------------------
        # PEDIDOS ARQUIVADOS
        # -------------------------------------------------

        pedidos_arquivados = banco.execute(
            """
            SELECT *
            FROM pedidos

            WHERE COALESCE(
                arquivado,
                0
            ) = 1

            ORDER BY id DESC
            """
        ).fetchall()


        # -------------------------------------------------
        # CLIENTES
        # -------------------------------------------------

        total_clientes = banco.execute(
            """
            SELECT COUNT(*) AS total
            FROM clientes
            """
        ).fetchone()["total"]


        # -------------------------------------------------
        # PEDIDOS ATIVOS
        # -------------------------------------------------

        total_pedidos = banco.execute(
            """
            SELECT COUNT(*) AS total
            FROM pedidos

            WHERE COALESCE(
                arquivado,
                0
            ) = 0
            """
        ).fetchone()["total"]


        # -------------------------------------------------
        # ESTOQUE TOTAL
        # -------------------------------------------------

        estoque_total = banco.execute(
            """
            SELECT COALESCE(
                SUM(estoque),
                0
            ) AS total

            FROM produtos
            """
        ).fetchone()["total"]


        # -------------------------------------------------
        # PRODUTOS DISPONÍVEIS
        # -------------------------------------------------

        produtos_disponiveis = banco.execute(
            """
            SELECT COUNT(*) AS total
            FROM produtos

            WHERE estoque > 0
            """
        ).fetchone()["total"]


        # -------------------------------------------------
        # PRODUTOS ESGOTADOS
        # -------------------------------------------------

        produtos_esgotados = banco.execute(
            """
            SELECT COUNT(*) AS total
            FROM produtos

            WHERE estoque <= 0
            """
        ).fetchone()["total"]


        # -------------------------------------------------
        # PEDIDOS POR STATUS
        # -------------------------------------------------

        pedidos_pagos = banco.execute(
            """
            SELECT COUNT(*) AS total
            FROM pedidos

            WHERE status = 'Pago'
            """
        ).fetchone()["total"]


        pedidos_processamento = banco.execute(
            """
            SELECT COUNT(*) AS total
            FROM pedidos

            WHERE status = 'Em processamento'
            """
        ).fetchone()["total"]


        pedidos_preparacao = banco.execute(
            """
            SELECT COUNT(*) AS total
            FROM pedidos

            WHERE status = 'Em preparação'
            """
        ).fetchone()["total"]


        pedidos_prontos = banco.execute(
            """
            SELECT COUNT(*) AS total
            FROM pedidos

            WHERE status = 'Pronto'
            """
        ).fetchone()["total"]


        pedidos_entregues = banco.execute(
            """
            SELECT COUNT(*) AS total
            FROM pedidos

            WHERE status = 'Entregue'
            """
        ).fetchone()["total"]


        pedidos_cancelados = banco.execute(
            """
            SELECT COUNT(*) AS total
            FROM pedidos

            WHERE status = 'Cancelado'
            """
        ).fetchone()["total"]


        # -------------------------------------------------
        # FATURAMENTO
        #
        # Não considera cancelados.
        # -------------------------------------------------

        faturamento = banco.execute(
            """
            SELECT COALESCE(
                SUM(total),
                0
            ) AS total

            FROM pedidos

            WHERE status != 'Cancelado'
            """
        ).fetchone()["total"]


        # -------------------------------------------------
        # VALOR CANCELADO
        # -------------------------------------------------

        valor_cancelado = banco.execute(
            """
            SELECT COALESCE(
                SUM(total),
                0
            ) AS total

            FROM pedidos

            WHERE status = 'Cancelado'
            """
        ).fetchone()["total"]


        # -------------------------------------------------
        # VALOR ENTREGUE
        # -------------------------------------------------

        valor_entregue = banco.execute(
            """
            SELECT COALESCE(
                SUM(total),
                0
            ) AS total

            FROM pedidos

            WHERE status = 'Entregue'
            """
        ).fetchone()["total"]


    except sqlite3.Error as erro:

        print(
            "ERRO AO CARREGAR ADMIN:",
            repr(erro)
        )


        produtos = []
        pedidos = []
        pedidos_arquivados = []

        total_clientes = 0
        total_pedidos = 0

        estoque_total = 0

        produtos_disponiveis = 0
        produtos_esgotados = 0

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

        banco.close()


    return render_template(
        "admin.html",

        produtos=produtos,

        pedidos=pedidos,

        pedidos_arquivados=
            pedidos_arquivados,

        total_clientes=
            total_clientes,

        total_pedidos=
            total_pedidos,

        estoque_total=
            estoque_total,

        produtos_disponiveis=
            produtos_disponiveis,

        produtos_esgotados=
            produtos_esgotados,

        pedidos_pagos=
            pedidos_pagos,

        pedidos_processamento=
            pedidos_processamento,

        pedidos_preparacao=
            pedidos_preparacao,

        pedidos_prontos=
            pedidos_prontos,

        pedidos_entregues=
            pedidos_entregues,

        pedidos_cancelados=
            pedidos_cancelados,

        faturamento=
            faturamento,

        valor_cancelado=
            valor_cancelado,

        valor_entregue=
            valor_entregue,

        admin_email=
            session.get(
                "admin_email",
                ADMIN_EMAIL
            )
    )


# =========================================================
# SAIR DO ADMIN
# =========================================================

@app.route("/admin-logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# ADICIONAR PRODUTO
#
# Endpoint EXATO usado pelo admin.html:
# admin_adicionar_produto
# =========================================================

@app.route(
    "/admin/produto/adicionar",
    methods=["POST"]
)
@app.route(
    "/admin/cardapio/adicionar",
    methods=["POST"]
)
def admin_adicionar_produto():

    if not admin_logado():

        return redirect(
            url_for("login")
        )


    nome = request.form.get(
        "nome",
        ""
    ).strip()


    descricao = request.form.get(
        "descricao",
        ""
    ).strip()


    preco = numero(
        request.form.get("preco"),
        0
    )


    estoque_inicial = inteiro(
        request.form.get("estoque"),
        0
    )


    if estoque_inicial < 0:
        estoque_inicial = 0


    arquivo = request.files.get(
        "imagem"
    )


    imagem = preparar_imagem(
        arquivo
    )


    if not nome:

        flash(
            "Digite o nome do produto.",
            "erro"
        )

        return redirect(
            url_for("admin")
        )


    banco = conectar()


    try:

        banco.execute(
            """
            INSERT INTO produtos (
                nome,
                descricao,
                preco,
                imagem,
                estoque
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                nome,
                descricao,
                preco,
                imagem,
                estoque_inicial
            )
        )


        banco.commit()


        if imagem and arquivo:

            arquivo.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    imagem
                )
            )


        flash(
            "Produto adicionado com sucesso.",
            "sucesso"
        )


    except sqlite3.Error as erro:

        banco.rollback()

        print(
            "ERRO AO ADICIONAR PRODUTO:",
            repr(erro)
        )

        flash(
            "Erro ao adicionar produto.",
            "erro"
        )


    finally:

        banco.close()


    return redirect(
        url_for("admin")
    )


# =========================================================
# EDITAR PRODUTO
# =========================================================

@app.route(
    "/admin/produto/editar/<int:produto_id>",
    methods=["POST"]
)
@app.route(
    "/admin/cardapio/editar/<int:produto_id>",
    methods=["POST"]
)
def admin_editar_produto(produto_id):

    if not admin_logado():

        return redirect(
            url_for("login")
        )


    nome = request.form.get(
        "nome",
        ""
    ).strip()


    descricao = request.form.get(
        "descricao",
        ""
    ).strip()


    preco = numero(
        request.form.get("preco"),
        0
    )


    estoque_novo = inteiro(
        request.form.get("estoque"),
        0
    )


    if estoque_novo < 0:
        estoque_novo = 0


    arquivo = request.files.get(
        "imagem"
    )


    nova_imagem = preparar_imagem(
        arquivo
    )


    banco = conectar()


    imagem_antiga = ""


    try:

        produto = banco.execute(
            """
            SELECT *
            FROM produtos

            WHERE id = ?

            LIMIT 1
            """,
            (produto_id,)
        ).fetchone()


        if produto is None:

            flash(
                "Produto não encontrado.",
                "erro"
            )

            return redirect(
                url_for("admin")
            )


        imagem_antiga = (
            produto["imagem"] or ""
        )


        imagem_final = (
            nova_imagem
            if nova_imagem
            else imagem_antiga
        )


        banco.execute(
            """
            UPDATE produtos

            SET
                nome = ?,
                descricao = ?,
                preco = ?,
                imagem = ?,
                estoque = ?

            WHERE id = ?
            """,
            (
                nome,
                descricao,
                preco,
                imagem_final,
                estoque_novo,
                produto_id
            )
        )


        banco.commit()


        if nova_imagem and arquivo:

            arquivo.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    nova_imagem
                )
            )


        # -------------------------------------------------
        # APAGAR IMAGEM ANTIGA
        # -------------------------------------------------

        if (
            nova_imagem
            and
            imagem_antiga
            and
            imagem_antiga != nova_imagem
        ):

            caminho_antigo = os.path.join(
                UPLOAD_FOLDER,
                imagem_antiga
            )


            if os.path.exists(
                caminho_antigo
            ):

                try:
                    os.remove(
                        caminho_antigo
                    )

                except OSError:
                    pass


        flash(
            "Produto atualizado com sucesso.",
            "sucesso"
        )


    except sqlite3.Error as erro:

        banco.rollback()

        print(
            "ERRO AO EDITAR PRODUTO:",
            repr(erro)
        )

        flash(
            "Erro ao editar produto.",
            "erro"
        )


    finally:

        banco.close()


    return redirect(
        url_for("admin")
    )


# =========================================================
# ALTERAR ESTOQUE
# =========================================================

@app.route(
    "/admin/produto/estoque/<int:produto_id>",
    methods=["POST"]
)
def admin_alterar_estoque(produto_id):

    if not admin_logado():

        return redirect(
            url_for("login")
        )


    estoque_novo = inteiro(
        request.form.get(
            "estoque"
        ),
        0
    )


    if estoque_novo < 0:
        estoque_novo = 0


    banco = conectar()


    try:

        banco.execute(
            """
            UPDATE produtos

            SET estoque = ?

            WHERE id = ?
            """,
            (
                estoque_novo,
                produto_id
            )
        )


        banco.commit()


        flash(
            "Estoque atualizado.",
            "sucesso"
        )


    except sqlite3.Error as erro:

        banco.rollback()

        print(
            "ERRO AO ALTERAR ESTOQUE:",
            repr(erro)
        )

        flash(
            "Erro ao alterar estoque.",
            "erro"
        )


    finally:

        banco.close()


    return redirect(
        url_for("admin")
    )


# =========================================================
# EXCLUIR PRODUTO
# =========================================================

@app.route(
    "/admin/produto/excluir/<int:produto_id>",
    methods=["GET", "POST"]
)
def admin_excluir_produto(produto_id):

    if not admin_logado():

        return redirect(
            url_for("login")
        )


    banco = conectar()

    imagem = ""


    try:

        produto = banco.execute(
            """
            SELECT imagem
            FROM produtos

            WHERE id = ?
            """,
            (produto_id,)
        ).fetchone()


        if produto:

            imagem = produto["imagem"] or ""


        banco.execute(
            """
            DELETE FROM produtos

            WHERE id = ?
            """,
            (produto_id,)
        )


        banco.commit()


        flash(
            "Produto excluído.",
            "sucesso"
        )


    except sqlite3.Error as erro:

        banco.rollback()

        print(
            "ERRO AO EXCLUIR PRODUTO:",
            repr(erro)
        )

        flash(
            "Erro ao excluir produto.",
            "erro"
        )


    finally:

        banco.close()


    if imagem:

        caminho = os.path.join(
            UPLOAD_FOLDER,
            imagem
        )


        if os.path.exists(caminho):

            try:
                os.remove(caminho)

            except OSError:
                pass


    return redirect(
        url_for("admin")
    )


# =========================================================
# ALTERAR STATUS
# =========================================================

@app.route(
    "/admin/alterar-status/<int:pedido_id>",
    methods=["POST"]
)
def admin_alterar_status(pedido_id):

    if not admin_logado():

        return redirect(
            url_for("login")
        )


    novo_status = request.form.get(
        "status",
        ""
    ).strip()


    if novo_status not in STATUS_PERMITIDOS:

        flash(
            "Status inválido.",
            "erro"
        )

        return redirect(
            url_for("admin")
        )


    banco = conectar()


    try:

        banco.execute(
            """
            UPDATE pedidos

            SET status = ?

            WHERE id = ?
            """,
            (
                novo_status,
                pedido_id
            )
        )


        banco.commit()


        flash(
            "Status do pedido atualizado.",
            "sucesso"
        )


    except sqlite3.Error as erro:

        banco.rollback()

        print(
            "ERRO AO ALTERAR STATUS:",
            repr(erro)
        )

        flash(
            "Erro ao alterar status.",
            "erro"
        )


    finally:

        banco.close()


    return redirect(
        url_for("admin")
    )


# =========================================================
# ARQUIVAR PEDIDO
#
# Endpoint EXATO usado pelo admin.html:
# admin_arquivar_pedido
# =========================================================

@app.route(
    "/admin/arquivar-pedido/<int:pedido_id>",
    methods=["GET", "POST"]
)
def admin_arquivar_pedido(pedido_id):

    if not admin_logado():

        return redirect(
            url_for("login")
        )


    banco = conectar()


    try:

        banco.execute(
            """
            UPDATE pedidos

            SET arquivado = 1

            WHERE id = ?
            """,
            (pedido_id,)
        )


        banco.commit()


        flash(
            "Pedido arquivado com sucesso.",
            "sucesso"
        )


    except sqlite3.Error as erro:

        banco.rollback()

        print(
            "ERRO AO ARQUIVAR PEDIDO:",
            repr(erro)
        )

        flash(
            "Erro ao arquivar pedido.",
            "erro"
        )


    finally:

        banco.close()


    return redirect(
        url_for("admin")
    )


# =========================================================
# PEDIDOS ARQUIVADOS
#
# Endpoint EXATO:
# admin_pedidos_arquivados
# =========================================================

@app.route(
    "/admin/pedidos-arquivados"
)
def admin_pedidos_arquivados():

    if not admin_logado():

        return redirect(
            url_for("login")
        )


    banco = conectar()


    try:

        pedidos = banco.execute(
            """
            SELECT *
            FROM pedidos

            WHERE COALESCE(
                arquivado,
                0
            ) = 1

            ORDER BY id DESC
            """
        ).fetchall()


    except sqlite3.Error as erro:

        print(
            "ERRO AO BUSCAR PEDIDOS ARQUIVADOS:",
            repr(erro)
        )

        pedidos = []


    finally:

        banco.close()


    # -----------------------------------------------------
    # Se você já tiver pedidos_arquivados.html,
    # usa o seu arquivo.
    #
    # Se não tiver, não dá erro:
    # o Flask mostra uma página própria.
    # -----------------------------------------------------

    caminho_template = os.path.join(
        BASE_DIR,
        "templates",
        "pedidos_arquivados.html"
    )


    if os.path.exists(
        caminho_template
    ):

        return render_template(
            "pedidos_arquivados.html",
            pedidos=pedidos
        )


    return render_template_string(
        """
        <!DOCTYPE html>

        <html lang="pt-BR">

        <head>

            <meta charset="UTF-8">

            <meta
                name="viewport"
                content="width=device-width, initial-scale=1.0"
            >

            <title>Pedidos arquivados - DevJuan</title>

            <style>

                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }

                body {
                    font-family: Arial, Helvetica, sans-serif;
                    background: #f4f5f7;
                    color: #222;
                    padding: 30px;
                }

                .topo {
                    max-width: 1000px;
                    margin: 0 auto 25px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 15px;
                }

                h1 {
                    font-size: 28px;
                }

                .voltar {
                    text-decoration: none;
                    background: #111827;
                    color: white;
                    padding: 12px 18px;
                    border-radius: 9px;
                    font-weight: bold;
                }

                .container {
                    max-width: 1000px;
                    margin: auto;
                }

                .pedido {
                    background: white;
                    border-radius: 15px;
                    padding: 22px;
                    margin-bottom: 18px;
                    box-shadow: 0 3px 14px rgba(0,0,0,0.07);
                }

                .pedido-topo {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 18px;
                    gap: 15px;
                }

                .pedido-id {
                    font-size: 20px;
                    font-weight: bold;
                }

                .status {
                    background: #e5e7eb;
                    padding: 7px 12px;
                    border-radius: 20px;
                    font-size: 13px;
                    font-weight: bold;
                }

                .info {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                    margin-bottom: 18px;
                }

                .box {
                    background: #f9fafb;
                    padding: 12px;
                    border-radius: 9px;
                }

                .itens {
                    background: #f9fafb;
                    border-radius: 10px;
                    padding: 15px;
                    margin-bottom: 15px;
                }

                .item {
                    display: flex;
                    justify-content: space-between;
                    gap: 15px;
                    padding: 8px 0;
                    border-bottom: 1px solid #e5e7eb;
                }

                .item:last-child {
                    border-bottom: none;
                }

                .total {
                    font-size: 20px;
                    font-weight: bold;
                    margin-bottom: 15px;
                }

                .restaurar {
                    border: none;
                    background: #059669;
                    color: white;
                    padding: 11px 16px;
                    border-radius: 9px;
                    font-weight: bold;
                    cursor: pointer;
                }

                .vazio {
                    background: white;
                    padding: 30px;
                    border-radius: 15px;
                    text-align: center;
                }

                @media (max-width: 700px) {

                    body {
                        padding: 15px;
                    }

                    .topo {
                        flex-direction: column;
                        align-items: flex-start;
                    }

                    .info {
                        grid-template-columns: 1fr;
                    }

                    .pedido-topo {
                        flex-direction: column;
                        align-items: flex-start;
                    }

                }

            </style>

        </head>

        <body>

            <div class="topo">

                <h1>
                    🗄️ Pedidos arquivados
                </h1>

                <a
                    href="{{ url_for('admin') }}"
                    class="voltar"
                >
                    ← Voltar ao painel
                </a>

            </div>


            <div class="container">

                {% if pedidos %}

                    {% for pedido in pedidos %}

                        <div class="pedido">

                            <div class="pedido-topo">

                                <div class="pedido-id">
                                    Pedido #{{ pedido["id"] }}
                                </div>

                                <div class="status">
                                    {{ pedido["status"] }}
                                </div>

                            </div>


                            <div class="info">

                                <div class="box">

                                    <strong>
                                        Cliente:
                                    </strong>

                                    {{ pedido["cliente"] }}

                                </div>


                                <div class="box">

                                    <strong>
                                        Pagamento:
                                    </strong>

                                    {{ pedido["pagamento"] }}

                                </div>


                                <div class="box">

                                    <strong>
                                        Entrega:
                                    </strong>

                                    {{ pedido["entrega"] or "Retirada no local" }}

                                </div>


                                <div class="box">

                                    <strong>
                                        Endereço:
                                    </strong>

                                    {{ pedido["endereco"] or "Retirada no local" }}

                                </div>

                            </div>


                            <div class="itens">

                                <strong>
                                    Itens
                                </strong>

                                {% set itens = pedido["itens"]|from_json %}

                                {% if itens %}

                                    {% for item in itens %}

                                        <div class="item">

                                            <span>

                                                {{ item.get("quantidade", 1) }}x

                                                {{ item.get("nome", "Produto") }}

                                            </span>


                                            <span>

                                                R$

                                                {{
                                                    "%.2f"|format(
                                                        item.get("subtotal", 0)
                                                    )|replace(".", ",")
                                                }}

                                            </span>

                                        </div>

                                    {% endfor %}

                                {% else %}

                                    <div class="item">

                                        <span>
                                            Nenhum item encontrado.
                                        </span>

                                    </div>

                                {% endif %}

                            </div>


                            <div class="total">

                                Total:

                                R$

                                {{
                                    "%.2f"|format(
                                        pedido["total"] or 0
                                    )|replace(".", ",")
                                }}

                            </div>


                            <form
                                method="POST"
                                action="{{
                                    url_for(
                                        'admin_restaurar_pedido',
                                        pedido_id=pedido['id']
                                    )
                                }}"
                            >

                                <button
                                    type="submit"
                                    class="restaurar"
                                >
                                    Restaurar pedido
                                </button>

                            </form>

                        </div>

                    {% endfor %}

                {% else %}

                    <div class="vazio">

                        <h2>
                            Nenhum pedido arquivado
                        </h2>

                        <p style="margin-top:10px;">
                            Quando você arquivar um pedido,
                            ele aparecerá aqui.
                        </p>

                    </div>

                {% endif %}

            </div>

        </body>

        </html>
        """,
        pedidos=pedidos
    )


# =========================================================
# RESTAURAR PEDIDO
# =========================================================

@app.route(
    "/admin/restaurar-pedido/<int:pedido_id>",
    methods=["GET", "POST"]
)
def admin_restaurar_pedido(pedido_id):

    if not admin_logado():

        return redirect(
            url_for("login")
        )


    banco = conectar()


    try:

        banco.execute(
            """
            UPDATE pedidos

            SET arquivado = 0

            WHERE id = ?
            """,
            (pedido_id,)
        )


        banco.commit()


        flash(
            "Pedido restaurado com sucesso.",
            "sucesso"
        )


    except sqlite3.Error as erro:

        banco.rollback()

        print(
            "ERRO AO RESTAURAR PEDIDO:",
            repr(erro)
        )

        flash(
            "Erro ao restaurar pedido.",
            "erro"
        )


    finally:

        banco.close()


    return redirect(
        url_for(
            "admin_pedidos_arquivados"
        )
    )


# =========================================================
# DEBUG CLIENTES
# =========================================================

@app.route("/debug-clientes")
def debug_clientes():

    if not admin_logado():

        return jsonify(
            erro="Acesso negado"
        ), 403


    banco = conectar()


    try:

        clientes = banco.execute(
            """
            SELECT *
            FROM clientes
            ORDER BY id DESC
            """
        ).fetchall()


        return jsonify(
            [
                dict(cliente)
                for cliente in clientes
            ]
        )


    finally:

        banco.close()


# =========================================================
# DEBUG PEDIDOS
# =========================================================

@app.route("/debug-pedidos")
def debug_pedidos():

    if not admin_logado():

        return jsonify(
            erro="Acesso negado"
        ), 403


    banco = conectar()


    try:

        pedidos = banco.execute(
            """
            SELECT *
            FROM pedidos
            ORDER BY id DESC
            """
        ).fetchall()


        return jsonify(
            [
                dict(pedido)
                for pedido in pedidos
            ]
        )


    finally:

        banco.close()


# =========================================================
# ERRO DE ARQUIVO GRANDE
# =========================================================

@app.errorhandler(413)
def arquivo_grande(erro):

    return jsonify(
        sucesso=False,
        erro="Arquivo muito grande. Limite: 16 MB."
    ), 413


# =========================================================
# EXECUTAR
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("DEVJUAN LANCHES")
    print("Servidor iniciado")
    print("Banco:", CAMINHO_BANCO)
    print("Admin:", ADMIN_EMAIL)
    print("=" * 60)

    app.run(
        debug=True
    )