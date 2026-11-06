# Calendario

Programa de consola en Python para crear un evento en el calendario principal de tu cuenta de Google. Pide el título, una descripción opcional, la fecha y hora de inicio y la duración. Al terminar, muestra el enlace al evento.

## Archivos del proyecto

- `crear_evento.py` valida los datos, autoriza la cuenta con OAuth y envía el evento a Google Calendar.
- `requirements.txt` enumera las dependencias que instala `pip`.
- `.gitignore` mantiene las credenciales, la sesión y los archivos locales de Python fuera de Git.
- `README.md` reúne los pasos para configurar, ejecutar y publicar el proyecto.

## Configurar Google Cloud

1. Abre [Google Cloud Console](https://console.cloud.google.com/) y crea o selecciona un proyecto.
2. Habilita la [API de Google Calendar](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com/) en ese proyecto.
3. En **Google Auth Platform**, configura **Branding**. Si usas una cuenta personal, selecciona audiencia **Externa** y, mientras la aplicación esté en pruebas, agrega en **Audience** la cuenta de Google con la que iniciarás sesión.
4. En **Data Access**, agrega el permiso `https://www.googleapis.com/auth/calendar.events.owned`. Este permiso permite administrar eventos en los calendarios de tu propiedad.
5. En **Clients**, crea un cliente OAuth de tipo **Desktop app**. Descarga el archivo JSON, renómbralo a `credentials.json` y colócalo junto a `crear_evento.py`.

[Guía oficial de Google Calendar API para Python](https://developers.google.com/workspace/calendar/api/quickstart/python)

## Instalar y ejecutar

Usa Python 3.11 o posterior. En PowerShell, desde la carpeta `OpenClaw`, ejecuta los siguientes comandos.

```powershell
cd Calendario
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe crear_evento.py
```

Escribe la fecha y hora como `AAAA-MM-DD HH:MM`. Presiona **Enter** en la duración para usar 60 minutos. El programa usa la zona horaria de Tijuana. Puedes cambiarla en `ZONA_HORARIA` dentro de `crear_evento.py`.

La primera vez se abrirá el navegador para que autorices la cuenta donde quieres crear el evento. El programa guarda la sesión en `token.json`. Si cambias de cuenta o se revoca la sesión, elimina ese archivo y vuelve a ejecutar el programa.

## Subir a GitHub

Crea un repositorio vacío en GitHub y ejecuta estos comandos desde `Calendario`. Sustituye la URL de ejemplo por la del repositorio.

```powershell
git remote add origin https://github.com/TU-USUARIO/Calendario.git
git push -u origin main
```

Conserva `credentials.json` y `token.json` en tu equipo. El archivo `.gitignore` los excluye junto con el entorno de Python.
