import json

import pandas as pd
import requests



# Configurações da API
base_url = "https://imunizacao-es.saude.gov.br/_search"
scroll_url = "https://imunizacao-es.saude.gov.br/_search/scroll"
username = "imunizacao_public"
password = "qlto5t&7r_@+#Tlstigi"
headers = {"Content-Type": "application/json"}


# Formatar a data para a API
data_inicio = "2025-06-06T00:00:00.000Z"
data_fim = "2025-06-06T23:59:59.999Z"
data_arquivo = "2025-06-06"

print(
    f"Buscando registros para a data: {data_arquivo} (formato API: {data_inicio} a {data_fim})"
)

# Usar a sintaxe de consulta JSON completa do Elasticsearch
url = f"{base_url}?scroll=1m"
payload = {
    "size": 1000,
    "query": {
        "bool": {
            "must": [
                {"term": {"estabelecimento_uf": "GO"}},
                {
                    "range": {
                        "vacina_dataAplicacao": {"gte": data_inicio, "lte": data_fim}
                    }
                },
            ]
        }
    },
}
all_records = []


# Função para processar requisições
def fetch_page(url, payload=None):
    try:
        response = requests.post(
            url,
            auth=(username, password),
            headers=headers,
            data=json.dumps(payload),
        )
        response.raise_for_status()  # Levanta exceção para erros HTTP
        return response.json()
    except requests.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None


# Requisição inicial
print("Buscando primeira página de registros...")
data = fetch_page(url, payload)
if not data:
    print("Falha na requisição inicial. Encerrando.")
    exit(1)

# Extraindo registros e scroll_id
scroll_id = data.get("_scroll_id")
records = data["hits"]["hits"]
all_records.extend([r["_source"] for r in records])
print(f"Primeira página: {len(records)} registros")

# Paginação com scroll
previous_scroll_id = None
page_count = 1
max_pages = 100  # Limite de segurança para evitar loops infinitos

while records and page_count < max_pages:
    payload_scroll = {"scroll": "1m", "scroll_id": scroll_id}
    print(f"Buscando próxima página ({page_count})...")
    data = fetch_page(scroll_url, payload_scroll)

    if not data:
        print("Falha ao buscar próxima página. Encerrando.")
        break

    # Verifica se o scroll_id é o mesmo da iteração anterior (indica fim da paginação)
    new_scroll_id = data.get("_scroll_id")
    if new_scroll_id == previous_scroll_id:
        print("Scroll ID repetido. Fim da paginação.")
        break

    previous_scroll_id = scroll_id
    scroll_id = new_scroll_id

    records = data["hits"]["hits"]

    # Para quando não houver mais registros
    if len(records) == 0:
        print("Todos os registros foram recuperados.")
        break

    all_records.extend([r["_source"] for r in records])
    print(
        f"Página {page_count}: {len(records)} registros, total acumulado: {len(all_records)}"
    )
    page_count += 1

# Exportando para CSV
if all_records:
    df = pd.DataFrame(all_records)
    output_file = f"vacinas_df_{data_arquivo}.csv"
    df.to_csv(output_file, index=False)
    print(
        f"Dados exportados para {output_file}. Total de registros: {len(all_records)}"
    )
else:
    print("Nenhum registro encontrado.")


