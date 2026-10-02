import csv
import os
import sys
import time
import smtplib
from email.message import EmailMessage

# ---------- Rutas ----------
CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_CSV = os.path.join(CARPETA, "empresas.csv")
CARPETA_BORRADORES = os.path.join(CARPETA, "borradores")
COLUMNAS = ["nombre", "rubro", "email", "web", "estado", "cv"]

# ---------- Configuración ----------
MODO_PRUEBA = False                 # True: todo llega a MAIL_PRUEBA y no se marca nada como enviado
MAIL_PRUEBA = "ivanagustinrodriguez2005@gmail.com"  # adonde llegan las pruebas
LIMITE_POR_EJECUCION = 10           # cuántos mails se envían por corrida (para no caer en spam)
PAUSA_SEGUNDOS = 30                 # espera entre un mail y otro

USUARIO = os.environ.get("GMAIL_USUARIO")
CLAVE = os.environ.get("GMAIL_CLAVE")


# ---------- Manejo del CSV ----------
def leer_empresas():
    with open(ARCHIVO_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def guardar_empresas(empresas):
    with open(ARCHIVO_CSV, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        escritor.writeheader()
        escritor.writerows(empresas)


# ---------- Armar el mail ----------
ARCHIVOS_CV = {
    "vendedora": "CV - Malena Villasboa - Empleada Comercial.pdf",
    "cajera": "CV - Malena Villasboa - Cajera.pdf",
}


def ruta_cv(empresa):
    return os.path.join(CARPETA, ARCHIVOS_CV[empresa["cv"]])


def leer_borrador(empresa):
    """Separa la línea 'ASUNTO: ...' del cuerpo del mail."""
    ruta = os.path.join(CARPETA_BORRADORES, empresa["email"] + ".txt")
    with open(ruta, encoding="utf-8") as f:
        lineas = f.read().strip().split("\n")
    asunto = lineas[0].replace("ASUNTO:", "").strip()
    cuerpo = "\n".join(lineas[1:]).strip()
    return asunto, cuerpo


def armar_mail(empresa):
    asunto, cuerpo = leer_borrador(empresa)
    mail = EmailMessage()
    mail["From"] = USUARIO
    if MODO_PRUEBA:
        mail["To"] = MAIL_PRUEBA
        mail["Subject"] = f"[PRUEBA para {empresa['email']}] {asunto}"
    else:
        mail["To"] = empresa["email"]
        mail["Subject"] = asunto
    mail.set_content(cuerpo)

    with open(ruta_cv(empresa), "rb") as f:   # "rb": leer el PDF como bytes
        mail.add_attachment(f.read(), maintype="application", subtype="pdf",
                            filename=ARCHIVOS_CV[empresa["cv"]])
    return mail


# ---------- Programa principal ----------
def main():
    if not USUARIO or not CLAVE:
        sys.exit("Faltan GMAIL_USUARIO o GMAIL_CLAVE. Revisá tu ~/.bashrc.")

    empresas = leer_empresas()
    aprobadas = [e for e in empresas if e["estado"] == "aprobado"][:LIMITE_POR_EJECUCION]

    if not aprobadas:
        print("No hay mails aprobados para enviar.")
        return

    # Chequear que todo exista ANTES de empezar a enviar
    for empresa in aprobadas:
        if not os.path.exists(ruta_cv(empresa)):
            sys.exit(f"No encuentro {ruta_cv(empresa)} (empresa: {empresa['nombre']}).")

    print("MODO PRUEBA: todo va a llegar a " + MAIL_PRUEBA if MODO_PRUEBA else "MODO REAL")
    print(f"Se van a enviar {len(aprobadas)} mails:")
    for empresa in aprobadas:
        print(f"  - {empresa['nombre']} ({empresa['email']}) con CV de {empresa['cv']}")

    # Envío automático: sin confirmación por terminal.
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(USUARIO, CLAVE)

        for i, empresa in enumerate(aprobadas):
            try:
                servidor.send_message(armar_mail(empresa))
            except Exception as error:
                print(f"ERROR con {empresa['nombre']}: {error}")
                continue

            print(f"Enviado: {empresa['nombre']}")
            if not MODO_PRUEBA:
                empresa["estado"] = "enviado"
                guardar_empresas(empresas)

            if i < len(aprobadas) - 1:
                time.sleep(PAUSA_SEGUNDOS)

    print("Listo.")


main()