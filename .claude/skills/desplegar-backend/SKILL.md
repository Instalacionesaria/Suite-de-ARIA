---
name: desplegar-backend
description: Despliega el backend de ARIA Suite (Backend-ARIA-Suite, FastAPI) a EasyPanel vía GitHub (commit + push a main → el usuario da clic en "Implementar" → EasyPanel reconstruye el Docker). Úsala cuando el usuario pida desplegar, publicar o subir el backend / la API de este proyecto.
---

# Desplegar Backend ARIA Suite

El backend (`Backend-ARIA-Suite/`, FastAPI) corre en **EasyPanel** y se despliega **vía GitHub**. ⚠️ NO es auto-deploy: el flujo es en **dos pasos** —
1. (lo hace Claude) `commit + push a main`
2. (lo hace EL USUARIO, manual) clic en el botón verde **"Implementar"** en EasyPanel, que reconstruye la imagen Docker desde el repo.

Claude NO puede disparar el rebuild; solo deja el código en GitHub. Tras el push, hay que **avisar al usuario que dé clic en "Implementar"**.

## Datos fijos de este proyecto

- **Repo:** `https://github.com/Instalacionesaria/Suite-de-ARIA.git` (remote `origin`)
- **Branch:** `main`
- **EasyPanel:** proyecto `backend-aria-suite` → servicio `backend-aria-suite-2026`. Fuente: GitHub `Instalacionesaria/Suite-de-ARIA`, rama `main`, **Ruta de compilación `/Backend-ARIA-Suite`** (monorepo), build por Dockerfile.
- **Backend:** `Backend-ARIA-Suite/` con `Dockerfile` (base `python:3.12-slim`, `uvicorn app:app` en el puerto 8000)
- **URL de producción:** (confirmar en EasyPanel → Dominios; es la que debe ir en `WEBHOOK_BASE_URL` para que los webhooks de Apify lleguen)
- **Health check:** `GET /` → `{"status":"online", "service":"ARIA Suite Backend API", ...}` (este backend NO tiene `/health`)
- El Dockerfile hace `COPY . .` + `pip install -r requirements.txt`, así que cualquier archivo nuevo en `Backend-ARIA-Suite/` entra solo al reconstruir.

## Workflow

### 1. Revisar qué se va a desplegar
```bash
git status --short
git diff --stat
```
Confirma que los cambios del backend (`app.py`, `tools_scrapers/`, `agente.py`, etc.) están ahí.

### 2. ⚠️ Si se agregaron dependencias de Python nuevas
Hay que añadirlas a `Backend-ARIA-Suite/requirements.txt` o el contenedor no las tendrá (el build hace `pip install -r requirements.txt`). Verifica con:
```bash
grep -iE "<paquete_nuevo>" Backend-ARIA-Suite/requirements.txt
```

### 3. Commit
Mensaje claro de lo que cambió. **Terminar SIEMPRE el mensaje con el footer de co-autoría:**
```
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```
Confirmar con el usuario antes de commitear si no lo pidió explícito.

### 4. Push a main
```bash
git push origin main
```
Esto solo sube el código a GitHub. **NO reconstruye nada por sí solo.**

### 5. Avisar al usuario que implemente (paso MANUAL del usuario)
Decirle explícitamente:
> "Push hecho ✅. Ahora ve a EasyPanel (servicio `backend-aria-suite-2026`) y dale clic al botón verde **'Implementar'** para que reconstruya con los cambios."

Claude no puede hacer este paso. Esperar a que el usuario confirme que ya implementó antes de verificar.

### 6. Verificar el despliegue (tras ~2-5 min de que el usuario implemente)
```bash
curl -s <URL_DE_PRODUCCION>/         # debe devolver {"status":"online", ...} con la lista de endpoints
```

## Notas

- **Frontend va aparte:** el frontend se despliega a Vercel con la CLI (skill `desplegar-frontend`). Pushear a `main` puede además disparar un deploy de Vercel si el proyecto está conectado a GitHub, pero el flujo oficial del frontend es por CLI.
- **Un solo repo:** frontend y backend viven en el mismo repo. Un push sube ambos; EasyPanel solo reconstruye el backend (su build apunta a `Backend-ARIA-Suite/`).
- Seguir la regla del proyecto: commit/push solo cuando el usuario lo pide.

## Si el deploy falla

- **Build falla en EasyPanel pero no local:** casi siempre es una dependencia faltante en `requirements.txt`. Revisar los logs de build en EasyPanel.
- **El contenedor arranca pero un endpoint falla:** puede ser falta de credenciales/env vars en EasyPanel (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `APIFY_API_TOKEN`, `WEBHOOK_BASE_URL`, etc.).
- **Webhooks de Apify no llegan:** `WEBHOOK_BASE_URL` debe apuntar a la URL pública de EasyPanel, no a ngrok.
