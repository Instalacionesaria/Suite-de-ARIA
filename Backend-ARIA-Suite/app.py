# === app.py (ARIA Suite Backend - v2.0 con Agente de Onboarding) ===

import os
import datetime
import requests
import json
import traceback
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from apify_client import ApifyClient
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
load_dotenv()

# --- Agente de Onboarding ---
from agente import chat_con_agente

# --- Módulos de scrapers (se añadirán después) ---
try:
    from tools_scrapers import google_maps_scraper
except ImportError:
    google_maps_scraper = None
    print("⚠️ google_maps_scraper no disponible aún")

try:
    from tools_scrapers import facebook_ads_scraper
except ImportError:
    facebook_ads_scraper = None
    print("⚠️ facebook_ads_scraper no disponible aún")

try:
    from tools_scrapers import facebook_pages_scraper
except ImportError:
    facebook_pages_scraper = None
    print("⚠️ facebook_pages_scraper no disponible aún")

try:
    from tools_scrapers import linkedin_apollo_scraper
except ImportError:
    linkedin_apollo_scraper = None
    print("⚠️ linkedin_apollo_scraper no disponible aún")

try:
    from tools_scrapers import ad_spy_scraper
except ImportError:
    ad_spy_scraper = None
    print("⚠️ ad_spy_scraper no disponible aún")

try:
    from tools_scrapers.envio_de_correo import enviar_correo
except ImportError:
    enviar_correo = None
    print("⚠️ envio_de_correo no disponible aún")

try:
    from tools_scrapers.highlevel_mcp import ejecutar_orden_highlevel
except ImportError:
    ejecutar_orden_highlevel = None
    print("⚠️ highlevel_mcp no disponible aún")

try:
    from tools_scrapers.envio_de_correo_LC_HighLevel import enviar_correo_masivo_lc, enviar_whatsapp_masivo_lc
except ImportError:
    enviar_correo_masivo_lc = None
    enviar_whatsapp_masivo_lc = None
    print("⚠️ envio_de_correo_LC_HighLevel no disponible aún")


# =============================================
# 1. MODELOS DE DATOS
# =============================================

# -- Onboarding Chat --
class MessageItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[MessageItem] = []
    model: Optional[str] = None
    api_key: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    extracted_data: dict | None = None

# -- Google Places Scraping --
class ScrapingRequest(BaseModel):
    businessType: str
    location: str
    getEmails: bool
    getBusinessModel: bool
    timestamp: datetime.datetime
    # ── DOS IDENTIDADES MIENTRAS ARIA-brain SIGA VIVO ────────────────────────
    #
    # `org_id` es la nueva y la que manda ARIA-Comando-Central desde la sesión. `cliente_id` es
    # la de ARIA-brain, que es **el hub que los alumnos usan HOY** y que no tiene noción de
    # organización: su identidad es `aria_brain_clientes.id`.
    #
    # Las dos son opcionales en el modelo y obligatorias en la práctica: `resolver_org()` exige
    # una y traduce la vieja. Ponerlas obligatorias acá habría hecho que el despliegue de este
    # backend rompiera la Prospección de todos los alumnos de ARIA-brain — Pydantic rechaza el
    # cuerpo antes de que ninguna lógica pueda traducir nada.
    #
    # Ninguna llega del navegador en ninguno de los dos hubs: las dos salen de la sesión, del
    # lado del servidor. Ver el encabezado de los proxies.
    org_id: Optional[str] = None
    cliente_id: Optional[str] = None
    maxLeads: int = 100

class ApifyWebhookResource(BaseModel):
    """
    El objeto `run` de Apify, tal como llega en el cuerpo del webhook.

    ═══════════════════════════════════════════════════════════════════════════
    EL COSTO YA VENÍA Y ESTE MODELO LO TIRABA

    La plantilla de los seis webhooks manda `{{resource}}` ENTERO —el run completo— y Pydantic
    descarta en silencio todo campo que el modelo no declare. Declaraba uno solo, así que
    `usageTotalUsd` llegaba en cada webhook y se perdía.

    O sea que medir el gasto de Apify no necesita ninguna llamada a su API ni el token en
    ningún lugar nuevo: sólo dejar de descartar un campo.
    ═══════════════════════════════════════════════════════════════════════════
    """

    defaultDatasetId: str

    # El identificador del run que terminó. Sirve para rastrear un cargo de la factura de Apify
    # hasta un trabajo nuestro, y como plan B si algún día `usageTotalUsd` no viniera.
    id: Optional[str] = None

    # Lo que ESTA corrida gastó, en dólares, ya sumado por Apify.
    #
    # `Optional` y no obligatorio, y la razón importa: estos webhooks son los que GUARDAN LOS
    # LEADS. Un modelo que exija el campo hace que Pydantic rechace el cuerpo entero si falta,
    # y ahí se cambiaría una columna de contabilidad vacía por leads pagados que se pierden.
    usageTotalUsd: Optional[float] = None

class GooglePlacesWebhookPayload(BaseModel):
    job_id: str
    resource: ApifyWebhookResource

class WebsiteCrawlerWebhookPayload(BaseModel):
    job_id: str
    google_places_dataset_id: str
    resource: ApifyWebhookResource

# -- Facebook Ads --
class FacebookAdsScrapingRequest(BaseModel):
    url: str
    org_id: Optional[str] = None
    cliente_id: Optional[str] = None
    timestamp: str
    scrape_url: Optional[str] = None
    link: Optional[str] = None

    def get_url(self) -> str:
        return self.url or self.scrape_url or self.link or ""

# -- Facebook Pages --
class FacebookPageItem(BaseModel):
    page_name: str
    page_profile_uri: str
    page_id: str

class FacebookPagesScrapingRequest(BaseModel):
    pages: List[FacebookPageItem]
    org_id: Optional[str] = None
    cliente_id: Optional[str] = None
    timestamp: str

    def get_page_urls(self) -> List[str]:
        return [page.page_profile_uri for page in self.pages]

    def get_original_pages_data(self) -> List[Dict[str, str]]:
        return [page.model_dump() for page in self.pages]

# -- LinkedIn (Apollo) Scraping --
class LinkedInScrapingRequest(BaseModel):
    job_title: str
    country: str
    state: Optional[str] = ""
    number_of_leads: int = 100
    org_id: Optional[str] = None
    cliente_id: Optional[str] = None
    timestamp: Optional[str] = None

# -- Ad Spy (Espía de Anuncios — Meta Ad Library) --
class AdSpyRequest(BaseModel):
    query: str
    country: Optional[str] = "ALL"
    source: Optional[str] = "meta"        # por ahora solo 'meta'
    count: Optional[int] = 60
    org_id: Optional[str] = None
    cliente_id: Optional[str] = None                            # solo identidad; NO consume saldo de leads

# -- HighLevel MCP --
class HighLevelMCPRequest(BaseModel):
    pit_token: str
    location_id: str
    orden: str

# -- Envío de Correos --
class EmailRequest(BaseModel):
    gmail_user: str
    gmail_app_password: str
    nombre_remitente: str
    destinatarios: List[str]
    mensaje: str

# -- Envío de Correos via LeadConnector (HighLevel) --
class EmailDestinatarioLC(BaseModel):
    email: str
    nombre: Optional[str] = ""
    telefono: Optional[str] = ""
    empresa: Optional[str] = ""

class EmailLCRequest(BaseModel):
    pit_token: str
    location_id: str
    asunto: str
    mensaje: str
    destinatarios: List[EmailDestinatarioLC]
    email_from: Optional[str] = ""

# -- Envío de WhatsApp via LeadConnector (HighLevel) --
class WhatsAppDestinatarioLC(BaseModel):
    telefono: str
    nombre: Optional[str] = ""
    email: Optional[str] = ""
    empresa: Optional[str] = ""

class WhatsAppLCRequest(BaseModel):
    pit_token: str
    location_id: str
    mensaje: str
    destinatarios: List[WhatsAppDestinatarioLC]


# =============================================
# 2. CONFIGURACIÓN Y CLAVES
# =============================================
app = FastAPI(
    title="ARIA Suite Backend API",
    description="Backend con agente de onboarding y orquestación de scraping con webhooks encadenados.",
    version="2.0.0",
)

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "https://leads.ariaia.com",
    "https://aria-scrapper.vercel.app",
    "https://frontend-aria-suite-2026.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
