"""
Agente IA de Onboarding - ARIA Suite
Recopila información del negocio del usuario para autocompletar los scrapers.
Usa tool calling de LangChain para registrar datos progresivamente.

Autor: Ing. Kevin Inofuente Colque - DataPath
"""

from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, ToolMessage

from tools.onboarding_tools import ALL_ONBOARDING_TOOLS, TOOL_MAP

# ============================================
# 1. MODELO POR DEFECTO Y CACHE
# ============================================
DEFAULT_MODEL = "gpt-4.1"
_model_cache: dict = {}


def get_models(model: str = DEFAULT_MODEL, api_key: str = None):
    """Obtiene el modelo con tools y sin tools, con cache."""
    cache_key = (model, api_key)
    if cache_key not in _model_cache:
        kwargs = {"temperature": 0.7}
        if api_key:
            kwargs["api_key"] = api_key
        chat = init_chat_model(model, **kwargs)
        _model_cache[cache_key] = (chat.bind_tools(ALL_ONBOARDING_TOOLS), chat)
    return _model_cache[cache_key]


# ============================================
# 2. PROMPT DE ONBOARDING
# ============================================
SYSTEM_PROMPT = """\
Eres el asistente de onboarding de ARIA Suite, una plataforma de scraping y outreach de leads.
Tu objetivo es conocer el negocio del usuario para autocompletar los campos de los scrapers.

INFORMACIÓN QUE NECESITAS RECOPILAR:
1. **Tipo de negocio**: Qué tipo de negocio tiene (ej: peluquería, restaurante, agencia de marketing, etc.)
2. **Productos/servicios**: Qué vende y a qué precio aproximado
3. **Cliente ideal**: A quién le vende (perfil de su cliente ideal)
4. **Localización**: Dónde está ubicado su negocio

REGLAS IMPORTANTES SOBRE LA LOCALIZACIÓN:
- La localización DEBE tener 3 niveles: distrito/zona, ciudad/región, país
- Ejemplo: "Cayma, Arequipa, Perú" o "Miraflores, Lima, Perú"
- Explícale al usuario que para scrapear es mejor ir de lo más específico a lo más general
- Si el usuario solo dice "Arequipa", pregúntale en qué distrito o zona específica

HERRAMIENTAS DISPONIBLES:
- Tienes herramientas para registrar cada dato del usuario (tipo_negocio, localizacion, productos, cliente_ideal).
- Llama a la herramienta correspondiente TAN PRONTO como el usuario te dé esa información, no esperes a tener todo.
- Puedes llamar múltiples herramientas en un mismo turno si el usuario te da varios datos a la vez.
- Sigue conversando normalmente después de registrar cada dato.

CÓMO COMPORTARTE:
- Sé amigable, conversacional y breve (no más de 3-4 oraciones por mensaje)
- Haz UNA pregunta a la vez, no bombardees con muchas preguntas
- Empieza preguntando sobre su negocio de forma natural

CUANDO YA TENGAS TODA LA INFORMACIÓN (tipo_negocio + localizacion como mínimo):
- Genera un mensaje de outreach usando la herramienta set_mensaje_outreach.
  El mensaje es un CORREO DE VENTA EN FRÍO que se enviará en masa a leads (negocios locales).
  El objetivo principal es GANAR CLIENTES, así que el mensaje debe ser altamente persuasivo.

  ESTRUCTURA DEL MENSAJE DE OUTREACH (debe tener TODOS estos elementos):
  1. ASUNTO GANCHO: Una línea inicial que genere curiosidad y evite sonar a spam.
  2. CONEXIÓN PERSONAL: Mencionar que encontraste su negocio buscando en su zona (ej: "Vi tu negocio en [zona]").
  3. PROBLEMA/DOLOR: Identificar un problema común que enfrentan los negocios como los de su cliente ideal.
  4. SOLUCIÓN CONCRETA: Explicar cómo los servicios/productos del usuario resuelven ese problema, con beneficios específicos y tangibles (no genéricos).
  5. PRUEBA SOCIAL o DATO: Incluir un dato, estadística o resultado que genere confianza (ej: "Nuestros clientes han visto un aumento del X%...").
  6. LLAMADA A LA ACCIÓN CLARA: Una pregunta o invitación específica para responder (no solo "conversemos", sino algo como "¿Te gustaría que te muestre cómo lo haríamos para tu negocio en particular?").
  7. DESPEDIDA PROFESIONAL: Nombre, cargo y empresa.

  REGLAS DEL MENSAJE:
  - Mínimo 8-10 oraciones, máximo 15.
  - Tono profesional pero cercano, NO corporativo ni frío.
  - Usar "[Tu Nombre]" como placeholder para el nombre del remitente.
  - Escríbelo en español.
  - NO usar emojis excesivos.
  - Cada párrafo debe ser corto (2-3 oraciones máximo) para facilitar la lectura.

- Haz un breve resumen confirmando los datos registrados.
- Dile al usuario que los campos del scraper y el mensaje de outreach ya están configurados automáticamente.
- Invítalo a ir a la sección "Scraper" para buscar leads y luego a "Outreach" para enviar correos.
- NO sigas haciendo preguntas ni sugiriendo configuraciones adicionales. Tu trabajo terminó.

Responde siempre en español."""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("history"),
    ("human", "{input}")
])

