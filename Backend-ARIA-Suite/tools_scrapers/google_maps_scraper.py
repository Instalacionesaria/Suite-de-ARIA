import os
from typing import Dict, Any, List, Optional

from apify_client import ApifyClient


APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")


def start_google_maps_scrape(
    business_type: str,
    location: str,
    get_emails: bool,
    webhook_base_url: str,
    job_id: str,
) -> str:
    """
    Inicia el actor 'compass/crawler-google-places' de Apify en modo no bloqueante
    y registra un webhook para continuar el flujo cuando el run termine.

    Devuelve el run_id del actor lanzado para tracking/cancelación.
    """
    client = ApifyClient(APIFY_TOKEN)

    run_input: Dict[str, Any] = {
        "searchStringsArray": [business_type],
        "locationQuery": location,
        "maxCrawledPlaces": 1,
        "maxAutomaticZoomOut": 0,
        "language": "es",
        "maxImages": 0,
        "maxReviews": 0,
        "proxyConfiguration": {"useApifyProxy": True},
    }
    if get_emails:
        run_input["maximumLeadsEnrichmentRecords"] = 2

    run = client.actor("compass/crawler-google-places").start(
        run_input=run_input,
        webhooks=[{
            "event_types": ["ACTOR.RUN.SUCCEEDED"],
            "request_url": f"{webhook_base_url}/webhook-google-places-succeeded",
            "payload_template": f'{{"job_id": "{job_id}", "resource": {{{{resource}}}}}}',
        }],
    )

    return run["id"]


def start_website_crawler(
    urls_to_crawl: List[Dict[str, str]],
    webhook_base_url: str,
    job_id: str,
    google_places_dataset_id: str,
) -> str:
    """
    Inicia el actor 'apify/website-content-crawler' para analizar los sitios web
    de los leads encontrados en Google Places.

    Devuelve el run_id del actor lanzado.
    """
    client = ApifyClient(APIFY_TOKEN)

    crawler_run_input = {
        "startUrls": urls_to_crawl,
        "maxCrawlDepth": 0,
        "maxConcurrency": 10,
    }

    payload_template = f'{{ "job_id": "{job_id}", "google_places_dataset_id": "{google_places_dataset_id}", "resource": {{{{resource}}}} }}'

    run = client.actor("apify/website-content-crawler").start(
        run_input=crawler_run_input,
        webhooks=[{
            "event_types": ["ACTOR.RUN.SUCCEEDED"],
            "request_url": f"{webhook_base_url}/webhook-website-crawler-succeeded",
            "payload_template": payload_template,
        }],
    )

    return run["id"]


def get_dataset_items(dataset_id: str) -> List[Dict[str, Any]]:
    """Obtiene los items de un dataset de Apify."""
    client = ApifyClient(APIFY_TOKEN)
    return client.dataset(dataset_id).list_items().items


def build_final_leads(
    dataset_items: List[Dict],
    get_emails: bool,
    business_models_map: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """
    Construye la lista final de leads normalizados a partir de los datos
    crudos de Google Places, con enriquecimiento de emails opcional.
    """
    final_results_list: List[Dict[str, Any]] = []
    base_fields = [
        "title", "categoryName", "address", "neighborhood",
        "street", "website", "phone", "phoneUnformatted",
    ]
    enrichment_fields = [
        "fullName", "jobTitle", "email", "emails", "linkedinProfile",
        "mobileNumber", "companyName", "companyWebsite", "companyLinkedin",
        "companyPhoneNumber", "companySize", "industry", "city",
    ]

    for item in dataset_items:
        final_lead = {field: None for field in base_fields + enrichment_fields + ["businessModel"]}
        for field in base_fields:
            if item.get(field):
                final_lead[field] = item.get(field)
        if get_emails and item.get("leadsEnrichment"):
            enrichment_data = item["leadsEnrichment"][0]
            for field in enrichment_fields:
                if enrichment_data.get(field):
                    final_lead[field] = enrichment_data.get(field)
        if business_models_map:
            lead_website = final_lead.get("website")
            final_lead["businessModel"] = business_models_map.get(
                lead_website, "N/A" if lead_website else "N/A (Sin sitio web)"
            )
        final_results_list.append(final_lead)
    return final_results_list