apify_token = os.getenv("APIFY_API_TOKEN")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")

# Leads gratis que recibe una organización nueva al provisionarse (primer uso).
# Se puede sobrescribir con la env var LEADS_GRATIS_NUEVO_CLIENTE.
LEADS_GRATIS_NUEVO_CLIENTE = int(os.getenv("LEADS_GRATIS_NUEVO_CLIENTE", "100"))


# =============================================
# LAS TRES TABLAS, Y POR QUÉ SON CONSTANTES
# =============================================
# Antes estaban escritas a mano en 28 f-strings. Como constantes, cambiar de base es cambiar
# tres líneas — y, más importante, un nombre mal escrito falla al importar el módulo en vez de
# fallar en la petición número mil, que es cuando PostgREST contesta 404 y el scraping se cae
# después de haber pagado la corrida de Apify.
#
# ── EL CAMBIO DE FONDO: LA LLAVE ES LA ORGANIZACIÓN ──────────────────────────
#
# Estas tablas viven en SOFIA (`pajh…`), el proyecto de ARIA-Comando-Central, y no en `urxu…`.
# Ver `migraciones/006_aria_cc_scraper.sql`. Tres consecuencias en este archivo:
#
#   1. `org_id` reemplaza a `cliente_id` Y a `user_id`. El monedero ya no tiene un `id`
#      propio: `org_id` ES su clave primaria. Se fue un nivel de indirección — antes había
#      que leer `usuarios_scraper` para traducir `cliente_id` → `id` antes de crear un job.
#
#   2. **Se cayeron las identidades legacy.** `correo_electronico` y `userId` ya no son
#      caminos posibles, y no por prolijidad: la tabla nueva NO TIENE esas columnas. Es la
#      Fase 3 de `migracion_cliente_id.sql` ("/login y /funnel-scrape eliminados"), que dejó
#      de ser opcional — una consulta por email contra `aria_cc_scraper_monedero` responde
#      400 de PostgREST, no un usuario no encontrado.
#
#   3. Los trabajos llevan `fuente` como columna de verdad. Antes el scraper se adivinaba
#      leyendo el prefijo de `business_type` ("LinkedIn: …", "AdSpy: …"), que es lo que el
#      script de copia tiene que hacer para las filas viejas. Las nuevas lo declaran.
TABLA_MONEDERO = "aria_cc_scraper_monedero"
TABLA_TRABAJOS = "aria_cc_scraper_trabajos"
TABLA_LEADS = "aria_cc_scraper_leads"


# =============================================
# 3. FUNCIONES AUXILIARES
# =============================================
def get_supabase_headers(content_type: bool = False, prefer_return: bool = False) -> dict:
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    if content_type:
        headers["Content-Type"] = "application/json"
    if prefer_return:
        headers["Prefer"] = "return=representation"
    return headers


# ── LOS WEBHOOKS NO CAMBIAN DE FORMA, Y ES A PROPÓSITO ───────────────────────
#
# La clave primaria del trabajo es `(org_id, id)`, así que se podría pensar que los seis
# webhooks de Apify tienen que traer `org_id` además del `job_id`. NO hace falta, y no meterlo
# fue deliberado:
#
#   · Cada webhook ya lee la fila del trabajo para saber qué hacer con ella, y esa fila TRAE
#     `org_id`. Un campo más en el payload sería un dato duplicado que puede contradecir a la
#     base — y ante la contradicción habría que creerle a la base igual.
#
#   · La búsqueda por `id` solo sigue siendo rápida: la 006 crea un índice COMÚN sobre `id`
#     (común, no único — un único sin `org_id` filtraría la existencia de filas ajenas, y
#     `aplicar_aislamiento` lo rechazaría).
#
#   · Y el modo de falla de la alternativa es peor: un webhook ya en vuelo durante el
#     despliegue llegaría sin el campo nuevo, Pydantic lo rechazaría, y se perdería un
#     scraping YA PAGADO.


# ═════════════════════════════════════════════════════════════════════════════
# EL PUENTE: `cliente_id` DE ARIA-brain → `org_id`
# ═════════════════════════════════════════════════════════════════════════════
# Un mapa chico (una entrada por organización vinculada) que se pide a la base y se guarda un
# minuto. Se cachea porque lo consulta CADA petición de ARIA-brain y el mapa cambia sólo cuando
# alguien vincula una organización nueva — pedirlo cada vez sería una consulta de más por
# scraping, y no cachearlo nunca sería una por sondeo, que corre cada cinco segundos.
#
# Un minuto y no una hora: vincular una organización y que el alumno tenga que esperar a que
# expire un caché largo es exactamente el tipo de espera que nadie relaciona con la causa.
_PUENTE: Dict[str, str] = {}
_PUENTE_VENCE = 0.0
_PUENTE_TTL_S = 60


def _puente() -> Dict[str, str]:
    global _PUENTE, _PUENTE_VENCE
    import time

    if _PUENTE and time.time() < _PUENTE_VENCE:
        return _PUENTE
    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/aria_cc_puente_scraper",
            headers=get_supabase_headers(content_type=True),
            json={},
            timeout=15,
        )
        if r.ok:
            _PUENTE = {str(f["cliente_id"]): f["org_id"] for f in r.json()}
            _PUENTE_VENCE = time.time() + _PUENTE_TTL_S
    except Exception as e:
        # Fail-open sobre el caché viejo y NO sobre un mapa vacío: si la base parpadea, un mapa
        # vacío convertiría todas las peticiones de ARIA-brain en "no estás vinculado", que es
        # un mensaje FALSO y manda al alumno a pedir un vínculo que ya tiene.
        print(f"No se pudo refrescar el puente cliente_id → org_id: {e}")
    return _PUENTE


def resolver_org(org_id: Optional[str], cliente_id: Optional[str]) -> str:
    """
    La organización de una petición, venga de cualquiera de los dos hubs.

    ═══════════════════════════════════════════════════════════════════════════
    POR QUÉ ACEPTA LA IDENTIDAD VIEJA, Y HASTA CUÁNDO

    Este backend lo comparten DOS hubs:

      · **ARIA-Comando-Central** manda `org_id`. Es el destino.
      · **ARIA-brain** manda `cliente_id`, y es el hub que los alumnos usan HOY. Su proxy
        (`app-next/app/api/scrape/route.ts`) deriva `cliente_id` del token de sesión y no
        tiene ninguna noción de organización.

    Exigir `org_id` habría dejado sin Prospección, sin Mis Leads y sin saldo a todos los
    alumnos de ARIA-brain en el momento del despliegue. Así que se traduce.

    ── LA CONSECUENCIA QUE HAY QUE DECIR EN VOZ ALTA ─────────────────────────

    La traducción necesita que la organización esté vinculada al alumno del hub
    (`organizaciones_credenciales.fundaciones_cliente_id`). **Un alumno de ARIA-brain que no
    corresponda a ninguna organización de Comando Central no puede scrapear**, y no hay forma
    de arreglarlo desde acá: la columna `org_id` tiene una foránea a `identidad.organizaciones`,
    así que su monedero no se puede ni representar en el esquema nuevo.

    Es el mismo freno que la migración eliminó para Comando Central, que reaparece del otro
    lado y por el lado contrario. Se responde con un mensaje que dice qué falta en vez de un
    500, para que se vea como lo que es: una cuenta sin organización, no una falla del motor.

    Esta función se borra el día que ARIA-brain deje de llamar a este backend.
    ═══════════════════════════════════════════════════════════════════════════
    """
    if org_id:
        return org_id

    if not cliente_id:
        raise HTTPException(status_code=400, detail="Falta org_id.")

    org = _puente().get(str(cliente_id))
    if not org:
        raise HTTPException(
            status_code=409,
            detail=(
                "Esta cuenta todavía no está asociada a una organización, y el scraping se "
                "cobra por organización. Avisale al equipo de ARIA para que la asocien."
            ),
        )
    return org


def create_scraping_job(org_id: str, request: ScrapingRequest) -> str:
    headers = get_supabase_headers(content_type=True, prefer_return=True)
    job_data = {
        "org_id": org_id,
        "fuente": "maps",
        "status": "PENDING",
        "business_type": request.businessType,
        "location": request.location,
        "get_emails": request.getEmails,
        "get_business_model": request.getBusinessModel,
        # Se guarda el tope pedido para recortar los resultados en el webhook
        # (el actor puede traer 1-2 de más). Se sobrescribe con los resultados finales.
        "results_data": {"max_leads": request.maxLeads},
    }
    response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}", headers=headers, json=job_data)
    if response.status_code == 201:
        return response.json()[0]["id"]
    else:
        raise HTTPException(status_code=500, detail="No se pudo registrar el trabajo.")


