import tkinter as tk
from tkinter import ttk, messagebox

from dao.recrutador_dao import (
    cadastrar_vaga,
    listar_vagas_recrutador,
    listar_candidatos_da_vaga,
    atualizar_status_candidatura,
    atualizar_vaga,
    excluir_vaga,
    obter_vaga_por_id
)
from utils import (
    LISTA_STATUS_VAGA,
    LISTA_STATUS_CANDIDATURA,
    STATUS_VAGA_ATIVA,
    validar_campos_obrigatorios,
    resetar_estilo_campos,
    formatar_moeda,
    converter_moeda_para_float
)


class RecrutadorView(tk.Frame):

    def __init__(self, master, controller=None):
        super().__init__(master, bg="#F4F6F9")
        self.controller = controller
        self.vaga_em_edicao_id = None
        self.vaga_selecionada_triagem_id = None
        self.candidatos_atuais = []
        self.inscricao_selecionada_id = None

        self.configurar_estilos()
        self.construir_interface()
        self.carregar_minhas_vagas()

    def obter_dados_usuario_logado(self) -> tuple[int, str]:
        if self.controller and hasattr(self.controller, "obter_usuario_logado"):
            usuario = self.controller.obter_usuario_logado()
            if usuario and isinstance(usuario, dict):
                return usuario.get("id", 1), usuario.get("nome", "Recrutador")

        try:
            import session
            if hasattr(session, "Sessao"):
                s = session.Sessao
                uid = getattr(s, "usuario_id", None) or getattr(s, "id", None)
                nome = getattr(s, "nome", "Recrutador")
                if uid:
                    return uid, nome
        except ImportError:
            pass

        return 1, "Empresa Recrutadora"

    def configurar_estilos(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#E3E8EE")
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[14, 6])

    def construir_interface(self) -> None:
        recrutador_id, nome_recrutador = self.obter_dados_usuario_logado()

        # Cabeçalho Superior
        frm_header = tk.Frame(self, bg="#1E293B", height=60, padx=20, pady=12)
        frm_header.pack(fill=tk.X)

        self.lbl_titulo_sistema = tk.Label(
            frm_header,
            text=f"Painel do Recrutador — {nome_recrutador}",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#1E293B"
        )
        self.lbl_titulo_sistema.pack(side=tk.LEFT)

        self.btn_sair = tk.Button(
            frm_header,
            text="Sair / Logout",
            font=("Segoe UI", 10, "bold"),
            bg="#DC2626",
            fg="white",
            activebackground="#B91C1C",
            activeforeground="white",
            relief=tk.FLAT,
            padx=14,
            pady=4,
            cursor="hand2",
            command=self.realizar_logout
        )
        self.btn_sair.pack(side=tk.RIGHT)

        self.ntb_recrutador = ttk.Notebook(self)
        self.ntb_recrutador.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        self.tab_minhas_vagas = tk.Frame(self.ntb_recrutador, bg="#F4F6F9", padx=14, pady=14)
        self.ntb_recrutador.add(self.tab_minhas_vagas, text="📋 Minhas Vagas")

        self.tab_formulario_vaga = tk.Frame(self.ntb_recrutador, bg="#F4F6F9", padx=20, pady=14)
        self.ntb_recrutador.add(self.tab_formulario_vaga, text="➕ Nova Vaga")

        self.tab_candidatos = tk.Frame(self.ntb_recrutador, bg="#F4F6F9", padx=14, pady=14)
        self.ntb_recrutador.add(self.tab_candidatos, text="🎓 Candidatos e Avaliação")

        self.construir_aba_minhas_vagas()
        self.construir_aba_formulario_vaga()
        self.construir_aba_candidatos()

    def construir_aba_minhas_vagas(self) -> None:
        frm_topo = tk.Frame(self.tab_minhas_vagas, bg="#F4F6F9")
        frm_topo.pack(fill=tk.X, pady=(0, 10))

        self.lbl_minhas_vagas = tk.Label(
            frm_topo,
            text="Oportunidades de Estágio Gerenciadas",
            font=("Segoe UI", 12, "bold"),
            bg="#F4F6F9",
            fg="#1E293B"
        )
        self.lbl_minhas_vagas.pack(side=tk.LEFT)

        self.btn_nova_vaga_atalho = tk.Button(
            frm_topo,
            text="+ Nova Vaga",
            font=("Segoe UI", 10, "bold"),
            bg="#2563EB",
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.abrir_formulario_nova_vaga
        )
        self.btn_nova_vaga_atalho.pack(side=tk.RIGHT, padx=4)

        self.btn_atualizar_lista = tk.Button(
            frm_topo,
            text="↻ Atualizar Lista",
            font=("Segoe UI", 10),
            bg="#64748B",
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.carregar_minhas_vagas
        )
        self.btn_atualizar_lista.pack(side=tk.RIGHT, padx=4)

        frm_tabela = tk.Frame(self.tab_minhas_vagas, bg="white", bd=1, relief=tk.SOLID)
        frm_tabela.pack(fill=tk.BOTH, expand=True)

        colunas = ("id", "titulo", "localidade", "bolsa", "status")
        self.tbl_vagas = ttk.Treeview(frm_tabela, columns=colunas, show="headings", selectmode="browse")

        self.tbl_vagas.heading("id", text="ID")
        self.tbl_vagas.heading("titulo", text="Título da Vaga")
        self.tbl_vagas.heading("localidade", text="Localidade")
        self.tbl_vagas.heading("bolsa", text="Bolsa-Auxílio")
        self.tbl_vagas.heading("status", text="Status")

        self.tbl_vagas.column("id", width=60, anchor=tk.CENTER)
        self.tbl_vagas.column("titulo", width=320, anchor=tk.W)
        self.tbl_vagas.column("localidade", width=180, anchor=tk.W)
        self.tbl_vagas.column("bolsa", width=130, anchor=tk.E)
        self.tbl_vagas.column("status", width=110, anchor=tk.CENTER)

        scroll_y = ttk.Scrollbar(frm_tabela, orient=tk.VERTICAL, command=self.tbl_vagas.yview)
        self.tbl_vagas.configure(yscrollcommand=scroll_y.set)

        self.tbl_vagas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        frm_acoes = tk.Frame(self.tab_minhas_vagas, bg="#F4F6F9", pady=10)
        frm_acoes.pack(fill=tk.X)

        self.btn_ver_candidatos = tk.Button(
            frm_acoes,
            text="👥 Ver Candidatos (UC08)",
            font=("Segoe UI", 10, "bold"),
            bg="#059669",
            fg="white",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.consultar_candidatos_vaga_selecionada
        )
        self.btn_ver_candidatos.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_editar_vaga = tk.Button(
            frm_acoes,
            text="✏️ Editar Vaga Selecionada",
            font=("Segoe UI", 10, "bold"),
            bg="#D97706",
            fg="white",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.preparar_edicao_vaga
        )
        self.btn_editar_vaga.pack(side=tk.LEFT, padx=8)

        self.btn_excluir_vaga = tk.Button(
            frm_acoes,
            text="🗑️ Excluir Vaga",
            font=("Segoe UI", 10, "bold"),
            bg="#DC2626",
            fg="white",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.remover_vaga_selecionada
        )
        self.btn_excluir_vaga.pack(side=tk.RIGHT)

    def construir_aba_formulario_vaga(self) -> None:
        frm_card = tk.Frame(self.tab_formulario_vaga, bg="white", padx=24, pady=20, bd=1, relief=tk.SOLID)
        frm_card.pack(fill=tk.BOTH, expand=True)

        self.lbl_form_titulo = tk.Label(
            frm_card,
            text="Cadastrar Nova Vaga de Estágio",
            font=("Segoe UI", 13, "bold"),
            bg="white",
            fg="#1E293B"
        )
        self.lbl_form_titulo.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 14))

        self.lbl_titulo = tk.Label(frm_card, text="Título da Vaga *:", font=("Segoe UI", 10, "bold"), bg="white")
        self.lbl_titulo.grid(row=1, column=0, sticky="w", pady=6)
        self.txt_titulo = tk.Entry(frm_card, font=("Segoe UI", 10), width=42, bd=1, relief=tk.SOLID)
        self.txt_titulo.grid(row=1, column=1, sticky="we", padx=(8, 20), pady=6)

        self.lbl_localidade = tk.Label(frm_card, text="Localidade (Cidade/UF) *:", font=("Segoe UI", 10, "bold"), bg="white")
        self.lbl_localidade.grid(row=1, column=2, sticky="w", pady=6)
        self.txt_localidade = tk.Entry(frm_card, font=("Segoe UI", 10), width=28, bd=1, relief=tk.SOLID)
        self.txt_localidade.grid(row=1, column=3, sticky="we", padx=(8, 0), pady=6)

        self.lbl_bolsa = tk.Label(frm_card, text="Bolsa-Auxílio (R$) *:", font=("Segoe UI", 10, "bold"), bg="white")
        self.lbl_bolsa.grid(row=2, column=0, sticky="w", pady=6)
        self.txt_bolsa_auxilio = tk.Entry(frm_card, font=("Segoe UI", 10), width=20, bd=1, relief=tk.SOLID)
        self.txt_bolsa_auxilio.grid(row=2, column=1, sticky="w", padx=(8, 20), pady=6)

        self.lbl_status_vaga = tk.Label(frm_card, text="Status da Vaga:", font=("Segoe UI", 10, "bold"), bg="white")
        self.lbl_status_vaga.grid(row=2, column=2, sticky="w", pady=6)
        self.cmb_status_vaga = ttk.Combobox(frm_card, values=LISTA_STATUS_VAGA, state="readonly", font=("Segoe UI", 10), width=25)
        self.cmb_status_vaga.set(STATUS_VAGA_ATIVA)
        self.cmb_status_vaga.grid(row=2, column=3, sticky="w", padx=(8, 0), pady=6)

        self.lbl_descricao = tk.Label(frm_card, text="Descrição das Atividades *:", font=("Segoe UI", 10, "bold"), bg="white")
        self.lbl_descricao.grid(row=3, column=0, columnspan=4, sticky="w", pady=(10, 4))
        self.txt_descricao = tk.Text(frm_card, font=("Segoe UI", 10), height=5, bd=1, relief=tk.SOLID)
        self.txt_descricao.grid(row=4, column=0, columnspan=4, sticky="nsew", pady=4)

        self.lbl_requisitos = tk.Label(frm_card, text="Requisitos Técnicos e Acadêmicos *:", font=("Segoe UI", 10, "bold"), bg="white")
        self.lbl_requisitos.grid(row=5, column=0, columnspan=4, sticky="w", pady=(10, 4))
        self.txt_requisitos = tk.Text(frm_card, font=("Segoe UI", 10), height=4, bd=1, relief=tk.SOLID)
        self.txt_requisitos.grid(row=6, column=0, columnspan=4, sticky="nsew", pady=4)

        frm_card.columnconfigure(1, weight=2)
        frm_card.columnconfigure(3, weight=1)
        frm_card.rowconfigure(4, weight=1)
        frm_card.rowconfigure(6, weight=1)

        frm_botoes_form = tk.Frame(frm_card, bg="white", pady=14)
        frm_botoes_form.grid(row=7, column=0, columnspan=4, sticky="e")

        self.btn_limpar_form = tk.Button(
            frm_botoes_form,
            text="Limpar / Cancelar Edição",
            font=("Segoe UI", 10),
            bg="#64748B",
            fg="white",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.limpar_formulario_vaga
        )
        self.btn_limpar_form.pack(side=tk.LEFT, padx=8)

        self.btn_salvar = tk.Button(
            frm_botoes_form,
            text="💾 Salvar",
            font=("Segoe UI", 10, "bold"),
            bg="#16A34A",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=6,
            cursor="hand2",
            command=self.salvar_vaga
        )
        self.btn_salvar.pack(side=tk.LEFT)

    def construir_aba_candidatos(self) -> None:
        frm_filtro_vaga = tk.Frame(self.tab_candidatos, bg="#F4F6F9")
        frm_filtro_vaga.pack(fill=tk.X, pady=(0, 10))

        self.lbl_vaga_avaliacao = tk.Label(
            frm_filtro_vaga,
            text="Vaga Selecionada para Triagem:",
            font=("Segoe UI", 10, "bold"),
            bg="#F4F6F9"
        )
        self.lbl_vaga_avaliacao.pack(side=tk.LEFT)

        self.cmb_vaga_triagem = ttk.Combobox(
            frm_filtro_vaga,
            state="readonly",
            font=("Segoe UI", 10),
            width=48
        )
        self.cmb_vaga_triagem.pack(side=tk.LEFT, padx=10)
        self.cmb_vaga_triagem.bind("<<ComboboxSelected>>", self.ao_selecionar_vaga_combobox)

        self.btn_carregar_inscritos = tk.Button(
            frm_filtro_vaga,
            text="🔍 Buscar Inscritos",
            font=("Segoe UI", 10, "bold"),
            bg="#2563EB",
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.carregar_inscritos_do_combobox
        )
        self.btn_carregar_inscritos.pack(side=tk.LEFT)

        frm_conteudo = tk.Frame(self.tab_candidatos, bg="#F4F6F9")
        frm_conteudo.pack(fill=tk.BOTH, expand=True)

        frm_esquerda = tk.Frame(frm_conteudo, bg="white", bd=1, relief=tk.SOLID, padx=8, pady=8)
        frm_esquerda.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self.lbl_lista_candidatos = tk.Label(
            frm_esquerda,
            text="Candidatos Inscritos na Vaga (Clique para ver o perfil completo)",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#1E293B"
        )
        self.lbl_lista_candidatos.pack(anchor="w", pady=(0, 6))

        colunas_cand = ("inscricao_id", "nome", "curso", "periodo", "status")
        self.tbl_candidatos = ttk.Treeview(
            frm_esquerda,
            columns=colunas_cand,
            show="headings",
            selectmode="browse"
        )

        self.tbl_candidatos.heading("inscricao_id", text="Inscrição")
        self.tbl_candidatos.heading("nome", text="Nome do Candidato")
        self.tbl_candidatos.heading("curso", text="Curso")
        self.tbl_candidatos.heading("periodo", text="Período")
        self.tbl_candidatos.heading("status", text="Status Atual")

        self.tbl_candidatos.column("inscricao_id", width=65, anchor=tk.CENTER)
        self.tbl_candidatos.column("nome", width=170, anchor=tk.W)
        self.tbl_candidatos.column("curso", width=160, anchor=tk.W)
        self.tbl_candidatos.column("periodo", width=80, anchor=tk.CENTER)
        self.tbl_candidatos.column("status", width=140, anchor=tk.CENTER)

        scroll_cand = ttk.Scrollbar(frm_esquerda, orient=tk.VERTICAL, command=self.tbl_candidatos.yview)
        self.tbl_candidatos.configure(yscrollcommand=scroll_cand.set)

        self.tbl_candidatos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_cand.pack(side=tk.RIGHT, fill=tk.Y)

        self.tbl_candidatos.bind("<<TreeviewSelect>>", self.exibir_detalhes_candidato_selecionado)

        frm_direita = tk.Frame(frm_conteudo, bg="white", bd=1, relief=tk.SOLID, padx=16, pady=12, width=380)
        frm_direita.pack(side=tk.RIGHT, fill=tk.BOTH)
        frm_direita.pack_propagate(False)

        self.lbl_detalhes_titulo = tk.Label(
            frm_direita,
            text="Perfil Acadêmico do Candidato",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#1E293B"
        )
        self.lbl_detalhes_titulo.pack(anchor="w", pady=(0, 8))

        self.txt_detalhes_candidato = tk.Text(
            frm_direita,
            font=("Segoe UI", 10),
            bg="#F8FAFC",
            fg="#1E293B",
            height=13,
            bd=1,
            relief=tk.SOLID,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.txt_detalhes_candidato.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        frm_avaliacao = tk.Frame(frm_direita, bg="white")
        frm_avaliacao.pack(fill=tk.X)

        self.lbl_status_avaliacao = tk.Label(
            frm_avaliacao,
            text="Selecione o Novo Status da Candidatura:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        )
        self.lbl_status_avaliacao.pack(anchor="w", pady=(0, 4))

        self.cmb_status_avaliacao = ttk.Combobox(
            frm_avaliacao,
            values=LISTA_STATUS_CANDIDATURA,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.cmb_status_avaliacao.set(LISTA_STATUS_CANDIDATURA[0])
        self.cmb_status_avaliacao.pack(fill=tk.X, pady=(0, 10))

        self.btn_confirmar_avaliacao = tk.Button(
            frm_avaliacao,
            text="✅ Confirmar Avaliação",
            font=("Segoe UI", 10, "bold"),
            bg="#16A34A",
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.confirmar_avaliacao_candidato
        )
        self.btn_confirmar_avaliacao.pack(fill=tk.X)

    def carregar_minhas_vagas(self) -> None:
        for item in self.tbl_vagas.get_children():
            self.tbl_vagas.delete(item)

        recrutador_id, _ = self.obter_dados_usuario_logado()
        vagas = listar_vagas_recrutador(recrutador_id)

        opcoes_combo = []
        self.mapa_combo_vagas = {}

        for v in vagas:
            bolsa_fmt = formatar_moeda(v["bolsa_auxilio"])
            self.tbl_vagas.insert(
                "",
                tk.END,
                values=(v["id"], v["titulo"], v["localidade"], bolsa_fmt, v["status"])
            )
            chave = f"#{v['id']} - {v['titulo']} ({v['localidade']})"
            opcoes_combo.append(chave)
            self.mapa_combo_vagas[chave] = v["id"]

        self.cmb_vaga_triagem["values"] = opcoes_combo
        if opcoes_combo and not self.cmb_vaga_triagem.get():
            self.cmb_vaga_triagem.set(opcoes_combo[0])

    def abrir_formulario_nova_vaga(self) -> None:
        self.limpar_formulario_vaga()
        self.ntb_recrutador.select(self.tab_formulario_vaga)

    def limpar_formulario_vaga(self) -> None:
        self.vaga_em_edicao_id = None
        self.lbl_form_titulo.config(text="Cadastrar Nova Vaga de Estágio")
        self.ntb_recrutador.tab(self.tab_formulario_vaga, text="➕ Nova Vaga")

        self.txt_titulo.delete(0, tk.END)
        self.txt_localidade.delete(0, tk.END)
        self.txt_bolsa_auxilio.delete(0, tk.END)
        self.cmb_status_vaga.set(STATUS_VAGA_ATIVA)
        self.txt_descricao.delete("1.0", tk.END)
        self.txt_requisitos.delete("1.0", tk.END)

        resetar_estilo_campos([
            self.txt_titulo,
            self.txt_localidade,
            self.txt_bolsa_auxilio,
            self.txt_descricao,
            self.txt_requisitos
        ])

    def salvar_vaga(self) -> None:
        campos_obrigatorios = {
            "Título": self.txt_titulo,
            "Localidade": self.txt_localidade,
            "Bolsa-Auxílio": self.txt_bolsa_auxilio,
            "Descrição": self.txt_descricao,
            "Requisitos": self.txt_requisitos
        }

        if not validar_campos_obrigatorios(campos_obrigatorios):
            return

        bolsa_valor = converter_moeda_para_float(self.txt_bolsa_auxilio.get())
        if bolsa_valor is None:
            self.txt_bolsa_auxilio.config(
                highlightbackground="#E53935",
                highlightcolor="#E53935",
                highlightthickness=2,
                bg="#FFEBEE"
            )
            messagebox.showwarning(
                "Valor Inválido",
                "Informe um valor numérico válido para a Bolsa-Auxílio (ex: 1200.00)."
            )
            return

        recrutador_id, _ = self.obter_dados_usuario_logado()
        titulo = self.txt_titulo.get().strip()
        localidade = self.txt_localidade.get().strip()
        descricao = self.txt_descricao.get("1.0", tk.END).strip()
        requisitos = self.txt_requisitos.get("1.0", tk.END).strip()
        status_vaga = self.cmb_status_vaga.get()

        if self.vaga_em_edicao_id is None:
            sucesso = cadastrar_vaga(
                recrutador_id=recrutador_id,
                titulo=titulo,
                descricao=descricao,
                localidade=localidade,
                bolsa=bolsa_valor,
                requisitos=requisitos
            )
            if sucesso:
                messagebox.showinfo("Sucesso", "Vaga cadastrada com sucesso!")
                self.limpar_formulario_vaga()
                self.carregar_minhas_vagas()
                self.ntb_recrutador.select(self.tab_minhas_vagas)
            else:
                messagebox.showerror("Erro", "Não foi possível salvar a vaga no banco de dados.")
        else:
            sucesso = atualizar_vaga(
                vaga_id=self.vaga_em_edicao_id,
                recrutador_id=recrutador_id,
                titulo=titulo,
                descricao=descricao,
                localidade=localidade,
                bolsa=bolsa_valor,
                requisitos=requisitos,
                status=status_vaga
            )
            if sucesso:
                messagebox.showinfo("Sucesso", "Vaga atualizada com sucesso!")
                self.limpar_formulario_vaga()
                self.carregar_minhas_vagas()
                self.ntb_recrutador.select(self.tab_minhas_vagas)
            else:
                messagebox.showerror("Erro", "Não foi possível atualizar a vaga selecionada.")

    def preparar_edicao_vaga(self) -> None:
        selecao = self.tbl_vagas.selection()
        if not selecao:
            messagebox.showwarning("Seleção Necessária", "Selecione uma vaga na tabela para editar.")
            return

        valores = self.tbl_vagas.item(selecao[0], "values")
        vaga_id = int(valores[0])
        vaga = obter_vaga_por_id(vaga_id)

        if not vaga:
            messagebox.showerror("Erro", "Vaga não encontrada no banco de dados.")
            return

        self.limpar_formulario_vaga()
        self.vaga_em_edicao_id = vaga["id"]
        self.lbl_form_titulo.config(text=f"Editar Vaga #{vaga['id']} — {vaga['titulo']}")
        self.ntb_recrutador.tab(self.tab_formulario_vaga, text="✏️ Editar Vaga")

        self.txt_titulo.insert(0, vaga["titulo"])
        self.txt_localidade.insert(0, vaga["localidade"])
        self.txt_bolsa_auxilio.insert(0, f"{float(vaga['bolsa_auxilio']):.2f}")
        self.cmb_status_vaga.set(vaga["status"])
        self.txt_descricao.insert("1.0", vaga["descricao"])
        self.txt_requisitos.insert("1.0", vaga["requisitos"])

        self.ntb_recrutador.select(self.tab_formulario_vaga)

    def remover_vaga_selecionada(self) -> None:
        selecao = self.tbl_vagas.selection()
        if not selecao:
            messagebox.showwarning("Seleção Necessária", "Selecione uma vaga na tabela para excluir.")
            return

        valores = self.tbl_vagas.item(selecao[0], "values")
        vaga_id = int(valores[0])
        titulo_vaga = valores[1]

        confirmar = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a vaga '{titulo_vaga}'?\n"
            "Todas as inscrições associadas também serão removidas."
        )
        if not confirmar:
            return

        recrutador_id, _ = self.obter_dados_usuario_logado()
        if excluir_vaga(vaga_id, recrutador_id):
            messagebox.showinfo("Sucesso", "Vaga excluída com sucesso!")
            self.carregar_minhas_vagas()
        else:
            messagebox.showerror("Erro", "Não foi possível excluir a vaga.")


    def consultar_candidatos_vaga_selecionada(self) -> None:
        selecao = self.tbl_vagas.selection()
        if not selecao:
            messagebox.showwarning("Seleção Necessária", "Selecione uma vaga na lista para ver os candidatos.")
            return

        valores = self.tbl_vagas.item(selecao[0], "values")
        vaga_id = int(valores[0])

        for chave, vid in getattr(self, "mapa_combo_vagas", {}).items():
            if vid == vaga_id:
                self.cmb_vaga_triagem.set(chave)
                break

        self.ntb_recrutador.select(self.tab_candidatos)
        self.carregar_candidatos_da_vaga(vaga_id)

    def ao_selecionar_vaga_combobox(self, event=None) -> None:
        self.carregar_inscritos_do_combobox()

    def carregar_inscritos_do_combobox(self) -> None:
        chave = self.cmb_vaga_triagem.get()
        vaga_id = getattr(self, "mapa_combo_vagas", {}).get(chave)
        if not vaga_id:
            messagebox.showwarning("Aviso", "Selecione uma vaga válida.")
            return
        self.carregar_candidatos_da_vaga(vaga_id)

    def carregar_candidatos_da_vaga(self, vaga_id: int) -> None:
        self.vaga_selecionada_triagem_id = vaga_id
        self.inscricao_selecionada_id = None
        self.limpar_painel_detalhes_candidato()

        for item in self.tbl_candidatos.get_children():
            self.tbl_candidatos.delete(item)

        self.candidatos_atuais = listar_candidatos_da_vaga(vaga_id)

        if not self.candidatos_atuais:
            messagebox.showinfo(
                "Sem Inscritos",
                "Ainda não há candidatos inscritos para esta vaga."
            )
            return

        for cand in self.candidatos_atuais:
            self.tbl_candidatos.insert(
                "",
                tk.END,
                values=(
                    cand["inscricao_id"],
                    cand["nome"],
                    cand["curso"],
                    cand["periodo"],
                    cand["status"]
                )
            )

    def limpar_painel_detalhes_candidato(self) -> None:
        self.txt_detalhes_candidato.config(state=tk.NORMAL)
        self.txt_detalhes_candidato.delete("1.0", tk.END)
        self.txt_detalhes_candidato.insert(
            "1.0",
            "Selecione um candidato na tabela ao lado para visualizar seus detalhes acadêmicos completos."
        )
        self.txt_detalhes_candidato.config(state=tk.DISABLED)

    def exibir_detalhes_candidato_selecionado(self, event=None) -> None: 
        selecao = self.tbl_candidatos.selection()
        if not selecao:
            return

        valores = self.tbl_candidatos.item(selecao[0], "values")
        inscricao_id = int(valores[0])
        self.inscricao_selecionada_id = inscricao_id

        candidato = next(
            (c for c in self.candidatos_atuais if c["inscricao_id"] == inscricao_id),
            None
        )
        if not candidato:
            return

        detalhes_texto = (
            f"Nome: {candidato['nome']}\n"
            f"E-mail: {candidato['email']}\n"
            f"Data da Inscrição: {candidato['data_inscricao']}\n"
            f"Status Atual: {candidato['status']}\n"
            f"{'-' * 42}\n"
            f"Curso: {candidato['curso']}\n"
            f"Instituição: {candidato['instituicao']}\n"
            f"Período/Semestre: {candidato['periodo']}\n\n"
            f"Habilidades / Competências:\n{candidato['habilidades']}\n\n"
            f"Resumo Profissional:\n{candidato['resumo']}"
        )

        self.txt_detalhes_candidato.config(state=tk.NORMAL)
        self.txt_detalhes_candidato.delete("1.0", tk.END)
        self.txt_detalhes_candidato.insert("1.0", detalhes_texto)
        self.txt_detalhes_candidato.config(state=tk.DISABLED)

        if candidato["status"] in LISTA_STATUS_CANDIDATURA:
            self.cmb_status_avaliacao.set(candidato["status"])

    def confirmar_avaliacao_candidato(self) -> None:
        if not self.inscricao_selecionada_id:
            messagebox.showwarning(
                "Seleção Necessária",
                "Clique primeiro em um candidato na lista para avaliar sua candidatura."
            )
            return

        novo_status = self.cmb_status_avaliacao.get()
        if not novo_status:
            messagebox.showwarning("Aviso", "Selecione um status válido para avaliação.")
            return

        sucesso = atualizar_status_candidatura(self.inscricao_selecionada_id, novo_status)
        if sucesso:
            messagebox.showinfo("Avaliação Concluída", "Status do candidato atualizado com sucesso")
            if self.vaga_selecionada_triagem_id:
                self.carregar_candidatos_da_vaga(self.vaga_selecionada_triagem_id)
        else:
            messagebox.showerror("Erro", "Não foi possível atualizar o status da candidatura.")

    def realizar_logout(self) -> None:
        if self.controller and hasattr(self.controller, "realizar_logout"):
            self.controller.realizar_logout()