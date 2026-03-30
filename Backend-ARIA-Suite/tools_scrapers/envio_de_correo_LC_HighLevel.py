"""
Envío de correos masivos via LeadConnector (HighLevel) API v2.

Flujo:
1. Busca si el contacto ya existe en HighLevel por email.
2. Si no existe, lo crea con los datos disponibles del lead.
3. Envía el email a través de la API de conversaciones de HighLevel.

Requiere:
- PIT (Private Integration Token) del usuario.
- Location ID de la subcuenta de HighLevel.

Autor: Ing. Kevin Inofuente Colque - DataPath
"""

import requests
from typing import Optional

LC_BASE_URL = "https://services.leadconnectorhq.com"
LC_API_VERSION = "2021-07-28"


def _get_headers(pit_token: str) -> dict:
    """Headers estándar para la API de LeadConnector."""
    return {
        "Authorization": f"Bearer {pit_token}",
        "Version": LC_API_VERSION,
        "Content-Type": "application/json",
    }


def buscar_contacto_por_email(pit_token: str, location_id: str, email: str) -> Optional[dict]:
    """Busca un contacto existente en HighLevel por email."""
    headers = _get_headers(pit_token)
    try:
        response = requests.get(
            f"{LC_BASE_URL}/contacts/",
            headers=headers,
            params={"locationId": location_id, "query": email},
        )
        if response.status_code == 200:
            contacts = response.json().get("contacts", [])
            for contact in contacts:
                if contact.get("email", "").lower() == email.lower():
                    return contact
        return None
    except Exception as e:
        print(f"Error buscando contacto {email}: {e}")
        return None


def crear_contacto(
    pit_token: str,
    location_id: str,
    email: str,
    nombre: str = "",
    telefono: str = "",
    empresa: str = "",
) -> Optional[dict]:
    """Crea un contacto nuevo en HighLevel. Retorna el contacto creado o None."""
    headers = _get_headers(pit_token)

    # Separar nombre en first/last name
    partes_nombre = nombre.strip().split(" ", 1) if nombre else [""]
    first_name = partes_nombre[0]
    last_name = partes_nombre[1] if len(partes_nombre) > 1 else ""

    body = {
        "locationId": location_id,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
    }
    if telefono:
        body["phone"] = telefono
    if empresa:
        body["companyName"] = empresa

    try:
        response = requests.post(
            f"{LC_BASE_URL}/contacts/",
            headers=headers,
            json=body,
        )
        if response.status_code in [200, 201]:
            return response.json().get("contact")
        else:
            print(f"Error creando contacto {email}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Excepción creando contacto {email}: {e}")
        return None


def obtener_o_crear_contacto(
    pit_token: str,
    location_id: str,
    email: str,
    nombre: str = "",
    telefono: str = "",
    empresa: str = "",
) -> Optional[dict]:
    """Busca un contacto por email; si no existe, lo crea."""
    contacto = buscar_contacto_por_email(pit_token, location_id, email)
    if contacto:
        return contacto
    return crear_contacto(pit_token, location_id, email, nombre, telefono, empresa)


def enviar_email_lc(
    pit_token: str,
    contact_id: str,
    asunto: str,
    mensaje_html: str,
    email_from: str = "",
) -> dict:
    """
    Envía un email a un contacto existente via LeadConnector.

    Args:
        pit_token: Private Integration Token de HighLevel.
        contact_id: ID del contacto en HighLevel.
        asunto: Asunto del email.
        mensaje_html: Cuerpo del email (puede ser HTML).
        email_from: Remitente (ej: "Juan Pérez <juan@empresa.com>"). Opcional.

    Returns:
        dict con 'success' (bool) y 'message' (str).
    """
    headers = _get_headers(pit_token)

    body = {
        "type": "Email",
        "contactId": contact_id,
        "subject": asunto,
        "html": mensaje_html,
    }
    if email_from:
        body["emailFrom"] = email_from

    try:
        response = requests.post(
            f"{LC_BASE_URL}/conversations/messages",
            headers=headers,
            json=body,
        )
        if response.status_code in [200, 201]:
            return {"success": True, "message": "Email enviado correctamente."}
        else:
            error_detail = response.text
            try:
                error_detail = response.json().get("message", response.text)
            except Exception:
                pass
            return {"success": False, "message": f"Error {response.status_code}: {error_detail}"}
    except Exception as e:
        return {"success": False, "message": f"Error de conexión: {e}"}


def enviar_correo_masivo_lc(
    pit_token: str,
    location_id: str,
    asunto: str,
    mensaje_html: str,
    destinatarios: list[dict],
    email_from: str = "",
) -> dict:
    """
    Envío masivo de emails via LeadConnector.

    Args:
        pit_token: Private Integration Token.
        location_id: Location ID de HighLevel.
        asunto: Asunto del email.
        mensaje_html: Cuerpo del email (HTML).
        destinatarios: Lista de dicts con al menos 'email', opcionalmente 'nombre', 'telefono', 'empresa'.
        email_from: Remitente (opcional).

    Returns:
        dict con resumen: enviados, fallidos, errores.
    """
    enviados = []
    fallidos = []

    for dest in destinatarios:
        email = dest.get("email", "").strip()
        if not email:
            fallidos.append({"email": "(vacío)", "error": "Email vacío"})
            continue

        # 1. Obtener o crear contacto
        contacto = obtener_o_crear_contacto(
            pit_token=pit_token,
            location_id=location_id,
            email=email,
            nombre=dest.get("nombre", ""),
            telefono=dest.get("telefono", ""),
            empresa=dest.get("empresa", ""),
        )

        if not contacto:
            fallidos.append({"email": email, "error": "No se pudo crear/encontrar el contacto en HighLevel"})
            continue

        contact_id = contacto.get("id")

        # 2. Enviar email
        resultado = enviar_email_lc(
            pit_token=pit_token,
            contact_id=contact_id,
            asunto=asunto,
            mensaje_html=mensaje_html,
            email_from=email_from,
        )

        if resultado["success"]:
            enviados.append(email)
        else:
            fallidos.append({"email": email, "error": resultado["message"]})

    return {
        "enviados": len(enviados),
        "fallidos": len(fallidos),
        "detalle_errores": fallidos,
        "message": f"Se enviaron {len(enviados)} correos correctamente."
        + (f" {len(fallidos)} fallaron." if fallidos else ""),
    }
