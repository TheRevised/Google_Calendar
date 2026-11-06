# Google Calendar desde Python

**Python 3.11+** · **Google Calendar API v3** · **[Licencia MIT](LICENSE)**

Crea eventos en tu calendario principal desde la terminal. Escribe el título, una descripción opcional, la fecha y hora de inicio y la duración. El programa te devuelve un enlace para abrir el evento en Google Calendar.

**[Instalar](#instalar) · [Google Cloud](#configurar-google-cloud) · [Ejemplo de uso](#ejemplo-de-uso) · [Archivos](#archivos-del-proyecto)**

---

## Instalar

Necesitas Python 3.11 o posterior y una cuenta de Google. En PowerShell, clona el proyecto y prepara el entorno.

```powershell
git clone https://github.com/TheRevised/Google_Calendar.git
cd Google_Calendar
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si ya tienes el proyecto en tu equipo, ejecuta los dos últimos comandos desde su carpeta.

## Configurar Google Cloud

1. Crea o selecciona un proyecto en [Google Cloud Console](https://console.cloud.google.com/).
2. Habilita la [API de Google Calendar](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com/) en el proyecto.
3. Completa **Branding** en **Google Auth Platform**. Si usas una cuenta personal y la aplicación está en modo de prueba, selecciona la audiencia **Externa** y agrega tu cuenta a **Usuarios de prueba** en **Audience**.
4. En **Data Access**, agrega el permiso `https://www.googleapis.com/auth/calendar.events.owned`, que permite administrar eventos en calendarios de tu propiedad.
5. En **Clients**, crea un cliente OAuth de tipo **Desktop app**. Descarga el JSON, renómbralo a `credentials.json` y colócalo junto a `crear_evento.py`.

[Guía oficial de Google Calendar API para Python](https://developers.google.com/workspace/calendar/api/quickstart/python)

> [!IMPORTANT]
> Conserva `credentials.json` y `token.json` en tu equipo. Git excluye ambos archivos.

## Ejemplo de uso

```powershell
.\.venv\Scripts\python.exe crear_evento.py
```

```text
Título: Reunión de equipo
Descripción (opcional): Revisar las tareas de la semana
Inicio en America/Tijuana (AAAA-MM-DD HH:MM): 2026-11-10 09:00
Duración en minutos [60]: 45
Evento creado: Reunión de equipo
```

El enlace al evento aparece debajo de la confirmación. Pulsa **Enter** en la duración para usar 60 minutos. Para cambiar la zona horaria, edita `ZONA_HORARIA` en [crear_evento.py](crear_evento.py).

La primera vez se abrirá el navegador para que autorices tu cuenta. Si quieres usar otra cuenta o necesitas volver a autorizar el programa, elimina `token.json` y ejecútalo de nuevo.

## Archivos del proyecto

| Archivo | Función |
| --- | --- |
| [`crear_evento.py`](crear_evento.py) | Valida los datos, autoriza la cuenta y envía el evento. |
| [`requirements.txt`](requirements.txt) | Lista las dependencias de Python. |
| [`.gitignore`](.gitignore) | Excluye credenciales, sesiones y archivos locales de Python. |
| [`README.md`](README.md) | Reúne los pasos de instalación, configuración y uso. |
| [`LICENSE`](LICENSE) | Contiene la licencia MIT. |

## Licencia

El proyecto se distribuye bajo la [licencia MIT](LICENSE).
