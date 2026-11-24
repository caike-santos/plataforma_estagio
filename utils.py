import tkinter as tk
from tkinter import messagebox

DB_NAME = "plataforma.db"

PERFIL_CANDIDATO = "Candidato"
PERFIL_RECRUTADOR = "Recrutador"

STATUS_VAGA_ATIVA = "Ativa"
STATUS_VAGA_ENCERRADA = "Encerrada"
LISTA_STATUS_VAGA = [STATUS_VAGA_ATIVA, STATUS_VAGA_ENCERRADA]

STATUS_EM_ANALISE = "Em Análise"
STATUS_APROVADO = "Aprovado para Entrevista"
STATUS_REPROVADO = "Reprovado"
STATUS_FINALIZADO = "Finalizado"

LISTA_STATUS_CANDIDATURA = [
    STATUS_EM_ANALISE,
    STATUS_APROVADO,
    STATUS_REPROVADO,
    STATUS_FINALIZADO
]


def validar_campos_obrigatorios(campos: dict) -> bool:
    campos_validos = True

    for nome_campo, widget in campos.items():
        valor = ""
        if isinstance(widget, tk.Entry):
            valor = widget.get().strip()
        elif isinstance(widget, tk.Text):
            valor = widget.get("1.0", tk.END).strip()

        if not valor:
            campos_validos = False
            try:
                widget.config(
                    highlightbackground="#E53935",
                    highlightcolor="#E53935",
                     highlightthickness=2,
                    bg="#FFEBEE"
                )
            except tk.TclError:
                pass
        else:
            try:
                widget.config(
                    highlightbackground="#CCCCCC",
                    highlightcolor="#2196F3",
                    highlightthickness=1,
                    bg="white"
                )
            except tk.TclError:
                pass

    if not campos_validos:
        messagebox.showwarning(
            "Validação de Campos",
            "Preencha todos os campos obrigatórios"
        )

    return campos_validos


def resetar_estilo_campos(widgets: list) -> None:
    for widget in widgets:
        try:
            widget.config(
                highlightbackground="#CCCCCC",
                highlightcolor="#2196F3",
                highlightthickness=1,
                bg="white"
            )
        except tk.TclError:
            pass


def formatar_moeda(valor: float) -> str:
    try:
        valor_float = float(valor)
        texto = f"R$ {valor_float:,.2f}"
        return texto.replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"


def converter_moeda_para_float(valor_str: str) -> float | None:
    if not valor_str:
        return None
    limpo = valor_str.replace("R$", "").replace(" ", "").strip()
    if "," in limpo and "." in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    elif "," in limpo:
        limpo = limpo.replace(",", ".")
    try:
        numero = float(limpo)
        return numero if numero >= 0 else None
    except ValueError:
        return None