"""
Tools de Onboarding - ARIA Suite
El agente llama estas herramientas progresivamente para registrar
los datos del usuario y autocompletar los scrapers.
"""

from langchain_core.tools import tool


@tool
def set_tipo_negocio(tipo_negocio: str) -> str:
    """Registra el tipo de negocio del usuario (ej: peluquería, restaurante, agencia de marketing).
    Llama a esta herramienta tan pronto como el usuario mencione su tipo de negocio."""
    return f"tipo_negocio registrado: {tipo_negocio}"


@tool
def set_localizacion(localizacion: str) -> str:
    """Registra la localización del negocio del usuario.
    IMPORTANTE: La localización DEBE tener 3 niveles: distrito/zona, ciudad/región, país.
    Ejemplo: 'Cayma, Arequipa, Perú'. Solo llama a esta herramienta cuando tengas los 3 niveles."""
    return f"localizacion registrada: {localizacion}"


@tool
def set_productos(productos: str) -> str:
    """Registra los productos o servicios que ofrece el negocio del usuario y su precio aproximado.
    Llama a esta herramienta cuando el usuario describa qué vende o qué servicios ofrece."""
    return f"productos registrados: {productos}"


@tool
def set_cliente_ideal(cliente_ideal: str) -> str:
    """Registra el perfil del cliente ideal del usuario.
    Llama a esta herramienta cuando el usuario describa a quién le vende o su público objetivo."""
    return f"cliente_ideal registrado: {cliente_ideal}"


@tool
def set_mensaje_outreach(mensaje: str) -> str:
    """Genera y registra un mensaje de outreach (correo de venta en frío) para enviar en masa a los leads.
    El mensaje debe ser largo (8-15 oraciones), altamente persuasivo, con estructura de: gancho, problema, solución, prueba social y llamada a la acción.
    Llama a esta herramienta SOLO cuando ya tengas tipo_negocio, productos y cliente_ideal registrados."""
    return "mensaje_outreach registrado"


ALL_ONBOARDING_TOOLS = [
    set_tipo_negocio,
    set_localizacion,
    set_productos,
    set_cliente_ideal,
    set_mensaje_outreach,
]

TOOL_MAP = {t.name: t for t in ALL_ONBOARDING_TOOLS}
