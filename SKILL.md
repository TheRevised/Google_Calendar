---
name: google-calendar
description: Crea eventos con título, descripción y horario en el calendario principal de Google cuando el usuario pida agendar algo.
---

# Crear eventos en Google Calendar

Ejecuta `{baseDir}/crear_evento.py` con la herramienta de ejecución de OpenClaw.
Usa el Python del entorno virtual de esta carpeta.

- Windows usa `{baseDir}/.venv/Scripts/python.exe`.
- Linux y macOS usan `{baseDir}/.venv/bin/python`.

## Crear un evento

Obtén el título, la fecha y la hora del pedido del usuario. La descripción es
opcional y la duración predeterminada es de 60 minutos. La zona predeterminada
es `America/Tijuana`. Si el usuario indica otra zona, pásala con
`--zona-horaria` usando un nombre IANA.

Llama a `crear` con estos argumentos separados. Adapta el entrecomillado al
intérprete de comandos y trata los textos del usuario como datos al construir
los argumentos.

```text
crear --titulo "Reunión de equipo" --descripcion "Revisar pendientes" --inicio "2026-11-10T09:00:00-08:00" --duracion 45 --zona-horaria "America/Tijuana" --solicitud "identificador-unico-del-pedido"
```

Genera una `--solicitud` única para cada evento nuevo y conserva exactamente ese
valor y los mismos datos si reintentas el pedido. Una repetición puede devolver
`reutilizado: true` junto al evento existente. Una nueva solicitud crea otro
evento incluso si los demás datos coinciden.

El comando devuelve JSON por stdout. Un código de salida 0 y `ok: true`
confirman el éxito. Usa `enlace` para mostrar el evento al usuario. Un código 1
y `ok: false` incluyen el motivo en `error`.

## Autorización inicial

Si falta la sesión o falla su renovación, indica al usuario que ejecute
`crear_evento.py autorizar` con el mismo Python en el equipo del agente,
complete el acceso en el navegador y después repita el pedido. El README
explica la configuración de Google Cloud y las rutas alternativas de
credenciales. La autorización requiere intervención de la persona.

Para detalles de instalación y uso manual, consulta [README.md](README.md).
