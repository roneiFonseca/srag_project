#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extração de dados de PDFs de SRAG hospitalizados
"""

import os
import PyPDF2
import re
import csv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(SCRIPT_DIR, 'dados/fvs_raw')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'dados_processados')

os.makedirs(OUTPUT_DIR, exist_ok=True)

def extrair_dados_pdf(arquivo_pdf):
    """Extrai dados estruturados de um arquivo PDF"""
    try:
        print(f"Processando {arquivo_pdf}...")
        
        # Extrair texto do PDF
        with open(arquivo_pdf, 'rb') as file:
            leitor = PyPDF2.PdfReader(file)
            texto = ""
            for pagina in leitor.pages:
                texto += pagina.extract_text()
        
        # Dividir em linhas e encontrar dados
        linhas = texto.split('\n')
        dados = []
        cabecalho = None
        
        # Padrão para linhas de dados (começam com número e têm data)
        padrao_dados = re.compile(r'^\s*\d+.*\d{2}/\d{2}/\d{4}')
        
        for i, linha in enumerate(linhas):
            # Primeira linha com 'Classi_Fin' é o cabeçalho
            if i == 0 and 'Classi_Fin' in linha:
                cabecalho = linha.split()
            # Linhas que parecem dados SRAG
            elif padrao_dados.match(linha) and len(linha.split()) > 5:
                dados.append(re.split(r'\s+', linha.strip()))
        
        # Se não achou cabeçalho, usar genérico
        if not cabecalho:
            cabecalho = ['DADOS']
        
        print(f"Encontradas {len(dados)} linhas de dados")
        return cabecalho, dados
        
    except Exception as e:
        print(f"Erro ao processar {arquivo_pdf}: {e}")
        return None, []

def salvar_csv(cabecalho, dados, nome_arquivo):
    """Salva os dados em arquivo CSV"""
    try:
        with open(nome_arquivo, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(cabecalho)
            writer.writerows(dados)
        print(f"Dados salvos em: {nome_arquivo}")
    except Exception as e:
        print(f"Erro ao salvar CSV: {e}")

def main():
    """Função principal"""
    # Buscar PDFs na pasta dados
    pasta_dados = PDF_DIR
    if not os.path.exists(pasta_dados):
        print(f"Pasta '{pasta_dados}' não encontrada.")
        return
    
    pdfs = [f for f in os.listdir(pasta_dados) if f.endswith('.pdf')]
    
    if not pdfs:
        print(f"Nenhum arquivo PDF encontrado na pasta '{pasta_dados}'.")
        return
    
    print(f"Encontrados {len(pdfs)} arquivos PDF na pasta '{pasta_dados}'")
    
    for pdf in pdfs:
        caminho_pdf = os.path.join(pasta_dados, pdf)
        cabecalho, dados = extrair_dados_pdf(caminho_pdf)
        
        if dados:
            nome_csv = pdf.replace('.pdf', '_dados.csv')
            salvar_csv(cabecalho, dados, os.path.join(OUTPUT_DIR, nome_csv))

if __name__ == "__main__":
    main()
