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
    from tools_scrapers.envio_de_correo_LC_HighLevel import enviar_correo_masivo_lc
except ImportError:
    enviar_correo_masivo_lc = None
    print("⚠️ envio_de_correo_LC_HighLevel no disponible aún")


# =============================================
# 1. MODELOS DE DATOS
# =============================================

# -- Login --
class LoginRequest(BaseModel):
    correo_electronico: str
    codigo_de_acceso: str

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
    userId: str
    correo_electronico: str

class ApifyWebhookResource(BaseModel):
    defaultDatasetId: str

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
    userId: str
    correo_electronico: str
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
    userId: str
    correo_electronico: str
    timestamp: str

    def get_page_urls(self) -> List[str]:
        return [page.page_profile_uri for page in self.pages]

    def get_original_pages_data(self) -> List[Dict[str, str]]:
        return [page.model_dump() for page in self.pages]

# -- HighLevel MCP --
class HighLevelMCPRequest(BaseModel):
    pit_token: str
    location_id: str
    orden: str

# -- Funnel Scrape (n8n → ARIA Suite) --
class FunnelScrapeRequest(BaseModel):
    niche: str
    location: str
    email: str
    name: Optional[str] = ""
    phone: Optional[str] = ""
    profession: Optional[str] = ""
    clientType: Optional[str] = ""

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


def create_scraping_job(user_id: str, request: ScrapingRequest) -> str:
    headers = get_supabase_headers(content_type=True, prefer_return=True)
    job_data = {
        "user_id": user_id,
        "status": "PENDING",
        "business_type": request.businessType,
        "location": request.location,
        "get_emails": request.getEmails,
        "get_business_model": request.getBusinessModel,
    }
    response = requests.post(f"{SUPABASE_URL}/rest/v1/scraping_jobs", headers=headers, json=job_data)
    if response.status_code == 201:
        return response.json()[0]["id"]
    else:
        raise HTTPException(status_code=500, detail="No se pudo registrar el trabajo.")


def update_job_run_id(job_id: str, run_id: str):
    headers = get_supabase_headers(content_type=True)
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/scraping_jobs?id=eq.{job_id}",
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
        f"{SUPABASE_URL}/rest/v1/scraping_jobs?id=eq.{job_id}",
        headers=headers,
        json=update_data,
    )
    if response.status_code in [200, 204]:
        return True
    else:
        print(f"Error al actualizar resultados del job {job_id}. Status: {response.status_code}, Response: {response.text}")
        return False


def increment_user_leads_count(user_id: str, leads_count: int) -> bool:
    try:
        headers = get_supabase_headers(content_type=True)

        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/usuarios_scraper?id=eq.{user_id}&select=numero_leads_scrapeados,leads_base_gratuitos,leads_adicionales_pagados",
            headers=headers,
        )

        if not response.json():
            print(f"No se encontró el usuario {user_id}")
            return False

        user_data = response.json()[0]
        current_leads_scrapeados = user_data.get("numero_leads_scrapeados", 0) or 0
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
        }

        update_response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/usuarios_scraper?id=eq.{user_id}",
            headers=headers,
            json=update_data,
        )

        if update_response.status_code in [200, 204]:
            print(f"Leads actualizados para usuario {user_id}: scrapeados {current_leads_scrapeados} -> {new_leads_scrapeados} (+{leads_count})")
            return True
        else:
            print(f"Error al actualizar leads: {update_response.status_code}, {update_response.text}")
            return False

    except Exception as e:
        print(f"Excepción al actualizar leads para usuario {user_id}: {e}")
        return False


def save_leads_to_table(user_id: str, job_id: str, source: str, leads: List[Dict[str, Any]]):
    """Guarda los leads en la tabla aria_suite_leads_per_user."""
    headers = get_supabase_headers(content_type=True)
    rows = []
    for lead in leads:
        row = {
            "user_id": user_id,
            "job_id": job_id,
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
            f"{SUPABASE_URL}/rest/v1/aria_suite_leads_per_user",
            headers=headers,
            json=batch,
        )
        if response.status_code in [200, 201]:
            print(f"Guardados {len(batch)} leads en aria_suite_leads_per_user (job {job_id})")
        else:
            print(f"Error guardando leads: {response.status_code} - {response.text}")


