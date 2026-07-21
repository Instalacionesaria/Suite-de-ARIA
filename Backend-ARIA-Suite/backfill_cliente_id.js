#!/usr/bin/env node
/**
 * BACKFILL: rellena usuarios_scraper.cliente_id cruzando por email con app-next.
 *
 * Las dos bases son proyectos Supabase distintos (no se puede JOIN en SQL):
 *   - Scraper  (urxu…): usuarios_scraper.correo_electronico  → se le pone cliente_id
 *   - app-next (pajh…): aria_brain_clientes.id + email       → fuente de la verdad
 *
 * Este script:
 *   1) Lee aria_brain_clientes (id,email) de app-next
 *   2) Lee usuarios_scraper (id,correo_electronico,cliente_id) del scraper
 *   3) Para cada usuario del scraper sin cliente_id, busca el cliente de app-next
 *      con el mismo email (case-insensitive) y hace PATCH del cliente_id.
 *
 * ⚠️ CORRER ESTO ANTES de desplegar el proxy nuevo (que ya manda cliente_id).
 *    Si no, un usuario existente sin cliente_id se auto-provisionaría como NUEVO
 *    (fila duplicada + saldo reseteado a los leads gratis).
 *
 * Uso (lee las claves de los dos .env automáticamente):
 *   node backfill_cliente_id.js            # modo simulación (dry-run, no escribe)
 *   node backfill_cliente_id.js --apply    # aplica los cambios
 */

const fs = require('fs');
const path = require('path');

// --- Cargar claves desde los dos archivos .env (sin depender de dotenv) ---
function parseEnv(file) {
  const out = {};
  if (!fs.existsSync(file)) return out;
  for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
    if (m) out[m[1]] = m[2].replace(/^["']|["']$/g, '');
  }
  return out;
}

const scraperEnv = parseEnv(path.join(__dirname, '.env'));
const appNextEnv = parseEnv(path.join(__dirname, '..', '..', 'app-next', '.env.local'));

const SCRAPER_URL = process.env.SCRAPER_SUPABASE_URL || scraperEnv.SUPABASE_URL;
const SCRAPER_KEY = process.env.SCRAPER_SERVICE_ROLE_KEY || scraperEnv.SUPABASE_SERVICE_ROLE_KEY;
const APPNEXT_URL = process.env.APPNEXT_SUPABASE_URL || appNextEnv.SUPABASE_URL;
const APPNEXT_KEY = process.env.APPNEXT_SERVICE_ROLE_KEY || appNextEnv.SUPABASE_SERVICE_ROLE_KEY;

const APPLY = process.argv.includes('--apply');

if (!SCRAPER_URL || !SCRAPER_KEY || !APPNEXT_URL || !APPNEXT_KEY) {
  console.error('❌ Faltan claves. Revisa Backend-ARIA-Suite/.env y app-next/.env.local');
  process.exit(1);
}

const headers = (key) => ({ apikey: key, Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' });

async function getAll(base, key, table, select) {
  const r = await fetch(`${base}/rest/v1/${table}?select=${select}`, { headers: headers(key) });
  if (!r.ok) throw new Error(`GET ${table} → ${r.status} ${await r.text()}`);
  return r.json();
}

(async () => {
  console.log(`\n=== BACKFILL cliente_id ${APPLY ? '(APLICAR)' : '(DRY-RUN — no escribe)'} ===\n`);

  const clientes = await getAll(APPNEXT_URL, APPNEXT_KEY, 'aria_brain_clientes', 'id,email');
  const porEmail = new Map();
  for (const c of clientes) {
    if (c.email) porEmail.set(String(c.email).trim().toLowerCase(), c.id);
  }
  console.log(`app-next: ${clientes.length} clientes cargados.`);

  const usuarios = await getAll(SCRAPER_URL, SCRAPER_KEY, 'usuarios_scraper', 'id,correo_electronico,cliente_id');
  console.log(`scraper: ${usuarios.length} usuarios_scraper.\n`);

  let mapeados = 0, yaTenian = 0, sinMatch = 0;
  const noMatch = [];

  for (const u of usuarios) {
    if (u.cliente_id) { yaTenian++; continue; }
    const email = (u.correo_electronico || '').trim().toLowerCase();
    const clienteId = email ? porEmail.get(email) : null;
    if (!clienteId) { sinMatch++; noMatch.push(u.correo_electronico || u.id); continue; }

    if (APPLY) {
      const r = await fetch(`${SCRAPER_URL}/rest/v1/usuarios_scraper?id=eq.${u.id}`, {
        method: 'PATCH',
        headers: headers(SCRAPER_KEY),
        body: JSON.stringify({ cliente_id: clienteId }),
      });
      if (!r.ok) { console.error(`  ⚠️ falló PATCH ${u.correo_electronico}: ${r.status}`); continue; }
    }
    mapeados++;
    console.log(`  ${APPLY ? '✔' : '·'} ${u.correo_electronico} → ${clienteId}`);
  }

  console.log(`\n--- Resumen ---`);
  console.log(`  Mapeados:      ${mapeados} ${APPLY ? '(escritos)' : '(se escribirían)'}`);
  console.log(`  Ya tenían:     ${yaTenian}`);
  console.log(`  Sin match:     ${sinMatch}`);
  if (noMatch.length) console.log(`  Sin cliente en app-next: ${noMatch.join(', ')}`);
  if (!APPLY) console.log(`\n👉 Revisa la lista. Si está bien, corre de nuevo con --apply\n`);
})();
