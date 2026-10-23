"""Actividad 1: worker UDP que envia heartbeats cada 2 segundos."""

import json
import socket
import sys
import time

PUERTO = 5001
INTERVALO_HEARTBEAT = 2  # Segundos


def iniciar_worker(worker_id, ip_servidor):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as worker:
        worker.settimeout(1)  # Tiempo maximo de espera por el ACK
        print(f"[WORKER] {worker_id} -> {ip_servidor}:{PUERTO}")

        try:
            while True:
                inicio = time.monotonic()
                mensaje = {"tipo": "heartbeat", "worker_id": worker_id}
                worker.sendto(json.dumps(mensaje).encode("utf-8"), (ip_servidor, PUERTO))
                print("[HEARTBEAT] Enviado", flush=True)

                try:
                    datos, direccion = worker.recvfrom(4096)
                    respuesta = json.loads(datos.decode("utf-8"))

                    if (
                        direccion[0] == socket.gethostbyname(ip_servidor)
                        and direccion[1] == PUERTO
                        and isinstance(respuesta, dict)
                        and respuesta.get("tipo") == "ack"
                        and respuesta.get("worker_id") == worker_id
                    ):
                        print("[ACK] Confirmacion recibida", flush=True)
                    else:
                        print("[AVISO] Respuesta inesperada", flush=True)

                except socket.timeout:
                    print("[AVISO] No se recibio ACK", flush=True)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    print("[ERROR] Respuesta JSON no valida", flush=True)

                # El tiempo usado esperando ACK cuenta dentro de los 2 segundos.
                time.sleep(max(0, INTERVALO_HEARTBEAT - (time.monotonic() - inicio)))

        except KeyboardInterrupt:
            print("\n[WORKER] Detenido")


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Uso: python3 worker_udp.py worker_01 [IP_SERVIDOR]")
        sys.exit(1)

    identificador = sys.argv[1]
    if not identificador.strip():
        print("El identificador del worker no puede estar vacio")
        sys.exit(1)

    servidor = sys.argv[2] if len(sys.argv) == 3 else "127.0.0.1"
    iniciar_worker(identificador, servidor)