def validate_user_and_leads(user_id: str = None, email: str = None) -> dict:
    """Valida que el usuario exista y tenga leads disponibles. Retorna datos del usuario."""
    headers = get_supabase_headers()

    usuario = None
    if user_id:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/usuarios_scraper?id=eq.{user_id}&select=*", headers=headers)
        if response.json():
            usuario = response.json()[0]

    if not usuario and email:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/usuarios_scraper?correo_electronico=eq.{email}&select=*", headers=headers)
        if response.json():
            usuario = response.json()[0]

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    leads_disponibles = usuario.get("leads_disponibles_en_total", 0) or 0
    if leads_disponibles <= 0:
        raise HTTPException(status_code=403, detail="No tienes leads disponibles. Por favor, adquiere más leads para continuar.")

    return usuario


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
            "send_email": "POST /send-email",
            "send_email_highlevel": "POST /send-email-highlevel",
            "highlevel_mcp": "POST /highlevel-mcp",
            "funnel_scrape": "POST /funnel-scrape",
            "job_status": "GET /job/{job_id}",
            "cancel_job": "POST /cancel-job/{job_id}",
        },
    }


# --- Login ---
@app.post("/login")
async def login(request: LoginRequest):
    headers = get_supabase_headers()
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/usuarios_scraper?correo_electronico=eq.{request.correo_electronico}&select=*",
        headers=headers,
    )
    if not response.json():
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    usuario = response.json()[0]
    if usuario.get("codigo_de_acceso") != request.codigo_de_acceso:
        raise HTTPException(status_code=401, detail="Código de acceso incorrecto.")

    return {
        "success": True,
        "user": {
            "id": usuario.get("id"),
            "correo_electronico": usuario.get("correo_electronico"),
            "nombre": usuario.get("nombre"),
            "leads_disponibles_en_total": usuario.get("leads_disponibles_en_total", 0),
            "numero_leads_scrapeados": usuario.get("numero_leads_scrapeados", 0),
        },
    }


# --- User Leads (para sidebar) ---
@app.get("/user-leads")
async def get_user_leads(email: str):
    headers = get_supabase_headers()
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/usuarios_scraper?correo_electronico=eq.{email}&select=numero_leads_scrapeados,leads_disponibles_en_total",
        headers=headers,
    )
    if not response.json():
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    usuario = response.json()[0]
    return {
        "numero_leads_scrapeados": usuario.get("numero_leads_scrapeados", 0),
        "leads_disponibles_en_total": usuario.get("leads_disponibles_en_total", 0),
    }


# --- Mis Leads (tabla aria_suite_leads_per_user) ---
@app.get("/mis-leads")
async def get_mis_leads(email: str):
    headers = get_supabase_headers()

    # Obtener user_id
    user_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/usuarios_scraper?correo_electronico=eq.{email}&select=id",
        headers=headers,
    )
    if not user_response.json():
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    user_id = user_response.json()[0]["id"]

    # Obtener leads
    leads_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/aria_suite_leads_per_user?user_id=eq.{user_id}&select=id,source,name,email,phone,website,location,category,raw_data,created_at&order=created_at.desc",
        headers=headers,
    )
    return leads_response.json()


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
    usuario = validate_user_and_leads(email=request.correo_electronico)
    job_id = create_scraping_job(usuario.get("id"), request)

    try:
        run_id = google_maps_scraper.start_google_maps_scrape(
            business_type=request.businessType,
            location=request.location,
            get_emails=request.getEmails,
            webhook_base_url=WEBHOOK_BASE_URL,
            job_id=job_id,
        )
        update_job_run_id(job_id, run_id)
    except Exception as e:
        update_job_results(job_id, "FAILED", error_message=str(e))
        raise HTTPException(status_code=502, detail=f"Error al iniciar el actor de Apify: {e}")

    return {"status": "success", "message": "Tu búsqueda ha comenzado.", "jobId": job_id}


