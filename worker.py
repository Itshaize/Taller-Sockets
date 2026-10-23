import socket
import threading
import json
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "Actividad3_Rafaga"))
from actividad3 import validar_orden, ejecutar_carga_local

HOST = "127.0.0.1"
PUERTO = 5002

nombre = sys.argv[1] if len(sys.argv) > 1 else "worker1"
bloqueo_envio = threading.Lock()
parar = threading.Event()
ocupado = threading.Event()


def enviar(conexion, mensaje):
    datos = json.dumps(mensaje) + "\n"
    with bloqueo_envio:
        conexion.sendall(datos.encode("utf-8"))


def ejecutar_tarea(conexion, comando):
    print("Ejecutando comando:", comando)

    if comando == "STATUS":
        resultado = "Worker activo y funcionando"
    elif comando == "FETCH_LOGS":
        resultado = "Registro de prueba: sin errores"
    elif comando == "EXEC_TASK":
        print("Procesando tarea...")
        time.sleep(5)
        resultado = "Tarea completada correctamente"
    else:
        resultado = "Comando no reconocido"

    try:
        enviar(conexion, {
            "tipo": "resultado",
            "datos": resultado
        })
        print("Resultado enviado al Master")
    except OSError:
        print("No se pudo enviar el resultado")


def enviar_latidos():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.settimeout(1)
        while not parar.is_set():
            inicio = time.monotonic()
            try:
                paquete = json.dumps({"tipo": "heartbeat", "worker_id": nombre}).encode()
                udp.sendto(paquete, (HOST, 5001))
                udp.recvfrom(4096)
            except OSError:
                pass
            parar.wait(max(0, 2 - (time.monotonic() - inicio)))


def ejecutar_stress(conexion, orden):
    try:
        resultado = ejecutar_carga_local(orden, nombre)
        enviar(conexion, resultado)
    except (ValueError, OSError) as exc:
        try:
            enviar(conexion, {"tipo": "STRESS_ERROR", "task_id": orden.get("task_id"), "error": str(exc)})
        except OSError:
            pass
    finally:
        ocupado.clear()


def iniciar_worker():
    conexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        conexion.connect((HOST, PUERTO))
        enviar(conexion, {
            "tipo": "registro",
            "nombre": nombre
        })
        print(f"{nombre} conectado al Master")
        threading.Thread(target=enviar_latidos, daemon=True).start()
        lector = conexion.makefile("r", encoding="utf-8")

        for linea in lector:
            mensaje = json.loads(linea)
            tipo = mensaje.get("tipo")

            if tipo == "confirmacion":
                print(mensaje.get("datos"))
            elif tipo == "error":
                print("Error del Master:", mensaje.get("datos"))
                break
            elif tipo == "BROADCAST_STRESS":
                try:
                    validar_orden(mensaje)
                    if ocupado.is_set():
                        enviar(conexion, {"tipo": "STRESS_ERROR", "task_id": mensaje.get("task_id"), "error": "Worker ocupado"})
                        continue
                    ocupado.set()
                    enviar(conexion, {"tipo": "STRESS_READY", "task_id": mensaje["task_id"]})
                    threading.Thread(target=ejecutar_stress, args=(conexion, mensaje), daemon=True).start()
                except ValueError as exc:
                    enviar(conexion, {"tipo": "STRESS_ERROR", "task_id": mensaje.get("task_id"), "error": str(exc)})

            elif tipo == "comando":
                comando = mensaje.get("accion", "")
                hilo = threading.Thread(
                    target=ejecutar_tarea,
                    args=(conexion, comando),
                    daemon=True
                )
                hilo.start()

    except (OSError, ValueError) as error:
        print("Error:", error)
    except KeyboardInterrupt:
        print("\nWorker detenido")
    finally:
        parar.set()
        try:
            conexion.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conexion.close()
        print("Conexion cerrada")


if __name__ == "__main__":
    iniciar_worker()
