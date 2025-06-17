import requests
from bs4 import BeautifulSoup   
import pandas as pd
import os
import re

# Configurar a URL base e os parâmetros como query parameters
url_base = "https://indicadores.saude.go.gov.br/pentaho/plugin/cda/api/doQuery"

def processar_casos_srag(df):
    """Processa a coluna 'casos' para extrair os valores de cada tipo de SRAG e remove a coluna original"""
    # Verificar se a coluna 'casos' existe no DataFrame
    if 'casos' not in df.columns:
        print("Coluna 'casos' não encontrada no DataFrame")
        return df
    
    # Tipos de SRAG que queremos extrair
    tipos_srag = [
        "SRAG EM INVESTIGACAO",
        "SRAG NAO ESPECIFICADO",
        "SRAG POR COVID19",
        "SRAG POR INFLUENZA",
        "SRAG POR OUTRO AGENTE ETIOLOGICO",
        "SRAG POR OUTRO VIRUS RESPIRATORIO"
    ]
    
    # Criar colunas para cada tipo de SRAG com valor padrão 0
    for tipo in tipos_srag:
        coluna = tipo.replace(" ", "_").lower()
        df[coluna] = 0
    
    # Função para extrair os valores de cada tipo de SRAG da string
    def extrair_valores_srag(casos_str):
        if pd.isna(casos_str) or casos_str is None:
            return {}
        
        valores = {}
        # Procurar padrões como "SRAG EM INVESTIGACAO:68" na string
        for tipo in tipos_srag:
            padrao = f"{tipo}:([0-9]+)"
            match = re.search(padrao, casos_str)
            if match:
                valores[tipo.replace(" ", "_").lower()] = int(match.group(1))
        return valores
    
    # Aplicar a função em cada linha da coluna 'casos'
    for idx, row in df.iterrows():
        if pd.notna(row['casos']):
            valores = extrair_valores_srag(row['casos'])
            for tipo, valor in valores.items():
                df.at[idx, tipo] = valor
    
    # Remover a coluna 'casos' original após extrair os dados
    df = df.drop(columns=['casos'])
    
    return df

