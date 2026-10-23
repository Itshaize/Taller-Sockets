import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from actividad3 import crear_orden, validar_orden, verificar_objetivo, resumir_reportes


class Actividad3Tests(unittest.TestCase):
    def test_orden_valida(self):
        orden = crear_orden("t1", 5, 1800000000.0)
        self.assertEqual(validar_orden(orden), orden)
        self.assertEqual(orden["rps_limit"], 12)

    def test_duracion_limite(self):
        for duracion in [-1, 0, 11, True, 5.2]:
            with self.subTest(duracion=duracion):
                with self.assertRaises(ValueError):
                    crear_orden("t1", duracion, 1800000000.0)

    def test_denegar_objetivo_externo(self):
        for ip in ["8.8.8.8", "192.168.1.2", "127.0.0.2", "example.org", "::1"]:
            with self.subTest(ip=ip):
                with self.assertRaises(ValueError):
                    verificar_objetivo(ip)
        self.assertEqual(verificar_objetivo("localhost"), "127.0.0.1")

    def test_resumen(self):
        registros = [
            {"sent": 10, "ok": 10, "avg_latency_ms": 2, "started_at": 100.0},
            {"sent": 10, "ok": 5, "avg_latency_ms": 4, "started_at": 100.02},
        ]
        resumen = resumir_reportes(registros)
        self.assertEqual(resumen["peticiones_correctas"], 15)
        self.assertEqual(resumen["peticiones_fallidas"], 5)
        self.assertEqual(resumen["tasa_exito_pct"], 75)
        self.assertEqual(resumen["latencia_media_ponderada_ms"], 2.667)
        self.assertEqual(resumen["diferencia_inicio_ms"], 20.0)


if __name__ == "__main__":
    unittest.main()