# --- Funnel Scrape (n8n → ARIA Suite) ---
@app.post("/funnel-scrape")
async def funnel_scrape(request: FunnelScrapeRequest):
    """
    Endpoint llamado por n8n cuando un lead llena el funnel de ventas.
    El usuario ya debe existir en Supabase (creado previamente por n8n).
    Solo lanza el scraping de Google Maps con niche + location.
    """
    headers = get_supabase_headers(content_type=True, prefer_return=True)

    # 1. Buscar usuario por email (ya creado por n8n)
    search_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/usuarios_scraper?correo_electronico=eq.{request.email}&select=*",
        headers=get_supabase_headers(),
    )
    if not search_response.json():
        raise HTTPException(status_code=404, detail=f"Usuario {request.email} no encontrado. Debe ser creado en n8n antes de llamar a este endpoint.")
    usuario = search_response.json()[0]

    # 2. Crear scraping job (sin validar leads disponibles — el funnel siempre scrapea)
    job_data = {
        "user_id": usuario["id"],
        "status": "PENDING",
        "business_type": request.niche,
        "location": request.location,
        "get_emails": True,
        "get_business_model": False,
    }
    job_response = requests.post(
        f"{SUPABASE_URL}/rest/v1/scraping_jobs",
        headers=headers,
        json=job_data,
    )
    if job_response.status_code not in [200, 201]:
        raise HTTPException(status_code=500, detail="No se pudo registrar el trabajo de scraping.")
    job_id = job_response.json()[0]["id"]

    # 5. Lanzar scraping en Apify (reutiliza el mismo scraper de Maps)
    try:
        run_id = google_maps_scraper.start_google_maps_scrape(
            business_type=request.niche,
            location=request.location,
            get_emails=True,
            webhook_base_url=WEBHOOK_BASE_URL,
            job_id=job_id,
        )
        update_job_run_id(job_id, run_id)
    except Exception as e:
        update_job_results(job_id, "FAILED", error_message=str(e))
        raise HTTPException(status_code=502, detail=f"Error al iniciar Apify: {e}")

    print(f"[Funnel] Scraping iniciado para {request.email}: '{request.niche}' en '{request.location}' (job: {job_id})")

    return {
        "status": "success",
        "message": f"Scraping iniciado para '{request.niche}' en '{request.location}'.",
        "jobId": job_id,
        "userId": usuario["id"],
        "email": request.email,
    }


# --- Job Status ---
@app.get("/job/{job_id}")
async def get_job_status_and_results(job_id: str):
    headers = get_supabase_headers()
    response = requests.get(f"{SUPABASE_URL}/rest/v1/scraping_jobs?id=eq.{job_id}&select=status,results_data", headers=headers)
    if not response.json():
        raise HTTPException(status_code=404, detail="Trabajo no encontrado.")
    job_data = response.json()[0]
    final_response = {"status": job_data.get("status")}
    if job_data.get("status") == "COMPLETED" and job_data.get("results_data"):
        final_response["results"] = job_data["results_data"]
    return final_response


# --- Cancel Job ---
@app.post("/cancel-job/{job_id}")
async def cancel_scraping_job(job_id: str):
    try:
        headers = get_supabase_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/scraping_jobs?id=eq.{job_id}&select=apify_actor_run_id,status",
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

        usuario = validate_user_and_leads(user_id=request.userId, email=request.correo_electronico)
        user_id = usuario.get("id")

        job_headers = get_supabase_headers(content_type=True, prefer_return=True)
        job_data = {
            "user_id": user_id,
            "status": "PENDING",
            "business_type": "Facebook Ads",
            "location": scrape_url,
            "get_emails": False,
            "get_business_model": False,
            "created_at": request.timestamp,
        }

        job_response = requests.post(f"{SUPABASE_URL}/rest/v1/scraping_jobs", headers=job_headers, json=job_data)
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

        usuario = validate_user_and_leads(user_id=request.userId, email=request.correo_electronico)
        user_id = usuario.get("id")

        job_headers = get_supabase_headers(content_type=True, prefer_return=True)
        job_data = {
            "user_id": user_id,
            "status": "PENDING",
            "business_type": "Facebook Pages (Bulk)",
            "location": f"{len(page_urls)} páginas",
            "get_emails": False,
            "get_business_model": False,
            "created_at": request.timestamp,
            "results_data": {"original_pages": original_pages_data},
        }

        job_response = requests.post(f"{SUPABASE_URL}/rest/v1/scraping_jobs", headers=job_headers, json=job_data)
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


# =============================================
# 5. WEBHOOKS Y TAREAS EN SEGUNDO PLANO
# =============================================

# --- Google Places Webhook ---
@app.post("/webhook-google-places-succeeded")
async def handle_google_places_webhook(payload: GooglePlacesWebhookPayload, background_tasks: BackgroundTasks):
    job_id = payload.job_id
    dataset_id = payload.resource.defaultDatasetId
    print(f"Webhook 1/2: Google Places terminó para Job ID: {job_id}.")
    background_tasks.add_task(process_google_places_results, job_id, dataset_id)
    return {"status": "webhook 1 received"}


