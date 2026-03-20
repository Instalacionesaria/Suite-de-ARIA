import os
from typing import Dict, Any, List

from apify_client import ApifyClient


APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")


def start_facebook_ads_scrape(scrape_url: str, webhook_base_url: str, job_id: str) -> str:
    """
    Inicia el actor 'curious_coder/facebook-ads-library-scraper' de Apify en modo no bloqueante
    y registra un webhook para continuar el flujo cuando el run termine.

    Devuelve el run_id del actor lanzado para tracking/cancelación.
    """
    client = ApifyClient(APIFY_TOKEN)

    # Formato exacto que espera el actor según la documentación de Apify
    run_input: Dict[str, Any] = {
        "count": 1000,  # Límite máximo de anuncios a scrapear por búsqueda
        "scrapeAdDetails": False,  # No scrapear detalles adicionales (más rápido)
        "scrapePageAds.activeStatus": "all",  # Estado de los anuncios
        "scrapePageAds.countryCode": "ALL",  # Código de país
        "urls": [
            {
                "url": scrape_url,  # URL completa de Facebook Ads Library
                "method": "GET"  # Método HTTP
            }
        ],
        "proxyConfiguration": {
            "useApifyProxy": True  # ✅ Usar proxies de Apify para evitar bloqueos geográficos
        }
    }
    
    print(f"🚀 Iniciando actor de Facebook Ads con input: {run_input}")
    print(f"🔗 URL enviada: {scrape_url}")

    run = client.actor("curious_coder/facebook-ads-library-scraper").start(
        run_input=run_input,
        memory_mbytes=512,  # 512 MB (el mínimo) - 1 URL requiere 512 MB según el actor
        webhooks=[
            {
                "event_types": ["ACTOR.RUN.SUCCEEDED"],
                "request_url": f"{webhook_base_url}/webhook-facebook-ads-succeeded",
                "payload_template": f'{{"job_id": "{job_id}", "resource": {{{{resource}}}}}}'
            }
        ],
    )

    return run["id"]


def build_facebook_ads_table_items(dataset_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extrae solo los 3 campos esenciales de cada anuncio:
    - page_name: Nombre de la página/anunciante
    - page_profile_uri: URL del perfil de Facebook
    - page_id: ID único de la página
    """
    simplified_items: List[Dict[str, Any]] = []
    
    for item in dataset_items:
        # Extraer los campos desde snapshot (donde están en la mayoría de los casos)
        snapshot = item.get("snapshot", {})
        
        # Construir item simplificado con solo los 3 campos
        simplified_item = {
            "page_name": snapshot.get("page_name") or item.get("page_name"),
            "page_profile_uri": snapshot.get("page_profile_uri") or item.get("page_profile_uri"),
            "page_id": snapshot.get("page_id") or item.get("page_id"),
        }
        
        simplified_items.append(simplified_item)
    
    return simplified_items


