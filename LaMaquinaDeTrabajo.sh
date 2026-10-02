#!/bin/bash
# La máquina de conseguir trabajo
# Busca empresas -> redacta mails -> envía CVs

set -e                      # si un paso falla, corta todo
cd "$(dirname "$0")"        # se ubica en la carpeta del proyecto
source .venv/bin/activate   # activa el entorno virtual

echo "=============================================="
echo "   LA MÁQUINA DE CONSEGUIR TRABAJO"
echo "=============================================="

echo ""
echo ">>> Paso 1/3: buscando empresas..."
python agente.py

echo ""
echo ">>> Paso 2/3: redactando mails..."
python redactar.py

echo ""
echo ">>> Paso 3/3: enviando CVs..."
python enviar.py

echo ""
echo "¡Listo! Mucha suerte, Malena."