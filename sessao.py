from typing import Any, Literal, cast

TipoPerfil = Literal["Candidato", "Recrutador"]
PERFIS_VALIDOS: set[str] = {"Candidato", "Recrutador"}


class Sessao:
    """Gerenciador global de estado do usuário autenticado na aplicação."""

    usuario_id: int | None = None
    nome: str | None = None
    tipo_perfil: TipoPerfil | None = None

    @classmethod
    def login(
        cls,
        usuario_id: int | dict[str, Any],
        nome: str | None = None,
        tipo_perfil: TipoPerfil | None = None,
    ) -> None:
        if isinstance(usuario_id, dict):
            dados = usuario_id
            uid = int(dados["id"])
            nome_val = str(dados["nome"])
            perfil_val = cast(TipoPerfil, dados["tipo_perfil"])
        else:
            if nome is None or tipo_perfil is None:
                raise ValueError("Os parâmetros 'nome' e 'tipo_perfil' são obrigatórios.")
            uid = int(usuario_id)
            nome_val = str(nome)
            perfil_val = tipo_perfil

        if perfil_val not in PERFIS_VALIDOS:
            raise ValueError(f"Tipo de perfil inválido: {perfil_val!r}.")
        cls.usuario_id = uid
        cls.nome = nome_val
        cls.tipo_perfil = perfil_val

    @classmethod
    def logout(cls) -> None:
        cls.usuario_id = None
        cls.nome = None
        cls.tipo_perfil = None

    @classmethod
    def esta_logado(cls) -> bool:
        return cls.usuario_id is not None
