import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

from dao.candidato_dao import CandidatoDAO, InscricaoDuplicadaError
from sessao import Sessao


def formatar_moeda(valor: float | int) -> str:
    return f"R$ {float(valor):.2f}"


class CandidatoView(ttk.Frame):
    """Painel principal do Candidato contendo Vagas, Candidaturas e Perfil Acadêmico."""

    def __init__(
        self,
        master: tk.Misc,
        on_logout: Callable[[], None] | None = None,
        controller: Any = None,
    ) -> None:
        super().__init__(master, padding=16)
        self.controller = controller
        self.on_logout = on_logout
        self._vagas_cache: dict[int, dict[str, Any]] = {}

        self._configurar_layout()
        self._construir_cabecalho()
        self._construir_aba_vagas()
        self._construir_aba_candidaturas()
        self._construir_aba_perfil()

        self._carregar_vagas()
        self._carregar_candidaturas()
        self._carregar_perfil()

    def _configurar_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.frame_topo = ttk.Frame(self)
        self.frame_topo.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.frame_topo.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self.aba_vagas = ttk.Frame(self.notebook, padding=14)
        self.aba_candidaturas = ttk.Frame(self.notebook, padding=14)
        self.aba_perfil = ttk.Frame(self.notebook, padding=14)

        self.notebook.add(self.aba_vagas, text="  Vagas Disponíveis  ")
        self.notebook.add(self.aba_candidaturas, text="  Minhas Candidaturas  ")
        self.notebook.add(self.aba_perfil, text="  Meu Perfil Acadêmico  ")

    def _construir_cabecalho(self) -> None:
        nome_usuario = Sessao.nome or "Candidato"
        lbl_boas_vindas = ttk.Label(
            self.frame_topo,
            text=f"Painel do Candidato — Olá, {nome_usuario}",
            font=("Segoe UI", 13, "bold"),
        )
        lbl_boas_vindas.grid(row=0, column=0, sticky="w")

        btn_sair = ttk.Button(
            self.frame_topo,
            text="Sair",
            command=self._executar_logout,
        )
        btn_sair.grid(row=0, column=1, sticky="e")

    def _construir_aba_vagas(self) -> None:
        self.aba_vagas.columnconfigure(0, weight=1)
        self.aba_vagas.rowconfigure(1, weight=3)
        self.aba_vagas.rowconfigure(2, weight=2)

        frame_filtro = ttk.Frame(self.aba_vagas)
        frame_filtro.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        frame_filtro.columnconfigure(1, weight=1)

        ttk.Label(frame_filtro, text="Filtrar por Localidade:").grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )
        self.var_filtro_localidade = tk.StringVar()
        entry_filtro = ttk.Entry(
            frame_filtro, textvariable=self.var_filtro_localidade
        )
        entry_filtro.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        entry_filtro.bind("<Return>", lambda _: self._carregar_vagas())

        ttk.Button(
            frame_filtro,
            text="Filtrar",
            command=self._carregar_vagas,
        ).grid(row=0, column=2, padx=(0, 6))

        ttk.Button(
            frame_filtro,
            text="Limpar",
            command=self._limpar_filtro_vagas,
        ).grid(row=0, column=3)

        frame_tabela = ttk.Frame(self.aba_vagas)
        frame_tabela.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        frame_tabela.columnconfigure(0, weight=1)
        frame_tabela.rowconfigure(0, weight=1)

        colunas = ("id", "titulo", "localidade", "bolsa", "requisitos")
        self.tree_vagas = ttk.Treeview(
            frame_tabela,
            columns=colunas,
            show="headings",
            selectmode="browse",
            height=8,
        )
        self.tree_vagas.heading("id", text="ID")
        self.tree_vagas.heading("titulo", text="Título")
        self.tree_vagas.heading("localidade", text="Localidade")
        self.tree_vagas.heading("bolsa", text="Bolsa Auxílio")
        self.tree_vagas.heading("requisitos", text="Requisitos")

        self.tree_vagas.column("id", width=50, anchor="center", stretch=False)
        self.tree_vagas.column("titulo", width=200, anchor="w")
        self.tree_vagas.column("localidade", width=130, anchor="w")
        self.tree_vagas.column("bolsa", width=110, anchor="e", stretch=False)
        self.tree_vagas.column("requisitos", width=240, anchor="w")

        scroll_vagas = ttk.Scrollbar(
            frame_tabela, orient="vertical", command=self.tree_vagas.yview
        )
        self.tree_vagas.configure(yscrollcommand=scroll_vagas.set)

        self.tree_vagas.grid(row=0, column=0, sticky="nsew")
        scroll_vagas.grid(row=0, column=1, sticky="ns")
        self.tree_vagas.bind("<<TreeviewSelect>>", self._ao_selecionar_vaga)

        frame_detalhes = ttk.LabelFrame(
            self.aba_vagas, text="Descrição Completa da Vaga Selecionada", padding=10
        )
        frame_detalhes.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        frame_detalhes.columnconfigure(0, weight=1)
        frame_detalhes.rowconfigure(0, weight=1)

        self.txt_descricao_vaga = tk.Text(
            frame_detalhes, height=4, wrap="word", state="disabled"
        )
        self.txt_descricao_vaga.grid(row=0, column=0, sticky="nsew")

        frame_acoes_vaga = ttk.Frame(self.aba_vagas)
        frame_acoes_vaga.grid(row=3, column=0, sticky="ew")
        frame_acoes_vaga.columnconfigure(0, weight=1)

        ttk.Button(
            frame_acoes_vaga,
            text="Atualizar Lista",
            command=self._carregar_vagas,
        ).grid(row=0, column=0, sticky="w")

        ttk.Button(
            frame_acoes_vaga,
            text="Candidatar-se à Vaga Selecionada",
            command=self._processar_candidatura,
        ).grid(row=0, column=1, sticky="e")

    def _construir_aba_candidaturas(self) -> None:
        self.aba_candidaturas.columnconfigure(0, weight=1)
        self.aba_candidaturas.rowconfigure(0, weight=1)

        frame_tabela = ttk.Frame(self.aba_candidaturas)
        frame_tabela.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        frame_tabela.columnconfigure(0, weight=1)
        frame_tabela.rowconfigure(0, weight=1)

        colunas = ("id", "titulo", "localidade", "bolsa", "data", "status")
        self.tree_candidaturas = ttk.Treeview(
            frame_tabela,
            columns=colunas,
            show="headings",
            selectmode="browse",
        )
        self.tree_candidaturas.heading("id", text="Inscrição #")
        self.tree_candidaturas.heading("titulo", text="Título da Vaga")
        self.tree_candidaturas.heading("localidade", text="Localidade")
        self.tree_candidaturas.heading("bolsa", text="Bolsa Auxílio")
        self.tree_candidaturas.heading("data", text="Data de Inscrição")
        self.tree_candidaturas.heading("status", text="Status")

        self.tree_candidaturas.column("id", width=85, anchor="center", stretch=False)
        self.tree_candidaturas.column("titulo", width=220, anchor="w")
        self.tree_candidaturas.column("localidade", width=140, anchor="w")
        self.tree_candidaturas.column("bolsa", width=110, anchor="e", stretch=False)
        self.tree_candidaturas.column("data", width=150, anchor="center", stretch=False)
        self.tree_candidaturas.column("status", width=120, anchor="center", stretch=False)

        scroll_cand = ttk.Scrollbar(
            frame_tabela, orient="vertical", command=self.tree_candidaturas.yview
        )
        self.tree_candidaturas.configure(yscrollcommand=scroll_cand.set)

        self.tree_candidaturas.grid(row=0, column=0, sticky="nsew")
        scroll_cand.grid(row=0, column=1, sticky="ns")

        btn_atualizar = ttk.Button(
            self.aba_candidaturas,
            text="Atualizar Status",
            command=self._carregar_candidaturas,
        )
        btn_atualizar.grid(row=1, column=0, sticky="e")

    def _construir_aba_perfil(self) -> None:
        self.aba_perfil.columnconfigure(1, weight=1)
        self.aba_perfil.rowconfigure(4, weight=1)

        ttk.Label(self.aba_perfil, text="Curso *:").grid(
            row=0, column=0, sticky="w", pady=(0, 8), padx=(0, 10)
        )
        self.var_curso = tk.StringVar()
        ttk.Entry(self.aba_perfil, textvariable=self.var_curso).grid(
            row=0, column=1, sticky="ew", pady=(0, 8)
        )

        ttk.Label(self.aba_perfil, text="Instituição *:").grid(
            row=1, column=0, sticky="w", pady=(0, 8), padx=(0, 10)
        )
        self.var_instituicao = tk.StringVar()
        ttk.Entry(self.aba_perfil, textvariable=self.var_instituicao).grid(
            row=1, column=1, sticky="ew", pady=(0, 8)
        )

        ttk.Label(self.aba_perfil, text="Período / Semestre *:").grid(
            row=2, column=0, sticky="w", pady=(0, 8), padx=(0, 10)
        )
        self.var_periodo = tk.StringVar()
        ttk.Entry(self.aba_perfil, textvariable=self.var_periodo).grid(
            row=2, column=1, sticky="ew", pady=(0, 8)
        )

        ttk.Label(self.aba_perfil, text="Habilidades:").grid(
            row=3, column=0, sticky="w", pady=(0, 8), padx=(0, 10)
        )
        self.var_habilidades = tk.StringVar()
        ttk.Entry(self.aba_perfil, textvariable=self.var_habilidades).grid(
            row=3, column=1, sticky="ew", pady=(0, 8)
        )

        ttk.Label(self.aba_perfil, text="Resumo Profissional:").grid(
            row=4, column=0, sticky="nw", pady=(0, 8), padx=(0, 10)
        )
        self.txt_resumo = tk.Text(self.aba_perfil, height=6, wrap="word")
        self.txt_resumo.grid(row=4, column=1, sticky="nsew", pady=(0, 12))

        frame_botoes = ttk.Frame(self.aba_perfil)
        frame_botoes.grid(row=5, column=0, columnspan=2, sticky="e")

        ttk.Button(
            frame_botoes,
            text="Excluir Perfil",
            command=self._excluir_perfil,
        ).grid(row=0, column=0, padx=(0, 8))

        ttk.Button(
            frame_botoes,
            text="Salvar Perfil",
            command=self._salvar_perfil,
        ).grid(row=0, column=1)

    def _limpar_filtro_vagas(self) -> None:
        self.var_filtro_localidade.set("")
        self._carregar_vagas()

    def _carregar_vagas(self) -> None:
        for item in self.tree_vagas.get_children():
            self.tree_vagas.delete(item)

        self._vagas_cache.clear()
        self._atualizar_texto_descricao("")

        filtro = self.var_filtro_localidade.get()
        vagas = CandidatoDAO.listar_vagas_ativas(filtro_localidade=filtro)

        for vaga in vagas:
            vaga_id = int(vaga["id"])
            self._vagas_cache[vaga_id] = vaga
            self.tree_vagas.insert(
                "",
                "end",
                iid=str(vaga_id),
                values=(
                    vaga_id,
                    vaga["titulo"],
                    vaga["localidade"],
                    formatar_moeda(vaga["bolsa_auxilio"]),
                    vaga["requisitos"],
                ),
            )

    def _ao_selecionar_vaga(self, _evento: tk.Event) -> None:  # type: ignore[type-arg]
        selecao = self.tree_vagas.selection()
        if not selecao:
            self._atualizar_texto_descricao("")
            return

        vaga_id = int(selecao[0])
        vaga = self._vagas_cache.get(vaga_id)
        if not vaga:
            self._atualizar_texto_descricao("")
            return

        detalhes = (
            f"Título: {vaga['titulo']}  |  Localidade: {vaga['localidade']}  |  "
            f"Bolsa: {formatar_moeda(vaga['bolsa_auxilio'])}\n"
            f"Requisitos: {vaga['requisitos']}\n\n"
            f"Descrição:\n{vaga['descricao']}"
        )
        self._atualizar_texto_descricao(detalhes)

    def _atualizar_texto_descricao(self, conteudo: str) -> None:
        self.txt_descricao_vaga.configure(state="normal")
        self.txt_descricao_vaga.delete("1.0", "end")
        self.txt_descricao_vaga.insert("1.0", conteudo)
        self.txt_descricao_vaga.configure(state="disabled")

    def _processar_candidatura(self) -> None:
        if Sessao.usuario_id is None:
            messagebox.showerror("Sessão expirada", "Faça login novamente.", parent=self)
            return

        selecao = self.tree_vagas.selection()
        if not selecao:
            messagebox.showwarning(
                "Selecione uma vaga",
                "Selecione uma vaga na tabela antes de se candidatar.",
                parent=self,
            )
            return

        vaga_id = int(selecao[0])
        try:
            CandidatoDAO.inscrever_candidato(
                candidato_id=Sessao.usuario_id,
                vaga_id=vaga_id,
            )
        except InscricaoDuplicadaError as erro:
            messagebox.showerror("Inscrição duplicada", str(erro), parent=self)
            return
        except Exception as erro:
            messagebox.showerror(
                "Erro ao se candidatar",
                f"Não foi possível registrar sua inscrição:\n{erro}",
                parent=self,
            )
            return

        self._carregar_candidaturas()
        messagebox.showinfo(
            "Inscrição realizada",
            "Sua candidatura foi registrada com sucesso!",
            parent=self,
        )

    def _carregar_candidaturas(self) -> None:
        for item in self.tree_candidaturas.get_children():
            self.tree_candidaturas.delete(item)

        if Sessao.usuario_id is None:
            return

        candidaturas = CandidatoDAO.listar_candidaturas(Sessao.usuario_id)
        for item in candidaturas:
            self.tree_candidaturas.insert(
                "",
                "end",
                values=(
                    item["id"],
                    item["titulo"],
                    item["localidade"],
                    formatar_moeda(item["bolsa_auxilio"]),
                    item["data_inscricao"],
                    item["status"],
                ),
            )

    def _carregar_perfil(self) -> None:
        if Sessao.usuario_id is None:
            return

        perfil = CandidatoDAO.buscar_perfil(Sessao.usuario_id)
        self.var_curso.set(perfil["curso"] if perfil else "")
        self.var_instituicao.set(perfil["instituicao"] if perfil else "")
        self.var_periodo.set(perfil["periodo"] if perfil else "")
        self.var_habilidades.set((perfil.get("habilidades") or "") if perfil else "")

        self.txt_resumo.delete("1.0", "end")
        if perfil and perfil.get("resumo"):
            self.txt_resumo.insert("1.0", perfil["resumo"])

    def _salvar_perfil(self) -> None:
        if Sessao.usuario_id is None:
            messagebox.showerror("Sessão expirada", "Faça login novamente.", parent=self)
            return

        resumo = self.txt_resumo.get("1.0", "end").strip()
        try:
            CandidatoDAO.salvar_perfil(
                usuario_id=Sessao.usuario_id,
                curso=self.var_curso.get(),
                instituicao=self.var_instituicao.get(),
                periodo=self.var_periodo.get(),
                habilidades=self.var_habilidades.get(),
                resumo=resumo,
            )
        except ValueError as erro:
            messagebox.showerror("Campos obrigatórios", str(erro), parent=self)
            return
        except Exception as erro:
            messagebox.showerror(
                "Erro ao salvar",
                f"Não foi possível salvar o perfil acadêmico:\n{erro}",
                parent=self,
            )
            return

        messagebox.showinfo(
            "Perfil salvo",
            "Seu perfil acadêmico foi salvo com sucesso!",
            parent=self,
        )

    def _excluir_perfil(self) -> None:
        if Sessao.usuario_id is None:
            return

        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            "Tem certeza de que deseja excluir seus dados de perfil acadêmico?",
            parent=self,
        )
        if not confirmar:
            return

        excluido = CandidatoDAO.excluir_perfil(Sessao.usuario_id)
        if not excluido:
            messagebox.showinfo(
                "Aviso",
                "Nenhum perfil acadêmico cadastrado para excluir.",
                parent=self,
            )
            return

        self._carregar_perfil()
        messagebox.showinfo(
            "Perfil excluído",
            "Seu perfil acadêmico foi removido com sucesso.",
            parent=self,
        )

    def _executar_logout(self) -> None:
        Sessao.logout()
        if callable(self.on_logout):
            self.on_logout()
        elif self.controller and hasattr(self.controller, "realizar_logout"):
            self.controller.realizar_logout()
