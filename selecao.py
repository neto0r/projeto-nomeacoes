import pandas as pd


def selecionar_candidatos(
        clientes,
        log,
        id_rem,
        quantidade,
        estados,
        status="TESTE",
):
    if quantidade <= 0:
        raise ValueError("A quantidade de clientes deve ser maior que zero.")

    if status not in ("ATIVO", "TESTE"):
        raise ValueError("O status deve ser 'ATIVO' ou 'TESTE'.")

    # 1. Seleciona os clentes dos estados e do status informados.
    filtro = (
        clientes['estado'].isin(estados) &
        (clientes['status'] == status)
    )

    candidatos = clientes.loc[filtro].copy()

    candidatos["ultimo_envio"] = pd.to_datetime(candidatos["ultimo_envio"], errors='raise', dayfirst=True)

    # 2. Consulta o Log (historico) somente os envios aceitos do remetente escolhido.
    
    filtro_historico = (
        (log["id_rem"] == id_rem) &
        (log["resultado"] == "aceito_smtp")
    )

    historico = log.loc[
        filtro_historico,
        ["id_cliente","data_hora"],
    ].copy()

    historico["data_hora"] = pd.to_datetime(
        historico["data_hora"],
        errors="raise",
        dayfirst=True,
    )

    # 3. Encontra o último envio desse remetente para cada cliente.
    if historico.empty:
        candidatos["ultimo_envio_remetente"] = pd.NaT

    else:
        ultimos_envios = (
            historico.groupby("id_cliente")["data_hora"].max()
        )

        candidatos["ultimo_envio_remetente"] = (
            candidatos["id_cliente"].map(ultimos_envios)
        )

    # 4. Marca os clientes que nunca receberam de nenhum remetente.
    candidatos["nunca_recebeu"] = candidatos["ultimo_envio"].isna()

    # 5. Aplica a ordem de prioridade.
    candidatos = candidatos.sort_values(
        by=[
            "nunca_recebeu",
            "ultimo_envio_remetente",
            "ultimo_envio",
        ],
        ascending=[False,True,True],
        na_position="first",
        kind="stable",
    )

    # 6. Limita a quantidade e remove as colunas auxiliares.
    selecionados = candidatos.head(quantidade).drop(columns=["nunca_recebeu","ultimo_envio_remetente"])

    return selecionados.to_dict(orient="records")



def montar_lista_final(candidatos):
    lista_final = []
    ids_adicionados = set()
    emails_adicionados = set()

    for cliente in candidatos:
        id_cliente = cliente["id_cliente"]
        email_cliente = cliente["email_cliente"]

        if pd.isna(id_cliente) or pd.isna(email_cliente):
            raise ValueError("Existe candidato sem ID ou e-mail.")

        email_cliente = str(email_cliente).strip()

        if not email_cliente:
            raise ValueError(f"Cliente {id_cliente} sem e-mail.")

        # Para duplicidades, adotamos comparação sem diferenciar
        # letras maiúsculas de minúsculas no endereço.
        chave_email = email_cliente.casefold()

        if (
            id_cliente in ids_adicionados
            or chave_email in emails_adicionados
        ):
            continue

        cliente_final = cliente.copy()
        cliente_final["email_cliente"] = email_cliente

        lista_final.append(cliente_final)
        ids_adicionados.add(id_cliente)
        emails_adicionados.add(chave_email)

    return lista_final

