import os
from typing import Dict, Any, List

from apify_client import ApifyClient


APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")


def start_facebook_page_scrape(page_urls: List[str], webhook_base_url: str, job_id: str) -> str:
    """
    Inicia el actor 'apify/facebook-pages-scraper' de Apify en modo no bloqueante
    y registra un webhook para continuar el flujo cuando el run termine.
    
    Acepta una lista de URLs de páginas de Facebook para scrapear todas en paralelo.
    Elimina URLs duplicadas automáticamente ya que Apify no las acepta.

    Devuelve el run_id del actor lanzado para tracking/cancelación.
    """
    client = ApifyClient(APIFY_TOKEN)

    # Eliminar URLs duplicadas manteniendo el orden de primera aparición
    # Usamos dict.fromkeys() para mantener el orden (Python 3.7+)
    unique_urls = list(dict.fromkeys(page_urls))
    
    print(f"📊 URLs originales: {len(page_urls)}, URLs únicas: {len(unique_urls)}")
    if len(page_urls) != len(unique_urls):
        print(f"⚠️ Se eliminaron {len(page_urls) - len(unique_urls)} URLs duplicadas")
    
    # Convertir la lista de URLs únicas al formato que espera el actor
    start_urls = [{"url": url, "method": "GET"} for url in unique_urls]
    
    # Formato que espera el actor de Facebook Pages Scraper
    run_input: Dict[str, Any] = {
        "startUrls": start_urls,
        "proxyConfiguration": {
            "useApifyProxy": True  # ✅ Usar proxies de Apify para evitar bloqueos geográficos
        }
    }
    
    print(f"🚀 Iniciando actor de Facebook Pages con {len(unique_urls)} páginas únicas")
    print(f"🔗 URLs únicas enviadas: {unique_urls[:5]}...")  # Solo mostrar las primeras 5

    run = client.actor("apify/facebook-pages-scraper").start(
        run_input=run_input,
        memory_mbytes=512,  # 512 MB de memoria
        webhooks=[
            {
                "event_types": ["ACTOR.RUN.SUCCEEDED"],
                "request_url": f"{webhook_base_url}/webhook-facebook-pages-succeeded",
                "payload_template": f'{{"job_id": "{job_id}", "resource": {{{{resource}}}}}}'
            }
        ],
    )

    return run["id"]


def build_facebook_pages_table_items(dataset_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extrae solo los campos esenciales de cada página de Facebook para el frontend.
    
    Campos extraídos:
    - facebookUrl: URL de la página de Facebook
    - likes: Número de likes
    - title: Título de la página
    - address: Dirección física
    - pageId: ID único de la página
    - pageName: Nombre único de la página
    - pageUrl: URL de la página
    - phone: Teléfono de contacto
    - email: Email de contacto
    - website: Sitio web
    - followers: Número de seguidores
    - business_service_area: Área de servicio del negocio
    """
    simplified_items: List[Dict[str, Any]] = []
    
    # Campos que queremos extraer
    desired_fields = [
        "facebookUrl",
        "likes",
        "title",
        "address",
        "pageId",
        "pageName",
        "pageUrl",
        "phone",
        "email",
        "website",
        "followers",
        "business_service_area"
    ]
    
    for item in dataset_items:
        simplified_item: Dict[str, Any] = {}
        
        # Extraer solo los campos deseados si existen
        for field in desired_fields:
            if field in item:
                simplified_item[field] = item.get(field)
            else:
                # Si el campo no existe, lo dejamos como None para que el frontend sepa que no está disponible
                simplified_item[field] = None
        
        simplified_items.append(simplified_item)
    
    return simplified_items

