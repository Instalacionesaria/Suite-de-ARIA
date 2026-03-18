# ARIA Suite — Frontend

Plataforma SaaS para scraping de leads y automatización de outreach. Construida con React 19, TypeScript y Tailwind CSS.

---

## Stack Tecnológico

| Tecnología | Versión | Uso |
|---|---|---|
| React | 19.2.4 | UI framework |
| TypeScript | ~5.9.3 | Tipado estático |
| Vite | 5.4.19 | Build tool + HMR |
| Tailwind CSS | 4.2.1 | Estilos utility-first |
| shadcn/ui | base-nova | Componentes UI |
| Framer Motion | 12.36.0 | Animaciones |
| React Router DOM | 7.13.1 | Navegación client-side |
| Lucide React | 0.577.0 | Iconos |

---

## Estructura del Proyecto

```
src/
├── App.tsx                    # Rutas principales
├── main.tsx                   # Punto de entrada de React
├── index.css                  # Estilos globales, animaciones, tema
├── components/
│   ├── ui/                    # 12 componentes shadcn/ui
│   └── HighLevelPanel.tsx     # Sidebar derecho (integración HighLevel)
├── layouts/
│   └── DashboardLayout.tsx    # Layout 3 columnas (nav + content + sidebar)
├── pages/
│   ├── LoginPage.tsx
│   └── dashboard/
│       ├── ScraperPage.tsx    # Scraping (Google Maps, LinkedIn, Facebook)
│       ├── LeadsPage.tsx      # Gestión de leads con tabla filtrable
│       ├── OutreachPage.tsx   # Outreach por Email/WhatsApp
│       ├── RecargaPage.tsx    # Planes de precios
│       └── OnboardingPage.tsx # Chatbot de asistencia IA
└── lib/
    └── utils.ts               # Utilidad cn()
```

---

## Rutas

```
/                        → LoginPage
/dashboard               → DashboardLayout
  /dashboard/scraper     → ScraperPage
  /dashboard/leads       → LeadsPage
  /dashboard/outreach    → OutreachPage
  /dashboard/recarga     → RecargaPage
  /dashboard/onboarding  → OnboardingPage
```

---

## Páginas

### Login
- Autenticación por email y código de acceso
- Carousel de módulos (Scrape, Prospect, Schedule)
- Animaciones con partículas y fondos con gradientes

### Scraper
- Tabs por fuente: Google Maps, LinkedIn, Facebook
- Formularios dinámicos por fuente
- Validación de inputs

### Leads
- Tabla con búsqueda y filtros por fuente
- Selección múltiple con acciones bulk
- Integración con panel de HighLevel

### Outreach
- Selección de canal: Email / WhatsApp
- Personalización de templates
- Indicador de leads seleccionados para envío

### Precios / Recarga
- Tres tiers: Basic, Professional, Enterprise
- Cards con stats y gradientes
- Links al sistema de pagos externo

### Onboarding
- Interfaz de chat con asistente IA
- Historial de mensajes con timestamps
- Botones de acción rápida
- Auto-scroll al último mensaje

---

## Arquitectura

**Layout:** Tres columnas fijas — navegación lateral izquierda (256px), contenido principal flexible, sidebar derecho con HighLevel (288px).

**Estado:** Local con `useState` por página. Sin estado global por ahora.

**Animaciones:**
- Framer Motion para transiciones de componentes y navegación
- CSS keyframes para animaciones repetitivas (drift, aurora, float, shimmer, border-spin)

**Sistema de diseño:**
- Colores primarios: índigo / púrpura (oklch color space)
- Fuente: Geist Variable
- Modo oscuro preparado en variables CSS

---

## Instalación y Desarrollo

```bash
# Instalar dependencias
npm install

# Servidor de desarrollo
npm run dev

# Build de producción
npm run build

# Preview del build
npm run preview
```

---

## Configuración de Paths

El alias `@/` apunta a `./src/` — disponible en TypeScript y Vite.

```ts
import { Button } from '@/components/ui/button'
```