def contar_ocorrencias_vacinas(data_inicio_str, data_fim_str, uf="GO"):
    """
    Função para contar ocorrências de vacinação em um período específico sem salvar em CSV.
    Apenas mostra os resultados na tela.

    Args:
        data_inicio_str (str): Data de início no formato 'YYYY-MM-DD'
        data_fim_str (str): Data de fim no formato 'YYYY-MM-DD'
        uf (str): Unidade federativa para busca (padrão: 'GO')
    """
    # Converter as datas para o formato da API
    data_inicio = f"{data_inicio_str}T00:00:00.000Z"
    data_fim = f"{data_fim_str}T23:59:59.999Z"

    print(
        f"\nContando registros de vacinação para {uf} no período: {data_inicio_str} a {data_fim_str}"
    )

    # Usar a sintaxe de consulta JSON completa do Elasticsearch
    url = f"{base_url}?scroll=1m"
    payload = {
        "size": 1000,  # Tamanho máximo permitido pela API
        "query": {
            "bool": {
                "must": [
                    {"term": {"estabelecimento_uf": uf}},
                    {
                        "range": {
                            "vacina_dataAplicacao": {
                                "gte": data_inicio,
                                "lte": data_fim,
                            }
                        }
                    },
                ]
            }
        },
    }

    # Contadores
    total_registros = 0
    total_paginas = 0

    # Requisição inicial
    print("Buscando primeira página de registros...")
    data = fetch_page(url, payload)
    if not data:
        print("Falha na requisição inicial. Encerrando.")
        return

    # Extraindo registros e scroll_id
    scroll_id = data.get("_scroll_id")
    records = data["hits"]["hits"]
    total_registros += len(records)
    total_paginas += 1

    print(f"Página 1: {len(records)} registros")
    
    # Verificar o total de hits reportado pela API
    total_hits = data["hits"].get("total", {})
    if isinstance(total_hits, dict):
        total_esperado = total_hits.get("value", 0)
    else:
        total_esperado = total_hits
        
    print(f"Total de registros esperados segundo a API: {total_esperado}")

    # Paginação com scroll
    page_count = 1
    max_pages = 11000  # Aumentando o limite para permitir mais páginas

    while records and page_count < max_pages:
        payload_scroll = {"scroll": "1m", "scroll_id": scroll_id}
        print(f"Buscando próxima página ({page_count + 1})...")
        data = fetch_page(scroll_url, payload_scroll)

        if not data:
            print("Falha ao buscar próxima página. Encerrando.")
            break

        # Atualiza o scroll_id para a próxima iteração
        scroll_id = data.get("_scroll_id")
        if not scroll_id:
            print("Scroll ID não encontrado. Fim da paginação.")
            break

        records = data["hits"]["hits"]

        # Para quando não houver mais registros
        if len(records) == 0:
            print("Todos os registros foram recuperados.")
            break

        total_registros += len(records)
        page_count += 1
        total_paginas += 1

        print(
            f"Página {page_count + 1}: {len(records)} registros, total acumulado: {total_registros}"
        )
        
        # Verificar se estamos próximos do total esperado
        if total_esperado > 0 and total_registros >= total_esperado:
            print(f"Atingido o total esperado de registros ({total_esperado}).")
            break

    # Resumo final
    print("\n=== RESUMO DA CONTAGEM ===")
    print(f"UF: {uf}")
    print(f"Período: {data_inicio_str} a {data_fim_str}")
    print(f"Total de páginas processadas: {total_paginas}")
    print(f"Total de registros de vacinação: {total_registros}")
    if total_esperado > 0:
        print(f"Total esperado segundo a API: {total_esperado}")
        if total_registros < total_esperado:
            print(f"ATENÇÃO: Foram recuperados apenas {total_registros}/{total_esperado} registros!")
    print("=======================\n")

    # Retorna o total para possível uso em outras funções
    return total_registros