# ============================================
# 3. FUNCIÓN CON HISTORIAL
# ============================================
def chat_con_agente(mensaje_usuario: str, historial: list = None, model: str = None, api_key: str = None) -> dict:
    """
    Envía un mensaje al agente con historial de conversación.
    Retorna el texto de respuesta y los datos extraídos (si los hay).
    """
    chat_with_tools, chat_plain = get_models(model or DEFAULT_MODEL, api_key or None)
    chain = prompt | chat_with_tools

    history = []
    if historial:
        for msg in historial:
            if msg["role"] == "user":
                history.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                history.append(("ai", msg["content"]))

    respuesta = chain.invoke({"input": mensaje_usuario, "history": history})

    # Extraer datos de tool calls si existen
    datos_extraidos = None
    if respuesta.tool_calls:
        datos_extraidos = {}
        for tc in respuesta.tool_calls:
            key = tc["name"].replace("set_", "")
            args = tc["args"]
            datos_extraidos[key] = args.get(key, list(args.values())[0])

    texto = respuesta.content or ""

    # Si el modelo solo devolvió tool calls sin texto, re-invocar con resultados
    if not texto.strip() and respuesta.tool_calls:
        tool_messages = []
        for tc in respuesta.tool_calls:
            tool_fn = TOOL_MAP[tc["name"]]
            result = tool_fn.invoke(tc["args"])
            tool_messages.append(
                ToolMessage(content=result, tool_call_id=tc["id"])
            )

        messages = list(prompt.invoke({"input": mensaje_usuario, "history": history}).to_messages())
        messages.append(respuesta)
        messages.extend(tool_messages)

        # Re-invocar SIN tools para forzar respuesta de texto
        followup = chat_plain.invoke(messages)
        texto = followup.content or ""

    return {"response": texto, "extracted_data": datos_extraidos}


# ============================================
# 5. LOOP DE CONVERSACIÓN (para testing local)
# ============================================
def main():
    print("=" * 50)
    print("ARIA Suite - Agente de Onboarding")
    print("=" * 50)
    print("Escribe 'salir' para terminar.\n")

    historial = []
    while True:
        usuario = input("Tú: ").strip()

        if usuario.lower() in ['salir', 'exit', 'quit']:
            print("\nHasta luego!")
            break

        if not usuario:
            continue

        resultado = chat_con_agente(usuario, historial)
        historial.append({"role": "user", "content": usuario})
        historial.append({"role": "assistant", "content": resultado["response"]})

        print(f"\nARIA: {resultado['response']}")
        if resultado["extracted_data"]:
            print(f"\nDatos extraídos: {resultado['extracted_data']}")
        print()


if __name__ == "__main__":
    main()
