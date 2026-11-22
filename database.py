from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator

DB_PATH: Path = Path(__file__).resolve().parent / "recrutamento.db"

SCHEMA_SQL: str = """
-- Tabela de Usuários (UC01, UC02)
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    tipo_perfil TEXT NOT NULL CHECK(tipo_perfil IN ('Candidato', 'Recrutador'))
);

-- Perfil Acadêmico do Candidato (UC03)
CREATE TABLE IF NOT EXISTS perfis_academicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER UNIQUE NOT NULL,
    curso TEXT NOT NULL,
    instituicao TEXT NOT NULL,
    periodo TEXT NOT NULL,
    habilidades TEXT,
    resumo TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

-- Tabela de Vagas (UC07, UC04, UC10)
CREATE TABLE IF NOT EXISTS vagas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recrutador_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    localidade TEXT NOT NULL,
    bolsa_auxilio REAL NOT NULL,
    requisitos TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Ativa',
    FOREIGN KEY (recrutador_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

-- Tabela de Inscrições (UC05, UC06, UC08, UC09) - Impede duplicidade (R13)
CREATE TABLE IF NOT EXISTS inscricoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidato_id INTEGER NOT NULL,
    vaga_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Em Análise',
    data_inscricao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidato_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    FOREIGN KEY (vaga_id) REFERENCES vagas (id) ON DELETE CASCADE,
    UNIQUE(candidato_id, vaga_id)
);
"""


@contextmanager
def obter_conexao(caminho_db: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    """Gerencia o ciclo de vida da conexão SQLite com suporte transacional e Foreign Keys ativas."""
    conexao = sqlite3.connect(caminho_db)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def inicializar_banco(caminho_db: Path = DB_PATH) -> None:
    """Executa a criação das tabelas caso ainda não existam."""
    with obter_conexao(caminho_db) as conexao:
        conexao.executescript(SCHEMA_SQL)


inicializar_banco()