def update_job_run_id(job_id: str, run_id: str):
    headers = get_supabase_headers(content_type=True)
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}?id=eq.{job_id}",
        headers=headers,
        json={"apify_actor_run_id": run_id, "status": "RUNNING"},
    )
    print(f"Job {job_id} vinculado con Apify Run ID: {run_id}. Estado: RUNNING.")


def update_job_results(job_id: str, status: str, results: Optional[Dict] = None, error_message: Optional[str] = None) -> bool:
    headers = get_supabase_headers(content_type=True)
    update_data = {"status": status}
    if error_message:
        update_data["error_message"] = error_message
    if results:
        update_data["results_data"] = results
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}?id=eq.{job_id}",
        headers=headers,
        json=update_data,
    )
    if response.status_code in [200, 204]:
        return True
    else:
        print(f"Error al actualizar resultados del job {job_id}. Status: {response.status_code}, Response: {response.text}")
        return False


def add_job_cost(job_id: str, usd: Optional[float]) -> None:
    """
    Suma al costo del trabajo lo que gastó un run de Apify.

    ═══════════════════════════════════════════════════════════════════════════
    ACUMULA, NO PISA — Y ESO ES TODO EL PUNTO

    Un trabajo de Google Maps son DOS actores: `crawler-google-places` y, encadenado desde su
    propio webhook, `website-content-crawler`. Cada uno dispara su webhook y reporta su gasto.
    Con un `update` a secas el costo del trabajo terminaría siendo el del último actor.

    Y por eso mismo esto no se podía hacer desde Comando Central: `apify_actor_run_id` guarda
    sólo el run del PRIMER actor —`update_job_run_id` se llama al lanzarlo— y el del segundo no
    se guarda en ninguna parte. Preguntándole a Apify por el run conocido, el costo salía más
    barato que el real y nada fallaba.

    `usd` puede ser `None`: el webhook llegó sin el campo. Se sella `costo_consultado_el` igual,
    para que "se preguntó y no había dato" no se confunda con "nunca se preguntó" — que es la
    distinción por la que esa columna existe.
    ═══════════════════════════════════════════════════════════════════════════
    """
    if usd is not None and usd < 0:
        # Un cargo negativo no es un estado posible de una factura. Es un dato que no
        # entendemos, y sumarlo restaría gasto real.
        print(f"[Costo] Apify reportó {usd} para el trabajo {job_id}: se ignora por negativo.")
        usd = None

    try:
        lectura = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}?id=eq.{job_id}&select=costo_usd",
            headers=get_supabase_headers(),
            timeout=15,
        )

        # ── SI LA LECTURA FALLA NO SE ESCRIBE ────────────────────────────────
        #
        # Es el mismo cuidado que `get_or_create_monedero`, y acá el daño es el mismo tipo de
        # silencioso: sin esta guarda, un parpadeo de red haría creer que el acumulado es cero
        # y el segundo actor de la cadena PISARÍA el costo del primero con su propio gasto. El
        # número quedaría más bajo que el real, con fecha de medición y todo — o sea, mintiendo
        # con cara de medido.
        if not lectura.ok:
            print(f"[Costo] No se pudo leer el costo actual del trabajo {job_id}: no se escribe nada.")
            return
        filas = lectura.json()
        if not filas:
            print(f"[Costo] El trabajo {job_id} no existe: no hay dónde sumar.")
            return

        actual = filas[0].get("costo_usd")
        # `actual` puede venir como texto: PostgREST serializa `numeric` como cadena para no
        # perder precisión en JSON. `float(actual or 0)` cubre las tres formas —número, cadena
        # y nulo— y `or 0` es seguro porque un costo de 0 y la ausencia dan lo mismo al sumar.
        nuevo = actual if usd is None else float(actual or 0) + float(usd)

        requests.patch(
            f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}?id=eq.{job_id}",
            headers=get_supabase_headers(content_type=True),
            json={
                "costo_usd": nuevo,
                "costo_consultado_el": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
            timeout=15,
        )
        print(f"[Costo] Trabajo {job_id}: +{usd} USD (acumulado {nuevo}).")
    except Exception as e:
        # Nunca lanza: un webhook que revienta hace que Apify reintente, y el reintento volvería
        # a procesar los leads. Perder un dato de contabilidad es mucho más barato que duplicar
        # leads o perderlos.
        print(f"[Costo] Excepción al registrar el costo del trabajo {job_id}: {e}")


def increment_user_leads_count(org_id: str, leads_count: int) -> bool:
    """
    Suma al histórico y descuenta del saldo: primero los gratuitos, después los pagados.

    Ese orden es de PRODUCTO y no de implementación: al revés, los 100 leads de regalo
    quedarían eternamente sin usar y la organización pagaría desde el primer lead.
    """
    try:
        headers = get_supabase_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABLA_MONEDERO}?org_id=eq.{org_id}"
            "&select=numero_leads_scrapeados,leads_base_gratuitos,leads_adicionales_pagados,sin_limite",
            headers=headers,
        )
        filas = response.json() if response.ok else []
        if not filas:
            print(f"No hay monedero para la organización {org_id}: no se descuenta nada.")
            return False
        user_data = filas[0]

        current_leads_scrapeados = user_data.get("numero_leads_scrapeados", 0) or 0

        # ── SIN TOPE: se cuenta, pero no se cobra ────────────────────────────
        #
        # Es ARIA, la dueña del software. El histórico SÍ sube y eso es deliberado: Apify nos
        # cobra igual, y `numero_leads_scrapeados` es la única forma de ver ese gasto. Lo que
        # no se toca es el saldo. Ver `migraciones/008_aria_scraper_sin_limite.sql`.
        if user_data.get("sin_limite"):
            r = requests.patch(
                f"{SUPABASE_URL}/rest/v1/{TABLA_MONEDERO}?org_id=eq.{org_id}",
                headers=get_supabase_headers(content_type=True),
                json={
                    "numero_leads_scrapeados": current_leads_scrapeados + leads_count,
                    "actualizado_el": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                },
            )
            print(f"Organización {org_id} sin tope: +{leads_count} al histórico, sin descontar.")
            return r.status_code in [200, 204]

        current_leads_gratuitos = user_data.get("leads_base_gratuitos", 0) or 0
        current_leads_pagados = user_data.get("leads_adicionales_pagados", 0) or 0

        new_leads_scrapeados = current_leads_scrapeados + leads_count

        leads_to_discount = leads_count
        new_leads_gratuitos = current_leads_gratuitos
        new_leads_pagados = current_leads_pagados

        if new_leads_gratuitos > 0:
            if new_leads_gratuitos >= leads_to_discount:
                new_leads_gratuitos -= leads_to_discount
                leads_to_discount = 0
            else:
                leads_to_discount -= new_leads_gratuitos
                new_leads_gratuitos = 0

        if leads_to_discount > 0:
            new_leads_pagados = max(0, new_leads_pagados - leads_to_discount)

        update_data = {
            "numero_leads_scrapeados": new_leads_scrapeados,
            "leads_base_gratuitos": new_leads_gratuitos,
            "leads_adicionales_pagados": new_leads_pagados,
            "actualizado_el": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        update_response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/{TABLA_MONEDERO}?org_id=eq.{org_id}",
            headers=get_supabase_headers(content_type=True),
            json=update_data,
        )

        if update_response.status_code in [200, 204]:
            print(f"Leads actualizados para la organización {org_id}: scrapeados {current_leads_scrapeados} -> {new_leads_scrapeados} (+{leads_count})")
            return True
        else:
            print(f"Error al actualizar leads: {update_response.status_code}, {update_response.text}")
            return False

    except Exception as e:
        print(f"Excepción al actualizar leads de la organización {org_id}: {e}")
        return False


