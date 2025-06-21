from srag_hospitalizados.covid19_srag_hospitalizados_scraper import SragHospitalizadosScraper
from vacinometro.vacinometro_covid_scrap import VacinometroCovidScraper

if __name__ == "__main__":
    scraper_hospitalizados = SragHospitalizadosScraper()
    scraper_hospitalizados.executar_scraping()
    
    scraper_vacinometro = VacinometroCovidScraper()
    scraper_vacinometro.executar_scraping()