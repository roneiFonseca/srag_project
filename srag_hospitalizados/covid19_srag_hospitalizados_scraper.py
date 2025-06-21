import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class SragHospitalizadosScraper:
    """Classe para fazer scraping de dados de SRAG hospitalizados do site da FVS-AM"""
    
    def __init__(self, dados_dir=None):
        """
        Inicializa o scraper
        
        Args:
            dados_dir (str, optional): Diretório para salvar os dados. 
                                     Se None, usa pasta padrão 'dados/fvs_raw'
        """
        # Definir pasta para salvar os dados
        if dados_dir is None:
            self.dados_dir = os.path.join(os.path.dirname(__file__), "dados/fvs_raw")
        else:
            self.dados_dir = dados_dir
            
        # Garantir que a pasta existe
        os.makedirs(self.dados_dir, exist_ok=True)
        
        # Obter timestamp para nomear arquivos
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Inicializar driver como None
        self.driver = None
        
    def _configurar_chrome(self):
        """Configura as opções do Chrome para download"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")  # Iniciar maximizado
        
        # Configurar diretório de download para a pasta DADOS_DIR
        prefs = {
            "download.default_directory": self.dados_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        return chrome_options
        
    def inicializar_driver(self):
        """Inicializa o driver do Chrome"""
        chrome_options = self._configurar_chrome()
        self.driver = webdriver.Chrome(options=chrome_options)
        
    def fechar_driver(self):
        """Fecha o driver do Chrome"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def acessar_pagina(self):
        """Abre a página uma única vez e aplica os filtros de região e UF em sequência"""
        if not self.driver:
            raise Exception("Driver não inicializado. Chame inicializar_driver() primeiro.")
            
        try:
            # Abrir a URL
            print("Abrindo URL...")
            self.driver.get("https://www.fvs.am.gov.br/indicadorSalaSituacao_view/60/2")

            # Aguardar carregamento da página
            print("Aguardando carregamento da página...")
            time.sleep(1)  # Dar tempo para página inicializar

        except Exception as e:
            print("Ocorreu um erro:")
            print(e)
            import traceback
            traceback.print_exc()

    def buscar_link_sharepoint(self):
        """Função para buscar diretamente o segundo link do SharePoint usando XPath específico"""
        try:
            # XPath específico do  link do SharePoint
            xpath_segundo_link = 'id("tabZoneId104")/DIV[1]/DIV[1]/DIV[1]/DIV[1]/DIV[1]/SPAN[1]/DIV[10]/SPAN[2]/A[1]'

            sharepoint_link = self.driver.find_element(By.XPATH, xpath_segundo_link)

            if sharepoint_link:
                href = sharepoint_link.get_attribute("href")
                print(f"Link encontrado: {href}")
                return sharepoint_link
            else:
                print("Link não encontrado com XPath específico")
                return None

        except Exception as e:
            print(f"Erro ao buscar link com XPath específico: {e}")
            return None

    def baixar_arquivo_sharepoint(self):
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
                arquivo_nome = self.driver.find_element(
                    By.XPATH,
                    "//span[contains(text(), 'sraghospitalizado_25set2024_microdados.xlsx')]",
                )
                self.driver.execute_script("arguments[0].click();", arquivo_nome)

                # Aguardar um pouco para o arquivo ser selecionado
                time.sleep(1)

                # Agora procurar e clicar no botão "Baixar"
                try:
                    botao_baixar = self.driver.find_element(
                        By.XPATH,
                        "//button[@data-id='download' and @data-automationid='downloadCommand']",
                    )
                    self.driver.execute_script("arguments[0].click();", botao_baixar)
                    arquivo_encontrado = True
                except Exception as e:
                    print(f"Botão 'Baixar' não encontrado: {e}")
                    # Tentar buscar por texto do botão
                    try:
                        botao_baixar_texto = self.driver.find_element(
                            By.XPATH, "//button[contains(.//span, 'Baixar')]"
                        )
                        print("Botão 'Baixar' encontrado por texto!")
                        self.driver.execute_script("arguments[0].click();", botao_baixar_texto)
                        arquivo_encontrado = True
                    except Exception as e2:
                        print(f"Botão 'Baixar' por texto também não encontrado: {e2}")

            except Exception as e:
                print(f"Erro na Estratégia 1: {e}")

            if arquivo_encontrado:
                print("Clique no arquivo executado. Aguardando download...")

                # Verificar se uma nova aba foi aberta (para visualização do arquivo)
                initial_windows = len(self.driver.window_handles)
                time.sleep(1)
                current_windows = len(self.driver.window_handles)

                if current_windows > initial_windows:
                    print("Nova aba detectada - arquivo pode ter aberto para visualização")
                    # Fechar a nova aba e voltar para a original
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])

                # Aguardar mais tempo para o download iniciar
                print("Aguardando download iniciar...")
                time.sleep(1)

                # Verificar se o arquivo foi baixado
                arquivos_baixados = []
                for arquivo in os.listdir(self.dados_dir):
                    if arquivo.endswith(".xlsx") and "srag" in arquivo.lower():
                        arquivos_baixados.append(arquivo)

                if arquivos_baixados:
                    print(f"Arquivos baixados encontrados: {arquivos_baixados}")
                else:
                    print(
                        "Nenhum arquivo Excel com 'srag' foi encontrado nas pastas de download"
                    )
                    print(f"Verificando pasta configurada: {self.dados_dir}")
                    todos_arquivos = os.listdir(self.dados_dir)
                    print(f"Todos os arquivos na pasta: {todos_arquivos}")
            else:
                print("Arquivo específico não foi encontrado na página")

        except Exception as e:
            print(f"Erro ao baixar arquivo do SharePoint: {e}")

    def baixar_dados(self):
        """Método principal para baixar os dados"""
        if not self.driver:
            raise Exception("Driver não inicializado. Chame inicializar_driver() primeiro.")
            
        try:
            # Aguardar mais tempo para garantir que conteúdo dinâmico carregue
            print("Aguardando carregamento de conteúdo dinâmico...")
            time.sleep(10)

            # Tentar múltiplas estratégias para encontrar o link
            sharepoint_link = None

            # Primeiro, verificar se há iframes na página
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Encontrados {len(iframes)} iframes na página")

            # Procurar no documento principal primeiro
            sharepoint_link = self.buscar_link_sharepoint()

            # Se não encontrou no documento principal, procurar nos iframes
            if not sharepoint_link and iframes:
                for i, iframe in enumerate(iframes):
                    try:
                        print(f"Verificando iframe {i + 1}...")
                        self.driver.switch_to.frame(iframe)
                        sharepoint_link = self.buscar_link_sharepoint()
                        if sharepoint_link:
                            print(f"Link encontrado no iframe {i + 1}")
                            break
                        self.driver.switch_to.default_content()
                    except Exception as e:
                        print(f"Erro ao verificar iframe {i + 1}: {e}")
                        self.driver.switch_to.default_content()

            if sharepoint_link:
                # Obter o href do link
                href = sharepoint_link.get_attribute("href")
                print(f"Abrindo SharePoint: {href}")

                # Abrir diretamente na mesma aba
                self.driver.get(href)

                # Aguardar a página do SharePoint carregar
                print("Aguardando página do SharePoint carregar...")
                time.sleep(1)

                # Verificar se chegou no SharePoint
                current_url = self.driver.current_url
                print(f"URL atual: {current_url}")

                if "sharepoint.com" in current_url:
                    print("Navegação para SharePoint bem-sucedida!")
                    # Procurar e clicar no arquivo específico
                    self.baixar_arquivo_sharepoint()
                else:
                    print("Falha ao navegar para o SharePoint")

            else:
                print("Nenhum link do SharePoint foi encontrado na página ou iframes")

        except Exception as e:
            print(f"Erro ao baixar dados: {e}")
            
    def executar_scraping(self):
        """Método principal que executa todo o processo de scraping"""
        try:
            print("Iniciando scraping de dados SRAG hospitalizados...")
            self.inicializar_driver()
            self.acessar_pagina()
            self.baixar_dados()
            print("Script concluído.")
        except Exception as e:
            print(f"Erro durante o scraping: {e}")
        finally:
            self.fechar_driver()


if __name__ == "__main__":
    # Criar instância do scraper e executar
    scraper = SragHospitalizadosScraper()
    scraper.executar_scraping()
