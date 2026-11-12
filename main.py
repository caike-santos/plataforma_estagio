import sqlite3
import tkinter as tk
from tkinter import messagebox

from utils import DB_NAME, PERFIL_CANDIDATO, PERFIL_RECRUTADOR
from views.recrutador_view import RecrutadorView


def garantir_inicializacao_banco() -> None:
    try:
        import database
        for nome_func in ("inicializar_banco", "criar_tabelas", "init_db", "setup_db"):
            if hasattr(database, nome_func):
                getattr(database, nome_func)()
                return
    except ImportError:
        pass

    ddl_sql = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        tipo_perfil TEXT NOT NULL CHECK(tipo_perfil IN ('Candidato', 'Recrutador'))
    );

    CREATE TABLE IF NOT EXISTS perfis_academicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER UNIQUE NOT NULL,
        curso TEXT NOT NULL,
        instituicao TEXT NOT NULL,
        periodo TEXT NOT NULL,
        habilidades TEXT,
        resumo TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS vagas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recrutador_id INTEGER NOT NULL,
        titulo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        localidade TEXT NOT NULL,
        bolsa_auxilio REAL NOT NULL,
        requisitos TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Ativa',
        FOREIGN KEY (recrutador_id) REFERENCES usuarios(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS inscricoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidato_id INTEGER NOT NULL,
        vaga_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Em Análise',
        data_inscricao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidato_id) REFERENCES usuarios(id) ON DELETE CASCADE,
        FOREIGN KEY (vaga_id) REFERENCES vagas(id) ON DELETE CASCADE,
        UNIQUE(candidato_id, vaga_id)
    );
    """
    with sqlite3.connect(DB_NAME) as conn:
        conn.executescript(ddl_sql)


class AplicacaoPrincipal(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Plataforma de Triagem para Vagas de Estágio")
        self.geometry("1080x680")
        self.minsize(960, 600)
        self.configure(bg="#F4F6F9")

        self.usuario_atual = None
        self.frame_atual = None

        # Container principal onde os Frames (Views) são empilhados/alternados
        self.container = tk.Frame(self, bg="#F4F6F9")
        self.container.pack(fill=tk.BOTH, expand=True)

        self.exibir_tela_login()

    def definir_usuario_logado(self, dados_usuario: dict) -> None:
        """Salva os dados do usuário no controller e sincroniza com session.py (Dev 1)."""
        self.usuario_atual = dados_usuario
        try:
            import session
            if hasattr(session, "Sessao"):
                s = session.Sessao
                if hasattr(s, "iniciar_sessao"):
                    s.iniciar_sessao(
                        dados_usuario.get("id"),
                        dados_usuario.get("nome"),
                        dados_usuario.get("tipo_perfil")
                    )
                elif hasattr(s, "login"):
                    s.login(dados_usuario)
                else:
                    s.usuario_id = dados_usuario.get("id")
                    s.nome = dados_usuario.get("nome")
                    s.tipo_perfil = dados_usuario.get("tipo_perfil")
        except ImportError:
            pass

    def obter_usuario_logado(self) -> dict | None:
        if self.usuario_atual:
            return self.usuario_atual

        try:
            import session
            if hasattr(session, "Sessao"):
                s = session.Sessao
                if hasattr(s, "obter_usuario"):
                    return s.obter_usuario()
                uid = getattr(s, "usuario_id", None) or getattr(s, "id", None)
                if uid:
                    return {
                        "id": uid,
                        "nome": getattr(s, "nome", "Usuário"),
                        "tipo_perfil": getattr(s, "tipo_perfil", PERFIL_RECRUTADOR)
                    }
        except ImportError:
            pass

        return None

    def limpar_container(self) -> None:
        if self.frame_atual is not None:
            self.frame_atual.destroy()
            self.frame_atual = None
        for widget in self.container.winfo_children():
            widget.destroy()

    def instanciar_view_flexivel(self, classe_view, **kwargs):
        try:
            return classe_view(self.container, controller=self, **kwargs)
        except TypeError:
            try:
                return classe_view(self.container, self)
            except TypeError:
                return classe_view(self.container)

    def navegar_por_perfil(self, dados_usuario: dict | None = None) -> None:
        if dados_usuario:
            self.definir_usuario_logado(dados_usuario)

        usuario = self.obter_usuario_logado()
        if not usuario:
            self.exibir_tela_login()
            return

        tipo_perfil = usuario.get("tipo_perfil")
        if tipo_perfil == PERFIL_RECRUTADOR:
            self.exibir_tela_recrutador()
        elif tipo_perfil == PERFIL_CANDIDATO:
            self.exibir_tela_candidato()
        else:
            messagebox.showerror("Erro de Perfil", f"Tipo de perfil desconhecido: {tipo_perfil}")
            self.exibir_tela_login()

    def exibir_tela_login(self) -> None:
        """Carrega a LoginView (Dev 1) ou exibe tela de integração caso ainda não exista."""
        self.limpar_container()
        try:
            from views.login_view import LoginView
            self.frame_atual = self.instanciar_view_flexivel(LoginView)
            if hasattr(self.frame_atual, "pack"):
                self.frame_atual.pack(fill=tk.BOTH, expand=True)
        except ImportError:
            self.construir_tela_fallback_login()

    def exibir_tela_candidato(self) -> None:
        """Carrega a CandidatoView (Dev 1)."""
        self.limpar_container()
        try:
            from views.candidato_view import CandidatoView
            self.frame_atual = self.instanciar_view_flexivel(CandidatoView)
            if hasattr(self.frame_atual, "pack"):
                self.frame_atual.pack(fill=tk.BOTH, expand=True)
        except ImportError:
            messagebox.showwarning(
                "Módulo Pendente (Dev 1)",
                "O arquivo 'views/candidato_view.py' (responsabilidade do Dev 1) ainda não foi integrado."
            )
            self.exibir_tela_login()

    def exibir_tela_recrutador(self) -> None:
        """Carrega a RecrutadorView (Dev 2)."""
        self.limpar_container()
        self.frame_atual = RecrutadorView(self.container, controller=self)
        self.frame_atual.pack(fill=tk.BOTH, expand=True)

    def realizar_logout(self) -> None:
        """Limpa os dados da sessão ativa e retorna para a tela inicial de login."""
        self.usuario_atual = None
        try:
            import session
            if hasattr(session, "Sessao"):
                s = session.Sessao
                if hasattr(s, "encerrar_sessao"):
                    s.encerrar_sessao()
                elif hasattr(s, "logout"):
                    s.logout()
                else:
                    s.usuario_id = None
                    s.nome = None
                    s.tipo_perfil = None
        except ImportError:
            pass

        self.exibir_tela_login()

    def construir_tela_fallback_login(self) -> None:
        frm_box = tk.Frame(self.container, bg="white", padx=32, pady=28, bd=1, relief=tk.SOLID)
        frm_box.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        lbl_aviso = tk.Label(
            frm_box,
            text="Ambiente de Desenvolvimento — Módulo Dev 2",
            font=("Segoe UI", 13, "bold"),
            bg="white",
            fg="#1E293B"
        )
        lbl_aviso.pack(pady=(0, 8))

        lbl_sub = tk.Label(
            frm_box,
            text=(
                "O módulo 'views/login_view.py' (Dev 1) ainda não foi detectado.\n"
                "Utilize o acesso rápido abaixo para testar todas as funcionalidades do Recrutador\n"
                "(UC07 - Gerenciar Vagas, UC08 - Consultar Inscritos e UC09 - Avaliar Candidaturas)."
            ),
            font=("Segoe UI", 10),
            bg="white",
            fg="#475569",
            justify=tk.CENTER
        )
        lbl_sub.pack(pady=(0, 18))

        btn_acessar_recrutador = tk.Button(
            frm_box,
            text="🚀 Entrar como Recrutador de Teste",
            font=("Segoe UI", 11, "bold"),
            bg="#2563EB",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.iniciar_sessao_recrutador_teste
        )
        btn_acessar_recrutador.pack(fill=tk.X)

    def iniciar_sessao_recrutador_teste(self) -> None:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome, tipo_perfil FROM usuarios WHERE tipo_perfil = 'Recrutador' LIMIT 1"
            )
            rec = cursor.fetchone()
            if not rec:
                cursor.execute(
                    "INSERT INTO usuarios (nome, email, senha, tipo_perfil) VALUES (?, ?, ?, ?)",
                    ("Tech Solutions S.A.", "rh@techsolutions.com.br", "123456", PERFIL_RECRUTADOR)
                )
                conn.commit()
                rec_id = cursor.lastrowid
                dados = {"id": rec_id, "nome": "Tech Solutions S.A.", "tipo_perfil": PERFIL_RECRUTADOR}
            else:
                dados = dict(rec)

        self.navegar_por_perfil(dados)


if __name__ == "__main__":
    garantir_inicializacao_banco()
    app = AplicacaoPrincipal()
    app.mainloop()