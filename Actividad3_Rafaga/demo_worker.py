"""Worker DEMO de Actividad 3; no reemplaza el worker de Isma/MAU."""
import argparse
import json
import socket
import threading
import time
from actividad3 import ejecutar_carga_local, validar_orden


def main():
    parser = argparse.ArgumentParser(description="Worker demo de Actividad 3")
    parser.add_argument("node_id")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5002)
    args = parser.parse_args()
    if not args.node_id.strip() or len(args.node_id) > 40:
        parser.error("node_id debe tener de 1 a 40 caracteres")
    with socket.create_connection((args.host, args.port), timeout=8) as sock:
        sock.settimeout(None)
        lock_envio = threading.Lock()
        ocupado = threading.Event()

        def enviar(mensaje):
            paquete = (json.dumps(mensaje, ensure_ascii=False) + "\n").encode("utf-8")
            with lock_envio:
                sock.sendall(paquete)

        def ejecutar(orden):
            try:
                print(f"[{args.node_id}] Tarea {orden['task_id']}: inicio en {max(0, orden['start_at'] - time.time()):.1f}s", flush=True)
                resultado = ejecutar_carga_local(orden, args.node_id)
                enviar(resultado)
                print(f"[{args.node_id}] Resultado: {resultado['ok']}/{resultado['sent']} correctos", flush=True)
            except (ValueError, OSError) as exc:
                try:
                    enviar({"tipo": "STRESS_ERROR", "node_id": args.node_id, "task_id": orden.get("task_id"), "error": str(exc)})
                except OSError:
                    pass
            finally:
                ocupado.clear()

        enviar({"tipo": "HELLO", "node_id": args.node_id})
        print(f"[{args.node_id}] Conectado al Master en {args.host}:{args.port}", flush=True)
        with sock.makefile("r", encoding="utf-8") as lector:
            for linea in lector:
                try:
                    mensaje = json.loads(linea)
                    validar_orden(mensaje)
                except (ValueError, TypeError) as exc:
                    try:
                        enviar({"tipo": "STRESS_ERROR", "node_id": args.node_id, "task_id": None, "error": str(exc)})
                    except OSError:
                        return
                    continue
                if ocupado.is_set():
                    enviar({"tipo": "STRESS_ERROR", "node_id": args.node_id, "task_id": mensaje["task_id"], "error": "Ya hay una tarea activa"})
                    continue
                ocupado.set()
                enviar({"tipo": "STRESS_READY", "node_id": args.node_id, "task_id": mensaje["task_id"]})
                threading.Thread(target=ejecutar, args=(mensaje,), daemon=True).start()
        print(f"[{args.node_id}] Conexión finalizada", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (ConnectionError, OSError) as exc:
        print(f"Error de conexión: {exc}")
