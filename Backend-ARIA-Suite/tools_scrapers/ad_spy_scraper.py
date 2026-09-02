"""
Espía de Anuncios (Ad Spy) — Meta Ad Library.

Separado del scraper de Facebook de Prospección (que solo saca page_name/uri/id
para descubrir anunciantes). Aquí conservamos la data RICA de cada anuncio:
creatividad, fecha de inicio (→ longevidad), tipo (video/imagen/carrusel), copy.

Usa el mismo actor de Apify (curious_coder/facebook-ads-library-scraper) pero
construyendo una URL de BÚSQUEDA de la Ad Library a partir del nicho/marca/página.

Autor: Ing. Kevin Inofuente Colque - DataPath
"""

import os
from datetime import datetime, timezone
from urllib.parse import quote
from typing import Dict, Any, List

from apify_client import ApifyClient


APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
ACTOR_ID = "curious_coder/facebook-ads-library-scraper"


def build_meta_ad_library_url(query: str, country: str = "ALL") -> str:
    """Arma una URL de búsqueda por palabra clave de la Meta Ad Library."""
    q = quote((query or "").strip())
    cc = ((country or "ALL").strip().upper()) or "ALL"
    return (
        "https://www.facebook.com/ads/library/"
        f"?active_status=all&ad_type=all&country={cc}"
        f"&q={q}&search_type=keyword_unordered&media_type=all"
    )


def start_ad_spy_scrape(
    query: str,
    country: str,
    webhook_base_url: str,
    job_id: str,
    count: int = 60,
) -> str:
    """Lanza el actor sobre una búsqueda de la Ad Library y registra el webhook. Devuelve run_id."""
    client = ApifyClient(APIFY_TOKEN)
    scrape_url = build_meta_ad_library_url(query, country)

    run_input: Dict[str, Any] = {
        "count": count,
        "scrapeAdDetails": False,
        "scrapePageAds.activeStatus": "all",
        "scrapePageAds.countryCode": (country or "ALL").upper(),
        "urls": [{"url": scrape_url, "method": "GET"}],
        "proxyConfiguration": {"useApifyProxy": True},
    }

    print(f"🕵️  Ad Spy: '{query}' ({country}) → {scrape_url}")
    run = client.actor(ACTOR_ID).start(
        run_input=run_input,
        memory_mbytes=512,
        webhooks=[{
            "event_types": ["ACTOR.RUN.SUCCEEDED"],
            "request_url": f"{webhook_base_url}/webhook-ad-spy-succeeded",
            "payload_template": f'{{"job_id": "{job_id}", "resource": {{{{resource}}}}}}',
        }],
    )
    return run["id"] if isinstance(run, dict) else run.id


def get_dataset_items(dataset_id: str) -> List[Dict[str, Any]]:
    client = ApifyClient(APIFY_TOKEN)
    return list(client.dataset(dataset_id).iterate_items())


def _media_type(display_format: str, snap: Dict[str, Any]) -> str:
    df = (display_format or "").upper()
    cards = snap.get("cards") or []
    if df in ("DCO", "CAROUSEL") or len(cards) > 1:
        return "carrusel"
    if df == "VIDEO" or (snap.get("videos")):
        return "video"
    return "imagen"


def _thumbnail(snap: Dict[str, Any]) -> str:
    vids = snap.get("videos") or []
    if vids and vids[0].get("video_preview_image_url"):
        return vids[0]["video_preview_image_url"]
    imgs = snap.get("images") or []
    if imgs and imgs[0].get("resized_image_url"):
        return imgs[0]["resized_image_url"]
    cards = snap.get("cards") or []
    if cards:
        c0 = cards[0]
        return c0.get("resized_image_url") or c0.get("video_preview_image_url") or ""
    return snap.get("page_profile_picture_url") or ""


def build_ad_spy_items(dataset_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normaliza cada anuncio a lo que necesita la tarjeta del panel, y ordena por longevidad.

    `page_profile_uri` NO es para la tarjeta: es la URL de la pagina de Facebook, y es lo unico
    que el actor `apify/facebook-pages-scraper` acepta como entrada. Sin ella, el Espia puede
    descubrir anunciantes y NO se les puede sacar el telefono, el email ni la web — que es lo
    que hace el paso 2 de Prospeccion en Frio.

    Estaba disponible y se tiraba: `build_facebook_ads_table_items` la lee del MISMO `snapshot`,
    porque los dos normalizadores procesan la salida del mismo actor
    (`curious_coder/facebook-ads-library-scraper`). La diferencia entre los dos nunca fue de
    datos, era de que se conservaba.
    """
    now = datetime.now(timezone.utc).timestamp()
    out: List[Dict[str, Any]] = []

    for it in dataset_items:
        # el actor a veces devuelve un item de error como primer elemento
        if not isinstance(it, dict) or "error" in it and len(it) == 1:
            continue
        snap = it.get("snapshot") or {}
        start = it.get("start_date") or 0
        end = it.get("end_date") or 0
        ref_end = end if (end and not it.get("is_active")) else now
        days = int((ref_end - start) // 86400) if start else 0

        body = snap.get("body")
        if isinstance(body, dict):
            body_text = body.get("text") or ""
        elif isinstance(body, str):
            body_text = body
        else:
            body_text = ""

        out.append({
            "ad_archive_id": it.get("ad_archive_id"),
            "page_name": it.get("page_name") or snap.get("page_name") or "",
            "page_id": it.get("page_id"),
            # Mismo orden de lectura que `facebook_ads_scraper`: primero el snapshot.
            "page_profile_uri": snap.get("page_profile_uri") or it.get("page_profile_uri") or "",
            "is_active": bool(it.get("is_active")),
            "days_active": max(days, 0),
            "start_date_formatted": it.get("start_date_formatted") or "",
            "media_type": _media_type(snap.get("display_format"), snap),
            "thumbnail_url": _thumbnail(snap),
            "body_text": body_text,
            "title": snap.get("title") or "",
            "caption": snap.get("caption") or "",
            "cta_text": snap.get("cta_text") or "",
            "link_url": snap.get("link_url") or "",
            "ad_library_url": it.get("ad_library_url") or it.get("url") or "",
        })

    out.sort(key=lambda a: a["days_active"], reverse=True)
    return out
