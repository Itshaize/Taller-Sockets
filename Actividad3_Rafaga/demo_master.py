"""Master DEMO: broadcast y recolección; no reemplaza módulos de compañeros."""
import argparse
import json
import socket
import threading
import time
import uuid
from actividad3 import crear_orden, resumir_reportes

HOST = "127.0.0.1"
PORT = 5002


class MasterDemo:
    def __init__(self):
        self.lock = threading.RLock()
        self.workers = {}
        self.tareas = {}
        self.servidor = None

    def aceptar(self, conexion, origen):
        node_id = None
        try:
            with conexion, conexion.makefile("r", encoding="utf-8") as lector:
                linea = lector.readline(8192)
                saludo = json.loads(linea)
                if saludo.get("tipo") != "HELLO" or not isinstance(saludo.get("node_id"), str):
                    return
                node_id = saludo["node_id"]
                if not 1 <= len(node_id) <= 40:
                    return
                with self.lock:
                    if node_id in self.workers:
                        print(f"[MASTER] ID repetido: {node_id}", flush=True)
                        return
                    self.workers[node_id] = (conexion, threading.Lock())
                print(f"[MASTER] Conectado: {node_id} desde {origen}", flush=True)
                for linea in lector:
                    try:
                        respuesta = json.loads(linea)
                    except ValueError:
                        continue
                    if not isinstance(respuesta, dict):
                        continue
                    tarea_id = respuesta.get("task_id")
                    with self.lock:
                        tarea = self.tareas.get(tarea_id)
                        if tarea is None or node_id not in tarea["esperados"]:
                            continue
                        if respuesta.get("tipo") == "STRESS_READY":
                            tarea["listos"].add(node_id)
                            print(f"[MASTER] {node_id}: LISTO para {tarea_id}", flush=True)
                        elif respuesta.get("tipo") == "STRESS_RESULT":
                            if node_id in tarea["resultados"]:
                                continue
                            tarea["resultados"][node_id] = respuesta
                            print(f"[MASTER] {node_id}: {respuesta['ok']}/{respuesta['sent']} OK | latencia media {respuesta['avg_latency_ms']} ms", flush=True)
                            if len(tarea["resultados"]) == len(tarea["esperados"]):
                                self.imprimir_resumen(tarea_id)
                        elif respuesta.get("tipo") == "STRESS_ERROR":
                            tarea["errores"][node_id] = respuesta.get("error", "desconocido")
                            print(f"[MASTER] Error {node_id}: {tarea['errores'][node_id]}", flush=True)
        except (OSError, ValueError, UnicodeError, KeyError) as exc:
            print(f"[MASTER] Cliente desconectado o mensaje inválido: {exc}", flush=True)
        finally:
            if node_id:
                with self.lock:
                    if self.workers.get(node_id, (None,))[0] is conexion:
                        self.workers.pop(node_id, None)
                print(f"[MASTER] Desconectado: {node_id}", flush=True)

    def recibir_conexiones(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
            self.servidor = servidor
            servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            servidor.bind((HOST, PORT))
            servidor.listen()
            servidor.settimeout(0.5)
            print(f"[MASTER] TCP escuchando en {HOST}:{PORT}", flush=True)
            while True:
                try:
                    conexion, addr = servidor.accept()
                    threading.Thread(target=self.aceptar, args=(conexion, addr), daemon=True).start()
                except socket.timeout:
                    continue

    def enviar_global(self, duracion):
        with self.lock:
            activos = list(self.workers.items())
            if not activos:
                print("[MASTER] No hay Workers conectados.", flush=True)
                return None
            task_id = uuid.uuid4().hex[:8]
            inicio = time.time() + 3
            orden = crear_orden(task_id, duracion, inicio)
            self.tareas[task_id] = {"esperados": set(x[0] for x in activos), "listos": set(), "resultados": {}, "errores": {}}
        print(f"[MASTER] BROADCAST_STRESS {task_id}: {duracion}s, {len(activos)} Workers; inicio {inicio:.3f}", flush=True)
        paquete = (json.dumps(orden) + "\n").encode("utf-8")
        for node_id, (conexion, envio_lock) in activos:
            try:
                with envio_lock:
                    conexion.sendall(paquete)
            except OSError as exc:
                with self.lock:
                    self.tareas[task_id]["errores"][node_id] = str(exc)
                print(f"[MASTER] No se pudo enviar a {node_id}: {exc}", flush=True)
        return task_id

    def imprimir_resumen(self, task_id):
        tarea = self.tareas[task_id]
        resultado = resumir_reportes(list(tarea["resultados"].values()))
        print("\n==== INFORME DE RENDIMIENTO ====", flush=True)
        print(f"Tarea: {task_id}", flush=True)
        print(f"Workers esperados: {len(tarea['esperados'])}; listos: {len(tarea['listos'])}; reportados: {resultado['workers_con_resultado']}", flush=True)
        for campo, valor in resultado.items():
            print(f"  {campo}: {valor}", flush=True)
        print("================================\n", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Master de demostración de Actividad 3")
    parser.add_argument("--auto", type=int, metavar="SEGUNDOS", help="Ejecuta una prueba automáticamente")
    parser.add_argument("--workers", type=int, default=2, help="Cantidad a esperar para --auto")
    args = parser.parse_args()
    master = MasterDemo()
    threading.Thread(target=master.recibir_conexiones, daemon=True).start()
    if args.auto is not None:
        limite = time.monotonic() + 15
        while time.monotonic() < limite:
            with master.lock:
                if len(master.workers) >= args.workers:
                    break
            time.sleep(0.1)
        tarea_id = master.enviar_global(args.auto)
        if tarea_id:
            limite = time.monotonic() + args.auto + 10
            while time.monotonic() < limite:
                with master.lock:
                    tarea = master.tareas[tarea_id]
                    if len(tarea["resultados"]) == len(tarea["esperados"]):
                        break
                time.sleep(0.15)
            with master.lock:
                tarea = master.tareas[tarea_id]
                faltantes = tarea["esperados"] - tarea["resultados"].keys()
            if faltantes:
                print("[MASTER] Sin reporte de:", ", ".join(sorted(faltantes)), flush=True)
        return
    print("Comandos: list | stress 5 | exit", flush=True)
    while True:
        try:
            comando = input("master> ").strip().split()
        except (EOFError, KeyboardInterrupt):
            break
        if not comando:
            continue
        if comando[0] == "exit":
            break
        if comando[0] == "list":
            with master.lock:
                print("Workers:", ", ".join(sorted(master.workers)) or "ninguno")
        elif comando[0] == "stress" and len(comando) == 2:
            try:
                master.enviar_global(int(comando[1]))
            except ValueError as exc:
                print("Uso: stress SEGUNDOS (1 a 10).", exc)
        else:
            print("Comandos: list | stress 5 | exit")


if __name__ == "__main__":
    main()
