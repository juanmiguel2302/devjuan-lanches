import sqlite3
import os

CAMINHO_BANCO = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "lanchonete.db")
)

print("Banco encontrado em:")
print(CAMINHO_BANCO)

banco = sqlite3.connect(CAMINHO_BANCO)

# =========================================================
# CRIA A TABELA PEDIDOS SE ELA NÃO EXISTIR
# =========================================================

banco.execute("""
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT,
    itens TEXT,
    total REAL,
    pagamento TEXT,
    status TEXT,
    entrega TEXT DEFAULT 'Retirada no local',
    endereco TEXT DEFAULT '',
    arquivado INTEGER NOT NULL DEFAULT 0
)
""")

# =========================================================
# DESCOBRE AS COLUNAS QUE JÁ EXISTEM
# =========================================================

colunas = {
    coluna[1]
    for coluna in banco.execute("PRAGMA table_info(pedidos)").fetchall()
}

print("\nColunas atuais:")
print(colunas)

# =========================================================
# ADICIONA SOMENTE O QUE ESTIVER FALTANDO
# =========================================================

if "cliente" not in colunas:
    banco.execute("ALTER TABLE pedidos ADD COLUMN cliente TEXT")
    print("OK: coluna cliente adicionada.")

if "itens" not in colunas:
    banco.execute("ALTER TABLE pedidos ADD COLUMN itens TEXT")
    print("OK: coluna itens adicionada.")

if "total" not in colunas:
    banco.execute("ALTER TABLE pedidos ADD COLUMN total REAL")
    print("OK: coluna total adicionada.")

if "pagamento" not in colunas:
    banco.execute("ALTER TABLE pedidos ADD COLUMN pagamento TEXT")
    print("OK: coluna pagamento adicionada.")

if "status" not in colunas:
    banco.execute("ALTER TABLE pedidos ADD COLUMN status TEXT")
    print("OK: coluna status adicionada.")

if "entrega" not in colunas:
    banco.execute("""
        ALTER TABLE pedidos
        ADD COLUMN entrega TEXT DEFAULT 'Retirada no local'
    """)
    print("OK: coluna entrega adicionada.")

if "endereco" not in colunas:
    banco.execute("""
        ALTER TABLE pedidos
        ADD COLUMN endereco TEXT DEFAULT ''
    """)
    print("OK: coluna endereco adicionada.")

if "arquivado" not in colunas:
    banco.execute("""
        ALTER TABLE pedidos
        ADD COLUMN arquivado INTEGER NOT NULL DEFAULT 0
    """)
    print("OK: coluna arquivado adicionada.")

# =========================================================
# SALVA
# =========================================================

banco.commit()

print("\n========================================")
print("BANCO CORRIGIDO COM SUCESSO!")
print("========================================")

# Mostra a estrutura final
print("\nEstrutura final da tabela pedidos:")

estrutura = banco.execute(
    "PRAGMA table_info(pedidos)"
).fetchall()

for coluna in estrutura:
    print("-", coluna[1])

banco.close()