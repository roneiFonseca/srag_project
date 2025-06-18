#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para extrair dados de hospitalizações por SRAG (Síndrome Respiratória Aguda Grave)
do dashboard Tableau da Fundação de Vigilância em Saúde do Amazonas (FVS-RCP/AM).

Este script utiliza Selenium para interagir com o dashboard Tableau e extrair os dados.
"""

import os
import time
import json
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# URL do dashboard Tableau com dados de SRAG
DASHBOARD_URL = "https://www.fvs.am.gov.br/indicadorSalaSituacao_view/60/2"

# Diretório para salvar os dados extraídos
DATA_DIR = os.path.join(os.path.dirname(__file__), "dados", "srag_amazonas")


def configurar_webdriver():
    """
    Configura e inicializa o WebDriver do Chrome para Selenium.
    
    Returns:
        webdriver.Chrome: Instância configurada do WebDriver.
    """
    # Configurar as opções do Chrome
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Executar em modo headless (sem interface gráfica)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Inicializar o WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    
    return driver


def extrair_dados_tableau(driver, url, timeout=180, max_tentativas=5):
    """
    Extrai dados do dashboard Tableau.
    
    Args:
        driver (webdriver.Chrome): Instância do WebDriver.
        url (str): URL do dashboard Tableau.
        timeout (int): Tempo máximo de espera em segundos.
        
    Returns:
        dict: Dados extraídos do dashboard ou None em caso de falha.
    """
    try:
        print(f"Acessando o dashboard: {url}")
        driver.get(url)
        
        # Aguardar o carregamento inicial do dashboard Tableau
        print("Aguardando o carregamento inicial do dashboard...")
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tableauViz"))
        )
        
        # Verificar se o elemento tableauViz está presente
        try:
            driver.find_element(By.CLASS_NAME, "tableauViz")
            print("Dashboard Tableau encontrado!")
        except NoSuchElementException:
            print("Erro: Não foi possível encontrar o dashboard Tableau na página.")
            return None
        
        # Analisar a estrutura da página para entender como o Tableau está carregado
        print("\nAnalisando a estrutura da página...")
        
        # Capturar screenshot para análise visual
        capturar_screenshot(driver, "pagina_inicial.png")
        
        # Listar todos os iframes na página
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Total de iframes na página: {len(iframes)}")
        
        for i, iframe in enumerate(iframes):
            try:
                iframe_id = iframe.get_attribute('id') or 'sem-id'
                iframe_src = iframe.get_attribute('src') or 'sem-src'
                iframe_name = iframe.get_attribute('name') or 'sem-nome'
                print(f"Iframe {i+1}: ID={iframe_id}, Name={iframe_name}, Src={iframe_src[:50]}...")
            except Exception as e:
                print(f"Erro ao obter atributos do iframe {i+1}: {str(e)}")
        
        # Tentar extrair dados sem mudar para o iframe
        print("\nTentando extrair dados sem mudar para o iframe...")
        
        # Aguardar um pouco mais para garantir que o dashboard carregue completamente
        print("Aguardando 30 segundos para carregamento completo...")
        time.sleep(30)
        
        # Capturar screenshot após a espera
        capturar_screenshot(driver, "apos_espera_30s.png")
        
        # Tentar encontrar elementos visíveis que possam conter dados
        try:
            # Verificar se há elementos do Tableau visíveis
            elementos_tableau = driver.find_elements(By.CSS_SELECTOR, ".tableauViz, .tab-viz, .tab-textRegion, .tabTable")
            print(f"Elementos do Tableau encontrados: {len(elementos_tableau)}")
            
            # Tentar encontrar o iframe correto com base em atributos específicos do Tableau
            tableau_iframes = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'tableau') or contains(@id, 'tableau')]")
            if tableau_iframes:
                print(f"Encontrados {len(tableau_iframes)} iframes relacionados ao Tableau")
                
                # Tentar mudar para o primeiro iframe relacionado ao Tableau
                try:
                    driver.switch_to.frame(tableau_iframes[0])
                    print(f"Mudou para o iframe Tableau: {tableau_iframes[0].get_attribute('id')}")
                except Exception as e:
                    print(f"Erro ao mudar para o iframe Tableau: {str(e)}")
                    # Continuar sem mudar de iframe
        except Exception as e:
            print(f"Erro ao analisar elementos do Tableau: {str(e)}")
            # Capturar screenshot para análise
            capturar_screenshot(driver, "erro_analise.png")
        
        # Implementar uma abordagem de tentativas múltiplas para extrair os dados
        print("Iniciando tentativas de extração de dados...")
        
        tableau_data = None
        tentativa = 0
        intervalo_espera = 15  # Segundos entre tentativas
        
        while tentativa < max_tentativas and tableau_data is None:
            tentativa += 1
            print(f"\nTentativa {tentativa} de {max_tentativas}:")
            
            # Dar tempo para o dashboard carregar
            print(f"Aguardando {intervalo_espera} segundos para carregamento...")
            time.sleep(intervalo_espera)
            
            # Capturar screenshot em cada tentativa para análise
            nome_arquivo = f"dashboard_tentativa_{tentativa}_de_{max_tentativas}.png"
            capturar_screenshot(driver, nome_arquivo)
            
            # Verificar elementos visíveis no dashboard
            try:
                # Tentar encontrar elementos de tabela
                tabelas = driver.find_elements(By.CSS_SELECTOR, ".tabTable")
                if tabelas:
                    print(f"Encontradas {len(tabelas)} tabelas no dashboard.")
                
                # Tentar encontrar elementos de texto
                textos = driver.find_elements(By.CSS_SELECTOR, ".tab-textRegion")
                if textos:
                    print(f"Encontrados {len(textos)} elementos de texto no dashboard.")
                    
                # Tentar encontrar elementos de gráfico
                graficos = driver.find_elements(By.CSS_SELECTOR, ".tab-viz")
                if graficos:
                    print(f"Encontrados {len(graficos)} elementos de gráfico no dashboard.")
            except Exception as e:
                print(f"Erro ao verificar elementos: {str(e)}")
            
            # Extrair dados usando JavaScript
            print("Executando script JavaScript para extração de dados...")
            try:
                tableau_data = driver.execute_script("""
                // Tenta obter os dados do objeto Tableau
                try {
                    // Inicializa o objeto de dados
                    const data = {};
                    
                    // Coleta texto visível
                    const textElements = document.querySelectorAll('.tab-vizHeaderTitle, .tab-filtersTitle, .tab-textRegion, .tabTextRegion, .tab-caption, .tab-subtitle');
                    data.textContent = Array.from(textElements).map(el => el.textContent.trim());
                    
                    // Busca mais amplamente por tabelas - tenta vários seletores conhecidos do Tableau
                    const tableSelectors = [
                        'table.tabTable', 
                        'table.tableau-data-table', 
                        'div.tabTable table', 
                        'div.tableauViz table',
                        'table'
                    ];
                    
                    let tables = [];
                    for (const selector of tableSelectors) {
                        const foundTables = document.querySelectorAll(selector);
                        if (foundTables && foundTables.length > 0) {
                            console.log(`Encontradas ${foundTables.length} tabelas com seletor: ${selector}`);
                            tables = foundTables;
                            break;
                        }
                    }
                    
                    // Processa as tabelas encontradas
                    data.tables = Array.from(tables).map((table, idx) => {
                        const rows = Array.from(table.querySelectorAll('tr')).map(row => {
                            return Array.from(row.querySelectorAll('td, th')).map(cell => cell.textContent.trim());
                        });
                        return {tableIndex: idx, rows: rows};
                    });
                    
                    // Tenta extrair dados diretamente dos elementos visuais do Tableau
                    const vizElements = document.querySelectorAll('.tab-viz, .tabCanvas');
                    data.vizElements = Array.from(vizElements).length;
                    
                    // Tenta extrair dados dos tooltips (podem conter informações valiosas)
                    const tooltips = document.querySelectorAll('.tab-tooltip, .tab-tooltipText');
                    if (tooltips && tooltips.length > 0) {
                        data.tooltips = Array.from(tooltips).map(tt => tt.textContent.trim());
                    }
                    
                    // Busca por elementos SVG que podem conter dados de gráficos
                    const svgElements = document.querySelectorAll('svg text');
                    if (svgElements && svgElements.length > 0) {
                        data.svgTexts = Array.from(svgElements).map(svg => svg.textContent.trim())
                            .filter(text => text && text.length > 0);
                    }
                    
                    // Tenta extrair dados de hospitalizados por SRAG - busca por textos específicos
                    const sragTexts = Array.from(document.querySelectorAll('*'))
                        .filter(el => el.textContent && el.textContent.includes('SRAG') || 
                                      el.textContent && el.textContent.includes('Hospitaliza'))
                        .map(el => el.textContent.trim());
                    
                    if (sragTexts.length > 0) {
                        data.sragData = sragTexts;
                    }
                    
                    return data;
                } catch (e) {
                    return {error: e.toString(), message: e.message, stack: e.stack};
                }
                """)
                
                if tableau_data:
                    print("Dados extraídos com sucesso via JavaScript!")
                    break  # Sair do loop de tentativas se conseguiu extrair dados
            except Exception as e:
                print(f"Erro ao executar JavaScript: {str(e)}")
                tableau_data = None
                
        # Fim do loop de tentativas
        
        print("Dados extraídos com sucesso!")
        return tableau_data
        
    except TimeoutException:
        print(f"Erro: Tempo limite excedido ({timeout}s) ao carregar o dashboard.")
        return None
    except Exception as e:
        print(f"Erro ao extrair dados: {str(e)}")
        return None
    finally:
        # Voltar ao contexto principal
        driver.switch_to.default_content()


def processar_dados(dados_brutos):
    """
    Processa os dados brutos extraídos do dashboard.
    
    Args:
        dados_brutos (dict): Dados brutos extraídos do dashboard.
        
    Returns:
        pandas.DataFrame: DataFrame com os dados processados ou None em caso de falha.
    """
    if not dados_brutos:
        print("Erro: Não há dados para processar.")
        return None
    
    try:
        print("Processando dados extraídos...")
        
        # Verificar se há dados de tabelas
        if 'tables' in dados_brutos and dados_brutos['tables']:
            dfs = []
            
            # Processar cada tabela encontrada
            for tabela in dados_brutos['tables']:
                if tabela['rows']:
                    # Primeira linha como cabeçalho
                    headers = tabela['rows'][0]
                    data = tabela['rows'][1:]
                    
                    # Criar DataFrame
                    df = pd.DataFrame(data, columns=headers)
                    dfs.append(df)
                    print(f"Tabela {tabela['tableIndex']} processada: {len(df)} linhas, {len(df.columns)} colunas")
            
            # Combinar DataFrames se houver mais de um
            if len(dfs) > 1:
                df_final = pd.concat(dfs, ignore_index=True)
                print(f"Dados combinados: {len(df_final)} linhas, {len(df_final.columns)} colunas")
                return df_final
            elif len(dfs) == 1:
                print(f"Dados processados: {len(dfs[0])} linhas, {len(dfs[0].columns)} colunas")
                return dfs[0]
        
        # Se não encontrou tabelas, tenta processar o conteúdo textual
        if 'textContent' in dados_brutos and dados_brutos['textContent']:
            print("Nenhuma tabela encontrada. Processando conteúdo textual...")
            # Criar um DataFrame simples com o conteúdo textual
            df = pd.DataFrame({'conteudo': dados_brutos['textContent']})
            return df
        
        print("Aviso: Não foi possível processar os dados no formato esperado.")
        # Retornar os dados brutos como DataFrame para análise
        return pd.DataFrame([dados_brutos])
        
    except Exception as e:
        print(f"Erro ao processar dados: {str(e)}")
        return None


def salvar_dados(df, formato='csv'):
    """
    Salva os dados extraídos em um arquivo.
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados a serem salvos.
        formato (str): Formato do arquivo ('csv' ou 'excel').
        
    Returns:
        str: Caminho do arquivo salvo ou None em caso de falha.
    """
    if df is None or df.empty:
        print("Erro: Não há dados para salvar.")
        return None
    
    try:
        # Criar diretório se não existir
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        # Gerar nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if formato.lower() == 'csv':
            filename = f"srag_amazonas_{timestamp}.csv"
            filepath = os.path.join(DATA_DIR, filename)
            df.to_csv(filepath, index=False, encoding='utf-8')
        elif formato.lower() == 'excel':
            filename = f"srag_amazonas_{timestamp}.xlsx"
            filepath = os.path.join(DATA_DIR, filename)
            df.to_excel(filepath, index=False)
        else:
            print(f"Formato não suportado: {formato}")
            return None
        
        print(f"Dados salvos com sucesso em: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Erro ao salvar dados: {str(e)}")
        return None


def capturar_screenshot(driver, nome_arquivo=None):
    """
    Captura uma screenshot do dashboard para análise visual.
    
    Args:
        driver (webdriver.Chrome): Instância do WebDriver.
        nome_arquivo (str, opcional): Nome do arquivo para salvar a screenshot.
        
    Returns:
        str: Caminho do arquivo salvo ou None em caso de falha.
    """
    try:
        # Criar diretório se não existir
        screenshot_dir = os.path.join(DATA_DIR, "screenshots")
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
        
        # Gerar nome do arquivo com timestamp se não fornecido
        if nome_arquivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"dashboard_srag_{timestamp}.png"
        
        filepath = os.path.join(screenshot_dir, nome_arquivo)
        
        # Capturar screenshot
        driver.save_screenshot(filepath)
        print(f"Screenshot salva em: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Erro ao capturar screenshot: {str(e)}")
        return None


def extrair_hospitalizacoes_srag():
    """
    Função principal para extrair dados de hospitalizações por SRAG.
    
    Returns:
        tuple: (DataFrame com os dados, caminho do arquivo salvo) ou (None, None) em caso de falha.
    """
    driver = None
    try:
        print("\n=== Iniciando extração de dados de hospitalizações por SRAG ===")
        print(f"URL do dashboard: {DASHBOARD_URL}")
        
        # Configurar e inicializar o WebDriver
        driver = configurar_webdriver()
        
        # Extrair dados do dashboard
        dados_brutos = extrair_dados_tableau(driver, DASHBOARD_URL)
        
        # Salvar dados brutos para análise (opcional)
        if dados_brutos:
            # Criar diretório se não existir
            raw_dir = os.path.join(DATA_DIR, "raw")
            if not os.path.exists(raw_dir):
                os.makedirs(raw_dir)
                
            # Salvar dados brutos como JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_filepath = os.path.join(raw_dir, f"raw_data_{timestamp}.json")
            
            with open(raw_filepath, 'w', encoding='utf-8') as f:
                json.dump(dados_brutos, f, ensure_ascii=False, indent=2)
            
            print(f"Dados brutos salvos em: {raw_filepath}")
        
        # Capturar screenshot do dashboard para análise visual
        capturar_screenshot(driver)
        
        # Processar dados
        df = processar_dados(dados_brutos)
        
        # Salvar dados processados
        filepath = None
        if df is not None and not df.empty:
            filepath = salvar_dados(df, formato='csv')
            
            # Mostrar primeiras linhas do DataFrame
            print("\nPrimeiras linhas dos dados extraídos:")
            print(df.head())
            
            # Mostrar informações sobre as colunas
            print("\nInformações sobre as colunas:")
            print(f"Número de colunas: {len(df.columns)}")
            print(f"Colunas: {', '.join(df.columns)}")
        
        print("\n=== Extração de dados concluída ===")
        return df, filepath
        
    except Exception as e:
        print(f"\nErro durante a extração de dados: {str(e)}")
        return None, None
    finally:
        # Fechar o navegador
        if driver:
            driver.quit()
            print("Navegador fechado.")


if __name__ == "__main__":
    # Criar diretório de dados se não existir
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Extrair dados de hospitalizações por SRAG
    df, filepath = extrair_hospitalizacoes_srag()
    
    if df is not None and filepath:
        print(f"\nDados extraídos com sucesso e salvos em: {filepath}")
        print(f"Total de registros: {len(df)}")
    else:
        print("\nFalha na extração de dados.")
