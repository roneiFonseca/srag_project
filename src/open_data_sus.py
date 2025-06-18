import json

import requests

url = "https://imunizacao-es.saude.gov.br/_search?scroll=1m"
username = "imunizacao_public"
password = "qito5t&7r_@+#Tlstigi"

# Update the query to filter for DF state
payload = json.dumps({
    "size": 50,  # Increased size to get more records
    "query": {
        "match": {
            "paciente_endereco_uf": "DF"
        }
    }
})

headers = {
    "Content-Type": "application/json",
}

response = requests.request("POST", url, auth=(username, password), headers=headers, data=payload)

# Parse the JSON response
data = json.loads(response.text)
print(data)

# Extract and print the requested fields from each hit
if 'hits' in data and 'hits' in data['hits']:
    records_found = len(data['hits']['hits'])
    print(f"Encontrados {records_found} registros para o estado DF:\n")
    
    for hit in data['hits']['hits']:
        source = hit.get('_source', {})
        
        # Extract the requested fields
        uf = source.get('paciente_endereco_uf', 'N/A')
        data_aplicacao = source.get('vacina_dataAplicacao', 'N/A')
        
        print(f"UF: {uf}, Data de Aplicação: {data_aplicacao}")
else:
    print("Não foi possível encontrar os dados solicitados na resposta.")