def save_leads_to_table(org_id: str, job_id: str, source: str, leads: List[Dict[str, Any]]):
    """Guarda los leads en aria_cc_scraper_leads, atados a la organización y al trabajo."""
    headers = get_supabase_headers(content_type=True)
    rows = []
    for lead in leads:
        row = {
            "org_id": org_id,
            "trabajo_id": job_id,
            "source": source,
            "name": lead.get("title") or lead.get("page_name") or lead.get("pageName") or lead.get("fullName") or "",
            "email": lead.get("email") or "",
            "phone": lead.get("phone") or lead.get("phoneUnformatted") or "",
            "website": lead.get("website") or lead.get("companyWebsite") or "",
            "location": lead.get("address") or lead.get("city") or "",
            "category": lead.get("categoryName") or lead.get("industry") or "",
            "raw_data": lead,
        }
        rows.append(row)

    if not rows:
        return

    # Insertar en lotes de 50
    for i in range(0, len(rows), 50):
        batch = rows[i:i + 50]
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/{TABLA_LEADS}",
            headers=headers,
            json=batch,
        )
        if response.status_code in [200, 201]:
            print(f"Guardados {len(batch)} leads en {TABLA_LEADS} (trabajo {job_id})")
        else:
            print(f"Error guardando leads: {response.status_code} - {response.text}")


def get_or_create_monedero(org_id: str) -> dict:
    """
    El monedero de una organización. Si no existe, lo abre con los leads de regalo.

    ═══════════════════════════════════════════════════════════════════════════
    LA AUTO-PROVISIÓN ES LO QUE HACE QUE ESTO FUNCIONE "A NIVEL DE EMPRESA"

    Antes esta función buscaba por `cliente_id`, un identificador del hub que alguien tenía
    que haber vinculado a mano con SQL (`temporal_2_vincular.sql`). Sin ese vínculo el
    alumno veía "sin_alumno_vinculado" y no podía scrapear.

    Ahora la llave es `org_id`, que TODA organización tiene por existir. Un cliente High
    Ticket que nazca por Walter abre su monedero en su primer scraping, solo, sin que nadie
    corra nada. Ese es el cambio, y no es de prolijidad: es la diferencia entre "hay que
    acordarse de vincular a cada cliente nuevo" y "funciona".
    ═══════════════════════════════════════════════════════════════════════════
    """
    headers = get_supabase_headers()
    ruta = f"{SUPABASE_URL}/rest/v1/{TABLA_MONEDERO}?org_id=eq.{org_id}&select=*"
    response = requests.get(ruta, headers=headers)

    # ── SI LA LECTURA FALLA, SE CORTA. NO SE SIGUE A CREAR ────────────────────
    #
    # Esta guarda no es defensiva por costumbre: sin ella, un parpadeo de red convierte "no
    # pude leer el monedero" en "esta organización no tiene monedero", y el camino de abajo lo
    # CREA — pisando el saldo y el histórico reales con los valores de una cuenta nueva.
    # Un 502 que se reintenta es infinitamente mejor que un saldo borrado en silencio.
    if not response.ok:
        raise HTTPException(status_code=502, detail="No se pudo leer el saldo de leads.")
    if response.json():
        return response.json()[0]

    # Primer uso de esta organización. No se escribe `leads_disponibles_en_total`: es columna
    # generada en el destino (base_gratuitos + adicionales_pagados).
    #
    # `ignore-duplicates` y NO `merge-duplicates`: si dos peticiones de la misma organización
    # llegan juntas —el panel pide el saldo mientras el alumno ya apretó scrapear— las dos ven
    # el monedero vacío y las dos insertan. Con `merge` la segunda PISA a la primera y devuelve
    # el saldo a 100. Con `ignore` no entra, no devuelve fila, y se relee abajo.
    nuevo = {
        "org_id": org_id,
        "numero_leads_scrapeados": 0,
        "leads_base_gratuitos": LEADS_GRATIS_NUEVO_CLIENTE,
        "leads_adicionales_pagados": 0,
    }
    create_resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/{TABLA_MONEDERO}?on_conflict=org_id",
        headers={
            **get_supabase_headers(content_type=True),
            "Prefer": "resolution=ignore-duplicates,return=representation",
        },
        json=nuevo,
    )

    if create_resp.status_code in [200, 201] and create_resp.json():
        print(f"[Provisión] Organización {org_id} abierta con {LEADS_GRATIS_NUEVO_CLIENTE} leads gratis.")
        return create_resp.json()[0]

    # Sin fila devuelta hay dos casos, y se distinguen releyendo: o ganó la carrera otra
    # petición (existe, y es la buena), o el insert falló de verdad.
    relectura = requests.get(ruta, headers=headers)
    if relectura.ok and relectura.json():
        return relectura.json()[0]

    # El fallo más probable acá es la foránea: `org_id` tiene que nombrar una fila de
    # `identidad.organizaciones`. Si el hub mandó un identificador que no existe, PostgREST
    # responde 409 — y eso NO es "no se pudo provisionar" a secas, es una organización que no
    # existe. Se registra el detalle porque el mensaje al usuario no lo puede decir.
    print(f"[Provisión] Falló para {org_id}: {create_resp.status_code} {create_resp.text}")
    raise HTTPException(status_code=500, detail="No se pudo provisionar la cuenta de scraping.")


def validate_user_and_leads(org_id: str) -> dict:
    """
    Que la organización tenga monedero (lo abre si no) y saldo. Devuelve el monedero.

    Ya no hay prioridad de identidades: `org_id` es la única. Los caminos por `userId` y por
    `correo_electronico` NO se quitaron por prolijidad — la tabla nueva no tiene esas
    columnas, así que una consulta por email responde 400 de PostgREST. Es la Fase 3 de
    `migracion_cliente_id.sql`, que dejó de ser opcional.
    """
    if not org_id:
        raise HTTPException(status_code=400, detail="Falta org_id.")

    monedero = get_or_create_monedero(org_id)

    # La casa no paga leads. Se devuelve el monedero igual, para que quien llama pueda mirar
    # `sin_limite` y saltarse también SUS validaciones de tope.
    if monedero.get("sin_limite"):
        return monedero

    leads_disponibles = monedero.get("leads_disponibles_en_total", 0) or 0
    if leads_disponibles <= 0:
        raise HTTPException(status_code=403, detail="No tienes leads disponibles. Por favor, adquiere más leads para continuar.")

    return monedero


# =============================================
# 4. ENDPOINTS
# =============================================

# --- Health Check ---
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "ARIA Suite Backend API",
        "version": "2.0.0",
        "endpoints": {
            "onboarding_chat": "POST /chat",
            "google_places": "POST /start-scraping",
            "facebook_ads": "POST /start-facebook-ads-scraping",
            "facebook_pages": "POST /start-facebook-pages-scraping",
            "linkedin_apollo": "POST /start-linkedin-scraping",
            "ad_spy": "POST /start-ad-spy",
            "send_email": "POST /send-email",
            "send_email_highlevel": "POST /send-email-highlevel",
            "send_whatsapp_highlevel": "POST /send-whatsapp-highlevel",
            "highlevel_mcp": "POST /highlevel-mcp",
            "user_leads": "GET /user-leads?org_id=  (o cliente_id=, legacy ARIA-brain)",
            "mis_leads": "GET /mis-leads?org_id=  (o cliente_id=, legacy ARIA-brain)",
            "job_status": "GET /job/{job_id}?org_id=",
            "cancel_job": "POST /cancel-job/{job_id}?org_id=",
        },
    }


# --- User Leads (para sidebar) ---
@app.get("/user-leads")
async def get_user_leads(org_id: str = None, cliente_id: str = None):
    # Se auto-provisiona al consultar el saldo, así el monedero existe desde que alguien
    # abre el panel de Prospección — antes de gastar nada.
    monedero = get_or_create_monedero(resolver_org(org_id, cliente_id))
    return {
        "numero_leads_scrapeados": monedero.get("numero_leads_scrapeados", 0),
        "leads_disponibles_en_total": monedero.get("leads_disponibles_en_total", 0),
        # Para que la pantalla pueda decir "sin límite" en vez de un número. Sin este campo
        # ARIA vería "0 leads disponibles", que es cierto y es exactamente lo contrario de lo
        # que pasa.
        "sin_limite": bool(monedero.get("sin_limite")),
    }


