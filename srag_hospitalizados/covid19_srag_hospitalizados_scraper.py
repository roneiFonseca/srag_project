import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Definir pasta para salvar os dados
DADOS_DIR = os.path.join(os.path.dirname(__file__), "dados/fvs_raw")

# Garantir que a pasta existe
os.makedirs(DADOS_DIR, exist_ok=True)

# Obter timestamp para nomear arquivos
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Configurar o Chrome com opções de download
chrome_options = Options()
chrome_options.add_argument("--start-maximized")  # Iniciar maximizado

# Configurar diretório de download para a pasta DADOS_DIR
prefs = {
    "download.default_directory": DADOS_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
}
chrome_options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=chrome_options)


def acessar_pagina(driver):
    """Abre a página uma única vez e aplica os filtros de região e UF em sequência"""

    try:
        # Abrir a URL
        print("Abrindo URL...")
        driver.get("https://www.fvs.am.gov.br/indicadorSalaSituacao_view/60/2")

        # Aguardar carregamento da página
        print("Aguardando carregamento da página...")
        time.sleep(1)  # Dar tempo para página inicializar

    except Exception as e:
        print("Ocorreu um erro:")
        print(e)
        import traceback

        traceback.print_exc()


def buscar_link_sharepoint(driver):
    """Função para buscar diretamente o segundo link do SharePoint usando XPath específico"""
    try:
        # XPath específico do  link do SharePoint
        xpath_segundo_link = 'id("tabZoneId104")/DIV[1]/DIV[1]/DIV[1]/DIV[1]/DIV[1]/SPAN[1]/DIV[10]/SPAN[2]/A[1]'

        sharepoint_link = driver.find_element(By.XPATH, xpath_segundo_link)

        if sharepoint_link:
            href = sharepoint_link.get_attribute("href")
            print(f"Link encontrado: {href}")
            return sharepoint_link
        else:
            print("Link não encontrado com XPath específico")
            return None

    except Exception as e:
        print(f"Erro ao buscar link com XPath específico: {e}")


def baixar_arquivo_sharepoint(driver):
    """Função para baixar o arquivo específico do SharePoint"""
    try:
        print(
            "Procurando arquivo 'sraghospitalizado_25set2024_microdados.xlsx' na página do SharePoint..."
        )

        # Aguardar um pouco mais para garantir que a página carregou completamente
        time.sleep(3)

        arquivo_encontrado = False

        try:
            # Procurar especificamente pelo nome do arquivo (isso vai selecionar o checkbox)
            arquivo_nome = driver.find_element(
                By.XPATH,
                "//span[contains(text(), 'sraghospitalizado_25set2024_microdados.xlsx')]",
            )
            driver.execute_script("arguments[0].click();", arquivo_nome)

            # Aguardar um pouco para o arquivo ser selecionado
            time.sleep(1)

            # Agora procurar e clicar no botão "Baixar"
            try:
                botao_baixar = driver.find_element(
                    By.XPATH,
                    "//button[@data-id='download' and @data-automationid='downloadCommand']",
                )
                driver.execute_script("arguments[0].click();", botao_baixar)
                arquivo_encontrado = True
            except Exception as e:
                print(f"Botão 'Baixar' não encontrado: {e}")
                # Tentar buscar por texto do botão
                try:
                    botao_baixar_texto = driver.find_element(
                        By.XPATH, "//button[contains(.//span, 'Baixar')]"
                    )
                    print("Botão 'Baixar' encontrado por texto!")
                    driver.execute_script("arguments[0].click();", botao_baixar_texto)
                    arquivo_encontrado = True
                except Exception as e2:
                    print(f"Botão 'Baixar' por texto também não encontrado: {e2}")

        except Exception as e:
            print(f"Erro na Estratégia 1: {e}")

        if arquivo_encontrado:
            print("Clique no arquivo executado. Aguardando download...")

            # Verificar se uma nova aba foi aberta (para visualização do arquivo)
            initial_windows = len(driver.window_handles)
            time.sleep(1)
            current_windows = len(driver.window_handles)

            if current_windows > initial_windows:
                print("Nova aba detectada - arquivo pode ter aberto para visualização")
                # Fechar a nova aba e voltar para a original
                driver.switch_to.window(driver.window_handles[-1])
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            # Aguardar mais tempo para o download iniciar
            print("Aguardando download iniciar...")
            time.sleep(1)

            # Verificar se o arquivo foi baixado
            arquivos_baixados = []
            for arquivo in os.listdir(DADOS_DIR):
                if arquivo.endswith(".xlsx") and "srag" in arquivo.lower():
                    arquivos_baixados.append(arquivo)

            if arquivos_baixados:
                print(f"Arquivos baixados encontrados: {arquivos_baixados}")
            else:
                print(
                    "Nenhum arquivo Excel com 'srag' foi encontrado nas pastas de download"
                )
                print(f"Verificando pasta configurada: {DADOS_DIR}")
                todos_arquivos = os.listdir(DADOS_DIR)
                print(f"Todos os arquivos na pasta: {todos_arquivos}")
        else:
            print("Arquivo específico não foi encontrado na página")

    except Exception as e:
        print(f"Erro ao baixar arquivo do SharePoint: {e}")


def baixar_dados(driver):
    try:
        # Aguardar mais tempo para garantir que conteúdo dinâmico carregue
        print("Aguardando carregamento de conteúdo dinâmico...")
        time.sleep(10)

        # Tentar múltiplas estratégias para encontrar o link
        sharepoint_link = None

        # Primeiro, verificar se há iframes na página
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Encontrados {len(iframes)} iframes na página")

        # Procurar no documento principal primeiro
        sharepoint_link = buscar_link_sharepoint(driver)

        # Se não encontrou no documento principal, procurar nos iframes
        if not sharepoint_link and iframes:
            for i, iframe in enumerate(iframes):
                try:
                    print(f"Verificando iframe {i + 1}...")
                    driver.switch_to.frame(iframe)
                    sharepoint_link = buscar_link_sharepoint(driver)
                    if sharepoint_link:
                        print(f"Link encontrado no iframe {i + 1}")
                        break
                    driver.switch_to.default_content()
                except Exception as e:
                    print(f"Erro ao verificar iframe {i + 1}: {e}")
                    driver.switch_to.default_content()

        if sharepoint_link:
            # Obter o href do link
            href = sharepoint_link.get_attribute("href")
            print(f"Abrindo SharePoint: {href}")

            # Abrir diretamente na mesma aba
            driver.get(href)

            # Aguardar a página do SharePoint carregar
            print("Aguardando página do SharePoint carregar...")
            time.sleep(1)

            # Verificar se chegou no SharePoint
            current_url = driver.current_url
            print(f"URL atual: {current_url}")

            if "sharepoint.com" in current_url:
                print("Navegação para SharePoint bem-sucedida!")
                # Procurar e clicar no arquivo específico
                baixar_arquivo_sharepoint(driver)
            else:
                print("Falha ao navegar para o SharePoint")

        else:
            print("Nenhum link do SharePoint foi encontrado na página ou iframes")

    except Exception as e:
        print(f"Erro ao baixar dados: {e}")


if __name__ == "__main__":
    # Executar os filtros em sequência em uma única sessão do navegador
    acessar_pagina(driver)
    baixar_dados(driver)

    print("Script concluído.")
