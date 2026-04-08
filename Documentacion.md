# ARIA Suite - Automatizacion de Captacion y Entrega de Leads via Funnel

## Resumen Ejecutivo

ARIA Suite ahora integra un **funnel de ventas inteligente** que captura prospectos interesados, scrapea leads automaticamente de Google Maps segun su nicho y ubicacion, y los entrega directamente en la cuenta del usuario dentro de la plataforma. Todo sin intervencion manual.

---

## Problema que Resuelve

Antes, el proceso era:

1. El vendedor contacta al prospecto
2. Le explica ARIA Suite
3. Le crea una cuenta manualmente
4. El prospecto entra y configura su primer scraping

**Ahora:** El prospecto llena un formulario (funnel), y automaticamente recibe sus leads scrapeados en su cuenta.

---

## Arquitectura del Flujo

```
┌─────────────────┐
│  Funnel de       │     El prospecto llena el formulario
│  Ventas (Web)    │     con su nicho, ubicacion, email, etc.
└───────┬─────────┘
        │ POST (datos del formulario)
        v
┌─────────────────┐
│  n8n             │     Recibe los datos via Webhook
│  (Automatizacion)│     y los distribuye a 2 destinos:
└───────┬─────────┘
        │
        ├──────────────────────────────┐
        │                              │
        v                              v
┌─────────────────┐          ┌─────────────────┐
│  Google Sheets   │          │  ARIA Suite      │
│  (Para el        │          │  Backend         │
│   vendedor)      │          │  /funnel-scrape  │
└─────────────────┘          └───────┬─────────┘
                                     │
                     ┌───────────────┼───────────────┐
                     │               │               │
                     v               v               v
              ┌───────────┐  ┌───────────┐  ┌───────────────┐
              │ Buscar o   │  │ Crear Job │  │ Lanzar Apify  │
              │ Crear      │  │ de        │  │ Google Maps   │
              │ Usuario    │  │ Scraping  │  │ Scraper       │
              │ (Supabase) │  │           │  │               │
              └───────────┘  └───────────┘  └───────┬───────┘
                                                     │
                                                     │ Webhook de vuelta
                                                     v
                                            ┌───────────────────┐
                                            │ Leads guardados en │
                                            │ la cuenta del      │
                                            │ usuario en ARIA    │
                                            │ Suite              │
                                            └───────────────────┘
```

---

## Detalle Tecnico del Flujo

### Paso 1: Funnel de Ventas

El prospecto visita una landing page y llena un formulario con:

| Campo       | Ejemplo                              | Uso                          |
|-------------|--------------------------------------|------------------------------|
| profession  | Agencia de Marketing                 | Contexto del cliente         |
| clientType  | Empresas medianas (20-200 empleados) | Segmentacion                 |
| **niche**   | gimnasios                            | **Que scrapear en Maps**     |
| **location**| lima, peru                           | **Donde scrapear**           |
| name        | Jorge                                | Nombre del usuario           |
| **email**   | jorge@gmail.com                      | **Identificador de cuenta**  |
| phone       | 925610279                            | Contacto / codigo de acceso  |

Los campos en **negrita** son los que usa el backend para ejecutar el scraping.

### Paso 2: n8n (Orquestador)

n8n recibe los datos del funnel y ejecuta 2 acciones en paralelo:

1. **Google Sheets** - Registra al prospecto para que el vendedor lo vea
2. **HTTP Request a ARIA Suite** - Llama a `POST /funnel-scrape` con los datos

**Configuracion del nodo HTTP Request en n8n:**

```
Metodo: POST
URL: https://[tu-backend-url]/funnel-scrape
Content-Type: application/json
Body:
{
  "niche": "{{ $json.body.niche }}",
  "location": "{{ $json.body.location }}",
  "email": "{{ $json.body.email }}",
  "name": "{{ $json.body.name }}",
  "phone": "{{ $json.body.phone }}",
  "profession": "{{ $json.body.profession }}",
  "clientType": "{{ $json.body.clientType }}"
}
```

### Paso 3: ARIA Suite Backend (`/funnel-scrape`)

El endpoint realiza 5 operaciones secuenciales:

1. **Buscar usuario** por email en Supabase (`usuarios_scraper`)
2. **Crear usuario** si no existe (con 100 leads gratuitos, tipo "funnel")
3. **Verificar leads disponibles** del usuario
4. **Crear job de scraping** en Supabase (`scraping_jobs`)
5. **Lanzar Apify** con el scraper de Google Maps usando `niche` y `location`

### Paso 4: Apify Scrapea y Devuelve Resultados

El scraper de Google Maps (Apify) ejecuta la busqueda y, al terminar, llama al webhook del backend. El backend:

1. Recibe los resultados de Apify
2. Procesa y limpia los leads
3. Los guarda en `aria_suite_leads_per_user` vinculados al usuario
4. Actualiza el contador de leads del usuario

### Paso 5: El Usuario Accede a sus Leads

El prospecto entra a ARIA Suite con su email y codigo de acceso (su numero de telefono), y encuentra sus leads ya scrapeados en la seccion **"Mis Leads"**.

---

## Stack Tecnologico

| Componente     | Tecnologia                    |
|----------------|-------------------------------|
| Funnel         | Landing page (cualquier CMS)  |
| Automatizacion | n8n (self-hosted)             |
| Backend        | FastAPI (Python) + Uvicorn    |
| Scraping       | Apify (Google Maps Scraper)   |
| Base de datos  | Supabase (PostgreSQL)         |
| Frontend       | React + Vite + TailwindCSS    |

---

## Metricas Clave

- **Tiempo de entrega**: El prospecto recibe sus leads en minutos despues de llenar el funnel
- **Cero intervencion manual**: Todo es automatico desde el formulario hasta la entrega
- **Reutilizacion total**: Se usa el mismo motor de scraping probado que ya funciona en produccion
- **Costo de adquisicion**: El prospecto "prueba" el producto antes de hablar con un vendedor

---

## Impacto en el Negocio

### Antes (Flujo Manual)
```
Vendedor contacta → Explica → Crea cuenta → Usuario configura → Scrapea
Tiempo: dias | Tasa de conversion: baja
```

### Ahora (Flujo Automatizado con Funnel)
```
Prospecto llena funnel → Leads aparecen en su cuenta automaticamente
Tiempo: minutos | Tasa de conversion: alta (el producto se vende solo)
```

El funnel funciona como un **"test drive"** de ARIA Suite: el prospecto experimenta el valor del producto antes de que el vendedor lo contacte, lo que cambia completamente la dinamica de la venta.
