"""Crea un evento en el calendario principal de la cuenta autorizada."""

import sys
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

from google.auth.exceptions import GoogleAuthError, RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauthlib.oauth2 import OAuth2Error

# Las credenciales se buscan junto al script, incluso si se ejecuta desde otra carpeta.
CARPETA = Path(__file__).resolve().parent
CREDENCIALES = CARPETA / "credentials.json"
TOKEN = CARPETA / "token.json"
# OAuth permite gestionar eventos en calendarios de los que la cuenta es dueña.
PERMISOS = ["https://www.googleapis.com/auth/calendar.events.owned"]
ZONA_HORARIA = "America/Tijuana"


def obtener_credenciales():
    """Reutiliza la sesión de Google o abre el navegador para autorizarla."""
    credenciales = None
    if TOKEN.is_file():
        try:
            credenciales = Credentials.from_authorized_user_file(str(TOKEN), PERMISOS)
        except ValueError:
            raise ValueError("Elimina token.json y vuelve a ejecutar el programa.") from None
        if credenciales.valid:
            return credenciales

    # Una sesión vencida se puede renovar sin volver a abrir el navegador.
    if credenciales and credenciales.refresh_token:
        credenciales.refresh(Request())
    else:
        if not CREDENCIALES.is_file():
            raise FileNotFoundError(
                "Falta credentials.json. Sigue la configuración de Google Cloud del README."
            )
        flujo = InstalledAppFlow.from_client_secrets_file(str(CREDENCIALES), PERMISOS)
        # Google devuelve la autorización a un puerto disponible de la computadora.
        credenciales = flujo.run_local_server(port=0)

    # Guarda la sesión nueva o renovada para la siguiente ejecución.
    TOKEN.write_text(credenciales.to_json(), encoding="utf-8")
    return credenciales


def pedir_evento():
    """Recoge y valida los datos antes de iniciar la autorización de Google."""
    titulo = input("Título: ").strip()
    if not titulo:
        raise ValueError("El título es obligatorio.")
    descripcion = input("Descripción (opcional): ").strip()

    zona = ZoneInfo(ZONA_HORARIA)
    entrada = input(f"Inicio en {ZONA_HORARIA} (AAAA-MM-DD HH:MM): ").strip()
    try:
        inicio = datetime.strptime(entrada, "%Y-%m-%d %H:%M").replace(tzinfo=zona)
    except ValueError:
        raise ValueError("Escribe una fecha y hora válidas con el formato indicado.") from None

    # Al cambiar el reloj, algunas horas locales se repiten o se omiten.
    if inicio.utcoffset() != inicio.replace(fold=1).utcoffset():
        raise ValueError(
            "Elige otra hora. La indicada es ambigua o no existe por el cambio de horario."
        )

    entrada = input("Duración en minutos [60]: ").strip()
    try:
        minutos = int(entrada or "60")
        if minutos <= 0:
            raise ValueError
        # Calcula el tiempo transcurrido en UTC y vuelve a la zona del evento.
        fin = (inicio.astimezone(timezone.utc) + timedelta(minutes=minutos)).astimezone(zona)
    except (ValueError, OverflowError):
        raise ValueError("La duración debe ser un número entero positivo válido.") from None

    # Calendar usa summary como título. Escapamos la descripción para tratarla como texto.
    return {
        "summary": titulo,
        "description": escape(descripcion),
        "start": {"dateTime": inicio.isoformat(), "timeZone": ZONA_HORARIA},
        "end": {"dateTime": fin.isoformat(), "timeZone": ZONA_HORARIA},
    }


def main():
    """Envía el evento y muestra el enlace devuelto por Calendar."""
    try:
        evento = pedir_evento()
        credenciales = obtener_credenciales()
        with build("calendar", "v3", credentials=credenciales) as servicio:
            # primary identifica el calendario principal de la cuenta autorizada.
            creado = servicio.events().insert(calendarId="primary", body=evento).execute()
    except (KeyboardInterrupt, EOFError):
        print("\nOperación cancelada.", file=sys.stderr)
        return 1
    except RefreshError:
        print(
            "No se pudo renovar la sesión. Si sigue fallando, elimina token.json y vuelve a autorizar.",
            file=sys.stderr,
        )
        return 1
    except (GoogleAuthError, OAuth2Error):
        print(
            "Falló la autorización. Revisa la configuración de OAuth en Google Cloud.",
            file=sys.stderr,
        )
        return 1
    except HttpError as error:
        print(f"Google Calendar devolvió el error HTTP {error.resp.status}.", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        mensaje = (
            str(error)
            if isinstance(error, FileNotFoundError)
            else "Revisa la conexión o los permisos de la carpeta."
        )
        print(f"Error: {mensaje}", file=sys.stderr)
        return 1

    print(f"Evento creado: {creado['summary']}")
    if creado.get("htmlLink"):
        print(creado["htmlLink"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