async def process_google_places_results(job_id: str, google_places_dataset_id: str):
    try:
        headers = get_supabase_headers()
        job_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/scraping_jobs?id=eq.{job_id}&select=*,usuarios_scraper(correo_electronico)",
            headers=headers,
        )
        if not job_response.json():
            return
        job_details = job_response.json()[0]

        dataset_items = google_maps_scraper.get_dataset_items(google_places_dataset_id)

        if not job_details.get("get_business_model"):
            final_leads = google_maps_scraper.build_final_leads(dataset_items, job_details.get("get_emails"))
            final_json_output = {"data": final_leads, "results_count": len(final_leads)}
            update_job_results(job_id, "COMPLETED", results=final_json_output)

            user_id = job_details.get("user_id")
            if user_id:
                increment_user_leads_count(user_id, len(final_leads))
                save_leads_to_table(user_id, job_id, "maps", final_leads)

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
            final_json_output = {"data": final_leads, "results_count": len(final_leads)}
            update_job_results(job_id, "COMPLETED", results=final_json_output)
            user_id = job_details.get("user_id")
            if user_id:
                increment_user_leads_count(user_id, len(final_leads))
                save_leads_to_table(user_id, job_id, "maps", final_leads)
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
            f"{SUPABASE_URL}/rest/v1/scraping_jobs?id=eq.{job_id}&select=*,usuarios_scraper(correo_electronico)",
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

        user_id = job_details.get("user_id")
        if user_id:
            increment_user_leads_count(user_id, len(final_leads))
            save_leads_to_table(user_id, job_id, "maps", final_leads)

        print(f"Trabajo {job_id} completado y resultados guardados exitosamente.")

    except Exception as e:
        print(f"Error en el procesamiento final para job {job_id}: {e}")
        update_job_results(job_id, "FAILED", error_message=str(e))


# --- Facebook Ads Webhook ---
@app.post("/webhook-facebook-ads-succeeded")
async def handle_facebook_ads_webhook(payload: GooglePlacesWebhookPayload, background_tasks: BackgroundTasks):
    job_id = payload.job_id
    dataset_id = payload.resource.defaultDatasetId
    print(f"Webhook: Facebook Ads terminó para Job ID: {job_id}")
    background_tasks.add_task(process_facebook_ads_results, job_id, dataset_id)
    return {"status": "webhook received"}


async def process_facebook_ads_results(job_id: str, dataset_id: str):
    try:
        headers = get_supabase_headers()
        job_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/scraping_jobs?id=eq.{job_id}&select=user_id",
            headers=headers,
        )
        user_id = job_response.json()[0].get("user_id") if job_response.json() else None

        client = ApifyClient(apify_token)
        dataset_items = client.dataset(dataset_id).list_items().items

        if dataset_items and "error" in dataset_items[0]:
            error_message = dataset_items[0].get("error", "Error desconocido del actor")
            update_job_results(job_id, "FAILED", error_message=str(error_message))
            return

        normalized_data = facebook_ads_scraper.build_facebook_ads_table_items(dataset_items)

        final_json_output = {"data": normalized_data, "results_count": len(normalized_data)}
        update_job_results(job_id, "COMPLETED", results=final_json_output)

        if user_id:
            save_leads_to_table(user_id, job_id, "facebook", normalized_data)

        print(f"Facebook Ads scraping {job_id} completado. {len(normalized_data)} anuncios extraídos.")

    except Exception as e:
        print(f"Error procesando resultados de Facebook Ads para job {job_id}: {e}")
        update_job_results(job_id, "FAILED", error_message=str(e))


# --- Facebook Pages Webhook ---
@app.post("/webhook-facebook-pages-succeeded")
async def handle_facebook_pages_webhook(payload: GooglePlacesWebhookPayload, background_tasks: BackgroundTasks):
    job_id = payload.job_id
    dataset_id = payload.resource.defaultDatasetId
    print(f"Webhook: Facebook Pages terminó para Job ID: {job_id}")
    background_tasks.add_task(process_facebook_pages_results, job_id, dataset_id)
    return {"status": "webhook received"}


async def process_facebook_pages_results(job_id: str, dataset_id: str):
    try:
        headers = get_supabase_headers()
        job_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/scraping_jobs?id=eq.{job_id}&select=user_id,results_data",
            headers=headers,
        )

        if not job_response.json():
            raise Exception("No se pudo recuperar el job de la base de datos")

        job_data = job_response.json()[0]
        user_id = job_data.get("user_id")
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

        if user_id:
            increment_user_leads_count(user_id, len(matched_results))
            save_leads_to_table(user_id, job_id, "facebook", matched_results)

        print(f"Facebook Pages scraping {job_id} completado. {len(matched_results)} páginas extraídas.")

    except Exception as e:
        print(f"Error procesando resultados de Facebook Pages para job {job_id}: {e}")
        update_job_results(job_id, "FAILED", error_message=str(e))