# --- Mis Leads (tabla aria_cc_scraper_leads) ---
#
# Antes esto hacía DOS consultas: una a `usuarios_scraper` para traducir la identidad al `id`
# interno del monedero, y otra a los leads. Con `org_id` directamente en la tabla de leads la
# primera desaparece — es el nivel de indirección que se fue con la migración.
@app.get("/mis-leads")
async def get_mis_leads(org_id: str = None, cliente_id: str = None, limite: int = 1000):
    org_id = resolver_org(org_id, cliente_id)

    leads_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/{TABLA_LEADS}?org_id=eq.{org_id}"
        "&select=id,source,name,email,phone,website,location,category,raw_data,created_at"
        f"&order=created_at.desc&limit={min(limite, 5000)}",
        headers=get_supabase_headers(),
    )
    return leads_response.json() if leads_response.ok else []


# --- Onboarding Chat (Agente IA) ---
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.api_key:
        raise HTTPException(status_code=400, detail="Debes proporcionar tu API Key de OpenAI para usar el onboarding.")
    historial = [{"role": m.role, "content": m.content} for m in req.history]
    resultado = chat_con_agente(req.message, historial, model=req.model, api_key=req.api_key)
    return ChatResponse(
        response=resultado["response"],
        extracted_data=resultado["extracted_data"],
    )


# --- Google Places Scraping ---
@app.post("/start-scraping")
async def start_scraping_job(request: ScrapingRequest):
    # Validar que la localización tenga al menos 3 partes separadas por coma
    # (ej: "Cayma, Arequipa, Perú" = distrito/zona, ciudad/provincia, país)
    location_parts = [p.strip() for p in request.location.split(",") if p.strip()]
    if len(location_parts) < 3:
        raise HTTPException(
            status_code=400,
            detail="La localización debe tener al menos 3 partes separadas por coma. Ej: 'Cayma, Arequipa, Perú' (distrito, ciudad, país).",
        )

    org_id = resolver_org(request.org_id, request.cliente_id)
    usuario = validate_user_and_leads(org_id)
    sin_limite = bool(usuario.get("sin_limite"))
    leads_disponibles = usuario.get("leads_disponibles_en_total", 0) or 0

    # El pedido debe estar entre el mínimo del actor (~72 con emails) y el saldo.
    #
    # El mínimo del actor se valida SIEMPRE, con tope o sin tope: no es una regla de cobro
    # nuestra, es que por debajo de ~72 leads Apify cobra lo mismo por menos. Saltárselo para
    # ARIA sería tirar plata de ARIA.
    min_leads = google_maps_scraper.min_leads_for_charge(request.getEmails)
    if not sin_limite and leads_disponibles < min_leads:
        raise HTTPException(
            status_code=403,
            detail=f"Necesitas al menos {min_leads} leads disponibles para scrapear. Recarga para continuar.",
        )
    if request.maxLeads < min_leads:
        raise HTTPException(status_code=400, detail=f"El mínimo a scrapear es {min_leads} leads.")
    if not sin_limite and request.maxLeads > leads_disponibles:
        raise HTTPException(status_code=400, detail=f"Solo tienes {leads_disponibles} leads disponibles.")

    job_id = create_scraping_job(org_id, request)

    try:
        run_id = google_maps_scraper.start_google_maps_scrape(
            business_type=request.businessType,
            location=request.location,
            get_emails=request.getEmails,
            webhook_base_url=WEBHOOK_BASE_URL,
            job_id=job_id,
            max_places=request.maxLeads,
        )
        update_job_run_id(job_id, run_id)
    except Exception as e:
        update_job_results(job_id, "FAILED", error_message=str(e))
        raise HTTPException(status_code=502, detail=f"Error al iniciar el actor de Apify: {e}")

    return {"status": "success", "message": "Tu búsqueda ha comenzado.", "jobId": job_id}


# --- Job Status ---
@app.get("/job/{job_id}")
async def get_job_status_and_results(job_id: str, org_id: str = None, cliente_id: str = None):
    org_id = resolver_org(org_id, cliente_id)
    headers = get_supabase_headers()
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}?org_id=eq.{org_id}&id=eq.{job_id}"
        "&select=status,results_data",
        headers=headers,
    )
    if not response.json():
        raise HTTPException(status_code=404, detail="Trabajo no encontrado.")
    job_data = response.json()[0]
    final_response = {"status": job_data.get("status")}
    if job_data.get("status") == "COMPLETED" and job_data.get("results_data"):
        final_response["results"] = job_data["results_data"]
    return final_response