def obter_dados_vacinacao(data_inicio_str, data_fim_str, uf="GO", nome_arquivo=None):
    """
    Função para obter dados de vacinação em um período específico e salvá-los em CSV.
    
    Args:
        data_inicio_str (str): Data de início no formato 'YYYY-MM-DD'
        data_fim_str (str): Data de fim no formato 'YYYY-MM-DD'
        uf (str): Unidade federativa para busca (padrão: 'GO')
        nome_arquivo (str, opcional): Nome do arquivo CSV para salvar os dados.
                                     Se None, será gerado automaticamente.
    
    Returns:
        pandas.DataFrame: DataFrame com os dados de vacinação
        str: Caminho do arquivo CSV salvo
    """
    # Converter as datas para o formato da API
    data_inicio = f"{data_inicio_str}T00:00:00.000Z"
    data_fim = f"{data_fim_str}T23:59:59.999Z"
    
    print(f"\nObtendo dados de vacinação para {uf} no período: {data_inicio_str} a {data_fim_str}")
    
    # Usar a sintaxe de consulta JSON completa do Elasticsearch
    url = f"{base_url}?scroll=1m"
    payload = {
        "size": 1000,  # Tamanho máximo permitido pela API
        "query": {
            "bool": {
                "must": [
                    {"term": {"estabelecimento_uf": uf}},
                    {
                        "range": {
                            "vacina_dataAplicacao": {
                                "gte": data_inicio,
                                "lte": data_fim,
                            }
                        }
                    },
                ]
            }
        },
    }
    
    # Lista para armazenar todos os registros
    all_records = []
    total_paginas = 0
    
    # Requisição inicial
    print("Buscando primeira página de registros...")
    data = fetch_page(url, payload)
    if not data:
        print("Falha na requisição inicial. Encerrando.")
        return None, None
    
    # Extraindo registros e scroll_id
    scroll_id = data.get("_scroll_id")
    records = data["hits"]["hits"]
    all_records.extend([r["_source"] for r in records])
    total_paginas += 1
    
    print(f"Página 1: {len(records)} registros")
    
    # Verificar o total de hits reportado pela API
    total_hits = data["hits"].get("total", {})
    if isinstance(total_hits, dict):
        total_esperado = total_hits.get("value", 0)
    else:
        total_esperado = total_hits
        
    print(f"Total de registros esperados segundo a API: {total_esperado}")
    
    # Paginação com scroll
    page_count = 1
    max_pages = 500  # Aumentando o limite para permitir mais páginas
    
    while records and page_count < max_pages:
        payload_scroll = {"scroll": "1m", "scroll_id": scroll_id}
        print(f"Buscando próxima página ({page_count + 1})...")
        data = fetch_page(scroll_url, payload_scroll)
        
        if not data:
            print("Falha ao buscar próxima página. Encerrando.")
            break
        
        # Atualiza o scroll_id para a próxima iteração
        scroll_id = data.get("_scroll_id")
        if not scroll_id:
            print("Scroll ID não encontrado. Fim da paginação.")
            break
        
        records = data["hits"]["hits"]
        
        # Para quando não houver mais registros
        if len(records) == 0:
            print("Todos os registros foram recuperados.")
            break
        
        all_records.extend([r["_source"] for r in records])
        page_count += 1
        total_paginas += 1
        
        print(f"Página {page_count + 1}: {len(records)} registros, total acumulado: {len(all_records)}")
        
        # Verificar se estamos próximos do total esperado
        if total_esperado > 0 and len(all_records) >= total_esperado:
            print(f"Atingido o total esperado de registros ({total_esperado}).")
            break
    
    # Criar DataFrame com os dados
    if all_records:
        df = pd.DataFrame(all_records)
        
        # Gerar nome de arquivo se não foi fornecido
        if nome_arquivo is None:
            nome_arquivo = f"vacinas_{uf}_{data_inicio_str}_a_{data_fim_str}.csv"
        
        # Criar diretório para dados se não existir
        import os
        diretorio_dados = os.path.join(os.path.dirname(__file__), "dados_vacinacao")
        if not os.path.exists(diretorio_dados):
            os.makedirs(diretorio_dados)
        
        # Caminho completo do arquivo
        caminho_arquivo = os.path.join(diretorio_dados, nome_arquivo)
        
        # Salvar DataFrame em CSV
        df.to_csv(caminho_arquivo, index=False)
        
        print(f"\nDados salvos com sucesso em: {caminho_arquivo}")
        print(f"Total de registros: {len(all_records)}")
        if total_esperado > 0:
            print(f"Total esperado segundo a API: {total_esperado}")
            if len(all_records) < total_esperado:
                print(f"ATENÇÃO: Foram recuperados apenas {len(all_records)}/{total_esperado} registros!")
        
        # Mostrar as primeiras linhas do DataFrame
        print("\nPrimeiras linhas do DataFrame:")
        print(df.head())
        
        # Mostrar informações sobre as colunas
        print("\nInformações sobre as colunas:")
        print(f"Número de colunas: {len(df.columns)}")
        print(f"Colunas: {', '.join(df.columns)}")
        
        return df, caminho_arquivo
    else:
        print("Nenhum registro encontrado.")
        return None, None


