import csv
import os
import anyio
from claude_agent_sdk import (
    tool, create_sdk_mcp_server, ClaudeAgentOptions, ClaudeSDKClient,
    AssistantMessage, TextBlock, ToolUseBlock,
)

# ---------- Configuración ----------
ARCHIVO_CSV = "empresas.csv"
COLUMNAS = ["nombre", "rubro", "email", "web", "estado"]
RUBRO = "comercios,callcenters,salones de belleza(manicura),vendedora, NO INMOBILIARIAS,NO ESTUDIOS CONTABLES"   # cambialo por lo que busca ella
ZONA = "La Plata/Berisso/Ensenada, Buenos Aires"
CANTIDAD = 10


def leer_emails_guardados():
    """Devuelve el conjunto de emails que ya están en el CSV."""
    if not os.path.exists(ARCHIVO_CSV):
        return set()
    with open(ARCHIVO_CSV, newline="", encoding="utf-8") as f:
        return {fila["email"].strip().lower() for fila in csv.DictReader(f)}


# ---------- Herramienta propia: guardar una empresa en el CSV ----------
@tool(
    "guardar_empresa",
    "Guarda una empresa en el CSV. Usala una vez por cada empresa con email de contacto verificado.",
    {"nombre": str, "rubro": str, "email": str, "web": str},
)
async def guardar_empresa(args):
    email = args["email"].strip().lower()

    if "@" not in email:
        return {"content": [{"type": "text", "text": f"Email inválido: {email}. No se guardó."}]}
    if email in leer_emails_guardados():
        return {"content": [{"type": "text", "text": f"{email} ya estaba en la lista. No se guardó."}]}

    archivo_nuevo = not os.path.exists(ARCHIVO_CSV)
    with open(ARCHIVO_CSV, "a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        if archivo_nuevo:
            escritor.writeheader()
        escritor.writerow({
            "nombre": args["nombre"],
            "rubro": args["rubro"],
            "email": email,
            "web": args["web"],
            "estado": "pendiente",
        })
    return {"content": [{"type": "text", "text": f"Guardada: {args['nombre']}"}]}


servidor = create_sdk_mcp_server(name="cvs", version="1.0.0", tools=[guardar_empresa])

# ---------- Instrucciones y opciones del agente ----------
INSTRUCCIONES = f"""Buscás empresas y negocios reales de {ZONA} para enviarles un CV.
Reglas:
- Usá WebSearch para encontrarlos y WebFetch para abrir su web y buscar el email de contacto.
- Guardá cada una con la herramienta guardar_empresa.
- Solo guardá emails que aparezcan publicados en la web o redes de la propia empresa.
  Nunca inventes ni deduzcas un email.
- Si no encontrás el email de una empresa, salteala.
- Cuando termines, decí cuántas guardaste."""

opciones = ClaudeAgentOptions(
    system_prompt=INSTRUCCIONES,
    mcp_servers={"cvs": servidor},
    allowed_tools=["WebSearch", "WebFetch", "mcp__cvs__guardar_empresa"],
    disallowed_tools=["Bash", "Write", "Edit"],
    max_turns=40,
    # cli_path="/home/tu-usuario/.local/bin/claude",  # descomentá si antes lo necesitaste
)


# ---------- Programa principal ----------
async def main():
    pedido = f"Encontrá {CANTIDAD} empresas o negocios del rubro '{RUBRO}' en {ZONA} y guardalos."
    async with ClaudeSDKClient(options=opciones) as cliente:
        await cliente.query(pedido)
        async for msg in cliente.receive_response():
            if isinstance(msg, AssistantMessage):
                for bloque in msg.content:
                    if isinstance(bloque, TextBlock):
                        print(bloque.text)
                    elif isinstance(bloque, ToolUseBlock):
                        print(f"  -> usando {bloque.name}")


anyio.run(main)