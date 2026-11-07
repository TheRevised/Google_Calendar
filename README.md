# Google Calendar para OpenClaw

**Python 3.11+** · **Google Calendar API v3** · **[Licencia MIT](LICENSE)**

Crea eventos en tu calendario principal desde OpenClaw. Incluye una habilidad lista para cargar, comandos sin preguntas interactivas y resultados en JSON. También puedes usarlo manualmente desde la terminal.

**[Instalar](#instalar) · [Google Cloud](#configurar-google-cloud) · [OpenClaw](#usar-con-openclaw) · [Uso manual](#ejemplo-de-uso) · [Archivos](#archivos-del-proyecto)**

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

### Instalar como habilidad de OpenClaw

Clona el repositorio dentro de `skills/google-calendar` en el workspace de tu agente y prepara el entorno virtual en esa carpeta. Puedes consultar el workspace configurado con `openclaw config get agents.defaults.workspace`.

En Windows, para un workspace en la ubicación predeterminada, usa estos comandos en lugar de la instalación anterior.

```powershell
$destino = Join-Path $env:USERPROFILE ".openclaw\workspace\skills\google-calendar"
git clone https://github.com/TheRevised/Google_Calendar.git $destino
Set-Location -LiteralPath $destino
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Para Linux o macOS, clona en `<workspace>/skills/google-calendar`, crea el entorno con `python3 -m venv .venv` e instala con `.venv/bin/python -m pip install -r requirements.txt`.

El archivo `SKILL.md` enseña al agente cómo ejecutar el programa. La instalación de Python y la ejecución deben estar disponibles en el entorno donde trabaje OpenClaw. [Documentación de habilidades](https://docs.openclaw.ai/tools/skills)

## Configurar Google Cloud

1. Crea o selecciona un proyecto en [Google Cloud Console](https://console.cloud.google.com/).
2. Habilita la [API de Google Calendar](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com/) en el proyecto.
3. Completa **Branding** en **Google Auth Platform**. Si usas una cuenta personal y la aplicación está en modo de prueba, selecciona la audiencia **Externa** y agrega tu cuenta a **Usuarios de prueba** en **Audience**.
4. En **Data Access**, agrega el permiso `https://www.googleapis.com/auth/calendar.events.owned`, que permite administrar eventos en calendarios de tu propiedad.
5. En **Clients**, crea un cliente OAuth de tipo **Desktop app**. Descarga el JSON, renómbralo a `credentials.json` y colócalo junto a `crear_evento.py`.

[Guía oficial de Google Calendar API para Python](https://developers.google.com/workspace/calendar/api/quickstart/python)

> [!IMPORTANT]
> Conserva `credentials.json` y `token.json` en tu equipo. Git excluye ambos archivos.

## Usar con OpenClaw

### 1. Autorizar la cuenta

Desde la carpeta del proyecto, ejecuta una vez el siguiente comando en el equipo donde se ejecuta el agente. Completa el acceso en el navegador.

```powershell
.\.venv\Scripts\python.exe crear_evento.py autorizar
```

En Linux o macOS, sustituye el ejecutable de Python por `.venv/bin/python`. La autorización interactiva necesita un navegador y acceso al servidor local de retorno de OAuth. La espera de autorización está limitada a tres minutos.

### 2. Comprobar la habilidad

```powershell
openclaw skills info google-calendar
```

### 3. Pedir el evento

> Agenda una reunión de equipo el 10 de noviembre de 2026 a las 9 de la mañana, hora de Tijuana, durante 45 minutos. En la descripción pon “Revisar pendientes”.

La habilidad utiliza un comando como el siguiente.

```powershell
.\.venv\Scripts\python.exe crear_evento.py crear --titulo "Reunión de equipo" --descripcion "Revisar pendientes" --inicio "2026-11-10T09:00:00-08:00" --duracion 45 --zona-horaria "America/Tijuana" --solicitud "reunion-equipo-20261110-0900"
```

| Parámetro | Uso |
| --- | --- |
| `--titulo` | Título obligatorio del evento. |
| `--descripcion` | Texto opcional. |
| `--inicio` | Fecha y hora ISO 8601. Admite un offset explícito. |
| `--duracion` | Minutos enteros positivos. Predeterminado de 60. |
| `--zona-horaria` | Zona IANA. Predeterminado de `America/Tijuana`. |
| `--solicitud` | ID única del pedido. Usa la misma ID y los mismos datos para reintentar. |

El comando devuelve un objeto JSON con `ok`, `id`, `titulo`, `inicio`, `fin`, `enlace` y `reutilizado`. Los errores devuelven `{"ok": false, "error": "..."}` y código de salida 1. Un resultado correcto devuelve código 0. La creación automática termina con error si falta la sesión.

### Rutas de credenciales

Por defecto, el cliente OAuth y el token se buscan junto al script. Puedes definir `GOOGLE_CALENDAR_CREDENTIALS` y `GOOGLE_CALENDAR_TOKEN` con rutas absolutas, o pasar `--credenciales` y `--token` **antes del subcomando**. Elige ubicaciones privadas si usas estas opciones.

```powershell
.\.venv\Scripts\python.exe crear_evento.py --credenciales "C:\privado\credentials.json" --token "C:\privado\token.json" autorizar
```

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
| [`SKILL.md`](SKILL.md) | Instrucciones que carga OpenClaw para crear eventos. |
| [`tests/test_calendario.py`](tests/test_calendario.py) | Pruebas de la CLI, autorización simulada y reintentos. |
| [`requirements.txt`](requirements.txt) | Lista las dependencias de Python. |
| [`.gitignore`](.gitignore) | Excluye credenciales, sesiones y archivos locales de Python. |
| [`README.md`](README.md) | Reúne los pasos de instalación, configuración y uso. |
| [`LICENSE`](LICENSE) | Contiene la licencia MIT. |

## Verificar el proyecto

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas usan respuestas simuladas de Google Calendar.

## Licencia

El proyecto se distribuye bajo la [licencia MIT](LICENSE).