def obter_dados_vacinacao_periodo(data_inicio_str, data_fim_str, uf="GO", intervalo_dias=30):
    """
    Função para obter dados de vacinação para um período mais amplo, dividindo-o em intervalos menores
    para evitar sobrecarregar a API.
    
    Args:
        data_inicio_str (str): Data de início no formato 'YYYY-MM-DD'
        data_fim_str (str): Data de fim no formato 'YYYY-MM-DD'
        uf (str): Unidade federativa para busca (padrão: 'GO')
        intervalo_dias (int): Número de dias para cada intervalo (padrão: 30 dias)
    
    Returns:
        pandas.DataFrame: DataFrame combinado com todos os dados de vacinação
        list: Lista de caminhos dos arquivos CSV salvos
    """
    from datetime import datetime, timedelta
    import pandas as pd
    import os
    
    # Converter strings de data para objetos datetime
    data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d")
    data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d")
    
    # Lista para armazenar DataFrames e caminhos de arquivos
    dfs = []
    arquivos = []
    
    # Diretório para dados combinados
    diretorio_dados = os.path.join(os.path.dirname(__file__), "dados_vacinacao")
    if not os.path.exists(diretorio_dados):
        os.makedirs(diretorio_dados)
    
    # Nome do arquivo combinado
    arquivo_combinado = os.path.join(diretorio_dados, f"vacinas_{uf}_{data_inicio_str}_a_{data_fim_str}_combinado.csv")
    
    print(f"\nObtendo dados de vacinação para {uf} no período: {data_inicio_str} a {data_fim_str}")
    print(f"Dividindo em intervalos de {intervalo_dias} dias")
    
    # Dividir o período em intervalos menores
    data_atual = data_inicio
    total_registros = 0
    
    while data_atual < data_fim:
        # Calcular a data de fim do intervalo atual
        data_fim_intervalo = data_atual + timedelta(days=intervalo_dias)
        
        # Garantir que não ultrapasse a data final
        if data_fim_intervalo > data_fim:
            data_fim_intervalo = data_fim
        
        # Converter para string no formato YYYY-MM-DD
        data_atual_str = data_atual.strftime("%Y-%m-%d")
        data_fim_intervalo_str = data_fim_intervalo.strftime("%Y-%m-%d")
        
        print(f"\nProcessando intervalo: {data_atual_str} a {data_fim_intervalo_str}")
        
        # Obter dados para o intervalo atual
        df, arquivo = obter_dados_vacinacao(
            data_atual_str, 
            data_fim_intervalo_str, 
            uf, 
            f"vacinas_{uf}_{data_atual_str}_a_{data_fim_intervalo_str}.csv"
        )
        
        # Adicionar às listas se houver dados
        if df is not None:
            dfs.append(df)
            arquivos.append(arquivo)
            total_registros += len(df)
        
        # Avançar para o próximo intervalo
        data_atual = data_fim_intervalo + timedelta(days=1)
    
    # Combinar todos os DataFrames
    if dfs:
        df_combinado = pd.concat(dfs, ignore_index=True)
        
        # Salvar DataFrame combinado
        df_combinado.to_csv(arquivo_combinado, index=False)
        
        print(f"\nTodos os dados foram combinados e salvos em: {arquivo_combinado}")
        print(f"Total de registros combinados: {total_registros}")
        print(f"Total de arquivos individuais: {len(arquivos)}")
        
        return df_combinado, arquivos
    else:
        print("Nenhum dado foi encontrado para o período especificado.")
        return None, []


# Exemplo de uso das funções
if __name__ == "__main__":
    # Primeiro, vamos contar o número de registros por ano para ter uma ideia do volume de dados
    print("\n=== Contagem de registros de vacinação por ano em Goiás ===\n")
    
    for ano in range(2021, 2025):
        total = contar_ocorrencias_vacinas(f"{ano}-01-01", f"{ano}-12-31", "GO")
        print(f"Total de registros para {ano}: {total}\n")
