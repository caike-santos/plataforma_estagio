import sqlite3
from utils import DB_NAME, STATUS_VAGA_ATIVA

try:
    from database import obter_conexao
except ImportError:
    def obter_conexao():
        conn = sqlite3.connect(DB_NAME)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def cadastrar_vaga(
    recrutador_id: int,
    titulo: str,
    descricao: str,
    localidade: str,
    bolsa: float,
    requisitos: str
) -> bool:
    sql = """
        INSERT INTO vagas (recrutador_id, titulo, descricao, localidade, bolsa_auxilio, requisitos, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    try:
        with obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                recrutador_id,
                titulo.strip(),
                descricao.strip(),
                localidade.strip(),
                float(bolsa),
                requisitos.strip(),
                STATUS_VAGA_ATIVA
            ))
            conn.commit()
            return True
    except sqlite3.Error as erro:
        print(f"[ERRO SQL - cadastrar_vaga]: {erro}")
        return False


def listar_vagas_recrutador(recrutador_id: int) -> list[dict]:
    sql = """
        SELECT id, recrutador_id, titulo, descricao, localidade, bolsa_auxilio, requisitos, status
        FROM vagas
        WHERE recrutador_id = ?
        ORDER BY id DESC
    """
    try:
        with obter_conexao() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, (recrutador_id,))
            registros = cursor.fetchall()
            return [dict(linha) for linha in registros]
    except sqlite3.Error as erro:
        print(f"[ERRO SQL - listar_vagas_recrutador]: {erro}")
        return []


def listar_candidatos_da_vaga(vaga_id: int) -> list[dict]:
    sql = """
        SELECT 
            i.id AS inscricao_id,
            i.candidato_id,
            i.vaga_id,
            i.status,
            i.data_inscricao,
            u.nome,
            u.email,
            COALESCE(p.curso, 'Não informado') AS curso,
            COALESCE(p.instituicao, 'Não informada') AS instituicao,
            COALESCE(p.periodo, 'Não informado') AS periodo,
            COALESCE(p.habilidades, 'Não informadas') AS habilidades,
            COALESCE(p.resumo, 'Sem resumo cadastrado.') AS resumo
        FROM inscricoes i
        INNER JOIN usuarios u ON i.candidato_id = u.id
        LEFT JOIN perfis_academicos p ON u.id = p.usuario_id
        WHERE i.vaga_id = ?
        ORDER BY i.data_inscricao DESC
    """
    try:
        with obter_conexao() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, (vaga_id,))
            registros = cursor.fetchall()
            return [dict(linha) for linha in registros]
    except sqlite3.Error as erro:
        print(f"[ERRO SQL - listar_candidatos_da_vaga]: {erro}")
        return []


def atualizar_status_candidatura(inscricao_id: int, novo_status: str) -> bool:
    sql = """
        UPDATE inscricoes
        SET status = ?
        WHERE id = ?
    """
    try:
        with obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (novo_status, inscricao_id))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as erro:
        print(f"[ERRO SQL - atualizar_status_candidatura]: {erro}")
        return False

def atualizar_vaga(
    vaga_id: int,
    recrutador_id: int,
    titulo: str,
    descricao: str,
    localidade: str,
    bolsa: float,
    requisitos: str,
    status: str = STATUS_VAGA_ATIVA
) -> bool:

    sql = """
        UPDATE vagas
        SET titulo = ?, descricao = ?, localidade = ?, bolsa_auxilio = ?, requisitos = ?, status = ?
        WHERE id = ? AND recrutador_id = ?
    """
    try:
        with obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                titulo.strip(),
                descricao.strip(),
                localidade.strip(),
                float(bolsa),
                requisitos.strip(),
                status,
                vaga_id,
                recrutador_id
            ))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as erro:
        print(f"[ERRO SQL - atualizar_vaga]: {erro}")
        return False


def excluir_vaga(vaga_id: int, recrutador_id: int) -> bool:
    sql = "DELETE FROM vagas WHERE id = ? AND recrutador_id = ?"
    try:
        with obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (vaga_id, recrutador_id))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as erro:
        print(f"[ERRO SQL - excluir_vaga]: {erro}")
        return False


def obter_vaga_por_id(vaga_id: int) -> dict | None:
    sql = """
        SELECT id, recrutador_id, titulo, descricao, localidade, bolsa_auxilio, requisitos, status
        FROM vagas
        WHERE id = ?
    """
    try:
        with obter_conexao() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, (vaga_id,))
            linha = cursor.fetchone()
            return dict(linha) if linha else None
    except sqlite3.Error as erro:
        print(f"[ERRO SQL - obter_vaga_por_id]: {erro}")
        return None


class RecrutadorDAO:
    cadastrar_vaga = staticmethod(cadastrar_vaga)
    listar_vagas_recrutador = staticmethod(listar_vagas_recrutador)
    listar_candidatos_da_vaga = staticmethod(listar_candidatos_da_vaga)
    atualizar_status_candidatura = staticmethod(atualizar_status_candidatura)
    atualizar_vaga = staticmethod(atualizar_vaga)
    excluir_vaga = staticmethod(excluir_vaga)
    obter_vaga_por_id = staticmethod(obter_vaga_por_id)