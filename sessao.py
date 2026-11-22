from typing import Literal

TipoPerfil = Literal["Candidato", "Recrutador"]
PERFIS_VALIDOS: set[str] = {"Candidato", "Recrutador"}


class Sessao:
    """Gerenciador global de estado do usuário autenticado na aplicação."""

    usuario_id: int | None = None
    nome: str | None = None
    tipo_perfil: TipoPerfil | None = None

    @classmethod
    def login(cls, usuario_id: int, nome: str, tipo_perfil: TipoPerfil) -> None:
        if tipo_perfil not in PERFIS_VALIDOS:
            raise ValueError(f"Tipo de perfil inválido: {tipo_perfil!r}.")
        cls.usuario_id = usuario_id
        cls.nome = nome
        cls.tipo_perfil = tipo_perfil

    @classmethod
    def logout(cls) -> None:
        cls.usuario_id = None
        cls.nome = None
        cls.tipo_perfil = None

    @classmethod
    def esta_logado(cls) -> bool:
        return cls.usuario_id is not None