# --- Cancel Job ---
@app.post("/cancel-job/{job_id}")
async def cancel_scraping_job(job_id: str, org_id: str = None, cliente_id: str = None):
    org_id = resolver_org(org_id, cliente_id)
    try:
        headers = get_supabase_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}?org_id=eq.{org_id}&id=eq.{job_id}"
            "&select=apify_actor_run_id,status",
            headers=headers,
        )
        if not response.json():
            raise HTTPException(status_code=404, detail="Trabajo no encontrado")

        job_data = response.json()[0]
        if job_data.get("status") not in ["PENDING", "RUNNING"]:
            raise HTTPException(status_code=400, detail=f"El trabajo no se puede cancelar. Estado actual: {job_data.get('status')}")

        apify_run_id = job_data.get("apify_actor_run_id")
        if apify_run_id:
            client = ApifyClient(apify_token)
            try:
                client.run(apify_run_id).abort()
                print(f"Actor de Apify {apify_run_id} cancelado exitosamente")
            except Exception as e:
                print(f"Error al cancelar en Apify: {e}")

        update_job_results(job_id, "CANCELLED", error_message="Trabajo cancelado por el usuario")
        return {"status": "success", "message": "El trabajo ha sido cancelado exitosamente", "jobId": job_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al cancelar el trabajo {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al cancelar el trabajo: {str(e)}")


# --- Envío de Correos ---
@app.post("/send-email")
async def send_email_endpoint(request: EmailRequest):
    if enviar_correo is None:
        raise HTTPException(status_code=501, detail="Módulo de envío de correos no disponible aún.")
    if not request.destinatarios:
        raise HTTPException(status_code=400, detail="La lista de destinatarios está vacía.")

    resultados = []
    errores = []

    for correo in request.destinatarios:
        resultado = enviar_correo(
            gmail_user=request.gmail_user,
            gmail_app_password=request.gmail_app_password,
            nombre_remitente=request.nombre_remitente,
            destinatario_nombre=correo,
            destinatario_correo=correo,
            mensaje=request.mensaje,
        )
        if resultado["success"]:
            resultados.append(correo)
        else:
            errores.append({"correo": correo, "error": resultado["message"]})

    if errores and not resultados:
        raise HTTPException(status_code=500, detail={"message": "Todos los correos fallaron.", "errores": errores})

    return {
        "enviados": len(resultados),
        "fallidos": len(errores),
        "detalle_errores": errores,
        "message": f"Se enviaron {len(resultados)} correos correctamente." + (f" {len(errores)} fallaron." if errores else ""),
    }


# --- Envío de Correos via LeadConnector (HighLevel) ---
@app.post("/send-email-highlevel")
async def send_email_highlevel_endpoint(request: EmailLCRequest):
    if enviar_correo_masivo_lc is None:
        raise HTTPException(status_code=501, detail="Módulo de envío via LeadConnector no disponible aún.")
    if not request.pit_token.strip():
        raise HTTPException(status_code=400, detail="El campo pit_token no puede estar vacío.")
    if not request.location_id.strip():
        raise HTTPException(status_code=400, detail="El campo location_id no puede estar vacío.")
    if not request.destinatarios:
        raise HTTPException(status_code=400, detail="La lista de destinatarios está vacía.")
    if not request.mensaje.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    destinatarios = [d.model_dump() for d in request.destinatarios]

    resultado = enviar_correo_masivo_lc(
        pit_token=request.pit_token,
        location_id=request.location_id,
        asunto=request.asunto,
        mensaje_html=request.mensaje,
        destinatarios=destinatarios,
        email_from=request.email_from or "",
    )

    if resultado["enviados"] == 0 and resultado["fallidos"] > 0:
        raise HTTPException(status_code=500, detail=resultado)

    return resultado


# --- Envío de WhatsApp via LeadConnector (HighLevel) ---
@app.post("/send-whatsapp-highlevel")
async def send_whatsapp_highlevel_endpoint(request: WhatsAppLCRequest):
    if enviar_whatsapp_masivo_lc is None:
        raise HTTPException(status_code=501, detail="Módulo de envío via LeadConnector no disponible aún.")
    if not request.pit_token.strip():
        raise HTTPException(status_code=400, detail="El campo pit_token no puede estar vacío.")
    if not request.location_id.strip():
        raise HTTPException(status_code=400, detail="El campo location_id no puede estar vacío.")
    if not request.destinatarios:
        raise HTTPException(status_code=400, detail="La lista de destinatarios está vacía.")
    if not request.mensaje.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    destinatarios = [d.model_dump() for d in request.destinatarios]

    resultado = enviar_whatsapp_masivo_lc(
        pit_token=request.pit_token,
        location_id=request.location_id,
        mensaje=request.mensaje,
        destinatarios=destinatarios,
    )

    if resultado["enviados"] == 0 and resultado["fallidos"] > 0:
        raise HTTPException(status_code=500, detail=resultado)

    return resultado


# --- Agente MCP de HighLevel ---
@app.post("/highlevel-mcp")
async def highlevel_mcp_endpoint(request: HighLevelMCPRequest):
    if ejecutar_orden_highlevel is None:
        raise HTTPException(status_code=501, detail="Módulo HighLevel MCP no disponible aún.")
    if not request.pit_token.strip():
        raise HTTPException(status_code=400, detail="El campo pit_token no puede estar vacío.")
    if not request.location_id.strip():
        raise HTTPException(status_code=400, detail="El campo location_id no puede estar vacío.")
    if not request.orden.strip():
        raise HTTPException(status_code=400, detail="El campo orden no puede estar vacío.")

    resultado = await ejecutar_orden_highlevel(
        pit_token=request.pit_token,
        location_id=request.location_id,
        orden=request.orden,
    )

    if not resultado["success"]:
        raise HTTPException(status_code=500, detail=resultado["respuesta"])

    return resultado


# --- Facebook Ads Scraping ---
@app.post("/start-facebook-ads-scraping")
async def start_facebook_ads_scraping(request: FacebookAdsScrapingRequest):
    if facebook_ads_scraper is None:
        raise HTTPException(status_code=501, detail="Módulo facebook_ads_scraper no disponible aún.")
    try:
        scrape_url = request.get_url()
        if not scrape_url:
            raise HTTPException(status_code=400, detail="Falta la URL de Facebook Ads.")

        org_id = resolver_org(request.org_id, request.cliente_id)
        validate_user_and_leads(org_id)

        job_headers = get_supabase_headers(content_type=True, prefer_return=True)
        job_data = {
            "org_id": org_id,
            "fuente": "facebook-ads",
            "status": "PENDING",
            "business_type": "Facebook Ads",
            "location": scrape_url,
            "get_emails": False,
            "get_business_model": False,
            "created_at": request.timestamp,
        }

        job_response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}", headers=job_headers, json=job_data)
        if job_response.status_code != 201:
            raise HTTPException(status_code=500, detail="No se pudo registrar el trabajo.")

        job_id = job_response.json()[0]["id"]

        run_id = facebook_ads_scraper.start_facebook_ads_scrape(
            scrape_url=scrape_url,
            webhook_base_url=WEBHOOK_BASE_URL,
            job_id=job_id,
        )
        update_job_run_id(job_id, run_id)

        return {"status": "success", "message": "El scraping de Facebook Ads ha comenzado.", "jobId": job_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al iniciar Facebook Ads scraping: {e}")
        raise HTTPException(status_code=500, detail=f"Error al iniciar el scraping: {str(e)}")


# --- Facebook Pages Scraping ---
@app.post("/start-facebook-pages-scraping")
@app.post("/start-facebook-page-scraping")
async def start_facebook_pages_scraping(request: FacebookPagesScrapingRequest):
    if facebook_pages_scraper is None:
        raise HTTPException(status_code=501, detail="Módulo facebook_pages_scraper no disponible aún.")
    try:
        original_pages_data = request.get_original_pages_data()
        if not original_pages_data:
            raise HTTPException(status_code=400, detail="Falta el array de páginas de Facebook.")

        # Filtrar duplicados
        seen_urls = set()
        unique_pages_data = []
        for page in original_pages_data:
            page_uri = page.get("page_profile_uri")
            if page_uri and page_uri not in seen_urls:
                seen_urls.add(page_uri)
                unique_pages_data.append(page)

        original_pages_data = unique_pages_data
        page_urls = [page.get("page_profile_uri") for page in unique_pages_data]

        org_id = resolver_org(request.org_id, request.cliente_id)
        validate_user_and_leads(org_id)

        job_headers = get_supabase_headers(content_type=True, prefer_return=True)
        job_data = {
            "org_id": org_id,
            "fuente": "facebook-pages",
            "status": "PENDING",
            "business_type": "Facebook Pages (Bulk)",
            "location": f"{len(page_urls)} páginas",
            "get_emails": False,
            "get_business_model": False,
            "created_at": request.timestamp,
            "results_data": {"original_pages": original_pages_data},
        }

        job_response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}", headers=job_headers, json=job_data)
        if job_response.status_code != 201:
            raise HTTPException(status_code=500, detail="No se pudo registrar el trabajo.")

        job_id = job_response.json()[0]["id"]

        run_id = facebook_pages_scraper.start_facebook_page_scrape(
            page_urls=page_urls,
            webhook_base_url=WEBHOOK_BASE_URL,
            job_id=job_id,
        )
        update_job_run_id(job_id, run_id)

        return {
            "status": "success",
            "message": "El scraping de la página de Facebook ha comenzado.",
            "jobId": job_id,
            "job_id": job_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al iniciar Facebook Pages scraping: {e}")
        raise HTTPException(status_code=500, detail=f"Error al iniciar el scraping: {str(e)}")


# --- LinkedIn (Apollo) Scraping ---
@app.post("/start-linkedin-scraping")
async def start_linkedin_scraping(request: LinkedInScrapingRequest):
    if linkedin_apollo_scraper is None:
        raise HTTPException(status_code=501, detail="Módulo linkedin_apollo_scraper no disponible aún.")

    if not request.job_title.strip():
        raise HTTPException(status_code=400, detail="job_title es obligatorio.")
    if not request.country.strip():
        raise HTTPException(status_code=400, detail="country es obligatorio.")
    if request.number_of_leads < 100 or request.number_of_leads > 30000:
        raise HTTPException(status_code=400, detail="number_of_leads debe estar entre 100 y 30000.")

    org_id = resolver_org(request.org_id, request.cliente_id)
    validate_user_and_leads(org_id)

    headers = get_supabase_headers(content_type=True, prefer_return=True)
    location_str = f"{request.state}, {request.country}".strip(", ") if request.state else request.country
    job_data = {
        "org_id": org_id,
        "fuente": "linkedin",
        "status": "PENDING",
        "business_type": f"LinkedIn: {request.job_title}",
        "location": location_str,
        "get_emails": True,
        "get_business_model": False,
    }
    job_response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}", headers=headers, json=job_data)
    if job_response.status_code not in [200, 201]:
        raise HTTPException(status_code=500, detail="No se pudo registrar el trabajo de LinkedIn.")
    job_id = job_response.json()[0]["id"]

    try:
        run_id = linkedin_apollo_scraper.start_linkedin_scrape(
            job_title=request.job_title,
            country=request.country,
            state=request.state or "",
            number_of_leads=request.number_of_leads,
            webhook_base_url=WEBHOOK_BASE_URL,
            job_id=job_id,
        )
        update_job_run_id(job_id, run_id)
    except Exception as e:
        update_job_results(job_id, "FAILED", error_message=str(e))
        raise HTTPException(status_code=502, detail=f"Error al iniciar Apify (LinkedIn): {e}")

    return {
        "status": "success",
        "message": f"Scraping de LinkedIn iniciado: {request.job_title} en {location_str}.",
        "jobId": job_id,
    }


# --- Ad Spy (Espía de Anuncios — Meta Ad Library) ---
@app.post("/start-ad-spy")
async def start_ad_spy(request: AdSpyRequest):
    """Espía la Meta Ad Library por nicho/marca/página. NO consume saldo de leads
    (es investigación de competencia, no generación de leads)."""
    if ad_spy_scraper is None:
        raise HTTPException(status_code=501, detail="Módulo ad_spy_scraper no disponible aún.")
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Escribe un nicho, marca o página a espiar.")

    # `org_id` es obligatorio, pero NO se valida saldo: Ad Spy es investigación y no genera
    # leads. Se abre el monedero igual —así la organización queda provisionada— y nada más.
    org_id = resolver_org(request.org_id, request.cliente_id)
    get_or_create_monedero(org_id)

    # Crea un trabajo en la misma tabla, marcado como Ad Spy. Sin validar saldo.
    headers = get_supabase_headers(content_type=True, prefer_return=True)
    job_data = {
        "org_id": org_id,
        "fuente": "ad-spy",
        "status": "PENDING",
        "business_type": f"AdSpy: {request.query.strip()}",
        "location": (request.country or "ALL"),
        "get_emails": False,
        "get_business_model": False,
    }
    job_response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}", headers=headers, json=job_data)
    if job_response.status_code not in [200, 201]:
        raise HTTPException(status_code=500, detail="No se pudo registrar el trabajo de Ad Spy.")
    job_id = job_response.json()[0]["id"]

    try:
        run_id = ad_spy_scraper.start_ad_spy_scrape(
            query=request.query.strip(),
            country=request.country or "ALL",
            webhook_base_url=WEBHOOK_BASE_URL,
            job_id=job_id,
            count=request.count or 60,
        )
        update_job_run_id(job_id, run_id)
    except Exception as e:
        update_job_results(job_id, "FAILED", error_message=str(e))
        raise HTTPException(status_code=502, detail=f"Error al iniciar el actor de Apify: {e}")

    return {"status": "success", "message": "Búsqueda de anuncios iniciada.", "jobId": job_id}


