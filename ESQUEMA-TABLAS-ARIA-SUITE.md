# Esquema de tablas del backend ARIA Suite (para la fusión con app-next)

> Reconstruido a partir de `Backend-ARIA-Suite/app.py`, `comandos_para_supabase.sql`
> y `tools_scrapers/*.py`. El backend NO usa el cliente de Supabase: pega directo a
> la **REST API** (`{SUPABASE_URL}/rest/v1/<tabla>`) con `apikey` + `Authorization`
> = `SUPABASE_SERVICE_ROLE_KEY`.

## ⚠️ Dato central para la fusión

El backend de ARIA Suite corre contra un **proyecto Supabase DISTINTO** al de `app-next`:

| App        | Proyecto Supabase        | Tabla(s) principales                                             |
|------------|--------------------------|------------------------------------------------------------------|
| ARIA Suite | `urxu…….supabase.co`     | `usuarios_scraper`, `scraping_jobs`, `aria_suite_leads_per_user` |
| app-next   | `pajh…….supabase.co`     | `aria_brain_client_state` (modelo clave-valor)                   |

Son dos bases separadas. Los scrapers dependen de SU base (la de `urxu…`), no de la
de `app-next`. Cualquier fusión tiene que decidir explícitamente **dónde viven estas
3 tablas** después de integrar (ver notas al final).

---

## Tabla 1 — `usuarios_scraper`  (cuentas + saldo de leads)

Es la tabla de usuarios del scraper. Login por `correo_electronico` + `codigo_de_acceso`
(el "código" es el teléfono, según la doc del funnel).

| Columna                     | Tipo (inferido) | Rol                                                                 |
|-----------------------------|-----------------|---------------------------------------------------------------------|
| `id`                        | UUID (PK)       | Identificador; referenciado por las otras 2 tablas                  |
| `correo_electronico`        | TEXT            | Identificador de login / búsqueda de usuario                        |
| `codigo_de_acceso`          | TEXT            | "Contraseña" (en el funnel = el teléfono)                           |
| `nombre`                    | TEXT            | Nombre del usuario                                                   |
| `numero_leads_scrapeados`   | INT             | Contador acumulado de leads ya scrapeados                           |
| `leads_base_gratuitos`      | INT             | Saldo de leads gratis (se descuenta primero)                        |
| `leads_adicionales_pagados` | INT             | Saldo de leads pagados (se descuenta después de agotar los gratis)  |
| `leads_disponibles_en_total`| INT             | **Probable columna GENERADA** = gratuitos + pagados (solo se lee)   |

**Lógica de saldo** (`increment_user_leads_count`, app.py:288): al guardar N leads,
sube `numero_leads_scrapeados += N` y descuenta N primero de `leads_base_gratuitos`
y el resto de `leads_adicionales_pagados` (nunca baja de 0). `leads_disponibles_en_total`
solo se lee, nunca se escribe → casi seguro es columna generada/vista.

---

## Tabla 2 — `scraping_jobs`  (un trabajo por búsqueda lanzada)

Cada búsqueda de scraping crea una fila. Vincula usuario ↔ run de Apify ↔ resultados.

| Columna              | Tipo (inferido) | Rol                                                                       |
|----------------------|-----------------|---------------------------------------------------------------------------|
| `id`                 | UUID (PK)       | Identificador del job (se pasa a Apify como `job_id` en el webhook)       |
| `user_id`            | UUID (FK→usuarios_scraper.id) | Dueño del job                                              |
| `status`             | TEXT            | `PENDING` → `RUNNING` → `COMPLETED` / `FAILED`                            |
| `business_type`      | TEXT            | Qué scrapear (nicho / búsqueda; en LinkedIn = job_title)                  |
| `location`           | TEXT            | Dónde scrapear (Maps exige ≥3 partes: distrito, ciudad, país)            |
| `get_emails`         | BOOL            | Si el scraper de Maps debe extraer emails                                 |
| `get_business_model` | BOOL            | Flag de "modelo de negocio"                                               |
| `apify_actor_run_id` | TEXT            | Run ID del actor de Apify (para tracking/cancelación)                     |
| `results_data`       | JSONB           | Antes de terminar: `{"max_leads": N}`. Al terminar: resultados finales    |
| `error_message`      | TEXT            | Mensaje si `status = FAILED`                                              |
| `created_at`         | TIMESTAMPTZ     | (inferido) fecha de creación                                              |

**Notas:**
- Se crea en 3 sitios: `create_scraping_job` (Maps normal, app.py:239), `/funnel-scrape`
  (app.py:580) y los endpoints de Facebook/LinkedIn (app.py:781, 852, 905).
- Apify llama de vuelta a `{WEBHOOK_BASE_URL}/webhook-…-succeeded` con `{job_id, resource:{defaultDatasetId}}`;
  el backend lee el dataset, normaliza y guarda en `aria_suite_leads_per_user`.
- El join `scraping_jobs?select=*,usuarios_scraper(correo_electronico)` (app.py:949)
  confirma la FK `scraping_jobs.user_id → usuarios_scraper.id`.

---

## Tabla 3 — `aria_suite_leads_per_user`  (los leads scrapeados)

Única tabla con SQL explícito (`comandos_para_supabase.sql`). Aquí caen TODOS los leads
sin importar la fuente; el detalle crudo va en `raw_data`.

