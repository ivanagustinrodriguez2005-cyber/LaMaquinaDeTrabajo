import csv
import os
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

# ---------- Rutas (todo queda en la carpeta del script) ----------
CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_CSV = os.path.join(CARPETA, "empresas.csv")
ARCHIVO_PERFIL = os.path.join(CARPETA, "perfil.txt")
CARPETA_BORRADORES = os.path.join(CARPETA, "borradores")
COLUMNAS = ["nombre", "rubro", "email", "web", "estado", "cv"]
CVS = ["vendedora", "cajera"]   # tienen que existir cv_vendedora.pdf y cv_cajera.pdf
LIMITE_POR_EJECUCION = 10       # cuántas empresas se redactan/aprueban por corrida


# ---------- Manejo del CSV ----------
def leer_empresas():
    with open(ARCHIVO_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def guardar_empresas(empresas):
    # "w" reescribe el archivo completo con los estados actualizados
    with open(ARCHIVO_CSV, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        escritor.writeheader()
        escritor.writerows(empresas)


def ruta_borrador(empresa):
    return os.path.join(CARPETA_BORRADORES, empresa["email"] + ".txt")


# ---------- Pedirle a Claude el borrador y el CV a usar ----------
async def redactar(empresa, perfil):
    instrucciones = f"""Redactás mails breves en español rioplatense para postularse a trabajar en una empresa.

Datos de la persona que se postula:
{perfil}

Tiene dos versiones de CV:
- vendedora: para comercios donde el trabajo es atender y vender (ropa, calzado, librerías, etc.)
- cajera: para supermercados, autoservicios, farmacias y lugares donde el puesto típico es la caja

Reglas:
- Si la empresa tiene web, abrila con WebFetch para mencionar algo concreto de ella.
- Elegí el CV que mejor encaje y orientá el mail a ese puesto.
- Máximo 120 palabras, tono cordial y profesional, sin exagerar.
- Aclará que el CV va adjunto.
- No inventes datos de la persona que no estén arriba.
- Respondé SOLO con esto, en este formato exacto:
CV: <vendedora o cajera>
ASUNTO: <asunto>
<cuerpo del mail>"""

    opciones = ClaudeAgentOptions(
        system_prompt=instrucciones,
        allowed_tools=["WebFetch"],
        disallowed_tools=["Bash", "Write", "Edit"],
        max_turns=6,
        # cli_path="/home/tu-usuario/.local/bin/claude",
    )
    pedido = f"Empresa: {empresa['nombre']}\nRubro: {empresa['rubro']}\nWeb: {empresa['web']}"

    textos = []
    async for msg in query(prompt=pedido, options=opciones):
        if isinstance(msg, AssistantMessage):
            for bloque in msg.content:
                if isinstance(bloque, TextBlock):
                    textos.append(bloque.text)

    completo = "\n".join(textos)

    # Separar la línea "CV: ..." del resto del mail
    cv = CVS[0]
    inicio_cv = completo.rfind("CV:")
    if inicio_cv != -1:
        primera_linea = completo[inicio_cv:].split("\n")[0]
        eleccion = primera_linea.replace("CV:", "").strip().lower()
        if eleccion in CVS:
            cv = eleccion

    inicio_mail = completo.rfind("ASUNTO:")
    mail = completo[inicio_mail:].strip() if inicio_mail != -1 else completo.strip()
    return cv, mail


# ---------- Programa principal ----------
async def main():
    with open(ARCHIVO_PERFIL, encoding="utf-8") as f:
        perfil = f.read()
    os.makedirs(CARPETA_BORRADORES, exist_ok=True)

    empresas = leer_empresas()
    pendientes = [e for e in empresas if e["estado"] == "pendiente"][:LIMITE_POR_EJECUCION]
    print(f"Se van a redactar {len(pendientes)} empresas en esta corrida.\n")

    for empresa in pendientes:
        print(f"=== {empresa['nombre']} ({empresa['email']}) ===")
        print("Redactando...")
        cv, borrador = await redactar(empresa, perfil)

        # Aprobación automática: se guarda el borrador con el CV sugerido por Claude.
        with open(ruta_borrador(empresa), "w", encoding="utf-8") as f:
            f.write(borrador)
        empresa["cv"] = cv
        empresa["estado"] = "aprobado"

        guardar_empresas(empresas)   # guarda después de cada empresa
        print(f"Aprobado automáticamente con CV de {cv}.\n")

    print("Listo. Los mails aprobados están en la carpeta 'borradores'.")


anyio.run(main)