# =============================================
# 5. WEBHOOKS Y TAREAS EN SEGUNDO PLANO
# =============================================

# --- Google Places Webhook ---
@app.post("/webhook-google-places-succeeded")
async def handle_google_places_webhook(payload: GooglePlacesWebhookPayload, background_tasks: BackgroundTasks):
    # El costo PRIMERO, antes de tocar los leads. Si el procesamiento de abajo falla, el gasto
    # de Apify ya ocurrió igual y tiene que quedar registrado: un costo perdido es un margen
    # inflado, que es peor que no tener el dato.
    #
    # Acá y no dentro de `update_job_results`, que es donde tienta ponerlo: esa función también
    # se llama desde caminos donde el actor NI ARRANCÓ —el `FAILED` del arranque— y ahí no hay
    # ningún run que cobrar.
    add_job_cost(payload.job_id, payload.resource.usageTotalUsd)

    job_id = payload.job_id
    dataset_id = payload.resource.defaultDatasetId
    print(f"Webhook 1/2: Google Places terminó para Job ID: {job_id}.")
    background_tasks.add_task(process_google_places_results, job_id, dataset_id)
    return {"status": "webhook 1 received"}


async def process_google_places_results(job_id: str, google_places_dataset_id: str):
    try:
        headers = get_supabase_headers()
        job_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}?id=eq.{job_id}&select=*",
            headers=headers,
        )
        if not job_response.json():
            return
        job_details = job_response.json()[0]

        # El webhook también llega cuando el run se aborta (por tope de presupuesto
        # o por cancelación del usuario). Si el usuario canceló, no tocar el job.
        if job_details.get("status") == "CANCELLED":
            print(f"Job {job_id} fue cancelado por el usuario; se ignora el webhook.")
            return

        # Tope de leads pedido por el usuario (guardado al crear el job). El actor
        # puede traer 1-2 de más por el límite de presupuesto; recortamos para que
        # reciba y se le descuente exactamente lo solicitado.
        max_leads = (job_details.get("results_data") or {}).get("max_leads")

        dataset_items = google_maps_scraper.get_dataset_items(google_places_dataset_id)

        if not job_details.get("get_business_model"):
            final_leads = google_maps_scraper.build_final_leads(dataset_items, job_details.get("get_emails"))
            if max_leads:
                final_leads = final_leads[:max_leads]
            final_json_output = {"data": final_leads, "results_count": len(final_leads)}
            update_job_results(job_id, "COMPLETED", results=final_json_output)

            org_id = job_details.get("org_id")
            if org_id:
                increment_user_leads_count(org_id, len(final_leads))
                save_leads_to_table(org_id, job_id, "maps", final_leads)

            print(f"Trabajo {job_id} completado (solo Google Places).")
            return

        print(f"Trabajo {job_id} requiere análisis de sitios web. Lanzando Website Content Crawler...")
        urls_to_crawl = [
            {"url": item["website"]}
            for item in dataset_items
            if item.get("website") and item["website"].startswith(("http://", "https://"))
        ]

        if not urls_to_crawl:
            final_leads = google_maps_scraper.build_final_leads(dataset_items, job_details.get("get_emails"))
            if max_leads:
                final_leads = final_leads[:max_leads]
            final_json_output = {"data": final_leads, "results_count": len(final_leads)}
            update_job_results(job_id, "COMPLETED", results=final_json_output)
            org_id = job_details.get("org_id")
            if org_id:
                increment_user_leads_count(org_id, len(final_leads))
                save_leads_to_table(org_id, job_id, "maps", final_leads)
            return

        google_maps_scraper.start_website_crawler(
            urls_to_crawl=urls_to_crawl,
            webhook_base_url=WEBHOOK_BASE_URL,
            job_id=job_id,
            google_places_dataset_id=google_places_dataset_id,
        )
        print(f"Website Crawler lanzado para {job_id}.")

    except Exception as e:
        print(f"Error en process_google_places_results para job {job_id}: {e}")
        traceback.print_exc()
        update_job_results(job_id, "FAILED", error_message=str(e))


# --- Website Crawler Webhook ---
@app.post("/webhook-website-crawler-succeeded")
async def handle_website_crawler_webhook(payload: WebsiteCrawlerWebhookPayload, background_tasks: BackgroundTasks):
    # El costo PRIMERO, antes de tocar los leads. Si el procesamiento de abajo falla, el gasto
    # de Apify ya ocurrió igual y tiene que quedar registrado: un costo perdido es un margen
    # inflado, que es peor que no tener el dato.
    #
    # Acá y no dentro de `update_job_results`, que es donde tienta ponerlo: esa función también
    # se llama desde caminos donde el actor NI ARRANCÓ —el `FAILED` del arranque— y ahí no hay
    # ningún run que cobrar.
    add_job_cost(payload.job_id, payload.resource.usageTotalUsd)

    print(f"Webhook 2/2: Website Crawler terminó para Job ID: {payload.job_id}.")
    background_tasks.add_task(process_final_results, payload)
    return {"status": "webhook 2 received"}


async def process_final_results(payload: WebsiteCrawlerWebhookPayload):
    job_id = payload.job_id
    google_places_dataset_id = payload.google_places_dataset_id
    website_content_dataset_id = payload.resource.defaultDatasetId

    try:
        headers = get_supabase_headers()
        job_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}?id=eq.{job_id}&select=*",
            headers=headers,
        )
        if not job_response.json():
            return
        job_details = job_response.json()[0]

        google_places_items = google_maps_scraper.get_dataset_items(google_places_dataset_id)
        # website_content_items disponible para análisis futuro
        google_maps_scraper.get_dataset_items(website_content_dataset_id)

        final_leads = google_maps_scraper.build_final_leads(google_places_items, job_details.get("get_emails"))
        final_json_output = {"data": final_leads, "results_count": len(final_leads)}

        update_job_results(job_id, "COMPLETED", results=final_json_output)

        org_id = job_details.get("org_id")
        if org_id:
            increment_user_leads_count(org_id, len(final_leads))
            save_leads_to_table(org_id, job_id, "maps", final_leads)

        print(f"Trabajo {job_id} completado y resultados guardados exitosamente.")

    except Exception as e:
        print(f"Error en el procesamiento final para job {job_id}: {e}")
        update_job_results(job_id, "FAILED", error_message=str(e))


# --- Facebook Ads Webhook ---
@app.post("/webhook-facebook-ads-succeeded")
async def handle_facebook_ads_webhook(payload: GooglePlacesWebhookPayload, background_tasks: BackgroundTasks):
    # El costo PRIMERO, antes de tocar los leads. Si el procesamiento de abajo falla, el gasto
    # de Apify ya ocurrió igual y tiene que quedar registrado: un costo perdido es un margen
    # inflado, que es peor que no tener el dato.
    #
    # Acá y no dentro de `update_job_results`, que es donde tienta ponerlo: esa función también
    # se llama desde caminos donde el actor NI ARRANCÓ —el `FAILED` del arranque— y ahí no hay
    # ningún run que cobrar.
    add_job_cost(payload.job_id, payload.resource.usageTotalUsd)

    job_id = payload.job_id
    dataset_id = payload.resource.defaultDatasetId
    print(f"Webhook: Facebook Ads terminó para Job ID: {job_id}")
    background_tasks.add_task(process_facebook_ads_results, job_id, dataset_id)
    return {"status": "webhook received"}


