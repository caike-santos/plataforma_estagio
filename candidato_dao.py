import sqlite3
from typing import Any

from database import obter_conexao


class InscricaoDuplicadaError(Exception):
    """Lançada quando o candidato tenta se inscrever novamente na mesma vaga (Regra R13)."""


class CandidatoDAO:
    """Camada de acesso a dados e regras de negócio para as funcionalidades do Candidato."""

    @staticmethod
    def buscar_perfil(usuario_id: int) -> dict[str, Any] | None:
        with obter_conexao() as conexao:
            cursor = conexao.execute(
                """
                SELECT id, usuario_id, curso, instituicao, periodo, habilidades, resumo
                FROM perfis_academicos
                WHERE usuario_id = ?
                """,
                (usuario_id,),
            )
            registro = cursor.fetchone()
            return dict(registro) if registro else None

    @staticmethod
    def salvar_perfil(
        usuario_id: int,
        curso: str,
        instituicao: str,
        periodo: str,
        habilidades: str = "",
        resumo: str = "",
    ) -> int:
        curso_limpo = curso.strip()
        instituicao_limpa = instituicao.strip()
        periodo_limpo = periodo.strip()
        habilidades_limpas = habilidades.strip()
        resumo_limpo = resumo.strip()

        if not curso_limpo or not instituicao_limpa or not periodo_limpo:
            raise ValueError(
                "Os campos Curso, Instituição e Período são obrigatórios."
            )

        with obter_conexao() as conexao:
            conexao.execute(
                """
                INSERT INTO perfis_academicos (
                    usuario_id, curso, instituicao, periodo, habilidades, resumo
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(usuario_id) DO UPDATE SET
                    curso = excluded.curso,
                    instituicao = excluded.instituicao,
                    periodo = excluded.periodo,
                    habilidades = excluded.habilidades,
                    resumo = excluded.resumo
                """,
                (
                    usuario_id,
                    curso_limpo,
                    instituicao_limpa,
                    periodo_limpo,
                    habilidades_limpas,
                    resumo_limpo,
                ),
            )
            cursor = conexao.execute(
                "SELECT id FROM perfis_academicos WHERE usuario_id = ?",
                (usuario_id,),
            )
            registro = cursor.fetchone()
            return int(registro["id"]) if registro else 0

    @staticmethod
    def excluir_perfil(usuario_id: int) -> bool:
        with obter_conexao() as conexao:
            cursor = conexao.execute(
                "DELETE FROM perfis_academicos WHERE usuario_id = ?",
                (usuario_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def listar_vagas_ativas(filtro_localidade: str = "") -> list[dict[str, Any]]:
        filtro_limpo = filtro_localidade.strip()

        with obter_conexao() as conexao:
            if filtro_limpo:
                cursor = conexao.execute(
                    """
                    SELECT id, recrutador_id, titulo, descricao, localidade,
                           bolsa_auxilio, requisitos, status
                    FROM vagas
                    WHERE localidade LIKE ? AND status = 'Ativa'
                    ORDER BY id DESC
                    """,
                    (f"%{filtro_limpo}%",),
                )
            else:
                cursor = conexao.execute(
                    """
                    SELECT id, recrutador_id, titulo, descricao, localidade,
                           bolsa_auxilio, requisitos, status
                    FROM vagas
                    WHERE status = 'Ativa'
                    ORDER BY id DESC
                    """
                )
            return [dict(linha) for linha in cursor.fetchall()]

    @staticmethod
    def inscrever_candidato(candidato_id: int, vaga_id: int) -> int:
        try:
            with obter_conexao() as conexao:
                cursor = conexao.execute(
                    """
                    INSERT INTO inscricoes (candidato_id, vaga_id)
                    VALUES (?, ?)
                    """,
                    (candidato_id, vaga_id),
                )
                return int(cursor.lastrowid or 0)
        except sqlite3.IntegrityError as erro:
            raise InscricaoDuplicadaError(
                "Você já possui uma inscrição ativa para esta vaga."
            ) from erro

    @staticmethod
    def listar_candidaturas(candidato_id: int) -> list[dict[str, Any]]:
        with obter_conexao() as conexao:
            cursor = conexao.execute(
                """
                SELECT
                    i.id,
                    i.vaga_id,
                    v.titulo,
                    v.localidade,
                    v.bolsa_auxilio,
                    i.data_inscricao,
                    i.status
                FROM inscricoes i
                INNER JOIN vagas v ON v.id = i.vaga_id
                WHERE i.candidato_id = ?
                ORDER BY i.data_inscricao DESC, i.id DESC
                """,
                (candidato_id,),
            )
            return [dict(linha) for linha in cursor.fetchall()]


buscar_perfil = CandidatoDAO.buscar_perfil
salvar_perfil = CandidatoDAO.salvar_perfil
excluir_perfil = CandidatoDAO.excluir_perfil
listar_vagas_ativas = CandidatoDAO.listar_vagas_ativas
inscrever_candidato = CandidatoDAO.inscrever_candidato
listar_candidaturas = CandidatoDAO.listar_candidaturas
