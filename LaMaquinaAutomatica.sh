#!/bin/bash
# Versión automática (sin interacción): redacta y envía CVs.
# La ejecuta el servicio de systemd cada 30 minutos.

cd "$(dirname "$0")"

# Toma las credenciales de Gmail desde ~/.bashrc (sin depender de shell interactiva)
eval "$(grep -E '^export GMAIL_(USUARIO|CLAVE)=' "$HOME/.bashrc")"

source .venv/bin/activate

# Que Python escriba al log al instante (sin buffer), para verlo en vivo con ./maquina.sh ver
export PYTHONUNBUFFERED=1

echo ""
echo "================= $(date '+%Y-%m-%d %H:%M:%S') ================="
echo ">>> Buscando empresas nuevas..."
python agente.py

echo ""
echo ">>> Redactando y aprobando mails pendientes..."
python redactar.py

echo ""
echo ">>> Enviando CVs aprobados..."
python enviar.py

echo ">>> Corrida terminada."
