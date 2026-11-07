"""Crea un evento en el calendario principal de la cuenta autorizada."""

import argparse
import hashlib
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from google.auth.exceptions import GoogleAuthError, RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from httplib2 import HttpLib2Error
from oauthlib.oauth2 import OAuth2Error

# Las credenciales se buscan junto al script, incluso si se ejecuta desde otra carpeta.
CARPETA = Path(__file__).resolve().parent
CREDENCIALES = CARPETA / "credentials.json"
TOKEN = CARPETA / "token.json"
# OAuth permite gestionar eventos en calendarios de los que la cuenta es dueña.
PERMISOS = ["https://www.googleapis.com/auth/calendar.events.owned"]
ZONA_HORARIA = "America/Tijuana"


def obtener_credenciales(autorizar=True, ruta_credenciales=CREDENCIALES, ruta_token=TOKEN):
    """Reutiliza la sesión de Google o abre el navegador para autorizarla."""
    credenciales = None
    if ruta_token.is_file():
        try:
            credenciales = Credentials.from_authorized_user_file(str(ruta_token), PERMISOS)
        except ValueError:
            raise ValueError("Elimina token.json y vuelve a ejecutar el programa.") from None
        if credenciales.valid:
            return credenciales

    # Una sesión vencida se puede renovar sin volver a abrir el navegador.
    if credenciales and credenciales.refresh_token:
        try:
            credenciales.refresh(Request())
        except RefreshError:
            if not autorizar:
                raise
            credenciales = None
    if not credenciales or not credenciales.valid:
        # Las ejecuciones del agente deben terminar sin pedir intervención.
        if not autorizar:
            raise ValueError("Falta una sesión válida. Ejecuta el comando autorizar primero.")
        if not ruta_credenciales.is_file():
            raise FileNotFoundError(
                "Falta credentials.json. Sigue la configuración de Google Cloud del README."
            )
        flujo = InstalledAppFlow.from_client_secrets_file(str(ruta_credenciales), PERMISOS)
        # Google devuelve la autorización a un puerto disponible de la computadora.
        credenciales = flujo.run_local_server(port=0, timeout_seconds=180)

    # Guarda la sesión nueva o renovada para la siguiente ejecución.
    # Reemplazar un archivo completo evita dejar JSON parcial ante una interrupción.
    ruta_token.parent.mkdir(parents=True, exist_ok=True)
    temporal = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=ruta_token.parent,
        prefix=".token-", suffix=".json.tmp", delete=False
    )
    ruta_temporal = Path(temporal.name)
    try:
        with temporal:
            temporal.write(credenciales.to_json())
        ruta_temporal.replace(ruta_token)
    finally:
        ruta_temporal.unlink(missing_ok=True)
    return credenciales


def pedir_evento():
    """Recoge y valida los datos antes de iniciar la autorización de Google."""
    titulo = input("Título: ").strip()
    if not titulo:
        raise ValueError("El título es obligatorio.")
    descripcion = input("Descripción (opcional): ").strip()

    entrada = input(f"Inicio en {ZONA_HORARIA} (AAAA-MM-DD HH:MM): ").strip()
    duracion = input("Duración en minutos [60]: ").strip() or "60"
    return construir_evento(titulo, descripcion, entrada, duracion)


def construir_evento(titulo, descripcion, entrada, duracion=60, zona_horaria=ZONA_HORARIA):
    """Comparte las validaciones entre la terminal y las llamadas de OpenClaw."""
    if not titulo.strip():
        raise ValueError("El título es obligatorio.")
    zona = ZoneInfo(zona_horaria)
    try:
        if "T" not in entrada and " " not in entrada:
            raise ValueError
        inicio = datetime.fromisoformat(entrada)
    except ValueError:
        raise ValueError("Escribe una fecha y hora válidas con el formato indicado.") from None

    # Una fecha con offset resuelve explícitamente las horas repetidas.
    if inicio.tzinfo:
        inicio = inicio.astimezone(zona)
    else:
        inicio = inicio.replace(tzinfo=zona)
        if inicio.utcoffset() != inicio.replace(fold=1).utcoffset():
            raise ValueError(
                "Elige otra hora o incluye un offset. La hora es ambigua o no existe."
            )

    try:
        minutos = int(duracion)
        if minutos <= 0:
            raise ValueError
        # Calcula el tiempo transcurrido en UTC y vuelve a la zona del evento.
        fin = (inicio.astimezone(timezone.utc) + timedelta(minutes=minutos)).astimezone(zona)
    except (ValueError, OverflowError):
        raise ValueError("La duración debe ser un número entero positivo válido.") from None

    # Calendar usa summary como título. Escapamos la descripción para tratarla como texto.
    return {
        "summary": titulo.strip(),
        "description": escape(descripcion),
        "start": {"dateTime": inicio.isoformat(), "timeZone": zona_horaria},
        "end": {"dateTime": fin.isoformat(), "timeZone": zona_horaria},
    }


class Argumentos(argparse.ArgumentParser):
    """Convierte errores de argumentos en la misma salida JSON que usa el agente."""

    def error(self, message):
        raise ValueError(message)


