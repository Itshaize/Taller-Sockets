import socket
import threading
import json
import time
import sys

HOST = "127.0.0.1"
PUERTO = 5002

nombre = sys.argv[1] if len(sys.argv) > 1 else "worker1"
bloqueo_envio = threading.Lock()


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


def iniciar_worker():
    conexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        conexion.connect((HOST, PUERTO))
        enviar(conexion, {
            "tipo": "registro",
            "nombre": nombre
        })
        print(f"{nombre} conectado al Master")
        lector = conexion.makefile("r", encoding="utf-8")

        for linea in lector:
            mensaje = json.loads(linea)
            tipo = mensaje.get("tipo")

            if tipo == "confirmacion":
                print(mensaje.get("datos"))
            elif tipo == "error":
                print("Error del Master:", mensaje.get("datos"))
                break
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
        try:
            conexion.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conexion.close()
        print("Conexion cerrada")


if __name__ == "__main__":
    iniciar_worker()
