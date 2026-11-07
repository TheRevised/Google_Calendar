"""Pruebas de integración de la CLI sin crear eventos ni abrir el navegador."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from httplib2 import Http, Response

import crear_evento as app


class CalendarioTests(unittest.TestCase):
    def setUp(self):
        self.argumentos = [
            "crear_evento.py", "crear", "--titulo", "Reunion",
            "--inicio", "2026-11-10T09:00:00-08:00", "--solicitud", "pedido-1",
        ]

    def ejecutar(self, argumentos, respuestas=None):
        salida = io.StringIO()
        http = Http()
        with (
            patch("sys.argv", argumentos),
            patch("builtins.input", side_effect=AssertionError("Entrada interactiva")),
            patch.object(app, "obtener_credenciales") as auth,
            patch.object(http, "request", side_effect=respuestas) as request,
            patch.object(app, "build", side_effect=lambda *a, **k: build(
                "calendar", "v3", http=http
            )),
            contextlib.redirect_stdout(salida),
        ):
            codigo = app.main()
        return codigo, json.loads(salida.getvalue()), request, auth

    def respuesta(self, estado, cuerpo):
        return Response({"status": str(estado)}), json.dumps(cuerpo).encode()

    def evento(self):
        cuerpo = app.construir_evento("Reunion", "", "2026-11-10T09:00:00-08:00")
        cuerpo.update(id="id-prueba", htmlLink="https://calendar.google.com/evento")
        return cuerpo

    def test_crear_por_cli(self):
        codigo, resultado, request, auth = self.ejecutar(
            self.argumentos, [self.respuesta(200, self.evento())]
        )
        self.assertEqual(codigo, 0)
        self.assertTrue(resultado["ok"])
        self.assertFalse(resultado["reutilizado"])
        self.assertIn("/calendars/primary/events", request.call_args.args[0])
        cuerpo = json.loads(request.call_args.kwargs["body"])
        self.assertEqual(len(cuerpo["id"]), 64)
        self.assertEqual(cuerpo["end"]["dateTime"], "2026-11-10T10:00:00-08:00")
        self.assertFalse(auth.call_args.args[0])

    def test_reintento_reutiliza_evento(self):
        respuestas = [
            self.respuesta(409, {"error": {"message": "Already exists"}}),
            self.respuesta(200, self.evento()),
        ]
        codigo, resultado, request, _ = self.ejecutar(self.argumentos, respuestas)
        self.assertEqual(codigo, 0)
        self.assertTrue(resultado["reutilizado"])
        primero, segundo = request.call_args_list
        cuerpo = json.loads(primero.kwargs["body"])
        self.assertIn(cuerpo["id"], segundo.args[0])

    def test_reintento_con_otro_contenido_falla(self):
        existente = self.evento()
        existente["summary"] = "Otro evento"
        codigo, resultado, _, _ = self.ejecutar(self.argumentos, [
            self.respuesta(409, {"error": {"message": "Already exists"}}),
            self.respuesta(200, existente),
        ])
        self.assertEqual(codigo, 1)
        self.assertFalse(resultado["ok"])

    def test_errores_de_argumentos_son_json(self):
        for argumentos in [
            ["crear_evento.py", "crear"],
            self.argumentos + ["--duracion", "0"],
            self.argumentos + ["--zona-horaria", "Zona/Inexistente"],
        ]:
            with self.subTest(argumentos=argumentos):
                codigo, resultado, request, auth = self.ejecutar(argumentos)
                self.assertEqual(codigo, 1)
                self.assertFalse(resultado["ok"])
                request.assert_not_called()
                auth.assert_not_called()

    def test_error_http_es_json(self):
        codigo, resultado, _, _ = self.ejecutar(
            self.argumentos, [self.respuesta(403, {"error": {"message": "Forbidden"}})]
        )
        self.assertEqual(codigo, 1)
        self.assertIn("403", resultado["error"])

    def test_horas_repetidas_y_omitidas(self):
        for inicio in ["2026-11-01T01:30", "2026-03-08T02:30"]:
            with self.assertRaises(ValueError):
                app.construir_evento("Evento", "", inicio)
        evento = app.construir_evento("Evento", "<equipo>", "2026-11-01T01:30:00-07:00")
        self.assertEqual(evento["description"], "&lt;equipo&gt;")
        self.assertEqual(evento["end"]["dateTime"], "2026-11-01T01:30:00-08:00")

    def test_modo_manual_conservado(self):
        with (
            patch("sys.argv", ["crear_evento.py"]),
            patch("builtins.input", side_effect=["Manual", "", "2026-11-10 09:00", ""]),
            patch.object(app, "obtener_credenciales"),
            patch.object(app, "build") as cliente,
            contextlib.redirect_stdout(io.StringIO()) as salida,
        ):
            servicio = cliente.return_value.__enter__.return_value
            servicio.events.return_value.insert.return_value.execute.return_value = self.evento()
            self.assertEqual(app.main(), 0)
        self.assertIn("Evento creado", salida.getvalue())

    def test_sin_sesion_automatica_no_abre_navegador(self):
        with tempfile.TemporaryDirectory() as carpeta:
            with patch.object(app.InstalledAppFlow, "from_client_secrets_file") as flujo:
                with self.assertRaises(ValueError):
                    app.obtener_credenciales(False, Path(carpeta)/"c.json", Path(carpeta)/"t.json")
                flujo.assert_not_called()

    def test_autorizar_recupera_sesion_revocada(self):
        with tempfile.TemporaryDirectory() as carpeta:
            credenciales = Path(carpeta) / "c.json"
            token = Path(carpeta) / "t.json"
            credenciales.write_text("{}")
            token.write_text("{}")
            anterior = Mock(valid=False, refresh_token="prueba")
            anterior.refresh.side_effect = RefreshError("revoked")
            nueva = Mock()
            nueva.to_json.return_value = '{"sesion": "simulada"}'
            with (
                patch.object(app.Credentials, "from_authorized_user_file", return_value=anterior),
                patch.object(app.InstalledAppFlow, "from_client_secrets_file") as flujo,
            ):
                flujo.return_value.run_local_server.return_value = nueva
                self.assertIs(app.obtener_credenciales(True, credenciales, token), nueva)
            self.assertEqual(json.loads(token.read_text()), {"sesion": "simulada"})
            self.assertEqual(sorted(p.name for p in Path(carpeta).iterdir()), ["c.json", "t.json"])


if __name__ == "__main__":
    unittest.main()
