import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class VacinometroCovidScraper:
    """Classe para fazer scraping de dados do vacinômetro COVID-19"""
    
    def __init__(self, dados_dir=None):
        """
        Inicializa o scraper
        
        Args:
            dados_dir (str, optional): Diretório para salvar os dados. 
                                     Se None, usa pasta padrão 'vacinometro/dados'
        """
        # Definir pasta para salvar os dados
        if dados_dir is None:
            self.dados_dir = os.path.join(os.path.dirname(__file__), "vacinometro/dados")
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
            "safebrowsing.enabled": True
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

    def aplicar_filtros(self):
        """Abre a página uma única vez e aplica os filtros de região e UF em sequência"""
        if not self.driver:
            raise Exception("Driver não inicializado. Chame inicializar_driver() primeiro.")
            
        try:
            # Abrir a URL
            print("Abrindo URL...")
            self.driver.get(
                "https://infoms.saude.gov.br/extensions/SEIDIGI_DEMAS_Vacina_C19/SEIDIGI_DEMAS_Vacina_C19.html"
            )

            # Aguardar carregamento da página
            print("Aguardando carregamento da página...")
            time.sleep(5)  # Dar tempo para página inicializar

            # Aplicar filtro de região (Norte)
            self.selecionar_regiao_norte()

            # Aplicar filtro de UF (AM)
            self.selecionar_uf_am()

            # Tirar screenshot final com todos os filtros aplicados
            time.sleep(0.5)
            screenshot_path = os.path.join(self.dados_dir, f"{self.timestamp}_filtros_aplicados.png")
            self.driver.save_screenshot(screenshot_path)
            print(f"Screenshot salvo em: {screenshot_path}")
            print("Todos os filtros foram aplicados com sucesso!")

        except Exception as e:
            print("Ocorreu um erro:")
            print(e)
            import traceback
            traceback.print_exc()

    def selecionar_regiao_norte(self):
        """Seleciona a região Norte no filtro"""
        try:
            # Aguardar o elemento do filtro aparecer
            print("Aguardando elementos de filtro carregarem...")
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".folded-listbox.css-abblij")
                )
            )

            # Clicar no filtro de região
            print("Clicando no filtro 'Região'...")
            region_filter = self.driver.find_element(
                By.CSS_SELECTOR, ".folded-listbox.css-abblij"
            )
            region_filter.click()

            # Aguardar as opções do dropdown aparecerem
            time.sleep(2)

            # Encontrar e clicar na opção "Norte"
            print("Procurando e selecionando a opção 'Norte'...")
            dropdown_options = self.driver.find_elements(
                By.CSS_SELECTOR, ".ListBox-styledScrollbars.css-1nwu5vb div"
            )

            # Procurar diretamente pela opção "Norte"
            norte_selecionado = False
            for option in dropdown_options:
                if option.text.strip() == "Norte" and option.is_displayed():
                    option.click()
                    print("Opção 'Norte' selecionada com sucesso!")
                    time.sleep(1)  # Pequena pausa para garantir que a seleção foi aplicada
                    screenshot_path = os.path.join(
                        self.dados_dir, f"{self.timestamp}_norte_selecionado.png"
                    )
                    self.driver.save_screenshot(screenshot_path)
                    print(f"Screenshot salvo em: {screenshot_path}")
                    norte_selecionado = True
                    break

            if not norte_selecionado:
                print("Não foi possível encontrar a opção 'Norte' no dropdown.")
                return False

            # Fechar o dropdown clicando em uma área vazia da página
            print("Fechando o dropdown de região...")
            try:
                # Tentar clicar no corpo da página para fechar o dropdown
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.click()
                time.sleep(1)  # Aguardar o fechamento do dropdown
            except Exception as e:
                print(f"Aviso: Não foi possível fechar o dropdown normalmente: {e}")
                # Tentar fechar usando JavaScript
                try:
                    self.driver.execute_script(
                        "document.querySelector('.MuiBackdrop-root').click();"
                    )
                    time.sleep(1)
                except Exception:
                    # Última tentativa: tecla ESC
                    from selenium.webdriver.common.keys import Keys

                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body.send_keys(Keys.ESCAPE)
                    time.sleep(1)

            return True

        except Exception as e:
            print(f"Erro ao selecionar região Norte: {e}")
            return False

    def selecionar_uf_am(self):
        """Seleciona a UF AM no filtro"""
        try:
            # Aguardar o elemento do filtro de UF aparecer
            print("Procurando o filtro 'UF'...")
            filters = self.driver.find_elements(By.CSS_SELECTOR, ".folded-listbox.css-abblij")

            uf_filter = None
            for filter_elem in filters:
                if "UF" in filter_elem.text:
                    uf_filter = filter_elem
                    print(f"Filtro UF encontrado: '{filter_elem.text}'")
                    break

            if not uf_filter and len(filters) >= 2:
                # Se não encontrou pelo texto, pegar o segundo filtro
                uf_filter = filters[1]  # Geralmente o segundo filtro é UF
                print("Usando o segundo filtro como UF")

            if not uf_filter:
                print("Não foi possível encontrar o filtro de UF")
                return False

            # Clicar no filtro de UF
            print("Clicando no filtro de UF...")
            uf_filter.click()

            # Aguardar as opções do dropdown aparecerem
            time.sleep(2)

            # Encontrar e clicar na opção "AM"
            print("Procurando e selecionando a opção 'AM'...")
            dropdown_options = self.driver.find_elements(
                By.CSS_SELECTOR, ".ListBox-styledScrollbars.css-1nwu5vb div"
            )

            # Procurar diretamente pela opção "AM"
            for option in dropdown_options:
                if option.text.strip() == "AM" and option.is_displayed():
                    option.click()
                    print("Opção 'AM' selecionada com sucesso!")
                    time.sleep(0.5)  # Pequena pausa para garantir que a seleção foi aplicada
                    screenshot_path = os.path.join(
                        self.dados_dir, f"{self.timestamp}_am_selecionado.png"
                    )
                    self.driver.save_screenshot(screenshot_path)
                    print(f"Screenshot salvo em: {screenshot_path}")
                    # Fechar o dropdown clicando em uma área vazia da página
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body.click()
                    time.sleep(0.5)  # Aguardar o fechamento do dropdown
                    return True

            print("Não foi possível encontrar a opção 'AM' no dropdown.")
            return False

        except Exception as e:
            print(f"Erro ao selecionar UF AM: {e}")
            return False

    def rolar_fim_pagina(self):
        """Rola a página até o fim"""
        if not self.driver:
            raise Exception("Driver não inicializado. Chame inicializar_driver() primeiro.")
            
        try:
            print("Rolando a página até o fim...")

            # Usar JavaScript para rolar até o fim da página
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            # Tentar rolar mais algumas vezes para garantir que chegou ao fim
            for _ in range(3):
                # Rolar mais um pouco
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(0.5)

            # Tirar screenshot da página rolada
            screenshot_path = os.path.join(self.dados_dir, f"{self.timestamp}_pagina_rolada.png")
            self.driver.save_screenshot(screenshot_path)
            print(f"Screenshot salvo em: {screenshot_path}")
            print("Página rolada com sucesso!")

        except Exception as e:
            print(f"Erro ao rolar a página: {e}")

    def baixar_dados(self):
        """Baixa os dados do vacinômetro"""
        if not self.driver:
            raise Exception("Driver não inicializado. Chame inicializar_driver() primeiro.")
            
        try:
            # Encontrar o botão pelo ID
            download_button = self.driver.find_element(By.ID, "exportar-dados-QV5")
            print("Botão encontrado pelo ID")

            # Tirar screenshot antes de clicar
            screenshot_path = os.path.join(self.dados_dir, f"{self.timestamp}_antes_download.png")
            self.driver.save_screenshot(screenshot_path)
            print(f"Screenshot salvo em: {screenshot_path}")
           
            # Clicar no botão de download
            print("Clicando no botão de download...")
            self.driver.execute_script("arguments[0].click();", download_button)
            # Aguardar o download terminar
            time.sleep(5)
         
        except Exception as e:
            print(f"Erro ao baixar dados: {e}")
            # Capturar uma screenshot para debug
            try:
                screenshot_path = os.path.join(self.dados_dir, f"{self.timestamp}_erro_download.png")
                self.driver.save_screenshot(screenshot_path)
                print(f"Screenshot de erro salvo em: {screenshot_path}")
            except Exception as screenshot_error:
                print(f"Não foi possível salvar screenshot de erro: {screenshot_error}")
                
    def executar_scraping(self):
        """Método principal que executa todo o processo de scraping"""
        try:
            print("Iniciando scraping de dados do vacinômetro COVID-19...")
            self.inicializar_driver()
            self.aplicar_filtros()
            self.rolar_fim_pagina()
            self.baixar_dados()
            print("Script concluído.")
        except Exception as e:
            print(f"Erro durante o scraping: {e}")
        finally:
            self.fechar_driver()


if __name__ == "__main__":
    # Criar instância do scraper e executar
    scraper = VacinometroCovidScraper()
    scraper.executar_scraping()
