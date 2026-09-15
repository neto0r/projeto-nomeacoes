import pandas as pd
from excel import ler_clientes, ler_remetente, ler_log
from selecao import selecionar_candidatos


caminho_arquivo = r"C:\Users\AdolfoRéss\OneDrive - Grupo Marista\Neto\Projeto nomeações\clientes.xlsx"

df_remetente = ler_remetente(caminho_arquivo)
df_clientes = ler_clientes(caminho_arquivo)
log = ler_log(caminho_arquivo)

print(log)


candidatos = selecionar_candidatos(df_clientes,log,1,50,["PR","SC","SP"],"TESTE")


print (candidatos)

