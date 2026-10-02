#!/bin/bash
# Control de la máquina automática de envío de CVs.
# Uso: ./maquina.sh {activar|desactivar|estado|ver|ahora}

case "$1" in
  activar)
    systemctl --user daemon-reload
    systemctl --user enable --now agente-cvs.timer
    loginctl enable-linger "$USER" 2>/dev/null \
      || echo "(Aviso: para que arranque sin iniciar sesión, corré: sudo loginctl enable-linger $USER)"
    echo "ACTIVADO. Se va a ejecutar cada 30 minutos y al prender la PC."
    ;;
  desactivar)
    systemctl --user disable --now agente-cvs.timer
    echo "DESACTIVADO. No se enviará ningún CV automáticamente hasta que lo vuelvas a activar."
    ;;
  estado)
    systemctl --user list-timers agente-cvs.timer --all
    echo "----------------------------------------"
    systemctl --user status agente-cvs.timer --no-pager
    ;;
  ver)
    echo "Mostrando el proceso de envíos (Ctrl+C para salir)..."
    touch /home/ivanrod/agente-cvs/envios.log
    tail -n 50 -f /home/ivanrod/agente-cvs/envios.log
    ;;
  ahora)
    echo "Ejecutando una corrida ahora mismo..."
    systemctl --user start agente-cvs.service
    echo "Listo. Mirá el resultado con: ./maquina.sh ver"
    ;;
  *)
    echo "Uso: ./maquina.sh {activar|desactivar|estado|ver|ahora}"
    echo "  activar     -> prende el servicio (cada 30 min + al encender la PC)"
    echo "  desactivar  -> apaga el servicio"
    echo "  estado      -> muestra si está activo y cuándo corre la próxima vez"
    echo "  ver         -> mira en vivo el proceso de envíos"
    echo "  ahora       -> fuerza una corrida inmediata"
    ;;
esac