def leer_argumentos():
    """Define comandos que pueden ejecutarse sin entrada interactiva."""
    parser = Argumentos(description=__doc__)
    parser.add_argument("--credenciales", type=Path, default=Path(
        os.environ.get("GOOGLE_CALENDAR_CREDENTIALS", str(CREDENCIALES))
    ))
    parser.add_argument("--token", type=Path, default=Path(
        os.environ.get("GOOGLE_CALENDAR_TOKEN", str(TOKEN))
    ))
    comandos = parser.add_subparsers(dest="comando")
    comandos.add_parser("autorizar", help="Autoriza la cuenta en el navegador.")
    crear = comandos.add_parser("crear", help="Crea un evento y devuelve JSON.")
    crear.add_argument("--titulo", required=True)
    crear.add_argument("--descripcion", default="")
    crear.add_argument("--inicio", required=True, help="Fecha ISO 8601 con hora.")
    crear.add_argument("--duracion", type=int, default=60)
    crear.add_argument("--zona-horaria", default=ZONA_HORARIA)
    crear.add_argument("--solicitud", required=True, help="Identificador único de esta petición.")
    return parser.parse_args()


def insertar_evento(servicio, evento, solicitud=None):
    """Reutiliza la misma ID en reintentos para evitar duplicar eventos."""
    if solicitud is not None:
        if not solicitud.strip():
            raise ValueError("El identificador de solicitud es obligatorio.")
        evento["id"] = hashlib.sha256(solicitud.encode("utf-8")).hexdigest()
    try:
        creado = servicio.events().insert(calendarId="primary", body=evento).execute()
        return creado, False
    except HttpError as error:
        if error.resp.status != 409 or solicitud is None:
            raise
        existente = servicio.events().get(
            calendarId="primary", eventId=evento["id"]
        ).execute()
        # Una misma solicitud representa siempre el mismo contenido.
        coincide = (
            existente.get("status") != "cancelled"
            and existente.get("summary") == evento["summary"]
            and existente.get("description", "") == evento["description"]
        )
        for campo in ("start", "end"):
            valor = existente.get(campo, {}).get("dateTime")
            coincide = coincide and valor is not None
            if valor is not None:
                coincide = coincide and (
                    datetime.fromisoformat(valor)
                    == datetime.fromisoformat(evento[campo]["dateTime"])
                )
        if not coincide:
            raise ValueError(
                "La solicitud ya existe con otros datos. Usa otra solicitud para un evento nuevo."
            ) from None
        return existente, True


def main():
    """Envía el evento y muestra el enlace devuelto por Calendar."""
    automatico = len(sys.argv) > 1
    try:
        args = leer_argumentos()
        if args.comando == "autorizar":
            # El navegador imprime instrucciones. Se reservan stdout para el JSON.
            with redirect_stdout(sys.stderr):
                obtener_credenciales(True, args.credenciales, args.token)
            print(json.dumps({"ok": True, "autorizado": True}))
            return 0
        if automatico and args.comando != "crear":
            raise ValueError("Indica el comando crear o autorizar.")
        if automatico:
            evento = construir_evento(
                args.titulo, args.descripcion, args.inicio, args.duracion, args.zona_horaria
            )
        else:
            evento = pedir_evento()
        credenciales = obtener_credenciales(
            not automatico, args.credenciales, args.token
        )
        with build("calendar", "v3", credentials=credenciales) as servicio:
            # primary identifica el calendario principal de la cuenta autorizada.
            creado, reutilizado = insertar_evento(
                servicio, evento, args.solicitud if automatico else None
            )
    except (KeyboardInterrupt, EOFError):
        mensaje = "Operación cancelada."
    except RefreshError:
        mensaje = "No se pudo renovar la sesión. Ejecuta autorizar para revisar el acceso."
    except (GoogleAuthError, OAuth2Error):
        mensaje = "Falló la autorización. Revisa la configuración de OAuth en Google Cloud."
    except HttpError as error:
        mensaje = f"Google Calendar devolvió el error HTTP {error.resp.status}."
    except ZoneInfoNotFoundError:
        mensaje = "Zona horaria desconocida. Instala las dependencias y usa un nombre IANA."
    except ValueError as error:
        mensaje = str(error)
    except (OSError, HttpLib2Error) as error:
        mensaje = (
            str(error)
            if isinstance(error, FileNotFoundError)
            else "Revisa la conexión o los permisos de la carpeta."
        )
    else:
        if automatico:
            print(json.dumps({
                "ok": True,
                "id": creado["id"],
                "titulo": creado["summary"],
                "inicio": creado["start"],
                "fin": creado["end"],
                "enlace": creado.get("htmlLink"),
                "reutilizado": reutilizado,
            }, ensure_ascii=True))
            return 0
        print(f"Evento creado: {creado['summary']}")
        if creado.get("htmlLink"):
            print(creado["htmlLink"])
        return 0

    if automatico:
        print(json.dumps({"ok": False, "error": mensaje}, ensure_ascii=True))
    else:
        print(f"Error: {mensaje}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