async def process_facebook_ads_results(job_id: str, dataset_id: str):
    try:
        headers = get_supabase_headers()
        job_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}?id=eq.{job_id}&select=org_id",
            headers=headers,
        )
        org_id = job_response.json()[0].get("org_id") if job_response.json() else None

        client = ApifyClient(apify_token)
        dataset_items = client.dataset(dataset_id).list_items().items

        if dataset_items and "error" in dataset_items[0]:
            error_message = dataset_items[0].get("error", "Error desconocido del actor")
            update_job_results(job_id, "FAILED", error_message=str(error_message))
            return

        normalized_data = facebook_ads_scraper.build_facebook_ads_table_items(dataset_items)

        final_json_output = {"data": normalized_data, "results_count": len(normalized_data)}
        update_job_results(job_id, "COMPLETED", results=final_json_output)

        if org_id:
            save_leads_to_table(org_id, job_id, "facebook", normalized_data)

        print(f"Facebook Ads scraping {job_id} completado. {len(normalized_data)} anuncios extraídos.")

    except Exception as e:
        print(f"Error procesando resultados de Facebook Ads para job {job_id}: {e}")
        update_job_results(job_id, "FAILED", error_message=str(e))


# --- Facebook Pages Webhook ---
@app.post("/webhook-facebook-pages-succeeded")
async def handle_facebook_pages_webhook(payload: GooglePlacesWebhookPayload, background_tasks: BackgroundTasks):
    # El costo PRIMERO, antes de tocar los leads. Si el procesamiento de abajo falla, el gasto
    # de Apify ya ocurrió igual y tiene que quedar registrado: un costo perdido es un margen
    # inflado, que es peor que no tener el dato.
    #
    # Acá y no dentro de `update_job_results`, que es donde tienta ponerlo: esa función también
    # se llama desde caminos donde el actor NI ARRANCÓ —el `FAILED` del arranque— y ahí no hay
    # ningún run que cobrar.
    add_job_cost(payload.job_id, payload.resource.usageTotalUsd)

    job_id = payload.job_id
    dataset_id = payload.resource.defaultDatasetId
    print(f"Webhook: Facebook Pages terminó para Job ID: {job_id}")
    background_tasks.add_task(process_facebook_pages_results, job_id, dataset_id)
    return {"status": "webhook received"}


async def process_facebook_pages_results(job_id: str, dataset_id: str):
    try:
        headers = get_supabase_headers()
        job_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}?id=eq.{job_id}&select=org_id,results_data",
            headers=headers,
        )

        if not job_response.json():
            raise Exception("No se pudo recuperar el job de la base de datos")

        job_data = job_response.json()[0]
        org_id = job_data.get("org_id")
        original_pages = job_data.get("results_data", {}).get("original_pages", [])

        client = ApifyClient(apify_token)
        dataset_items = client.dataset(dataset_id).list_items().items

        scraped_data = facebook_pages_scraper.build_facebook_pages_table_items(dataset_items)

        scraped_map = {item.get("pageUrl") or item.get("facebookUrl"): item for item in scraped_data}

        matched_results = []
        for original_page in original_pages:
            page_uri = original_page.get("page_profile_uri")
            scraped_item = scraped_map.get(page_uri, {})
            combined_item = {**original_page, **scraped_item}
            matched_results.append(combined_item)

        final_json_output = {"data": matched_results, "results_count": len(matched_results)}
        update_job_results(job_id, "COMPLETED", results=final_json_output)

        if org_id:
            increment_user_leads_count(org_id, len(matched_results))
            save_leads_to_table(org_id, job_id, "facebook", matched_results)

        print(f"Facebook Pages scraping {job_id} completado. {len(matched_results)} páginas extraídas.")

    except Exception as e:
        print(f"Error procesando resultados de Facebook Pages para job {job_id}: {e}")
        update_job_results(job_id, "FAILED", error_message=str(e))


# --- LinkedIn (Apollo) Webhook ---
@app.post("/webhook-linkedin-apollo-succeeded")
async def handle_linkedin_apollo_webhook(payload: GooglePlacesWebhookPayload, background_tasks: BackgroundTasks):
    # El costo PRIMERO, antes de tocar los leads. Si el procesamiento de abajo falla, el gasto
    # de Apify ya ocurrió igual y tiene que quedar registrado: un costo perdido es un margen
    # inflado, que es peor que no tener el dato.
    #
    # Acá y no dentro de `update_job_results`, que es donde tienta ponerlo: esa función también
    # se llama desde caminos donde el actor NI ARRANCÓ —el `FAILED` del arranque— y ahí no hay
    # ningún run que cobrar.
    add_job_cost(payload.job_id, payload.resource.usageTotalUsd)

    job_id = payload.job_id
    dataset_id = payload.resource.defaultDatasetId
    print(f"Webhook: LinkedIn (Apollo) terminó para Job ID: {job_id}")
    background_tasks.add_task(process_linkedin_apollo_results, job_id, dataset_id)
    return {"status": "webhook received"}


async def process_linkedin_apollo_results(job_id: str, dataset_id: str):
    try:
        headers = get_supabase_headers()
        job_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABLA_TRABAJOS}?id=eq.{job_id}&select=org_id",
            headers=headers,
        )
        if not job_response.json():
            raise Exception("Job no encontrado")

        org_id = job_response.json()[0].get("org_id")

        items = linkedin_apollo_scraper.get_dataset_items(dataset_id)
        final_leads = linkedin_apollo_scraper.build_final_leads(items)
        final_json_output = {"data": final_leads, "results_count": len(final_leads)}
        update_job_results(job_id, "COMPLETED", results=final_json_output)

        if org_id:
            increment_user_leads_count(org_id, len(final_leads))
            save_leads_to_table(org_id, job_id, "linkedin", final_leads)

        print(f"LinkedIn (Apollo) {job_id} completado. {len(final_leads)} leads guardados.")

    except Exception as e:
        print(f"Error procesando resultados de LinkedIn para job {job_id}: {e}")
        update_job_results(job_id, "FAILED", error_message=str(e))


# --- Ad Spy Webhook (Meta Ad Library) ---
@app.post("/webhook-ad-spy-succeeded")
async def handle_ad_spy_webhook(payload: GooglePlacesWebhookPayload, background_tasks: BackgroundTasks):
    # El costo PRIMERO, antes de tocar los leads. Si el procesamiento de abajo falla, el gasto
    # de Apify ya ocurrió igual y tiene que quedar registrado: un costo perdido es un margen
    # inflado, que es peor que no tener el dato.
    #
    # Acá y no dentro de `update_job_results`, que es donde tienta ponerlo: esa función también
    # se llama desde caminos donde el actor NI ARRANCÓ —el `FAILED` del arranque— y ahí no hay
    # ningún run que cobrar.
    add_job_cost(payload.job_id, payload.resource.usageTotalUsd)

    job_id = payload.job_id
    dataset_id = payload.resource.defaultDatasetId
    print(f"Webhook: Ad Spy terminó para Job ID: {job_id}")
    background_tasks.add_task(process_ad_spy_results, job_id, dataset_id)
    return {"status": "webhook received"}


async def process_ad_spy_results(job_id: str, dataset_id: str):
    """Procesa los anuncios espiados y los guarda en results_data del job.
    NO guarda en aria_cc_scraper_leads ni descuenta saldo (es investigación)."""
    try:
        dataset_items = ad_spy_scraper.get_dataset_items(dataset_id)
        if dataset_items and isinstance(dataset_items[0], dict) and "error" in dataset_items[0] and len(dataset_items[0]) == 1:
            update_job_results(job_id, "FAILED", error_message=str(dataset_items[0].get("error", "Error del actor")))
            return

        ads = ad_spy_scraper.build_ad_spy_items(dataset_items)
        final_json_output = {"data": ads, "results_count": len(ads)}
        update_job_results(job_id, "COMPLETED", results=final_json_output)
        print(f"Ad Spy {job_id} completado. {len(ads)} anuncios espiados.")

    except Exception as e:
        print(f"Error procesando resultados de Ad Spy para job {job_id}: {e}")
        traceback.print_exc()
        update_job_results(job_id, "FAILED", error_message=str(e))
