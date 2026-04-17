"""
Scraper de leads de LinkedIn vía Apollo (actor 'peakydev/leads-scraper' en Apify).

Recibe job_title, country, state y number_of_leads. Lanza el actor en modo
no bloqueante y registra un webhook para procesar los resultados al terminar.

Autor: Ing. Kevin Inofuente Colque - DataPath
"""

import os
from typing import Dict, Any, List

from apify_client import ApifyClient


APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
ACTOR_ID = "peakydev/leads-scraper"


def start_linkedin_scrape(
    job_title: str,
    country: str,
    state: str,
    number_of_leads: int,
    webhook_base_url: str,
    job_id: str,
) -> str:
    """
    Lanza el actor de Apollo/LinkedIn en Apify y devuelve el run_id.
    """
    client = ApifyClient(APIFY_TOKEN)

    person_locations: List[str] = []
    if state and country:
        person_locations.append(f"{state}, {country}")
    elif country:
        person_locations.append(country)

    run_input: Dict[str, Any] = {
        "totalRecords": int(number_of_leads),
        "personTitles": [job_title] if job_title else [],
    }
    if person_locations:
        run_input["personLocations"] = person_locations

    run = client.actor(ACTOR_ID).start(
        run_input=run_input,
        webhooks=[{
            "event_types": ["ACTOR.RUN.SUCCEEDED"],
            "request_url": f"{webhook_base_url}/webhook-linkedin-apollo-succeeded",
            "payload_template": f'{{"job_id": "{job_id}", "resource": {{{{resource}}}}}}',
        }],
    )

    return run["id"]


def get_dataset_items(dataset_id: str) -> List[Dict[str, Any]]:
    """Lee los items del dataset producido por el actor."""
    client = ApifyClient(APIFY_TOKEN)
    return list(client.dataset(dataset_id).iterate_items())


def build_final_leads(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normaliza los items del actor para guardarlos en aria_suite_leads_per_user.
    El actor devuelve campos como name, first_name, last_name, email, phone,
    title, organization (con name, website_url, industry, city, country, etc.),
    linkedin_url, etc.
    """
    leads: List[Dict[str, Any]] = []
    for it in items:
        org = it.get("organization") or {}
        full_name = it.get("name") or f"{it.get('first_name', '')} {it.get('last_name', '')}".strip()
        location_parts = [
            it.get("city"),
            it.get("state"),
            it.get("country"),
        ]
        location = ", ".join([p for p in location_parts if p])

        lead = {
            "title": full_name,
            "fullName": full_name,
            "email": it.get("email") or "",
            "phone": it.get("phone") or it.get("organization_phone") or "",
            "phoneUnformatted": it.get("phone") or "",
            "mobileNumber": it.get("mobile_phone") or "",
            "jobTitle": it.get("title") or "",
            "linkedinProfile": it.get("linkedin_url") or "",
            "categoryName": it.get("seniority") or "",
            "address": location,
            "city": it.get("city") or "",
            "industry": (org.get("industry") if org else "") or it.get("industry") or "",
            "companyName": (org.get("name") if org else "") or "",
            "companyWebsite": (org.get("website_url") if org else "") or "",
            "companyLinkedin": (org.get("linkedin_url") if org else "") or "",
            "companyPhoneNumber": (org.get("phone") if org else "") or "",
            "companySize": (org.get("estimated_num_employees") if org else "") or "",
            "businessModel": "",
            "website": (org.get("website_url") if org else "") or "",
            "street": "",
            "emails": it.get("email") or "",
        }
        leads.append(lead)

    return leads
