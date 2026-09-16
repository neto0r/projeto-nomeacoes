import smtplib

from mensagem import montar_mensagem
from send_mail import enviar_email
from excel import registrar_envio


def executar_lote(
    clientes,
    remetente,
    senha,
    caminho_arquivo,
):
    resumo = {
        "aceito_smtp": 0,
        "falha": 0,
        "indeterminado": 0,
        "nao_processados": len(clientes),
    }

    # Prepara todas as mensagens antes de enviar a primeira.
    mensagens = [
        montar_mensagem(
            email_destinatario=cliente["email_cliente"],
            remetente=remetente,
        )
        for cliente in clientes
    ]

    for cliente, mensagem in zip(clientes, mensagens):
        interromper = False

        try:
            enviar_email(
                mensagem=mensagem,
                remetente=remetente["email_rem"],
                senha=senha,
            )

        except smtplib.SMTPAuthenticationError as erro: 
            resultado = "falha"
            interromper = True

            resposta = erro.smtp_error

            if isinstance(resposta,bytes):
                resposta = resposta.decode("utf-8",errors="replace")

            print("Autenticação recusada pelo servidor.")
            print(f"Código SMTP: {erro.smtp_code}")
            print(f"Resposta: {resposta}")

        except smtplib.SMTPRecipientsRefused:
            resultado = "falha"
            print(f"Destinatário recusado: {cliente['email_cliente']}")

        except (
            smtplib.SMTPSenderRefused,
            smtplib.SMTPConnectError,
            smtplib.SMTPHeloError,
            smtplib.SMTPNotSupportedError,
        ) as erro:
            resultado = "falha"
            interromper = True
            print(f"Falha na conexão ou no remetente: {erro}")

        except smtplib.SMTPDataError:
            resultado = "falha"
            interromper = True
            print("O servidor recusou o conteúdo da mensagem.")

        except (smtplib.SMTPException, OSError):
            # A função de envio não informa em qual etapa
            # a conexão falhou. Evitamos presumir que não enviou.
            resultado = "indeterminado"
            interromper = True
            print(
                "Não foi possível confirmar o resultado. "
                "Confira antes de reenviar."
            )

        else:
            resultado = "aceito_smtp"

        # Este tratamento é separado do SMTP.
        try:
            registrar_envio(
                caminho_arquivo=caminho_arquivo,
                id_rem=remetente["id_rem"],
                email_rem=remetente["email_rem"],
                id_cliente=cliente["id_cliente"],
                email_cliente=cliente["email_cliente"],
                resultado=resultado,
            )

        except Exception as erro:
            print(
                "Não foi possível salvar o resultado:\n"
                f"Remetente: {remetente['id_rem']}\n"
                f"Cliente: {cliente['id_cliente']}\n"
                f"E-mail: {cliente['email_cliente']}\n"
                f"Resultado SMTP: {resultado}"
            )

            raise RuntimeError(
                "Lote interrompido por falha na gravação. "
                "Confira o envio e reconcilie a planilha antes "
                "de executar novamente."
            ) from erro

        resumo[resultado] += 1
        resumo["nao_processados"] -= 1

        print(f"{cliente['email_cliente']}: {resultado}")

        if interromper:
            break

    return resumo