def buscar_srag_goias(dataAccessId, paramAno):
    params = {
        "path": "/srag/paineis/painel.cda",
        "dataAccessId": dataAccessId,
        "paramAno": paramAno,
        "paramSrag": "SRAG EM INVESTIGACAO,SRAG NAO ESPECIFICADO,SRAG POR COVID19,SRAG POR INFLUENZA,SRAG POR OUTRO AGENTE ETIOLOGICO,SRAG POR OUTRO VIRUS RESPIRATORIO"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    # Fazer a requisição usando params em vez de data
    response = requests.get(url_base, headers=headers, params=params)

    # Verificar o status da resposta
    print(f"Status code: {response.status_code}")

    # Tentar decodificar o JSON apenas se a resposta for bem-sucedida
    if response.status_code == 200:
        try:
            data_json = response.json()
            
            # Extrair os nomes das colunas da metadata
            column_names = [col['colName'] for col in data_json['metadata']]
        
            # Extrair os dados do resultset
            resultset = data_json['resultset']
        
            # Criar o DataFrame com os nomes de colunas corretos
            df = pd.DataFrame(resultset, columns=column_names)
            
            # Processar a coluna 'casos' para extrair os valores de cada tipo de SRAG
            df = processar_casos_srag(df)
        
            # Exibir as primeiras linhas do DataFrame para verificação
            print(df.head())
        
            # Salvar o DataFrame em um arquivo CSV com o nome definido em dataAccessId+paramAno.csv
            filename = f"{params['dataAccessId']}_{params['paramAno']}.csv" 
            if not os.path.exists(os.path.join(os.path.dirname(__file__), "dados")):
                os.makedirs(os.path.join(os.path.dirname(__file__), "dados"))
            caminho_arquivo = os.path.join(os.path.dirname(__file__), "dados", filename)
            df.to_csv(caminho_arquivo, index=False)
            print(f"Arquivo {filename} salvo com sucesso!")
            
            return df
        except ValueError as e:
            print(f"Erro ao processar JSON: {e}")
            return None
    else:
        print(f"Erro na requisição para {params['dataAccessId']} e {params['paramAno']}: {response.status_code}")
        return None

def gerar_resumo(ano):
    """Gera um resumo dos dados de SRAG para o ano especificado"""
    print(f"\n=== Resumo dos dados de SRAG em Goiás para {ano} ===")
    
    # Buscar dados de municípios, regiões e macrorregiões
    df_municipios = buscar_srag_goias("dsCasosMunicipios", ano)
    df_regioes = buscar_srag_goias("dsCasosRegioes", ano)
    df_macrorregioes = buscar_srag_goias("dsCasosMacrorregioes", ano)
    
    if df_macrorregioes is not None:
        # Calcular o total de casos por tipo de SRAG nas macrorregiões
        tipos_srag = [
            "srag_em_investigacao",
            "srag_nao_especificado",
            "srag_por_covid19",
            "srag_por_influenza",
            "srag_por_outro_agente_etiologico",
            "srag_por_outro_virus_respiratorio"
        ]
        
        print("\nTotal de casos por tipo de SRAG nas macrorregiões:")
        for tipo in tipos_srag:
            total = df_macrorregioes[tipo].sum()
            print(f"{tipo.replace('_', ' ').upper()}: {total}")
        
        # Calcular o total de notificações
        total_notificacoes = df_macrorregioes['notificacoes'].sum()
        print(f"\nTotal de notificações: {total_notificacoes}")
        
        # Calcular a macrorregião com maior índice
        max_indice = df_macrorregioes.loc[df_macrorregioes['indice'].idxmax()]
        print(f"\nMacrorregião com maior índice: {max_indice['local']} ({max_indice['indice']:.2f})")

def extrair_todos_dados_srag():
    """Extrai todos os dados de SRAG disponíveis na API para todos os anos"""
    # Anos disponíveis na API (ajuste conforme necessário)
    anos = ["2020", "2021", "2022", "2023", "2024", "2025"]
    
    # Endpoints disponíveis
    endpoints = [
        "dsCasosMunicipios",
        "dsCasosRegioes",
        "dsCasosMacrorregioes"
    ]
    
    print("\n=== Extraindo todos os dados de SRAG ===\n")
    
    # Criar diretório para dados consolidados
    diretorio_consolidados = os.path.join(os.path.dirname(__file__), "dados_consolidados")
    if not os.path.exists(diretorio_consolidados):
        os.makedirs(diretorio_consolidados)
    
    # Para cada endpoint e ano, extrair os dados
    for endpoint in endpoints:
        # Criar DataFrame vazio para consolidar dados de todos os anos
        df_consolidado = None
        
        for ano in anos:
            print(f"Extraindo dados de {endpoint} para o ano {ano}...")
            df = buscar_srag_goias(endpoint, ano)
            
            if df is not None:
                # Adicionar coluna de ano
                df['ano'] = ano
                
                # Consolidar com dados anteriores
                if df_consolidado is None:
                    df_consolidado = df
                else:
                    df_consolidado = pd.concat([df_consolidado, df], ignore_index=True)
        
        # Salvar dados consolidados
        if df_consolidado is not None:
            # Garantir que a coluna 'casos' seja removida antes de salvar
            if 'casos' in df_consolidado.columns:
                df_consolidado = df_consolidado.drop(columns=['casos'])
                
            nome_arquivo = f"{endpoint}_todos_anos.csv"
            arquivo_consolidado = os.path.join(os.path.dirname(__file__), "dados_consolidados", nome_arquivo)
            df_consolidado.to_csv(arquivo_consolidado, index=False)
            print(f"Arquivo consolidado salvo em {nome_arquivo}")
    
    print("\n=== Extração de dados concluída ===\n")

if __name__ == "__main__":
    # Extrair todos os dados de SRAG
    extrair_todos_dados_srag()