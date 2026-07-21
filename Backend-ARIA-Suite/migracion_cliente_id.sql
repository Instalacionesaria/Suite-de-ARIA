-- ============================================================
-- MIGRACIÓN: usuarios_scraper → identidad por cliente_id (app-next)
-- Proyecto Supabase del scraper: urxu… (NO el de app-next)
-- ============================================================
-- Contexto: ARIA Suite como producto separado desaparece. Ya no hay login
-- propio ni funnel. La identidad la da app-next (aria_brain_clientes.id).
-- usuarios_scraper deja de ser "tabla de usuarios" y pasa a ser el "monedero
-- de leads", ligado al cliente por cliente_id.
--
-- ⚠️ EJECUTAR EN ORDEN. La FASE 3 (DROP) es IRREVERSIBLE: correr solo
--    después de que el backend y el proxy ya usen cliente_id y esté probado.
-- ============================================================


-- ============================================================
-- FASE 1 — AGREGAR (no destructivo, reversible)
-- ============================================================

-- 1.1 Nueva llave de unión con app-next (nullable al inicio)
ALTER TABLE usuarios_scraper ADD COLUMN IF NOT EXISTS cliente_id UUID;

-- 1.2 Índice único (permite filas legacy sin cliente_id mientras se migra)
CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_scraper_cliente_id
  ON usuarios_scraper (cliente_id)
  WHERE cliente_id IS NOT NULL;


-- ============================================================
-- FASE 2 — BACKFILL (rellenar cliente_id de las filas existentes)
-- ============================================================
-- Las dos bases (urxu… scraper y pajh… app-next) son proyectos Supabase
-- distintos: NO se puede hacer un JOIN entre ellas en SQL. El backfill se
-- hace con un script (Node) que:
--   1) Lee correo_electronico + id de usuarios_scraper (urxu…)
--   2) Busca en aria_brain_clientes (pajh…) el id cuyo email coincida
--   3) UPDATE usuarios_scraper SET cliente_id = <ese id> WHERE id = <fila>
-- (Ver script backfill_cliente_id.js — pendiente de crear.)
--
-- Verificación post-backfill: cuántas filas quedaron sin mapear.
--   SELECT count(*) FROM usuarios_scraper WHERE cliente_id IS NULL;


-- ============================================================
-- FASE 3 — BORRAR (DESTRUCTIVO — solo tras probar backend + proxy)
-- ============================================================
-- Requisitos antes de correr esto:
--   [ ] app.py busca/crea usuarios_scraper por cliente_id (no por email)
--   [ ] /login y /funnel-scrape eliminados del backend
--   [ ] proxy route.ts envía cliente_id = sesion.sub
--   [ ] Probado en vivo: scrapea, muestra saldo y "Mis Leads"
--
-- ALTER TABLE usuarios_scraper DROP COLUMN codigo_de_acceso;   -- password muerto
-- ALTER TABLE usuarios_scraper DROP COLUMN nombre;             -- sale de app-next
-- ALTER TABLE usuarios_scraper DROP COLUMN correo_electronico; -- funnel eliminado
--
-- Opcional: hacer cliente_id obligatorio una vez migrado todo.
-- ALTER TABLE usuarios_scraper ALTER COLUMN cliente_id SET NOT NULL;