```sql
CREATE TABLE aria_suite_leads_per_user (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES usuarios_scraper(id),
  job_id  UUID REFERENCES scraping_jobs(id),
  source  TEXT NOT NULL DEFAULT 'maps',   -- 'maps' | 'facebook' | 'linkedin'
  name     TEXT,
  email    TEXT,
  phone    TEXT,
  website  TEXT,
  location TEXT,
  category TEXT,
  raw_data JSONB DEFAULT '{}',            -- el lead completo, sin recortar
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_aria_leads_user_id ON aria_suite_leads_per_user(user_id);
CREATE INDEX idx_aria_leads_email   ON aria_suite_leads_per_user(email);
```

**Mapeo de columnas planas** (`save_leads_to_table`, app.py:347) — es tolerante a
distintas formas de nombrar según la fuente:

| Columna    | Se llena desde (primer no-vacío)                                        |
|------------|-------------------------------------------------------------------------|
| `name`     | `title` / `page_name` / `pageName` / `fullName`                         |
| `email`    | `email`                                                                 |
| `phone`    | `phone` / `phoneUnformatted`                                            |
| `website`  | `website` / `companyWebsite`                                            |
| `location` | `address` / `city`                                                      |
| `category` | `categoryName` / `industry`                                             |
| `raw_data` | el objeto lead COMPLETO (todo lo que trajo el scraper)                  |

Se inserta en **lotes de 50**.

### `source` y forma del `raw_data` por scraper

- **`maps`** (`google_maps_scraper`): leads de Google Places. Campos ricos: `title`,
  `address`, `phone`, `website`, `email`, `categoryName`, etc.
- **`facebook`** (Ads → Pages): el flujo de Ads solo saca `page_name`, `page_profile_uri`,
  `page_id`; luego Pages enriquece con `facebookUrl`, `likes`, `title`, `address`,
  `pageId`, `pageName`, `pageUrl`, `phone`, `email`, `website`, `followers`,
  `business_service_area`.
- **`linkedin`** (Apollo, `build_final_leads`): normaliza a `title`/`fullName`, `email`,
  `phone`, `jobTitle`, `linkedinProfile`, `companyName`, `companyWebsite`,
  `companyLinkedin`, `companySize`, `industry`, `city`, etc.

---

## Endpoints del backend (FastAPI) — contrato que consume el frontend

| Método | Ruta                              | Para qué                                              |
|--------|-----------------------------------|-------------------------------------------------------|
| POST   | `/login`                          | Login por correo + código de acceso                   |
| GET    | `/user-leads?email=`              | Saldo del usuario (sidebar)                           |
| GET    | `/mis-leads?email=`               | Lista de leads del usuario                            |
| POST   | `/start-scraping`                 | Lanza scraping de Google Maps                         |
| POST   | `/start-facebook-ads-scraping`    | Lanza scraping de Facebook Ads Library                |
| POST   | `/start-facebook-pages-scraping`  | Lanza scraping de Facebook Pages                      |
| POST   | `/start-linkedin-scraping`        | Lanza scraping de LinkedIn (Apollo)                   |
| POST   | `/funnel-scrape`                  | Entrada del funnel (n8n) → crea job y scrapea Maps    |
| GET    | `/job/{job_id}`                   | Estado + resultados de un job                         |
| POST   | `/cancel-job/{job_id}`            | Cancela un run de Apify                               |
| POST   | `/chat`                           | Agente de onboarding (OpenAI)                         |
| POST   | `/send-email`, `/send-email-highlevel`, `/highlevel-mcp` | Email / HighLevel          |

Webhooks de retorno (los llama Apify, no el frontend):
`/webhook-google-places-succeeded`, `/webhook-facebook-ads-succeeded`,
`/webhook-facebook-pages-succeeded`, `/webhook-linkedin-apollo-succeeded`.

Env vars del backend: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `APIFY_API_TOKEN`,
`WEBHOOK_BASE_URL` (host público del backend en EasyPanel, para que Apify devuelva).

---

## Opciones para la fusión con app-next (sin romper los scrapers)

Los scrapers dependen de: (a) sus 3 tablas en el proyecto `urxu…`, (b) los tokens de
Apify, (c) `WEBHOOK_BASE_URL` público para el callback de Apify. Tres caminos:

1. **Proxy (menos invasivo, recomendado para empezar):** app-next NO toca las tablas
   del scraper; solo expone rutas en `/api/scrape/*` que reenvían al backend FastAPI
   existente (que sigue en EasyPanel con su Supabase `urxu…`). Cero migración de datos,
   cero riesgo de romper webhooks. La "fusión" es de UX, no de base de datos.

2. **Mismo proyecto Supabase, dos familias de tablas:** mover/duplicar `usuarios_scraper`,
   `scraping_jobs`, `aria_suite_leads_per_user` al proyecto `pajh…` de app-next y
   apuntar el backend ahí. Hay que mapear `usuarios_scraper.id` ↔ `cliente_id` de
   app-next y reconfigurar `WEBHOOK_BASE_URL`. Más trabajo, pero unifica datos.

3. **Reescribir la orquestación dentro de app-next:** portar los endpoints FastAPI a
   rutas Next.js. Máximo control, máximo riesgo — Apify + webhooks + saldo de leads hay
   que reimplementarlos con cuidado. Solo si se quiere retirar el backend Python.
