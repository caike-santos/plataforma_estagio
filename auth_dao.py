import hashlib
import sqlite3
from typing import Any, cast

from database import obter_conexao
from sessao import PERFIS_VALIDOS, Sessao, TipoPerfil


class CredenciaisInvalidasError(Exception):
    """Lançada quando o e-mail ou a senha informados não conferem."""


class EmailJaCadastradoError(Exception):
    """Lançada quando há tentativa de cadastro com um e-mail já existente (Regra R2)."""


def gerar_hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


class AuthDAO:
    """Camada de acesso a dados e regras de negócio para autenticação e cadastro (UC01 e UC02)."""

    @staticmethod
    def autenticar(email: str, senha: str) -> dict[str, Any]:
        email_limpo = email.strip().lower()
        if not email_limpo or not senha:
            raise CredenciaisInvalidasError("Informe o e-mail e a senha para entrar.")

        senha_hash = gerar_hash_senha(senha)

        with obter_conexao() as conexao:
            cursor = conexao.execute(
                """
                SELECT id, nome, email, tipo_perfil
                FROM usuarios
                WHERE LOWER(email) = ? AND senha = ?
                """,
                (email_limpo, senha_hash),
            )
            registro = cursor.fetchone()

        if registro is None:
            raise CredenciaisInvalidasError("E-mail ou senha inválidos.")

        usuario = dict(registro)
        Sessao.login(
            usuario_id=int(usuario["id"]),
            nome=str(usuario["nome"]),
            tipo_perfil=cast(TipoPerfil, usuario["tipo_perfil"]),
        )
        return usuario

    @staticmethod
    def cadastrar_usuario(
        nome: str,
        email: str,
        senha: str,
        tipo_perfil: str,
    ) -> int:
        nome_limpo = nome.strip()
        email_limpo = email.strip().lower()
        perfil_limpo = tipo_perfil.strip()

        if not nome_limpo or not email_limpo or not senha or not perfil_limpo:
            raise ValueError("Todos os campos são obrigatórios.")

        if "@" not in email_limpo or "." not in email_limpo.split("@")[-1]:
            raise ValueError("Informe um endereço de e-mail válido.")

        if perfil_limpo not in PERFIS_VALIDOS:
            raise ValueError("O tipo de perfil deve ser 'Candidato' ou 'Recrutador'.")

        senha_hash = gerar_hash_senha(senha)

        try:
            with obter_conexao() as conexao:
                cursor = conexao.execute(
                    """
                    INSERT INTO usuarios (nome, email, senha, tipo_perfil)
                    VALUES (?, ?, ?, ?)
                    """,
                    (nome_limpo, email_limpo, senha_hash, perfil_limpo),
                )
                return int(cursor.lastrowid or 0)
        except sqlite3.IntegrityError as erro:
            raise EmailJaCadastradoError(
                f"O e-mail '{email_limpo}' já está cadastrado no sistema."
            ) from erro


autenticar = AuthDAO.autenticar
cadastrar_usuario = AuthDAO.cadastrar_usuario
