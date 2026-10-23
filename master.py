import socket
import threading
import json
import time
import uuid
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "Actividad3_Rafaga"))
from actividad3 import crear_orden, resumir_reportes

HOST = "0.0.0.0"
PUERTO = 5002

workers = {}
bloqueo = threading.RLock()
heartbeats = {}
tareas = {}
ejecutando = True


def recibir_latidos():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.bind(("0.0.0.0", 5001))
        udp.settimeout(0.5)
        print("Master UDP escuchando en puerto 5001", flush=True)
        while ejecutando:
            try:
                datos, direccion = udp.recvfrom(4096)
                msg = json.loads(datos.decode("utf-8"))
                if not isinstance(msg, dict) or msg.get("tipo") != "heartbeat":
                    continue
                nombre = msg.get("worker_id")
                if not isinstance(nombre, str) or not nombre.strip():
                    continue
                with bloqueo:
                    nuevo = nombre not in heartbeats
                    heartbeats[nombre] = time.monotonic()
                if nuevo:
                    print("\\nUDP registrado:", nombre, flush=True)
                udp.sendto(json.dumps({"tipo": "ack", "worker_id": nombre}).encode(), direccion)
            except socket.timeout:
                pass
            except (OSError, ValueError, UnicodeError):
                pass
            with bloqueo:
                caidos = [n for n, t in heartbeats.items() if time.monotonic() - t >= 6]
                for n in caidos:
                    del heartbeats[n]
            for n in caidos:
                print("\\nUDP desconectado:", n, flush=True)


def lanzar_prueba(duracion):
    with bloqueo:
        activos = {n: c for n, c in workers.items() if n in heartbeats}
        if not activos:
            print("No hay Workers registrados en UDP y TCP")
            return
        task_id = uuid.uuid4().hex[:8]
        orden = crear_orden(task_id, duracion, time.time() + 3)
        tarea = {"esperados": set(activos), "listos": set(), "resultados": {}, "errores": {}}
        tareas[task_id] = tarea
    for nombre, conexion in activos.items():
        try:
            enviar(conexion, orden)
        except OSError as exc:
            with bloqueo:
                tarea["errores"][nombre] = str(exc)
    print("Prueba local:", task_id, "Workers:", sorted(activos))
    def resumen():
        limite = time.monotonic() + duracion + 12
        while time.monotonic() < limite:
            with bloqueo:
                finalizados = set(tarea["resultados"]) | set(tarea["errores"])
                if finalizados >= tarea["esperados"]:
                    break
            time.sleep(0.2)
        with bloqueo:
            reportes = list(tarea["resultados"].values())
            print("Resultados:", resumir_reportes(reportes))
            print("Listos:", sorted(tarea["listos"]))
            print("Errores:", tarea["errores"])
            print("Sin respuesta:", sorted(tarea["esperados"] - set(tarea["resultados"]) - set(tarea["errores"])))
    threading.Thread(target=resumen, daemon=True).start()


def enviar(conexion, mensaje):
    datos = json.dumps(mensaje) + "\n"
    conexion.sendall(datos.encode("utf-8"))


def atender_worker(conexion, direccion):
    nombre = None

    try:
        lector = conexion.makefile("r", encoding="utf-8")

        for linea in lector:
            mensaje = json.loads(linea)
            tipo = mensaje.get("tipo")

            if tipo == "registro":
                nuevo_nombre = mensaje.get("nombre")

                if not nuevo_nombre:
                    break

                with bloqueo:
                    if nuevo_nombre in workers:
                        enviar(conexion, {
                            "tipo": "error",
                            "datos": "Nombre ya registrado"
                        })
                        break

                    nombre = nuevo_nombre
                    workers[nombre] = conexion

                print(f"\n{nombre} conectado desde {direccion}")
                enviar(conexion, {
                    "tipo": "confirmacion",
                    "datos": "Registro correcto"
                })

            elif tipo == "resultado":
                print(f"\nResultado de {nombre}: {mensaje.get('datos')}")
            elif tipo in ("STRESS_READY", "STRESS_RESULT", "STRESS_ERROR"):
                task_id = mensaje.get("task_id")
                with bloqueo:
                    tarea = tareas.get(task_id)
                    if tarea and nombre in tarea["esperados"]:
                        if tipo == "STRESS_READY":
                            tarea["listos"].add(nombre)
                        elif tipo == "STRESS_RESULT":
                            tarea["resultados"][nombre] = mensaje
                        else:
                            tarea["errores"][nombre] = mensaje.get("error", "Error")
                print(f"\n{tipo} de {nombre}: {task_id}")


    except (OSError, ValueError, KeyError) as error:
        print(f"\nError de conexion: {error}")

    finally:
        with bloqueo:
            if nombre and workers.get(nombre) is conexion:
                del workers[nombre]
        conexion.close()
        print(f"\nWorker desconectado: {nombre}")


def aceptar_workers(servidor):
    while ejecutando:
        try:
            conexion, direccion = servidor.accept()
            hilo = threading.Thread(
                target=atender_worker,
                args=(conexion, direccion),
                daemon=True
            )
            hilo.start()
        except OSError:
            break


def iniciar_servidor():
    global ejecutando

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        servidor.bind((HOST, PUERTO))
        servidor.listen()
        threading.Thread(target=recibir_latidos, daemon=True).start()
        print(f"Master TCP escuchando en {HOST}:{PUERTO}")

        hilo = threading.Thread(
            target=aceptar_workers,
            args=(servidor,),
            daemon=True
        )
        hilo.start()

        while True:
            print("\n1. Ver Workers")
            print("2. Enviar comando")
            print("3. Salir")
            print("4. Prueba sincronizada local")
            opcion = input("Opcion: ")

            if opcion == "1":
                with bloqueo:
                    nombres = list(workers.keys())
                print("Workers TCP:", nombres)
                with bloqueo:
                    print("Workers UDP:", sorted(heartbeats))

            elif opcion == "2":
                nombre = input("Nombre del Worker: ").strip()
                comando = input(
                    "Comando (STATUS, FETCH_LOGS, EXEC_TASK): "
                ).strip().upper()

                with bloqueo:
                    conexion = workers.get(nombre)

                if conexion:
                    try:
                        enviar(conexion, {
                            "tipo": "comando",
                            "accion": comando
                        })
                        print("Comando enviado")
                    except OSError:
                        print("Error al enviar el comando")
                else:
                    print("Worker no encontrado")

            elif opcion == "4":
                try:
                    lanzar_prueba(int(input("Duracion (1 a 10 segundos): ")))
                except ValueError as exc:
                    print("Duracion incorrecta:", exc)

            elif opcion == "3":
                print("Cerrando Master...")
                break
            else:
                print("Opcion incorrecta")

    except OSError as error:
        print("Error del servidor:", error)
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma interrumpido")
    finally:
        ejecutando = False
        servidor.close()
        with bloqueo:
            conexiones = list(workers.values())
            workers.clear()
        for conexion in conexiones:
            try:
                conexion.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            conexion.close()
        print("Servidor cerrado")


if __name__ == "__main__":
    iniciar_servidor()
