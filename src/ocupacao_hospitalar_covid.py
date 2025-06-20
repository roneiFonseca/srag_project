import json
import sys
import csv
import os
import requests
from datetime import datetime

# Configurações da API
base_url = "https://apidadosabertos.saude.gov.br/assistencia-a-saude/registro-de-ocupacao-hospitalar-covid-19"

headers = {
    "Accept": "application/json"
}

def buscar_ocupacao_hospitalar(estado, data_inicio=None, data_fim=None, offset=0):
    """
    Busca dados de ocupação hospitalar para um estado e período específico
    
    Args:
        estado (str): Nome do estado para buscar dados
        data_inicio (str ou datetime): Data inicial do período
        data_fim (str ou datetime): Data final do período
        offset (int): Deslocamento para paginação dos resultados
    
    Returns:
        list: Lista de registros encontrados
    """
    # Se não for fornecida uma data, usa um período padrão de 2021
    if not data_inicio:
        # Usar uma data de 2021 como padrão (período com mais dados de COVID)
        data_inicio = "2021-01-01"
    if not data_fim:
        data_fim = "2021-12-31"
    
    # Converter strings para objetos datetime
    if isinstance(data_inicio, str):
        data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
    if isinstance(data_fim, str):
        data_fim = datetime.strptime(data_fim, "%Y-%m-%d")
        
    # Formatar as datas para a API
    data_inicio_str = data_inicio.strftime("%Y-%m-%dT00:00:00.000Z")
    data_fim_str = data_fim.strftime("%Y-%m-%dT23:59:59.999Z")
    
    print(f"Buscando registros para o estado: {estado}")
    print(f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    print(f"Offset: {offset}")
    
    # Construir parâmetros de consulta para a API
    params = {
        "dataNotificacaoInicio": data_inicio_str,
        "dataNotificacaoFim": data_fim_str,
        "limit": 1000,  # Aumentar o limite para obter mais registros
        "offset": offset,
        # Adicionar outros parâmetros que podem ajudar na filtragem
        "estado": estado,
        "format": "json"
    }
    
    try:
        # Fazer a requisição GET com os parâmetros de consulta
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()  # Verificar se houve erro na requisição
        
        data = response.json()
        
        # Verificar se há registros retornados
        if data and "registro_ocupacao_hospitalar_covid19" in data and len(data["registro_ocupacao_hospitalar_covid19"]) > 0:
            # Filtrar manualmente os registros pelo estado
            registros_filtrados = []
            for registro in data["registro_ocupacao_hospitalar_covid19"]:
                if registro.get("estado") == estado:
                    # Adicionar informação sobre o período de consulta para referência
                    registro["periodo_consulta"] = f"{data_inicio.strftime('%Y-%m-%d')} a {data_fim.strftime('%Y-%m-%d')}"
                    registros_filtrados.append(registro)
            
            if registros_filtrados:
                print(f"Total de registros encontrados para {estado}: {len(registros_filtrados)}")
                if len(registros_filtrados) > 0:
                    print("\nPrimeiro registro:")
                    print(json.dumps(registros_filtrados[0], indent=4))
                return registros_filtrados
            else:
                print(f"Nenhum registro encontrado para o estado de {estado} no período especificado.")
                print(f"Total de registros retornados pela API: {len(data['registro_ocupacao_hospitalar_covid19'])}")
                estados_disponiveis = set(reg.get("estado") for reg in data["registro_ocupacao_hospitalar_covid19"])
                print(f"Estados disponíveis nos dados ({len(estados_disponiveis)}):")
                print(", ".join(sorted(estados_disponiveis)))
                return []
        else:
            print("Nenhum registro retornado pela API para o período especificado.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer a requisição: {e}")
        return []


def salvar_para_csv(registros, nome_arquivo, metadados=None):
    """
    Salva os registros em um arquivo CSV com metadados
    
    Args:
        registros (list): Lista de dicionários com os registros a serem salvos
        nome_arquivo (str): Caminho completo do arquivo CSV a ser criado
        metadados (dict): Dicionário com metadados opcionais sobre a coleta
    
    Returns:
        bool: True se os dados foram salvos com sucesso, False caso contrário
    """
    if not registros:
        print("Nenhum registro para salvar.")
        return False
    
    # Garantir que o diretório de saída exista
    diretorio = os.path.dirname(nome_arquivo)
    if diretorio and not os.path.exists(diretorio):
        os.makedirs(diretorio)
    
    # Organizar os campos em uma ordem mais lógica
    campos_prioritarios = [
        'estado', 'municipio', 'cnes', 'datanotificacao', 
        'ocupacaoconfirmadocli', 'ocupacaosuspeitocli', 'ocupacaoconfirmadouti', 'ocupacaosuspeitouti',
        'saidaconfirmadaobitos', 'saidasuspeitaobitos', 'saidaconfirmadaaltas', 'saidasuspeitaaltas',
        'ocupacaocovidcli', 'ocupacaocoviduti', 'ocupacaohospitalarcli', 'ocupacaohospitalaruti',
        'validado', 'excluido', 'origem', 'periodo_consulta'
    ]
    
    # Obter todos os campos disponíveis nos registros
    todos_campos = set()
    for registro in registros:
        todos_campos.update(registro.keys())
    
    # Criar a lista final de cabeçalhos, priorizando os campos importantes
    cabecalhos = [campo for campo in campos_prioritarios if campo in todos_campos]
    # Adicionar campos restantes que não estão na lista prioritária
    cabecalhos.extend([campo for campo in todos_campos if campo not in campos_prioritarios])
    
    try:
        # Criar arquivo de metadados para documentar a coleta
        if metadados:
            meta_arquivo = f"{os.path.splitext(nome_arquivo)[0]}_metadados.json"
            with open(meta_arquivo, 'w', encoding='utf-8') as f:
                json.dump(metadados, f, indent=4, ensure_ascii=False)
            print(f"Metadados salvos em: {meta_arquivo}")
        
        # Salvar os registros no arquivo CSV
        with open(nome_arquivo, 'w', newline='', encoding='utf-8') as arquivo_csv:
            writer = csv.DictWriter(arquivo_csv, fieldnames=cabecalhos)
            writer.writeheader()
            writer.writerows(registros)
        
        print(f"Dados salvos com sucesso em: {nome_arquivo}")
        print(f"Total de registros salvos: {len(registros)}")
        
        # Criar um arquivo de resumo com estatísticas básicas
        resumo = {
            "total_registros": len(registros),
            "municipios": len(set(r.get('municipio', '') for r in registros)),
            "unidades_saude": len(set(r.get('cnes', '') for r in registros)),
            "datas_notificacao": len(set(r.get('datanotificacao', '') for r in registros))
        }
        
        resumo_arquivo = f"{os.path.splitext(nome_arquivo)[0]}_resumo.json"
        with open(resumo_arquivo, 'w', encoding='utf-8') as f:
            json.dump(resumo, f, indent=4, ensure_ascii=False)
        print(f"Resumo estatístico salvo em: {resumo_arquivo}")
        
        return True
    except Exception as e:
        print(f"Erro ao salvar dados: {e}")
        return False

def coletar_dados_ano(estado, ano):
    """
    Coleta dados para um estado e ano específico, por trimestres
    """
    todos_registros = []
    registros_unicos = set()  # Para evitar duplicação de registros
    
    print(f"Coletando dados para {estado} no ano {ano}...")
    
    # Dividir o ano em trimestres para obter mais dados
    trimestres = [
        (f"{ano}-01-01", f"{ano}-03-31"),  # 1º trimestre
        (f"{ano}-04-01", f"{ano}-06-30"),  # 2º trimestre
        (f"{ano}-07-01", f"{ano}-09-30"),  # 3º trimestre
        (f"{ano}-10-01", f"{ano}-12-31"),  # 4º trimestre
    ]
    
    # Tentar diferentes offsets para obter mais dados
    offsets = [0, 1000, 2000]
    
    for inicio, fim in trimestres:
        print(f"\nBuscando dados para o período: {inicio} a {fim}")
        
        for offset in offsets:
            try:
                # Busca os registros para este trimestre
                registros_trimestre = buscar_ocupacao_hospitalar(estado, inicio, fim, offset)
                
                if registros_trimestre:
                    # Adicionar apenas registros únicos baseados em alguma chave única
                    novos_registros = 0
                    for registro in registros_trimestre:
                        # Criar uma chave única para cada registro
                        chave = (registro.get('cnes', ''), registro.get('datanotificacao', ''), 
                                registro.get('municipio', ''))
                        
                        if chave not in registros_unicos:
                            registros_unicos.add(chave)
                            todos_registros.append(registro)
                            novos_registros += 1
                    
                    print(f"Adicionados {novos_registros} novos registros únicos.")
                    print(f"Progresso: {len(todos_registros)} registros coletados até agora.")
                    
                    # Se não encontrou novos registros, não precisa continuar com os próximos offsets
                    if novos_registros == 0:
                        break
                else:
                    print(f"Nenhum registro encontrado para o período {inicio} a {fim} com offset {offset}.")
                    break  # Se não encontrou registros, não precisa tentar outros offsets
            except Exception as e:
                print(f"Erro ao processar período {inicio} a {fim}: {e}")
    
    print(f"\nTotal de registros únicos coletados para {estado} em {ano}: {len(todos_registros)}")
    return todos_registros

if __name__ == "__main__":
    # Verificar argumentos da linha de comando
    estado = "Amazonas"  # Estado padrão
    ano = 2023  # Ano padrão
    
    # Se houver argumentos, usar o primeiro como estado e o segundo como ano
    if len(sys.argv) > 1:
        estado = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            ano = int(sys.argv[2])
        except ValueError:
            print(f"Ano inválido: {sys.argv[2]}. Usando ano padrão: 2021")
            ano = 2021
    
    print("\n" + "="*50)
    print("Iniciando coleta de dados de ocupação hospitalar COVID-19")
    print(f"Estado: {estado}")
    print(f"Ano: {ano}")
    print("="*50 + "\n")
    
    # Registrar horário de início
    inicio_coleta = datetime.now()
    
    # Coletar dados para o estado e ano especificados
    registros = coletar_dados_ano(estado, ano)
    
    # Calcular tempo de execução
    fim_coleta = datetime.now()
    tempo_execucao = (fim_coleta - inicio_coleta).total_seconds()
    
    # Criar metadados sobre a coleta
    metadados = {
        "estado": estado,
        "ano": ano,
        "data_coleta": fim_coleta.strftime("%Y-%m-%d %H:%M:%S"),
        "tempo_execucao_segundos": tempo_execucao,
        "total_registros": len(registros),
        "versao_script": "1.1.0"
    }
    
    # Salvar os registros em um arquivo CSV
    if registros:
        # Criar nome de arquivo com base no estado e ano
        nome_arquivo = f"dados/ocupacao_hospitalar_{estado.lower()}_{ano}.csv"
        salvar_para_csv(registros, nome_arquivo, metadados)
        
        print("\n" + "="*50)
        print("Coleta finalizada com sucesso!")
        print(f"Tempo de execução: {tempo_execucao:.2f} segundos")
        print("="*50)
    else:
        print("\n" + "="*50)
        print(f"Nenhum registro encontrado para {estado} em {ano}.")
        print("Verifique se os parâmetros estão corretos ou tente outro período.")
        print("="*50)