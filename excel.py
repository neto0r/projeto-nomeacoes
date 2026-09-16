from datetime import datetime
from uuid import uuid4
from pathlib import Path
from tempfile import NamedTemporaryFile
import os

import pandas as pd
from openpyxl import load_workbook

ABA_CLIENTES = "Clientes"
ABA_REMETENTE = "Colaborador"
ABA_LOG = "Log"

COLUNAS_LOG = [
    "id_envio",
    "data_hora",
    "id_rem",
    "email_rem",
    "id_cliente",
    "email_cliente",
    "resultado",
]



# =================
# CLIENTES
# =================
def ler_clientes(caminho_arquivo):
    """
    Lê um arquivo Excel contendo informações de clientes e retorna um DataFrame do pandas.

    Parâmetros:
    caminho_arquivo (str): O caminho para o arquivo Excel.

    Retorna:
    pd.DataFrame: Um DataFrame contendo os dados dos clientes.
    """
    
    return pd.read_excel(
            caminho_arquivo,
            sheet_name=ABA_CLIENTES,
            engine='openpyxl',
            dtype={
                "id_cliente": int,
                "email_cliente": str,
                "estado": str,
                "status": str
            },    
        )

# =================
# REMETENTES
# =================
def ler_remetentes(caminho_arquivo):
    """
    Lê um arquivo Excel contendo informações do remetente e retorna um DataFrame do pandas.

    Parâmetros:
    caminho_arquivo (str): O caminho para o arquivo Excel.

    Retorna:
    pd.DataFrame: Um DataFrame contendo os dados do remetente.
    """
    return pd.read_excel(
            caminho_arquivo,
            sheet_name=ABA_REMETENTE,
            engine='openpyxl',
            dtype={
                "id_rem": int,
                "email_rem": str,
                "anexo": str,
                "status": str
            },
    )

# =================
# LOG
# =================
def ler_log(caminho_arquivo):
    """
    Lê um arquivo Excel contendo informações do Historico de envios e retorna um DataFrame do pandas.

    Parâmetros:
    caminho_arquivo (str): O caminho para o arquivo Excel.

    Retorna:
    pd.DataFrame: Um DataFrame contendo os dados do remetente.
    """
    log = pd.read_excel(
            caminho_arquivo,
            sheet_name=ABA_LOG,
            engine='openpyxl',
    )

    # Remove somente linhas sem nenhum valor nas colunas do log.
    log = log.dropna(
        how="all",
        subset=COLUNAS_LOG,
    ).reset_index(drop=True)

    # Linhas parcialmente preenchidas precisam ser corrigidas.
    ids_ausentes = (
        log["id_rem"].isna()
        | log["id_cliente"].isna()
    )

    if ids_ausentes.any():
        raise ValueError(
            "Existem registros no Log sem id_rem ou id_cliente."
        )

    return log




def registrar_envio(caminho_arquivo, id_rem, email_rem, id_cliente, email_cliente, resultado,):

    if resultado not in ("aceito_smtp", "falha", "indeterminado"):
        raise ValueError("Resultado de envio inválido")

    registro = {
        "id_envio": str(uuid4()),
        "data_hora": datetime.now(),
        "id_rem": id_rem,
        "email_rem": email_rem,
        "id_cliente": id_cliente,
        "email_cliente": email_cliente,
        "resultado": resultado,
    }

    caminho_arquivo = Path(caminho_arquivo)
    arquivo = load_workbook(caminho_arquivo)
    caminho_temporario = None

    try:
        aba_log = arquivo[ABA_LOG]

        cabecalhos = [celula.value for celula in aba_log[1]]

        if cabecalhos != COLUNAS_LOG:
            raise ValueError(
                "Os cabeçalhos da aba 'Log' não correspondem ao esperado."
            )

        if resultado == "aceito_smtp":
            aba_clientes = arquivo[ABA_CLIENTES]

            # Associa o nome de cada coluna ao seu número no Excel.
            colunas = {
                celula.value: celula.column
                for celula in aba_clientes[1]
            }

            obrigatorias = {
                "id_cliente",
                "qtd_enviados",
                "ultimo_envio", 
            }

            if not obrigatorias.issubset(colunas):
                raise ValueError("Faltam colunas de controle na aba de clientes")

            # O ID deve identificar exatamente uma linha
            linhas = [
                numero
                for numero in range(2, aba_clientes.max_row + 1)
                if aba_clientes.cell(
                    row=numero,
                    column=colunas["id_cliente"],
                ).value == id_cliente
            ]

            if len(linhas) != 1:
                raise ValueError(
                    f"O cliente {id_cliente} deve aparecer uma única vez."
                )

            numero_linha = linhas[0]

            celula_quantidade = aba_clientes.cell(
                row=numero_linha,
                column=colunas["qtd_enviados"],
            )

            quantidade_atual = celula_quantidade.value

            if quantidade_atual is None:
                quantidade_atual = 0

            quantidade_numerica = float(quantidade_atual)

            if (not quantidade_numerica.is_integer()
                or quantidade_numerica < 0):
                raise ValueError(f"qtd_enviados inválida para o cliente {id_cliente}.")

            celula_quantidade.value = int(quantidade_numerica) + 1

            celula_data = aba_clientes.cell(
                row=numero_linha,
                column=colunas["ultimo_envio"],
            )

            celula_data.value = registro["data_hora"]
            celula_data.number_format = "dd/mm/yyyy hh:mm:ss"

        numero_linha_log = proxima_linha_log(aba_log)

        for numero_coluna, nome_coluna in enumerate(COLUNAS_LOG, start=1):
            aba_log.cell(
                row=numero_linha_log,
                column=numero_coluna,
                value=registro[nome_coluna],
            )


        aba_log.cell(
            row=numero_linha_log,
            column=2,
        ).number_format = "dd/mm/yyyy hh:mm:ss"
        

        # Primeiro grava uma cópia completa na mesma pasta.
        with NamedTemporaryFile(
            dir=caminho_arquivo.parent,
            suffix=".xlsx",
            delete=False,
        ) as temporario:
            caminho_temporario = Path(temporario.name)

        arquivo.save(caminho_temporario)
        arquivo.close()

        # Só substitui o original depois que a cópia ofi gravada
        os.replace(caminho_temporario,caminho_arquivo)

    finally:
        arquivo.close()

        if (
            caminho_temporario is not None
            and caminho_temporario.exists()
        ):
            caminho_temporario.unlink()

    return registro


def proxima_linha_log(aba):
    # Procura de baixo para cima uma linha com algum conteúdo.
    for numero in range(aba.max_row, 1, -1):
        possui_conteudo = any(
            aba.cell(row=numero, column=coluna).value not in (None, "")
            for coluna in range(1, len(COLUNAS_LOG) + 1)
        )

        if possui_conteudo:
            return numero + 1

    # Se houver somente cabeçalhos, começa na linha 2.
    return 2