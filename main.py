import os
from pathlib import Path

from dotenv import load_dotenv

from excel import ler_clientes, ler_remetentes, ler_log
from selecao import selecionar_candidatos, montar_lista_final
from envios import executar_lote


PASTA_PROJETO = Path(__file__).resolve().parent
CAMINHO_ARQUIVO = PASTA_PROJETO / "clientes.xlsx"


def obter_senha(id_rem):
    nome_variavel = f"REMETENTE_{id_rem}_SENHA"
    senha = os.getenv(nome_variavel)

    if not senha:
        raise ValueError(
            f"Preencha {nome_variavel} no arquivo .env."
        )

    return senha


def main():
    load_dotenv(PASTA_PROJETO / ".env")

    df_clientes = ler_clientes(CAMINHO_ARQUIVO)
    df_remetentes = ler_remetentes(CAMINHO_ARQUIVO)
    log = ler_log(CAMINHO_ARQUIVO)

    # Mantém os tipos dos IDs compatíveis com os cadastros.
    log["id_rem"] = log["id_rem"].astype(
        df_remetentes["id_rem"].dtype
    )
    log["id_cliente"] = log["id_cliente"].astype(
        df_clientes["id_cliente"].dtype
    )

    # Um resultado incerto precisa ser conferido antes de novo lote.
    if log["resultado"].eq("indeterminado").any():
        raise ValueError(
            "Existe envio indeterminado no Log. "
            "Confira e resolva esse registro antes de continuar."
        )

    remetentes_disponiveis = df_remetentes.loc[
        df_remetentes["status"].isin(["ATIVO", "TESTE"])
    ]

    print("\nRemetentes disponíveis:")
    print(
        remetentes_disponiveis[
            ["id_rem", "nome_completo", "email_rem"]
        ].to_string(index=False)
    )

    id_rem = int(input("\nID do remetente: "))

    selecionado = remetentes_disponiveis.loc[
        remetentes_disponiveis["id_rem"] == id_rem
    ]

    if len(selecionado) != 1:
        raise ValueError(
            "O ID deve identificar exatamente um remetente disponível."
        )

    remetente = selecionado.to_dict(orient="records")[0]
    senha = obter_senha(id_rem)

    quantidade = int(input("Quantidade de clientes para teste: "))

    estados = [
        estado.strip().upper()
        for estado in input("Estados separados por vírgula: ").split(",")
        if estado.strip()
    ]

    if not estados:
        raise ValueError("Informe pelo menos um estado.")

    candidatos = selecionar_candidatos(
        clientes=df_clientes,
        log=log,
        id_rem=id_rem,
        quantidade=quantidade,
        estados=estados,
        status="TESTE",
    )

    clientes_finais = montar_lista_final(candidatos)

    if not clientes_finais:
        print("Nenhum cliente disponível para esses filtros.")
        return

    print(f"\nRemetente: {remetente['email_rem']}")
    print(f"Currículo: {remetente.get('anexo')}")
    print(f"Quantidade final: {len(clientes_finais)}")

    print("\nDestinatários:")
    for cliente in clientes_finais:
        print(f"- {cliente['id_cliente']}: {cliente['email_cliente']}")

    confirmacao = input(
        "\nDigite ENVIAR para realizar os envios: "
    ).strip()

    if confirmacao != "ENVIAR":
        print("Envio cancelado.")
        return

    resumo = executar_lote(
        clientes=clientes_finais,
        remetente=remetente,
        senha=senha,
        caminho_arquivo=CAMINHO_ARQUIVO,
    )

    print("\nResultado do lote:")
    for resultado, quantidade in resumo.items():
        print(f"{resultado}: {quantidade}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError) as erro:
        print(f"\nExecução interrompida: {erro}")