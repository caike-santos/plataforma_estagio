"""Script para popular o banco de dados SQLite com dados mock realistas para testes e apresentação."""

import hashlib
from pathlib import Path
import sqlite3

from database import DB_PATH, inicializar_banco, obter_conexao


def gerar_hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def popular_dados_mock(caminho_db: Path = DB_PATH) -> None:
    inicializar_banco(caminho_db)
    senha_padrao = gerar_hash_senha("123456")

    usuarios_mock = [
        # Recrutadores
        ("Tech Solutions S.A.", "rh@techsolutions.com.br", senha_padrao, "Recrutador"),
        ("Inova Data & Analytics", "talentos@inova.com.br", senha_padrao, "Recrutador"),
        # Candidatos
        ("Carlos Eduardo", "cadu@email.com", senha_padrao, "Candidato"),
        ("Mariana Costa Silva", "mariana@email.com", senha_padrao, "Candidato"),
        ("Lucas Ferreira Mendes", "lucas@email.com", senha_padrao, "Candidato"),
        ("Beatriz Almeida Souza", "beatriz@email.com", senha_padrao, "Candidato"),
    ]

    with obter_conexao(caminho_db) as conn:
        for nome, email, senha_hash, tipo_perfil in usuarios_mock:
            conn.execute(
                """
                INSERT INTO usuarios (nome, email, senha, tipo_perfil)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    nome = excluded.nome,
                    senha = excluded.senha,
                    tipo_perfil = excluded.tipo_perfil
                """,
                (nome, email, senha_hash, tipo_perfil),
            )

        mapa_usuarios: dict[str, int] = {
            linha["email"]: int(linha["id"])
            for linha in conn.execute("SELECT id, email FROM usuarios").fetchall()
        }

        perfis_mock = [
            (
                mapa_usuarios["cadu@email.com"],
                "Análise e Desenvolvimento de Sistemas",
                "Estácio",
                "4º Período",
                "Python, Tkinter, SQLite, SQL, Git, POO",
                "Estudante focado em desenvolvimento desktop e backend em Python, com projetos práticos utilizando arquitetura DAO e bancos relacionais.",
            ),
            (
                mapa_usuarios["mariana@email.com"],
                "Ciência da Computação",
                "UFMG",
                "5º Período",
                "Python, Pandas, SQL, Power BI, Estatística",
                "Apaixonada por análise de dados e automação de processos. Experiência em iniciação científica com processamento de dados em Python.",
            ),
            (
                mapa_usuarios["lucas@email.com"],
                "Engenharia de Software",
                "PUC",
                "3º Período",
                "Python, JavaScript, HTML/CSS, Git, Testes Automatizados",
                "Busco primeira oportunidade de estágio em desenvolvimento de software. Facilidade com trabalho em equipe e metodologias ágeis (Scrum/RAD).",
            ),
            (
                mapa_usuarios["beatriz@email.com"],
                "Sistemas de Informação",
                "USP",
                "6º Período",
                "SQL, Python, Linux, Redes, Segurança da Informação",
                "Monitora da disciplina de Banco de Dados. Experiência acadêmica em modelagem relacional, consultas SQL otimizadas e administração de sistemas.",
            ),
        ]

        for usuario_id, curso, instituicao, periodo, habilidades, resumo in perfis_mock:
            conn.execute(
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
                (usuario_id, curso, instituicao, periodo, habilidades, resumo),
            )

        rec_tech = mapa_usuarios["rh@techsolutions.com.br"]
        rec_inova = mapa_usuarios["talentos@inova.com.br"]

        vagas_mock = [
            (
                rec_tech,
                "Estágio em Desenvolvimento Python Desktop",
                "Atuar no desenvolvimento e manutenção de aplicações desktop internas utilizando Python, Tkinter e banco de dados SQLite3 seguindo a metodologia RAD.",
                "São Paulo - SP (Híbrido)",
                1800.00,
                "Cursando ADS, Ciência da Computação ou áreas correlatas; Lógica de programação; Python básico/intermediário e noções de SQL.",
                "Ativa",
            ),
            (
                rec_tech,
                "Estágio em Engenharia de Dados & SQL",
                "Apoiar a equipe de dados na criação de rotinas ETL em Python, modelagem de tabelas relacionais e elaboração de relatórios gerenciais.",
                "Remoto",
                2100.00,
                "Conhecimento em SQL (JOINs, agregações), Python e Git. Desejável familiaridade com bancos relacionais.",
                "Ativa",
            ),
            (
                rec_tech,
                "Estágio em Qualidade de Software (QA)",
                "Elaboração de casos de teste, validação de requisitos de casos de uso (UC) e execução de testes funcionais em sistemas desktop e web.",
                "Rio de Janeiro - RJ",
                1550.00,
                "Atenção a detalhes, documentação de bugs, noções de banco de dados e lógica de programação.",
                "Ativa",
            ),
            (
                rec_inova,
                "Estágio em Business Intelligence & Analytics",
                "Construção de painéis de indicadores, consultas em bancos de dados SQL e suporte na análise de métricas de recrutamento e operações.",
                "Belo Horizonte - MG",
                1950.00,
                "Cursando Sistemas de Informação, Ciência da Computação ou Engenharia; SQL intermediário e Python para análise de dados.",
                "Ativa",
            ),
            (
                rec_inova,
                "Estágio em Suporte Técnico e Infraestrutura",
                "Atendimento a usuários internos, configuração de ambientes Python no Windows e manutenção preventiva de estações de trabalho.",
                "Curitiba - PR",
                1400.00,
                "Conhecimento em Windows, variáveis de ambiente (PATH), redes básicas e disposição para aprender.",
                "Encerrada",
            ),
        ]

        vagas_existentes = {
            linha["titulo"]: int(linha["id"])
            for linha in conn.execute("SELECT id, titulo FROM vagas").fetchall()
        }

        for rec_id, titulo, descricao, localidade, bolsa, requisitos, status in vagas_mock:
            if titulo not in vagas_existentes:
                cursor = conn.execute(
                    """
                    INSERT INTO vagas (
                        recrutador_id, titulo, descricao, localidade,
                        bolsa_auxilio, requisitos, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (rec_id, titulo, descricao, localidade, bolsa, requisitos, status),
                )
                vagas_existentes[titulo] = int(cursor.lastrowid or 0)

        inscricoes_mock = [
            (
                mapa_usuarios["cadu@email.com"],
                vagas_existentes["Estágio em Desenvolvimento Python Desktop"],
                "Aprovado para Entrevista",
            ),
            (
                mapa_usuarios["cadu@email.com"],
                vagas_existentes["Estágio em Engenharia de Dados & SQL"],
                "Em Análise",
            ),
            (
                mapa_usuarios["mariana@email.com"],
                vagas_existentes["Estágio em Desenvolvimento Python Desktop"],
                "Em Análise",
            ),
            (
                mapa_usuarios["mariana@email.com"],
                vagas_existentes["Estágio em Business Intelligence & Analytics"],
                "Aprovado para Entrevista",
            ),
            (
                mapa_usuarios["lucas@email.com"],
                vagas_existentes["Estágio em Desenvolvimento Python Desktop"],
                "Reprovado",
            ),
            (
                mapa_usuarios["lucas@email.com"],
                vagas_existentes["Estágio em Qualidade de Software (QA)"],
                "Em Análise",
            ),
            (
                mapa_usuarios["beatriz@email.com"],
                vagas_existentes["Estágio em Engenharia de Dados & SQL"],
                "Finalizado",
            ),
        ]

        for candidato_id, vaga_id, status_insc in inscricoes_mock:
            conn.execute(
                """
                INSERT INTO inscricoes (candidato_id, vaga_id, status)
                VALUES (?, ?, ?)
                ON CONFLICT(candidato_id, vaga_id) DO UPDATE SET
                    status = excluded.status
                """,
                (candidato_id, vaga_id, status_insc),
            )

    print(f"Dados mock inseridos com sucesso em: {caminho_db}")


if __name__ == "__main__":
    popular_dados_mock()
