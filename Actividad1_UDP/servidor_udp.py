"""Actividad 1: servidor UDP para registrar y supervisar workers."""

import json
import socket
import time

HOST = "0.0.0.0"
PUERTO = 5001
TIEMPO_DESCONEXION = 6  # Segundos sin heartbeat para dar de baja un worker


def iniciar_servidor():
    # Guarda la direccion de cada worker y la hora de su ultimo heartbeat.
    workers = {}

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as servidor:
        servidor.bind((HOST, PUERTO))
        servidor.settimeout(0.2)  # Permite comprobar desconexiones aun sin mensajes

        print(f"[SERVIDOR] UDP escuchando en {HOST}:{PUERTO}", flush=True)

        try:
            while True:
                try:
                    datos, direccion = servidor.recvfrom(4096)
                    mensaje = json.loads(datos.decode("utf-8"))

                    if not isinstance(mensaje, dict) or mensaje.get("tipo") != "heartbeat":
                        print("[AVISO] Mensaje no reconocido", flush=True)
                        continue

                    worker_id = mensaje.get("worker_id")
                    if not isinstance(worker_id, str) or not worker_id.strip():
                        print("[AVISO] Worker sin identificador valido", flush=True)
                        continue

                    es_nuevo = worker_id not in workers
                    workers[worker_id] = {
                        "ip": direccion[0],
                        "puerto": direccion[1],
                        "ultimo_heartbeat": time.monotonic(),
                    }

                    if es_nuevo:
                        print(f"[REGISTRO] {worker_id} desde {direccion[0]}:{direccion[1]}", flush=True)
                    print(f"[HEARTBEAT] Recibido de {worker_id}", flush=True)

                    # UDP no confirma la entrega por si mismo: enviamos nuestro ACK.
                    ack = {"tipo": "ack", "worker_id": worker_id}
                    servidor.sendto(json.dumps(ack).encode("utf-8"), direccion)
                    print(f"[ACK] Enviado a {worker_id}", flush=True)

                except socket.timeout:
                    pass  # No hay datos, pero hay que revisar el estado de los workers.
                except (UnicodeDecodeError, json.JSONDecodeError):
                    print("[ERROR] Mensaje JSON no valido", flush=True)

                # Se ejecuta incluso cuando ningun worker envia mensajes.
                ahora = time.monotonic()
                for worker_id, info in list(workers.items()):
                    if ahora - info["ultimo_heartbeat"] >= TIEMPO_DESCONEXION:
                        print(f"[DESCONECTADO] {worker_id} (6 s sin heartbeat)", flush=True)
                        del workers[worker_id]

        except KeyboardInterrupt:
            print("\n[SERVIDOR] Detenido")


if __name__ == "__main__":
    iniciar_servidor()
