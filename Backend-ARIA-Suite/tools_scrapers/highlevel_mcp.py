import asyncio
import os
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent


async def ejecutar_orden_highlevel(
    pit_token: str,
    location_id: str,
    orden: str,
) -> dict:
    """
    Conecta al MCP de HighLevel con las credenciales del usuario y ejecuta
    una orden en lenguaje natural usando un agente LangGraph + GPT-4o.

    Retorna un dict con:
      - success (bool)
      - respuesta (str): texto final del agente
      - pasos_ejecutados (int): cuántas herramientas usó el agente
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return {
            "success": False,
            "respuesta": "Error de configuración: OPENAI_API_KEY no está definida en el servidor.",
            "pasos_ejecutados": 0,
        }

    try:
        async with MultiServerMCPClient(
            {
                "ghl": {
                    "url": "https://services.leadconnectorhq.com/mcp/",
                    "transport": "streamable_http",
                    "headers": {
                        "Authorization": f"Bearer {pit_token}",
                        "locationId": location_id,
                    },
                }
            }
        ) as client:
            tools = await client.get_tools()

            llm = ChatOpenAI(
                model="gpt-4o",
                api_key=openai_api_key,
            )

            agent = create_react_agent(llm, tools)

            result = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                f"Eres un asistente experto en HighLevel. "
                                f"El locationId del usuario es: {location_id}. "
                                "Responde siempre en español. "
                                "Sé conciso y claro en tus respuestas."
                            ),
                        },
                        {"role": "user", "content": orden},
                    ]
                }
            )

            messages = result.get("messages", [])
            respuesta_final = ""
            pasos = 0

            for msg in messages:
                if hasattr(msg, "type") and msg.type == "tool":
                    pasos += 1
                if hasattr(msg, "type") and msg.type == "ai" and msg.content:
                    respuesta_final = msg.content

            if not respuesta_final:
                respuesta_final = "El agente completó la tarea pero no generó una respuesta en texto."

            return {
                "success": True,
                "respuesta": respuesta_final,
                "pasos_ejecutados": pasos,
            }

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            return {
                "success": False,
                "respuesta": "Token inválido o sin permisos. Verifica tu Private Integration Token (PIT) en HighLevel → Settings → Private Integrations.",
                "pasos_ejecutados": 0,
            }
        if "locationId" in error_msg or "location" in error_msg.lower():
            return {
                "success": False,
                "respuesta": "Location ID inválido. Verifica tu Location ID en HighLevel → Settings → Business Profile.",
                "pasos_ejecutados": 0,
            }
        return {
            "success": False,
            "respuesta": f"Error al ejecutar la orden: {error_msg}",
            "pasos_ejecutados": 0,
        }


def ejecutar_orden_highlevel_sync(pit_token: str, location_id: str, orden: str) -> dict:
    """
    Wrapper síncrono para llamar desde FastAPI usando asyncio.run().
    """
    return asyncio.run(ejecutar_orden_highlevel(pit_token, location_id, orden))
