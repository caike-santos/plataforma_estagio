import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from dao.auth_dao import (
    AuthDAO,
    CredenciaisInvalidasError,
    EmailJaCadastradoError,
)
from sessao import TipoPerfil


class LoginView(ttk.Frame):
    """Tela unificada de Login e Cadastro de Usuário."""

    def __init__(
        self,
        master: tk.Misc,
        on_login_success: Callable[[TipoPerfil], None] | None = None,
        controller: object = None,
    ) -> None:
        super().__init__(master, padding=24)
        self.controller = controller
        self.on_login_success = on_login_success

        self._configurar_layout()
        self._construir_aba_login()
        self._construir_aba_cadastro()

    def _configurar_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        titulo = ttk.Label(
            self,
            text="Sistema de Recrutamento de Estágios",
            font=("Segoe UI", 15, "bold"),
            anchor="center",
        )
        titulo.grid(row=0, column=0, pady=(0, 16), sticky="ew")

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self.aba_login = ttk.Frame(self.notebook, padding=20)
        self.aba_cadastro = ttk.Frame(self.notebook, padding=20)

        self.notebook.add(self.aba_login, text="  Login  ")
        self.notebook.add(self.aba_cadastro, text="  Criar Conta  ")

    def _construir_aba_login(self) -> None:
        self.aba_login.columnconfigure(0, weight=1)

        ttk.Label(self.aba_login, text="E-mail:").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self.var_login_email = tk.StringVar()
        self.entry_login_email = ttk.Entry(
            self.aba_login, textvariable=self.var_login_email, width=38
        )
        self.entry_login_email.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        ttk.Label(self.aba_login, text="Senha:").grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        self.var_login_senha = tk.StringVar()
        self.entry_login_senha = ttk.Entry(
            self.aba_login, textvariable=self.var_login_senha, show="*", width=38
        )
        self.entry_login_senha.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        self.entry_login_senha.bind("<Return>", lambda _: self._processar_login())

        btn_entrar = ttk.Button(
            self.aba_login,
            text="Entrar",
            command=self._processar_login,
        )
        btn_entrar.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        btn_ir_cadastro = ttk.Button(
            self.aba_login,
            text="Não tem conta? Cadastre-se",
            command=lambda: self.notebook.select(self.aba_cadastro),
        )
        btn_ir_cadastro.grid(row=5, column=0, sticky="ew")

    def _construir_aba_cadastro(self) -> None:
        self.aba_cadastro.columnconfigure(0, weight=1)

        ttk.Label(self.aba_cadastro, text="Nome completo:").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self.var_cad_nome = tk.StringVar()
        ttk.Entry(self.aba_cadastro, textvariable=self.var_cad_nome, width=38).grid(
            row=1, column=0, sticky="ew", pady=(0, 10)
        )

        ttk.Label(self.aba_cadastro, text="E-mail:").grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        self.var_cad_email = tk.StringVar()
        ttk.Entry(self.aba_cadastro, textvariable=self.var_cad_email, width=38).grid(
            row=3, column=0, sticky="ew", pady=(0, 10)
        )

        ttk.Label(self.aba_cadastro, text="Senha:").grid(
            row=4, column=0, sticky="w", pady=(0, 4)
        )
        self.var_cad_senha = tk.StringVar()
        ttk.Entry(
            self.aba_cadastro, textvariable=self.var_cad_senha, show="*", width=38
        ).grid(row=5, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(self.aba_cadastro, text="Perfil:").grid(
            row=6, column=0, sticky="w", pady=(0, 4)
        )
        self.var_cad_perfil = tk.StringVar(value="Candidato")
        self.combo_perfil = ttk.Combobox(
            self.aba_cadastro,
            textvariable=self.var_cad_perfil,
            values=("Candidato", "Recrutador"),
            state="readonly",
            width=35,
        )
        self.combo_perfil.grid(row=7, column=0, sticky="ew", pady=(0, 16))

        btn_cadastrar = ttk.Button(
            self.aba_cadastro,
            text="Cadastrar",
            command=self._processar_cadastro,
        )
        btn_cadastrar.grid(row=8, column=0, sticky="ew", pady=(0, 8))

        btn_voltar_login = ttk.Button(
            self.aba_cadastro,
            text="Já possui conta? Fazer Login",
            command=lambda: self.notebook.select(self.aba_login),
        )
        btn_voltar_login.grid(row=9, column=0, sticky="ew")

    def _processar_login(self) -> None:
        email = self.var_login_email.get().strip()
        senha = self.var_login_senha.get()

        if not email or not senha:
            messagebox.showerror(
                "Campos obrigatórios",
                "Preencha o e-mail e a senha para continuar.",
                parent=self,
            )
            return

        try:
            usuario = AuthDAO.autenticar(email=email, senha=senha)
        except CredenciaisInvalidasError as erro:
            messagebox.showerror("Falha no Login", str(erro), parent=self)
            return
        except Exception as erro:
            messagebox.showerror(
                "Erro inesperado",
                f"Não foi possível realizar o login:\n{erro}",
                parent=self,
            )
            return

        self.var_login_senha.set("")
        tipo_perfil: TipoPerfil = usuario["tipo_perfil"]
        messagebox.showinfo(
            "Bem-vindo(a)",
            f"Login realizado com sucesso, {usuario['nome']} ({tipo_perfil})!",
            parent=self,
        )
        if callable(self.on_login_success):
            self.on_login_success(tipo_perfil)
        elif self.controller is not None and hasattr(self.controller, "navegar_por_perfil"):
            self.controller.navegar_por_perfil(usuario)
        elif hasattr(self.on_login_success, "navegar_por_perfil"):
            self.on_login_success.navegar_por_perfil(usuario)

    def _processar_cadastro(self) -> None:
        nome = self.var_cad_nome.get().strip()
        email = self.var_cad_email.get().strip()
        senha = self.var_cad_senha.get()
        tipo_perfil = self.var_cad_perfil.get().strip()

        if not nome or not email or not senha or not tipo_perfil:
            messagebox.showerror(
                "Campos obrigatórios",
                "Todos os campos de cadastro devem ser preenchidos.",
                parent=self,
            )
            return

        try:
            AuthDAO.cadastrar_usuario(
                nome=nome,
                email=email,
                senha=senha,
                tipo_perfil=tipo_perfil,
            )
        except (EmailJaCadastradoError, ValueError) as erro:
            messagebox.showerror("Não foi possível cadastrar", str(erro), parent=self)
            return
        except Exception as erro:
            messagebox.showerror(
                "Erro inesperado",
                f"Ocorreu um erro ao salvar o cadastro:\n{erro}",
                parent=self,
            )
            return

        messagebox.showinfo(
            "Cadastro concluído",
            "Conta criada com sucesso! Faça login para acessar o sistema.",
            parent=self,
        )

        self.var_login_email.set(email)
        self.var_login_senha.set("")
        self.var_cad_nome.set("")
        self.var_cad_email.set("")
        self.var_cad_senha.set("")
        self.var_cad_perfil.set("Candidato")

        self.notebook.select(self.aba_login)
        self.entry_login_senha.focus_set()
