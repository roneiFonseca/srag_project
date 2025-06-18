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
                {"term": {"estabelecimento_uf": "DF"}},
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
