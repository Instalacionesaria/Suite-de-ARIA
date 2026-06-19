---
name: desplegar-frontend
description: Despliega el frontend de TIBESA (Frontend-Scraper-TIBESA, React+Vite) a Vercel con la CLI. Úsala cuando el usuario pida desplegar, publicar, subir o poner en producción el frontend de este proyecto.
---

# Desplegar Frontend TIBESA

Despliega el frontend de este proyecto (`Frontend-Scraper-TIBESA/`, React + Vite) al proyecto de Vercel **`frontend-scraper-tibesa-2026`** usando la CLI de Vercel ya logueada.

## Datos fijos de este proyecto

- **Directorio del frontend:** `Frontend-Scraper-TIBESA/` (¡el deploy se corre DESDE ahí, no desde la raíz del repo!)
- **Proyecto Vercel:** `frontend-scraper-tibesa-2026` (ya vinculado en `.vercel/project.json`)
- **URL de producción:** https://frontend-scraper-tibesa-2026.vercel.app
- **Cuenta Vercel:** `instalacionesariaia-1374`
- **Build:** `npm run build` (Vite) → `dist/`
- **`vercel.json`:** rewrite SPA (`/(.*) → /index.html`). No tocarlo.
- **API backend:** el frontend lee `VITE_API_BASE` (definida con `import.meta.env.VITE_API_BASE`, fallback `http://localhost:8000`). En Vercel **ya está configurada** como env var de Production. No hace falta setearla en cada deploy.

## Workflow

### 1. Posicionarse en el frontend
```bash
cd Frontend-Scraper-TIBESA
```

### 2. Preflight rápido
```bash
vercel whoami            # confirmar login (debe ser instalacionesariaia-1374)
cat .vercel/project.json # confirmar que sigue vinculado a frontend-scraper-tibesa-2026
```
Si no está logueado: pedir al usuario que corra `! vercel login` en el prompt.
Si no está vinculado: `vercel link --yes --project frontend-scraper-tibesa-2026`.

### 3. Verificar el build ANTES de subir
```bash
npm run build
```
Si el build falla, **detente y reporta el error**. No subas un build roto.

### 4. Confirmar producción vs preview
- Default: **preview** → `vercel --yes` (URL temporal, no toca producción).
- **Producción** (solo si el usuario lo pide explícito): pide confirmación mostrando proyecto + branch, y luego:
```bash
vercel --prod --yes
```

### 5. Reportar
Devuelve la URL del deployment, el tipo (preview/prod) y el inspector URL.

## ⚠️ Recordatorio crítico: el backend va aparte

El frontend en Vercel apunta al **backend de producción** vía `VITE_API_BASE`. Los scrapers/funciones nuevas solo funcionan en vivo cuando el **backend** (`Backend-Scraper-TIBESA/`, desplegado en EasyPanel/Docker) también tiene esos cambios. Desplegar el frontend NO despliega el backend. Si el usuario agregó scrapers o endpoints nuevos, recuérdale desplegar el backend (commit + push para que EasyPanel reconstruya) o las tarjetas nuevas fallarán al usarse.

## Reglas

- Nunca desplegar a producción sin confirmación explícita del usuario en la conversación actual.
- No modificar `.env` ni `vercel.json` sin pedirlo.
- Esta skill solo despliega: no hace `git commit` ni `git push`.
- El deploy por CLI sube el working tree actual (incluye cambios sin commitear).
