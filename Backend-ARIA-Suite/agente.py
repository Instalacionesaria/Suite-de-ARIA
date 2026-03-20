"""
Agente IA de Onboarding - ARIA Suite
Recopila información del negocio del usuario para autocompletar los scrapers.

Autor: Ing. Kevin Inofuente Colque - DataPath
"""

from dotenv import load_dotenv
load_dotenv()

import json
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ============================================
# 1. CONFIGURACIÓN DEL MODELO
# ============================================
chat = init_chat_model(
    "gpt-4.1",
    temperature=0.7,
)

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

CÓMO COMPORTARTE:
- Sé amigable, conversacional y breve (no más de 3-4 oraciones por mensaje)
- Haz UNA pregunta a la vez, no bombardees con muchas preguntas
- Empieza preguntando sobre su negocio de forma natural
- Cuando tengas toda la información, haz un resumen confirmando los datos

CUANDO TENGAS TODA LA INFORMACIÓN (tipo de negocio + localización como mínimo):
Al final de tu mensaje, agrega un bloque JSON en este formato exacto:
```json
{{"tipo_negocio": "...", "localizacion": "Distrito, Ciudad, País", "productos": "...", "cliente_ideal": "..."}}
```
Solo incluye el bloque JSON cuando tengas al menos tipo_negocio y localizacion completa (con 3 niveles).
No incluyas el JSON si aún falta información.

Responde siempre en español."""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("history"),
    ("human", "{input}")
])

# ============================================
# 3. CREAR LA CHAIN
# ============================================
chain = prompt | chat

# ============================================
# 4. FUNCIÓN CON HISTORIAL
# ============================================
def chat_con_agente(mensaje_usuario: str, historial: list = None) -> dict:
    """
    Envía un mensaje al agente con historial de conversación.
    Retorna el texto de respuesta y los datos extraídos (si los hay).
    """
    history = []
    if historial:
        for msg in historial:
            if msg["role"] == "user":
                history.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                history.append(("ai", msg["content"]))

    respuesta = chain.invoke({"input": mensaje_usuario, "history": history})
    texto = respuesta.content

    # Extraer JSON si existe
    datos_extraidos = None
    if "```json" in texto:
        try:
            json_str = texto.split("```json")[1].split("```")[0].strip()
            datos_extraidos = json.loads(json_str)
            # Limpiar el JSON del texto visible
            texto = texto.split("```json")[0].strip()
        except (json.JSONDecodeError, IndexError):
            pass

    return {"response": texto, "extracted_data": datos_extraidos}


# ============================================
# 5. LOOP DE CONVERSACIÓN (para testing local)
# ============================================
def main():
    print("=" * 50)
    print("🤖 ARIA Suite - Agente de Onboarding")
    print("=" * 50)
    print("Escribe 'salir' para terminar.\n")

    historial = []
    while True:
        usuario = input("Tú: ").strip()

        if usuario.lower() in ['salir', 'exit', 'quit']:
            print("\n¡Hasta luego! 👋")
            break

        if not usuario:
            continue

        resultado = chat_con_agente(usuario, historial)
        historial.append({"role": "user", "content": usuario})
        historial.append({"role": "assistant", "content": resultado["response"]})

        print(f"\n🤖 ARIA: {resultado['response']}")
        if resultado["extracted_data"]:
            print(f"\n📋 Datos extraídos: {resultado['extracted_data']}")
        print()


if __name__ == "__main__":
    main()
