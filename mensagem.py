from email.message import EmailMessage
from email.utils import make_msgid, formatdate
from pathlib import Path
import pandas as pd
from html import escape


ASSUNTO = "Apresentação de Currículo – Perito Judicial"


def montar_assinatura_texto(remetente: dict) -> str:
    """
    Monta a assinatura em texto puro exibindo
    apenas os campos que estiverem preenchidos.
    """

    linhas = []

    campos = [
        ("nome_completo", ""),
        ("profissao", ""),
        ("registro_profissional", ""),
        ("telefone", "Telefone/WhatsApp: "),
        ("email_rem", "E-mail: "),
    ]

    for campo, prefixo in campos:
        valor = remetente.get(campo)

        if pd.notna(valor):
            texto = str(valor).strip()

            if texto:
                linhas.append(f"{prefixo}{texto}")

    return "\n".join(linhas)

def montar_assinatura_html(remetente: dict) -> str:
    """
    Monta a assinatura HTML exibindo apenas
    os campos que estiverem preenchidos.
    """

    assinatura = montar_assinatura_texto(remetente)

    return "<br>".join(
        escape(linha)
        for linha in assinatura.splitlines()
    )


def montar_mensagem(
    email_destinatario: str,
    remetente: dict,
) -> EmailMessage:
    """
    Monta o e-mail em texto + HTML e anexa
    o currículo do remetente.
    """

    assinatura_texto = montar_assinatura_texto(remetente)
    assinatura_html = montar_assinatura_html(remetente)

    corpo_texto = f"""Prezados(as) Senhores(as),

A presente comunicação possui caráter estritamente institucional e decorre da evolução dos mecanismos de gestão e nomeação de auxiliares da Justiça no âmbito do Poder Judiciário.

Nesse contexto, o subscritor encontra-se cadastrado no Portal de Auxiliares da Justiça, ferramenta integrada ao ecossistema do Programa Justiça 4.0, desenvolvido pelo Conselho Nacional de Justiça (CNJ), em parceria com o Tribunal de Justiça do Estado de São Paulo, por intermédio da plataforma Conecta.

Além da plataforma Conecta, o subscritor também possui cadastro ativo no CAJU - Cadastro de Auxiliares da Justiça do Tribunal de Justiça do Estado do Paraná, encontrando-se disponível para atuação nas áreas de sua qualificação técnica.

A presente apresentação busca, portanto, facilitar o acesso desse D. Juízo às informações relativas à qualificação profissional, às áreas de atuação e aos meios de contato do Perito, para eventual consulta ou nomeação em demandas que demandem prova técnica contábil, financeira ou correlata.

O subscritor possui ampla experiência na elaboração de Laudos Periciais, cálculos judiciais, respostas a quesitos e esclarecimentos periciais, com atuação em demandas cíveis, tributárias, previdenciárias e trabalhistas, bem como em processos submetidos à assistência judiciária gratuita, falências, recuperações judiciais e fases de liquidação e cumprimento de sentença.

Permanecem à disposição desse D. Juízo o currículo profissional e os documentos comprobatórios da qualificação técnica, caso entendidos necessários.

Sem mais para o momento, renova protestos de elevada estima e consideração.

Cordialmente,

{assinatura_texto}
"""

    corpo_html = f"""
<html>
  <body style="font-family: Arial, sans-serif; font-size: 14px; color: #222; line-height: 1.6;">

    <p>Prezados(as) Senhores(as),</p>

    <p>
      A presente comunicação possui caráter estritamente institucional e decorre
      da evolução dos mecanismos de gestão e nomeação de auxiliares da Justiça
      no âmbito do Poder Judiciário.
    </p>

    <p>
      Nesse contexto, o subscritor encontra-se cadastrado no Portal de Auxiliares
      da Justiça, ferramenta integrada ao ecossistema do Programa Justiça 4.0,
      desenvolvido pelo Conselho Nacional de Justiça (CNJ), em parceria com o
      Tribunal de Justiça do Estado de São Paulo, por intermédio da plataforma
      Conecta.
    </p>

    <p>
      Além da plataforma Conecta, o subscritor também possui cadastro ativo no
      CAJU - Cadastro de Auxiliares da Justiça do Tribunal de Justiça do Estado
      do Paraná, encontrando-se disponível para atuação nas áreas de sua
      qualificação técnica.
    </p>

    <p>
      A presente apresentação busca, portanto, facilitar o acesso desse D. Juízo
      às informações relativas à qualificação profissional, às áreas de atuação
      e aos meios de contato do Perito, para eventual consulta ou nomeação em
      demandas que demandem prova técnica contábil, financeira ou correlata.
    </p>

    <p>
      O subscritor possui ampla experiência na elaboração de Laudos Periciais,
      cálculos judiciais, respostas a quesitos e esclarecimentos periciais, com
      atuação em demandas cíveis, tributárias, previdenciárias e trabalhistas,
      bem como em processos submetidos à assistência judiciária gratuita,
      falências, recuperações judiciais e fases de liquidação e cumprimento
      de sentença.
    </p>

    <p>
      Permanecem à disposição desse D. Juízo o currículo profissional e os
      documentos comprobatórios da qualificação técnica, caso entendidos
      necessários.
    </p>

    <p>
      Sem mais para o momento, renova protestos de elevada estima e consideração.
    </p>

    <p>Cordialmente,</p>

    <p>
      {assinatura_html}
    </p>

  </body>
</html>
"""

    msg = EmailMessage()

    msg["Subject"] = ASSUNTO
    msg["From"] = remetente["email_rem"]
    msg["To"] = email_destinatario
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()

    msg["List-Unsubscribe"] = (
        f"<mailto:{remetente['email_rem']}?subject=unsubscribe>"
    )

    msg.set_content(corpo_texto)
    msg.add_alternative(corpo_html, subtype="html")

    valor_anexo = remetente.get("anexo")

    if pd.isna(valor_anexo) or not str(valor_anexo).strip():
        raise ValueError("O remetente selecionado está sem currículo informado.")

    pasta_projeto = Path(__file__).resolve().parent
    pasta_curriculos = pasta_projeto / "curriculos"

    caminho_anexo = pasta_curriculos / str(valor_anexo).strip()

    # Caminhos relativos serão considerados a partir deste arquivo.
    if not caminho_anexo.is_file():
        raise FileNotFoundError(
            f"Currículo não encontrado: {caminho_anexo}"
        )

    if not caminho_anexo.exists():
        raise FileNotFoundError(
            f"Currículo não encontrado: {caminho_anexo.resolve()}"
        )

    with open(caminho_anexo, "rb") as arquivo:
        dados_anexo = arquivo.read()

    msg.add_attachment(
        dados_anexo,
        maintype="application",
        subtype="pdf",
        filename=caminho_anexo.name,
    )

    return msg